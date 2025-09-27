# hook-setuptools.py
# Prevent setuptools from interfering with standard library modules

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import sys

# Don't collect any setuptools submodules to prevent interference
hiddenimports = []

# Don't collect any data files
datas = []

# Block setuptools imports during analysis
def pre_safe_import_module(api):
    # Prevent setuptools from being imported during analysis
    if api.__name__ == 'setuptools':
        return None
    return api

# Ensure glob uses standard library
def pre_find_module_path(api):
    if api.__name__ == 'glob':
        # Force glob to use standard library path
        import glob
        if hasattr(glob, '__file__'):
            api.__path__ = [glob.__file__]
    return api
