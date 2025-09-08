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
    """فئة مزامنة الوقت"""
    
    @staticmethod
    def sync_time() -> datetime:
        """مزامنة الوقت مع خادم NTP"""
        if not NTPLIB_AVAILABLE:
            return datetime.now()

        NTP_SERVERS = [
            'pool.ntp.org',
            'time.google.com',
            'time.windows.com',
            'time.nist.gov'
        ]
        for server in NTP_SERVERS:
            try:
                client = ntplib.NTPClient()
                response = client.request(server, timeout=10)
                synced_time = datetime.fromtimestamp(response.tx_time)
                logger.info(f"تم مزامنة الوقت مع خادم NTP: {server}")
                return synced_time
            except Exception as e:
                logger.warning(f"فشل في مزامنة الوقت من {server}: {e}")
        
        logger.error("فشل في مزامنة الوقت من جميع خوادم NTP.")
        return datetime.now()

class QiblaCalculator:
    """حاسبة اتجاه القبلة"""
    
    KAABA_LAT = 21.4225
    KAABA_LON = 39.8262
    
    @staticmethod
    def calculate_qibla(lat: float, lon: float) -> float:
        """حساب اتجاه القبلة بالدرجات"""
        try:
            lat1 = math.radians(lat)
            lon1 = math.radians(lon)
            lat2 = math.radians(QiblaCalculator.KAABA_LAT)
            lon2 = math.radians(QiblaCalculator.KAABA_LON)
            
            dlon = lon2 - lon1
            y = math.sin(dlon) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
            
            bearing = math.atan2(y, x)
            bearing = math.degrees(bearing)
            bearing = (bearing + 360) % 360
            
            return bearing
        except Exception as e:
            logger.error(f"خطأ في حساب القبلة {e}")
            return 0

    @staticmethod
    def calculate_distance(lat: float, lon: float) -> float:
        """حساب المسافة إلى الكعبة بالكيلومترات"""
        try:
            R = 6371  # Earth radius in kilometers
            lat1 = math.radians(lat)
            lon1 = math.radians(lon)
            lat2 = math.radians(QiblaCalculator.KAABA_LAT)
            lon2 = math.radians(QiblaCalculator.KAABA_LON)
            
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            
            a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            distance = R * c
            return distance
        except Exception as e:
            logger.error(f"خطأ في حساب المسافة {e}")
            return 0
