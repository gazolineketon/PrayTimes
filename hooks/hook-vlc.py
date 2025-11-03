# hook-vlc.py
# PyInstaller hook for python-vlc

import os
import sys
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_data_files, collect_submodules

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

    # Add VLC library directory for additional DLLs
    libvlc_path = None
    try:
        libvlc_path = vlc.dll._name  # Try to get the VLC DLL path
    except:
        # Fallback: look for libvlc.dll in common locations
        possible_paths = [
            r'C:\Program Files\VideoLAN\VLC',
            r'C:\Program Files (x86)\VideoLAN\VLC',
            os.path.join(sys.base_prefix, 'Lib', 'site-packages', 'vlc'),
        ]
        for path in possible_paths:
            dll_path = os.path.join(path, 'libvlc.dll')
            if os.path.exists(dll_path):
                libvlc_path = path
                break

    if libvlc_path and os.path.exists(libvlc_path):
        # Add the entire VLC directory to binaries
        for root, dirs, files in os.walk(libvlc_path):
            for file in files:
                if file.endswith(('.dll', '.so', '.dylib')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(root, libvlc_path)
                    if rel_path == '.':
                        binaries.append((full_path, '.'))
                    else:
                        binaries.append((full_path, rel_path))

        # Add plugins directory
        plugins_path = os.path.join(libvlc_path, 'plugins')
        if os.path.exists(plugins_path):
            datas.append((plugins_path, 'vlc/plugins'))

except ImportError:
    pass

# Ensure VLC is included in hidden imports
hiddenimports = ['vlc', 'vlc.libvlc', 'vlc.libvlc_audio', 'vlc.libvlc_media', 'vlc.libvlc_media_player', 'vlc.libvlc_instance'] + collect_submodules('vlc')
