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

# إضافة ملفات tkinter مع تجميع TCL/TK من Python الحالي
try:
    import tkinter
    import _tkinter

    # إضافة ملفات tkinter الأساسية
    tkinter_dir = os.path.dirname(tkinter.__file__)
    if os.path.exists(tkinter_dir):
        datas.append((tkinter_dir, 'tkinter'))
        print(f"تم إضافة tkinter: {tkinter_dir}")

    # تجميع TCL/TK من Python الحالي (ديناميكي)
    python_tcl = os.path.join(sys.base_prefix, 'Library', 'lib', 'tcl8.6')
    python_tk = os.path.join(sys.base_prefix, 'Library', 'lib', 'tk8.6')

    if os.path.exists(python_tcl):
        datas.append((python_tcl, 'tcl8.6'))
        print(f"تم إضافة TCL 8.6 من Python: {python_tcl}")
    else:
        print(f"تحذير: لم يتم العثور على TCL 8.6 في: {python_tcl}")

    if os.path.exists(python_tk):
        datas.append((python_tk, 'tk8.6'))
        print(f"تم إضافة TK 8.6 من Python: {python_tk}")
    else:
        print(f"تحذير: لم يتم العثور على TK 8.6 في: {python_tk}")

    print("تم تجميع ملفات TCL/TK لضمان عمل tkinter في التطبيق المجمد")

except ImportError as e:
    print(f"تحذير: لم يتم العثور على tkinter: {e}")
except Exception as e:
    print(f"تحذير: خطأ في إعداد tkinter: {e}")

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
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'PIL.ImageTk',
        'PIL.Image',
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
    [],
    exclude_binaries=True,
    name='Praytimes',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    icon='pray_times.ico' if os.path.exists('pray_times.ico') else None,
    version=None,
    manifest=None,
    resources=[],
    codesign_identity=None,
    entitlements_file=None,
    hardened_runtime=False
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Praytimes'
)
