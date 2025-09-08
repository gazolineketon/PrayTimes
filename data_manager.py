# -*- coding: utf-8 -*-

"""
data_manager.py
يحتوي هذا الملف على الكلاسات والوظائف المسؤولة عن جلب وإدارة البيانات
"""

import json
import logging
import pickle
import requests
from datetime import datetime, date
from pathlib import Path
from typing import Optional, Tuple

from config import COUNTRIES_CACHE_FILE, CITIES_CACHE_DIR, CACHE_DIR, WORLD_CITIES_DIR

logger = logging.getLogger(__name__)

def get_countries() -> list[tuple[str, str]]:
    """جلب قائمة الدول مع الأسماء العربية والإنجليزية، مع استخدام التخزين المؤقت"""
    if COUNTRIES_CACHE_FILE.exists():
        try:
            with open(COUNTRIES_CACHE_FILE, 'r', encoding='utf-8') as f:
                countries = json.load(f)
            logger.info("تم تحميل قائمة الدول من الملف المؤقت")
            return countries
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"خطأ في تحميل قائمة الدول من الملف المؤقت: {e}")

    # إذا فشل تحميل من الإنترنت، محاولة تحميل من ملف JSON المحلي
    countries_json_path = Path(__file__).parent / 'countries.json'
    local_countries_map = {}
    if countries_json_path.exists():
        try:
            with open(countries_json_path, 'r', encoding='utf-8') as f:
                local_countries_data = json.load(f)
                local_countries_map = {item[0]: item[1] for item in local_countries_data}
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"خطأ في تحميل ملف countries.json: {e}")

    try:
        response = requests.get("https://restcountries.com/v3.1/all?fields=name,translations", timeout=10)
        response.raise_for_status()
        countries_data = response.json()

        countries = []
        for country in countries_data:
            english_name = country.get('name', {}).get('common')
            arabic_name = country.get('translations', {}).get('ara', {}).get('common')

            # إذا لم تتوفر ترجمة عربية من الـ API، ابحث في ملف countries.json
            if not arabic_name and english_name in local_countries_map:
                arabic_name = local_countries_map[english_name]

            if english_name:
                countries.append((english_name, arabic_name if arabic_name else english_name))

        countries = sorted(countries, key=lambda x: x[1])

        try:
            with open(COUNTRIES_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(countries, f, ensure_ascii=False, indent=2)
            logger.info("تم حفظ قائمة الدول في الملف المؤقت")
        except IOError as e:
            logger.error(f"خطأ في حفظ قائمة الدول في الملف المؤقت: {e}")

        logger.info("تم جلب قائمة الدول بنجاح من المصدر")
        return countries

    except requests.exceptions.RequestException as e:
        logger.error(f"خطأ في جلب الدول: {e}")
        # إذا فشل جلب الدول من الإنترنت، جرب جلبها من الملف المحلي
        countries = []
        if local_countries_map:
            for eng, ara in local_countries_map.items():
                countries.append((eng, ara))
            countries = sorted(countries, key=lambda x: x[1])
        return countries

def get_cities(country_name: str) -> list[tuple[str, str]]:
    """جلب قائمة المدن من API وترجمتها من الملفات المحلية"""
    cities_cache_file = CITIES_CACHE_DIR / f"{country_name}.json"
    if cities_cache_file.exists():
        try:
            with open(cities_cache_file, 'r', encoding='utf-8') as f:
                cities = json.load(f)
            logger.info(f"تم تحميل قائمة المدن لـ {country_name} من الملف المؤقت")
            return cities
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"خطأ في تحميل قائمة المدن لـ {country_name} من الملف المؤقت: {e}")

    # API جلب المدن من
    try:
        response = requests.post("https://countriesnow.space/api/v0.1/countries/cities", json={'country': country_name}, timeout=10)
        response.raise_for_status()
        cities_data = response.json()
        english_names = sorted(cities_data.get('data', []))
        if not english_names:
            return []
    except requests.exceptions.RequestException as e:
        logger.error(f"خطأ في جلب المدن لـ {country_name} من API: {e}")
        return []

    # جلب الترجمة المحلية
    country_file = WORLD_CITIES_DIR / f"{country_name}.json"
    translation_map = {}
    if country_file.exists():
        try:
            with open(country_file, 'r', encoding='utf-8') as f:
                translation_data = json.load(f)
            translation_map = {city.get('english_name', '').lower(): city.get('arabic_name', '') for city in translation_data}
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"خطأ في تحميل ملف الترجمة المحلي لـ {country_name}: {e}")

    # ترجمة وعمل قائمة المدن
    cities = []
    for eng_name in english_names:
        ara_name = translation_map.get(eng_name.lower(), eng_name)
        cities.append((eng_name, ara_name))

    cities = sorted(cities, key=lambda x: x[1])

    # حفظ النتائج في ملف مؤقت
    try:
        with open(cities_cache_file, 'w', encoding='utf-8') as f:
            json.dump(cities, f, ensure_ascii=False, indent=2)
        logger.info(f"تم حفظ قائمة المدن المترجمة لـ {country_name} في الملف المؤقت")
    except IOError as e:
        logger.error(f"خطأ في حفظ قائمة المدن لـ {country_name} في الملف المؤقت: {e}")

    logger.info(f"تم جلب وترجمة قائمة المدن لـ {country_name} بنجاح")
    return cities

def get_coordinates_for_city(city: str, country: str) -> Optional[Tuple[float, float]]:
    """
    Get coordinates (latitude, longitude) for a city using Nominatim API.
    """
    try:
        url = f"https://nominatim.openstreetmap.org/search"
        params = {'q': f'{city}, {country}', 'format': 'json', 'limit': 1}
        headers = {'User-Agent': 'PrayerTimesApp/2.0'} # Nominatim requires a User-Agent
        response = requests.get(url, params=params, timeout=10, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            logger.info(f"Coordinates for {city}, {country}: ({lat}, {lon})")
            return lat, lon
        else:
            logger.warning(f"Could not find coordinates for {city}, {country}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching coordinates for {city}, {country}: {e}")
        return None
    except (KeyError, IndexError, ValueError) as e:
        logger.error(f"Error parsing coordinates for {city}, {country}: {e}")
        return None

class CacheManager:
    """مدير البيانات المؤقتة"""    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_cache_file(self, city: str, country: str) -> Path:
        """الحصول على مسار ملف البيانات المؤقتة"""
        today = date.today().isoformat()
        return self.cache_dir / f"prayer_{city}_{country}_{today}.pkl"
    
    def save_data(self, city: str, country: str, data: dict):
        """حفظ البيانات في ذاكرة التخزين المؤقت"""
        try:
            cache_file = self.get_cache_file(city, country)
            with open(cache_file, 'wb') as f:
                pickle.dump({'data': data, 'timestamp': datetime.now().isoformat(), 'city': city, 'country': country}, f)
            logger.info(f"تم حفظ البيانات المؤقتة لـ {city}")
        except Exception as e:
            logger.error(f"خطأ في حفظ البيانات المؤقتة {e}")
    
    def load_data(self, city: str, country: str) -> Optional[dict]:
        """تحميل البيانات من ذاكرة التخزين المؤقت"""
        try:
            cache_file = self.get_cache_file(city, country)
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    logger.info(f"تم تحميل البيانات المؤقتة لـ {city}")
                    return cached_data['data']
        except Exception as e:
            logger.error(f"خطأ في تحميل البيانات المؤقتة {e}")
        return None
    
    def cleanup_old_cache(self):
        """تنظيف البيانات المؤقتة القديمة"""
        try:
            today = date.today()
            for cache_file in self.cache_dir.glob("prayer_*.pkl"):
                try:
                    # استخراج التاريخ من اسم الملف
                    parts = cache_file.stem.split('_')
                    if len(parts) >= 4:
                        file_date_str = parts[-1]
                        file_date = date.fromisoformat(file_date_str)
                        if file_date < today:
                            cache_file.unlink()
                            logger.info(f"تم حذف الملف المؤقت القديم {cache_file}")
                except Exception as e:
                    logger.error(f"خطأ في حذف الملف {cache_file} {e}")
        except Exception as e:
            logger.error(f"خطأ في تنظيف البيانات المؤقتة {e}")