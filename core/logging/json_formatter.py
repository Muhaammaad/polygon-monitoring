import json
import logging
from datetime import datetime

# Fields to exclude from JSON output
DEFAULT_EXCLUDE = {
    'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
    'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
    'created', 'msecs', 'relativeCreated', 'thread', 'threadName', 'processName',
    'process'
}

# JSON log formatter
class JsonFormatter(logging.Formatter):
    """Simple JSON formatter suitable for structured logging."""

    # Initialize formatter
    def __init__(self, *, include_time: bool = True):
        super().__init__()
        self.include_time = include_time

    # Format log record as JSON string
    def format(self, record: logging.LogRecord) -> str:
        data = {
            'level': record.levelname,
            'name': record.name,
            'message': record.getMessage(),
        }
        if self.include_time:
            # ISO timestamp in UTC
            data['ts'] = datetime.utcfromtimestamp(record.created).isoformat() + 'Z'

        # Include any extra fields provided via logger(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in DEFAULT_EXCLUDE and not key.startswith('_'):
                # Avoid overriding base keys
                if key in ('level', 'name', 'message', 'ts'):
                    continue
                try:
                    json.dumps(value)  # ensure serializable
                    data[key] = value
                except Exception:
                    # fallback to string
                    data[key] = str(value)

        # Render exception info if present 
        
        if record.exc_info:
            data['exception'] = self.formatException(record.exc_info)

        # Return JSON string
        return json.dumps(data, ensure_ascii=False)
