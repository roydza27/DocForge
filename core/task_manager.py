"""
Task Manager — executes processing jobs with logging, error handling,
and a simple progress indicator.
"""

import time
from pathlib import Path
from typing import Callable, Any, Optional

from core.logger import get_logger
from core.file_manager import JobWorkspace, generate_job_id

log = get_logger("task_manager")


class TaskResult:
    """Holds the outcome of a task execution."""

    def __init__(
        self,
        job_id: str,
        success: bool,
        output_path: Optional[Path] = None,
        message: str = "",
        elapsed: float = 0.0,
    ) -> None:
        self.job_id = job_id
        self.success = success
        self.output_path = output_path
        self.message = message
        self.elapsed = elapsed

    def __str__(self) -> str:
        status = "✓ SUCCESS" if self.success else "✗ FAILED"
        lines = [f"[{self.job_id}] {status} ({self.elapsed:.2f}s)"]
        if self.message:
            lines.append(f"  {self.message}")
        if self.output_path:
            lines.append(f"  Output → {self.output_path}")
        return "\n".join(lines)


class TaskManager:
    """
    Executes a processing callable inside a managed workspace.

    The callable signature::

        fn(workspace: JobWorkspace, **kwargs) -> Path | None
    """

    def run(
        self,
        fn: Callable[..., Optional[Path]],
        operation: str = "operation",
        **kwargs: Any,
    ) -> TaskResult:
        """
        Run *fn* inside a temporary workspace.

        Args:
            fn:        Callable that performs the actual work.
            operation: Human-readable name for logging.
            **kwargs:  Forwarded to *fn*.

        Returns:
            TaskResult describing the outcome.
        """
        job_id = generate_job_id()
        log.info("Starting %s  [%s]", operation, job_id)
        start = time.perf_counter()

        try:
            with JobWorkspace(job_id) as workspace:
                output_path = fn(workspace=workspace, **kwargs)

            elapsed = time.perf_counter() - start
            result = TaskResult(
                job_id=job_id,
                success=True,
                output_path=output_path,
                message=f"{operation} completed successfully.",
                elapsed=elapsed,
            )
            log.info("Completed %s in %.2fs → %s", operation, elapsed, output_path)

        except (FileNotFoundError, ValueError, PermissionError) as exc:
            elapsed = time.perf_counter() - start
            result = TaskResult(
                job_id=job_id,
                success=False,
                message=str(exc),
                elapsed=elapsed,
            )
            log.error("%s failed: %s", operation, exc)

        except Exception as exc:
            elapsed = time.perf_counter() - start
            result = TaskResult(
                job_id=job_id,
                success=False,
                message=f"Unexpected error: {exc}",
                elapsed=elapsed,
            )
            log.exception("Unexpected error during %s", operation)

        return result


# Module-level singleton
task_manager = TaskManager()
