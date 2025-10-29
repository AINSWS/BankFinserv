"""
Modular Bank Reconciliation UI - Main Interface
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinterdnd2 import TkinterDnD
from ui_styles.theme import UITheme
from components.file_slot import FileSlot
import sys
import os
import pandas as pd
import logging

# Import openpyxl for Excel formatting
try:
    from openpyxl import load_workbook
    from openpyxl.styles import PatternFill, Font
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("⚠️ Warning: openpyxl not available - Excel formatting will be limited")

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__)))
sys.path.append(os.path.join(os.path.dirname(__file__), 'reconciliation'))

from reconciliation.modular_engine import ModularReconciliationEngine

class BankReconciliationUI:
    """Main UI class for bank reconciliation application"""
    
    def __init__(self, root):
        self.root = root
        self.uploaded_files = {}
        self.file_slots = []
        self.target_file_count = 3
        
        # UI components
        self.main_canvas = None
        self.main_container = None
        self.files_container = None
        self.results_container = None
        self.results_outer_container = None
        self.compare_btn = None
        self.export_btn = None
        self.current_results = None
        self.current_recon_engine = None
        
        self._setup_window()
        self._setup_ui()
    
    def _setup_window(self):
        """Configure main window"""
        self.root.title("🏦 Unnatti Finserv Reconciliation Tool")
        self.root.geometry("1280x720")  # 720p compatible size
        self.root.minsize(1024, 600)    # Support lower resolutions
        self.root.configure(bg=UITheme.BACKGROUND_DARK)
        self.root.resizable(True, True)
        
        # Window positioning
        self.root.update_idletasks()
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(lambda: self.root.attributes('-topmost', False))
        
        # Configure TTK styles
        style = ttk.Style()
        UITheme.configure_ttk_styles(style)
    
    def _setup_ui(self):
        """Setup the main UI components"""
        self._create_scrollable_container()
        self._create_header()
        self._create_file_slots_container()
        self._create_action_buttons()
        self._create_results_container()
        self._create_status_bar()
        
        # Initialize file slots
        self._create_file_slots()
        
        # Bind resize events
        self.root.bind("<Configure>", self._on_window_resize)
        
        # Center window
        self.root.after(100, self._center_window)
    
    def _create_scrollable_container(self):
        """Create main scrollable container"""
        self.main_canvas = tk.Canvas(self.root, bg=UITheme.BACKGROUND_DARK, highlightthickness=0)
        main_scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.main_canvas.yview)
        self.main_container = tk.Frame(self.main_canvas, bg=UITheme.BACKGROUND_DARK)
        
        # Configure scrolling
        def on_container_configure(e):
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
            self.root.after_idle(self._center_canvas_content)
        
        self.main_container.bind("<Configure>", on_container_configure)
        
        # Create canvas window
        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.main_container, anchor="nw")
        self.main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Mouse wheel scrolling
        def on_mousewheel(event):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.root.bind("<MouseWheel>", on_mousewheel)
        self.main_canvas.bind("<MouseWheel>", on_mousewheel)
        self.main_canvas.bind("<Configure>", lambda e: self.root.after_idle(self._center_canvas_content))
        
        # Pack canvas and scrollbar
        self.main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        # Main content frame
        self.main_content = tk.Frame(self.main_container, bg=UITheme.BACKGROUND_DARK)
        self.main_content.pack(fill="both", expand=True, padx=0, pady=0)
    
    def _center_canvas_content(self):
        """Center canvas content for full width utilization"""
        canvas_width = self.main_canvas.winfo_width()
        self.main_container.update_idletasks()
        
        # Always use full canvas width
        self.main_canvas.coords(self.canvas_window, 0, 0)
        self.main_canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _create_header(self):
        """Create application header"""
        header_frame = tk.Frame(self.main_content, bg=UITheme.BACKGROUND_DARK)
        header_frame.pack(fill="x", pady=(5, 10))
        
        title_label = tk.Label(
            header_frame,
            text="🏦 Unnatti Finserv Reconciliation Tool",
            font=UITheme.get_font_config("title"),
            fg=UITheme.ACCENT_BLUE,
            bg=UITheme.BACKGROUND_DARK
        )
        title_label.pack(pady=(0, 2))
        
        subtitle_label = tk.Label(
            header_frame,
            text="Upload 3 files for comprehensive bank reconciliation analysis",
            font=UITheme.get_font_config("subtitle"),
            fg=UITheme.TEXT_SECONDARY,
            bg=UITheme.BACKGROUND_DARK
        )
        subtitle_label.pack()
    
    def _create_file_slots_container(self):
        """Create container for file slots"""
        files_frame = tk.Frame(self.main_content, bg=UITheme.BACKGROUND_DARK)
        files_frame.pack(fill="x", expand=False, pady=(0, 5))  # Changed to fill="x", expand=False for fixed height
        
        self.files_container = tk.Frame(files_frame, bg=UITheme.BACKGROUND_DARK)
        self.files_container.pack(fill="x", expand=False, padx=5, pady=5)  # Changed to fill="x", expand=False
        
        # Configure grid
        files_frame.grid_columnconfigure(0, weight=1)
        files_frame.grid_rowconfigure(0, weight=1)
    
    def _create_file_slots(self):
        """Create file upload slots"""
        # Clear existing slots
        for widget in self.files_container.winfo_children():
            widget.destroy()
        self.file_slots.clear()
        
        # Calculate grid layout
        grid_columns = self._calculate_grid_columns()
        
        # Create slots
        for i in range(self.target_file_count):
            row = i // grid_columns
            col = i % grid_columns
            
            slot = FileSlot(
                self.files_container, 
                i + 1, 
                row, 
                col,
                self._on_file_loaded,
                self._on_file_cleared
            )
            self.file_slots.append(slot)
        
        # Configure grid centering
        for col in range(grid_columns):
            self.files_container.grid_columnconfigure(col, weight=1, pad=5)
        
        self.files_container.grid_anchor("center")
    
    def _calculate_grid_columns(self):
        """Calculate optimal grid layout for 3 files"""
        try:
            self.root.update()
            window_width = self.root.winfo_width()
            
            if window_width <= 100:
                window_width = 1200  # Default fallback
        except:
            window_width = 1200
        
        # Optimal layout for 3 files
        if window_width < 600:
            return 1  # Stack vertically
        elif window_width < 900:
            return 2  # 2 columns
        else:
            return 3  # 3 columns (ideal)
    
    def _create_action_buttons(self):
        """Create action buttons"""
        action_frame = tk.Frame(self.main_content, bg=UITheme.BACKGROUND_DARK)
        action_frame.pack(fill="x", pady=(5, 5))
        
        action_inner = tk.Frame(action_frame, bg=UITheme.BACKGROUND_DARK)
        action_inner.pack(anchor="center")
        
        # Export to Excel button
        export_style = UITheme.get_button_style("disabled")
        self.export_btn = tk.Button(
            action_inner,
            text="📊 Export to Excel",
            command=self._export_results,
            font=UITheme.get_font_config("subheader"),
            **export_style,
            padx=30,
            pady=12,
            state="disabled"
        )
        self.export_btn.pack(side="right")
        
        # Compare button
        compare_style = UITheme.get_button_style("disabled")
        self.compare_btn = tk.Button(
            action_inner,
            text="🔍 Reconcile",
            command=self._compare_files,
            font=UITheme.get_font_config("subheader"),
            **compare_style,
            padx=30,
            pady=12,
            state="disabled"
        )
        self.compare_btn.pack(side="right", padx=(15, 15))
        
        # Clear all button
        clear_style = UITheme.get_button_style("danger")
        clear_all_btn = tk.Button(
            action_inner,
            text="🗑️ Clear All",
            command=self._clear_all_files,
            font=UITheme.get_font_config("subheader"),
            **clear_style,
            padx=30,
            pady=12
        )
        clear_all_btn.pack(side="right", padx=(15, 0))
    
    def _create_results_container(self):
        """Create results display container"""
        self.results_outer_container = tk.Frame(self.main_content, bg=UITheme.BACKGROUND_DARK)
        self.results_container = tk.Frame(self.results_outer_container, bg=UITheme.BACKGROUND_DARK)
        self.results_container.pack(fill="both", expand=True, padx=5, pady=5)
    
    def _create_status_bar(self):
        """Create status bar"""
        status_frame = tk.Frame(self.main_content, bg=UITheme.BACKGROUND_DARK)
        status_frame.pack(fill="x", pady=(5, 0))
        
        status_label = tk.Label(
            status_frame,
            text="📊 Ready to upload 3 files for reconciliation...",
            font=UITheme.get_font_config("body"),
            fg=UITheme.TEXT_SECONDARY,
            bg=UITheme.BACKGROUND_DARK
        )
        status_label.pack(side="left")
    
    def _on_file_loaded(self, slot_number, file_data):
        """Handle file loaded event"""
        self.uploaded_files[slot_number] = file_data
        self._update_button_states()
    
    def _on_file_cleared(self, slot_number):
        """Handle file cleared event"""
        if slot_number in self.uploaded_files:
            del self.uploaded_files[slot_number]
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button states based on loaded files"""
        if len(self.uploaded_files) >= 3:
            primary_style = UITheme.get_button_style("primary")
            self.compare_btn.configure(state="normal", **primary_style)
            
            # Enable export button only if results are available
            if hasattr(self, 'current_results') and self.current_results:
                export_style = UITheme.get_button_style("primary")
                self.export_btn.configure(state="normal", **export_style)
            else:
                disabled_style = UITheme.get_button_style("disabled")
                self.export_btn.configure(state="disabled", **disabled_style)
        else:
            disabled_style = UITheme.get_button_style("disabled")
            self.compare_btn.configure(state="disabled", **disabled_style)
            self.export_btn.configure(state="disabled", **disabled_style)
            
            # Reset results when clearing files
            self.results_outer_container.pack_forget()
            self.current_results = None
    
    def _compare_files(self):
        """Perform file comparison and reconciliation"""
        if len(self.uploaded_files) < 3:
            messagebox.showwarning("Insufficient Files", "Please upload all 3 files for reconciliation")
            return
        
        # Clear previous results
        for widget in self.results_container.winfo_children():
            widget.destroy()
        
        # Show results container
        self.results_outer_container.pack(fill="both", expand=True, pady=(20, 0))
        
        # Get file data
        file_list = list(self.uploaded_files.values())
        bank_ledger_df = file_list[0]['data']
        sib_qr_df = file_list[1]['data'] 
        demand_report_df = file_list[2]['data']
        
        # Create reconciliation engine
        recon_engine = ModularReconciliationEngine(bank_ledger_df, sib_qr_df, demand_report_df)
        
        # Store engine for export functionality
        self.current_recon_engine = recon_engine
        self.current_results = True  # Flag that results are available
        self._update_button_states()  # Enable export button
        
        # Results header
        results_header = tk.Frame(self.results_container, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
        results_header.pack(fill="x", padx=5, pady=(0, 10))
        
        header_label = tk.Label(
            results_header,
            text="🏦 Unnatti Finserv Reconciliation Results",
            font=UITheme.get_font_config("header"),
            fg=UITheme.ACCENT_BLUE,
            bg=UITheme.BACKGROUND_MEDIUM
        )
        header_label.pack(pady=15)
        
        # Create results notebook
        notebook = ttk.Notebook(self.results_container)
        notebook.pack(fill="both", expand=True, padx=5)
        
        # Add reconciliation tab
        self._create_reconciliation_tab(notebook, recon_engine)
    
    def _create_reconciliation_tab(self, notebook, recon_engine):
        """Create reconciliation analysis tab"""
        recon_frame = tk.Frame(notebook, bg=UITheme.BACKGROUND_DARK)
        notebook.add(recon_frame, text="🏦 Reconciliation Analysis")
        
        # Create scrollable frame
        canvas = tk.Canvas(recon_frame, bg=UITheme.BACKGROUND_DARK, highlightthickness=0)
        scrollbar = ttk.Scrollbar(recon_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=UITheme.BACKGROUND_DARK)
        
        def configure_scroll_region():
            # Force update of all child widgets first
            scrollable_frame.update_idletasks()
            canvas.update_idletasks()
            
            # Get the actual bounding box of all content
            bbox = canvas.bbox("all")
            if bbox:
                canvas.configure(scrollregion=bbox)
                # Add extra padding to ensure full content is scrollable
                x1, y1, x2, y2 = bbox
                canvas.configure(scrollregion=(x1, y1, x2, y2 + 50))  # Add 50px padding at bottom
            
            # Update canvas window size to match canvas width
            canvas_width = canvas.winfo_width()
            if canvas_width > 1:
                canvas.itemconfig(canvas_window, width=canvas_width)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.after_idle(configure_scroll_region))
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enhanced mouse wheel scrolling
        def on_scroll(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Bind scroll to multiple widgets for better coverage
        canvas.bind("<MouseWheel>", on_scroll)
        scrollable_frame.bind("<MouseWheel>", on_scroll)
        recon_frame.bind("<MouseWheel>", on_scroll)
        
        # Bind canvas resize to update scroll region
        canvas.bind("<Configure>", lambda e: canvas.after_idle(configure_scroll_region))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Generate simple reconciliation analysis
        try:
            # Use direct pivot table comparison
            reconciliation_result = recon_engine.merge_pivot_tables_comparison()
            
            # CRITICAL: Cache the results for export
            self.current_results = reconciliation_result
            
            self._display_simple_reconciliation_results(scrollable_frame, reconciliation_result, recon_engine)
            
            # Force multiple scroll region updates to ensure content is captured
            def final_scroll_update():
                # Manual calculation of required scroll height
                total_height = 0
                
                # Add height of all child widgets
                for child in scrollable_frame.winfo_children():
                    child.update_idletasks()
                    total_height += child.winfo_reqheight()
                
                # Set scroll region to at least the calculated height
                canvas.configure(scrollregion=(0, 0, 0, max(total_height, 600)))
                configure_scroll_region()
            
            canvas.after(100, configure_scroll_region)
            canvas.after(500, configure_scroll_region)  # Additional delayed update
            canvas.after(1000, final_scroll_update)     # Final comprehensive update
        except Exception as e:
            error_label = tk.Label(
                scrollable_frame,
                text=f"Error during reconciliation analysis:\n{str(e)}",
                font=UITheme.get_font_config("body"),
                fg=UITheme.ERROR_RED,
                bg=UITheme.BACKGROUND_DARK
            )
            error_label.pack(expand=True)
    
    def _display_simple_reconciliation_results(self, parent, results, recon_engine=None):
        """Display simplified reconciliation results showing only total matches and mismatches"""
        try:
            summary = results.get('reconciliation_summary', {})
            
            # Create cards container
            cards_container = tk.Frame(parent, bg=UITheme.BACKGROUND_DARK)
            cards_container.pack(fill="x", padx=20, pady=10)
            
            # Configure grid for two equal columns
            cards_container.grid_columnconfigure(0, weight=1)
            cards_container.grid_columnconfigure(1, weight=1)
            
            # Get totals
            total_matched = summary.get('total_matches', 0)
            total_mismatches = summary.get('amount_mismatches', 0)
            match_rate = summary.get('match_percentage', 0)
            
            # Create matched records card
            matched_card = tk.Frame(cards_container, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
            matched_card.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
            
            # Matches card header
            tk.Label(
                matched_card,
                text="✅ Matched Records",
                font=UITheme.get_font_config("subheader"),
                fg=UITheme.ACCENT_BLUE,
                bg=UITheme.BACKGROUND_MEDIUM
            ).pack(pady=5)
            
            # Matches count
            tk.Label(
                matched_card,
                text=f"{total_matched}",
                font=UITheme.get_font_config("title"),
                fg="#00C851",  # Green color for matches
                bg=UITheme.BACKGROUND_MEDIUM
            ).pack(pady=5)
            
            # Match rate percentage
            tk.Label(
                matched_card,
                text=f"Match Rate: {match_rate:.1f}%",
                font=UITheme.get_font_config("body"),
                fg=UITheme.TEXT_PRIMARY,
                bg=UITheme.BACKGROUND_MEDIUM
            ).pack(pady=5)
            
            # Create mismatched records card
            mismatch_card = tk.Frame(cards_container, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
            mismatch_card.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
            
            # Mismatches card header
            tk.Label(
                mismatch_card,
                text="❌ Mismatched Records",
                font=UITheme.get_font_config("subheader"),
                fg=UITheme.ACCENT_BLUE,
                bg=UITheme.BACKGROUND_MEDIUM
            ).pack(pady=5)
            
            # Mismatches count
            tk.Label(
                mismatch_card,
                text=f"{total_mismatches}",
                font=UITheme.get_font_config("title"),
                fg="#ff4444",  # Red color for mismatches
                bg=UITheme.BACKGROUND_MEDIUM
            ).pack(pady=5)
            
            # Net difference if available
            if 'net_difference' in summary:
                net_diff = summary['net_difference']
                tk.Label(
                    mismatch_card,
                    text=f"Net Difference: ₹{net_diff:,.2f}",
                    font=UITheme.get_font_config("body"),
                    fg=UITheme.TEXT_PRIMARY,
                    bg=UITheme.BACKGROUND_MEDIUM
                ).pack(pady=5)
            
            # Stage 2 Results (Group Payment Distribution)
            if 'stage2_results' in results:
                stage2_results = results['stage2_results']
                if stage2_results and stage2_results.get('status') == 'success' and stage2_results.get('newly_matched') is not None and not stage2_results['newly_matched'].empty:
                    # Only show if there are actual group matches
                    group_frame = tk.Frame(cards_container, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
                    group_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
                    
                    group_matches = len(stage2_results['newly_matched'])
                    
                    tk.Label(
                        group_frame,
                        text=f"✅ Group Payment Matches: {group_matches}",
                        font=UITheme.get_font_config("subheader"),
                        fg=UITheme.ACCENT_BLUE,
                        bg=UITheme.BACKGROUND_MEDIUM
                    ).pack(pady=5)
                    
                    # Show the group payment details in a table
                    self._create_simple_data_table(
                        group_frame, 
                        "Group Payment Details", 
                        stage2_results['newly_matched']
                    )
            
        except Exception as e:
            error_msg = f"Error displaying results: {str(e)}"
            logging.error(error_msg, exc_info=True)
            
            error_label = tk.Label(
                parent,
                text=error_msg,
                font=UITheme.get_font_config("body"),
                fg=UITheme.ERROR_RED,
                bg=UITheme.BACKGROUND_DARK,
                wraplength=600
            )
            error_label.pack(pady=20)
    
    def _export_simple_results(self, results):
        """Export simplified reconciliation results to Excel"""
        try:
            # Get file path
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Reconciliation Report"
            )
            
            if not file_path:
                return
            
            # Show export options dialog
            export_dialog = tk.Toplevel(self.root)
            export_dialog.title("Export Options")
            export_dialog.geometry("400x200")
            export_dialog.transient(self.root)
            export_dialog.grab_set()
            
            # Center the dialog
            export_dialog.update_idletasks()
            x = (export_dialog.winfo_screenwidth() // 2) - (export_dialog.winfo_width() // 2)
            y = (export_dialog.winfo_screenheight() // 2) - (export_dialog.winfo_height() // 2)
            export_dialog.geometry(f"+{x}+{y}")
            
            tk.Label(
                export_dialog, 
                text="Select Export Format:", 
                font=("Arial", 12, "bold")
            ).pack(pady=20)
            
            export_format = tk.StringVar(value="reconciliation")
            
            tk.Radiobutton(
                export_dialog,
                text="📊 Standard Reconciliation Report (Pivoted)",
                variable=export_format,
                value="reconciliation",
                font=("Arial", 10)
            ).pack(anchor="w", padx=40, pady=5)
            
            tk.Radiobutton(
                export_dialog,
                text="🏦 Bank Ledger Format (with Credit/Debit/Remarks)",
                variable=export_format,
                value="bank_ledger",
                font=("Arial", 10)
            ).pack(anchor="w", padx=40, pady=5)
            
            def do_export():
                export_dialog.destroy()
                selected_format = export_format.get()
                
                try:
                    if selected_format == "bank_ledger":
                        # Export in bank ledger format
                        print("🏦 Exporting in bank ledger format...")
                        if hasattr(self, 'current_recon_engine') and self.current_recon_engine:
                            # Use the new bank ledger export
                            from reconciliation.exporters.export_manager import ExportManager
                            export_mgr = ExportManager()
                            
                            export_path = export_mgr.export_bank_ledger_with_reconciliation(
                                bank_processor=self.current_recon_engine.bank_processor,
                                reconciliation_data=results,
                                output_filename=os.path.basename(file_path),
                                output_dir=os.path.dirname(file_path)
                            )
                            
                            if export_path:
                                messagebox.showinfo(
                                    "Export Successful", 
                                    f"Bank ledger with reconciliation results exported successfully!\n\n"
                                    f"File: {export_path}\n\n"
                                    f"Format includes:\n"
                                    f"• All original bank columns\n"
                                    f"• Credit (QR Collected)\n"
                                    f"• Debit (System Required)\n"
                                    f"• Difference\n"
                                    f"• Remarks\n\n"
                                    f"✗ Unmatched entries highlighted in RED"
                                )
                            else:
                                messagebox.showerror("Export Error", "Failed to export bank ledger format")
                        else:
                            messagebox.showerror("Export Error", "Reconciliation engine not available")
                    else:
                        # Export standard reconciliation report
                        print("📊 Exporting standard reconciliation report...")
                        merged_data = results.get('merged_pivot_data')
                        
                        if merged_data is not None and not merged_data.empty:
                            # Export to Excel
                            with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
                                merged_data.to_excel(writer, sheet_name='Reconciliation', index=False)
                                
                                # Add summary sheet if available
                                if 'reconciliation_summary' in results:
                                    summary = results['reconciliation_summary']
                                    summary_df = pd.DataFrame(list(summary.items()), columns=['Metric', 'Value'])
                                    summary_df.to_excel(writer, sheet_name='Summary', index=False)
                            
                            messagebox.showinfo(
                                "Export Successful", 
                                f"Reconciliation results exported successfully to:\n{file_path}"
                            )
                        else:
                            messagebox.showerror("Export Error", "No data available to export")
                            
                except Exception as e:
                    error_msg = f"Error during export: {str(e)}"
                    logging.error(error_msg, exc_info=True)
                    messagebox.showerror("Export Error", error_msg)
                    import traceback
                    traceback.print_exc()
            
            tk.Button(
                export_dialog,
                text="Export",
                command=do_export,
                font=("Arial", 10, "bold"),
                bg="#4CAF50",
                fg="white",
                padx=20,
                pady=5
            ).pack(pady=20)
            
        except Exception as e:
            error_msg = f"Error exporting results: {str(e)}"
            logging.error(error_msg, exc_info=True)
            messagebox.showerror("Export Error", error_msg)

    def _create_simple_data_table(self, parent, title, dataframe):
        """Create a simple data table display for reconciliation results"""
        try:
            # Table frame - increased size for better visibility
            table_frame = tk.Frame(parent, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
            table_frame.pack(fill="both", expand=True, padx=10, pady=8)  # Changed to fill="both", expand=True
            
            # Table header
            header = tk.Label(
                table_frame,
                text=title,
                font=UITheme.get_font_config("subheader"),
                fg=UITheme.ACCENT_BLUE,
                bg=UITheme.BACKGROUND_MEDIUM
            )
            header.pack(pady=5)
            
            # Show only first few rows and relevant columns for reconciliation data
            display_columns = []
            
            # Check if this is simplified report data
            simplified_columns = ['loan_id', 'customer_name', 'group_id', 'branch', 'system_entry', 'qr_collection', 'difference']
            is_simplified = any(col in dataframe.columns for col in simplified_columns)
            
            if is_simplified:
                # Use simplified column structure
                essential_cols = ['loan_id', 'customer_name', 'group_id', 'branch', 'system_entry', 'qr_collection', 'difference']
                display_columns = [col for col in essential_cols if col in dataframe.columns]
            elif "QR Only" in title:
                # For QR Only records, use reference_id_clean instead of loan_id (which will be NaN)
                if 'reference_id_clean' in dataframe.columns:
                    display_columns.append('reference_id_clean')
                if 'qr_amount' in dataframe.columns:
                    display_columns.append('qr_amount')
                if 'amount_difference' in dataframe.columns:
                    display_columns.append('amount_difference')
                if 'reconciliation_status' in dataframe.columns:
                    display_columns.append('reconciliation_status')
            else:
                # For other records (Matched, Bank Only), use loan_id
                if 'loan_id' in dataframe.columns:
                    display_columns.append('loan_id')
                if 'system_amount' in dataframe.columns:
                    display_columns.append('system_amount')
                if 'qr_amount' in dataframe.columns:
                    display_columns.append('qr_amount')
                if 'amount_difference' in dataframe.columns:
                    display_columns.append('amount_difference')
                if 'reconciliation_status' in dataframe.columns:
                    display_columns.append('reconciliation_status')
            
            # Fallback to generic columns if reconciliation columns not found
            if not display_columns:
                if 'reference_id' in dataframe.columns:
                    display_columns.append('reference_id')
                if 'reference_id_clean' in dataframe.columns:
                    display_columns.append('reference_id_clean')
                if 'amount' in dataframe.columns:
                    display_columns.append('amount')
                if 'total_amount' in dataframe.columns:
                    display_columns.append('total_amount')
                if 'date' in dataframe.columns:
                    display_columns.append('date')
                if 'narration' in dataframe.columns:
                    display_columns.append('narration')
            
            # Final fallback: use first few columns
            if not display_columns:
                display_columns = list(dataframe.columns)[:4]
                
            # Limit to maximum 5 columns for readability
            display_columns = display_columns[:5]
            
            # Create text widget for table display - increased height for better visibility
            text_widget = tk.Text(
                table_frame,
                height=15,  # Increased from 8 to 15 for better visibility
                font=UITheme.get_font_config("mono"),
                bg=UITheme.BACKGROUND_LIGHT,
                fg=UITheme.TEXT_PRIMARY,
                wrap=tk.NONE
            )
            
            # Add scrollbars
            h_scrollbar = tk.Scrollbar(table_frame, orient="horizontal", command=text_widget.xview)
            v_scrollbar = tk.Scrollbar(table_frame, orient="vertical", command=text_widget.yview)
            text_widget.configure(xscrollcommand=h_scrollbar.set, yscrollcommand=v_scrollbar.set)
            
            # Format and insert data
            if not dataframe.empty:
                # Header row
                header_row = "\t".join([col[:25] for col in display_columns])  # Increased from 20 to 25
                text_widget.insert(tk.END, header_row + "\n")
                text_widget.insert(tk.END, "-" * 120 + "\n")  # Increased separator length from 80 to 120
                
                # Data rows - show more rows due to increased height
                display_data = dataframe[display_columns].head(20)  # Increased from 10 to 20 rows
                for _, row in display_data.iterrows():
                    data_row = "\t".join([str(row[col])[:25] for col in display_columns])  # Increased column width from 20 to 25
                    text_widget.insert(tk.END, data_row + "\n")
                
                if len(dataframe) > 20:
                    text_widget.insert(tk.END, f"\n... and {len(dataframe) - 20} more rows")
            else:
                text_widget.insert(tk.END, "No data to display")
            
            text_widget.config(state=tk.DISABLED)
            
            # Pack widgets
            text_widget.pack(side="left", fill="both", expand=True, padx=5, pady=5)
            v_scrollbar.pack(side="right", fill="y")
            h_scrollbar.pack(side="bottom", fill="x")
            
        except Exception as e:
            error_label = tk.Label(
                parent,
                text=f"Error displaying table {title}: {str(e)}",
                font=UITheme.get_font_config("body"),
                fg=UITheme.ERROR_RED,
                bg=UITheme.BACKGROUND_DARK
            )
            error_label.pack(pady=5)
    
    def _export_simple_results(self, results):
        """Export bank ledger with reconciliation remarks to Excel"""
        try:
            if not self.current_recon_engine:
                messagebox.showerror("Error", "No reconciliation engine available")
                return
            
            # Get file path from user
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Save Bank Ledger with Reconciliation Remarks"
            )
            
            if not file_path:
                return
            
            # Get output directory and filename from path
            output_dir = os.path.dirname(file_path)
            output_filename = os.path.basename(file_path)
            
            # Export bank ledger with remarks using the engine's method
            exported_path = self.current_recon_engine.export_manager.export_bank_ledger_with_reconciliation(
                bank_processor=self.current_recon_engine.bank_processor,
                reconciliation_data=results,
                output_filename=output_filename,
                output_dir=output_dir
            )
            
            if exported_path:
                # Get summary for success message
                summary = results.get('reconciliation_summary', {})
                total_records = summary.get('total_unique_loans', 0)
                total_matches = summary.get('total_matches', 0)
                match_rate = summary.get('match_percentage', 0)
                
                success_msg = f"📊 Bank Ledger Exported Successfully!\n\n"
                success_msg += f"📋 Summary:\n"
                success_msg += f"   • Total Bank Entries: {total_records:,}\n"
                success_msg += f"   • Matched Entries: {total_matches:,}\n"
                success_msg += f"   • Match Rate: {match_rate:.2f}%\n\n"
                success_msg += f"✨ Export Details:\n"
                success_msg += f"   • All original bank ledger columns preserved\n"
                success_msg += f"   • Remarks column added with match status\n"
                success_msg += f"   • Green highlighting for matched entries\n"
                success_msg += f"   • Red highlighting for unmatched entries\n\n"
                success_msg += f"📁 File: {file_path}"
                
                messagebox.showinfo("Export Successful", success_msg)
                print(f"✅ Export successful: {file_path}")
            else:
                messagebox.showerror("Export Failed", "Could not export bank ledger")
            
        except Exception as e:
            error_msg = f"Error exporting results: {str(e)}"
            logging.error(error_msg, exc_info=True)
            messagebox.showerror("Export Error", error_msg)
    
    def _apply_clean_formatting(self, file_path):
        """Apply clean, visible formatting to Excel file"""
        if not OPENPYXL_AVAILABLE:
            print("⚠️ Skipping formatting - openpyxl not available")
            return
            
        try:
            print(f"🔧 Starting formatting for: {file_path}")
            
            # Load the workbook
            print(f"📂 Loading workbook...")
            wb = load_workbook(file_path)
            print(f"📋 Sheets found: {wb.sheetnames}")
            
            # Define clean colors
            matched_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")  # Light green
            mismatch_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")  # Light red
            header_fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")   # Light gray
            header_font = Font(bold=True)
            
            for sheet_name in wb.sheetnames:
                print(f"🎨 Processing sheet: {sheet_name}")
                ws = wb[sheet_name]
                
                # Apply auto-filter to make it visible - with safe checks
                try:
                    max_row = ws.max_row
                    max_col = ws.max_column
                    if max_row and max_row > 1 and max_col and max_col > 1:
                        filter_ref = f"A1:{ws.cell(row=1, column=max_col).coordinate}{max_row}"
                        ws.auto_filter.ref = filter_ref
                        print(f"   ✅ Auto-filter applied: {filter_ref}")
                    else:
                        print(f"   ⚠️ Sheet {sheet_name} too small for auto-filter (rows: {max_row}, cols: {max_col})")
                except Exception as filter_error:
                    print(f"   ⚠️ Could not apply auto-filter to {sheet_name}: {filter_error}")
                    continue
                
                # Format headers - with safe max_column check
                try:
                    max_col = ws.max_column
                    if max_col and max_col > 0:
                        for col in range(1, max_col + 1):
                            cell = ws.cell(row=1, column=col)
                            cell.fill = header_fill
                            cell.font = header_font
                        print(f"   🎨 Headers formatted (columns 1-{max_col})")
                    else:
                        print(f"   ⚠️ No columns found in sheet {sheet_name}")
                except Exception as col_error:
                    print(f"   ⚠️ Could not format headers in {sheet_name}: {col_error}")
                    continue
                
                # Apply row coloring based on sheet name and status - with safe checks
                try:
                    max_row = ws.max_row
                    max_col = ws.max_column
                    
                    if 'Matched' in sheet_name and max_row and max_col and max_row > 1:
                        # Light green for matched records (limit rows for performance)
                        row_limit = min(max_row + 1, 1000)
                        for row in range(2, row_limit):
                            for col in range(1, max_col + 1):
                                ws.cell(row=row, column=col).fill = matched_fill
                        print(f"   🟢 Applied green background to {row_limit-2} rows")
                                
                    elif 'Mismatched' in sheet_name and max_row and max_col and max_row > 1:
                        # Light red for mismatched records (limit rows for performance)
                        row_limit = min(max_row + 1, 1000)
                        for row in range(2, row_limit):
                            for col in range(1, max_col + 1):
                                ws.cell(row=row, column=col).fill = mismatch_fill
                        print(f"   🔴 Applied red background to {row_limit-2} rows")
                
                    elif 'All' in sheet_name and max_row and max_col and max_row > 1:
                        # Apply conditional coloring based on status column
                        status_col = None
                        for col in range(1, max_col + 1):
                            cell_value = ws.cell(row=1, column=col).value
                            if cell_value and 'status' in str(cell_value).lower():
                                status_col = col
                                break
                        
                        if status_col:
                            row_limit = min(max_row + 1, 1000)  # Performance limit
                            for row in range(2, row_limit):
                                status_value = ws.cell(row=row, column=status_col).value
                                if status_value and 'MATCHED' in str(status_value):
                                    for col in range(1, max_col + 1):
                                        ws.cell(row=row, column=col).fill = matched_fill
                                elif status_value and 'MISMATCH' in str(status_value):
                                    for col in range(1, max_col + 1):
                                        ws.cell(row=row, column=col).fill = mismatch_fill
                            print(f"   🎨 Applied conditional coloring to {row_limit-2} rows")
                
                except Exception as color_error:
                    print(f"   ⚠️ Could not apply row coloring to {sheet_name}: {color_error}")
                
                # Auto-adjust column widths for better visibility - with safe checks
                try:
                    if ws.max_column and ws.max_column > 0:
                        for column in ws.columns:
                            max_length = 0
                            column_letter = column[0].column_letter
                            for cell in column[:100]:  # Limit cells checked for performance
                                try:
                                    cell_value = str(cell.value) if cell.value is not None else ""
                                    if len(cell_value) > max_length:
                                        max_length = len(cell_value)
                                except:
                                    pass
                            adjusted_width = min(max_length + 2, 30)  # Cap at 30 chars
                            ws.column_dimensions[column_letter].width = adjusted_width
                        print(f"   📏 Column widths auto-adjusted")
                except Exception as width_error:
                    print(f"   ⚠️ Could not adjust column widths in {sheet_name}: {width_error}")
            
            # Save the formatted workbook
            wb.save(file_path)
            print("✅ Clean formatting applied - filters and colors should be visible")
            
        except Exception as e:
            print(f"⚠️ Warning: Could not apply formatting: {e}")
            # Don't fail the export if formatting fails
    
    def _display_reconciliation_results(self, parent, summary, recon_engine=None):
        """Display reconciliation results"""
        # Bank Ledger Analysis
        bank_frame = tk.Frame(parent, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
        bank_frame.pack(fill="x", padx=10, pady=5)
        
        bank_header = tk.Label(
            bank_frame,
            text="📋 Bank Ledger Analysis",
            font=UITheme.get_font_config("subheader"),
            fg=UITheme.ACCENT_BLUE,
            bg=UITheme.BACKGROUND_MEDIUM
        )
        bank_header.pack(pady=5)
        
        bank_analysis = summary['bank_ledger']
        if bank_analysis['status'] == 'success':
            filtered_data = bank_analysis['filtered_data']
            parsed_data = bank_analysis.get('parsed_data')
            
            # Summary statistics in compact format
            stats_frame = tk.Frame(bank_frame, bg=UITheme.BACKGROUND_LIGHT, relief="solid", bd=1)
            stats_frame.pack(fill="x", padx=10, pady=5)
            
            if parsed_data:
                stats_text = f"� Total: {filtered_data['total_rows']} | ✅ Valid Loans: {parsed_data['valid_loan_entries']} | ❌ Filtered: {parsed_data['filtered_out_entries']} | Success: {(parsed_data['valid_loan_entries'] / parsed_data['total_rows'] * 100):.1f}%"
            else:
                stats_text = f"📊 Processed Rows: {filtered_data['total_rows']} | Columns: {filtered_data['narration_column']}, {filtered_data['amount_column']}"
            
            stats_label = tk.Label(
                stats_frame,
                text=stats_text,
                font=UITheme.get_font_config("body"),
                fg=UITheme.TEXT_PRIMARY,
                bg=UITheme.BACKGROUND_LIGHT
            )
            stats_label.pack(pady=5, padx=10)
            
            # Create table for parsed loan data
            if parsed_data and parsed_data['sample_valid_loans']:
                self._create_data_table(
                    bank_frame, 
                    "✅ Valid Loan Entries - Parsed Data (Head)",
                    parsed_data['sample_valid_loans'][:5],
                    ['description', 'loan_id', 'customer_name', 'group_name', filtered_data['amount_column']],
                    ['Description', 'Loan ID', 'Customer Name', 'Group', 'Amount'],
                    UITheme.SUCCESS_GREEN
                )
            
            # Create table for filtered out entries
            if parsed_data and parsed_data['sample_filtered_out']:
                self._create_data_table(
                    bank_frame,
                    "❌ Filtered Out Entries (Head)",
                    parsed_data['sample_filtered_out'][:3],
                    ['loan_id_original', 'filter_reason'],
                    ['Original Value', 'Filter Reason'],
                    UITheme.ERROR_RED
                )
        
        # SIB QR Report Analysis
        sib_frame = tk.Frame(parent, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
        sib_frame.pack(fill="x", padx=10, pady=5)
        
        sib_header = tk.Label(
            sib_frame,
            text="📱 SIB QR Report Analysis",
            font=UITheme.get_font_config("subheader"),
            fg=UITheme.ACCENT_BLUE,
            bg=UITheme.BACKGROUND_MEDIUM
        )
        sib_header.pack(pady=5)
        
        sib_analysis = summary['sib_qr_report']
        if sib_analysis.get('sample_data'):
            # Get column names from the data
            sample_data = sib_analysis['sample_data']
            if sample_data:
                # Use first few columns from the actual data
                available_columns = list(sample_data[0].keys())[:5]  # Show first 5 columns
                display_names = [col.replace('_', ' ').title() for col in available_columns]
                
                self._create_data_table(
                    sib_frame,
                    f"📱 SIB QR Report Data (Head - {len(sample_data)} rows)",
                    sample_data,
                    available_columns,
                    display_names,
                    UITheme.BACKGROUND_LIGHT
                )
        else:
            no_data_label = tk.Label(
                sib_frame,
                text="📝 Total Rows: {} | Total Columns: {}".format(
                    sib_analysis.get('total_rows', 0),
                    sib_analysis.get('total_columns', 0)
                ),
                font=UITheme.get_font_config("body"),
                fg=UITheme.TEXT_PRIMARY,
                bg=UITheme.BACKGROUND_MEDIUM
            )
            no_data_label.pack(pady=5, padx=10)
        
        # Demand Report Analysis
        demand_frame = tk.Frame(parent, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
        demand_frame.pack(fill="x", padx=10, pady=5)
        
        demand_header = tk.Label(
            demand_frame,
            text="📋 Demand Report Analysis",
            font=UITheme.get_font_config("subheader"),
            fg=UITheme.ACCENT_BLUE,
            bg=UITheme.BACKGROUND_MEDIUM
        )
        demand_header.pack(pady=5)
        
        demand_analysis = summary['demand_report']
        if demand_analysis.get('sample_data'):
            # Get column names from the data
            sample_data = demand_analysis['sample_data']
            if sample_data:
                # Use first few columns from the actual data
                available_columns = list(sample_data[0].keys())[:5]  # Show first 5 columns
                display_names = [col.replace('_', ' ').title() for col in available_columns]
                
                self._create_data_table(
                    demand_frame,
                    f"📋 Demand Report Data (Head - {len(sample_data)} rows)",
                    sample_data,
                    available_columns,
                    display_names,
                    UITheme.BACKGROUND_LIGHT
                )
        else:
            no_data_label = tk.Label(
                demand_frame,
                text="📝 Total Rows: {} | Total Columns: {}".format(
                    demand_analysis.get('total_rows', 0),
                    demand_analysis.get('total_columns', 0)
                ),
                font=UITheme.get_font_config("body"),
                fg=UITheme.TEXT_PRIMARY,
                bg=UITheme.BACKGROUND_MEDIUM
            )
            no_data_label.pack(pady=5, padx=10)
        
        # SIB QR Report Analysis
        sib_analysis = summary.get('sib_qr_report')
        if sib_analysis and sib_analysis.get('processed_data'):
            sib_frame = tk.Frame(parent, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
            sib_frame.pack(fill="x", padx=10, pady=5)
            
            sib_header = tk.Label(
                sib_frame,
                text="📱 SIB QR Report Analysis",
                font=UITheme.get_font_config("subheader"),
                fg=UITheme.ACCENT_BLUE,
                bg=UITheme.BACKGROUND_MEDIUM
            )
            sib_header.pack(pady=5)
            
            sib_data = sib_analysis['processed_data']
            sib_info_text = f"""
✅ SIB QR Report Processing:
📊 Total Records: {sib_data['total_rows']}
🆔 Reference ID Column: {sib_data['reference_id_column']}
💰 Amount Column: {sib_data['amount_column']}
            """
            
            sib_info_label = tk.Label(
                sib_frame,
                text=sib_info_text.strip(),
                font=UITheme.get_font_config("body"),
                fg=UITheme.TEXT_PRIMARY,
                bg=UITheme.BACKGROUND_MEDIUM,
                justify="left"
            )
            sib_info_label.pack(pady=5, padx=10)
            
            # Display SIB QR data table
            if sib_data['sample_data']:
                display_columns = ['reference_id', 'amount', 'payer_name', 'tran_date', 'payer_vpa']
                table_frame = self._create_data_table(
                    sib_frame,
                    "📱 SIB QR Report Data (Sample)",
                    sib_data['sample_data'],
                    list(sib_data['sample_data'][0].keys()) if sib_data['sample_data'] else [],
                    display_columns,
                    UITheme.BACKGROUND_LIGHT
                )
        
        # Demand Report Analysis
        demand_analysis = summary.get('demand_report')
        if demand_analysis and demand_analysis.get('extracted_data'):
            demand_frame = tk.Frame(parent, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
            demand_frame.pack(fill="x", padx=10, pady=5)
            
            demand_header = tk.Label(
                demand_frame,
                text="📋 Demand Report Analysis",
                font=UITheme.get_font_config("subheader"),
                fg=UITheme.ACCENT_BLUE,
                bg=UITheme.BACKGROUND_MEDIUM
            )
            demand_header.pack(pady=5)
            
            demand_data = demand_analysis['extracted_data']
            demand_info_text = f"""
✅ Demand Report Extraction:
📊 Total Records: {demand_data['total_rows']}
🆔 Loan ID Column: {demand_data['loan_id_column']}
📝 Extracted for Merging: loan_id, branch_name, group_name, member_name
            """
            
            demand_info_label = tk.Label(
                demand_frame,
                text=demand_info_text.strip(),
                font=UITheme.get_font_config("body"),
                fg=UITheme.TEXT_PRIMARY,
                bg=UITheme.BACKGROUND_MEDIUM,
                justify="left"
            )
            demand_info_label.pack(pady=5, padx=10)
            
            # Display Demand Report data table
            if demand_data['sample_data']:
                display_columns = ['loan_id', 'branch_name', 'group_name', 'member_name']
                table_frame = self._create_data_table(
                    demand_frame,
                    "📋 Demand Report Data (Sample)",
                    demand_data['sample_data'],
                    list(demand_data['sample_data'][0].keys()) if demand_data['sample_data'] else [],
                    display_columns,
                    UITheme.BACKGROUND_LIGHT
                )
        
        # Merged SIB QR + Demand Report Data
        merged_data = summary.get('merged_sib_demand')
        if merged_data and merged_data['status'] == 'success':
            merged_frame = tk.Frame(parent, bg=UITheme.BACKGROUND_MEDIUM, relief="solid", bd=1)
            merged_frame.pack(fill="x", padx=10, pady=5)
            
            merged_header = tk.Label(
                merged_frame,
                text="🔗 Merged SIB QR + Demand Report Data",
                font=UITheme.get_font_config("subheader"),
                fg=UITheme.ACCENT_BLUE,
                bg=UITheme.BACKGROUND_MEDIUM
            )
            merged_header.pack(pady=5)
            
            # Merge statistics
            merge_stats = merged_data['merge_stats']
            debug_info = merged_data.get('debug_info', {})
            
            merge_stats_text = f"""
✅ Merge Results:
📊 SIB QR Records: {merge_stats['sib_records']}
📋 Demand Records: {merge_stats['demand_records']}
🔗 Matched Records: {merge_stats['matched_records']}
❌ Unmatched SIB Records: {merge_stats['unmatched_sib_records']}
📈 Match Rate: {merge_stats['match_rate']:.1f}%
            """
            
            # Add debug info if there are issues
            if debug_info.get('error_message'):
                merge_stats_text += f"""
⚠️ Debug Info:
• SIB Data Available: {debug_info.get('sib_data_available', 'Unknown')}
• Demand Data Available: {debug_info.get('demand_data_available', 'Unknown')}
• Merge Columns Present: {debug_info.get('merge_columns_present', 'Unknown')}
• Error: {debug_info.get('error_message', 'No error')}
            """
            
            merge_stats_label = tk.Label(
                merged_frame,
                text=merge_stats_text.strip(),
                font=UITheme.get_font_config("body"),
                fg=UITheme.TEXT_PRIMARY,
                bg=UITheme.BACKGROUND_MEDIUM,
                justify="left"
            )
            merge_stats_label.pack(pady=5, padx=10)
            
            # Display merged data tables
            merged_table_data = merged_data['merged_data']
            if merged_table_data:
                # Display matched records
                if merged_table_data.get('matched_sample'):
                    display_columns = [
                        'reference_id', 'amount', 'payer_name', 'tran_date',
                        'branch_name', 'group_name', 'member_name', 'merge_status'
                    ]
                    
                    matched_table = self._create_data_table(
                        merged_frame,
                        "✅ Successfully Matched Records",
                        merged_table_data['matched_sample'],
                        list(merged_table_data['matched_sample'][0].keys()) if merged_table_data['matched_sample'] else [],
                        display_columns,
                        UITheme.SUCCESS_GREEN
                    )
                
                # Display unmatched records
                if merged_table_data.get('unmatched_sample'):
                    unmatched_columns = [
                        'reference_id', 'amount', 'payer_name', 'tran_date', 'merge_status'
                    ]
                    
                    unmatched_table = self._create_data_table(
                        merged_frame,
                        "❌ Unmatched SIB QR Records",
                        merged_table_data['unmatched_sample'],
                        list(merged_table_data['unmatched_sample'][0].keys()) if merged_table_data['unmatched_sample'] else [],
                        unmatched_columns,
                        UITheme.ERROR_RED
                    )
                
                # Show all data sample if no specific matched/unmatched samples
                elif merged_table_data.get('sample_data'):
                    display_columns = [
                        'reference_id', 'amount', 'payer_name', 
                        'branch_name', 'group_name', 'member_name', 'merge_status'
                    ]
                    
                    all_table = self._create_data_table(
                        merged_frame,
                        "🔗 Merged SIB QR + Demand Data (Sample)",
                        merged_table_data['sample_data'],
                        list(merged_table_data['sample_data'][0].keys()) if merged_table_data['sample_data'] else [],
                        display_columns,
                        UITheme.SUCCESS_GREEN
                    )
        
        # Summary Statistics
        stats_frame = tk.Frame(parent, bg=UITheme.SUCCESS_GREEN, relief="solid", bd=1)
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        stats_header = tk.Label(
            stats_frame,
            text="📊 Reconciliation Summary",
            font=UITheme.get_font_config("subheader"),
            fg=UITheme.ACCENT_BLUE,
            bg=UITheme.SUCCESS_GREEN
        )
        stats_header.pack(pady=5)
        
        stats = summary['summary_stats']
        stats_text = f"""
🏦 Bank Transactions: {stats['total_bank_transactions']}
📱 SIB QR Transactions: {stats['total_sib_transactions']}  
📋 Demand Entries: {stats['total_demand_entries']}
🔗 Bank-SIB Matches: {stats['bank_sib_matches']}
🔗 Bank-Demand Matches: {stats['bank_demand_matches']}
📈 Match Rate: {stats['match_percentage']:.1f}%
        """
        
        stats_label = tk.Label(
            stats_frame,
            text=stats_text.strip(),
            font=UITheme.get_font_config("body"),
            fg=UITheme.TEXT_PRIMARY,
            bg=UITheme.SUCCESS_GREEN,
            justify="left"
        )
        stats_label.pack(pady=5, padx=10)
        
        # Export buttons section
        if recon_engine:
            self._create_export_buttons(parent, recon_engine)
    
    def _create_data_table(self, parent, title, data, data_columns, display_columns, bg_color):
        """Create a formatted table display for data"""
        if not data:
            return
        
        table_frame = tk.Frame(parent, bg=bg_color, relief="solid", bd=1)
        table_frame.pack(fill="x", padx=10, pady=5)
        
        # Table header
        header_label = tk.Label(
            table_frame,
            text=title,
            font=UITheme.get_font_config("body"),
            fg=UITheme.ACCENT_BLUE,
            bg=bg_color
        )
        header_label.pack(pady=3)
        
        # Create table container with scrollbar if needed
        table_container = tk.Frame(table_frame, bg=bg_color)
        table_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Column headers
        header_frame = tk.Frame(table_container, bg=UITheme.BACKGROUND_DARK, relief="solid", bd=1)
        header_frame.pack(fill="x", pady=(0, 2))
        
        for i, col_name in enumerate(display_columns):
            header_cell = tk.Label(
                header_frame,
                text=col_name,
                font=UITheme.get_font_config("body"),
                fg=UITheme.TEXT_PRIMARY,
                bg=UITheme.BACKGROUND_DARK,
                relief="solid",
                bd=1,
                anchor="w",
                padx=8,
                pady=4
            )
            header_cell.grid(row=0, column=i, sticky="ew")
        
        # Configure column weights for responsive layout
        for i in range(len(display_columns)):
            header_frame.grid_columnconfigure(i, weight=1)
        
        # Data rows
        for row_idx, record in enumerate(data):
            row_frame = tk.Frame(table_container, bg=UITheme.BACKGROUND_LIGHT, relief="solid", bd=1)
            row_frame.pack(fill="x", pady=1)
            
            for col_idx, col_key in enumerate(data_columns):
                cell_value = str(record.get(col_key, 'N/A'))
                
                # Truncate long values
                if len(cell_value) > 25:
                    cell_value = cell_value[:22] + "..."
                
                cell_label = tk.Label(
                    row_frame,
                    text=cell_value,
                    font=UITheme.get_font_config("small"),
                    fg=UITheme.TEXT_PRIMARY,
                    bg=UITheme.BACKGROUND_LIGHT,
                    relief="solid",
                    bd=1,
                    anchor="w",
                    padx=8,
                    pady=3
                )
                cell_label.grid(row=0, column=col_idx, sticky="ew")
            
            # Configure column weights for this row
            for i in range(len(data_columns)):
                row_frame.grid_columnconfigure(i, weight=1)
    
    def _export_results(self):
        """Export reconciliation results to Excel"""
        if not hasattr(self, 'current_results') or not self.current_results:
            messagebox.showwarning("Export Not Available", "Please run 'Reconcile' first to generate results before exporting.")
            return
        
        try:
            # Use cached reconciliation data (already includes Stage 2 processing)
            reconciliation_data = self.current_results
            
            if reconciliation_data and reconciliation_data.get('status') == 'success':
                # Use the existing working export method
                self._export_simple_results(reconciliation_data)
                
                # Show additional info if Stage 2 was applied
                if reconciliation_data.get('stage2_result'):
                    stage2_info = reconciliation_data['stage2_result']
                    resolved_count = len(stage2_info.get('newly_matched', []))
                    if resolved_count > 0:
                        messagebox.showinfo("Export Info", 
                                          f"Export includes Stage 2 group payment redistributions.\n"
                                          f"✅ {resolved_count} records were redistributed with correct individual amounts.")
            else:
                messagebox.showerror("Export Error", "Failed to get reconciliation data for export")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Error exporting results: {str(e)}")
            print(f"Export error: {e}")
            import traceback
            traceback.print_exc()
    
    def _clear_all_files(self):
        """Clear all uploaded files"""
        if messagebox.askyesno("Clear All", "Are you sure you want to clear all files?"):
            self.uploaded_files.clear()
            
            # Clear all file slots
            for slot in self.file_slots:
                slot._clear_file()
            
            # Clear results
            self.current_results = None
            self.current_recon_engine = None
            
            self._hide_results()
            self._update_button_states()
    
    def _on_window_resize(self, event):
        """Handle window resize events"""
        if event.widget != self.root:
            return
        
        # Update scroll region
        self.root.after_idle(lambda: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        
        # Center content
        self.root.after_idle(self._center_canvas_content)
        
        # Recreate file slots if grid layout should change
        old_columns = getattr(self, '_last_grid_columns', 3)
        new_columns = self._calculate_grid_columns()
        
        if old_columns != new_columns and self.file_slots:
            self._last_grid_columns = new_columns
            # Save current data
            temp_files = self.uploaded_files.copy()
            
            # Recreate slots
            self._create_file_slots()
            
            # Restore data
            for slot_num, file_data in temp_files.items():
                if slot_num <= len(self.file_slots):
                    slot = self.file_slots[slot_num - 1]
                    slot.file_data = file_data
                    slot._update_loaded_state()
            
            self.uploaded_files = temp_files
            self._update_button_states()
    
    def _center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def _create_export_buttons(self, parent, recon_engine):
        """Create export functionality buttons"""
        
        # Export section header
        export_frame = tk.Frame(parent, bg=UITheme.ACCENT_BLUE, relief="solid", bd=1)
        export_frame.pack(fill="x", padx=10, pady=(15, 5))
        
        export_header = tk.Label(
            export_frame,
            text="📊 Export Results",
            font=UITheme.get_font_config("subheader"),
            fg="white",
            bg=UITheme.ACCENT_BLUE
        )
        export_header.pack(pady=10)
        
        # Export buttons container
        buttons_frame = tk.Frame(export_frame, bg=UITheme.ACCENT_BLUE)
        buttons_frame.pack(pady=(0, 15))
        
        # Export complete report button
        complete_export_btn = tk.Button(
            buttons_frame,
            text="📋 Export Complete Report",
            font=UITheme.get_font_config("button"),
            command=lambda: self._export_complete_report(recon_engine),
            **UITheme.get_button_style("primary"),
            width=20
        )
        complete_export_btn.pack(side="left", padx=10)
        
        # Export individual sheets button
        individual_export_btn = tk.Button(
            buttons_frame,
            text="📄 Export Individual Sheets",
            font=UITheme.get_font_config("button"),
            command=lambda: self._export_individual_sheets(recon_engine),
            **UITheme.get_button_style("secondary"),
            width=20
        )
        individual_export_btn.pack(side="left", padx=10)
        
        # Create template button
        template_btn = tk.Button(
            buttons_frame,
            text="📝 Create Template",
            font=UITheme.get_font_config("button"),
            command=lambda: self._create_input_template(),
            **UITheme.get_button_style("accent"),
            width=20
        )
        template_btn.pack(side="left", padx=10)
    
    def _export_complete_report(self, recon_engine):
        """Export complete reconciliation report"""
        try:
            # Ask user for output directory
            output_dir = filedialog.askdirectory(
                title="Select Export Directory",
                initialdir=os.getcwd()
            )
            
            if output_dir:
                # Export the report
                export_path = recon_engine.export_reconciliation_to_excel(
                    output_dir=output_dir
                )
                
                messagebox.showinfo(
                    "Export Successful",
                    f"Complete reconciliation report exported successfully!\n\nFile location:\n{export_path}"
                )
                
        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export complete report:\n{str(e)}"
            )
    
    def _export_individual_sheets(self, recon_engine):
        """Export individual analysis sheets"""
        try:
            # Ask user for output directory
            output_dir = filedialog.askdirectory(
                title="Select Export Directory for Individual Sheets",
                initialdir=os.getcwd()
            )
            
            if output_dir:
                # Export individual sheets
                export_paths = recon_engine.export_individual_sheets(
                    output_dir=output_dir
                )
                
                # Create success message
                success_msg = "Individual sheets exported successfully!\n\nFiles created:\n"
                for sheet_type, path in export_paths.items():
                    filename = os.path.basename(path)
                    success_msg += f"• {sheet_type}: {filename}\n"
                
                success_msg += f"\nLocation: {output_dir}"
                
                messagebox.showinfo("Export Successful", success_msg)
                
        except Exception as e:
            messagebox.showerror(
                "Export Error",
                f"Failed to export individual sheets:\n{str(e)}"
            )
    
    def _create_input_template(self):
        """Create input template files"""
        try:
            from utils.excel_exporter import ExcelExporter
            
            # Ask user for output directory
            output_dir = filedialog.askdirectory(
                title="Select Directory for Template Files",
                initialdir=os.getcwd()
            )
            
            if output_dir:
                exporter = ExcelExporter(output_dir=output_dir)
                
                # Create reconciliation template
                template_path = exporter.create_template_file('reconciliation')
                
                messagebox.showinfo(
                    "Template Created",
                    f"Input template created successfully!\n\nFile location:\n{template_path}"
                )
                
        except Exception as e:
            messagebox.showerror(
                "Template Error",
                f"Failed to create template:\n{str(e)}"
            )


def build_multi_file_ui(root=None):
    """Main function to build the UI (for backward compatibility)"""
    if root is None:
        root = TkinterDnD.Tk()
    
    app = BankReconciliationUI(root)
    return app, root