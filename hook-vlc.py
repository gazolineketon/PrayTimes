# hook-vlc.py
# PyInstaller hook for python-vlc

import os
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files

# Collect VLC dynamic libraries
binaries = collect_dynamic_libs('vlc')

# Collect VLC data files (if any)
datas = collect_data_files('vlc')

# Add VLC plugins directory if it exists
try:
    import vlc
    vlc_path = os.path.dirname(vlc.__file__)
    plugins_dir = os.path.join(vlc_path, 'plugins')
    if os.path.exists(plugins_dir):
        datas.append((plugins_dir, 'vlc/plugins'))
except ImportError:
    pass

# Ensure VLC is included in hidden imports
hiddenimports = ['vlc', 'vlc.libvlc']
