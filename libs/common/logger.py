# common/logger.py
import inspect
import logging
import os
import sys
from typing import Any

import structlog


# ANSI color codes
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
WHITE = "\033[0m"
RESET = "\033[0m"

# Custom SUCCESS log level (between INFO=20 and WARNING=30)
SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")


def _get_level_and_color(level: str) -> tuple[str, str]:
    """Get display level name and ANSI color code for log level.
    
    Returns:
        Tuple of (display_level, color_code)
    """
    level_lower = level.lower()
    
    if level_lower == "error" or level_lower == "critical":
        return (level.upper(), RED)
    elif level_lower == "warning":
        return ("WARNING", YELLOW)
    elif level_lower == "success":
        return ("SUCCESS", GREEN)
    elif level_lower == "info":
        return ("INFO", WHITE)
    else:  # debug
        return ("DEBUG", WHITE)


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


def _preserve_success_level(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Preserve success level if explicitly set in context."""
    # Check if level="success" was set in the event_dict (from bind or kwargs)
    if "level" in event_dict and event_dict["level"] == "success":
        # Keep it as success - add_log_level processor will override it, so we need to set it after
        event_dict["_success_level"] = True
    return event_dict


def _format_log_message(logger: Any, event_dict: dict[str, Any], use_colors: bool = True) -> str:
    """Format log message as [LEVEL] pathname:lineno - message
    
    Cursor recognizes clickable patterns like:
    - /absolute/path/to/file.py:123
    - relative/path/file.py:123
    - file.py:123
    
    The pathname:lineno must appear as a contiguous pattern without extra formatting.
    """
    level = event_dict.get("level", "info")
    event = event_dict.get("event", "")
    filename = event_dict.get("filename", "")
    lineno = event_dict.get("lineno", "")
    
    # Get display level and color
    display_level, level_color = _get_level_and_color(level)
    
    # Build clickable file path in format Cursor recognizes: pathname:lineno
    # Cursor recognizes: /absolute/path:line, relative/path:line, or filename:line
    # IMPORTANT: The pathname:lineno must be contiguous without extra characters
    clickable_location = ""
    if filename and lineno:
        # Use absolute path for better clickability
        if not os.path.isabs(filename):
            abs_path = os.path.abspath(filename)
        else:
            abs_path = filename
        
        # Format: pathname:lineno (Cursor recognizes this exact pattern)
        # No extra characters, just path:line
        clickable_location = f"{abs_path}:{lineno}"
    elif filename:
        abs_path = os.path.abspath(filename) if not os.path.isabs(filename) else filename
        clickable_location = abs_path
    elif lineno:
        clickable_location = f"line:{lineno}"
    
    # Build log body from remaining context
    context_parts = []
    for key, value in event_dict.items():
        if key not in ["level", "event", "logger", "filename", "lineno", "timestamp", "exc_info"]:
            context_parts.append(f"{key}={value}")
    
    log_body = event
    if context_parts:
        log_body = f"{event} " + " ".join(context_parts)
    
    # Format: [LEVEL][pathname:lineno] - message
    # Cursor recognizes pathname:lineno pattern even inside brackets
    # The pathname:lineno must appear as a contiguous string that Cursor can recognize
    if use_colors:
        if clickable_location:
            # Format: [LEVEL][pathname:lineno] - message
            formatted = f"[{level_color}{display_level}{RESET}][{clickable_location}] - {log_body}"
        else:
            formatted = f"[{level_color}{display_level}{RESET}] - {log_body}"
    else:
        if clickable_location:
            formatted = f"[{display_level}][{clickable_location}] - {log_body}"
        else:
            formatted = f"[{display_level}] - {log_body}"
    
    # Add exception info if present
    if "exc_info" in event_dict and event_dict["exc_info"]:
        formatted += f"\n{event_dict['exc_info']}"
    
    return formatted


def _restore_success_level(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Restore success level after add_log_level processor runs."""
    # If _success_level marker exists, override the level set by add_log_level
    if event_dict.get("_success_level"):
        event_dict["level"] = "success"
        # Remove the marker
        event_dict.pop("_success_level", None)
    return event_dict


class ColoredConsoleRenderer:
    """Custom renderer that formats logs with colors and custom format."""
    
    def __init__(self, use_colors: bool = True) -> None:
        self.use_colors = use_colors
    
    def __call__(self, logger: Any, method_name: str, event_dict: dict[str, Any]) -> str:
        # Check if success level was explicitly set in context
        if "level" in event_dict and event_dict["level"] == "success":
            event_dict["level"] = "success"
        # Also check if it's in the logger's context
        elif hasattr(logger, "_context") and logger._context.get("level") == "success":
            event_dict["level"] = "success"
        
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
        _preserve_success_level,  # Must run before add_log_level to preserve success level
        structlog.processors.add_log_level,
        _restore_success_level,  # Restore success level after add_log_level runs
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


class SuccessLogger:
    """Wrapper to add success method to structlog logger."""
    
    def __init__(self, logger: structlog.BoundLogger) -> None:
        self._logger = logger
    
    def success(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Log a success message explicitly at SUCCESS level."""
        # Bind level="success" to the logger context, then call info
        # The renderer will detect the level="success" in the event_dict
        bound_logger = self._logger.bind(level="success")
        bound_logger.info(event, *args, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        # Delegate all other methods to the underlying logger
        return getattr(self._logger, name)


def get_logger(name: str) -> Any:
    logger = structlog.get_logger(name)
    # Bind logger name to context so it's available in processors
    logger = logger.bind(logger=name)
    # Wrap with SuccessLogger to add success method
    return SuccessLogger(logger)
