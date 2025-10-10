import requests
import json
import os

def clean_arabic(name):
    to_remove = ['محافظة ', 'مدينة ', 'مقاطعة ', 'قسم ', 'مركز ', 'ولاية ', 'مديرية ', 'منطقة ', 'إدارة ', 'ملعب ', 'إقليم ', 'ناحية ', 'بلدية', 'المجلس الوطني لقوى الثورة ']
    for word in to_remove:
        name = name.replace(word, '')
    return name.strip()

# Load countries from existing countries.json
with open('countries.json', 'r', encoding='utf-8') as f:
    countries = json.load(f)

# Output directory
output_dir = r"C:\Temp\Contries&Cities"
os.makedirs(output_dir, exist_ok=True)

# Process each country
for country in countries:
    english = country[0]
    arabic = country[1]
    
    # Filename based on English country name
    filename = english + '.json'
    
    # Path to cities file
    cities_file = os.path.join('Countries&Cities', filename)
    
    # Load cities if file exists
    if os.path.exists(cities_file):
        with open(cities_file, 'r', encoding='utf-8') as f:
            cities = json.load(f)
        # Clean Arabic names
        for city in cities:
            city['arabic_name'] = clean_arabic(city['arabic_name'])
    else:
        cities = []
    
    # Write to output directory
    output_file = os.path.join(output_dir, filename)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cities, f, ensure_ascii=False, indent=4)

print("Program completed. Files created in C:\\Temp\\Contries&Cities")
