
# create_installer.py
# إنشاء حزمة تثبيت احترافية للبرنامج

import os
import sys
import shutil
import subprocess
import platform
import tempfile
import logging

logger = logging.getLogger(__name__)

def create_installer():
    """إنشاء حزمة تثبيت للبرنامج"""
    try:
        # التحقق من وجود PyInstaller
        try:
            import PyInstaller
            logger.info("PyInstaller موجود")
        except ImportError:
            logger.error("PyInstaller غير مثبت. يرجى تثبيته باستخدام: pip install pyinstaller")
            return False

        # بناء التطبيق باستخدام ملف المواصفات
        logger.info("بدء بناء التطبيق...")
        # Using a list of arguments for safety against command injection
        pyinstaller_args = [sys.executable, "-m", "PyInstaller", "main.spec", "--clean"]
        try:
            result = subprocess.run(pyinstaller_args, 
                                 capture_output=True, 
                                 text=True,
                                 check=True)  # Will raise CalledProcessError if return code != 0
        except subprocess.CalledProcessError as e:
            logger.error(f"فشل بناء التطبيق: {e.stderr}")
            return False

        logger.info("تم بناء التطبيق بنجاح")

        # إنشاء حزمة تثبيت
        logger.info("إنشاء حزمة تثبيت...")

        # استخدام NSIS لإنشاء حزمة تثبيت (موجود في معظم أنظمة ويندوز)
        nsis_path = find_nsis()
        if nsis_path:
            logger.info(f"NSIS موجود في: {nsis_path}")
            create_nsis_installer(nsis_path)
        else:
            logger.warning("NSIS غير موجود. سيتم إنشاء حزمة ZIP كبديل.")
            create_zip_installer()

        return True
    except Exception as e:
        logger.error(f"خطأ في إنشاء حزمة التثبيت: {e}")
        return False

def find_nsis():
    """البحث عن NSIS في النظام"""
    nsis_paths = [
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "NSIS"),
        os.path.join(os.environ.get("ProgramFiles", ""), "NSIS"),
        "C:\NSIS",
        "D:\NSIS",
    ]

    for path in nsis_paths:
        if os.path.exists(path):
            makensis = os.path.join(path, "makensis.exe")
            if os.path.exists(makensis):
                return makensis

    return None

def create_nsis_installer(nsis_path):
    """إنشاء حزمة تثبيت باستخدام NSIS"""
    try:
        # إنشاء ملف NSIS Script
        nsis_script = """
!define APPNAME "PrayerTimes"
!define VERSION "0.53.0"
!define PUBLISHER "PrayerTimes Developer"
!define URL "https://example.com"

RequestExecutionLevel admin

; واجهة التثبيت الحديثة
!include "MUI2.nsh"

; الواجهة
!define MUI_ABORTWARNING
!define MUI_ICON "pray_times.ico"
!define MUI_UNICON "pray_times.ico"

; الصفحات
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "EULA.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; اللغات
!insertmacro MUI_LANGUAGE "Arabic"
!insertmacro MUI_LANGUAGE "English"

; المعلومات
Name "${APPNAME}"
OutFile "PrayerTimesInstaller.exe"
InstallDir "$PROGRAMFILES\${APPNAME}"
InstallDirRegKey HKLM "Software\${APPNAME}" "InstallPath"

; المكونات
Section "Main Program" SecMain
    SectionIn RO

    SetOutPath "$INSTDIR"
    File /r "dist\Praytimes\*"

    ; إنشاء اختصارات
    CreateDirectory "$SMPROGRAMS\${APPNAME}"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\Praytimes.exe"
    CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\uninstall.exe"

    ; تسجيل التثبيت
    WriteRegStr HKLM "Software\${APPNAME}" "InstallPath" "$INSTDIR"
    WriteRegStr HKLM "Software\${APPNAME}" "Version" "${VERSION}"

    ; إنشاء مثبّت الإزالة
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; تسجيل البرنامج في إضافة/إزالة البرامج
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "URLInfoAbout" "${URL}"
SectionEnd

; قسم الإزالة
Section "Uninstall"
    Delete "$INSTDIR\uninstall.exe"
    RMDir /r "$INSTDIR"

    Delete "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk"
    Delete "$SMPROGRAMS\${APPNAME}\Uninstall.lnk"
    RMDir "$SMPROGRAMS\${APPNAME}"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
    DeleteRegKey HKLM "Software\${APPNAME}"
SectionEnd
"""

        # حفظ ملف NSIS Script
        nsis_file = os.path.join(os.getcwd(), "installer.nsi")
        with open(nsis_file, "w", encoding="utf-8") as f:
            f.write(nsis_script)

        # Validate NSIS path and script path
        if not os.path.isfile(nsis_path) or not os.path.isfile(nsis_file):
            logger.error("Invalid NSIS or script path")
            return False

        # Using a list of arguments and validating paths for safety against command injection
        nsis_args = [nsis_path, nsis_file]
        try:
            result = subprocess.run(nsis_args, 
                                 capture_output=True, 
                                 text=True,
                                 check=True)  # Will raise CalledProcessError if return code != 0
        except subprocess.CalledProcessError as e:
            logger.error(f"فشل إنشاء حزمة تثبيت NSIS: {e.stderr}")
            return False

        logger.info("تم إنشاء حزمة تثبيت NSIS بنجاح")
        return True
    except Exception as e:
        logger.error(f"خطأ في إنشاء حزمة تثبيت NSIS: {e}")
        return False

def create_zip_installer():
    """إنشاء حزمة تثبيت بصيغة ZIP"""
    try:
        import zipfile

        # إنشاء ملف ZIP
        zip_path = os.path.join(os.getcwd(), f"PrayerTimesPortable.zip")

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # إضافة ملفات التطبيق
            app_dir = os.path.join(os.getcwd(), "dist", "Praytimes")
            for root, dirs, files in os.walk(app_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, app_dir)
                    zipf.write(file_path, arcname)

            # إضافة ملف تشغيل
            run_script = """@echo off
echo جاري تشغيل PrayerTimes...
cd /d "%~dp0"
start Praytimes.exe
"""
            zipf.writestr("run.bat", run_script)

        logger.info(f"تم إنشاء حزمة ZIP بنجاح: {zip_path}")
        return True
    except Exception as e:
        logger.error(f"خطأ في إنشاء حزمة ZIP: {e}")
        return False

def setup_logging():
    """إعداد التسجيل"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("installer.log"),
            logging.StreamHandler()
        ]
    )

def main():
    """الوظيفة الرئيسية لإنشاء الحزمة"""
    setup_logging()
    logger.info("بدء عملية إنشاء حزمة التثبيت...")

    if create_installer():
        logger.info("اكتملت عملية إنشاء حزمة التثبيت بنجاح")
    else:
        logger.error("فشلت عملية إنشاء حزمة التثبيت")

if __name__ == "__main__":
    main()
