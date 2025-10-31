"""
File handling utilities for Excel and CSV files
"""
import pandas as pd
import os
from tkinter import messagebox

class FileHandler:
    """Handles file loading and validation"""
    
    SUPPORTED_EXTENSIONS = ('.xlsx', '.xls', '.csv')
    
    @staticmethod
    def find_table_start_row(file_path):
        """
        Find the row where the actual data table starts by looking for 'S.no' or similar column.
        This skips company headers, logos, etc. that appear above the table.
        
        Returns:
            int: Row number (0-indexed) where table starts, or 0 if not found
        """
        try:
            # Read first 20 rows to search for the header
            if file_path.lower().endswith('.csv'):
                df_preview = pd.read_csv(file_path, nrows=20, header=None, encoding='utf-8', low_memory=False)
            else:
                df_preview = pd.read_excel(file_path, nrows=20, header=None)
            
            # Search for 'S.no' or variations in each row
            for idx, row in df_preview.iterrows():
                # Convert row to string and check for S.no patterns
                row_str = ' '.join([str(cell).strip().lower() for cell in row if pd.notna(cell)])
                
                # Check for common variations of S.no
                if any(pattern in row_str for pattern in ['s.no', 's no', 'sno', 'sr.no', 'sr no', 'serial']):
                    print(f"   ✓ Found table header at row {idx + 1}, skipping {idx} header rows")
                    return idx
            
            # If not found, assume table starts at row 0
            print("   ℹ️ No 'S.no' column found, assuming table starts at row 1")
            return 0
            
        except Exception as e:
            print(f"   ⚠️ Error detecting table start: {str(e)}, assuming row 1")
            return 0
    
    @staticmethod
    def validate_file(file_path):
        """Validate file exists and has supported extension"""
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return False, "File does not exist or is not accessible"
        
        if not file_path.lower().endswith(FileHandler.SUPPORTED_EXTENSIONS):
            ext = os.path.splitext(file_path)[1].lower()
            return False, f"Unsupported file type: {ext}. Please use Excel (.xlsx, .xls) or CSV (.csv) files."
        
        return True, "Valid file"
    
    @staticmethod
    def load_file(file_path):
        """Load Excel or CSV file into pandas DataFrame"""
        try:
            df = None
            
            # Detect where the actual table starts (skip company headers, etc.)
            skip_rows = FileHandler.find_table_start_row(file_path)
            
            if file_path.lower().endswith('.csv'):
                # Enhanced CSV loading with multiple encoding attempts
                try:
                    df = pd.read_csv(file_path, skiprows=skip_rows, encoding='utf-8', low_memory=False)
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, skiprows=skip_rows, encoding='latin-1', low_memory=False)
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, skiprows=skip_rows, encoding='cp1252', low_memory=False)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                # Excel file handling with header detection
                df = pd.read_excel(file_path, skiprows=skip_rows)
            
            if df is not None and not df.empty:
                return df, None
            else:
                return None, "File appears to be empty or could not be read properly"
                
        except pd.errors.EmptyDataError:
            return None, "The file is empty or contains no data"
        except pd.errors.ParserError as e:
            return None, f"Could not parse the file. Please check the file format.\n\nDetails: {str(e)}"
        except FileNotFoundError:
            return None, "The file could not be found"
        except PermissionError:
            return None, "Cannot access the file. Please check if the file is open in another application"
        except Exception as e:
            return None, f"Could not load file: {str(e)}\n\nPlease ensure the file is a valid Excel or CSV file"
    
    @staticmethod
    def get_file_info(file_path, df):
        """Get file information for display"""
        file_size = os.path.getsize(file_path)
        size_str = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
        file_type = "CSV" if file_path.lower().endswith('.csv') else "Excel"
        
        return {
            'filename': os.path.basename(file_path),
            'size': size_str,
            'type': file_type,
            'rows': len(df),
            'columns': len(df.columns),
            'path': file_path
        }
    
    @staticmethod
    def get_file_dialog_config():
        """Get file dialog configuration"""
        return {
            'filetypes': [
                ("Excel & CSV Files", "*.xlsx *.xls *.csv"),
                ("Excel Files", "*.xlsx *.xls"),
                ("CSV Files", "*.csv"),
                ("All Files", "*.*")
            ]
        }