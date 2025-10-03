import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from uploader import handle_excel, handle_multiple_files
import os


def build_ui(root):
    # Configure main window with responsive design
    root.title("🚀 Excel File Comparison Tool")  # Updated title
    root.geometry("800x600")  # Larger window for multiple files
    root.minsize(700, 500)    # Larger minimum size
    root.configure(bg="#0f1419")
    root.resizable(True, True)  # Allow resizing
    
    # Make sure window appears on top and is visible
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(lambda: root.attributes('-topmost', False))
    
    # Global variables for file management
    global uploaded_files, file_slots, current_file_count, target_file_count
    uploaded_files = {}  # Dictionary to store uploaded file data
    file_slots = []      # List to store file slot widgets
    current_file_count = 0
    target_file_count = 2  # Default to 2 files
    
    # Configure modern style
    style = ttk.Style()
    style.theme_use('clam')
    
    # Create main container with responsive padding
    main_container = tk.Frame(root, bg="#0f1419")
    main_container.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Header section - responsive
    header_frame = tk.Frame(main_container, bg="#0f1419")
    header_frame.pack(fill="x", pady=(0, 15))
    
    title_label = tk.Label(
        header_frame,
        text="📊 Excel File Uploader",  # Added emoji back
        font=("Segoe UI", 24, "bold"),  # Slightly smaller for better fit
        fg="#00d4aa",
        bg="#0f1419"
    )
    title_label.pack()
    
    subtitle_label = tk.Label(
        header_frame,
        text="Upload your Excel files with modern drag & drop interface",
        font=("Segoe UI", 11),  # Slightly smaller for better fit
        fg="#8a92a3",
        bg="#0f1419",
        wraplength=500  # Allow text to wrap on smaller windows
    )
    subtitle_label.pack(pady=(5, 0))
    
    # Main upload area
    upload_container = tk.Frame(main_container, bg="#0f1419")
    upload_container.pack(fill="both", expand=True)
    
    # Drag & Drop area with responsive styling
    drop_frame = tk.Frame(
        upload_container,
        bg="#1a1f29",
        relief="solid",
        bd=2,
        highlightbackground="#00d4aa",
        highlightthickness=0
    )
    drop_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Inner content frame - responsive padding
    content_frame = tk.Frame(drop_frame, bg="#1a1f29")
    content_frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Upload icon and text - responsive sizing
    icon_label = tk.Label(
        content_frame,
        text="📁",
        font=("Segoe UI", 36),  # Beautiful emoji icon
        fg="#00d4aa",
        bg="#1a1f29"
    )
    icon_label.pack(pady=(10, 8))
    
    main_text = tk.Label(
        content_frame,
        text="Drag & Drop your Excel file here",
        font=("Segoe UI", 16, "bold"),  # Responsive font size
        fg="#ffffff",
        bg="#1a1f29",
        wraplength=400  # Allow text wrapping
    )
    main_text.pack()
    
    sub_text = tk.Label(
        content_frame,
        text="or click the button below to browse",
        font=("Segoe UI", 11),  # Responsive font size
        fg="#8a92a3",
        bg="#1a1f29",
        wraplength=350  # Allow text wrapping
    )
    sub_text.pack(pady=(5, 15))
    
    # Supported formats
    formats_text = tk.Label(
        content_frame,
        text="Supported formats: .xlsx, .xls",
        font=("Segoe UI", 9),  # Smaller font
        fg="#5a6270",
        bg="#1a1f29"
    )
    formats_text.pack()
    
    # Modern Browse Button
    def browse_file():
        file_path = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        if file_path:
            update_ui_on_file_select(os.path.basename(file_path))
            handle_excel(file_path, on_success_callback, on_error_callback)

    browse_btn = tk.Button(
        content_frame,
        text="🗂️  Browse Files",
        command=browse_file,
        font=("Segoe UI", 11, "bold"),  # Responsive font size
        fg="#ffffff",
        bg="#00d4aa",
        activebackground="#00b894",
        activeforeground="#ffffff",
        relief="flat",
        padx=25,  # Responsive padding
        pady=10,
        cursor="hand2"
    )
    browse_btn.pack(pady=(15, 0))
    
    # Status area - responsive
    status_frame = tk.Frame(main_container, bg="#0f1419")
    status_frame.pack(fill="x", pady=(15, 0))
    
    global status_label, progress_bar
    status_label = tk.Label(
        status_frame,
        text="Ready to upload...",
        font=("Segoe UI", 10),  # Responsive font size
        fg="#8a92a3",
        bg="#0f1419",
        wraplength=450  # Allow text wrapping
    )
    status_label.pack()
    
    # Progress bar (initially hidden) - responsive width
    progress_bar = ttk.Progressbar(
        status_frame,
        mode='indeterminate',
        length=250,  # Smaller default length
        style='Modern.Horizontal.TProgressbar'
    )
    
    # Configure progress bar style
    style.configure(
        'Modern.Horizontal.TProgressbar',
        background='#00d4aa',
        troughcolor='#2c3440',
        borderwidth=0,
        lightcolor='#00d4aa',
        darkcolor='#00d4aa'
    )
    
    # Hover effects for drag area
    def on_enter(event):
        drop_frame.configure(highlightthickness=2, highlightbackground="#00d4aa")
        icon_label.configure(fg="#00ff7f")
        main_text.configure(fg="#00d4aa")
    
    def on_leave(event):
        drop_frame.configure(highlightthickness=0)
        icon_label.configure(fg="#00d4aa")
        main_text.configure(fg="#ffffff")
    
    # Bind hover effects
    drop_frame.bind("<Enter>", on_enter)
    drop_frame.bind("<Leave>", on_leave)
    content_frame.bind("<Enter>", on_enter)
    content_frame.bind("<Leave>", on_leave)
    
    # File selection UI updates
    def update_ui_on_file_select(filename):
        status_label.configure(text=f"Selected: {filename}", fg="#00d4aa")
        progress_bar.pack(pady=(10, 0))
        progress_bar.start(10)
    
    def on_success_callback(message):
        progress_bar.stop()
        progress_bar.pack_forget()
        status_label.configure(text="✅ File uploaded successfully!", fg="#00d4aa")
        root.after(3000, lambda: status_label.configure(text="Ready to upload...", fg="#8a92a3"))
    
    def on_error_callback(error_message):
        progress_bar.stop()
        progress_bar.pack_forget()
        status_label.configure(text=f"❌ Error: {error_message}", fg="#ff6b6b")
        root.after(5000, lambda: status_label.configure(text="Ready to upload...", fg="#8a92a3"))
    
    # Enhanced drag & drop functionality
    def on_drop(event):
        file_path = event.data.strip('{}')  # Handle spaces in paths
        if file_path.lower().endswith(('.xlsx', '.xls')):
            filename = os.path.basename(file_path)
            update_ui_on_file_select(filename)
            handle_excel(file_path, on_success_callback, on_error_callback)
        else:
            on_error_callback("Please select a valid Excel file (.xlsx or .xls)")
    
    def on_drag_enter(event):
        drop_frame.configure(bg="#2c3440", highlightthickness=3, highlightbackground="#00d4aa")
        main_text.configure(text="Drop your file here!", fg="#00d4aa")
        icon_label.configure(text="📥", fg="#00ff7f")
    
    def on_drag_leave(event):
        drop_frame.configure(bg="#1a1f29", highlightthickness=0)
        main_text.configure(text="Drag & Drop your Excel file here", fg="#ffffff")
        icon_label.configure(text="📁", fg="#00d4aa")
    
    # Register drag & drop events
    drop_frame.drop_target_register(DND_FILES)
    drop_frame.dnd_bind('<<Drop>>', on_drop)
    drop_frame.dnd_bind('<<DragEnter>>', on_drag_enter)
    drop_frame.dnd_bind('<<DragLeave>>', on_drag_leave)
    
    # Responsive behavior - adjust elements based on window size
    def on_window_resize(event):
        if event.widget != root:  # Only respond to root window resize
            return
            
        try:
            width = root.winfo_width()
            
            # Adjust font sizes based on window width
            if width < 600:
                # Small window
                title_label.configure(font=("Segoe UI", 18, "bold"))
                subtitle_label.configure(font=("Segoe UI", 9))
                main_text.configure(font=("Segoe UI", 14, "bold"))
                sub_text.configure(font=("Segoe UI", 10))
                browse_btn.configure(font=("Segoe UI", 10, "bold"), padx=20, pady=8)
                icon_label.configure(font=("Segoe UI", 28))
                if progress_bar.winfo_exists():
                    progress_bar.configure(length=200)
            elif width < 750:
                # Medium window
                title_label.configure(font=("Segoe UI", 22, "bold"))
                subtitle_label.configure(font=("Segoe UI", 10))
                main_text.configure(font=("Segoe UI", 15, "bold"))
                sub_text.configure(font=("Segoe UI", 10))
                browse_btn.configure(font=("Segoe UI", 10, "bold"), padx=22, pady=9)
                icon_label.configure(font=("Segoe UI", 32))
                if progress_bar.winfo_exists():
                    progress_bar.configure(length=250)
            else:
                # Large window
                title_label.configure(font=("Segoe UI", 26, "bold"))
                subtitle_label.configure(font=("Segoe UI", 11))
                main_text.configure(font=("Segoe UI", 16, "bold"))
                sub_text.configure(font=("Segoe UI", 11))
                browse_btn.configure(font=("Segoe UI", 11, "bold"), padx=25, pady=10)
                icon_label.configure(font=("Segoe UI", 36))
                if progress_bar.winfo_exists():
                    progress_bar.configure(length=300)
                    
        except (tk.TclError, AttributeError):
            # Ignore any errors during resize
            pass
    
    # Bind resize event
    root.bind('<Configure>', on_window_resize)
    
    # Center window on screen
    def center_window():
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
    
    # Center the window after initial setup
    root.after(100, center_window)
