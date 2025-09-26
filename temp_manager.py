# -*- coding: utf-8 -*-

"""
temp_manager.py
إدارة المجلدات المؤقتة وتنظيفها لتجنب مشاكل الصلاحيات
"""

import os
import sys
import tempfile
import shutil
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TempManager:
    """مدير المجلدات المؤقتة"""
    
    def __init__(self):
        self.temp_dirs_created = []
        self.app_data_dir = self._get_app_data_dir()
    
    def _get_app_data_dir(self):
        """الحصول على مجلد البيانات الدائم"""
        if sys.platform.startswith('win'):
            app_data = os.environ.get('APPDATA', '')
            app_dir = os.path.join(app_data, 'PrayTimes')
        else:
            home = os.path.expanduser('~')
            app_dir = os.path.join(home, '.praytimes')
        
        Path(app_dir).mkdir(parents=True, exist_ok=True)
        return app_dir
    
    def cleanup_old_mei_folders(self):
        """تنظيف مجلدات _MEI القديمة"""
        # تمكين تنظيف _MEI القديمة حتى للتطبيقات المجمدة لتجنب مشاكل إعادة التشغيل

        try:
            temp_dir = tempfile.gettempdir()
            current_time = time.time()
            
            logger.info(f"بدء تنظيف المجلدات المؤقتة في: {temp_dir}")
            
            cleaned_count = 0
            for item in os.listdir(temp_dir):
                if item.startswith('_MEI') and os.path.isdir(os.path.join(temp_dir, item)):
                    mei_path = os.path.join(temp_dir, item)
                    try:
                        # التحقق من عمر المجلد (أكثر من 6 ساعات)
                        folder_age = current_time - os.path.getctime(mei_path)
                        if folder_age > 3600:  # ساعة واحدة
                            # محاولة حذف المجلد
                            shutil.rmtree(mei_path, ignore_errors=True)
                            if not os.path.exists(mei_path):
                                logger.info(f"تم حذف المجلد المؤقت: {mei_path}")
                                cleaned_count += 1
                            else:
                                logger.warning(f"فشل في حذف المجلد: {mei_path}")
                    except Exception as e:
                        logger.debug(f"خطأ في معالجة المجلد {mei_path}: {e}")
                        continue
            
            if cleaned_count > 0:
                logger.info(f"تم تنظيف {cleaned_count} مجلد مؤقت")
            else:
                logger.debug("لا توجد مجلدات مؤقتة قديمة للحذف")
                
        except Exception as e:
            logger.error(f"خطأ في تنظيف المجلدات المؤقتة: {e}")
    
    def force_cleanup_current_mei(self):
        """محاولة تنظيف المجلد المؤقت الحالي عند الإغلاق"""
        try:
            if hasattr(sys, '_MEIPASS'):
                current_mei = sys._MEIPASS
                logger.info(f"محاولة تنظيف المجلد المؤقت الحالي: {current_mei}")
                
                # تأخير قصير للسماح للعمليات بالانتهاء
                time.sleep(0.5)
                
                # محاولة حذف المجلد
                try:
                    shutil.rmtree(current_mei, ignore_errors=True)
                    if not os.path.exists(current_mei):
                        logger.info("تم حذف المجلد المؤقت الحالي بنجاح")
                except Exception as e:
                    logger.debug(f"لم يتم حذف المجلد المؤقت الحالي: {e}")
        except Exception as e:
            logger.debug(f"خطأ في تنظيف المجلد المؤقت الحالي: {e}")
    
    def ensure_app_data_structure(self):
        """التأكد من وجود هيكل المجلدات المطلوب"""
        try:
            required_dirs = [
                'cache',
                'logs', 
                'sounds',
                'world_cities',
                'cache/cities_cache'
            ]
            
            for dir_name in required_dirs:
                dir_path = os.path.join(self.app_data_dir, dir_name)
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                logger.debug(f"تم التأكد من وجود المجلد: {dir_path}")
                
        except Exception as e:
            logger.error(f"خطأ في إنشاء هيكل المجلدات: {e}")
    
    def get_safe_temp_dir(self):
        """الحصول على مجلد مؤقت آمن داخل مجلد البيانات"""
        try:
            temp_dir = os.path.join(self.app_data_dir, 'temp')
            Path(temp_dir).mkdir(parents=True, exist_ok=True)
            return temp_dir
        except Exception as e:
            logger.error(f"خطأ في إنشاء المجلد المؤقت الآمن: {e}")
            return tempfile.gettempdir()
    
    def cleanup_app_temp_files(self):
        """تنظيف الملفات المؤقتة الخاصة بالتطبيق"""
        try:
            app_temp_dir = os.path.join(self.app_data_dir, 'temp')
            if os.path.exists(app_temp_dir):
                current_time = time.time()
                cleaned_count = 0
                
                for item in os.listdir(app_temp_dir):
                    item_path = os.path.join(app_temp_dir, item)
                    try:
                        # حذف الملفات الأقدم من ساعة واحدة
                        if current_time - os.path.getctime(item_path) > 3600:
                            if os.path.isfile(item_path):
                                os.remove(item_path)
                                cleaned_count += 1
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path, ignore_errors=True)
                                cleaned_count += 1
                    except Exception:
                        continue
                
                if cleaned_count > 0:
                    logger.info(f"تم تنظيف {cleaned_count} ملف مؤقت من مجلد التطبيق")
                    
        except Exception as e:
            logger.debug(f"خطأ في تنظيف ملفات التطبيق المؤقتة: {e}")

# إنشاء مثيل عام للاستخدام
temp_manager = TempManager()

def register_temp_cleanup():
    """تسجيل دوال التنظيف"""
    import atexit
    
    # تنظيف المجلدات القديمة عند البدء
    temp_manager.cleanup_old_mei_folders()
    
    temp_manager.cleanup_app_temp_files()
    temp_manager.ensure_app_data_structure()
    
    # تسجيل دوال التنظيف عند الإغلاق
    # تعطيل حذف المجلد المؤقت الحالي لتجنب مشاكل الصلاحيات
    # atexit.register(temp_manager.force_cleanup_current_mei)
    
    # تعطيل تنظيف _MEI للتطبيقات المجمدة لتجنب مشاكل الصلاحيات
    if not getattr(sys, 'frozen', False):
        atexit.register(temp_manager.cleanup_old_mei_folders)
    
    atexit.register(temp_manager.cleanup_app_temp_files)
    
    logger.info("تم تسجيل دوال تنظيف المجلدات المؤقتة")
