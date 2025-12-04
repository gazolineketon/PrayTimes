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

# إضافة ملفات TCL/TK يدوياً من Python الأساسي أو Anaconda
# Use PyInstaller's collect_all to automatically bundle all tkinter dependencies
from PyInstaller.utils.hooks import collect_all

tkinter_binaries = []
tkinter_datas = []

try:
    # Automatically collect all tkinter data and binaries
    datas_tkinter, binaries_tkinter, hiddenimports_tkinter = collect_all('tkinter')
    tkinter_datas.extend(datas_tkinter)
    tkinter_binaries.extend(binaries_tkinter)
    
    print(f"Automatically collected {len(binaries_tkinter)} binaries and {len(datas_tkinter)} data files for tkinter")
    
except Exception as e:
    print(f"خطأ في جمع ملفات tkinter: {e}")
    import traceback
    traceback.print_exc()

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

# تحديد مسارات pyexpat و ctypes يدوياً لحل مشكلة DLL
pyexpat_binaries = []
ctypes_binaries = []

try:
    base_python = sys.base_prefix
    
    # ملفات pyexpat
    possible_pyexpat_pyd = [
        os.path.join(base_python, 'DLLs', 'pyexpat.pyd'),
        os.path.join(base_python, 'Library', 'bin', 'pyexpat.pyd'),
        r'C:\Users\Nassar_Home\anaconda3\DLLs\pyexpat.pyd',
    ]
    
    possible_libexpat_dll = [
        os.path.join(base_python, 'Library', 'bin', 'libexpat.dll'),
        os.path.join(base_python, 'DLLs', 'libexpat.dll'),
        r'C:\Users\Nassar_Home\anaconda3\Library\bin\libexpat.dll',
    ]
    
    for pyd in possible_pyexpat_pyd:
        if os.path.exists(pyd):
            pyexpat_binaries.append((pyd, '.'))
            print(f"تم إضافة pyexpat.pyd: {pyd}")
            break
    
    for dll in possible_libexpat_dll:
        if os.path.exists(dll):
            pyexpat_binaries.append((dll, '.'))
            print(f"تم إضافة libexpat.dll: {dll}")
            break
    
    # ملفات ctypes (_ctypes.pyd و libffi)
    possible_ctypes_pyd = [
        os.path.join(base_python, 'DLLs', '_ctypes.pyd'),
        os.path.join(base_python, 'Library', 'bin', '_ctypes.pyd'),
        r'C:\Users\Nassar_Home\anaconda3\DLLs\_ctypes.pyd',
    ]
    
    # إضافة جميع إصدارات libffi لضمان التوافق الأقصى
    possible_libffi_dlls = [
        [  # المجموعة 1: مجلد Library/bin
            os.path.join(base_python, 'Library', 'bin', 'ffi.dll'),
            os.path.join(base_python, 'Library', 'bin', 'ffi-7.dll'),
            os.path.join(base_python, 'Library', 'bin', 'ffi-8.dll'),
            r'C:\Users\Nassar_Home\anaconda3\Library\bin\ffi.dll',
            r'C:\Users\Nassar_Home\anaconda3\Library\bin\ffi-7.dll',
            r'C:\Users\Nassar_Home\anaconda3\Library\bin\ffi-8.dll',
        ],
        [  # المجموعة 2: مجلد DLLs
            os.path.join(base_python, 'DLLs', 'ffi.dll'),
            os.path.join(base_python, 'DLLs', 'ffi-7.dll'),
            os.path.join(base_python, 'DLLs', 'ffi-8.dll'),
        ]
    ]
    
    for pyd in possible_ctypes_pyd:
        if os.path.exists(pyd):
            ctypes_binaries.append((pyd, '.'))
            print(f"تم إضافة _ctypes.pyd: {pyd}")
            break
    
    # إضافة كل ملفات libffi الموجودة (وليس أول واحد فقط)
    for dll_group in possible_libffi_dlls:
        for dll in dll_group:
            if os.path.exists(dll):
                # تحقق من عدم وجود نفس الملف مسبقاً
                if dll not in [b[0] for b in ctypes_binaries]:
                    ctypes_binaries.append((dll, '.'))
                    print(f"تم إضافة libffi DLL: {dll}")
    
    print(f"تم جمع {len(pyexpat_binaries)} ملفات pyexpat و {len(ctypes_binaries)} ملفات ctypes")
    
except Exception as e:
    print(f"تحذير: خطأ في جمع ملفات pyexpat/ctypes: {e}")
    import traceback
    traceback.print_exc()

a = Analysis(
    ['main.py'],  # تأكد أن resource_helper.py في نفس المجلد
    pathex=['.'],
    binaries=collect_dynamic_libs('PIL') + pyexpat_binaries + ctypes_binaries + vlc_binaries + tkinter_binaries,
    datas=datas + vlc_datas + tkinter_datas,
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
    excludes=['test', 'setuptools.glob', 'setuptools.config', 'setuptools.config.setup'],  # استبعاد setuptools المشاكل
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
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='pray_times.ico',
    version='version.txt',
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
)

