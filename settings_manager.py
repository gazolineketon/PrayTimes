# -*- coding: utf-8 -*-

"""
settings_manager.py
يحتوي هذا الملف على كلاس لإدارة إعدادات التطبيق
"""

import json
import logging
from config import SETTINGS_FILE

logger = logging.getLogger(__name__)

class Settings:
    """فئة إعدادات التطبيق"""
    
    def __init__(self):
        self.notifications_enabled = True
        self.sound_enabled = True
        self.calculation_method = 5
        self.theme = "light"
        self.language = "ar"
        self.notification_before_minutes = 5
        self.auto_update_interval = 60
        self.sound_volume = 0.7
        self.adhan_sound_file = ""
        self.notification_sound_file = ""
        self.qibla_enabled = True
        self.weather_enabled = False
        self.selected_country = "Egypt"  # البلد الإفتراضى
        self.selected_city = "Cairo"      # المدينة الإفتراضية
        self.load_settings()
    
    def load_settings(self):
        """تحميل الإعدادات من ملف"""
        try:
            if SETTINGS_FILE.exists():
                with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                logger.info("تم تحميل الإعدادات بنجاح")
        except Exception as e:
            logger.error(f"خطأ في تحميل الإعدادات {e}")
    
    def save_settings(self):
        """حفظ الإعدادات في ملف"""
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.__dict__, f, ensure_ascii=False, indent=2)
            logger.info("تم حفظ الإعدادات بنجاح")
        except Exception as e:
            logger.error(f"خطأ في حفظ الإعدادات {e}")
