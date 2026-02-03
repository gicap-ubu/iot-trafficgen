#!/usr/bin/env python3
"""
Add DURATION_SECONDS_PLACEHOLDER to attack scenario YAMLs
"""
import sys
from pathlib import Path
import yaml

# Scenarios that need DURATION_SECONDS
NEEDS_DURATION = [
    'denial_of_service',           # SYN Flood, ICMP Flood, MQTT Flood
    'dns_beacon',    # DNS Beaconing
    'mitm',      # ARP Spoofing
    'mqtt_inj',      # MQTT Injection
]

def add_duration_to_yaml(yaml_path: Path) -> bool:
    """Add DURATION_SECONDS_PLACEHOLDER to a YAML file if not present."""
    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if not data or 'runs' not in data:
            return False
        
        modified = False
        for run in data['runs']:
            if 'env' not in run:
                continue
            
            # Check if DURATION_SECONDS already exists
            if 'DURATION_SECONDS' not in run['env']:
                # Add it after the last placeholder or at the end
                run['env']['DURATION_SECONDS'] = 'DURATION_SECONDS_PLACEHOLDER'
                modified = True
                print(f"  Added DURATION_SECONDS to {yaml_path.name}")
        
        if modified:
            with open(yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        
        return modified
    
    except Exception as e:
        print(f"  ERROR processing {yaml_path}: {e}")
        return False

def main():
    scenarios_dir = Path('scenarios')
    
    if not scenarios_dir.exists():
        print("ERROR: scenarios/ directory not found")
        print("Run this script from the project root directory")
        sys.exit(1)
    
    total_modified = 0
    
    for category in NEEDS_DURATION:
        category_dir = scenarios_dir / category
        
        if not category_dir.exists():
            print(f"WARNING: {category_dir} not found, skipping")
            continue
        
        print(f"\nProcessing {category}/")
        
        yaml_files = sorted(category_dir.glob('*.yaml'))
        
        if not yaml_files:
            print(f"  No YAML files found")
            continue
        
        for yaml_file in yaml_files:
            if add_duration_to_yaml(yaml_file):
                total_modified += 1
    
    print(f"\n✓ Modified {total_modified} files")
    print("\nNext steps:")
    print("  git add scenarios/")
    print('  git commit -m "feat: Add DURATION_SECONDS to timed attack scenarios"')
    print("  git push origin main")

if __name__ == '__main__':
    main()