import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from uploader import handle_excel
import pandas as pd
import os
from datetime import datetime


def build_multi_file_ui(root):
    # Configure main window
    root.title("🚀 Excel/CSV File Comparison Tool")
    root.geometry("900x700")
    root.minsize(800, 600)
    root.configure(bg="#0f1419")
    root.resizable(True, True)
    
    # Make sure window appears on top
    root.lift()
    root.attributes('-topmost', True)
    root.after_idle(lambda: root.attributes('-topmost', False))
    
    # Global variables for file management
    global uploaded_files, file_slots, current_file_count, target_file_count, files_container
    uploaded_files = {}
    file_slots = []
    current_file_count = 0
    target_file_count = 2
    
    # Configure modern style
    style = ttk.Style()
    style.theme_use('clam')
    style.configure(
        'Modern.Horizontal.TProgressbar',
        background='#00d4aa',
        troughcolor='#2c3440',
        borderwidth=0,
        lightcolor='#00d4aa',
        darkcolor='#00d4aa'
    )
    
    # Create main container
    main_container = tk.Frame(root, bg="#0f1419")
    main_container.pack(fill="both", expand=True, padx=15, pady=15)
    
    # Header section
    header_frame = tk.Frame(main_container, bg="#0f1419")
    header_frame.pack(fill="x", pady=(0, 20))
    
    title_label = tk.Label(
        header_frame,
        text="📊 Excel/CSV File Comparison Tool",
        font=("Segoe UI", 22, "bold"),
        fg="#00d4aa",
        bg="#0f1419"
    )
    title_label.pack()
    
    subtitle_label = tk.Label(
        header_frame,
        text="Upload multiple Excel/CSV files for comparison and analysis",
        font=("Segoe UI", 11),
        fg="#8a92a3",
        bg="#0f1419",
        wraplength=600
    )
    subtitle_label.pack(pady=(5, 0))
    
    # Control panel
    control_frame = tk.Frame(main_container, bg="#1a1f29", relief="solid", bd=1)
    control_frame.pack(fill="x", pady=(0, 20), padx=5)
    
    control_inner = tk.Frame(control_frame, bg="#1a1f29")
    control_inner.pack(fill="x", padx=15, pady=15)
    
    # File count selection
    count_label = tk.Label(
        control_inner,
        text="🔢 Number of files to compare:",
        font=("Segoe UI", 12, "bold"),
        fg="#ffffff",
        bg="#1a1f29"
    )
    count_label.pack(side="left")
    
    file_count_var = tk.StringVar(value="2")
    count_spinbox = tk.Spinbox(
        control_inner,
        from_=2,
        to=10,
        width=5,
        textvariable=file_count_var,
        font=("Segoe UI", 11),
        bg="#2c3440",
        fg="#ffffff",
        buttonbackground="#00d4aa",
        relief="flat",
        bd=2
    )
    count_spinbox.pack(side="left", padx=(10, 15))
    
    # File slots container (scrollable with grid layout)
    files_frame = tk.Frame(main_container, bg="#0f1419")
    files_frame.pack(fill="both", expand=True)
    
    # Canvas for scrollable content
    canvas = tk.Canvas(files_frame, bg="#0f1419", highlightthickness=0)
    scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=canvas.yview)
    files_container = tk.Frame(canvas, bg="#0f1419")
    
    files_container.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=files_container, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Variables for grid layout
    global grid_columns
    grid_columns = 2  # Default to 2 columns
    
    # Functions for file management
    def create_file_slots():
        # Clear existing slots
        for widget in files_container.winfo_children():
            widget.destroy()
        file_slots.clear()
        global current_file_count
        current_file_count = 0
        
        # Calculate responsive grid layout
        calculate_grid_layout()
        
        # Create new slots in grid layout
        for i in range(target_file_count):
            row = i // grid_columns
            col = i % grid_columns
            create_file_slot(i + 1, row, col)
        
        # Update canvas scroll region
        files_container.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def calculate_grid_layout():
        """Calculate optimal grid layout based on window width and file count"""
        global grid_columns
        
        # Get current window width
        root.update_idletasks()
        window_width = canvas.winfo_width()
        
        # Calculate optimal columns based on window width
        # Minimum slot width: 300px, preferred: 350px
        if window_width < 300:
            grid_columns = 1
        elif window_width < 650:
            grid_columns = 1
        elif window_width < 1000:
            grid_columns = 2
        elif window_width < 1350:
            grid_columns = 3
        else:
            grid_columns = 4
        
        # Don't exceed the number of files
        grid_columns = min(grid_columns, target_file_count)
    
    def create_file_slot(slot_number, row, col):
        slot_frame = tk.Frame(files_container, bg="#1a1f29", relief="solid", bd=1)
        # Use grid layout with padding
        slot_frame.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
        
        # Configure grid weights for responsive behavior
        files_container.grid_columnconfigure(col, weight=1, minsize=300)
        files_container.grid_rowconfigure(row, weight=0)
        
        # Slot header - more compact for grid layout
        header_frame = tk.Frame(slot_frame, bg="#1a1f29")
        header_frame.pack(fill="x", padx=10, pady=(10, 8))
        
        slot_label = tk.Label(
            header_frame,
            text=f"📋 File {slot_number}",
            font=("Segoe UI", 11, "bold"),
            fg="#00d4aa",
            bg="#1a1f29"
        )
        slot_label.pack(side="left")
        
        # Status label
        status_label = tk.Label(
            header_frame,
            text="⚪ Empty",
            font=("Segoe UI", 9),
            fg="#8a92a3",
            bg="#1a1f29"
        )
        status_label.pack(side="right")
        
        # Drop area - compact for grid
        drop_frame = tk.Frame(
            slot_frame,
            bg="#2c3440",
            relief="ridge",
            bd=2,
            height=100
        )
        drop_frame.pack(fill="x", padx=10, pady=(0, 8))
        drop_frame.pack_propagate(False)
        
        # Drop content
        drop_content = tk.Frame(drop_frame, bg="#2c3440")
        drop_content.pack(expand=True, fill="both")
        
        file_icon = tk.Label(
            drop_content,
            text="📁",
            font=("Segoe UI", 20),
            fg="#8a92a3",
            bg="#2c3440"
        )
        file_icon.pack(pady=(8, 3))
        
        drop_text = tk.Label(
            drop_content,
            text="Drag & Drop file here\nor click Browse",
            font=("Segoe UI", 9),
            fg="#8a92a3",
            bg="#2c3440",
            justify="center"
        )
        drop_text.pack()
        
        # Buttons frame - more compact
        buttons_frame = tk.Frame(slot_frame, bg="#1a1f29")
        buttons_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Browse button
        def browse_file_for_slot():
            file_path = filedialog.askopenfilename(
                title=f"Select Excel/CSV File for Slot {slot_number}",
                filetypes=[
                    ("Excel Files", "*.xlsx *.xls"),
                    ("CSV Files", "*.csv"),
                    ("All Files", "*.*")
                ]
            )
            if file_path:
                load_file_to_slot(slot_number, file_path)
        
        browse_btn = tk.Button(
            buttons_frame,
            text="🗂️ Browse",
            command=browse_file_for_slot,
            font=("Segoe UI", 8, "bold"),
            fg="#ffffff",
            bg="#00d4aa",
            activebackground="#00b894",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2"
        )
        browse_btn.pack(side="left")
        
        # Clear button
        def clear_slot():
            if slot_number in uploaded_files:
                del uploaded_files[slot_number]
                global current_file_count
                current_file_count -= 1
            
            # Reset slot appearance
            status_label.configure(text="⚪ Empty", fg="#8a92a3")
            drop_frame.configure(bg="#2c3440", relief="ridge")
            drop_content.configure(bg="#2c3440")
            file_icon.configure(text="📁", fg="#8a92a3", bg="#2c3440")
            drop_text.configure(text="Drag & Drop file here\nor click Browse", bg="#2c3440")
            clear_btn.configure(state="disabled")
            
            update_compare_button_state()
        
        clear_btn = tk.Button(
            buttons_frame,
            text="🗑️ Clear",
            command=clear_slot,
            font=("Segoe UI", 8, "bold"),
            fg="#ffffff",
            bg="#ff6b6b",
            activebackground="#ff5252",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            state="disabled"
        )
        clear_btn.pack(side="left", padx=(8, 0))
        
        # File info label (initially hidden)
        info_label = tk.Label(
            slot_frame,
            text="",
            font=("Segoe UI", 9),
            fg="#8a92a3",
            bg="#1a1f29",
            wraplength=400
        )
        
        # Store references
        slot_data = {
            'frame': slot_frame,
            'status_label': status_label,
            'drop_frame': drop_frame,
            'drop_content': drop_content,
            'file_icon': file_icon,
            'drop_text': drop_text,
            'clear_btn': clear_btn,
            'info_label': info_label,
            'browse_btn': browse_btn
        }
        file_slots.append(slot_data)
        
        # Drag & drop functionality
        def on_drop(event):
            file_path = event.data.strip('{}')
            if file_path.lower().endswith(('.xlsx', '.xls', '.csv')):
                load_file_to_slot(slot_number, file_path)
            else:
                messagebox.showerror("Invalid File", "Please select an Excel (.xlsx, .xls) or CSV (.csv) file")
        
        def on_drag_enter(event):
            drop_frame.configure(bg="#00d4aa", relief="solid")
            drop_content.configure(bg="#00d4aa")
            file_icon.configure(text="📥", fg="#ffffff", bg="#00d4aa")
            drop_text.configure(text="Drop your file here!", bg="#00d4aa", fg="#ffffff")
        
        def on_drag_leave(event):
            if slot_number not in uploaded_files:
                drop_frame.configure(bg="#2c3440", relief="ridge")
                drop_content.configure(bg="#2c3440")
                file_icon.configure(text="📁", fg="#8a92a3", bg="#2c3440")
                drop_text.configure(text="Drag & Drop file here\nor click Browse", bg="#2c3440", fg="#8a92a3")
        
        # Register drag & drop
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', on_drop)
        drop_frame.dnd_bind('<<DragEnter>>', on_drag_enter)
        drop_frame.dnd_bind('<<DragLeave>>', on_drag_leave)
    
    def load_file_to_slot(slot_number, file_path):
        try:
            # Load the file
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = handle_excel(file_path, None, None, return_data=True)
            
            if df is not None:
                # Store file data
                uploaded_files[slot_number] = {
                    'path': file_path,
                    'data': df,
                    'filename': os.path.basename(file_path)
                }
                
                # Update slot appearance
                slot_data = file_slots[slot_number - 1]
                slot_data['status_label'].configure(text="✅ Loaded", fg="#00d4aa")
                slot_data['drop_frame'].configure(bg="#1a4d3a", relief="solid")
                slot_data['drop_content'].configure(bg="#1a4d3a")
                slot_data['file_icon'].configure(text="📊", fg="#00d4aa", bg="#1a4d3a")
                slot_data['drop_text'].configure(
                    text=f"{os.path.basename(file_path)}\n{len(df)} rows × {len(df.columns)} columns",
                    bg="#1a4d3a",
                    fg="#ffffff"
                )
                slot_data['clear_btn'].configure(state="normal")
                
                # Show file info - compact format
                file_size = os.path.getsize(file_path)
                size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
                slot_data['info_label'].configure(text=f"📄 {size_str} • {datetime.now().strftime('%H:%M')}")
                slot_data['info_label'].pack(fill="x", padx=10, pady=(0, 8))
                
                global current_file_count
                if slot_number not in [k for k in uploaded_files.keys() if k != slot_number]:
                    current_file_count += 1
                
                update_compare_button_state()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file: {str(e)}")
    
    def update_file_slots():
        global target_file_count
        try:
            new_count = int(file_count_var.get())
            if 2 <= new_count <= 10:
                target_file_count = new_count
                create_file_slots()
                update_compare_button_state()
            else:
                messagebox.showwarning("Invalid Count", "Please select between 2-10 files")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number")
    
    # Update button
    update_btn = tk.Button(
        control_inner,
        text="📝 Update Slots",
        command=update_file_slots,
        font=("Segoe UI", 10, "bold"),
        fg="#ffffff",
        bg="#00d4aa",
        activebackground="#00b894",
        relief="flat",
        padx=15,
        pady=5,
        cursor="hand2"
    )
    update_btn.pack(side="left")
    
    # Action buttons frame
    action_frame = tk.Frame(main_container, bg="#0f1419")
    action_frame.pack(fill="x", pady=(20, 0))
    
    # Compare button
    def compare_files():
        if len(uploaded_files) < 2:
            messagebox.showwarning("Insufficient Files", "Please upload at least 2 files to compare")
            return
        
        # For now, just show a preview of loaded files
        file_info = []
        for slot_num, file_data in uploaded_files.items():
            df = file_data['data']
            file_info.append(f"File {slot_num}: {file_data['filename']}")
            file_info.append(f"  - Rows: {len(df)}, Columns: {len(df.columns)}")
            file_info.append(f"  - Columns: {', '.join(list(df.columns)[:5])}{'...' if len(df.columns) > 5 else ''}")
            file_info.append("")
        
        messagebox.showinfo("Files Ready for Comparison", "\\n".join(file_info))
    
    def update_compare_button_state():
        if len(uploaded_files) >= 2:
            compare_btn.configure(state="normal", bg="#00d4aa")
        else:
            compare_btn.configure(state="disabled", bg="#5a6270")
    
    compare_btn = tk.Button(
        action_frame,
        text="🔍 Compare Files",
        command=compare_files,
        font=("Segoe UI", 12, "bold"),
        fg="#ffffff",
        bg="#5a6270",
        activebackground="#00b894",
        relief="flat",
        padx=30,
        pady=12,
        cursor="hand2",
        state="disabled"
    )
    compare_btn.pack(side="right")
    
    # Clear all button
    def clear_all_files():
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all files?"):
            uploaded_files.clear()
            global current_file_count
            current_file_count = 0
            create_file_slots()
            update_compare_button_state()
    
    clear_all_btn = tk.Button(
        action_frame,
        text="🗑️ Clear All",
        command=clear_all_files,
        font=("Segoe UI", 11, "bold"),
        fg="#ffffff",
        bg="#ff6b6b",
        activebackground="#ff5252",
        relief="flat",
        padx=20,
        pady=10,
        cursor="hand2"
    )
    clear_all_btn.pack(side="right", padx=(0, 15))
    
    # Status bar
    status_frame = tk.Frame(main_container, bg="#0f1419")
    status_frame.pack(fill="x", pady=(15, 0))
    
    status_label = tk.Label(
        status_frame,
        text="📊 Ready to upload files for comparison...",
        font=("Segoe UI", 10),
        fg="#8a92a3",
        bg="#0f1419"
    )
    status_label.pack(side="left")
    
    # Responsive grid layout on window resize
    def on_window_resize(event):
        if event.widget == root:
            # Recalculate and update grid layout when window is resized
            old_columns = grid_columns
            calculate_grid_layout()
            
            # Only recreate slots if grid layout changed
            if old_columns != grid_columns and file_slots:
                # Save current uploaded files
                temp_files = uploaded_files.copy()
                create_file_slots()
                # Restore uploaded files
                for slot_num, file_data in temp_files.items():
                    if slot_num <= len(file_slots):
                        uploaded_files[slot_num] = file_data
                        # Update slot appearance
                        slot_data = file_slots[slot_num - 1]
                        slot_data['status_label'].configure(text="✅ Loaded", fg="#00d4aa")
                        slot_data['drop_frame'].configure(bg="#1a4d3a", relief="solid")
                        slot_data['drop_content'].configure(bg="#1a4d3a")
                        slot_data['file_icon'].configure(text="📊", fg="#00d4aa", bg="#1a4d3a")
                        filename = os.path.basename(file_data['path'])
                        df = file_data['data']
                        slot_data['drop_text'].configure(
                            text=f"{filename}\n{len(df)} rows × {len(df.columns)} columns",
                            bg="#1a4d3a",
                            fg="#ffffff"
                        )
                        slot_data['clear_btn'].configure(state="normal")
                        
                        # Show file info
                        file_size = os.path.getsize(file_data['path'])
                        size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
                        slot_data['info_label'].configure(text=f"📄 {size_str} • {datetime.now().strftime('%H:%M')}")
                        slot_data['info_label'].pack(fill="x", padx=10, pady=(0, 8))
                
                update_compare_button_state()
    
    # Bind resize event
    root.bind('<Configure>', on_window_resize)
    
    # Initialize with default slots
    create_file_slots()
    
    # Center window
    def center_window():
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.after(100, center_window)


# For backward compatibility, also create the single file version
def build_ui(root):
    build_multi_file_ui(root)