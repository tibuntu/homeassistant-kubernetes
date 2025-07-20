#!/usr/bin/env python3
"""
Update documentation links script.

This script updates various documentation links to ensure they point to the correct
repository URLs and are consistent across the project.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


def get_repo_url() -> str:
    """Get the repository URL from git remote."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=True
        )
        repo_url = result.stdout.strip()
        # Convert SSH URL to HTTPS if needed
        if repo_url.startswith("git@"):
            repo_url = repo_url.replace("git@github.com:", "https://github.com/")
        return repo_url
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to a default URL
        return "https://github.com/your-username/homeassistant-kubernetes"


def update_file_links(file_path: Path, repo_url: str) -> bool:
    """Update links in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Warning: Could not read {file_path} as UTF-8, skipping...")
        return False

    original_content = content
    changes_made = False

    # Clean up repo_url for comparisons
    clean_repo_url = repo_url.replace('.git', '')
    repo_name = clean_repo_url.split('/')[-1]

    # Update repository URLs in documentation
    patterns = [
        # Update clone URLs (only if they contain placeholder)
        (r'git clone https://github\.com/your-username/homeassistant-kubernetes\.git',
         f'git clone {repo_url}'),

        # Update repository references (only if they contain placeholder)
        (r'https://github\.com/your-username/homeassistant-kubernetes',
         clean_repo_url),

        # Update placeholder usernames (only if they're actually placeholders)
        (r'your-username',
         repo_name if repo_name == 'homeassistant-kubernetes' else 'your-username'),
    ]

    for pattern, replacement in patterns:
        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            changes_made = True

    # Update specific documentation links
    if file_path.name == 'DEVELOPMENT.md':
        # Update Home Assistant documentation links to latest versions
        ha_doc_patterns = [
            (r'https://developers\.home-assistant\.io/docs/creating_integration_manifest/',
             'https://developers.home-assistant.io/docs/creating_integration_manifest/'),
            (r'https://developers\.home-assistant\.io/docs/architecture_index/',
             'https://developers.home-assistant.io/docs/architecture_index/'),
        ]

        for pattern, replacement in ha_doc_patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                changes_made = True

    if changes_made:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {file_path}")
            return True
        except Exception as e:
            print(f"Error writing to {file_path}: {e}")
            return False

    return False


def main():
    """Main function to update documentation links."""
    print("Updating documentation links...")

    # Get repository URL
    repo_url = get_repo_url()
    print(f"Repository URL: {repo_url}")

    # Files to check for link updates
    doc_files = [
        Path("README.md"),
        Path("docs/DEVELOPMENT.md"),
    ]

    # Additional files that might contain links
    additional_files = [
        Path("custom_components/kubernetes/manifest.json"),
    ]

    all_files = doc_files + additional_files

    changes_made = False

    for file_path in all_files:
        if file_path.exists():
            if update_file_links(file_path, repo_url):
                changes_made = True
        else:
            print(f"Warning: {file_path} does not exist, skipping...")

    if changes_made:
        print("Documentation links updated successfully!")
        return 0
    else:
        print("No changes were needed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
