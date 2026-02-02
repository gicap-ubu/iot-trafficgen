"""
Logging system for iottrafficgen
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# ANSI color codes
COLORS = {
    'DEBUG': '\033[36m',     # Cyan
    'INFO': '\033[32m',      # Green
    'WARNING': '\033[33m',   # Yellow
    'ERROR': '\033[31m',     # Red
    'CRITICAL': '\033[35m',  # Magenta
    'RESET': '\033[0m'
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    def format(self, record):
        levelname = record.levelname
        if levelname in COLORS:
            record.levelname = f"{COLORS[levelname]}{levelname}{COLORS['RESET']}"
        return super().format(record)


def setup_logging(
    log_dir: Optional[Path] = None,
    verbose: bool = False,
    quiet: bool = False
) -> logging.Logger:
    """
    Setup logging system with file and console handlers.
    
    Args:
        log_dir: Directory for log files (if None, console only)
        verbose: Enable DEBUG level logging
        quiet: Only show ERROR and CRITICAL
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger('iottrafficgen')
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if quiet:
        console_handler.setLevel(logging.ERROR)
    elif verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    
    console_format = ColoredFormatter(
        '%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (if log_dir specified)
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"execution_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Always DEBUG in file
        
        file_format = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
        
        logger.debug(f"Logging to file: {log_file}")
    
    return logger


def get_logger() -> logging.Logger:
    """Get the iottrafficgen logger instance."""
    return logging.getLogger('iottrafficgen')