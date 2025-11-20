
import sys
import os
import glob

def check_tcl_tk():
    print(f"Python Executable: {sys.executable}")
    print(f"Prefix: {sys.prefix}")
    print(f"Base Prefix: {sys.base_prefix}")
    
    search_paths = [
        os.path.join(sys.prefix, 'DLLs'),
        os.path.join(sys.prefix, 'Library', 'bin'),
        os.path.join(sys.base_prefix, 'DLLs'),
        os.path.join(sys.base_prefix, 'Library', 'bin'),
    ]
    
    print("\nSearching for TCL/TK DLLs:")
    for path in search_paths:
        if os.path.exists(path):
            print(f"\nChecking in: {path}")
            tcl_dlls = glob.glob(os.path.join(path, 'tcl*.dll'))
            tk_dlls = glob.glob(os.path.join(path, 'tk*.dll'))
            tkinter_pyd = glob.glob(os.path.join(path, '_tkinter.pyd'))
            
            for dll in tcl_dlls:
                print(f"  Found TCL: {os.path.basename(dll)}")
            for dll in tk_dlls:
                print(f"  Found TK: {os.path.basename(dll)}")
            for pyd in tkinter_pyd:
                print(f"  Found _tkinter: {os.path.basename(pyd)}")

if __name__ == "__main__":
    check_tcl_tk()
