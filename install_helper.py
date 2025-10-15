
# install_helper.py
# مساعد للتثبيت والتعامل مع مشاكل التبعيات المفقودة

import os
import sys
import subprocess
import platform
import tempfile
import shutil
import logging

try:
    import psutil
except ImportError:  # التعامل مع عدم توفر psutil
    psutil = None

logger = logging.getLogger(__name__)

def check_system_requirements():
    """فحص متطلبات النظام"""
    system_info = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
    }

    # إضافة معلومات الذاكرة إذا كانت psutil متوفرة
    if psutil is not None:
        try:
            total_ram_gb = round(psutil.virtual_memory().total / (1024.0 ** 3))
            system_info["ram"] = f"{total_ram_gb} GB"
        except Exception as exc:
            logger.debug(f"تعذر قراءة الذاكرة عبر psutil: {exc}")
    else:
        logger.info("psutil غير مثبت؛ سيتم تخطي معلومات الذاكرة.")

    return system_info

def install_visual_cpp_redistributable():
    """تثبيت Visual C++ Redistributable إذا لزم الأمر"""
    try:
        # تحقق مما إذا كان Visual C++ مثبتًا
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        vcpp_installed = False

        for i in range(1024):
            try:
                subkey_name = winreg.EnumKey(key, i)
                if "Visual C++" in subkey_name:
                    vcpp_installed = True
                    break
            except WindowsError:
                break

        winreg.CloseKey(key)

        if not vcpp_installed:
            # تثبيت Visual C++ Redistributable
            logger.info("محاولة تثبيت Visual C++ Redistributable...")
            # هنا يمكن إضافة كود لتنزيل وتثبيت الحزمة
            return False
        return True
    except Exception as e:
        logger.error(f"خطأ في فحص Visual C++ Redistributable: {e}")
        return False

def create_portable_python_environment():
    """إنشاء بيئة بايثون محمولة مدمجة مع التطبيق"""
    if getattr(sys, 'frozen', False):
        return True  # التطبيق مجمد بالفعل

    try:
        # إنشاء مجلد مؤقت للبيئة المحمولة
        portable_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "python_portable")
        if not os.path.exists(portable_dir):
            os.makedirs(portable_dir)

        # هنا يمكن إضافة كود لتنزيل وتثبيت بايثون محمول
        # أو نسخ بايثون من الجهاز الحالي

        return True
    except Exception as e:
        logger.error(f"خطأ في إنشاء بيئة بايثون محمولة: {e}")
        return False

def handle_missing_dlls():
    """معالجة ملفات DLL المفقودة"""
    try:
        # قائمة بملفات DLL الشائعة المطلوبة
        required_dlls = [
            "vcruntime140.dll",
            "msvcp140.dll",
            "python3.dll",
            "python39.dll"  # استبدل بالنسخة المناسبة
        ]

        missing_dlls = []

        # التحقق من وجود الملفات
        for dll in required_dlls:
            if not any(os.path.exists(os.path.join(p, dll)) 
                      for p in sys.path + [os.getcwd(), os.path.dirname(sys.executable)]):
                missing_dlls.append(dll)

        if missing_dlls:
            logger.warning(f"ملفات DLL مفقودة: {missing_dlls}")
            # هنا يمكن إضافة كود لتنزيل الملفات المفقودة أو نسخها

        return len(missing_dlls) == 0
    except Exception as e:
        logger.error(f"خطأ في فحص ملفات DLL: {e}")
        return False

def setup_application_environment():
    """إعداد بيئة التطبيق"""
    try:
        # التأكد من وجود مجلدات التطبيق
        required_dirs = ["sounds", "images", "locales"]
        for dir_name in required_dirs:
            dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), dir_name)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"تم إنشاء مجلد: {dir_name}")

        return True
    except Exception as e:
        logger.error(f"خطأ في إعداد بيئة التطبيق: {e}")
        return False

def main():
    """الوظيفة الرئيسية للمساعد"""
    logger.info("بدء فحص متطلبات النظام...")
    system_info = check_system_requirements()
    logger.info(f"معلومات النظام: {system_info}")

    logger.info("فحص وتثبيت متطلبات النظام...")
    install_visual_cpp_redistributable()

    logger.info("معالجة ملفات DLL المفقودة...")
    handle_missing_dlls()

    logger.info("إعداد بيئة التطبيق...")
    setup_application_environment()

    logger.info("اكتمل فحص متطلبات النظام")

if __name__ == "__main__":
    main()
