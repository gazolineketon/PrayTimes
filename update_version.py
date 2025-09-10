# -*- coding: utf-8 -*-
import re
import subprocess
from pathlib import Path

def update_version():
    """
    This script automatically updates the __version__ in main.py
    based on the total number of git commits.
    """
    try:
        # Get the total number of commits
        commit_count = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD']).strip().decode('utf-8')
        
        # Define the new version string
        new_version = f"0.{commit_count}.0"
        
        # Path to main.py
        main_py_path = Path(__file__).parent / 'main.py'
        
        # Read the content of main.py
        content = main_py_path.read_text(encoding='utf-8')
        
        # Find and replace the version
        old_version_pattern = re.compile(r'__version__\s*=\s*"[^"]+"')
        if old_version_pattern.search(content):
            new_content = old_version_pattern.sub(f'__version__ = "{new_version}"', content)
            
            # Write the updated content back to main.py
            main_py_path.write_text(new_content, encoding='utf-8')
            
            print(f"Successfully updated version to {new_version}")
        else:
            print("Error: __version__ variable not found in main.py")

    except FileNotFoundError:
        print("Error: 'git' command not found. Make sure Git is installed and in your PATH.")
    except subprocess.CalledProcessError:
        print("Error: Not a git repository or no commits found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    update_version()
