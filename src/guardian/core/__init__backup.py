# src/guardian/core/__init__.py
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
import logging

@dataclass
class Result:
    """Standard result object for all operations"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Exception] = None

class Service:
    """Base class for all Guardian services"""
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_dir = Path.home() / '.guardian'
        self.config_dir.mkdir(exist_ok=True)
    
    def create_result(self, success: bool, message: str, 
                     data: Optional[Dict[str, Any]] = None,
                     error: Optional[Exception] = None) -> Result:
        """Create a standardized result object"""
        if error:
            self.logger.error(f"{message}: {str(error)}")
        elif not success:
            self.logger.warning(message)
        else:
            self.logger.info(message)
        
        return Result(success=success, message=message, data=data, error=error)
