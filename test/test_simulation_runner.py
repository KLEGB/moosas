from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from MoosasPy.simulation.runner import CommandError, CommandTimeoutError, Runner


class RunnerTests(unittest.TestCase):
    def test_success_returns_structured_diagnostics(self):
        command = ("native-tool", "--version")
        completed = subprocess.CompletedProcess(command, 0, stdout="ready", stderr="warning")

        with patch("MoosasPy.simulation.runner.subprocess.run", return_value=completed):
            result = Runner(timeout_seconds=12).run_command(command, cwd="workdir")

        self.assertEqual(result.command, command)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "ready")
        self.assertEqual(result.stderr, "warning")

    def test_nonzero_exit_preserves_diagnostics(self):
        command = ("native-tool", "input")
        completed = subprocess.CompletedProcess(command, 4, stdout="partial", stderr="bad input")

        with patch("MoosasPy.simulation.runner.subprocess.run", return_value=completed):
            with self.assertRaises(CommandError) as error:
                Runner().run_command(command)

        self.assertEqual(error.exception.returncode, 4)
        self.assertEqual(error.exception.stdout, "partial")
        self.assertEqual(error.exception.stderr, "bad input")

    def test_timeout_preserves_diagnostics(self):
        command = ("native-tool", "input")
        timeout = subprocess.TimeoutExpired(command, 3, output=b"partial", stderr=b"timed out")

        with patch("MoosasPy.simulation.runner.subprocess.run", side_effect=timeout):
            with self.assertRaises(CommandTimeoutError) as error:
                Runner(timeout_seconds=3).run_command(command)

        self.assertEqual(error.exception.stdout, "partial")
        self.assertEqual(error.exception.stderr, "timed out")

    def test_file_streams_are_passed_without_shell_redirection(self):
        command = ("native-tool", "input")

        def run_command(*_args, stdin, stdout, **_kwargs):
            self.assertIsNotNone(stdin)
            self.assertIsNotNone(stdout)
            stdout.write("result\n")
            return subprocess.CompletedProcess(command, 0, stdout=None, stderr="")

        with tempfile.TemporaryDirectory() as temporary_dir:
            root = Path(temporary_dir)
            input_path = root / "input.txt"
            output_path = root / "output.txt"
            input_path.write_text("request\n", encoding="utf-8")
            with input_path.open("r", encoding="utf-8") as input_file, output_path.open("w", encoding="utf-8") as output_file, patch(
                "MoosasPy.simulation.runner.subprocess.run", side_effect=run_command
            ):
                Runner().run_command(command, stdin=input_file, stdout=output_file)

            self.assertEqual(output_path.read_text(encoding="utf-8"), "result\n")


if __name__ == "__main__":
    unittest.main()