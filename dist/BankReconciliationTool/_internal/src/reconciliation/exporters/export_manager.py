"""
Export Manager - Handles all export operations for reconciliation data
"""

import pandas as pd
import sys
import os

# Add utils directory to path for imports
# Add src directory to path for absolute imports
import sys
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from utils.excel_exporter import ExcelExporter

class ExportManager:
    """
    Handles all export operations for reconciliation data:
    - Complete reconciliation reports
    - Individual sheet exports
    - Template creation
    """
    
    def __init__(self, output_dir: str = None):
        self.excel_exporter = ExcelExporter(output_dir=output_dir)
    
    def export_reconciliation_to_excel(self, reconciliation_data, output_filename: str = None, output_dir: str = None) -> str:
        """
        Export complete reconciliation analysis to Excel format
        
        Args:
            reconciliation_data: Complete reconciliation data
            output_filename (str): Custom filename for the export. Auto-generated if not provided.
            output_dir (str): Custom output directory. Uses exporter default if not provided.
            
        Returns:
            str: Path to the exported Excel file
        """
        print(f"📊 Starting Excel export of reconciliation data...")
        
        # Update exporter output directory if specified
        if output_dir:
            self.excel_exporter.output_dir = output_dir
            os.makedirs(output_dir, exist_ok=True)
        
        # Export to Excel
        export_path = self.excel_exporter.export_reconciliation_report(
            reconciliation_data, 
            output_filename
        )
        
        print(f"✅ Reconciliation data exported successfully!")
        print(f"📁 Export location: {export_path}")
        
        return export_path
    
    def export_enhanced_reconciliation_to_excel(self, reconciliation_result, mismatched_analysis=None, output_filename: str = None, output_dir: str = None) -> str:
        """
        Export enhanced reconciliation results with separate mismatched entries to Excel
        
        Args:
            reconciliation_result: Result from merge_pivot_tables with ±3 tolerance
            mismatched_analysis: Result from extract_mismatched_entries
            output_filename (str): Custom filename for the export. Auto-generated if not provided.
            output_dir (str): Custom output directory. Uses exporter default if not provided.
            
        Returns:
            str: Path to the exported Excel file
        """
        print(f"📊 Starting enhanced Excel export with separate mismatch analysis...")
        
        # Update exporter output directory if specified
        if output_dir:
            self.excel_exporter.output_dir = output_dir
            os.makedirs(output_dir, exist_ok=True)
        
        # Export to Excel using enhanced method
        export_path = self.excel_exporter.export_enhanced_reconciliation_report(
            reconciliation_result, 
            mismatched_analysis,
            output_filename
        )
        
        print(f"✅ Enhanced reconciliation data exported successfully!")
        print(f"📁 Export location: {export_path}")
        print(f"📊 Includes: Complete data + Separate sheets for each mismatch category")
        
        return export_path
    
    def export_individual_sheets(self, bank_analysis, sib_analysis, demand_analysis, merged_data, sheet_types: list = None, output_dir: str = None) -> dict:
        """
        Export individual analysis sheets to separate Excel files
        
        Args:
            bank_analysis: Bank ledger analysis results
            sib_analysis: SIB QR analysis results
            demand_analysis: Demand report analysis results
            merged_data: Merged data results
            sheet_types (list): List of sheet types to export. 
                               Options: ['bank_ledger', 'sib_qr', 'demand_report', 'merged_data']
                               Defaults to all types.
            output_dir (str): Custom output directory.
            
        Returns:
            dict: Dictionary mapping sheet_type -> exported_file_path
        """
        if sheet_types is None:
            sheet_types = ['bank_ledger', 'sib_qr', 'demand_report', 'merged_data']
        
        if output_dir:
            self.excel_exporter.output_dir = output_dir
            os.makedirs(output_dir, exist_ok=True)
        
        export_paths = {}
        
        print(f"📊 Exporting individual sheets: {', '.join(sheet_types)}")
        
        for sheet_type in sheet_types:
            try:
                if sheet_type == 'bank_ledger':
                    if bank_analysis.get('filtered_data') and bank_analysis['filtered_data'].get('dataframe') is not None:
                        filename = f"bank_ledger_analysis.xlsx"
                        path = self.excel_exporter.export_dataframe(
                            bank_analysis['filtered_data']['dataframe'], 
                            filename, 
                            'Bank Ledger Analysis'
                        )
                        export_paths[sheet_type] = path
                
                elif sheet_type == 'sib_qr':
                    if sib_analysis.get('processed_data') and sib_analysis['processed_data'].get('dataframe') is not None:
                        filename = f"sib_qr_analysis.xlsx"
                        path = self.excel_exporter.export_dataframe(
                            sib_analysis['processed_data']['dataframe'], 
                            filename, 
                            'SIB QR Analysis'
                        )
                        export_paths[sheet_type] = path
                
                elif sheet_type == 'demand_report':
                    if demand_analysis.get('processed_data') and demand_analysis['processed_data'].get('dataframe') is not None:
                        filename = f"demand_report_analysis.xlsx"
                        path = self.excel_exporter.export_dataframe(
                            demand_analysis['processed_data']['dataframe'], 
                            filename, 
                            'Demand Report Analysis'
                        )
                        export_paths[sheet_type] = path
                
                elif sheet_type == 'merged_data':
                    if merged_data.get('merged_data') is not None:
                        filename = f"merged_sib_demand_data.xlsx"
                        path = self.excel_exporter.export_dataframe(
                            merged_data['merged_data'], 
                            filename, 
                            'Merged SIB+Demand Data'
                        )
                        export_paths[sheet_type] = path
                
            except Exception as e:
                print(f"⚠️ Failed to export {sheet_type}: {str(e)}")
        
        print(f"✅ Individual sheet exports completed!")
        return export_paths
    
    def create_input_template(self, template_type: str = 'reconciliation', output_dir: str = None) -> str:
        """
        Create input template files
        
        Args:
            template_type (str): Type of template to create
            output_dir (str): Custom output directory
            
        Returns:
            str: Path to created template
        """
        if output_dir:
            self.excel_exporter.output_dir = output_dir
            os.makedirs(output_dir, exist_ok=True)
        
        template_path = self.excel_exporter.create_template_file(template_type)
        
        print(f"✅ Template created: {template_path}")
        return template_path