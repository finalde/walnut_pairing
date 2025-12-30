# common/logger.py
import inspect
import logging
import sys
from typing import Any

import structlog


# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
WHITE = "\033[0m"
RESET = "\033[0m"


def _get_color_for_level(level: str, event: str = "") -> str:
    """Get ANSI color code for log level."""
    level_lower = level.lower()
    event_lower = event.lower()
    
    if level_lower == "error" or level_lower == "critical":
        return RED
    elif level_lower == "warning":
        return YELLOW
    elif level_lower == "info":
        # Check if this is a success message
        is_success = any(keyword in event_lower for keyword in ["saved", "estimated", "created", "loaded", "generated"])
        return GREEN if is_success else WHITE
    else:  # debug
        return WHITE


def _add_logger_name(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Add logger name to event dict."""
    # Try to get logger name from various sources
    logger_name = ""
    
    # Check logger_factory_args first (most reliable for BoundLoggerLazyProxy)
    if hasattr(logger, "logger_factory_args") and logger.logger_factory_args:
        logger_name = logger.logger_factory_args[0] if isinstance(logger.logger_factory_args, tuple) and len(logger.logger_factory_args) > 0 else ""
    elif hasattr(logger, "_logger") and logger._logger is not None and hasattr(logger._logger, "_name"):
        logger_name = logger._logger._name
    elif hasattr(logger, "_name"):
        logger_name = logger._name
    elif hasattr(logger, "_initial_values") and "logger" in logger._initial_values:
        logger_name = logger._initial_values["logger"]
    
    if logger_name:
        event_dict["logger"] = logger_name
    
    return event_dict


def _format_log_message(logger: Any, event_dict: dict[str, Any], use_colors: bool = True) -> str:
    """Format log message as [LogLevel: level][Place]: [log body]"""
    level = event_dict.get("level", "info").upper()
    event = event_dict.get("event", "")
    logger_name = event_dict.get("logger", "")
    filename = event_dict.get("filename", "")
    lineno = event_dict.get("lineno", "")
    
    # Build place string (logger name, file name, line number)
    place_parts = []
    if logger_name:
        place_parts.append(logger_name)
    if filename:
        # Extract just the filename without path
        file_part = filename.split("/")[-1] if "/" in filename else filename
        if lineno:
            place_parts.append(f"{file_part}:{lineno}")
        else:
            place_parts.append(file_part)
    elif lineno:
        place_parts.append(f"line:{lineno}")
    
    place = ".".join(place_parts) if place_parts else "unknown"
    
    # Build log body from remaining context
    context_parts = []
    for key, value in event_dict.items():
        if key not in ["level", "event", "logger", "filename", "lineno", "timestamp", "exc_info"]:
            context_parts.append(f"{key}={value}")
    
    log_body = event
    if context_parts:
        log_body = f"{event} " + " ".join(context_parts)
    
    # Format: [LogLevel: level][Place]: [log body]
    if use_colors:
        level_color = _get_color_for_level(level, event)
        formatted = f"[LogLevel: {level_color}{level}{RESET}][{place}]: {log_body}"
    else:
        formatted = f"[LogLevel: {level}][{place}]: {log_body}"
    
    # Add exception info if present
    if "exc_info" in event_dict and event_dict["exc_info"]:
        formatted += f"\n{event_dict['exc_info']}"
    
    return formatted


class ColoredConsoleRenderer:
    """Custom renderer that formats logs with colors and custom format."""
    
    def __init__(self, use_colors: bool = True) -> None:
        self.use_colors = use_colors
    
    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> str:
        # Use colors if explicitly enabled (user wants colors)
        # TTY check is optional - if use_colors=True, apply colors
        return _format_log_message(logger, event_dict, use_colors=self.use_colors)


def configure_logging(log_level: str = "INFO", use_colors: bool = True) -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        _add_logger_name,
        structlog.processors.CallsiteParameterAdder(
            parameters=[
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.LINENO,
            ]
        ),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        ColoredConsoleRenderer(use_colors=use_colors),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, log_level.upper())),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    logger = structlog.get_logger(name)
    # Bind logger name to context so it's available in processors
    logger = logger.bind(logger=name)
    return logger
