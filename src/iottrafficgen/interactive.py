"""
Interactive menu
"""
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

BANNER = f"""{Fore.CYAN}  ═══════════════════════════════════════════════════
   ██╗ ██████╗ ████████╗     █████╗ ████████╗ ██████╗ 
   ██║██╔═══██╗╚══██╔══╝    ██╔══██╗╚══██╔══╝██╔════╝ 
   ██║██║   ██║   ██║       ███████║   ██║   ██║  ███╗
   ██║██║   ██║   ██║       ██╔══██║   ██║   ██║   ██║
   ██║╚██████╔╝   ██║       ██║  ██║   ██║   ╚██████╔╝
   ╚═╝ ╚═════╝    ╚═╝       ╚═╝  ╚═╝   ╚═╝    ╚═════╝ 
   
           IoT Attack Traffic Generator
                  Version 0.1.0
  ═══════════════════════════════════════════════════{Style.RESET_ALL}
"""

# Attack categories configuration
CATEGORIES = {
    "1": {
        "name": "NMAP Reconnaissance",
        "path": "scenarios/nmap",
        "count": 30,
        "description": "Network scanning and host discovery"
    },
    "2": {
        "name": "SSH Brute Force",
        "path": "scenarios/bruteforce",
        "count": 6,
        "description": "SSH credential attacks"
    },
    "3": {
        "name": "SQL Injection",
        "path": "scenarios/sqli",
        "count": 6,
        "description": "Database exploitation attacks"
    },
    "4": {
        "name": "Denial of Service",
        "path": "scenarios/denial_of_service",
        "count": 17,
        "description": "DoS and DDoS attacks"
    },
    "5": {
        "name": "ARP Spoofing",
        "path": "scenarios/mitm",
        "count": 1,
        "description": "Man-in-the-Middle attacks"
    },
    "6": {
        "name": "MQTT Injection",
        "path": "scenarios/mqtt_inj",
        "count": 2,
        "description": "False data injection"
    },
    "7": {
        "name": "DNS Beaconing",
        "path": "scenarios/dns_beacon",
        "count": 1,
        "description": "C2 communication simulation"
    }
}


def print_banner():
    """Print the application banner."""
    print(BANNER)


def print_main_menu():
    """Print the main category selection menu."""
    print(f"\n{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}       Attack Categories Available{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")
    
    for key, cat in CATEGORIES.items():
        count_str = f"({cat['count']:2} scenario{'s' if cat['count'] > 1 else ' '})"
        print(f" {Fore.GREEN}[{key}]{Style.RESET_ALL} {cat['name']:<25} {Fore.CYAN}{count_str}{Style.RESET_ALL}")
    
    print(f" {Fore.RED}[8]{Style.RESET_ALL} Exit\n")
    print(f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")


def scan_scenarios(category_path: Path) -> List[Tuple[str, Path, str]]:
    """
    Scan a category directory for scenario YAML files.
    
    Returns:
        List of tuples (scenario_number, scenario_path, description)
    """
    if not category_path.exists():
        return []
    
    scenarios = []
    for yaml_file in sorted(category_path.glob("*.yaml")):
        # Extract scenario number from filename (e.g., "01.yaml" -> "01")
        scenario_num = yaml_file.stem
        
        # Try to read description from YAML
        description = "No description"
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'scenario' in data and 'description' in data['scenario']:
                    description = data['scenario']['description']
        except Exception:
            pass  # Keep default description if file can't be read
        
        scenarios.append((scenario_num, yaml_file, description))
    
    return scenarios


def print_scenario_menu(category_name: str, scenarios: List[Tuple[str, Path, str]]):
    """Print compact scenario selection menu in columns."""
    print(f"\n{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {category_name} - Select Scenario{Style.RESET_ALL}")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")
    
    # Print scenarios in 3 columns
    num_scenarios = len(scenarios)
    for i in range(0, num_scenarios, 3):
        row = []
        for j in range(3):
            idx = i + j
            if idx < num_scenarios:
                num, _, _ = scenarios[idx]
                row.append(f" {Fore.GREEN}[{idx+1:2}]{Style.RESET_ALL} Scenario {num}")
            else:
                row.append(" " * 20)  # Empty space for alignment
        print("".join(f"{item:25}" for item in row))
    
    print(f"\n {Fore.YELLOW}[ 0]{Style.RESET_ALL} Back to main menu  |  {Fore.RED}[-1]{Style.RESET_ALL} Exit")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")


def get_input(prompt: str, valid_range: range) -> int:
    """Get validated integer input from user."""
    while True:
        try:
            print(f"{Fore.YELLOW}→{Style.RESET_ALL} {prompt}", end=" ")
            choice = input().strip()
            
            if not choice:
                continue
            
            value = int(choice)
            if value in valid_range or value == -1:
                return value
            else:
                print(f"{Fore.RED}Invalid choice. Please try again.{Style.RESET_ALL}")
        except ValueError:
            print(f"{Fore.RED}Please enter a valid number.{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Interrupted by user.{Style.RESET_ALL}")
            sys.exit(0)


def print_scenario_details(scenario_num: str, scenario_path: Path, description: str):
    """Print detailed information about a selected scenario."""
    # Read additional info from YAML
    name = "Unknown"
    profile = "Unknown"
    script = "Unknown"
    
    try:
        with open(scenario_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            if data:
                if 'scenario' in data and 'name' in data['scenario']:
                    name = data['scenario']['name']
                if 'runs' in data and len(data['runs']) > 0:
                    run = data['runs'][0]
                    if 'profile' in run:
                        profile = Path(run['profile']).name
                    if 'script' in run:
                        script = Path(run['script']).name
    except Exception:
        pass
    
    print(f"\n{Fore.YELLOW}Scenario Details:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}┌─────────────────────────────────────────────────────────────┐{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Name: {name:<53}{Fore.CYAN}│{Style.RESET_ALL}")
    
    # Wrap description if too long
    desc_lines = []
    if len(description) <= 53:
        desc_lines.append(description)
    else:
        words = description.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= 53:
                current_line += (word + " ")
            else:
                desc_lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            desc_lines.append(current_line.strip())
    
    for i, line in enumerate(desc_lines):
        if i == 0:
            print(f"{Fore.CYAN}│{Style.RESET_ALL} Description: {line:<47}{Fore.CYAN}│{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}│{Style.RESET_ALL}              {line:<47}{Fore.CYAN}│{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Profile: {profile:<49}{Fore.CYAN}│{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Script: {script:<50}{Fore.CYAN}│{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└─────────────────────────────────────────────────────────────┘{Style.RESET_ALL}\n")


def detect_and_configure_placeholders(scenario_path: Path) -> Optional[Path]:
    """
    Detect placeholders in scenario and prompt user for values.
    Creates a temporary configured YAML file.
    
    Returns:
        Path to configured temporary YAML, or None if user cancels
    """
    import tempfile
    import shutil
    
    try:
        with open(scenario_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
    except Exception as e:
        print(f"{Fore.RED}Error reading scenario: {e}{Style.RESET_ALL}")
        return None
    
    # Find all placeholders in env variables
    placeholders = {}
    if 'runs' in data:
        for run in data['runs']:
            if 'env' in run:
                for key, value in run['env'].items():
                    if isinstance(value, str) and '_PLACEHOLDER' in value:
                        placeholders[key] = value
    
    if not placeholders:
        # No placeholders, use original file
        return scenario_path
    
    # Prompt for configuration
    print(f"{Fore.YELLOW}Configuration required:{Style.RESET_ALL}\n")
    
    configured_values = {}
    for key, placeholder in placeholders.items():
        while True:
            try:
                print(f"{Fore.CYAN}  {key}:{Style.RESET_ALL} ", end="")
                value = input().strip()
                
                if not value:
                    print(f"{Fore.RED}  Value cannot be empty. Please try again.{Style.RESET_ALL}")
                    continue
                
                configured_values[key] = value
                break
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Configuration cancelled.{Style.RESET_ALL}")
                return None
    
    # Replace placeholders in the data
    for run in data['runs']:
        if 'env' in run:
            for key, value in configured_values.items():
                if key in run['env']:
                    run['env'][key] = value
        
        # Resolve relative paths to absolute paths
        if 'script' in run:
            script_path = Path(run['script'])
            if not script_path.is_absolute():
                # Resolve relative to original scenario directory
                absolute_script = (scenario_path.parent / script_path).resolve()
                run['script'] = str(absolute_script)
        
        if 'profile' in run:
            profile_path = Path(run['profile'])
            if not profile_path.is_absolute():
                # Resolve relative to original scenario directory
                absolute_profile = (scenario_path.parent / profile_path).resolve()
                run['profile'] = str(absolute_profile)
    
    # Create temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.yaml', prefix='iottrafficgen_')
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        return Path(temp_path)
    except Exception as e:
        print(f"{Fore.RED}Error creating temporary file: {e}{Style.RESET_ALL}")
        return None


def confirm_execution(scenario_path: Path) -> bool:
    """Ask user to confirm scenario execution."""
    print(f"{Fore.YELLOW}→{Style.RESET_ALL} Execute this scenario? [y/N/back]: ", end="")
    
    try:
        response = input().strip().lower()
        if response == 'back':
            return False
        return response in ('y', 'yes')
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
        return False


def interactive_mode(workspace: Path) -> Optional[Path]:
    """
    Run interactive menu for scenario selection.
    
    Returns:
        Path to selected scenario, or None if user exits
    """
    print_banner()
    
    while True:
        print_main_menu()
        
        choice = get_input("Select [1-8]:", range(1, 9))
        
        if choice == 8 or choice == -1:
            print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
            return None
        
        # Get selected category
        category = CATEGORIES[str(choice)]
        category_path = workspace / category["path"]
        
        # Scan for scenarios
        scenarios = scan_scenarios(category_path)
        
        if not scenarios:
            print(f"\n{Fore.RED}No scenarios found in {category_path}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            input()
            continue
        
        # Show scenario menu
        while True:
            print_scenario_menu(category["name"], scenarios)
            
            scenario_choice = get_input(
                f"Select [1-{len(scenarios)}] or 0 (back) or -1 (exit):",
                range(0, len(scenarios) + 1)
            )
            
            if scenario_choice == -1:
                print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
                return None
            
            if scenario_choice == 0:
                break  # Back to main menu
            
            # Get selected scenario
            scenario_num, selected_scenario, description = scenarios[scenario_choice - 1]
            
            # Show details
            print_scenario_details(scenario_num, selected_scenario, description)
            
            # Detect and configure placeholders
            configured_scenario = detect_and_configure_placeholders(selected_scenario)
            
            if configured_scenario is None:
                # User cancelled configuration
                print(f"{Fore.YELLOW}Returning to menu...{Style.RESET_ALL}\n")
                continue
            
            # Confirm execution
            if confirm_execution(configured_scenario):
                return configured_scenario
            else:
                # Clean up temp file if it was created
                if configured_scenario != selected_scenario and configured_scenario.exists():
                    configured_scenario.unlink()
                continue