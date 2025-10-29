"""
File slot component for drag and drop file uploading
"""
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES
from datetime import datetime
from ui_styles.theme import UITheme
from file_handlers.file_manager import FileHandler

class FileSlot:
    """Individual file slot component"""
    
    FILE_CONFIGS = {
        1: {
            'name': '📋 File 1: Bank Ledger',
            'drop_text': 'Drop Bank Ledger file here\nor click Browse',
            'dialog_title': 'Select Bank Ledger File'
        },
        2: {
            'name': '📋 File 2: SIB QR Report',
            'drop_text': 'Drop SIB QR Report file here\nor click Browse', 
            'dialog_title': 'Select SIB QR Report File'
        },
        3: {
            'name': '📋 File 3: Demand Report',
            'drop_text': 'Drop Demand Report file here\nor click Browse',
            'dialog_title': 'Select Demand Report File'
        }
    }
    
    def __init__(self, parent, slot_number, row, col, on_file_loaded, on_file_cleared):
        self.parent = parent
        self.slot_number = slot_number
        self.on_file_loaded = on_file_loaded
        self.on_file_cleared = on_file_cleared
        
        self.file_data = None
        self.widgets = {}
        
        self._create_slot(row, col)
    
    def _create_slot(self, row, col):
        """Create the file slot UI"""
        # Main slot frame
        slot_frame = tk.Frame(self.parent, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=2)
        slot_frame.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
        slot_frame.configure(width=360, height=210)
        
        # Configure grid
        self.parent.grid_columnconfigure(col, weight=1, minsize=300)
        self.parent.grid_rowconfigure(row, weight=0)
        
        # Header frame
        header_frame = tk.Frame(slot_frame, bg=UITheme.BACKGROUND_MEDIUM)
        header_frame.pack(fill="x", padx=10, pady=(10, 8))
        
        # Slot label
        config = self.FILE_CONFIGS.get(self.slot_number, {})
        slot_label = tk.Label(
            header_frame,
            text=config.get('name', f"📋 File {self.slot_number}"),
            font=UITheme.get_font_config("subheader"),
            fg=UITheme.ACCENT_BLUE,
            bg=UITheme.BACKGROUND_MEDIUM
        )
        slot_label.pack(side="left")
        
        # Status label
        status_label = tk.Label(
            header_frame,
            text="⚪ Empty",
            font=UITheme.get_font_config("small"),
            fg=UITheme.TEXT_SECONDARY,
            bg=UITheme.BACKGROUND_MEDIUM
        )
        status_label.pack(side="right")
        
        # Drop area
        drop_frame = tk.Frame(slot_frame, bg=UITheme.BACKGROUND_LIGHT, relief="solid", bd=1, height=115)
        drop_frame.pack(fill="x", padx=8, pady=(0, 10))
        drop_frame.pack_propagate(False)
        
        drop_content = tk.Frame(drop_frame, bg=UITheme.BACKGROUND_LIGHT)
        drop_content.pack(expand=True, fill="both")
        
        # File icon
        file_icon = tk.Label(
            drop_content,
            text="📁",
            font=("Segoe UI", 24),
            fg=UITheme.TEXT_SECONDARY,
            bg=UITheme.BACKGROUND_LIGHT
        )
        file_icon.pack(pady=(12, 6))
        
        # Drop text
        drop_text = tk.Label(
            drop_content,
            text=config.get('drop_text', "Drag & Drop file here\nor click Browse"),
            font=UITheme.get_font_config("body"),
            fg=UITheme.TEXT_SECONDARY,
            bg=UITheme.BACKGROUND_LIGHT,
            justify="center"
        )
        drop_text.pack()
        
        # Buttons frame
        buttons_frame = tk.Frame(slot_frame, bg=UITheme.BACKGROUND_MEDIUM)
        buttons_frame.pack(fill="x", padx=8, pady=(0, 10))
        
        # Browse button
        browse_style = UITheme.get_button_style("primary")
        browse_btn = tk.Button(
            buttons_frame,
            text="🗂️ Browse",
            command=self._browse_file,
            font=UITheme.get_font_config("body"),
            **browse_style,
            padx=20,
            pady=8
        )
        browse_btn.pack(side="left", padx=(0, 5))
        
        # Download button - disabled until file is uploaded
        download_style = UITheme.get_button_style("secondary")
        template_btn = tk.Button(
            buttons_frame,
            text="📥 Download",
            command=self._download_template,
            font=UITheme.get_font_config("body"),
            **download_style,
            padx=15,
            pady=8,
            state="disabled"
        )
        template_btn.pack(side="left", padx=(0, 5))
        
        # Clear button
        clear_style = UITheme.get_button_style("danger")
        clear_btn = tk.Button(
            buttons_frame,
            text="🗑️ Clear",
            command=self._clear_file,
            font=UITheme.get_font_config("body"),
            **clear_style,
            padx=20,
            pady=8,
            state="disabled"
        )
        clear_btn.pack(side="left")
        
        # File info label
        info_label = tk.Label(
            slot_frame,
            text="",
            font=UITheme.get_font_config("small"),
            fg=UITheme.TEXT_SECONDARY,
            bg=UITheme.BACKGROUND_MEDIUM,
            wraplength=400
        )
        
        # Store widget references
        self.widgets = {
            'frame': slot_frame,
            'status_label': status_label,
            'drop_frame': drop_frame,
            'drop_content': drop_content,
            'file_icon': file_icon,
            'drop_text': drop_text,
            'browse_btn': browse_btn,
            'template_btn': template_btn,
            'clear_btn': clear_btn,
            'info_label': info_label
        }
        
        # Setup drag and drop
        self._setup_drag_drop()
    
    def _setup_drag_drop(self):
        """Setup drag and drop functionality"""
        drop_frame = self.widgets['drop_frame']
        
        def on_drop(event):
            file_path = event.data.strip('{}')
            is_valid, message = FileHandler.validate_file(file_path)
            
            if is_valid:
                self._load_file(file_path)
            else:
                messagebox.showerror("File Error", message)
        
        def on_drag_enter(event):
            self._set_drag_state(True)
        
        def on_drag_leave(event):
            if not self.file_data:
                self._set_drag_state(False)
        
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', on_drop)
        drop_frame.dnd_bind('<<DragEnter>>', on_drag_enter)
        drop_frame.dnd_bind('<<DragLeave>>', on_drag_leave)
    
    def _set_drag_state(self, is_dragging):
        """Set visual state for drag operations"""
        if is_dragging:
            self.widgets['drop_frame'].configure(bg=UITheme.ACCENT_BLUE_LIGHT, relief="solid")
            self.widgets['drop_content'].configure(bg=UITheme.ACCENT_BLUE_LIGHT)
            self.widgets['file_icon'].configure(text="📥", fg=UITheme.TEXT_PRIMARY, bg=UITheme.ACCENT_BLUE_LIGHT)
            self.widgets['drop_text'].configure(text="Drop your file here!", bg=UITheme.ACCENT_BLUE_LIGHT, fg=UITheme.TEXT_PRIMARY)
        else:
            self.widgets['drop_frame'].configure(bg=UITheme.BACKGROUND_LIGHT, relief="ridge")
            self.widgets['drop_content'].configure(bg=UITheme.BACKGROUND_LIGHT)
            self.widgets['file_icon'].configure(text="📁", fg=UITheme.TEXT_SECONDARY, bg=UITheme.BACKGROUND_LIGHT)
            config = self.FILE_CONFIGS.get(self.slot_number, {})
            original_text = config.get('drop_text', "Drag & Drop file here\nor click Browse")
            self.widgets['drop_text'].configure(text=original_text, bg=UITheme.BACKGROUND_LIGHT, fg=UITheme.TEXT_SECONDARY)
    
    def _browse_file(self):
        """Open file browser dialog"""
        config = self.FILE_CONFIGS.get(self.slot_number, {})
        title = config.get('dialog_title', f"Select File for Slot {self.slot_number}")
        
        file_path = filedialog.askopenfilename(
            title=title,
            **FileHandler.get_file_dialog_config()
        )
        
        if file_path:
            is_valid, message = FileHandler.validate_file(file_path)
            if is_valid:
                self._load_file(file_path)
            else:
                messagebox.showerror("File Error", message)
    
    def _load_file(self, file_path):
        """Load file and update UI"""
        df, error = FileHandler.load_file(file_path)
        
        if error:
            messagebox.showerror("Load Error", error)
            return
        
        # Store file data
        self.file_data = {
            'path': file_path,
            'data': df,
            **FileHandler.get_file_info(file_path, df)
        }
        
        # Update UI to show loaded state
        self._update_loaded_state()
        
        # Notify parent
        self.on_file_loaded(self.slot_number, self.file_data)
    
    def _update_loaded_state(self):
        """Update UI to show file is loaded"""
        if not self.file_data:
            return
        
        self.widgets['status_label'].configure(text="✅ Loaded", fg=UITheme.ACCENT_BLUE)
        self.widgets['drop_frame'].configure(bg=UITheme.SUCCESS_GREEN, relief="solid")
        self.widgets['drop_content'].configure(bg=UITheme.SUCCESS_GREEN)
        self.widgets['file_icon'].configure(text="📊", fg=UITheme.ACCENT_BLUE, bg=UITheme.SUCCESS_GREEN)
        
        display_text = f"{self.file_data['filename']}\n{self.file_data['rows']} rows × {self.file_data['columns']} columns"
        self.widgets['drop_text'].configure(
            text=display_text,
            bg=UITheme.SUCCESS_GREEN,
            fg=UITheme.TEXT_PRIMARY
        )
        
        # Update button states
        self.widgets['clear_btn'].configure(state="normal")
        self.widgets['template_btn'].configure(state="normal")  # Enable download button when file is loaded
        
        # Show file info
        info_text = f"📄 {self.file_data['size']} • {datetime.now().strftime('%H:%M')}"
        self.widgets['info_label'].configure(text=info_text)
        self.widgets['info_label'].pack(fill="x", padx=10, pady=(0, 8))
    
    def _download_template(self):
        """Download a template file based on the currently loaded file or provide a sample"""
        import pandas as pd
        import os
        
        # Ask user where to save the template
        config = self.FILE_CONFIGS.get(self.slot_number, {})
        file_name = config.get('name', f"File {self.slot_number}").replace('📋 ', '').replace(':', '')
        default_filename = f"{file_name.replace(' ', '_')}_Template.xlsx"
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            initialfile=default_filename,
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title=f"Save {file_name} Template"
        )
        
        if not file_path:
            return
        
        try:
            # Download the entire uploaded file for verification
            if self.file_data and self.file_data.get('data') is not None:
                # Export the entire uploaded file
                df = self.file_data['data']
                
                # Save the complete file
                df.to_excel(file_path, index=False, engine='openpyxl')
                
                messagebox.showinfo(
                    "File Downloaded",
                    f"✅ Complete file downloaded successfully!\n\n"
                    f"📁 Location: {file_path}\n\n"
                    f"📊 Total Rows: {len(df):,}\n"
                    f"📋 Total Columns: {len(df.columns)}\n\n"
                    f"💡 Use this to verify you uploaded the correct file format.\n"
                    f"Check column names and data structure match your requirements."
                )
            else:
                # This shouldn't happen as button is disabled, but safety check
                messagebox.showwarning(
                    "No File Uploaded",
                    "Please upload a file first before downloading.\n\n"
                    "The download button will be enabled after you upload a file."
                )
        
        except Exception as e:
            messagebox.showerror(
                "Template Error",
                f"Failed to create template:\n{str(e)}"
            )
    
    def _clear_file(self):
        """Clear the loaded file"""
        self.file_data = None
        
        # Reset UI to empty state
        self.widgets['status_label'].configure(text="⚪ Empty", fg=UITheme.TEXT_SECONDARY)
        self._set_drag_state(False)
        self.widgets['clear_btn'].configure(state="disabled")
        self.widgets['template_btn'].configure(state="disabled")  # Disable download button when file is cleared
        self.widgets['info_label'].pack_forget()
        
        # Notify parent
        self.on_file_cleared(self.slot_number)
    
    def get_data(self):
        """Get the loaded file data"""
        return self.file_data