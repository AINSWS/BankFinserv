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
            
            if file_path.lower().endswith('.csv'):
                # Enhanced CSV loading with multiple encoding attempts
                try:
                    df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file_path, encoding='latin-1', low_memory=False)
                    except UnicodeDecodeError:
                        df = pd.read_csv(file_path, encoding='cp1252', low_memory=False)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                # Excel file handling
                df = pd.read_excel(file_path)
            
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