# hook-pkg_resources.py
# Disable pkg_resources hook to prevent setuptools interference

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Don't collect any pkg_resources submodules
hiddenimports = []

# Don't collect any data files
datas = []

# Disable the pkg_resources runtime hook
excludedimports = ['pkg_resources']

def pre_safe_import_module(api):
    # Block pkg_resources imports during analysis
    if api.__name__ == 'pkg_resources':
        return None
    return api
