#!/usr/bin/env python3
"""Update README.md version badge from version.py (single source of truth)."""

import re
from pathlib import Path
from version import __version__

def update_readme_badge():
    """Update the version badge in README.md to match version.py."""
    readme_path = Path(__file__).parent / "README.md"
    
    if not readme_path.exists():
        print(f"Error: {readme_path} not found")
        return False
    
    # Read README
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update version badge
    # Pattern: ![Version](https://img.shields.io/badge/version-<version>-blue.svg)
    # Match any version number in the badge
    pattern = r'!\[Version\]\(https://img\.shields\.io/badge/version-([\d.]+)-blue\.svg\)'
    replacement = f'![Version](https://img.shields.io/badge/version-{__version__}-blue.svg)'
    
    new_content = re.sub(pattern, replacement, content)
    
    # Check if version was actually updated
    if re.search(rf'version-{re.escape(__version__)}-blue\.svg', new_content):
        if new_content == content:
            print(f"README.md version badge already shows {__version__}")
            return True
        else:
            print(f"Updated README.md version badge to {__version__}")
            # Write back
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    else:
        print(f"Error: Could not find or update version badge pattern")
        return False
    
    # Write back
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"Updated README.md version badge to {__version__}")
    return True

if __name__ == "__main__":
    update_readme_badge()
