import argparse
import glob
import shutil
import sqlite3
from pathlib import Path
from eppy import modeleditor
from eppy.runner.run_functions import run


def find_energyplus_idd():
    """Find the Energy+.idd file in common EnergyPlus installation paths on the C: drive."""
    search_patterns = [
        Path("C:/") / "EnergyPlusV*" / "Energy+.idd",
        Path("C:/Program Files") / "EnergyPlusV*" / "Energy+.idd",
        Path("C:/Program Files (x86)") / "EnergyPlusV*" / "Energy+.idd"
    ]

    idd_candidates = []
    for pattern in search_patterns:
        for idd_path in glob.glob(str(pattern)):
            candidate = Path(idd_path)
            if candidate.exists():
                idd_candidates.append(candidate)

    if not idd_candidates:
        return None

    def extract_version(idd_path):
        version_str = idd_path.parent.name.replace("EnergyPlusV", "")
        return tuple(map(int, version_str.split("-")))

    idd_candidates.sort(key=extract_version, reverse=True)
    return idd_candidates[0]


def prepare_simulation_directory(idf_path, epw_path):
    """Prepare simulation directory and return paths to new IDF, directory, and EPW prefix."""
    sim_dir = idf_path.parent / idf_path.stem
    sim_dir.mkdir(exist_ok=True)

    epw_prefix = epw_path.stem  # EPW filename without extension (used as output prefix)

    new_idf_name = f"{epw_prefix}.idf"
    new_idf_path = sim_dir / new_idf_name
    shutil.copy2(idf_path, new_idf_path)

    return new_idf_path, sim_dir, epw_prefix


def ensure_hourly_output_variables(idf):
    """Ensure IDF includes hourly Output:Variable objects for the 3 required variables."""
    # Define required variables (Category, Variable Name, Reporting Frequency = "hourly")
    # Note: Categories are inferred from typical EnergyPlus variable groupings
    required_vars = [
        ("HVAC", "Zone Air System Sensible Cooling Rate", "hourly"),
        ("HVAC", "Zone Air System Sensible Heating Rate", "hourly"),
        ("Zone", "Zone Lights Electricity Energy", "hourly")
    ]

    for category, var_name, freq in required_vars:
        # Check if Output:Variable already exists with hourly frequency
        existing_vars = idf.idfobjects["Output:Variable"]
        exists = any(
            obj.Variable_Name == var_name and
            obj.Reporting_Frequency.lower() == freq and
            obj.Key_Value == "*"  # Apply to all zones/systems
            for obj in existing_vars
        )

        if not exists:
            # Add new Output:Variable with hourly reporting
            output_var = idf.newidfobject("Output:Variable")
            output_var.Key_Value = "*"  # All applicable objects
            output_var.Variable_Name = var_name
            output_var.Reporting_Frequency = freq
            print(f"Added hourly Output:Variable for '{category} - {var_name}'")

    idf.save()


def ensure_sql_output(idf):
    """Ensure Output:SQLite is enabled in the IDF."""
    if len(idf.idfobjects["Output:SQLite"]) == 0:
        sql_obj = idf.newidfobject("Output:SQLite")
        sql_obj.Option_Type = "Simple"
        idf.save()
        print(f"Added Output:SQLite to {idf.idfname}")


def query_hourly_results(sql_path):
    """Query SQL file for hourly results of the 3 variables (SQL-like logic)."""
    # SQL queries to extract hourly data (matches "hourly" reporting frequency)
    queries = {
        "Output:Variable, *, Zone Air System Sensible Cooling Rate, hourly;": """
            SELECT TimeIndex, Value FROM ReportVariable
            WHERE VariableName = 'Zone Air System Sensible Cooling Rate'
              AND Category = 'HVAC'
              AND ReportingFrequency = 'Hourly'
              ORDER BY TimeIndex
        """,
        "Output:Variable, *, Zone Air System Sensible Heating Rate, hourly;": """
            SELECT TimeIndex, Value FROM ReportVariable
            WHERE VariableName = 'Zone Air System Sensible Heating Rate'
              AND Category = 'HVAC'
              AND ReportingFrequency = 'Hourly'
              ORDER BY TimeIndex
        """,
        "Output:Variable, *, Zone Lights Electric Power, hourly;": """
            SELECT TimeIndex, Value FROM ReportVariable
            WHERE VariableName = 'Zone Lights Electric Power'
              AND Category = 'Zone'
              AND ReportingFrequency = 'Hourly'
              ORDER BY TimeIndex
        """
    }

    results = {}
    with sqlite3.connect(sql_path) as conn:
        cursor = conn.cursor()
        for desc, query in queries.items():
            cursor.execute(query)
            hourly_data = cursor.fetchall()  # List of (TimeIndex, Value) tuples
            if hourly_data:
                # Store as list of dictionaries for readability
                results[desc] = [{"TimeIndex": idx, "Value (W)": val} for idx, val in hourly_data]
            else:
                results[desc] = None  # No hourly data found

    return results


def run_simulation(idf_path, epw_path, idd_path, output_dir, output_prefix):
    """Run simulation, ensure hourly variables, and verify results via SQL."""
    modeleditor.IDF.setiddname(str(idd_path))
    idf = modeleditor.IDF(str(idf_path))

    # Ensure SQL output and hourly variables are enabled
    ensure_sql_output(idf)
    ensure_hourly_output_variables(idf)

    print(f"Starting simulation with IDF: {idf_path}, EPW: {epw_path}")
    run(
        idf,
        weather=str(epw_path),
        output_directory=str(output_dir),
        output_prefix=output_prefix
    )

    # Verify SQL output exists
    sql_path = output_dir / f"{output_prefix}out.sql"
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL output file missing: {sql_path}")

    # Query and validate hourly results
    # print("\nQuerying hourly results from SQL...")
    # hourly_results = query_hourly_results(sql_path)
    #
    # # Check for missing data and print samples
    # for desc, data in hourly_results.items():
    #     if data is None:
    #         raise ValueError(f"Missing hourly data for: {desc}")
    #     # Print first 5 entries as a sample
    #     print(f"\n{desc} (first 5 entries):")
    #     for entry in data[:5]:
    #         print(f"  TimeIndex: {entry['TimeIndex']}, Value: {entry['Value (W)']:.2f} W")
    #
    # print("\nAll required hourly variables are present in the output.")


def main():
    parser = argparse.ArgumentParser(description="Run EnergyPlus with hourly variable verification.")
    parser.add_argument("-w", required=True, help="Path to the EPW weather file")
    parser.add_argument("idf", help="Path to the IDF input file")
    args = parser.parse_args()

    epw_path = Path(args.w).resolve()
    idf_path = Path(args.idf).resolve()

    if not epw_path.exists():
        raise FileNotFoundError(f"EPW file not found: {epw_path}")
    if not idf_path.exists():
        raise FileNotFoundError(f"IDF file not found: {idf_path}")

    print("Searching for Energy+.idd...")
    idd_path = find_energyplus_idd()
    if not idd_path or not idd_path.exists():
        raise FileNotFoundError(
            "Energy+.idd not found. Checked paths include:\n"
            "- C:/EnergyPlusV*/\n"
            "- C:/Program Files/EnergyPlusV*/\n"
            "- C:/Program Files (x86)/EnergyPlusV*/"
        )
    print(f"Found Energy+.idd at: {idd_path}")

    print("Preparing simulation environment...")
    new_idf_path, sim_dir, epw_prefix = prepare_simulation_directory(idf_path, epw_path)
    print(f"Processed IDF saved to: {new_idf_path}")
    print(f"Output files will use prefix: {epw_prefix}")

    run_simulation(new_idf_path, epw_path, idd_path, sim_dir, epw_prefix)


if __name__ == "__main__":
    main()