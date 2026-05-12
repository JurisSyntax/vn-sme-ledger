import requests, shutil, os
from datetime import datetime
import db, tax_engine

def is_online():
    for url in ["https://www.google.com", "https://1.1.1.1"]:
        try:
            requests.get(url, timeout=3)
            return True
        except:
            pass
    return False

def run_sync(conn):
    if not is_online():
        raise ConnectionError("Không có kết nối Internet. Đang hoạt động offline.\n(No internet. Working offline.)")
    os.makedirs("data/backups", exist_ok=True)
    shutil.copy("data/ledger.db", f"data/backups/ledger_{datetime.now():%Y%m%d_%H%M%S}.db")
    tax_engine.update_tax_online()
    print("Sync complete.")

def upload_to_cloud(file_path, settings):
    """
    Uploads the database to a cloud endpoint (Webhook or SFTP).
    """
    method = settings.get("backup_method", "none")
    if method == "webhook":
        url = settings.get("backup_webhook_url")
        if not url: return "Missing Webhook URL"
        try:
            with open(file_path, 'rb') as f:
                r = requests.post(url, files={'file': f}, timeout=30)
            return f"Webhook: {r.status_code}"
        except Exception as e: return f"Webhook Error: {e}"
    
    elif method == "sftp":
        # Requires paramiko, fallback to simple message if not installed
        try:
            import paramiko
            host = settings.get("backup_sftp_host")
            user = settings.get("backup_sftp_user")
            pwd = settings.get("backup_sftp_pass")
            port = int(settings.get("backup_sftp_port", 22))
            if not all([host, user, pwd]): return "Missing SFTP credentials"
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port, user, pwd)
            sftp = ssh.open_sftp()
            sftp.put(file_path, f"ledger_backup_{datetime.now():%Y%m%d_%H%M%S}.db")
            sftp.close(); ssh.close()
            return "SFTP Success"
        except ImportError:
            return "SFTP: paramiko not installed"
        except Exception as e: return f"SFTP Error: {e}"
    
    return "No cloud method selected"
