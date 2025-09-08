import sys
import os
import time
import subprocess

def restart_app():
    """إعادة تشغيل التطبيق"""
    if len(sys.argv) > 1:
        main_script = sys.argv[1]
        time.sleep(1)
        subprocess.Popen([sys.executable, main_script])

if __name__ == "__main__":
    restart_app()
