
import sys
import os

def check_dirs():
    python_path = sys.base_prefix
    print(f"Base Prefix: {python_path}")
    
    paths_to_check = [
        os.path.join(python_path, 'tcl'),
        os.path.join(python_path, 'tcl', 'tcl8.6'),
        os.path.join(python_path, 'Library', 'lib'),
        os.path.join(python_path, 'Library', 'lib', 'tcl8.6'),
    ]
    
    for p in paths_to_check:
        if os.path.exists(p):
            print(f"Exists: {p}")
            if os.path.isdir(p):
                print(f"Contents of {os.path.basename(p)}: {os.listdir(p)[:5]}")

if __name__ == "__main__":
    check_dirs()
