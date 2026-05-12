import db
import datetime
from vas_mapper import auto_vas_lines, VAS_RULES
from presets_loader import get_vas_rules
import os

# Set up test environment
test_db_path = "data/test_ledger.db"
if os.path.exists(test_db_path):
    os.remove(test_db_path)

print("Starting backend test...")
conn = db.init_db(test_db_path)

# Load a preset and configure VAS_RULES
VAS_RULES.update(get_vas_rules("photocopy_print"))
print("Loaded preset: photocopy_print")

# Post a Sales transaction
tx_type = "Sales"
amount = 1100000 # 1 million + 10% VAT
lines = auto_vas_lines(tx_type, amount, vat_rate=0.10)
ref = f"SAL-{datetime.datetime.now():%y%m%d}"
eid = db.post_entry(conn, datetime.date.today().strftime("%Y-%m-%d"), ref, "Test Sale", lines, tx_type)
print(f"Posted {tx_type} transaction. Entry ID: {eid}")

# Get flat df and verify
df = db.get_flat_df(conn)
print(f"Total journal lines in DB: {len(df)}")
if len(df) == 3:
    print("Backend test PASSED.")
else:
    print("Backend test FAILED.")

# Clean up
conn.close()
if os.path.exists(test_db_path):
    os.remove(test_db_path)
