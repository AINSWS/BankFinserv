import tkinter as tk
from tkinterdnd2 import TkinterDnD

def test_window():
    print("Creating test window...")
    root = TkinterDnD.Tk()
    root.title("Test Excel Uploader")  # Removed emoji characters
    root.geometry("400x300")
    root.configure(bg="#0f1419")
    
    label = tk.Label(root, text="Test Window - Can you see this?", 
                    font=("Arial", 16), fg="white", bg="#0f1419")
    label.pack(expand=True)
    
    print("Window created, starting mainloop...")
    root.mainloop()
    print("Window closed.")

if __name__ == "__main__":
    test_window()