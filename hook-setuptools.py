# hook-setuptools.py
# منع setuptools من التدخل في وحدات المكتبة القياسية

from PyInstaller.utils.hooks import collect_submodules, collect_data_files
import sys

# لا تقم بجمع أي وحدات فرعية لـ setuptools لمنع التدخل
hiddenimports = []

# لا تقم بجمع أي ملفات بيانات
datas = []

# حظر استيراد setuptools أثناء التحليل
def pre_safe_import_module(api):
    # منع setuptools من الاستيراد أثناء التحليل
    if api.__name__ == 'setuptools' or api.__name__ == 'setuptools.config':
        return None
    return api

# إجبار glob على استخدام المكتبة القياسية
def pre_find_module_path(api):
    if api.__name__ == 'glob':
        # إجبار glob على استخدام مسار المكتبة القياسية
        import glob
        if hasattr(glob, '__file__'):
            api.__path__ = [glob.__file__]
    elif api.__name__ == 'setuptools.config':
        # منع setuptools.config من الاستيراد
        return None
    return api

# استبعاد المكونات المسببة للمشاكل
excludedimports = [
    'setuptools.config',
    'setuptools.config.setup',
    'setuptools.glob',
]

# منع الاستيرادات النسبية في setuptools
def hook(mod):
    if mod.name.startswith('setuptools.config'):
        mod.__spec__ = None
    return mod
