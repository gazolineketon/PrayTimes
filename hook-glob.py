
# hook-glob.py
# خطاف PyInstaller للتعامل مع مشكلة تعارض glob مع setuptools

import os
import sys
from PyInstaller.utils.hooks import collect_data_files

# استبعاد مكتبة glob من setuptools
hiddenimports = [
    'glob',
    'pathlib',
    'pathlib._abc',
]

# التأكد من عدم استخدام glob من setuptools
excludedimports = [
    'setuptools.glob',
]
