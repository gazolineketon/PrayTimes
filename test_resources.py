import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from resource_helper import get_working_path, get_resource_path

print("Testing resource paths...")

# Test sound files
sound_files = ['sounds/adhan_mekka.wma', 'sounds/notification.wav']

for sound_file in sound_files:
    working_path = get_working_path(sound_file)
    resource_path = get_resource_path(sound_file)

    print(f"\nFile: {sound_file}")
    print(f"Working path: {working_path}")
    print(f"Resource path: {resource_path}")
    print(f"Working path exists: {os.path.exists(working_path)}")
    print(f"Resource path exists: {os.path.exists(resource_path)}")

# Check APPDATA directory
from resource_helper import get_app_data_dir
app_data_dir = get_app_data_dir()
print(f"\nAPPDATA directory: {app_data_dir}")
print(f"APPDATA exists: {os.path.exists(app_data_dir)}")

# Check if sounds directory exists in APPDATA
sounds_in_appdata = os.path.join(app_data_dir, 'sounds')
print(f"Sounds in APPDATA: {sounds_in_appdata}")
print(f"Sounds in APPDATA exists: {os.path.exists(sounds_in_appdata)}")

if os.path.exists(sounds_in_appdata):
    print("Files in APPDATA sounds:")
    for f in os.listdir(sounds_in_appdata):
        print(f"  {f}")
