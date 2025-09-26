# runtime_hook.py
# إصلاح مسارات PIL للتطبيقات المجمدة

import sys
import os

# إضافة مجلد التطبيق إلى sys.path لضمان استخدام PIL المضمن
if hasattr(sys, '_MEIPASS'):
    app_dir = sys._MEIPASS

    # إضافة مجلد PIL المضمن إلى sys.path أولاً
    pil_path = os.path.join(app_dir, 'PIL')
    if os.path.exists(pil_path):
        if pil_path not in sys.path:
            sys.path.insert(0, pil_path)

        # تعيين متغيرات البيئة لتوجيه PIL
        os.environ['PILLOW_ROOT'] = pil_path

        # محاولة إعادة توجيه استيراد PIL إذا كان قد تم استيراده
        if 'PIL' in sys.modules:
            try:
                import importlib
                # إعادة تحميل PIL من المسار الصحيح
                spec = importlib.util.spec_from_file_location("PIL", os.path.join(pil_path, '__init__.py'))
                if spec and spec.loader:
                    new_pil = importlib.util.module_from_spec(spec)
                    # حفظ الوحدات الفرعية الموجودة
                    old_submodules = {}
                    for name, module in sys.modules.items():
                        if name.startswith('PIL.') and module is not None:
                            old_submodules[name] = module

                    sys.modules['PIL'] = new_pil
                    spec.loader.exec_module(new_pil)

                    # إعادة ربط الوحدات الفرعية
                    for name, module in old_submodules.items():
                        if hasattr(new_pil, name.split('.')[-1]):
                            setattr(new_pil, name.split('.')[-1], module)
            except Exception as e:
                print(f"فشل في إعادة توجيه PIL: {e}")

    # التأكد من أن PIL يستخدم المسار الصحيح
    try:
        import PIL
        if hasattr(PIL, '__file__'):
            bundled_pil_init = os.path.join(pil_path, '__init__.py')
            if os.path.exists(bundled_pil_init):
                PIL.__file__ = bundled_pil_init
    except ImportError:
        pass

    # إضافة مجلد setuptools المضمن إلى sys.path أولاً
    setuptools_path = os.path.join(app_dir, 'setuptools')
    if os.path.exists(setuptools_path):
        if setuptools_path not in sys.path:
            sys.path.insert(0, setuptools_path)

        # التأكد من أن setuptools يستخدم المسار الصحيح
        try:
            import setuptools
            if hasattr(setuptools, '__file__'):
                bundled_setuptools_init = os.path.join(setuptools_path, '__init__.py')
                if os.path.exists(bundled_setuptools_init):
                    setuptools.__file__ = bundled_setuptools_init
        except ImportError:
            pass

        # التأكد من أن pkg_resources يستخدم المسار الصحيح
        try:
            import pkg_resources
            if hasattr(pkg_resources, '__file__'):
                bundled_pkg_resources_init = os.path.join(setuptools_path, '_vendor', 'pkg_resources', '__init__.py')
                if os.path.exists(bundled_pkg_resources_init):
                    pkg_resources.__file__ = bundled_pkg_resources_init
        except ImportError:
            pass

    # إصلاح مشكلة glob module التي يسببها setuptools
    try:
        import glob
        # التأكد من أن glob يستخدم الوحدة القياسية وليس setuptools
        if hasattr(glob, '__file__') and 'setuptools' in glob.__file__:
            # إعادة استيراد glob من المكتبة القياسية
            import importlib
            import sys
            # حذف glob من sys.modules لإجبار إعادة الاستيراد
            if 'glob' in sys.modules:
                del sys.modules['glob']
            # إعادة استيراد glob
            import glob
    except Exception as e:
        print(f"فشل في إصلاح glob: {e}")
