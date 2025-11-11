# hook-vlc.py
# PyInstaller hook for python-vlc to ensure self-contained VLC operation

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

    # Add VLC plugins directory
    plugins_dir = os.path.join(vlc_path, 'plugins')
    if os.path.exists(plugins_dir):
        datas.append((plugins_dir, 'vlc/plugins'))

    # Look for VLC libraries in the python-vlc package directory
    libvlc_path = None
    try:
        # Try to get the VLC DLL path from the vlc module
        if hasattr(vlc, 'dll') and hasattr(vlc.dll, '_name'):
            dll_path = vlc.dll._name
            if os.path.exists(dll_path):
                libvlc_path = os.path.dirname(dll_path)
    except:
        pass

    # Fallback: look for libvlc in the vlc package directory
    if not libvlc_path:
        lib_dir = os.path.join(vlc_path, 'lib')
        if os.path.exists(lib_dir):
            libvlc_path = lib_dir

    # Additional fallback: look for libvlc.dll in common locations
    if not libvlc_path:
        possible_paths = [
            r'C:\Program Files\VideoLAN\VLC',
            r'C:\Program Files (x86)\VideoLAN\VLC',
            os.path.join(sys.base_prefix, 'Lib', 'site-packages', 'vlc'),
            vlc_path,  # Check in the vlc package directory itself
        ]
        for path in possible_paths:
            dll_path = os.path.join(path, 'libvlc.dll')
            if os.path.exists(dll_path):
                libvlc_path = path
                break

    if libvlc_path and os.path.exists(libvlc_path):
        # Add all VLC-related DLLs and libraries
        for root, dirs, files in os.walk(libvlc_path):
            for file in files:
                if file.endswith(('.dll', '.so', '.dylib', '.lib')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(root, libvlc_path)
                    if rel_path == '.':
                        binaries.append((full_path, '.'))
                    else:
                        binaries.append((full_path, rel_path))

        # Add plugins directory if it exists
        plugins_path = os.path.join(libvlc_path, 'plugins')
        if os.path.exists(plugins_path):
            datas.append((plugins_path, 'vlc/plugins'))

        # Add locale files if they exist
        locale_path = os.path.join(libvlc_path, 'locale')
        if os.path.exists(locale_path):
            datas.append((locale_path, 'vlc/locale'))

except ImportError:
    pass

# Ensure VLC is included in hidden imports
hiddenimports = [
    'vlc',
    'vlc.libvlc',
    'vlc.libvlc_audio',
    'vlc.libvlc_media',
    'vlc.libvlc_media_player',
    'vlc.libvlc_instance',
    'vlc.libvlc_media_discoverer',
    'vlc.libvlc_media_library',
    'vlc.libvlc_media_list',
    'vlc.libvlc_media_list_player',
    'vlc.libvlc_renderer_discoverer',
    'vlc.libvlc_vlm'
] + collect_submodules('vlc')
