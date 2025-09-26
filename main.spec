# main.spec
import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE
from PyInstaller.utils.hooks import collect_dynamic_libs

# Disable pkg_resources runtime hook to prevent setuptools interference
os.environ['PYINSTALLER_NO_PKG_RESOURCES'] = '1'

# التحقق من وجود الملفات قبل إضافتها
datas = []

# إضافة المجلدات إذا كانت موجودة
if os.path.exists('sounds'):
    datas.append(('sounds', 'sounds'))
if os.path.exists('world_cities'):
    datas.append(('world_cities', 'world_cities'))

# إضافة الملفات المفردة إذا كانت موجودة
files_to_add = ['countries.json', 'pray_logo.png', 'pray_times.ico']
for file in files_to_add:
    if os.path.exists(file):
        datas.append((file, '.'))

# إضافة ملفات tkinter لتجنب مشاكل _MEI
try:
    import tkinter
    tkinter_path = os.path.dirname(tkinter.__file__)

    # إضافة مجلد tcl
    tcl_path = os.path.join(os.path.dirname(tkinter_path), 'tcl')
    if os.path.exists(tcl_path):
        datas.append((tcl_path, 'tcl'))

    # إضافة مجلد tk
    tk_path = os.path.join(os.path.dirname(tkinter_path), 'tk')
    if os.path.exists(tk_path):
        datas.append((tk_path, 'tk'))

    print(f"تم إضافة ملفات tkinter: tcl={tcl_path}, tk={tk_path}")
except ImportError:
    print("تحذير: لم يتم العثور على tkinter")

# إضافة ملفات PIL لدعم tkinter
try:
    import PIL
    pil_path = os.path.dirname(PIL.__file__)

    # إضافة مجلد PIL بالكامل لضمان تضمين جميع الملفات
    if os.path.exists(pil_path):
        datas.append((pil_path, 'PIL'))
        print(f"تم إضافة مجلد PIL: {pil_path}")

    print(f"تم العثور على PIL في: {pil_path}")
except ImportError:
    print("تحذير: لم يتم العثور على PIL")


a = Analysis(
    ['main.py'],  # تأكد أن resource_helper.py في نفس المجلد
    pathex=['.'],
    binaries=collect_dynamic_libs('PIL'),
    datas=datas,
    hiddenimports=[
        'glob',
        'ast',
        'concurrent',
        'config',
        'data_manager',
        'main_app_ui',
        'media_manager',
        'multiprocessing',
        'ntplib',
        'pickle',
        'playsound',
        'plyer',
        'prayer_logic',
        'pystray',
        'qibla_ui',
        'requests',
        'settings_manager',
        'subprocess',
        'tkinter',
        'typing',
        'ui_components',
        'vlc',
        'datetime',
        'json',
        'logging',
        'math',
        'os',
        'pathlib',
        're',
        'sys',
        'threading',
        'time',
        'shutil'
    ],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=['update_version.py', 'test', 'setuptools', 'pkg_resources'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Praytimes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # تعطيل UPX لتقليل مشاكل التنظيف
    upx_exclude=[],
    runtime_tmpdir=os.path.join(os.environ.get('APPDATA', ''), 'PrayTimes', 'temp'),
    console=False,
    disable_windowed_traceback=False,
    icon='pray_times.ico' if os.path.exists('pray_times.ico') else None
)