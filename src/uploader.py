import pandas as pd
from tkinter import messagebox, Toplevel, Text, Scrollbar
import tkinter as tk
import os
from datetime import datetime

def handle_excel(file_path: str, success_callback=None, error_callback=None, return_data=False):
    """Read and preview Excel file with modern UI feedback."""
    try:
        # Validate file exists and has correct extension
        if not os.path.exists(file_path):
            error_msg = "File not found"
            if error_callback:
                error_callback(error_msg)
            else:
                messagebox.showerror("Error", error_msg)
            return None
        
        if not file_path.lower().endswith(('.xlsx', '.xls')):
            error_msg = "Invalid file format. Please select an Excel file."
            if error_callback:
                error_callback(error_msg)
            else:
                messagebox.showerror("Error", error_msg)
            return None
        
        # Read the Excel file
        df = pd.read_excel(file_path)
        
        # If return_data is True, just return the data without showing preview
        if return_data:
            return df
        
        # Show modern preview window
        show_modern_preview(file_path, df)
        
        # Call success callback
        if success_callback:
            success_callback("File processed successfully")
        
        return df
        
    except FileNotFoundError:
        error_msg = "File not found"
        if error_callback:
            error_callback(error_msg)
        else:
            messagebox.showerror("Error", error_msg)
        return None
    except PermissionError:
        error_msg = "Permission denied. File may be open in another application."
        if error_callback:
            error_callback(error_msg)
        else:
            messagebox.showerror("Error", error_msg)
        return None
    except Exception as e:
        error_msg = f"Could not read file: {str(e)}"
        if error_callback:
            error_callback(error_msg)
        else:
            messagebox.showerror("Error", error_msg)
        return None

def show_modern_preview(file_path: str, df: pd.DataFrame):
    """Show a modern responsive preview window for the Excel file."""
    preview_window = Toplevel()
    preview_window.title("📊 Excel File Preview")
    preview_window.geometry("700x500")  # Smaller initial size
    preview_window.minsize(500, 400)    # Set minimum size
    preview_window.configure(bg="#0f1419")
    preview_window.resizable(True, True)
    
    # Make window modal
    preview_window.transient()
    preview_window.grab_set()
    
    # Header frame - responsive padding
    header_frame = tk.Frame(preview_window, bg="#0f1419")
    header_frame.pack(fill="x", padx=15, pady=(15, 10))
    
    # File info
    filename = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    file_size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
    
    title_label = tk.Label(
        header_frame,
        text=f"📄 {filename}",
        font=("Segoe UI", 14, "bold"),  # Responsive font size
        fg="#00d4aa",
        bg="#0f1419",
        wraplength=450  # Allow filename wrapping
    )
    title_label.pack(anchor="w")
    
    info_frame = tk.Frame(header_frame, bg="#0f1419")
    info_frame.pack(fill="x", pady=(5, 0))
    
    info_text = f"📊 {len(df)} rows × {len(df.columns)} columns  •  💾 {file_size_str}  •  📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    info_label = tk.Label(
        info_frame,
        text=info_text,
        font=("Segoe UI", 9),  # Smaller responsive font
        fg="#8a92a3",
        bg="#0f1419",
        wraplength=500  # Allow text wrapping
    )
    info_label.pack(anchor="w")
    
    # Main content frame - responsive padding
    content_frame = tk.Frame(preview_window, bg="#1a1f29", relief="solid", bd=1)
    content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
    
    # Preview text with scrollbar
    text_frame = tk.Frame(content_frame, bg="#1a1f29")
    text_frame.pack(fill="both", expand=True, padx=15, pady=15)
    
    # Create text widget with scrollbar
    text_widget = Text(
        text_frame,
        font=("Consolas", 10),
        bg="#1a1f29",
        fg="#ffffff",
        insertbackground="#00d4aa",
        selectbackground="#00d4aa",
        selectforeground="#000000",
        wrap="none",
        relief="flat",
        padx=10,
        pady=10
    )
    
    scrollbar_y = Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
    scrollbar_x = Scrollbar(text_frame, orient="horizontal", command=text_widget.xview)
    
    text_widget.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
    
    # Pack scrollbars and text widget
    scrollbar_y.pack(side="right", fill="y")
    scrollbar_x.pack(side="bottom", fill="x")
    text_widget.pack(side="left", fill="both", expand=True)
    
    # Format and insert data
    preview_text = f"Data Preview (showing first 10 rows):\n\n"
    preview_text += df.head(10).to_string(index=True, max_cols=None, max_colwidth=20)
    
    if len(df) > 10:
        preview_text += f"\n\n... and {len(df) - 10} more rows"
    
    # Add column info
    preview_text += f"\n\nColumn Names:\n"
    for i, col in enumerate(df.columns, 1):
        preview_text += f"{i:2d}. {col}\n"
    
    # Add data types info
    preview_text += f"\nData Types:\n"
    for col, dtype in df.dtypes.items():
        preview_text += f"{col}: {dtype}\n"
    
    text_widget.insert("1.0", preview_text)
    text_widget.configure(state="disabled")  # Make read-only
    
    # Button frame - responsive
    button_frame = tk.Frame(preview_window, bg="#0f1419")
    button_frame.pack(fill="x", padx=15, pady=(0, 15))
    
    close_btn = tk.Button(
        button_frame,
        text="✅ Close Preview",
        command=preview_window.destroy,
        font=("Segoe UI", 10, "bold"),  # Responsive font size
        fg="#ffffff",
        bg="#00d4aa",
        activebackground="#00b894",
        activeforeground="#ffffff",
        relief="flat",
        padx=18,  # Responsive padding
        pady=7,
        cursor="hand2"
    )
    close_btn.pack(side="right")
    
    # Center the window
    preview_window.update_idletasks()
    x = (preview_window.winfo_screenwidth() // 2) - (preview_window.winfo_width() // 2)
    y = (preview_window.winfo_screenheight() // 2) - (preview_window.winfo_height() // 2)
    preview_window.geometry(f"+{x}+{y}")
    
    # Focus on the window
    preview_window.focus_set()

def handle_multiple_files(file_paths: list, success_callback=None, error_callback=None):
    """Handle multiple Excel/CSV files for comparison."""
    loaded_files = {}
    errors = []
    
    for i, file_path in enumerate(file_paths):
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            loaded_files[i + 1] = {
                'path': file_path,
                'data': df,
                'filename': os.path.basename(file_path)
            }
            
        except Exception as e:
            errors.append(f"Error loading {os.path.basename(file_path)}: {str(e)}")
    
    if errors and error_callback:
        error_callback("\n".join(errors))
    
    if loaded_files and success_callback:
        success_callback(f"Successfully loaded {len(loaded_files)} files")
    
    return loaded_files, errors
