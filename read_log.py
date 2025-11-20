
import os
import sys

def read_log():
    app_data = os.environ.get('APPDATA', '')
    log_file = os.path.join(app_data, 'PrayTimes', 'logs', 'prayer_app.log')
    
    print(f"Reading log file: {log_file}")
    
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"Total lines: {len(lines)}")
                print("Last 20 lines:")
                for line in lines[-20:]:
                    print(line.strip())
        except Exception as e:
            print(f"Error reading log file: {e}")
    else:
        print("Log file does not exist.")

if __name__ == "__main__":
    read_log()
