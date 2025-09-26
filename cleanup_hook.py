import os
import sys
import atexit

def cleanup_pyinstaller():
    """تنظيف محسن لـ PyInstaller"""
    import gc
    import time
    
    # جمع القمامة
    gc.collect()
    
    # انتظار قصير
    time.sleep(0.1)
    
    print("تنظيف PyInstaller مكتمل")

if hasattr(sys, '_MEIPASS'):
    atexit.register(cleanup_pyinstaller)
