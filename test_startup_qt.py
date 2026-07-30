import sys
import traceback
from PyQt6.QtWidgets import QApplication

try:
    print("Initializing PyQt6 Application...")
    app = QApplication(sys.argv)
    
    # Import the main window class
    import main_qt
    
    print("Instantiating VnSmeLedgerApp...")
    window = main_qt.VnSmeLedgerApp()
    print("SUCCESS")
    
    # Clean up
    window.close()
    
except Exception as e:
    print("CRASH!")
    traceback.print_exc()
    sys.exit(1)
