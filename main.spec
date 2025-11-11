# main.spec
import os
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE
from PyInstaller.utils.hooks import collect_dynamic_libs, collect_submodules, collect_data_files

# تعطيل خطاف تشغيل pkg_resources لمنع تدخل setuptools
os.environ['PYINSTALLER_NO_PKG_RESOURCES'] = '1'

# جمع ملفات VLC للعمل المستقل
vlc_binaries = []
vlc_datas = []

# إضافة ملفات VLC الإضافية إذا كانت متوفرة
try:
    import vlc

    # البحث عن مكتبات VLC في مجلدات مختلفة
    libvlc_path = None
    possible_lib_paths = [
        r'C:\Program Files\VideoLAN\VLC',
        r'C:\Program Files (x86)\VideoLAN\VLC',
    ]

    for path in possible_lib_paths:
        if os.path.exists(path):
            libvlc_path = path
            print(f"تم العثور على VLC في: {libvlc_path}")
            break

    if libvlc_path:
        # إضافة ملفات VLC الأساسية
        essential_dlls = ['libvlc.dll', 'libvlccore.dll', 'axvlc.dll']
        for dll in essential_dlls:
            dll_path = os.path.join(libvlc_path, dll)
            if os.path.exists(dll_path):
                vlc_binaries.append((dll_path, '.'))
                print(f"تم إضافة {dll}: {dll_path}")

        # إضافة ملفات VLC الإضافية من مجلد VLC
        for root, dirs, files in os.walk(libvlc_path):
            for file in files:
                if file.endswith(('.dll', '.exe')) and file not in essential_dlls:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(root, libvlc_path)
                    if rel_path == '.':
                        vlc_binaries.append((full_path, '.'))
                    else:
                        vlc_binaries.append((full_path, rel_path))

        # إضافة مجلد plugins بالكامل
        plugins_path = os.path.join(libvlc_path, 'plugins')
        if os.path.exists(plugins_path):
            vlc_datas.append((plugins_path, 'vlc/plugins'))
            print(f"تم إضافة مجلد plugins: {plugins_path}")

        # إضافة مجلد locale إذا كان موجوداً
        locale_path = os.path.join(libvlc_path, 'locale')
        if os.path.exists(locale_path):
            vlc_datas.append((locale_path, 'vlc/locale'))
            print(f"تم إضافة مجلد locale: {locale_path}")

        print(f"تم جمع {len(vlc_binaries)} ملفات VLC و {len(vlc_datas)} مجلدات بيانات")

except ImportError:
    print("تحذير: لم يتم العثور على مكتبة VLC")
except Exception as e:
    print(f"تحذير: خطأ في جمع ملفات VLC: {e}")

# التحقق من وجود الملفات قبل إضافتها
datas = []

# إضافة المجلدات إذا كانت موجودة
if os.path.exists('sounds'):
    datas.append(('sounds', 'sounds'))
    print(f"تم إضافة مجلد sounds: {len(os.listdir('sounds'))} ملفات")
if os.path.exists('Countries&Cities'):
    datas.append(('Countries&Cities', 'Countries&Cities'))
    print(f"تم إضافة مجلد Countries&Cities: {len(os.listdir('Countries&Cities'))} ملفات")

# إضافة الملفات المفردة إذا كانت موجودة
files_to_add = ['countries.json', 'pray_logo.png', 'pray_times.ico']
for file in files_to_add:
    if os.path.exists(file):
        datas.append((file, '.'))

# ملاحظة: تم نقل إعداد tkinter إلى hook مخصص في hooks/hook-tkinter.py

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

# تحديد مسارات pyexpat يدويًا لحل مشكلة DLL
pyexpat_binaries = []
try:
    pyexpat_pyd_path = os.path.join(sys.base_prefix, 'DLLs', 'pyexpat.pyd')
    libexpat_dll_path = os.path.join(sys.base_prefix, 'Library', 'bin', 'libexpat.dll')
    if os.path.exists(pyexpat_pyd_path): pyexpat_binaries.append((pyexpat_pyd_path, '.'))
    if os.path.exists(libexpat_dll_path): pyexpat_binaries.append((libexpat_dll_path, '.'))
except Exception as e:
    print(f"تحذير: لم يتم العثور على ملفات pyexpat يدويًا: {e}")

a = Analysis(
    ['main.py'],  # تأكد أن resource_helper.py في نفس المجلد
    pathex=['.'],
    binaries=collect_dynamic_libs('PIL') + pyexpat_binaries + vlc_binaries,
    datas=datas + vlc_datas,
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
        'typing',
        'ui_components',
        'vlc',
        'vlc.libvlc',
        'vlc.libvlc_audio',
        'vlc.libvlc_media',
        'vlc.libvlc_media_player',
        'vlc.libvlc_instance',
        'winsound',
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
        'xml.parsers.expat',
        'plistlib',
        'ctypes',
        'ctypes.wintypes',
        'win32api',
        'win32con',
        'win32gui',
        'win32clipboard',
        'queue',  # لضمان عمل multiprocessing بشكل صحيح
    ] + collect_submodules('PIL'),
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
    console=False,  # Hide console for production build
    disable_windowed_traceback=False,
    icon='pray_times.ico' if os.path.exists('pray_times.ico') else None,
    version='version.txt',
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
