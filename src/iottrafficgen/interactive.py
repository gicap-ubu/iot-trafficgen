"""
Interactive menu for iottrafficgen
"""
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import yaml
from colorama import Fore, Style, init

init(autoreset=True)

BANNER = f"""{Fore.CYAN}  ═══════════════════════════════════════════════════════
   ██╗ ██████╗ ████████╗    ██████╗      █████╗ ████████╗ ██████╗ 
   ██║██╔═══██╗╚══██╔══╝    ██╔══██╗    ██╔══██╗╚══██╔══╝██╔════╝ 
   ██║██║   ██║   ██║       ██████╔╝    ███████║   ██║   ██║  ███╗
   ██║██║   ██║   ██║       ██╔══██╗    ██╔══██║   ██║   ██║   ██║
   ██║╚██████╔╝   ██║       ██████╔╝    ██║  ██║   ██║   ╚██████╔╝
   ╚═╝ ╚═════╝    ╚═╝       ╚═════╝     ╚═╝  ╚═╝   ╚═╝    ╚═════╝ 
   
      IoT Benign & Attack Traffic Generator (B_ATG)
                     Version 0.1.0
  ═══════════════════════════════════════════════════════{Style.RESET_ALL}
"""

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
    },
    "8": {
        "name": "Benign Traffic",
        "path": "scenarios/benign",
        "count": 1,
        "description": "IoT baseline traffic generation"
    }
}


def print_banner():
    """Print the application banner."""
    print(BANNER)


def print_main_menu():
    """Print the main category selection menu."""
    print(f"\n{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}       Traffic Generation Categories{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")
    
    for key, cat in CATEGORIES.items():
        count_str = f"({cat['count']:2} scenario{'s' if cat['count'] > 1 else ' '})"
        print(f" {Fore.GREEN}[{key}]{Style.RESET_ALL} {cat['name']:<25} {Fore.CYAN}{count_str}{Style.RESET_ALL}")
    
    print(f" {Fore.RED}[9]{Style.RESET_ALL} Exit\n")
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
        scenario_num = yaml_file.stem
        
        description = "No description"
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'scenario' in data and 'description' in data['scenario']:
                    description = data['scenario']['description']
        except Exception:
            pass
        
        scenarios.append((scenario_num, yaml_file, description))
    
    return scenarios


def print_scenario_menu(category_name: str, scenarios: List[Tuple[str, Path, str]]):
    """Print compact scenario selection menu in columns."""
    print(f"\n{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  {category_name} - Select Scenario{Style.RESET_ALL}")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")
    
    num_scenarios = len(scenarios)
    for i in range(0, num_scenarios, 3):
        row = []
        for j in range(3):
            idx = i + j
            if idx < num_scenarios:
                num, _, _ = scenarios[idx]
                row.append(f" {Fore.GREEN}[{idx+1:2}]{Style.RESET_ALL} Scenario {num}")
            else:
                row.append(" " * 20)
        print("".join(f"{item:25}" for item in row))
    
    print(f"\n {Fore.YELLOW}[ 0]{Style.RESET_ALL} Back to main menu  |  {Fore.RED}[-1]{Style.RESET_ALL} Exit")


def print_benign_submenu():
    """Print benign traffic component selection submenu."""
    print(f"\n{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")
    print(f"{Fore.CYAN}  Benign Traffic - Select Component{Style.RESET_ALL}")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}\n")
    
    print(f" {Fore.GREEN}[1]{Style.RESET_ALL} IoT Device Swarm        Generate sensor traffic")
    print(f" {Fore.GREEN}[2]{Style.RESET_ALL} MQTT Bridge             Connect MQTT to database")
    print(f" {Fore.GREEN}[3]{Style.RESET_ALL} Infrastructure Setup    Verify/configure services\n")
    
    print(f" {Fore.YELLOW}[0]{Style.RESET_ALL} Back to main menu  |  {Fore.RED}[-1]{Style.RESET_ALL} Exit")
    print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Style.RESET_ALL}")


def show_benign_submenu(workspace: Path) -> Optional[list]:
    """
    Show benign traffic component submenu and return selected scenario.
    
    Returns:
        List with single scenario tuple, or None if user exits, or empty list if back
    """
    benign_components = {
        1: "01_device_swarm.yaml",
        2: "02_mqtt_bridge.yaml",
        3: "03_infrastructure.yaml"
    }
    
    while True:
        print_benign_submenu()
        
        component_choice = get_input("Select [1-3] or 0 (back) or -1 (exit):", range(0, 4))
        
        if component_choice == -1:
            return None
        
        if component_choice == 0:
            return []
        
        scenario_file = benign_components[component_choice]
        scenario_path = workspace / "scenarios" / "benign" / scenario_file
        
        if not scenario_path.exists():
            print(f"\n{Fore.RED}Scenario not found: {scenario_path}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            input()
            continue
        
        try:
            with open(scenario_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and 'scenario' in data and 'description' in data['scenario']:
                    description = data['scenario']['description']
                else:
                    description = "No description"
        except Exception:
            description = "No description"
        
        return [(scenario_path.stem, scenario_path, description)]


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
    
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Profile: {profile:<50}{Fore.CYAN}│{Style.RESET_ALL}")
    print(f"{Fore.CYAN}│{Style.RESET_ALL} Script:  {script:<50}{Fore.CYAN}│{Style.RESET_ALL}")
    print(f"{Fore.CYAN}└─────────────────────────────────────────────────────────────┘{Style.RESET_ALL}\n")


def detect_and_configure_placeholders(scenario_path: Path) -> Optional[Path]:
    """
    Detect placeholders in scenario and prompt for configuration.
    Creates a temporary configured YAML file.
    
    Placeholders can have default values in the original YAML.
    If user presses Enter without typing, the default is used.
    
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
    
    env_vars = {}
    defaults = {}
    
    # Extract ALL environment variables from runs
    if 'runs' in data:
        for run in data['runs']:
            if 'env' in run:
                for key, value in run['env'].items():
                    if isinstance(value, str):
                        env_vars[key] = value
                        # Extract default value
                        if '_PLACEHOLDER' in value:
                            # Remove _PLACEHOLDER suffix to get default
                            default_val = value.replace('_PLACEHOLDER', '').strip()
                            defaults[key] = default_val if default_val else ''
                        else:
                            # Value itself is the default
                            defaults[key] = value
    
    # Check for marker host placeholder
    if 'scenario' in data and 'markers' in data['scenario']:
        markers = data['scenario']['markers']
        if 'host' in markers and isinstance(markers['host'], str) and '_PLACEHOLDER' in markers['host']:
            env_vars['MARKER_HOST'] = markers['host']
            default_val = markers['host'].replace('_PLACEHOLDER', '').strip()
            defaults['MARKER_HOST'] = default_val if default_val else ''
    
    if not env_vars:
        return scenario_path
    
    # Prompt user for values
    print(f"\n{Fore.YELLOW}Configuration Required{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}")
    print(f"Press {Fore.GREEN}Enter{Style.RESET_ALL} to use default values shown in {Fore.CYAN}[brackets]{Style.RESET_ALL}\n")
    
    user_values = {}
    
    for key in sorted(env_vars.keys()):
        default = defaults.get(key, '')
        
        if default:
            prompt = f"{Fore.GREEN}{key}{Style.RESET_ALL} [{Fore.CYAN}{default}{Style.RESET_ALL}]: "
        else:
            prompt = f"{Fore.GREEN}{key}{Style.RESET_ALL} (required): "
        
        user_input = input(prompt).strip()
        
        # If empty and there's a default, use it
        if not user_input and default:
            user_values[key] = default
            print(f"  → Using default: {Fore.CYAN}{default}{Style.RESET_ALL}")
        # If empty and no default, require input
        elif not user_input and not default:
            print(f"  {Fore.RED}This value is required{Style.RESET_ALL}")
            # Re-prompt for this key
            while not user_input:
                user_input = input(prompt).strip()
                if not user_input:
                    print(f"  {Fore.RED}This value is required{Style.RESET_ALL}")
            user_values[key] = user_input
        # Use what user typed
        else:
            user_values[key] = user_input
    
    # Create temporary configured YAML
    try:
        # Replace placeholders in env
        if 'runs' in data:
            for run in data['runs']:
                if 'env' in run:
                    for key, value in run['env'].items():
                        if key in user_values:
                            run['env'][key] = user_values[key]
                
                # Resolve relative script paths to absolute
                if 'script' in run:
                    script_path = Path(run['script'])
                    if not script_path.is_absolute():
                        absolute_script = (scenario_path.parent / script_path).resolve()
                        run['script'] = str(absolute_script)
                
                # Resolve relative profile paths to absolute
                if 'profile' in run:
                    profile_path = Path(run['profile'])
                    if not profile_path.is_absolute():
                        absolute_profile = (scenario_path.parent / profile_path).resolve()
                        run['profile'] = str(absolute_profile)
                
                # Special handling for WORDLIST paths
                if 'env' in run and 'WORDLIST' in run['env']:
                    wordlist_value = run['env']['WORDLIST']
                    wordlist_path = Path(wordlist_value)
                    
                    if wordlist_path.is_absolute():
                        run['env']['WORDLIST'] = str(wordlist_path)
                    elif '/' not in wordlist_value and '\\' not in wordlist_value:
                        project_root = scenario_path.parent.parent.parent
                        search_paths = [
                            Path.cwd() / wordlist_value,
                            project_root / 'scripts' / 'attacks' / 'bruteforce' / wordlist_value,
                        ]
                        
                        found = False
                        for candidate in search_paths:
                            if candidate.exists():
                                run['env']['WORDLIST'] = str(candidate.resolve())
                                found = True
                                break
                        
                        if not found:
                            run['env']['WORDLIST'] = wordlist_value
                    else:
                        absolute_wordlist = (Path.cwd() / wordlist_path).resolve()
                        run['env']['WORDLIST'] = str(absolute_wordlist)
        
        # Replace marker host placeholder
        if 'MARKER_HOST' in user_values:
            if 'scenario' not in data:
                data['scenario'] = {}
            if 'markers' not in data['scenario']:
                data['scenario']['markers'] = {}
            data['scenario']['markers']['host'] = user_values['MARKER_HOST']
        
        # Create temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.yaml', prefix='iottrafficgen_')
        temp_file = Path(temp_path)
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        
        print(f"\n{Fore.GREEN}✓{Style.RESET_ALL} Configuration complete")
        print(f"{Fore.CYAN}{'─' * 60}{Style.RESET_ALL}\n")
        
        return temp_file
        
    except Exception as e:
        print(f"{Fore.RED}Error creating configured scenario: {e}{Style.RESET_ALL}")
        return None


def confirm_execution(scenario_path: Path) -> bool:
    """Ask user to confirm scenario execution."""
    print(f"{Fore.YELLOW}→{Style.RESET_ALL} Execute this scenario? [y/N]: ", end="")
    
    try:
        response = input().strip().lower()
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
        
        choice = get_input("Select [1-9]:", range(1, 10))
        
        if choice == 9 or choice == -1:
            print(f"\n{Fore.YELLOW}Exiting...{Style.RESET_ALL}")
            return None
        
        category = CATEGORIES[str(choice)]
        category_path = workspace / category["path"]
        
        if choice == 8:
            scenarios = show_benign_submenu(workspace)
            if scenarios is None:
                return None
            if len(scenarios) == 0:
                continue
        else:
            scenarios = scan_scenarios(category_path)
        
        if not scenarios:
            print(f"\n{Fore.RED}No scenarios found in {category_path}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            input()
            continue
        
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
                break
            
            scenario_num, selected_scenario, description = scenarios[scenario_choice - 1]
            
            print_scenario_details(scenario_num, selected_scenario, description)
            
            configured_scenario = detect_and_configure_placeholders(selected_scenario)
            
            if configured_scenario is None:
                print(f"{Fore.YELLOW}Returning to menu...{Style.RESET_ALL}\n")
                continue
            
            if confirm_execution(configured_scenario):
                return configured_scenario
            else:
                if configured_scenario != selected_scenario and configured_scenario.exists():
                    configured_scenario.unlink()
                continue