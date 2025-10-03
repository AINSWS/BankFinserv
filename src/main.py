from tkinterdnd2 import TkinterDnD
from ui_multi import build_multi_file_ui

def main():
    root = TkinterDnD.Tk()
    build_multi_file_ui(root)
    root.mainloop()

if __name__ == "__main__":
    main()
