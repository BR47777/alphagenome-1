#!/usr/bin/env python3
"""
Logging configuration for AlphaGenome UI application.
"""

import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


class AlphaGenomeLogger:
    """Custom logger for AlphaGenome application."""
    
    def __init__(self, name: str = "alphagenome_ui", log_level: str = "INFO"):
        self.name = name
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.logger = None
        self._setup_logger()
    
    def _setup_logger(self):
        """Set up the logger with appropriate handlers."""
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(self.log_level)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler (if logs directory exists or can be created)
        try:
            logs_dir = Path("logs")
            logs_dir.mkdir(exist_ok=True)
            
            log_file = logs_dir / f"alphagenome_ui_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)
            
        except (OSError, PermissionError) as e:
            # If we can't create log files, just use console logging
            self.logger.warning(f"Could not set up file logging: {e}")
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger."""
        return self.logger
    
    def log_api_call(self, method: str, params: dict, success: bool, 
                     duration: Optional[float] = None, error: Optional[str] = None):
        """Log API call details."""
        log_data = {
            "method": method,
            "params_count": len(params),
            "success": success,
            "duration_ms": round(duration * 1000, 2) if duration else None
        }
        
        if success:
            self.logger.info(f"API call successful: {method} ({log_data})")
        else:
            self.logger.error(f"API call failed: {method} - {error} ({log_data})")
    
    def log_validation_error(self, validation_type: str, input_data: str, error: str):
        """Log validation errors."""
        self.logger.warning(f"Validation failed [{validation_type}]: {error} (input: {input_data[:100]}...)")
    
    def log_user_action(self, action: str, details: dict = None):
        """Log user actions."""
        details_str = f" - {details}" if details else ""
        self.logger.info(f"User action: {action}{details_str}")
    
    def log_performance(self, operation: str, duration: float, details: dict = None):
        """Log performance metrics."""
        details_str = f" - {details}" if details else ""
        self.logger.info(f"Performance [{operation}]: {duration:.3f}s{details_str}")


class ErrorHandler:
    """Centralized error handling for the application."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def handle_validation_error(self, error_type: str, message: str, user_input: str = "") -> str:
        """Handle validation errors and return user-friendly message."""
        self.logger.warning(f"Validation error [{error_type}]: {message} (input: {user_input[:50]}...)")
        
        error_messages = {
            "api_key": "❌ **Invalid API Key**: Please check your AlphaGenome API key format.",
            "sequence": "❌ **Invalid DNA Sequence**: Please provide a valid DNA sequence (A, C, G, T, N only).",
            "interval": "❌ **Invalid Genomic Interval**: Please use format chr:start-end (e.g., chr22:1000-2000).",
            "variant": "❌ **Invalid Variant**: Please use format chr:pos:ref>alt (e.g., chr22:1000:A>T).",
            "ontology": "❌ **Invalid Ontology Terms**: Please provide valid ontology terms (e.g., UBERON:0001157).",
            "output_types": "❌ **Invalid Output Types**: Please select valid AlphaGenome output types."
        }
        
        base_message = error_messages.get(error_type, "❌ **Validation Error**")
        return f"{base_message}\n\n**Details**: {message}"
    
    def handle_api_error(self, error: Exception, operation: str = "API call") -> str:
        """Handle API errors and return user-friendly message."""
        error_str = str(error)
        self.logger.error(f"API error during {operation}: {error_str}")
        
        # Import APIValidator for error handling
        try:
            from ui_components import APIValidator
            return APIValidator.handle_api_error(error)
        except ImportError:
            return f"❌ **API Error**: {error_str}"
    
    def handle_unexpected_error(self, error: Exception, context: str = "operation") -> str:
        """Handle unexpected errors."""
        import traceback
        error_trace = traceback.format_exc()
        self.logger.error(f"Unexpected error during {context}: {error_trace}")
        
        return (
            f"❌ **Unexpected Error**: An error occurred during {context}.\n\n"
            f"**Error**: {str(error)}\n\n"
            "Please try again or contact support if the issue persists."
        )
    
    def log_and_format_error(self, error: Exception, error_type: str, context: str = "") -> str:
        """Log error and return formatted message for user."""
        if error_type == "validation":
            return self.handle_validation_error("general", str(error), context)
        elif error_type == "api":
            return self.handle_api_error(error, context)
        else:
            return self.handle_unexpected_error(error, context)


class PerformanceMonitor:
    """Monitor application performance."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.start_times = {}
    
    def start_timer(self, operation: str):
        """Start timing an operation."""
        import time
        self.start_times[operation] = time.time()
    
    def end_timer(self, operation: str, details: dict = None) -> float:
        """End timing an operation and log the duration."""
        import time
        if operation not in self.start_times:
            self.logger.warning(f"Timer for operation '{operation}' was not started")
            return 0.0
        
        duration = time.time() - self.start_times[operation]
        del self.start_times[operation]
        
        # Log performance
        details_str = f" - {details}" if details else ""
        self.logger.info(f"Performance [{operation}]: {duration:.3f}s{details_str}")
        
        # Warn about slow operations
        if duration > 30:  # 30 seconds
            self.logger.warning(f"Slow operation detected: {operation} took {duration:.3f}s")
        
        return duration
    
    def log_memory_usage(self, context: str = ""):
        """Log current memory usage if psutil is available."""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            context_str = f" [{context}]" if context else ""
            self.logger.info(f"Memory usage{context_str}: {memory_mb:.1f} MB")
            
            # Warn about high memory usage
            if memory_mb > 1000:  # 1GB
                self.logger.warning(f"High memory usage detected: {memory_mb:.1f} MB")
                
        except ImportError:
            # psutil not available, skip memory monitoring
            pass
        except Exception as e:
            self.logger.debug(f"Could not get memory usage: {e}")


# Global logger instance
_global_logger = None
_global_error_handler = None
_global_performance_monitor = None


def get_logger() -> logging.Logger:
    """Get the global logger instance."""
    global _global_logger
    if _global_logger is None:
        _global_logger = AlphaGenomeLogger()
    return _global_logger.get_logger()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler(get_logger())
    return _global_error_handler


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _global_performance_monitor
    if _global_performance_monitor is None:
        _global_performance_monitor = PerformanceMonitor(get_logger())
    return _global_performance_monitor


def setup_logging(log_level: str = "INFO"):
    """Set up logging for the application."""
    global _global_logger, _global_error_handler, _global_performance_monitor
    
    _global_logger = AlphaGenomeLogger(log_level=log_level)
    _global_error_handler = ErrorHandler(_global_logger.get_logger())
    _global_performance_monitor = PerformanceMonitor(_global_logger.get_logger())
    
    logger = _global_logger.get_logger()
    logger.info("AlphaGenome UI logging initialized")
    
    return logger
