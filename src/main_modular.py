"""
Main entry point for modular bank reconciliation application
"""
from tkinterdnd2 import TkinterDnD
import sys
import os

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from ui_modular import BankReconciliationUI

def main():
    """Main application entry point"""
    # Use TkinterDnD.Tk() instead of tk.Tk() for drag and drop support
    root = TkinterDnD.Tk()
    
    app = BankReconciliationUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()