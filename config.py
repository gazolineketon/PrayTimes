# -*- coding: utf-8 -*- 

"""
config.py
يحتوي هذا الملف على الثوابت والإعدادات العامة للتطبيق
"""

from pathlib import Path

# ترجمات النصوص المستخدمة في التطبيق
TRANSLATIONS = {
    "ar": {
        "prayer_times": "مواقيت الصلاة",
        "settings": "⚙️ إعدادات",
        "update": "🔄 تحديث",
        "location": "🌍 الموقع",
        "country": "الدولة ",
        "city": "المدينة ",
        "qibla_direction": "🧭 اتجاه القبلة",
        "prayer_times_table_title": "🕐 مواقيت الصلاة",
        "fajr": "الفجر",
        "sunrise": "الشروق",
        "dhuhr": "الظهر",
        "asr": "العصر",
        "maghrib": "المغرب",
        "isha": "العشاء",
        "now": "الآن ⏰",
        "finished": "انتهت ✓",
        "upcoming": "قادمة",
        "remaining_time_on": "⏰ الوقت المتبقي على",
        "hour": "ساعة",
        "minute": "دقيقة",
        "connected": "متصل",
        "disconnected": "غير متصل",
        "version": "الإصدار",
        "last_update": "آخر تحديث",
        "app_settings": "إعدادات التطبيق",
        "general": "عام",
        "notifications": "الإشعارات",
        "sounds": "الأصوات",
        "qibla": "القبلة",
        "save": "حفظ",
        "cancel": "إلغاء",
        "restore_defaults": "استعادة الافتراضي",
        "prayer_calculation_method": "طريقة حساب مواقيت الصلاة",
        "auto_update_interval": "فترة التحديث التلقائي (ثواني)",
        "theme": "المظهر",
        "light": "فاتح",
        "dark": "داكن",
        "enable_notifications": "تفعيل الإشعارات",
        "notification_before_prayer": "الإشعار قبل الأذان (دقائق)",
        "enable_adhan_sounds": "تفعيل أصوات الأذان",
        "volume": "مستوى الصوت",
        "custom_sound_file": "ملف الصوت المخصص",
        "browse": "تصفح",
        "show_qibla_direction": "إظهار اتجاه القبلة",
        "qibla_info": "معلومات",
        "qibla_info_text": "        • يتم حساب اتجاه القبلة بناءً على موقع المدينة المختارة •\n        • الاتجاه محسوب بالنسبة للشمال الجغرافي•\n        • للحصول على دقة أكبر، تأكد من اتصالك بالإنترنت •\n        ",
        "location_settings_title": "تحديد الموقع (سيتم تطبيقه عند إعادة التشغيل)",
        "country_en_name": "الدولة (اسم إنجليزي):",
        "city_en_name": "المدينة (اسم إنجليزي):",
        "saved_successfully": "تم الحفظ",
        "settings_saved_successfully": "تم تغيير الإعدادات. إضغط لإعادة التشغيل أو الاستمرار حاليا وسيتم تطبيق الإعدادات عند إعادة التشغيل",
        "confirm": "تأكيد",
        "confirm_restore_defaults": "هل تريد استعادة جميع الإعدادات الافتراضية؟",
        "searching": "جاري البحث...",
        "no_cities": "لا توجد مدن",
        "loading_prayer_times": "🔄 جاري تحميل مواقيت الصلاة...",
        "error": "خطأ",
        "failed_to_fetch_data": "فشل في جلب البيانات",
        "no_server_response": "لا يوجد استجابة من الخادم",
        "connection_error": "خطأ في الاتصال",
        "direction": "الاتجاه",
        "degrees": "درجة",
        "undefined": "غير محدد",
        "updated_successfully": "تم التحديث",
        "prayer_times_updated_successfully": "تم تحديث مواقيت الصلاة بنجاح",
        "please_select_city_country": "الرجاء تحديد المدينة والدولة أولاً في الإعدادات.",
        "app_error": "خطأ في التطبيق",
        "fatal_error": "خطأ فادح",
        "fatal_app_error": "حدث خطأ فادح",
        "language": "اللغة",
        "arabic": "العربية",
        "english": "English",
        "select_adhan_file": "اختر ملف الأذان",
        "audio_files": "ملفات الصوت",
        "all_files": "جميع الملفات",
        "prayer_notification_alert": "تنبيه موقيت الصلاة",
        "minutes_remaining_for_prayer": "يتبقى {minutes} دقائق على أذان {prayer_name}",
        "prayer_time": "وقت الصلاة",
        "its_time_for_prayer": "حان الآن وقت أذان {prayer_name}",
        "current_time_label": "🕐 الوقت الحالي {time_str}",
        "date_label": "📅 التاريخ {date_str}",
        "direction_label": "الاتجاه: --- درجة",
        "qibla_direction_label": "الاتجاه {direction:.1f}°",
        "direction_is": "الاتجاه {direction_name}",
        "prayer_status_now": "الآن ⏰",
        "prayer_status_finished": "انتهت ✓",
        "prayer_status_upcoming": "قادمة",
        "prayer_status_within_hour": "خلال {time_diff}د",
        "table_header_prayer": "الصلاة",
        "table_header_time": "الوقت",
        "table_header_status": "الحالة",
        "error_opening_settings": "حدث خطأ في فتح نافذة الإعدادات",
        "app_title": "🕌 مواقيت الصلاة",
        "restart_required": "إعادة التشغيل مطلوبة",
        "settings_saved_successfully_restart": "تم حفظ الإعدادات. بعض التغييرات تتطلب إعادة تشغيل التطبيق لتفعيلها. هل تريد إعادة التشغيل الآن؟",
        "restart_now": "إعادة التشغيل الآن",
        "continue_later": "المتابعة لاحقاً",
    },
    "en": {
        "prayer_times": "Prayer Times",
        "settings": "⚙️ Settings",
        "update": "🔄 Update",
        "location": "🌍 Location",
        "country": "Country ",
        "city": "City ",
        "qibla_direction": "🧭 Qibla Direction",
        "prayer_times_table_title": "🕐 Prayer Times",
        "fajr": "Fajr",
        "sunrise": "Sunrise",
        "dhuhr": "Dhuhr",
        "asr": "Asr",
        "maghrib": "Maghrib",
        "isha": "Isha",
        "now": "Now ⏰",
        "finished": "Finished ✓",
        "upcoming": "Upcoming",
        "remaining_time_on": "⏰ Time remaining for",
        "hour": "hour",
        "minute": "minute",
        "connected": "Connected",
        "disconnected": "Disconnected",
        "version": "Version",
        "last_update": "Last update",
        "app_settings": "Application Settings",
        "general": "General",
        "notifications": "Notifications",
        "sounds": "Sounds",
        "qibla": "Qibla",
        "save": "Save",
        "cancel": "Cancel",
        "restore_defaults": "Restore Defaults",
        "prayer_calculation_method": "Prayer Times Calculation Method",
        "auto_update_interval": "Auto Update Interval (seconds)",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark",
        "enable_notifications": "Enable Notifications",
        "notification_before_prayer": "Notify before prayer (minutes)",
        "enable_adhan_sounds": "Enable Adhan Sounds",
        "volume": "Volume",
        "custom_sound_file": "Custom Sound File",
        "browse": "Browse",
        "show_qibla_direction": "Show Qibla Direction",
        "qibla_info": "Information",
        "qibla_info_text": "        • Qibla direction is calculated based on the selected city's location.\n        • The direction is calculated relative to True North.\n        • For better accuracy, ensure you are connected to the internet.\n        ",
        "location_settings_title": "Set Location (applies on restart)",
        "country_en_name": "Country (English name):",
        "city_en_name": "City (English name):",
        "saved_successfully": "Saved",
        "settings_saved_successfully": "Settings have been changed. Click to restart or continue and settings will be applied on restart.",
        "confirm": "Confirm",
        "confirm_restore_defaults": "Are you sure you want to restore all default settings?",
        "searching": "Searching...",
        "no_cities": "No cities found",
        "loading_prayer_times": "🔄 Loading prayer times...",
        "error": "Error",
        "failed_to_fetch_data": "Failed to fetch data",
        "no_server_response": "No response from server",
        "connection_error": "Connection error",
        "direction": "Direction",
        "degrees": "degrees",
        "undefined": "Undefined",
        "updated_successfully": "Updated",
        "prayer_times_updated_successfully": "Prayer times updated successfully",
        "please_select_city_country": "Please select the city and country first in the settings.",
        "app_error": "Application Error",
        "fatal_error": "Fatal Error",
        "fatal_app_error": "A fatal error occurred",
        "language": "Language",
        "arabic": "العربية",
        "english": "English",
        "select_adhan_file": "Select Adhan File",
        "audio_files": "Audio Files",
        "all_files": "All Files",
        "prayer_notification_alert": "Prayer Time Alert",
        "minutes_remaining_for_prayer": "{minutes} minutes remaining for {prayer_name} prayer",
        "prayer_time": "Prayer Time",
        "its_time_for_prayer": "It's time for {prayer_name} prayer",
        "current_time_label": "🕐 Current Time {time_str}",
        "date_label": "📅 Date {date_str}",
        "direction_label": "Direction: --- degrees",
        "qibla_direction_label": "Direction {direction:.1f}°",
        "direction_is": "Direction {direction_name}",
        "prayer_status_now": "Now ⏰",
        "prayer_status_finished": "Finished ✓",
        "prayer_status_upcoming": "Upcoming",
        "prayer_status_within_hour": "In {time_diff} min",
        "table_header_prayer": "Prayer",
        "table_header_time": "Time",
        "table_header_status": "Status",
        "error_opening_settings": "Error opening settings window",
        "app_title": "🕌 Prayer Times",
        "restart_required": "Restart Required",
        "settings_saved_successfully_restart": "Settings saved. Some changes require a restart to take effect. Do you want to restart now?",
        "restart_now": "Restart Now",
        "continue_later": "Continue Later",
    }
}

# طرق حساب مواقيت الصلاة
CALCULATION_METHODS = {
    "جامعة العلوم الإسلامية - كراتشي": 1,
    "الجمعية الإسلامية لأمريكا الشمالية": 2,
    "رابطة العالم الإسلامي": 3,
    "أم القرى - مكة المكرمة": 4,
    "الهيئة المصرية العامة للمساحة": 5,
    "جامعة طهران للعلوم": 7,
    "معهد الجيوفيزياء - جامعة طهران": 8,
    "الخليج - دولة الإمارات": 9,
    "الكويت": 10,
    "قطر": 11,
    "مجلس الشورى الإسلامي الأعلى - الجزائر": 12,
    "فرنسا - اتحاد المنظمات الإسلامية": 13,
    "تركيا - رئاسة الشؤون الدينية": 14,
    "روسيا - المجلس الديني": 15
}
CALCULATION_METHODS_REV = {v: k for k, v in CALCULATION_METHODS.items()}

# تحديد المسار الجذري للمشروع لضمان استقلالية المسارات
APP_DIR = Path(__file__).parent.resolve()
ROOT_DIR = APP_DIR

# المسارات للملفات والمجلدات الرئيسية
SETTINGS_FILE = APP_DIR / 'settings.json'
CACHE_DIR = ROOT_DIR / 'cache'
LOG_DIR = ROOT_DIR / 'logs'
LOG_FILE = LOG_DIR / 'prayer_app.log'
COUNTRIES_CACHE_FILE = CACHE_DIR / 'countries.json'
CITIES_CACHE_DIR = CACHE_DIR / 'cities_cache'
WORLD_CITIES_DIR = ROOT_DIR / 'world_cities'
SOUNDS_DIR = ROOT_DIR / 'sounds'

# تأكد من وجود مجلدات التخزين المؤقت والسجلات
CACHE_DIR.mkdir(exist_ok=True)
CITIES_CACHE_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

class Translator:
    def __init__(self, language="ar"):
        self.language = language
        if language not in TRANSLATIONS:
            self.language = "en"

    def set_language(self, language):
        if language in TRANSLATIONS:
            self.language = language

    def get(self, key, **kwargs):
        translation = TRANSLATIONS.get(self.language, {}).get(key, key)
        if kwargs:
            return translation.format(**kwargs)
        return translation
