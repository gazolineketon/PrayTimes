# -*- coding: utf-8 -*-

"""
instance_manager.py
إدارة نسخة واحدة من التطبيق للتأكد من عدم تشغيل نسخ متعددة
"""

import os
import sys
import tempfile
import logging
import atexit
import time

logger = logging.getLogger(__name__)

class SingleInstance:
    """
    فئة لضمان تشغيل نسخة واحدة فقط من التطبيق
    تستخدم ملف قفل في المجلد المؤقت
    """
    
    def __init__(self, app_name="PrayerTimes", timeout=1.0):
        """
        تهيئة مدير النسخة الواحدة
        
        Args:
            app_name: اسم التطبيق المستخدم لإنشاء ملف القفل
            timeout: الوقت المسموح لانتظار تحرير القفل
        """
        self.app_name = app_name
        self.timeout = timeout
        self.lock_file = None
        self.lock_file_path = None
        self.is_locked = False
        
    def acquire(self):
        """
        محاولة الحصول على القفل
        
        Returns:
            True إذا تم الحصول على القفل بنجاح، False خلاف ذلك
        """
        # إنشاء مسار ملف القفل في المجلد المؤقت
        temp_dir = tempfile.gettempdir()
        self.lock_file_path = os.path.join(temp_dir, f"{self.app_name}.lock")
        
        try:
            # محاولة فتح ملف القفل
            if os.path.exists(self.lock_file_path):
                # التحقق من عمر ملف القفل
                lock_age = time.time() - os.path.getmtime(self.lock_file_path)
                
                # إذا كان ملف القفل قديمًا جدًا (أكثر من ساعة)، فربما تم ترك القفل دون تنظيف
                if lock_age > 3600:
                    logger.warning(f"تم العثور على ملف قفل قديم (عمره {lock_age:.0f} ثانية)، سيتم حذفه")
                    try:
                        os.remove(self.lock_file_path)
                    except Exception as e:
                        logger.error(f"فشل حذف ملف القفل القديم: {e}")
                        return False
                else:
                    # هناك نسخة أخرى قيد التشغيل
                    logger.info("تم اكتشاف نسخة أخرى من التطبيق قيد التشغيل")
                    return False
            
            # محاولة إنشاء ملف القفل
            # استخدام os.O_CREAT | os.O_EXCL | os.O_RDWR للتأكد من أن هذه العملية فقط يمكنها إنشاء الملف
            try:
                # في Windows، نستخدم طريقة مختلفة قليلاً
                if sys.platform == 'win32':
                    # محاولة فتح الملف بشكل حصري
                    self.lock_file = open(self.lock_file_path, 'w')
                    # كتابة معرف العملية في الملف
                    self.lock_file.write(f"{os.getpid()}\n")
                    self.lock_file.flush()
                    
                    # تسجيل دالة التنظيف عند الخروج
                    atexit.register(self.release)
                    self.is_locked = True
                    logger.info(f"تم الحصول على قفل التطبيق: {self.lock_file_path}")
                    return True
                else:
                    # في Linux/Unix
                    fd = os.open(
                        self.lock_file_path,
                        os.O_CREAT | os.O_EXCL | os.O_RDWR
                    )
                    self.lock_file = os.fdopen(fd, 'w')
                    self.lock_file.write(f"{os.getpid()}\n")
                    self.lock_file.flush()
                    
                    atexit.register(self.release)
                    self.is_locked = True
                    logger.info(f"تم الحصول على قفل التطبيق: {self.lock_file_path}")
                    return True
                    
            except (OSError, IOError) as e:
                # فشل في إنشاء الملف، ربما هناك نسخة أخرى
                logger.info(f"فشل في الحصول على القفل: {e}")
                return False
                
        except Exception as e:
            logger.error(f"خطأ في محاولة الحصول على القفل: {e}", exc_info=True)
            return False
    
    def release(self):
        """
        تحرير القفل وحذف ملف القفل
        """
        if not self.is_locked:
            return
            
        try:
            # إغلاق ملف القفل
            if self.lock_file:
                try:
                    self.lock_file.close()
                except Exception as e:
                    logger.warning(f"خطأ في إغلاق ملف القفل: {e}")
                    
            # حذف ملف القفل
            if self.lock_file_path and os.path.exists(self.lock_file_path):
                try:
                    os.remove(self.lock_file_path)
                    logger.info("تم تحرير قفل التطبيق")
                except Exception as e:
                    logger.warning(f"خطأ في حذف ملف القفل: {e}")
                    
            self.is_locked = False
            
        except Exception as e:
            logger.error(f"خطأ في تحرير القفل: {e}", exc_info=True)
    
    def __del__(self):
        """
        التأكد من تحرير القفل عند حذف الكائن
        """
        self.release()


# إنشاء مدير النسخة الواحدة العام
_instance_manager = None

def get_instance_manager():
    """
    الحصول على مدير النسخة الواحدة
    
    Returns:
        كائن SingleInstance
    """
    global _instance_manager
    if _instance_manager is None:
        _instance_manager = SingleInstance()
    return _instance_manager

def ensure_single_instance():
    """
    التأكد من تشغيل نسخة واحدة فقط من التطبيق
    
    Returns:
        True إذا كانت هذه هي النسخة الوحيدة، False خلاف ذلك
    """
    manager = get_instance_manager()
    return manager.acquire()
