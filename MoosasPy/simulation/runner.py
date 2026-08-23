"""Shared execution primitives for native simulation tools."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import TextIO


@dataclass(frozen=True)
class CommandResult:
    """Captured result of one native-tool command."""

    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str


class CommandError(RuntimeError):
    """Raised when a native-tool command cannot be completed."""

    def __init__(self, command: tuple[str, ...], returncode: int, stdout: str, stderr: str):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(
            f"Command failed with exit code {returncode}: {' '.join(command)}\n{stderr}"
        )


class CommandTimeoutError(TimeoutError):
    """Raised when a native-tool command exceeds its configured timeout."""

    def __init__(self, command: tuple[str, ...], timeout_seconds: float, stdout: str, stderr: str):
        self.command = command
        self.timeout_seconds = timeout_seconds
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(f"Command timed out after {timeout_seconds}s: {' '.join(command)}")


class Runner:
    """Execute a native command without mutating process-global state."""

    result_type = CommandResult
    error_type = CommandError
    timeout_error_type = CommandTimeoutError

    def __init__(self, timeout_seconds: float = 300.0):
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive.")
        self.timeout_seconds = timeout_seconds

    def run_command(
        self,
        command: tuple[str, ...] | list[str],
        cwd: str | Path | None = None,
        stdin: TextIO | None = None,
        stdout: TextIO | None = None,
    ) -> CommandResult:
        """Run one command and return captured diagnostics or raise a typed error."""
        command_tuple = tuple(str(part) for part in command)
        try:
            completed = subprocess.run(
                command_tuple,
                cwd=str(cwd) if cwd is not None else None,
                stdin=stdin,
                stdout=stdout if stdout is not None else subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise self.timeout_error_type(
                command_tuple,
                self.timeout_seconds,
                self._decode_output(error.stdout),
                self._decode_output(error.stderr),
            ) from error
        except OSError as error:
            raise self.error_type(command_tuple, -1, "", str(error)) from error

        stdout_text = completed.stdout or ""
        stderr_text = completed.stderr or ""
        if completed.returncode != 0:
            raise self.error_type(command_tuple, completed.returncode, stdout_text, stderr_text)
        return self.result_type(command_tuple, completed.returncode, stdout_text, stderr_text)

    @staticmethod
    def _decode_output(output: str | bytes | None) -> str:
        if isinstance(output, bytes):
            return output.decode(errors="replace")
        return output or ""