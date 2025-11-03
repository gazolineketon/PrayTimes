import winreg
import os
import sys
import subprocess
import logging

logger = logging.getLogger(__name__)

def enable_windows_notifications():
    """
    Enable Windows notifications for the application
    """
    try:
        app_name = "مواقيت الصلاة"
        
        # 1. تسجيل التطبيق في سجل النظام
        key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings"
        app_key_path = f"{key_path}\\{app_name}"
        
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, app_key_path)
            winreg.SetValueEx(key, "Enabled", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "ShowInActionCenter", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            logger.info("تم تمكين الإشعارات في سجل النظام")
        except Exception as e:
            logger.error(f"خطأ في تسجيل الإشعارات: {e}")

        # 2. تأكد من تفعيل إشعارات النظام
        try:
            # تفعيل الإشعارات عبر PowerShell
            ps_command = '''
            # تفعيل إشعارات النظام
            $notifications_key = "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Notifications\\Settings"
            if (!(Test-Path $notifications_key)) {
                New-Item -Path $notifications_key -Force | Out-Null
            }
            Set-ItemProperty -Path $notifications_key -Name "NOC_GLOBAL_SETTING_TOASTS_ENABLED" -Type DWord -Value 1

            # تفعيل إشعارات مركز الإجراءات
            $action_center_key = "HKCU:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\PushNotifications"
            if (!(Test-Path $action_center_key)) {
                New-Item -Path $action_center_key -Force | Out-Null
            }
            Set-ItemProperty -Path $action_center_key -Name "ToastEnabled" -Type DWord -Value 1
            '''

            # تشغيل PowerShell كمسؤول
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info("تم تمكين إشعارات النظام")
            
        except Exception as e:
            logger.error(f"خطأ في تفعيل إشعارات النظام: {e}")

        # 3. تسجيل التطبيق في AppUserModelID
        try:
            app_id = app_name
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                exe_path = os.path.abspath(sys.argv[0])

            shortcut_path = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\مواقيت الصلاة.lnk")
            
            # إنشاء اختصار مع AppUserModelID
            ps_shortcut = f'''
            $WshShell = New-Object -comObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
            $Shortcut.TargetPath = "{exe_path}"
            $Shortcut.Save()
            
            $folder = Split-Path "{shortcut_path}"
            if (!(Test-Path $folder)) {{
                New-Item -ItemType Directory -Path $folder -Force | Out-Null
            }}
            
            $bytes = [System.IO.File]::ReadAllBytes("{shortcut_path}")
            $bytes[0x15] = $bytes[0x15] -bor 0x20
            [System.IO.File]::WriteAllBytes("{shortcut_path}", $bytes)
            '''

            subprocess.run(
                ["powershell", "-Command", ps_shortcut],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logger.info("تم إنشاء اختصار التطبيق مع AppUserModelID")
            
        except Exception as e:
            logger.error(f"خطأ في إنشاء اختصار التطبيق: {e}")

        return True

    except Exception as e:
        logger.error(f"خطأ عام في تمكين الإشعارات: {e}")
        return False