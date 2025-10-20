
# hook-pathlib.py
# خطاف PyInstaller للتعامل مع مشكلة pathlib

from PyInstaller.utils.hooks import collect_data_files

# التأكد من تضمين pathlib بشكل صحيح
hiddenimports = [
    'pathlib',
    'pathlib._abc',
    'pathlib._local',
    'pathlib._os',
    'pathlib._posix',
    'pathlib._windows',
    'pathlib._url',
    'pathlib._py_3.9',
]

# استبعاد الإصدارات غير المتوافقة
excludedimports = [
    'setuptools.glob',
]
