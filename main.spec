# main.spec
import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE
from PyInstaller.utils.hooks import collect_dynamic_libs

# تعطيل خطاف تشغيل pkg_resources لمنع تدخل setuptools
os.environ['PYINSTALLER_NO_PKG_RESOURCES'] = '1'

# التحقق من وجود الملفات قبل إضافتها
datas = []

# إضافة المجلدات إذا كانت موجودة
if os.path.exists('sounds'):
    datas.append(('sounds', 'sounds'))
if os.path.exists('Countries&Cities'):
    datas.append(('Countries&Cities', 'Countries&Cities'))

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


# إضافة دعم أفضل لمكتبات TCL/TK والمكتبات الأخرى
import sys
def get_tcl_tk_paths():
    try:
        import tkinter
        tcl_dir = os.path.join(os.path.dirname(tkinter.__file__), '...')
        tcl_dirs = [d for d in os.listdir(tcl_dir) if d.startswith('tcl')]
        tk_dirs = [d for d in os.listdir(tcl_dir) if d.startswith('tk')]
        return [(os.path.join(tcl_dir, d), d) for d in tcl_dirs + tk_dirs]
    except:
        return []

# إضافة مسارات TCL/TK
tk_paths = get_tcl_tk_paths()
for src, dst in tk_paths:
    if os.path.exists(src):
        datas.append((src, dst))

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
        'plyer.notifications',
        'plyer.libs',
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
        'tkinter.font',
        'PIL.ImageTk',
        'PIL.Image',
        'PIL._tkinter_finder',
        'typing',
        'ui_components',
        'vlc',
        'vlc.libvlc',
        'vlc.libvlc_audio',
        'vlc.libvlc_media',
        'vlc.libvlc_media_player',
        'vlc.libvlc_instance',
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
        'shutil',
        'encodings',
        'encodings.idna',
        'encodings.utf_8',
        'encodings.latin1',
        'encodings.ascii',
        'encodings.cp1252',
        'encodings.cp65001',
        'pkg_resources',
        'pkg_resources.py2_warn',  # إضافة لدعم التوافق
        'ctypes',
        'ctypes.wintypes',
        'win32api',
        'win32con',
        'win32gui',
        'win32clipboard',
        'queue',  # لضمان عمل multiprocessing بشكل صحيح
    ],
    hooksconfig={},
    runtime_hooks=['runtime_hook.py'],
    excludes=['update_version.py', 'test', 'setuptools.glob', 'setuptools.config', 'setuptools.config.setup'],  # استبعاد setuptools المشاكل
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
    hardened_runtime=False,
    # إضافة خيارات إضافية لضمان التوافق
    argv_emulation=False,  # تجنب مشاكل في تمرير المعطيات
    target_arch=None,
    embed_manifest=True,  # تضمين الـ manifest لضمان التوافق مع ويندوز
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Praytimes',
    # إضافة خيارات إضافية لضمان التوافق
    exclude_binaries=False,
    # نسخ مكتبات النظام المطلوبة للعمل على جميع أجهزة ويندوز
    exclude_system_binaries=False,
)
