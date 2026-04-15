import json
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from typing import Any, Dict

from ..config import get_settings


class StructuredJSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Include standard logging attributes if they exist as extras
        for key, value in record.__dict__.items():
            if key not in {
                "args", "asctime", "created", "exc_info", "exc_text", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs", "message", "msg",
                "name", "pathname", "process", "processName", "relativeCreated",
                "stack_info", "thread", "threadName", "taskName"
            }:
                log_obj[key] = value

        if record.exc_info:
            log_obj["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if the logger is requested multiple times
    if not logger.handlers:
        formatter = StructuredJSONFormatter()
        
        # Console Handler
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # File Handler
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        file_handler = RotatingFileHandler(
            os.path.join(log_dir, "agent_core.log"), 
            maxBytes=5*1024*1024, 
            backupCount=3
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        settings = get_settings()
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))
        
        # Prevent propagation to the root logger to avoid duplicate log entries
        logger.propagate = False

    return logger
