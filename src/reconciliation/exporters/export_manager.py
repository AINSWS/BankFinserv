"""
Export Manager - Handles all export operations for reconciliation data
"""

import pandas as pd
import sys
import os

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from excel_exporter import ExcelExporter

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
    
    def export_bank_ledger_with_reconciliation(self, bank_processor, reconciliation_data, output_filename: str = None, output_dir: str = None) -> str:
        """
        Export original bank ledger with added Remarks column showing reconciliation status
        
        Args:
            bank_processor: BankLedgerProcessor instance
            reconciliation_data: Reconciliation results dict with 'merged_pivot_data'
            output_filename: Custom filename (optional)
            output_dir: Custom output directory (optional)
            
        Returns:
            str: Path to exported Excel file
        """
        try:
            from datetime import datetime
            
            print("📊 Exporting bank ledger with reconciliation remarks...")
            
            # Get original bank ledger DataFrame
            original_bank_df = bank_processor.bank_ledger_df.copy()
            
            # Remove any unnamed columns
            original_bank_df = original_bank_df.loc[:, ~original_bank_df.columns.str.contains('^Unnamed')]
            
            # Get parsed data with loan IDs
            bank_analysis = bank_processor.extract_bank_ledger_data()
            if bank_analysis['status'] != 'success':
                raise Exception("Could not extract bank ledger data")
            
            parsed_df = bank_analysis['parsed_data']['dataframe'].copy()
            
            # Get reconciliation matches
            matches_df = reconciliation_data.get('merged_pivot_data')
            if matches_df is None or matches_df.empty:
                raise Exception("No reconciliation data available")
            
            # Create mapping from loan_id to reconciliation status and difference
            recon_map = {}
            for _, row in matches_df.iterrows():
                loan_id = row.get('loan_id')
                if loan_id:
                    status = row.get('reconciliation_status', row.get('status', 'Unknown'))
                    difference = row.get('amount_difference', 0)
                    
                    # Create remarks based on status
                    if 'MATCHED' in str(status):
                        if 'Group Payment' in str(status):
                            remarks = f"✓ MATCHED - {status}"
                        elif 'Credit/Debit' in str(status) or 'Phase 3' in str(status):
                            remarks = f"✓ MATCHED - {status}"
                        else:
                            remarks = "✓ MATCHED"
                    elif 'MISMATCH' in str(status):
                        remarks = f"✗ MISMATCH"
                    else:
                        remarks = str(status)
                    
                    recon_map[loan_id] = {
                        'remarks': remarks,
                        'difference': difference
                    }
            
            # Add Difference and Remarks columns to original bank ledger
            difference_col = []
            remarks_col = []
            
            for idx, row in original_bank_df.iterrows():
                # Try to get loan_id from parsed data at same index
                if idx < len(parsed_df):
                    parsed_row = parsed_df.iloc[idx]
                    loan_id = parsed_row.get('loan_id') if parsed_row.get('loan_id_valid', False) else None
                    
                    if loan_id and loan_id in recon_map:
                        difference_col.append(recon_map[loan_id]['difference'])
                        remarks_col.append(recon_map[loan_id]['remarks'])
                    else:
                        difference_col.append("")
                        remarks_col.append("")  # Empty for non-reconciled entries
                else:
                    difference_col.append("")
                    remarks_col.append("")
            
            # Add new columns to DataFrame
            original_bank_df['Difference'] = difference_col
            original_bank_df['Remarks'] = remarks_col
            
            # Prepare filename
            if output_filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_filename = f'Bank_Ledger_with_Remarks_{timestamp}.xlsx'
            
            # Determine output directory
            if output_dir:
                export_dir = output_dir
            else:
                export_dir = self.excel_exporter.output_dir
            
            os.makedirs(export_dir, exist_ok=True)
            output_path = os.path.join(export_dir, output_filename)
            
            # Export to Excel with formatting
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                original_bank_df.to_excel(writer, sheet_name='Bank_Ledger', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Bank_Ledger']
                
                # Define formats
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'bg_color': '#4472C4',
                    'font_color': 'white',
                    'border': 1
                })
                
                matched_format = workbook.add_format({'bg_color': '#C6EFCE'})  # Light green
                unmatched_format = workbook.add_format({'bg_color': '#FFC7CE'})  # Light red
                
                # Write headers
                for col_num, value in enumerate(original_bank_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Add autofilter to headers
                worksheet.autofilter(0, 0, len(original_bank_df), len(original_bank_df.columns) - 1)
                
                # Auto-adjust column widths
                for idx, col in enumerate(original_bank_df.columns):
                    series = original_bank_df[col]
                    max_len = max(
                        series.astype(str).apply(len).max(),
                        len(str(series.name))
                    ) + 2
                    worksheet.set_column(idx, idx, min(max_len, 50))
                
                # Apply conditional formatting to ENTIRE ROW based on Remarks column
                remarks_col_idx = original_bank_df.columns.get_loc('Remarks')
                num_cols = len(original_bank_df.columns)
                
                # Green for matched rows - apply to all columns
                for col_idx in range(num_cols):
                    worksheet.conditional_format(1, col_idx, len(original_bank_df), col_idx, {
                        'type': 'formula',
                        'criteria': f'=ISNUMBER(SEARCH("✓",$' + chr(65 + remarks_col_idx) + '2))',
                        'format': matched_format
                    })
                
                # Red for mismatched rows - apply to all columns
                for col_idx in range(num_cols):
                    worksheet.conditional_format(1, col_idx, len(original_bank_df), col_idx, {
                        'type': 'formula',
                        'criteria': f'=ISNUMBER(SEARCH("✗",$' + chr(65 + remarks_col_idx) + '2))',
                        'format': unmatched_format
                    })
            
            print(f"✅ Bank ledger with remarks exported to: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error exporting bank ledger: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
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