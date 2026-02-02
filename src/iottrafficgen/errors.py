"""
Error handling
"""
from pathlib import Path
from typing import Optional
import click


class IoTTrafficGenError(Exception):
    """Base exception for iottrafficgen errors."""
    
    def __init__(self, message: str, hint: Optional[str] = None):
        self.message = message
        self.hint = hint
        super().__init__(self.message)
    
    def display(self):
        """Display formatted error message."""
        click.secho(f"\n[ERROR] {self.message}", fg="red", bold=True)
        if self.hint:
            click.secho(f"\n  Hint: {self.hint}", fg="yellow")
        click.echo()


class PermissionError(IoTTrafficGenError):
    """Raised when script execution requires elevated permissions."""
    
    def __init__(self, script: Path):
        super().__init__(
            f"Permission denied executing: {script}",
            "Try running with sudo:\n     sudo iottrafficgen run <scenario>"
        )


class ScriptNotFoundError(IoTTrafficGenError):
    """Raised when a script file doesn't exist."""
    
    def __init__(self, script: Path):
        super().__init__(
            f"Script not found: {script}",
            "Check that the script path in the scenario YAML is correct."
        )


class ScriptNotExecutableError(IoTTrafficGenError):
    """Raised when script file is not executable."""
    
    def __init__(self, script: Path):
        super().__init__(
            f"Script is not executable: {script}",
            f"Fix with: chmod +x {script}"
        )


class ToolNotInstalledError(IoTTrafficGenError):
    """Raised when required tool is not installed."""
    
    def __init__(self, tool: str, install_hint: Optional[str] = None):
        hint = install_hint or f"Install {tool} and ensure it's in your PATH"
        super().__init__(
            f"Required tool not found: {tool}",
            hint
        )


class PlaceholderNotConfiguredError(IoTTrafficGenError):
    """Raised when scenario contains unconfigured placeholders."""
    
    def __init__(self, placeholders: list[str], scenario: Path):
        placeholder_list = "\n     ".join(placeholders)
        super().__init__(
            f"Scenario contains unconfigured placeholders:\n     {placeholder_list}",
            f"Edit {scenario} and replace placeholder values with your configuration."
        )


class InvalidScenarioError(IoTTrafficGenError):
    """Raised when scenario YAML is invalid."""
    
    def __init__(self, message: str):
        super().__init__(
            f"Invalid scenario: {message}",
            "Check the scenario YAML syntax and required fields."
        )


class ProfileNotFoundError(IoTTrafficGenError):
    """Raised when profile file doesn't exist."""
    
    def __init__(self, profile: Path):
        super().__init__(
            f"Profile not found: {profile}",
            "Check that the profile path in the scenario YAML is correct."
        )


def check_tool_installed(tool: str) -> bool:
    """
    Check if a tool is installed and available in PATH.
    
    Args:
        tool: Tool name to check
        
    Returns:
        True if installed, False otherwise
    """
    import shutil
    return shutil.which(tool) is not None


def validate_script_executable(script: Path) -> None:
    """
    Validate that a script exists and is executable.
    
    Args:
        script: Path to script
        
    Raises:
        ScriptNotFoundError: If script doesn't exist
        ScriptNotExecutableError: If script is not executable
    """
    if not script.exists():
        raise ScriptNotFoundError(script)
    
    if not script.is_file():
        raise IoTTrafficGenError(f"Script path is not a file: {script}")
    
    # Check if executable (Unix-like systems)
    import os
    if not os.access(script, os.X_OK):
        raise ScriptNotExecutableError(script)


def detect_placeholders(env: dict) -> list[str]:
    """
    Detect unconfigured placeholder values in environment variables.
    
    Args:
        env: Environment variables dict
        
    Returns:
        List of placeholder variable names
    """
    placeholders = []
    for key, value in env.items():
        if isinstance(value, str) and "_PLACEHOLDER" in value:
            placeholders.append(f"{key}={value}")
    return placeholders


TOOL_INSTALL_HINTS = {
    "nmap": "apt install nmap  (or)  brew install nmap",
    "hping3": "apt install hping3  (or)  brew install hping3",
    "sqlmap": "pip install sqlmap  (or)  apt install sqlmap",
    "hydra": "apt install hydra  (or)  brew install hydra",
    "arpspoof": "apt install dsniff  (or)  brew install dsniff",
    "python3": "apt install python3  (or)  brew install python3",
}


def get_install_hint(tool: str) -> Optional[str]:
    """Get installation hint for a specific tool."""
    return TOOL_INSTALL_HINTS.get(tool)