import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
from uploader import handle_excel
import pandas as pd
import os
from datetime import datetime


def build_multi_file_ui(root):
    # Configure main window - optimized size
    root.title("🚀 Excel/CSV File Comparison Tool")
    root.geometry("1200x750")  # Larger default size for better scaling
    root.minsize(900, 650)
    root.configure(bg="#0f1419")
    root.resizable(True, True)
    
    # Force window update to get proper dimensions
    root.update_idletasks()
    
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
    
    # Create main scrollable container - fully responsive
    main_canvas = tk.Canvas(root, bg="#0f1419", highlightthickness=0)
    main_scrollbar = ttk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
    main_container = tk.Frame(main_canvas, bg="#0f1419")
    
    # Configure universal scrolling
    def on_container_configure(e):
        main_canvas.configure(scrollregion=main_canvas.bbox("all"))
        # Also center content when container changes
        root.after_idle(center_canvas_content)
    
    main_container.bind("<Configure>", on_container_configure)
    
    # Create window with dynamic centering
    canvas_window = main_canvas.create_window((0, 0), window=main_container, anchor="nw")
    main_canvas.configure(yscrollcommand=main_scrollbar.set)
    
    # Function for 100% width utilization
    def center_canvas_content():
        # For 100% utilization, always position at x=0 and expand container to full width
        canvas_width = main_canvas.winfo_width()
        main_container.update_idletasks()
        
        # Always use full canvas width - no centering needed
        x_pos = 0
        
        # Update window position and ensure container uses full width
        main_canvas.coords(canvas_window, x_pos, 0)
        main_canvas.itemconfig(canvas_window, width=canvas_width)
    
    # Add mouse wheel scrolling for entire window
    def on_main_mousewheel(event):
        main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    # Bind mouse wheel to entire window and canvas
    root.bind("<MouseWheel>", on_main_mousewheel)
    main_canvas.bind("<MouseWheel>", on_main_mousewheel)
    main_canvas.bind("<Button-4>", lambda e: main_canvas.yview_scroll(-1, "units"))
    main_canvas.bind("<Button-5>", lambda e: main_canvas.yview_scroll(1, "units"))
    
    # Bind canvas configure to center content
    main_canvas.bind("<Configure>", lambda e: root.after_idle(center_canvas_content))
    
    # Pack canvas and scrollbar
    main_canvas.pack(side="left", fill="both", expand=True)
    main_scrollbar.pack(side="right", fill="y")
    
    # Full window utilization - no padding
    main_content = tk.Frame(main_container, bg="#0f1419")
    main_content.pack(fill="both", expand=True, padx=0, pady=0)
    
    # Add comprehensive resize event handler for dynamic layout
    def on_window_resize(event=None):
        # Only respond to root window resize events
        if event and event.widget != root:
            return
            
        # Update scroll region for universal scrolling
        root.after_idle(lambda: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        
        # Center the content horizontally
        root.after_idle(center_canvas_content)
        
        # Always refresh grid layout on resize with delay to ensure window size is updated
        if len(file_slots) > 0:
            root.after(100, refresh_file_grid)  # Longer delay for better size detection
        else:
            # Even if no files, recalculate grid for future file slots
            root.after(100, calculate_grid_layout)
    
    root.bind("<Configure>", on_window_resize)
    
    # Header section - minimal padding for 100% utilization
    header_frame = tk.Frame(main_content, bg="#0f1419")
    header_frame.pack(fill="x", pady=(5, 10))
    

    
    title_label = tk.Label(
        header_frame,
        text="📊 Excel/CSV File Comparison Tool",
        font=("Segoe UI", 16, "bold"),
        fg="#00d4aa",
        bg="#0f1419"
    )
    title_label.pack(pady=(0, 2))
    
    subtitle_label = tk.Label(
        header_frame,
        text="Upload multiple Excel/CSV files for comparison and analysis",
        font=("Segoe UI", 10),
        fg="#8a92a3",
        bg="#0f1419"
    )
    subtitle_label.pack()
    
    # Control panel - full width but centered content
    control_frame = tk.Frame(main_content, bg="#1a1f29", relief="solid", bd=1)
    control_frame.pack(fill="x", pady=(0, 10))  # Fill width, minimal padding
    
    control_inner = tk.Frame(control_frame, bg="#1a1f29")
    control_inner.pack(anchor="center", padx=15, pady=10)  # Center the inner content, less padding
    
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
    
    # File slots container - full utilization
    files_frame = tk.Frame(main_content, bg="#0f1419")
    files_frame.pack(fill="both", expand=True, pady=(0, 5))
    
    # Direct container for file slots - full width utilization
    files_container = tk.Frame(files_frame, bg="#0f1419")
    files_container.pack(fill="both", expand=True, padx=5, pady=5)  # Minimal padding for maximum space
    
    # Configure the files_container to expand properly
    files_frame.grid_columnconfigure(0, weight=1)
    files_frame.grid_rowconfigure(0, weight=1)
    
    # Variables for grid layout
    global grid_columns
    grid_columns = 2  # Default to 2 columns
    
    # Functions for file management
    def refresh_file_grid():
        """Refresh the grid layout when window is resized"""
        if uploaded_files and len(uploaded_files) > 0:
            calculate_grid_layout()
            create_file_slots()
            # Restore uploaded files
            for i, file_data in enumerate(uploaded_files[:target_file_count]):
                if i < len(file_slots):
                    slot_num = i + 1
                    filename = file_data.get('filename', f'file_{slot_num}')
                    file_slots[i]['file_data'] = file_data
                    # Update UI to show uploaded state
                    file_slots[i]['status_label'].config(text="✅ Uploaded", fg="#00d4aa")
                    file_slots[i]['filename_label'].config(text=filename)
                    file_slots[i]['preview_button'].config(state="normal")
    
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
        
        # Update container and configure columns
        files_container.update_idletasks()
        
        # Configure active columns with proper centering
        for col in range(grid_columns):
            files_container.grid_columnconfigure(col, weight=1, pad=5)
        
        # Configure the container to center the grid
        files_container.grid_anchor("center")
    
    def calculate_grid_layout():
        """Calculate optimal grid layout based on actual window width"""
        global grid_columns
        
        # Get current window width with better detection
        try:
            root.update()  # Force window update first
            window_width = root.winfo_width()
            
            # If window is not properly initialized, try alternative methods
            if window_width <= 100:  # Very small means not initialized
                geometry = root.geometry()
                if 'x' in geometry:
                    window_width = int(geometry.split('x')[0])
                else:
                    window_width = 1100  # Default fallback
            
            
        except Exception as e:
            window_width = 1100
        
        # More aggressive responsive calculation based on actual width
        available_width = window_width - 100  # Account for padding and scrollbar
        min_card_width = 300  # Minimum width per card
        
        # Calculate maximum possible columns
        max_possible = max(1, available_width // min_card_width)
        
        # Responsive breakpoints based on actual window size
        if window_width < 500:
            grid_columns = 1
        elif window_width < 800:
            grid_columns = min(2, max_possible)
        elif window_width < 1100:
            grid_columns = min(3, max_possible)
        elif window_width < 1400:
            grid_columns = min(4, max_possible)
        else:
            grid_columns = min(5, max_possible)
        
        # Don't exceed file count
        grid_columns = min(grid_columns, target_file_count)
        grid_columns = max(1, grid_columns)
        

        
        # Don't exceed the number of files
        grid_columns = min(grid_columns, target_file_count)
        
        # Always have at least 1 column
        grid_columns = max(1, grid_columns)
    
    def create_file_slot(slot_number, row, col):
        slot_frame = tk.Frame(files_container, bg="#1a1f29", relief="solid", bd=2)
        # Minimal spacing for maximum space utilization
        slot_frame.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
        
        # Configure grid for better space usage
        files_container.grid_columnconfigure(col, weight=1, minsize=300)
        files_container.grid_rowconfigure(row, weight=0)
        
        # Larger card size for better space utilization
        slot_frame.configure(width=360, height=210)
        
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
        
        # Drop area - dynamic width, fixed height
        drop_frame = tk.Frame(
            slot_frame,
            bg="#2c3440",
            relief="solid",
            bd=1,
            height=115
        )
        drop_frame.pack(fill="x", padx=8, pady=(0, 10))
        drop_frame.pack_propagate(False)
        
        # Drop content
        drop_content = tk.Frame(drop_frame, bg="#2c3440")
        drop_content.pack(expand=True, fill="both")
        
        file_icon = tk.Label(
            drop_content,
            text="📁",
            font=("Segoe UI", 24),
            fg="#8a92a3",
            bg="#2c3440"
        )
        file_icon.pack(pady=(12, 6))
        
        drop_text = tk.Label(
            drop_content,
            text="Drag & Drop file here\nor click Browse",
            font=("Segoe UI", 11),
            fg="#8a92a3",
            bg="#2c3440",
            justify="center"
        )
        drop_text.pack()
        
        # Buttons frame - dynamic width
        buttons_frame = tk.Frame(slot_frame, bg="#1a1f29")
        buttons_frame.pack(fill="x", padx=8, pady=(0, 10))
        
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
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg="#00d4aa",
            activebackground="#00b894",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2"
        )
        browse_btn.pack(side="left", padx=(0, 10))
        
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
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg="#ff6b6b",
            activebackground="#ff5252",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            state="disabled"
        )
        clear_btn.pack(side="left")
        
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
    
    # Action buttons frame - full width with centered buttons
    action_frame = tk.Frame(main_content, bg="#0f1419")
    action_frame.pack(fill="x", pady=(5, 5))  # Fill width, minimal padding
    
    # Create inner frame for centering buttons
    action_inner = tk.Frame(action_frame, bg="#0f1419")
    action_inner.pack(anchor="center")
    
    # Results container (initially hidden) - responsive frame
    global results_container
    results_outer_frame = tk.Frame(main_content, bg="#0f1419")
    results_container = tk.Frame(results_outer_frame, bg="#0f1419")
    
    # Pack the results container with responsive padding
    results_container.pack(fill="both", expand=True, padx=5, pady=5)
    
    # Store reference to outer frame for show/hide
    global results_outer_container
    results_outer_container = results_outer_frame
    
    # Compare button
    def compare_files():
        if len(uploaded_files) < 2:
            messagebox.showwarning("Insufficient Files", "Please upload at least 2 files to compare")
            return
        
        # Show the comparison results
        show_comparison_results()
    
    def show_comparison_results():
        """Display detailed comparison results in tabular form"""
        # Clear previous results
        for widget in results_container.winfo_children():
            widget.destroy()
        
        # Show results container with scrolling
        results_outer_container.pack(fill="both", expand=True, pady=(20, 0))
        
        # Results header
        results_header = tk.Frame(results_container, bg="#1a1f29", relief="solid", bd=1)
        results_header.pack(fill="x", padx=5, pady=(0, 10))
        
        header_label = tk.Label(
            results_header,
            text="📊 Comparison Results",
            font=("Segoe UI", 16, "bold"),
            fg="#00d4aa",
            bg="#1a1f29"
        )
        header_label.pack(pady=15)
        
        # Create notebook for different comparison views
        notebook = ttk.Notebook(results_container)
        notebook.pack(fill="both", expand=True, padx=5)
        
        # Style the notebook
        style.configure('TNotebook', background='#0f1419', borderwidth=0)
        style.configure('TNotebook.Tab', background='#2c3440', foreground='#ffffff', 
                       padding=[12, 8], focuscolor='none')
        style.map('TNotebook.Tab', background=[('selected', '#00d4aa')], 
                  foreground=[('selected', '#000000')])
        
        # Tab 1: File Overview
        create_overview_tab(notebook)
        
        # Tab 2: Column Comparison
        create_column_comparison_tab(notebook)
        
        # Tab 3: Data Differences (if files have same structure)
        create_data_differences_tab(notebook)
        
        # Tab 4: Statistics
        create_statistics_tab(notebook)
    
    def create_overview_tab(notebook):
        """Create overview tab showing basic file information"""
        overview_frame = tk.Frame(notebook, bg="#0f1419")
        notebook.add(overview_frame, text="📋 File Overview")
        
        # Create scrollable frame
        canvas_overview = tk.Canvas(overview_frame, bg="#0f1419", highlightthickness=0)
        scrollbar_overview = ttk.Scrollbar(overview_frame, orient="vertical", command=canvas_overview.yview)
        scrollable_overview = tk.Frame(canvas_overview, bg="#0f1419")
        
        scrollable_overview.bind(
            "<Configure>",
            lambda e: canvas_overview.configure(scrollregion=canvas_overview.bbox("all"))
        )
        
        canvas_overview.create_window((0, 0), window=scrollable_overview, anchor="nw")
        canvas_overview.configure(yscrollcommand=scrollbar_overview.set)
        
        # Add mouse wheel scrolling for overview tab
        def on_overview_scroll(event):
            canvas_overview.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas_overview.bind("<MouseWheel>", on_overview_scroll)
        
        canvas_overview.pack(side="left", fill="both", expand=True)
        scrollbar_overview.pack(side="right", fill="y")
        
        # File information display - simplified
        for slot_num, file_data in uploaded_files.items():
            df = file_data['data']
            file_size = os.path.getsize(file_data['path'])
            size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
            file_type = "CSV" if file_data['path'].lower().endswith('.csv') else "Excel"
            
            # File info frame
            file_info_frame = tk.Frame(scrollable_overview, bg="#1a1f29", relief="solid", bd=1)
            file_info_frame.pack(fill="x", padx=10, pady=5)
            
            # File header
            file_header = tk.Label(
                file_info_frame,
                text=f"📊 File {slot_num}: {file_data['filename']}",
                font=("Segoe UI", 12, "bold"),
                fg="#00d4aa",
                bg="#1a1f29"
            )
            file_header.pack(pady=10)
            
            # File details
            details_text = f"""
📋 Rows: {len(df):,}
📊 Columns: {len(df.columns):,}
💾 Size: {size_str}
📄 Type: {file_type}
🕒 Loaded: {datetime.now().strftime('%H:%M:%S')}
            """
            
            details_label = tk.Label(
                file_info_frame,
                text=details_text.strip(),
                font=("Segoe UI", 10),
                fg="#ffffff",
                bg="#1a1f29",
                justify="left"
            )
            details_label.pack(pady=5, padx=15)
        

    
    def create_column_comparison_tab(notebook):
        """Create column comparison tab"""
        column_frame = tk.Frame(notebook, bg="#0f1419")
        notebook.add(column_frame, text="📊 Column Analysis")
        
        # Create scrollable frame
        canvas_col = tk.Canvas(column_frame, bg="#0f1419", highlightthickness=0)
        scrollbar_col = ttk.Scrollbar(column_frame, orient="vertical", command=canvas_col.yview)
        scrollable_col = tk.Frame(canvas_col, bg="#0f1419")
        
        scrollable_col.bind(
            "<Configure>",
            lambda e: canvas_col.configure(scrollregion=canvas_col.bbox("all"))
        )
        
        canvas_col.create_window((0, 0), window=scrollable_col, anchor="nw")
        canvas_col.configure(yscrollcommand=scrollbar_col.set)
        
        # Add mouse wheel scrolling for column tab
        def on_col_scroll(event):
            canvas_col.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas_col.bind("<MouseWheel>", on_col_scroll)
        
        canvas_col.pack(side="left", fill="both", expand=True)
        scrollbar_col.pack(side="right", fill="y")
        
        # Get all unique columns across files
        all_columns = set()
        file_columns = {}
        
        for slot_num, file_data in uploaded_files.items():
            df = file_data['data']
            cols = list(df.columns)
            file_columns[slot_num] = cols
            all_columns.update(cols)
        
        # Column comparison - simplified display
        col_info_frame = tk.Frame(scrollable_col, bg="#1a1f29", relief="solid", bd=1)
        col_info_frame.pack(fill="x", padx=10, pady=10)
        
        col_info_header = tk.Label(
            col_info_frame,
            text="📊 Column Analysis",
            font=("Segoe UI", 12, "bold"),
            fg="#00d4aa",
            bg="#1a1f29"
        )
        col_info_header.pack(pady=10)
        
        # Show column information for each file
        for slot_num, file_data in uploaded_files.items():
            df = file_data['data']
            
            file_col_frame = tk.Frame(col_info_frame, bg="#252a35", relief="solid", bd=1)
            file_col_frame.pack(fill="x", padx=5, pady=5)
            
            file_col_header = tk.Label(
                file_col_frame,
                text=f"📋 File {slot_num}: {file_data['filename']}",
                font=("Segoe UI", 11, "bold"),
                fg="#00d4aa",
                bg="#252a35"
            )
            file_col_header.pack(pady=5)
            
            # Column list
            columns_text = "Columns: " + ", ".join(df.columns[:10])
            if len(df.columns) > 10:
                columns_text += f" ... and {len(df.columns) - 10} more"
                
            columns_label = tk.Label(
                file_col_frame,
                text=columns_text,
                font=("Segoe UI", 9),
                fg="#ffffff",
                bg="#252a35",
                wraplength=600,
                justify="left"
            )
            columns_label.pack(pady=5, padx=10)
            
        # Show common and unique columns
        if len(uploaded_files) >= 2:
            files_list = list(uploaded_files.values())
            all_cols = [set(f['data'].columns) for f in files_list]
            
            common_cols = set.intersection(*all_cols)
            
            common_frame = tk.Frame(col_info_frame, bg="#1a4d3a", relief="solid", bd=1)
            common_frame.pack(fill="x", padx=5, pady=5)
            
            common_header = tk.Label(
                common_frame,
                text=f"🔗 Common Columns ({len(common_cols)})",
                font=("Segoe UI", 11, "bold"),
                fg="#00d4aa",
                bg="#1a4d3a"
            )
            common_header.pack(pady=5)
            
            if common_cols:
                common_text = ", ".join(sorted(common_cols))
                common_label = tk.Label(
                    common_frame,
                    text=common_text,
                    font=("Segoe UI", 9),
                    fg="#ffffff",
                    bg="#1a4d3a",
                    wraplength=600,
                    justify="left"
                )
                common_label.pack(pady=5, padx=10)
        

    
    def create_data_differences_tab(notebook):
        """Create data differences tab for files with similar structure"""
        diff_frame = tk.Frame(notebook, bg="#0f1419")
        notebook.add(diff_frame, text="🔍 Data Differences")
        
        # Check if files can be compared (similar columns)
        if len(uploaded_files) != 2:
            info_label = tk.Label(
                diff_frame,
                text="📝 Data difference comparison is available for exactly 2 files only.",
                font=("Segoe UI", 12),
                fg="#8a92a3",
                bg="#0f1419"
            )
            info_label.pack(expand=True)
            return
        
        file_list = list(uploaded_files.values())
        df1, df2 = file_list[0]['data'], file_list[1]['data']
        
        # Check if files have similar structure
        common_columns = set(df1.columns) & set(df2.columns)
        
        if len(common_columns) == 0:
            info_label = tk.Label(
                diff_frame,
                text="📝 No common columns found between files.\nData comparison requires files with similar structure.",
                font=("Segoe UI", 12),
                fg="#8a92a3",
                bg="#0f1419",
                justify="center"
            )
            info_label.pack(expand=True)
            return
        
        # Create scrollable frame for differences
        canvas_diff = tk.Canvas(diff_frame, bg="#0f1419", highlightthickness=0)
        scrollbar_diff = ttk.Scrollbar(diff_frame, orient="vertical", command=canvas_diff.yview)
        scrollable_diff = tk.Frame(canvas_diff, bg="#0f1419")
        
        scrollable_diff.bind(
            "<Configure>",
            lambda e: canvas_diff.configure(scrollregion=canvas_diff.bbox("all"))
        )
        
        canvas_diff.create_window((0, 0), window=scrollable_diff, anchor="nw")
        canvas_diff.configure(yscrollcommand=scrollbar_diff.set)
        
        # Add mouse wheel scrolling for diff tab
        def on_diff_scroll(event):
            canvas_diff.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas_diff.bind("<MouseWheel>", on_diff_scroll)
        
        canvas_diff.pack(side="left", fill="both", expand=True)
        scrollbar_diff.pack(side="right", fill="y")
        
        # Summary of differences
        summary_frame = tk.Frame(scrollable_diff, bg="#1a1f29", relief="solid", bd=1)
        summary_frame.pack(fill="x", padx=10, pady=10)
        
        summary_label = tk.Label(
            summary_frame,
            text="📋 Comparison Summary",
            font=("Segoe UI", 12, "bold"),
            fg="#00d4aa",
            bg="#1a1f29"
        )
        summary_label.pack(pady=10)
        
        # Calculate differences
        file1_name = file_list[0]['filename']
        file2_name = file_list[1]['filename']
        
        summary_text = f"""
📊 File 1: {file1_name} ({len(df1)} rows, {len(df1.columns)} columns)
📊 File 2: {file2_name} ({len(df2)} rows, {len(df2.columns)} columns)
🔗 Common Columns: {len(common_columns)}
📈 Unique to File 1: {len(set(df1.columns) - set(df2.columns))}
📉 Unique to File 2: {len(set(df2.columns) - set(df1.columns))}
        """
        
        summary_text_label = tk.Label(
            summary_frame,
            text=summary_text.strip(),
            font=("Segoe UI", 10),
            fg="#ffffff",
            bg="#1a1f29",
            justify="left"
        )
        summary_text_label.pack(pady=5)
    
    def create_statistics_tab(notebook):
        """Create statistics tab"""
        stats_frame = tk.Frame(notebook, bg="#0f1419")
        notebook.add(stats_frame, text="📈 Statistics")
        
        # Create scrollable frame
        canvas_stats = tk.Canvas(stats_frame, bg="#0f1419", highlightthickness=0)
        scrollbar_stats = ttk.Scrollbar(stats_frame, orient="vertical", command=canvas_stats.yview)
        scrollable_stats = tk.Frame(canvas_stats, bg="#0f1419")
        
        scrollable_stats.bind(
            "<Configure>",
            lambda e: canvas_stats.configure(scrollregion=canvas_stats.bbox("all"))
        )
        
        canvas_stats.create_window((0, 0), window=scrollable_stats, anchor="nw")
        canvas_stats.configure(yscrollcommand=scrollbar_stats.set)
        
        # Add mouse wheel scrolling for stats tab
        def on_stats_scroll(event):
            canvas_stats.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas_stats.bind("<MouseWheel>", on_stats_scroll)
        
        canvas_stats.pack(side="left", fill="both", expand=True)
        scrollbar_stats.pack(side="right", fill="y")
        
        # Statistics for each file
        for slot_num, file_data in uploaded_files.items():
            df = file_data['data']
            
            # File statistics frame
            file_stats_frame = tk.Frame(scrollable_stats, bg="#1a1f29", relief="solid", bd=1)
            file_stats_frame.pack(fill="x", padx=10, pady=5)
            
            # File header
            file_header = tk.Label(
                file_stats_frame,
                text=f"📊 File {slot_num}: {file_data['filename']}",
                font=("Segoe UI", 12, "bold"),
                fg="#00d4aa",
                bg="#1a1f29"
            )
            file_header.pack(pady=10)
            
            # Basic statistics
            stats_text = f"""
📋 Total Rows: {len(df)}
📊 Total Columns: {len(df.columns)}
🔢 Numeric Columns: {len(df.select_dtypes(include=['number']).columns)}
📝 Text Columns: {len(df.select_dtypes(include=['object']).columns)}
📅 Date Columns: {len(df.select_dtypes(include=['datetime']).columns)}
💾 Memory Usage: {df.memory_usage(deep=True).sum() / 1024:.1f} KB
            """
            
            stats_label = tk.Label(
                file_stats_frame,
                text=stats_text.strip(),
                font=("Segoe UI", 10),
                fg="#ffffff",
                bg="#1a1f29",
                justify="left"
            )
            stats_label.pack(pady=5, padx=15)
    
    def update_compare_button_state():
        if len(uploaded_files) >= 2:
            compare_btn.configure(state="normal", bg="#00d4aa")
            hide_results_btn.configure(state="normal", bg="#ff6b6b")
        else:
            compare_btn.configure(state="disabled", bg="#5a6270")
            hide_results_btn.configure(state="disabled", bg="#5a6270")
            # Hide results if less than 2 files
            results_outer_container.pack_forget()
    
    def hide_comparison_results():
        """Hide the comparison results"""
        results_outer_container.pack_forget()
    
    compare_btn = tk.Button(
        action_inner,
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
    
    # Hide results button
    global hide_results_btn
    hide_results_btn = tk.Button(
        action_inner,
        text="👁️ Hide Results",
        command=hide_comparison_results,
        font=("Segoe UI", 12, "bold"),
        fg="#ffffff",
        bg="#5a6270",
        activebackground="#ff5252",
        relief="flat",
        padx=30,
        pady=12,
        cursor="hand2",
        state="disabled"
    )
    hide_results_btn.pack(side="right", padx=(15, 15))
    
    # Clear all button
    def clear_all_files():
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all files?"):
            uploaded_files.clear()
            global current_file_count
            current_file_count = 0
            create_file_slots()
            hide_comparison_results()  # Hide results when clearing all
            update_compare_button_state()
    
    clear_all_btn = tk.Button(
        action_inner,
        text="🗑️ Clear All",
        command=clear_all_files,
        font=("Segoe UI", 12, "bold"),
        fg="#ffffff",
        bg="#ff6b6b",
        activebackground="#ff5252",
        relief="flat",
        padx=30,
        pady=12,
        cursor="hand2"
    )
    clear_all_btn.pack(side="right", padx=(15, 0))
    
    # Status bar
    status_frame = tk.Frame(main_content, bg="#0f1419")
    status_frame.pack(fill="x", pady=(5, 0))
    
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