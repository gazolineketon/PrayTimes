# -*- coding: utf-8 -*-

"""
prayer_logic.py
يحتوي هذا الملف على منطق حساب مواقيت الصلاة والقبلة
"""

import math
import logging
import requests
from datetime import datetime
from typing import Tuple

logger = logging.getLogger(__name__)

try:
    import ntplib
    NTPLIB_AVAILABLE = True
except ImportError:
    NTPLIB_AVAILABLE = False
    logger.warning("ntplib غير متوفر - مزامنة الوقت معطلة")

class TimeSync:
    """فئة مزامنة الوقت مع تخزين مؤقت للتقليل من طلبات الشبكة"""
    
    # تخزين مؤقت للوقت المتزامن
    _last_sync_time = None
    _last_local_time = None
    _time_offset = None
    _last_sync_timestamp = 0
    
    # الفاصل الزمني بين عمليات المزامنة (بالثواني)
    SYNC_INTERVAL = 3600  # مزامنة مرة واحدة كل ساعة
    
    @classmethod
    def sync_time(cls) -> datetime:
        """مزامنة الوقت مع خادم NTP مع تخزين مؤقت للنتائج"""
        current_time = datetime.now()
        current_timestamp = current_time.timestamp()
        
        # إذا كان هناك فرق زمني محسوب سابقًا وما زال ضمن الفترة المسموح بها، استخدمه
        if cls._time_offset is not None and (current_timestamp - cls._last_sync_timestamp) < cls.SYNC_INTERVAL:
            adjusted_time = current_time + cls._time_offset
            logger.debug("استخدام الفرق الزمني المخزن مؤقتًا")
            return adjusted_time
            
        # إذا لم تكن المكتبة متوفرة، استخدم الوقت المحلي
        if not NTPLIB_AVAILABLE:
            return current_time

        NTP_SERVERS = [
            'pool.ntp.org',
            'time.google.com',
            'time.windows.com',
            'time.nist.gov'
        ]
        
        for server in NTP_SERVERS:
            try:
                client = ntplib.NTPClient()
                response = client.request(server, timeout=5)  # تقليل فترة انتظار الطلب
                
                # احسب الوقت المتزامن
                synced_time = datetime.fromtimestamp(response.tx_time)
                
                # احسب الفرق الزمني بين الوقت المحلي والوقت المتزامن
                cls._time_offset = synced_time - current_time
                cls._last_sync_time = synced_time
                cls._last_local_time = current_time
                cls._last_sync_timestamp = current_timestamp
                
                logger.info(f"تم مزامنة الوقت مع خادم NTP: {server}, الفرق: {cls._time_offset}")
                return synced_time
            except Exception as e:
                logger.warning(f"فشل في مزامنة الوقت من {server}: {e}")
        
        logger.error("فشل في مزامنة الوقت من جميع خوادم NTP.")
        return current_time
    
    @classmethod
    def get_current_time(cls) -> datetime:
        """الحصول على الوقت الحالي المتزامن بدون الاتصال بالخادم في كل مرة"""
        if cls._time_offset is None:
            # إذا لم تتم المزامنة من قبل، قم بإجراء المزامنة
            return cls.sync_time()
        
        # استخدم الفرق الزمني المحسوب مسبقًا
        current_time = datetime.now()
        current_timestamp = current_time.timestamp()
        
        # إذا مر وقت طويل منذ آخر مزامنة، قم بمزامنة جديدة
        if (current_timestamp - cls._last_sync_timestamp) >= cls.SYNC_INTERVAL:
            return cls.sync_time()
            
        # استخدم الفرق الزمني المحسوب مسبقًا
        adjusted_time = current_time + cls._time_offset
        return adjusted_time

class QiblaCalculator:
    """حاسبة اتجاه القبلة مع تخزين مؤقت للنتائج"""
    
    KAABA_LAT = 21.4225
    KAABA_LON = 39.8262
    
    # تخزين مؤقت للحسابات (كمية محدودة للحفاظ على الذاكرة)
    _qibla_cache = {}
    _distance_cache = {}
    _MAX_CACHE_SIZE = 100
    
    @classmethod
    def calculate_qibla(cls, lat: float, lon: float) -> float:
        """حساب اتجاه القبلة بالدرجات مع تخزين النتائج مؤقتًا"""
        # تقريب الإحداثيات إلى 4 أرقام عشرية للتخزين المؤقت (كافٍ للدقة ~10 متر)
        cache_key = (round(lat, 4), round(lon, 4))
        
        # التحقق إذا كانت النتيجة موجودة في التخزين المؤقت
        if cache_key in cls._qibla_cache:
            return cls._qibla_cache[cache_key]
        
        try:
            lat1 = math.radians(lat)
            lon1 = math.radians(lon)
            lat2 = math.radians(cls.KAABA_LAT)
            lon2 = math.radians(cls.KAABA_LON)
            
            dlon = lon2 - lon1
            y = math.sin(dlon) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
            
            bearing = math.atan2(y, x)
            bearing = math.degrees(bearing)
            bearing = (bearing + 360) % 360
            
            # تخزين النتيجة في التخزين المؤقت
            if len(cls._qibla_cache) >= cls._MAX_CACHE_SIZE:
                # حذف أول عنصر إذا امتلأ التخزين المؤقت
                cls._qibla_cache.pop(next(iter(cls._qibla_cache)))
            
            cls._qibla_cache[cache_key] = bearing
            return bearing
        except Exception as e:
            logger.error(f"خطأ في حساب القبلة: {e}")
            return 0

    @classmethod
    def calculate_distance(cls, lat: float, lon: float) -> float:
        """حساب المسافة إلى الكعبة بالكيلومترات مع تخزين النتائج مؤقتًا"""
        # تقريب الإحداثيات إلى 4 أرقام عشرية للتخزين المؤقت
        cache_key = (round(lat, 4), round(lon, 4))
        
        # التحقق إذا كانت النتيجة موجودة في التخزين المؤقت
        if cache_key in cls._distance_cache:
            return cls._distance_cache[cache_key]
        
        try:
            R = 6371  # نصف قطر الأرض بالكيلومترات
            lat1 = math.radians(lat)
            lon1 = math.radians(lon)
            lat2 = math.radians(cls.KAABA_LAT)
            lon2 = math.radians(cls.KAABA_LON)
            
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            
            a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            distance = R * c
            
            # تخزين النتيجة في التخزين المؤقت
            if len(cls._distance_cache) >= cls._MAX_CACHE_SIZE:
                # حذف أول عنصر إذا امتلأ التخزين المؤقت
                cls._distance_cache.pop(next(iter(cls._distance_cache)))
            
            cls._distance_cache[cache_key] = distance
            return distance
        except Exception as e:
            logger.error(f"خطأ في حساب المسافة: {e}")
            return 0
            
    @classmethod
    def clear_cache(cls):
        """تنظيف التخزين المؤقت (يمكن استدعاؤها عند الحاجة لتحرير الذاكرة)"""
        cls._qibla_cache.clear()
        cls._distance_cache.clear()
        logger.debug("تم مسح التخزين المؤقت لحسابات القبلة")
