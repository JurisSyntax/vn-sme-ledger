import os, datetime, json, shutil, zipfile, sys
import config
import urllib.parse

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_vietqr_url(settings, amount, description=""):
    """
    Generate a VietQR (Napas 247) image URL for payments.
    Reference: https://vietqr.io/
    """
    bank_name = settings.get("bank_name", "Vietcombank")
    account_no = settings.get("bank_account", "")
    account_name = settings.get("company_name", "")
    
    if not account_no:
        return None
        
    bank_id = config.NAPAS_BANKS.get(bank_name, "970436") # Default to VCB
    
    # Template: 'compact' or 'print'
    template = "compact" 
    
    # URL encoded parameters
    note = urllib.parse.quote(description[:25]) # Limit note length
    name = urllib.parse.quote(account_name)
    
    url = f"https://img.vietqr.io/image/{bank_id}-{account_no}-{template}.jpg?amount={int(amount)}&addInfo={note}&accountName={name}"
    return url

LOG_DIR = "data/logs"
MAX_LOG_FILES = 3
MAX_LOG_SIZE_KB = 50

def log_activity(msg):
    if not os.path.exists(LOG_DIR): os.makedirs(LOG_DIR)
    
    # Get current log file (latest)
    logs = sorted([f for f in os.listdir(LOG_DIR) if f.startswith("activity_")], reverse=True)
    
    current_log = None
    if logs:
        last_log = os.path.join(LOG_DIR, logs[0])
        if os.path.getsize(last_log) < MAX_LOG_SIZE_KB * 1024:
            current_log = last_log
            
    if not current_log:
        # Create new log file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        current_log = os.path.join(LOG_DIR, f"activity_{timestamp}.log")
        
        # Rotate if too many
        if len(logs) >= MAX_LOG_FILES:
            os.remove(os.path.join(LOG_DIR, logs[-1]))
            
    with open(current_log, "a", encoding="utf-8") as f:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {msg}\n")

def get_recent_activities(limit=8):
    if not os.path.exists(LOG_DIR): return []
    logs = sorted([f for f in os.listdir(LOG_DIR) if f.startswith("activity_")], reverse=True)
    all_lines = []
    for l in logs:
        with open(os.path.join(LOG_DIR, l), "r", encoding="utf-8") as f:
            all_lines.extend(f.readlines())
    return [line.strip() for line in all_lines[-limit:][::-1]]

def create_backup():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/SME_Ledger_Backup_{timestamp}.zip"
    if not os.path.exists("backups"): os.makedirs("backups")
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk("data"):
            for file in files:
                zipf.write(os.path.join(root, file))
        for root, dirs, files in os.walk("docs"):
            for file in files:
                zipf.write(os.path.join(root, file))
    return backup_path
