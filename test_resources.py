#!/usr/bin/env python3
# test_resources.py
from resource_helper import initialize_resources, get_working_path, debug_resource_paths, list_available_files
import os

def test_resources():
    """اختبار وجود الموارد"""
    print("=== اختبار الموارد ===")
    
    # عرض معلومات التصحيح
    debug_resource_paths()
    print()
    
    # تحضير الموارد
    resources = initialize_resources()
    print()
    
    # اختبار الملفات المحددة
    specific_files = [
        "sounds/adhan_mekka.wma",
        "sounds/notification.wav",
        "world_cities/cities.json",  # أو أي ملف في مجلد المدن
        "countries.json",
        "pray_logo.png",
        "pray_times.ico"
    ]
    
    print("=== اختبار ملفات محددة ===")
    for file in specific_files:
        path = get_working_path(file)
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        print(f"{'✓' if exists else '✗'} {file}")
        print(f"   المسار: {path}")
        print(f"   الحجم: {size} بايت")
        print()
    
    # عرض محتويات المجلدات
    print("=== محتويات المجلدات ===")
    list_available_files("sounds")
    print()
    list_available_files("world_cities")

if __name__ == "__main__":
    test_resources()
