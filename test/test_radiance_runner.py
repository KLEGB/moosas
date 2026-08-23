from datetime import datetime
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from MoosasPy.simulation.rad.runner import (
    RadianceCommandError,
    RadianceRunner,
    RadianceSky,
    RadianceTimeoutError,
)


class RadianceRunnerTests(unittest.TestCase):
    def setUp(self):
        self.sky = RadianceSky(datetime(2026, 1, 1, 12), "-c", diffuse_illuminance=15000)

    def test_run_uses_an_isolated_temporary_directory(self):
        floor = SimpleNamespace(Uid="floor-1")
        model = SimpleNamespace(
            spaceList=[SimpleNamespace(getAllFaces=lambda to_dict: {"MoosasFloor": [floor]})]
        )
        recorded_work_dirs = []

        def write_grid(_floor, gridPath, **_kwargs):
            Path(gridPath).write_text("0 0 0 0 0 1\n", encoding="utf-8")
            return ["0 0 0 0 0 1"]

        def run_command(command, cwd, **_kwargs):
            recorded_work_dirs.append(Path(cwd))
            if Path(command[0]).name.startswith("rtrace"):
                return subprocess.CompletedProcess(command, 0, stdout="1 1 1\n", stderr="")
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        with tempfile.TemporaryDirectory() as parent_dir:
            with patch("MoosasPy.simulation.rad.runner.modelToRad"), patch(
                "MoosasPy.simulation.rad.runner.writeGrid", side_effect=write_grid
            ), patch("MoosasPy.simulation.rad.runner.subprocess.run", side_effect=run_command):
                result = RadianceRunner(model, self.sky, work_dir=parent_dir).run()

        self.assertEqual(len(result.floors), 1)
        self.assertAlmostEqual(result.floors[0].illuminances[0], 179.0)
        self.assertAlmostEqual(result.floors[0].daylight_factor, 179.0 / 15000)
        self.assertTrue(recorded_work_dirs)
        self.assertFalse(recorded_work_dirs[0].exists())

    def test_nonzero_exit_preserves_stderr(self):
        runner = RadianceRunner(SimpleNamespace(), self.sky)
        command = ("rtrace", "model.oct")
        completed = subprocess.CompletedProcess(command, 3, stdout="", stderr="missing octree")

        with tempfile.TemporaryDirectory() as run_dir, patch(
            "MoosasPy.simulation.rad.runner.subprocess.run", return_value=completed
        ):
            with self.assertRaises(RadianceCommandError) as error:
                runner._run_command(command, Path(run_dir))

        self.assertEqual(error.exception.returncode, 3)
        self.assertEqual(error.exception.stderr, "missing octree")

    def test_timeout_preserves_command_diagnostics(self):
        runner = RadianceRunner(SimpleNamespace(), self.sky, timeout_seconds=1)
        command = ("rtrace", "model.oct")
        timeout = subprocess.TimeoutExpired(command, 1, output=b"partial output", stderr=b"still running")

        with tempfile.TemporaryDirectory() as run_dir, patch(
            "MoosasPy.simulation.rad.runner.subprocess.run", side_effect=timeout
        ):
            with self.assertRaises(RadianceTimeoutError) as error:
                runner._run_command(command, Path(run_dir))

        self.assertEqual(error.exception.stdout, "partial output")
        self.assertEqual(error.exception.stderr, "still running")


if __name__ == "__main__":
    unittest.main()