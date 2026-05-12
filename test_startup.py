import config, traceback, sys
import main

try:
    s = config.load_settings()
    s["language"] = "en"
    config.save_settings(s)
    
    print("Initializing App...")
    app = main.App()
    print("SUCCESS")
    
    if "--interactive" in sys.argv:
        print("Starting mainloop (Close window to finish test)...")
        app.mainloop()
    else:
        app.destroy()
        
except Exception as e:
    print("CRASH!")
    traceback.print_exc()
    sys.exit(1)
