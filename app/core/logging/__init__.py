"""
نظام السجلات - Logging System
"""
import logging
import sys
from typing import Any

def setup_logging(level: str = "INFO") -> None:
    """
    إعداد نظام السجلات
    
    Args:
        level: مستوى السجل (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def get_logger(name: str) -> logging.Logger:
    """
    الحصول على مسجل
    
    Args:
        name: اسم المسجل
        
    Returns:
        مسجل مُعد
    """
    return logging.getLogger(name)
