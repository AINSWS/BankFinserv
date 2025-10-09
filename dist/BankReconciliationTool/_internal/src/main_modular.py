"""
Main entry point for modular bank reconciliation application
"""
from tkinterdnd2 import TkinterDnD
import sys
import os

# Handle PyInstaller bundled vs development environment
def get_application_path():
    """Get the correct path for both development and PyInstaller environments"""
    if hasattr(sys, '_MEIPASS'):
        # Running in PyInstaller bundle
        return os.path.join(sys._MEIPASS, 'src')
    else:
        # Running in development
        return os.path.dirname(os.path.abspath(__file__))

# Add appropriate paths
app_path = get_application_path()
sys.path.insert(0, app_path)

# Try importing from current directory first, then from src subdirectory
try:
    from ui_modular import BankReconciliationUI
except ImportError:
    try:
        sys.path.insert(0, os.path.join(app_path, 'src'))
        from ui_modular import BankReconciliationUI
    except ImportError:
        # Final fallback - direct path
        ui_path = os.path.join(app_path, 'ui_modular.py')
        if os.path.exists(ui_path):
            import importlib.util
            spec = importlib.util.spec_from_file_location("ui_modular", ui_path)
            ui_modular = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(ui_modular)
            BankReconciliationUI = ui_modular.BankReconciliationUI
        else:
            raise ImportError("Could not find ui_modular module")

def main():
    """Main application entry point"""
    # Use TkinterDnD.Tk() instead of tk.Tk() for drag and drop support
    root = TkinterDnD.Tk()
    
    app = BankReconciliationUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()