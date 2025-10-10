import json

with open('C:\\Users\\Nassar_Home\\AppData\\Roaming\\PrayTimes\\cache\\cities_cache\\Egypt.json', 'r', encoding='utf-8') as f:
    cities = json.load(f)

untranslated = [city for city in cities if city[0] == city[1]]
print('مدن غير مترجمة:')
for city in untranslated:
    print(f'"{city[0]}"')
print(f'إجمالي: {len(untranslated)}')

# أيضًا، ابحث عن التكرارات
from collections import Counter
english_names = [city[0] for city in cities]
arabic_names = [city[1] for city in cities]
english_duplicates = [name for name, count in Counter(english_names).items() if count > 1]
arabic_duplicates = [name for name, count in Counter(arabic_names).items() if count > 1]
print('\nمدن مكررة (أسماء إنجليزية):')
for dup in english_duplicates:
    print(f'"{dup}"')

print('\nمدن مكررة (أسماء عربية):')
for dup in arabic_duplicates:
    print(f'"{dup}"')