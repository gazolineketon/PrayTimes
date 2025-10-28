# hook-pkg_resources.py
# تعطيل خطاف pkg_resources لمنع تدخل setuptools

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# لا تقم بجمع أي وحدات فرعية لـ pkg_resources
hiddenimports = []

# لا تقم بجمع أي ملفات بيانات
datas = []

# تعطيل خطاف تشغيل pkg_resources
excludedimports = ['pkg_resources']

def pre_safe_import_module(api):
    # حظر استيراد pkg_resources أثناء التحليل
    if api.__name__ == 'pkg_resources':
        return None
    return api
