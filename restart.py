"""
restart.py
معالج إعادة تشغيل التطبيق: ينتظر حتى تغلق العملية الأم ثم يعيد تشغيل التطبيق مرة أخرى
"""

import sys
import os
import time
import subprocess
import logging
import json
import traceback

# تكوين السجل
log_dir = os.path.join(os.path.expanduser("~"), ".praytimes")
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, "restart_log.txt")

logging.basicConfig(
    filename=log_file_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("restart")

def is_process_running(pid):
    """التحقق مما إذا كانت العملية بالمعرف المحدد لا تزال قيد التشغيل"""
    try:
        if sys.platform == "win32":
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # استخدام صلاحية PROCESS_QUERY_LIMITED_INFORMATION للوصول الأفضل في Windows
            handle = kernel32.OpenProcess(0x1000, 0, pid)
            if handle == 0:
                logger.debug(f"لا يمكن فتح العملية {pid} - ربما تكون قد انتهت بالفعل")
                return False
            
            exit_code = ctypes.c_ulong()
            try:
                # التحقق مما إذا كانت العملية نشطة
                if kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)) and exit_code.value == 259:  # STILL_ACTIVE
                    return True
                logger.debug(f"العملية {pid} موجودة ولكنها ليست نشطة، رمز الخروج: {exit_code.value}")
                return False
            finally:
                kernel32.CloseHandle(handle)
        else:
            # للأنظمة الشبيهة بـ Unix
            try:
                os.kill(pid, 0)
                return True
            except OSError:
                return False
    except Exception as e:
        logger.error(f"خطأ أثناء التحقق من حالة العملية {pid}: {e}")
        return False

def detect_executable_environment():
    """الكشف عما إذا كان التطبيق يعمل كملف تنفيذي أو كبرنامج نصي"""
    is_frozen = getattr(sys, 'frozen', False)
    is_pyinstaller = is_frozen and hasattr(sys, '_MEIPASS')
    is_script = not is_frozen
    
    executable_path = sys.executable
    script_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    return {
        'is_frozen': is_frozen,
        'is_pyinstaller': is_pyinstaller,
        'is_script': is_script,
        'executable_path': executable_path,
        'script_path': script_path
    }

def restart_app():
    """
    تنتظر حتى تنتهي العملية الأم ثم تعيد تشغيل التطبيق
    مع دعم محسن لـ PyInstaller
    """
    try:
        logger.info("=== بدء جلسة إعادة تشغيل جديدة ===")
        logger.info(f"وسيطات النظام: {sys.argv}")
        logger.info(f"مسار البرنامج التنفيذي: {sys.executable}")

        if len(sys.argv) < 3:
            logger.error(f"عدد غير كافٍ من الوسيطات: {len(sys.argv)}")
            return

        # اكتشاف بيئة التشغيل
        env_info = detect_executable_environment()
        logger.info(f"معلومات بيئة التشغيل: {json.dumps(env_info)}")

        main_path = sys.argv[1]
        parent_pid = int(sys.argv[2])
        
        logger.info(f"مسار البرنامج الرئيسي: {main_path}")
        logger.info(f"معرف العملية الأم: {parent_pid}")

        # انتظار انتهاء العملية الأم
        max_wait_seconds = 30  # زيادة وقت الانتظار لـ PyInstaller على الأجهزة منخفضة الصلاحية
        logger.info("انتظار انتهاء العملية الأم...")

        wait_count = 0
        for i in range(max_wait_seconds * 4):  # فحص كل 0.25 ثانية
            if not is_process_running(parent_pid):
                logger.info(f"العملية الأم {parent_pid} توقفت (بعد {i*0.25:.2f} ثانية).")
                break
            time.sleep(0.25)
            wait_count += 1

            # عرض تقدم الانتظار
            if wait_count % 20 == 0:  # كل 5 ثوانٍ
                logger.info(f"لا تزال تنتظر انتهاء العملية {parent_pid}... ({wait_count/4:.1f}s)")
        else:
            logger.warning(f"العملية الأم {parent_pid} لا تزال تعمل بعد {max_wait_seconds} ثوانٍ.")
            logger.warning("محاولة المتابعة على أية حال...")

        # انتظار إضافي لتحرير موارد النظام (خاصة مع PyInstaller)
        wait_time = 5 if env_info['is_pyinstaller'] else 2
        logger.info(f"انتظار تحرير موارد النظام ({wait_time} ثانية)...")
        time.sleep(wait_time)

        # تنظيف آمن للمجلدات المؤقتة الحديثة قبل إعادة التشغيل
        if env_info['is_pyinstaller']:
            try:
                from temp_manager import temp_manager
                logger.info("تنظيف مجلدات _MEI الحديثة قبل إعادة التشغيل...")
                temp_manager.safe_cleanup_recent_mei(max_age=600)  # 10 دقائق
                time.sleep(2)  # انتظار إضافي بعد التنظيف الأول
                temp_manager.safe_cleanup_recent_mei(max_age=600)  # محاولة تنظيف ثانية
            except Exception as e:
                logger.warning(f"فشل في تنظيف المجلدات المؤقتة: {e}")

        # إعادة تشغيل التطبيق حسب نوع البيئة
        if env_info['is_pyinstaller'] or os.path.isfile(main_path) and main_path.lower().endswith('.exe'):
            # للملفات التنفيذية، تشغيل المسار مباشرة
            logger.info(f"إعادة تشغيل التطبيق كملف تنفيذي: {main_path}")
            try:
                if sys.platform == "win32":
                    # في Windows، استخدام أعلام خاصة لإنشاء نافذة جديدة
                    CREATE_NO_WINDOW = 0x08000000
                    DETACHED_PROCESS = 0x00000008
                    # Validate and normalize paths
                    main_path_abs = os.path.abspath(main_path)
                    if not os.path.isfile(main_path_abs):
                        raise FileNotFoundError(f"Executable not found: {main_path_abs}")
                        
                    subprocess.Popen([main_path_abs], 
                                  creationflags=DETACHED_PROCESS,
                                  cwd=os.path.dirname(main_path_abs))
                else:
                    main_path_abs = os.path.abspath(main_path)
                    if not os.path.isfile(main_path_abs):
                        raise FileNotFoundError(f"Executable not found: {main_path_abs}")
                        
                    subprocess.Popen([main_path_abs],
                                  cwd=os.path.dirname(main_path_abs))
                logger.info("تم إعادة تشغيل الملف التنفيذي بنجاح.")
            except Exception as e:
                logger.error(f"فشل في إعادة تشغيل الملف التنفيذي: {e}")
                logger.error(traceback.format_exc())
                # محاولة بديلة باستخدام python.exe إذا كان متاحاً
                try:
                    python_exe = os.path.join(os.path.dirname(sys.executable), 'python.exe')
                    if os.path.exists(python_exe):
                        logger.info(f"محاولة إعادة التشغيل باستخدام python.exe: {python_exe} {main_path}")
                        # Validate python executable and script paths
                        python_exe_abs = os.path.abspath(python_exe)
                        main_path_abs = os.path.abspath(main_path)
                        
                        if not os.path.isfile(python_exe_abs):
                            raise FileNotFoundError(f"Python executable not found: {python_exe_abs}")
                        if not os.path.isfile(main_path_abs):
                            raise FileNotFoundError(f"Script not found: {main_path_abs}")
                        
                        subprocess.Popen([python_exe_abs, main_path_abs], 
                                      creationflags=DETACHED_PROCESS,
                                      cwd=os.path.dirname(main_path_abs))
                        logger.info("تم إعادة التشغيل باستخدام python.exe بنجاح.")
                    else:
                        logger.warning("python.exe غير متاح للمحاولة البديلة.")
                except Exception as fallback_e:
                    logger.error(f"فشل في المحاولة البديلة: {fallback_e}")
        else:
            # للبرامج النصية، استخدام مترجم بايثون الحالي
            logger.info(f"إعادة تشغيل البرنامج النصي: {sys.executable} {main_path}")
            try:
                if sys.platform == "win32":
                    # في Windows، استخدام أعلام خاصة
                    CREATE_NO_WINDOW = 0x08000000
                    # Validate executable and script paths
                    python_exe = os.path.abspath(sys.executable)
                    main_path_abs = os.path.abspath(main_path)
                    
                    if not os.path.isfile(python_exe):
                        raise FileNotFoundError(f"Python executable not found: {python_exe}")
                    if not os.path.isfile(main_path_abs):
                        raise FileNotFoundError(f"Script not found: {main_path_abs}")
                    
                    subprocess.Popen([python_exe, main_path_abs], 
                                  creationflags=CREATE_NO_WINDOW,
                                  cwd=os.path.dirname(main_path_abs))
                else:
                    # Validate executable and script paths
                    python_exe = os.path.abspath(sys.executable)
                    main_path_abs = os.path.abspath(main_path)
                    
                    if not os.path.isfile(python_exe):
                        raise FileNotFoundError(f"Python executable not found: {python_exe}")
                    if not os.path.isfile(main_path_abs):
                        raise FileNotFoundError(f"Script not found: {main_path_abs}")
                    
                    subprocess.Popen([python_exe, main_path_abs],
                                  cwd=os.path.dirname(main_path_abs))
                logger.info("تم إعادة تشغيل البرنامج النصي بنجاح.")
            except Exception as e:
                logger.error(f"فشل في إعادة تشغيل البرنامج النصي: {e}")
                logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(f"خطأ غير متوقع في برنامج إعادة التشغيل: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    try:
        restart_app()
    except Exception as e:
        logger.error(f"خطأ فادح في برنامج إعادة التشغيل: {e}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("=== اكتمال برنامج إعادة التشغيل ===")
        sys.exit(0)
