# -*- coding: utf-8 -*-
import re
import subprocess
from pathlib import Path

def update_version():
    """
    يقوم هذا البرنامج النصي بتحديث __version__ تلقائيًا في main.py استنادًا إلى العدد الإجمالي لعمليات تثبيت بـ git.
    """
    try:
        # الحصول على العدد الإجمالي للتثبيتات
        commit_count = subprocess.check_output(['git', 'rev-list', '--count', 'HEAD']).strip().decode('utf-8')
        
        # تعريف الإصدار الجديد
        new_version = f"0.{commit_count}.0"
        
        # المسار لـ main.py
        main_py_path = Path(__file__).parent / 'main.py'
        
        # قراءة محتوى main.py
        content = main_py_path.read_text(encoding='utf-8')
        
        # بحث واستبدال الإصدار
        old_version_pattern = re.compile(r'__version__\s*=\s*"[^"]+"')
        if old_version_pattern.search(content):
            new_content = old_version_pattern.sub(f'__version__ = "{new_version}"', content)
            
            # كتابة المحتوى الجديد إلى main.py
            main_py_path.write_text(new_content, encoding='utf-8')
            
            print(f"Successfully updated version in main.py to {new_version}")
        else:
            print("Error: __version__ variable not found in main.py")
        
        # المسار لـ README.md
        readme_path = Path(__file__).parent / 'README.md'
        if readme_path.exists():
            readme_content = readme_path.read_text(encoding='utf-8')
            
            # Regex لتحديث شارة الإصدار
            readme_pattern = re.compile(r'(https://img.shields.io/badge/Version-)[\d.]+(-orange\.svg)')
            if readme_pattern.search(readme_content):
                # استبدال الإصدار القديم بالجديد
                new_readme_content = readme_pattern.sub(rf'\g<1>{new_version}\g<2>', readme_content)
                
                # كتابة المحتوى المحدث إلى README.md
                readme_path.write_text(new_readme_content, encoding='utf-8')
                
                print(f"Successfully updated version in README.md to {new_version}")
            else:
                print("Warning: Version badge not found in README.md")
        else:
            print("Warning: README.md not found.")

    except FileNotFoundError:
        print("Error: 'git' command not found. Make sure Git is installed and in your PATH.")
    except subprocess.CalledProcessError:
        print("Error: Not a git repository or no commits found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    update_version()
