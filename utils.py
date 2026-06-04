import os, datetime, json, shutil, zipfile, sys
import urllib.parse
import config

CURRENT_VERSION = "Beta v2"

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
    Generate a VietQR (Napas 247) payment QR image URL.
    Returns URL string or None if bank account not configured.
    Reference: https://vietqr.io/
    """
    bank_name = settings.get("bank_name", "Vietcombank")
    account_no = settings.get("bank_account", "")
    account_name = settings.get("company_name", "")

    if not account_no:
        return None

    bank_id = config.NAPAS_BANKS.get(bank_name, "970436")  # Default VCB
    template = "compact2"
    note = urllib.parse.quote(str(description)[:25])
    name = urllib.parse.quote(str(account_name))

    return (
        f"https://img.vietqr.io/image/{bank_id}-{account_no}-{template}.jpg"
        f"?amount={int(amount)}&addInfo={note}&accountName={name}"
    )


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


def check_for_updates():
    """Optional online update check. Called only when update_check_enabled is true."""
    try:
        import re
        import requests

        repo = "JurisSyntax/vn-sme-ledger"
        url = f"https://api.github.com/repos/{repo}/releases/latest"
        response = requests.get(url, headers={"User-Agent": "VN-SME-Ledger-Updater"}, timeout=5)
        if response.status_code != 200:
            return False, "", "", ""
        data = response.json()
        latest_version = data.get("tag_name", "").strip()
        release_notes = data.get("body", "")
        download_url = data.get("html_url", "")
        if not latest_version or latest_version == CURRENT_VERSION:
            return False, "", "", ""
        latest_num = re.findall(r"\d+", latest_version)
        current_num = re.findall(r"\d+", CURRENT_VERSION)
        if latest_num and current_num and int(latest_num[0]) <= int(current_num[0]):
            return False, "", "", ""
        return True, latest_version, release_notes, download_url
    except Exception:
        return False, "", "", ""


def prompt_update(parent_widget=None):
    """Prompt for an online update only after the user opted in."""
    try:
        import webbrowser
        from tkinter import messagebox

        available, version, notes, url = check_for_updates()
        if not available:
            return
        msg = f"Đã có phiên bản mới: {version} (Phiên bản hiện tại: {CURRENT_VERSION})\n\n"
        if notes:
            msg += f"Thông tin cập nhật:\n{notes[:300]}...\n\n"
        msg += "Bạn có muốn mở trang tải xuống bản cập nhật mới không?"
        if messagebox.askyesno("Cập nhật phần mềm", msg, parent=parent_widget):
            webbrowser.open(url)
    except Exception:
        pass
