import argparse
import numpy as np
from pathlib import Path
from db_eplusout_reader import get_results, Variable, constants
from db_eplusout_reader import exceptions


def parse_arguments():
    """Parse command-line arguments for input SQL file and output CSV file.

    Returns
    -------
    dict
        Dictionary with keys:
            - 'sql_path': pathlib.Path to the EnergyPlus SQL result file.
            - 'output_path': pathlib.Path to the output CSV file.
    """
    parser = argparse.ArgumentParser(description="Read EnergyPlus SQL results with db_eplusout_reader.get_results.")
    parser.add_argument("-o", required=True, help="Path to the output CSV file")
    parser.add_argument("sql", help="Path to the EnergyPlus SQL result file")
    args = parser.parse_args()

    return {
        "sql_path": Path(args.sql).resolve(),
        "output_path": Path(args.o).resolve()
    }


def get_all_zones(results_variables):
    """Extract all unique zone names from results variables.

    Parameters
    ----------
    results_variables : list of Variable
        List of Variable objects returned by get_results().

    Returns
    -------
    list of str
        List of unique zone names (e.g., ["Zone 1", "Zone 2"]).
    """
    # Extract zone names from variable keys (exclude wildcard "*")
    zones = list({var.key for var in results_variables if var.key != "*"})
    return sorted(zones)


def extract_hourly_data(results, zones):
    """Extract and aggregate hourly data for target variables across all zones.

    Parameters
    ----------
    results : object
        Results object returned by get_results() containing 'variables' (list of Variable) and 'arrays' (list of lists).
    zones : list of str
        List of zone names to process.

    Returns
    -------
    tuple of (np.ndarray, np.ndarray, np.ndarray, np.ndarray)
        - hours: 1D array of hour indices (shape: (n_hours,))
        - total_lights: 1D array of aggregated lighting power (W) (shape: (n_hours,))
        - total_cooling: 1D array of aggregated cooling rate (W) (shape: (n_hours,))
        - total_heating: 1D array of aggregated heating rate (W) (shape: (n_hours,))
    """
    # Get number of hours from the length of the first data list (handle empty results)
    n_hours = len(results.arrays[0]) if results.arrays else 0
    hours = np.arange(n_hours, dtype=int)

    # Initialize total arrays with zeros
    total_lights = np.zeros(n_hours, dtype=np.float64)
    total_cooling = np.zeros(n_hours, dtype=np.float64)
    total_heating = np.zeros(n_hours, dtype=np.float64)

    # Map variables to their data (convert lists to numpy arrays for arithmetic)
    var_data_map = {}
    for var, data_list in zip(results.variables, results.arrays):
        # Convert list to numpy array for consistent handling
        var_array = np.array(data_list, dtype=np.float64)
        var_data_map[(var.key, var.type)] = var_array

    # Aggregate data for each zone
    for zone in zones:
        # Sum lighting data
        lights_key = (zone, "Zone Lights Electricity Energy")
        total_lights += var_data_map.get(lights_key, np.zeros(n_hours))

        # Sum cooling data
        cooling_key = (zone, "Zone Air System Sensible Cooling Rate")
        total_cooling += var_data_map.get(cooling_key, np.zeros(n_hours))

        # Sum heating data
        heating_key = (zone, "Zone Air System Sensible Heating Rate")
        total_heating += var_data_map.get(heating_key, np.zeros(n_hours))

    return hours, total_lights, total_cooling, total_heating


def export_to_csv(hours, lights, cooling, heating, output_path):
    """Export aggregated data to CSV using numpy.

    Parameters
    ----------
    hours : np.ndarray
        1D array of hour indices (shape: (n_hours,)).
    lights : np.ndarray
        1D array of total lighting power (W) (shape: (n_hours,)).
    cooling : np.ndarray
        1D array of total cooling rate (W) (shape: (n_hours,)).
    heating : np.ndarray
        1D array of total heating rate (W) (shape: (n_hours,)).
    output_path : pathlib.Path
        Path to save the CSV file.
    """
    # Combine data into a single 2D array
    data = np.column_stack((hours, lights, cooling, heating))

    # CSV header
    header = "hour,lights electricity,sensible cooling,sensible heating"

    # Write to CSV
    np.savetxt(
        output_path,
        data,
        delimiter=",",
        header=header,
        comments="",
        fmt=["%d", "%.2f", "%.2f", "%.2f"]
    )
    print(f"Aggregated data exported to: {output_path}")


def main():
    """Main workflow: parse arguments, load results, process data, export CSV."""
    args = parse_arguments()
    sql_path = args["sql_path"]
    output_path = args["output_path"]

    # Validate SQL file exists
    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")

    # Define target variables (using wildcard "*" to get all zones)
    target_vars = [
        Variable(None, "Zone Lights Electricity Energy", "J"),
        Variable(None, "Zone Air System Sensible Cooling Rate", "W"),
        Variable(None, "Zone Air System Sensible Heating Rate", "W")
    ]

    # Load results with hourly frequency (constants.H)
    print(f"Loading hourly results from SQL file: {sql_path}")
    try:
        results = get_results(
            str(sql_path),
            variables=target_vars,
            frequency=constants.H  # Hourly frequency
        )
    except exceptions.NoResults:
        raise ValueError("No hourly results found for the target variables.")
    # Identify all zones from results
    zones = get_all_zones(results.variables)
    print(f"Found {len(zones)} zones: {', '.join(zones)}")
    if not zones:
        raise ValueError("No zones found in the SQL results.")

    # Extract and aggregate hourly data
    print("Extracting and aggregating hourly data...")
    hours, total_lights, total_cooling, total_heating = extract_hourly_data(results, zones)

    # Export to CSV
    export_to_csv(hours, total_lights, total_cooling, total_heating, output_path)


if __name__ == "__main__":
    main()