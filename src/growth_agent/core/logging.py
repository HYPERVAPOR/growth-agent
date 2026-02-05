"""
Structured logging configuration.

This module sets up logging with console and file outputs.
"""

import logging
import sys
from datetime import datetime, UTC
from pathlib import Path

from growth_agent.config import Settings


def setup_logging(settings: Settings) -> None:
    """
    Configure structured logging for the application.

    Features:
    - Console output with colored formatting
    - Daily rotating file logs in data/logs/
    - Structured JSON format for file logs
    - Workflow-specific loggers

    Args:
        settings: Application settings
    """
    # Create logs directory
    logs_dir = Path(settings.data_root) / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    # Log filename with current date
    log_file = logs_dir / datetime.now(UTC).strftime("%Y-%m-%d.log")

    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.log_level))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler (human-readable with colors)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level))

    # Colored formatter for console
    console_formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)

    # File handler (structured JSON)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Always debug in files

    # JSON formatter for files
    file_formatter = JsonFormatter()
    file_handler.setFormatter(file_formatter)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("lancedb").setLevel(logging.WARNING)

    logger.info(f"Logging initialized: level={settings.log_level}, file={log_file}")


class ColoredFormatter(logging.Formatter):
    """Console formatter with ANSI colors."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        return super().format(record)


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        import json

        log_data = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "logger": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data, ensure_ascii=False)


def get_workflow_logger(workflow_name: str) -> logging.Logger:
    """
    Get a logger for a specific workflow.

    Args:
        workflow_name: Name of the workflow (e.g., "workflow_b")

    Returns:
        Logger instance
    """
    return logging.getLogger(f"growth_agent.{workflow_name}")
