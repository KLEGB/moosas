from __future__ import annotations

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from MoosasPy.simulation.airflow import create_openfoam_workspace
from MoosasPy.simulation.weather import write_epw_csv


class NativeToolMigrationTests(unittest.TestCase):
    def test_create_openfoam_workspace_replaces_existing_content(self):
        with TemporaryDirectory() as directory:
            workspace = Path(directory) / "case"
            workspace.mkdir()
            (workspace / "stale.txt").write_text("stale", encoding="utf-8")

            self.assertEqual(create_openfoam_workspace(workspace), workspace)

            self.assertFalse((workspace / "stale.txt").exists())
            for relative_path in ("0", "constant/triSurface", "log", "system"):
                self.assertTrue((workspace / relative_path).is_dir())
            self.assertTrue((workspace / "vent.foam").is_file())

    def test_write_epw_csv_matches_dest_format(self):
        with TemporaryDirectory() as directory:
            epw_path = Path(directory) / "weather.epw"
            output_path = Path(directory) / "weather.csv"
            self._write_epw_fixture(epw_path)

            self.assertEqual(write_epw_csv(epw_path, output_path), str(output_path))

            with output_path.open(newline="", encoding="utf-8") as output_file:
                rows = list(csv.reader(output_file))

        self.assertEqual(len(rows), 8760)
        self.assertEqual(rows[0], [
            "12345", "0", "0", "20.13", "7.65", "100.00", "50.00",
            "10.00", "269.70", "1.00", "16", "101325.00", "9999999",
        ])

    @staticmethod
    def _write_epw_fixture(epw_path: Path) -> None:
        ground_temperatures = ["GROUND", "0", "0", "0", "0", "0"] + ["10"] * 12
        hourly_record = ["0"] * 22
        hourly_record[6] = "20.125"
        hourly_record[7] = "10"
        hourly_record[9] = "101325"
        hourly_record[12] = "300"
        hourly_record[13] = "100"
        hourly_record[15] = "50"
        hourly_record[20] = "0"
        hourly_record[21] = "1"
        lines = [
            "LOCATION,City,State,Country,Source,12345;,1,2,3,4",
            "header",
            "header",
            ",".join(ground_temperatures),
            "header",
            "header",
            "header",
            "header",
        ] + [",".join(hourly_record)] * 8760
        epw_path.write_text("\n".join(lines), encoding="utf-8")