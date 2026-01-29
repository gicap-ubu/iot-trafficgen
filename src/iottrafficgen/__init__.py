"""
iottrafficgen: Reproducible IoT traffic generation for cybersecurity research
"""

__version__ = "0.1.0"
__author__ = "Branly Martinez - GICAP Research Group"

from .core import run_scenario

__all__ = [
    "__version__",
    "__author__",
    "run_scenario",
]