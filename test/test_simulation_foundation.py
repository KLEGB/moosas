from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from MoosasPy.simulation import SimulationWorkspace
from MoosasPy.simulation.engine import NativeExecution
from MoosasPy.simulation.runner import Runner


class RecordingEngine:
    name = "recording"

    def __init__(self):
        self.calls = []

    def execute(self, command, **options):
        self.calls.append((command, options))
        return NativeExecution(command, 0, "engine output", "")


class SimulationFoundationTests(unittest.TestCase):
    def test_runner_accepts_a_replaceable_native_engine(self):
        engine = RecordingEngine()

        result = Runner(engine=engine, timeout_seconds=17).run_command(
            ["native-tool", 42], cwd="workspace"
        )

        self.assertEqual(result.command, ("native-tool", "42"))
        self.assertEqual(result.stdout, "engine output")
        self.assertEqual(engine.calls[0][1]["timeout_seconds"], 17)

    def test_temporary_workspace_is_cleaned_and_reported(self):
        with TemporaryDirectory() as parent:
            with SimulationWorkspace(parent=parent, prefix="test-run-") as workspace:
                artifact = workspace.child("output", "result.txt")
                artifact.write_text("result", encoding="utf-8")
                report = workspace.report
                self.assertTrue(artifact.exists())
                self.assertFalse(report.retained)

            self.assertFalse(Path(report.path).exists())

    def test_retained_workspace_survives_context_exit(self):
        with TemporaryDirectory() as parent:
            with SimulationWorkspace(parent=parent, prefix="test-run-", retain=True) as workspace:
                report = workspace.report

            self.assertTrue(Path(report.path).is_dir())
            self.assertTrue(report.retained)


if __name__ == "__main__":
    unittest.main()
