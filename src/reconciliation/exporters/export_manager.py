"""
Export Manager - Handles all export operations for reconciliation data
"""

import pandas as pd
import sys
import os

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

# Import with fallback for both PyInstaller and normal execution
try:
    from src.utils.excel_exporter import ExcelExporter
except ModuleNotFoundError:
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
            
            # DEBUG: Check if Phase 3 updates are present
            if 'reconciliation_status' in matches_df.columns:
                phase3_count = len(matches_df[matches_df['reconciliation_status'].str.contains('Phase 3', na=False)])
                stage2_count = len(matches_df[matches_df['reconciliation_status'].str.contains('Group Payment', na=False)])
                print(f"   🔍 DEBUG - Reconciliation data check:")
                print(f"      • Total records: {len(matches_df)}")
                print(f"      • Phase 3 matches: {phase3_count}")
                print(f"      • Stage 2 matches: {stage2_count}")
                # Show actual status values for debugging
                unique_statuses = matches_df['reconciliation_status'].unique()
                print(f"      • Unique statuses found: {list(unique_statuses)[:10]}")  # Show first 10
            
            # CRITICAL FIX: Use direct "Loan Id" column from bank ledger instead of index matching
            # Find the loan_id column in original bank ledger
            loan_id_col = None
            for col in original_bank_df.columns:
                if 'loan' in col.lower() and 'id' in col.lower():
                    loan_id_col = col
                    print(f"   ✓ Found direct Loan ID column: '{loan_id_col}'")
                    break
            
            # Create sets of matched and mismatched loan IDs from reconciliation data
            matched_loan_ids = set()
            mismatched_loan_ids = set()
            recon_map = {}  # loan_id → {status, difference}
            
            for _, row in matches_df.iterrows():
                # Convert to string and remove .0 if it's a float
                loan_id_raw = row.get('loan_id', '')
                if pd.notna(loan_id_raw):
                    loan_id = str(loan_id_raw).strip()
                    # Remove .0 suffix if present (e.g., '223345.0' → '223345')
                    if loan_id.endswith('.0'):
                        loan_id = loan_id[:-2]
                else:
                    loan_id = ''
                    
                if loan_id:
                    status = row.get('reconciliation_status', row.get('status', 'Unknown'))
                    difference = row.get('amount_difference', 0)
                    
                    # Categorize loan IDs
                    if 'MATCHED' in str(status):
                        matched_loan_ids.add(loan_id)
                        if 'Group Payment' in str(status):
                            remarks = f"✓ {status}"
                        elif 'Phase 3' in str(status) or 'Credit/Debit' in str(status):
                            remarks = f"✓ {status}"
                        else:
                            remarks = "✓ MATCHED"
                    elif 'MISMATCH' in str(status):
                        mismatched_loan_ids.add(loan_id)
                        remarks = f"✗ MISMATCH (Diff: {difference:.2f})"
                    else:
                        remarks = str(status)
                    
                    recon_map[loan_id] = {
                        'remarks': remarks,
                        'difference': difference
                    }
            
            print(f"   • Matched loan IDs: {len(matched_loan_ids)}")
            print(f"   • Mismatched loan IDs: {len(mismatched_loan_ids)}")
            
            # Add Remarks column to original bank ledger using direct loan_id column
            remarks_col = []
            remarks_added = 0
            
            if loan_id_col:
                # DEBUG: Check first few loan IDs from bank ledger
                sample_bank_ids = original_bank_df[loan_id_col].head(3).tolist()
                sample_recon_ids = list(recon_map.keys())[:3]
                print(f"   🔍 DEBUG - Loan ID matching:")
                print(f"      • Sample bank ledger IDs: {sample_bank_ids}")
                print(f"      • Sample reconciliation IDs: {sample_recon_ids}")
                
                # Use direct loan_id column from bank ledger
                for idx, row in original_bank_df.iterrows():
                    loan_id_raw = row.get(loan_id_col, '')
                    if pd.notna(loan_id_raw):
                        loan_id_value = str(loan_id_raw).strip()
                        # Remove .0 suffix if present
                        if loan_id_value.endswith('.0'):
                            loan_id_value = loan_id_value[:-2]
                    else:
                        loan_id_value = ''
                    
                    if loan_id_value and loan_id_value in recon_map:
                        remarks_col.append(recon_map[loan_id_value]['remarks'])
                        remarks_added += 1
                    else:
                        remarks_col.append("")  # Empty for non-reconciled entries
                
                print(f"   • Remarks added to {remarks_added}/{len(original_bank_df)} rows")
            else:
                # Fallback: Try to use parsed data (old method)
                print(f"   ⚠️ No direct Loan ID column found, using parsed data fallback")
                for idx, row in original_bank_df.iterrows():
                    if idx < len(parsed_df):
                        parsed_row = parsed_df.iloc[idx]
                        loan_id = parsed_row.get('loan_id') if parsed_row.get('loan_id_valid', False) else None
                        
                        if loan_id and loan_id in recon_map:
                            remarks_col.append(recon_map[loan_id]['remarks'])
                        else:
                            remarks_col.append("")
                    else:
                        remarks_col.append("")
            
            # Add Remarks column to DataFrame
            original_bank_df['Remarks'] = remarks_col
            
            # Sort by Loan ID in ascending order (if loan_id_col was found)
            if loan_id_col and loan_id_col in original_bank_df.columns:
                print(f"   📊 Sorting bank ledger by '{loan_id_col}' in ascending order...")
                # Convert to numeric for proper sorting (handles both numeric and string IDs)
                original_bank_df[loan_id_col] = pd.to_numeric(original_bank_df[loan_id_col], errors='coerce')
                original_bank_df = original_bank_df.sort_values(by=loan_id_col, ascending=True, na_position='last')
                original_bank_df = original_bank_df.reset_index(drop=True)
            
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
            
            # Export to Excel with formatting and include Matched / Mismatched sheets
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                # Sheet 1: Bank Ledger (original with Difference & Remarks)
                original_bank_df.to_excel(writer, sheet_name='Bank_Ledger', index=False)

                workbook = writer.book
                ledger_ws = writer.sheets['Bank_Ledger']

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

                # Write headers and autofilter for ledger
                for col_num, value in enumerate(original_bank_df.columns.values):
                    ledger_ws.write(0, col_num, value, header_format)

                ledger_ws.autofilter(0, 0, len(original_bank_df), len(original_bank_df.columns) - 1)

                # Auto-adjust column widths for ledger
                for idx, col in enumerate(original_bank_df.columns):
                    series = original_bank_df[col]
                    try:
                        max_len = max(
                            series.astype(str).apply(len).max(),
                            len(str(series.name))
                        ) + 2
                    except Exception:
                        max_len = min(20, len(str(series.name)) + 2)
                    ledger_ws.set_column(idx, idx, min(max_len, 50))

                # Apply conditional formatting to ENTIRE ROW based on Remarks column if present
                if 'Remarks' in original_bank_df.columns:
                    remarks_col_idx = original_bank_df.columns.get_loc('Remarks')
                    num_cols = len(original_bank_df.columns)

                    # Green for matched rows - apply to all columns
                    for col_idx in range(num_cols):
                        ledger_ws.conditional_format(1, col_idx, len(original_bank_df), col_idx, {
                            'type': 'formula',
                            'criteria': f'=ISNUMBER(SEARCH("✓",$' + chr(65 + remarks_col_idx) + '2))',
                            'format': matched_format
                        })

                    # Red for mismatched rows - apply to all columns
                    for col_idx in range(num_cols):
                        ledger_ws.conditional_format(1, col_idx, len(original_bank_df), col_idx, {
                            'type': 'formula',
                            'criteria': f'=ISNUMBER(SEARCH("✗",$' + chr(65 + remarks_col_idx) + '2))',
                            'format': unmatched_format
                        })

                # Prepare Matched and Mismatched sheets from reconciliation data if available
                matches_df = matches_df if 'matches_df' in locals() else reconciliation_data.get('merged_pivot_data')
                if matches_df is None or matches_df.empty:
                    # try alternate key names
                    matches_df = reconciliation_data.get('merged_data') or reconciliation_data.get('merged')

                try:
                    if matches_df is not None and not matches_df.empty:
                        # Determine status column name
                        status_col = None
                        for candidate in ['reconciliation_status', 'status', 'recon_status']:
                            if candidate in matches_df.columns:
                                status_col = candidate
                                break

                        # Normalize status values to string upper for filtering
                        if status_col is not None:
                            status_series = matches_df[status_col].fillna('').astype(str).str.upper()
                        else:
                            status_series = pd.Series([''] * len(matches_df))

                        matched_df = matches_df[status_series.str.contains('MATCHED', na=False)].copy()
                        mismatched_df = matches_df[status_series.str.contains('MISMATCH', na=False)].copy()

                        # Define the required columns for matched/mismatched sheets
                        required_cols = ['loan_id', 'customer_name', 'group_id', 'branch', 'system_entry', 'qr_collection', 'difference', 'status']
                        
                        # Helper function to prepare sheet with required columns
                        def prepare_sheet_data(df, status_col):
                            if df.empty:
                                return pd.DataFrame(columns=required_cols)
                            
                            result_df = pd.DataFrame()
                            
                            # Map columns - try different possible names
                            col_mapping = {
                                'loan_id': ['loan_id', 'loanid', 'id'],
                                'customer_name': ['customer_name', 'name', 'member_name'],
                                'group_id': ['group_id', 'group', 'group_name'],
                                'branch': ['branch', 'branch_name'],
                                'system_entry': ['system_amount', 'system_entry', 'bank_amount'],
                                'qr_collection': ['qr_amount', 'qr_collection', 'collection'],
                                'difference': ['amount_difference', 'difference', 'diff'],
                                'status': [status_col] if status_col else ['reconciliation_status', 'status']
                            }
                            
                            for target_col, possible_names in col_mapping.items():
                                found = False
                                for col_name in possible_names:
                                    if col_name in df.columns:
                                        result_df[target_col] = df[col_name]
                                        found = True
                                        break
                                if not found:
                                    result_df[target_col] = ''
                            
                            return result_df

                        # Prepare matched and mismatched data
                        matched_export_df = prepare_sheet_data(matched_df, status_col)
                        mismatched_export_df = prepare_sheet_data(mismatched_df, status_col)

                        # Sheet 2: Matched (with green background)
                        if not matched_export_df.empty:
                            matched_export_df.to_excel(writer, sheet_name='Matched', index=False)
                            matched_ws = writer.sheets['Matched']
                            
                            # Write headers
                            for col_num, value in enumerate(matched_export_df.columns.values):
                                matched_ws.write(0, col_num, value, header_format)
                            
                            # Apply green background to all data cells
                            for row_num in range(1, len(matched_export_df) + 1):
                                for col_num in range(len(matched_export_df.columns)):
                                    matched_ws.write(row_num, col_num, matched_export_df.iloc[row_num - 1, col_num], matched_format)
                            
                            # Add autofilter
                            matched_ws.autofilter(0, 0, len(matched_export_df), len(matched_export_df.columns) - 1)
                            
                            # Auto-adjust column widths
                            for idx, col in enumerate(matched_export_df.columns):
                                try:
                                    max_len = max(matched_export_df[col].astype(str).apply(len).max(), len(str(col))) + 2
                                except Exception:
                                    max_len = min(20, len(str(col)) + 2)
                                matched_ws.set_column(idx, idx, min(max_len, 50))
                        else:
                            # Empty matched sheet
                            empty_df = pd.DataFrame({'Note': ['No matched records available']})
                            empty_df.to_excel(writer, sheet_name='Matched', index=False)

                        # Sheet 3: Mismatched (with red background)
                        if not mismatched_export_df.empty:
                            mismatched_export_df.to_excel(writer, sheet_name='Mismatched', index=False)
                            mismatched_ws = writer.sheets['Mismatched']
                            
                            # Write headers
                            for col_num, value in enumerate(mismatched_export_df.columns.values):
                                mismatched_ws.write(0, col_num, value, header_format)
                            
                            # Apply red background to all data cells
                            for row_num in range(1, len(mismatched_export_df) + 1):
                                for col_num in range(len(mismatched_export_df.columns)):
                                    mismatched_ws.write(row_num, col_num, mismatched_export_df.iloc[row_num - 1, col_num], unmatched_format)
                            
                            # Add autofilter
                            mismatched_ws.autofilter(0, 0, len(mismatched_export_df), len(mismatched_export_df.columns) - 1)
                            
                            # Auto-adjust column widths
                            for idx, col in enumerate(mismatched_export_df.columns):
                                try:
                                    max_len = max(mismatched_export_df[col].astype(str).apply(len).max(), len(str(col))) + 2
                                except Exception:
                                    max_len = min(20, len(str(col)) + 2)
                                mismatched_ws.set_column(idx, idx, min(max_len, 50))
                        else:
                            # Empty mismatched sheet
                            empty_df = pd.DataFrame({'Note': ['No mismatched records available']})
                            empty_df.to_excel(writer, sheet_name='Mismatched', index=False)

                except Exception as e:
                    print(f"⚠️ Could not generate matched/mismatched sheets: {e}")
                    import traceback
                    traceback.print_exc()
            
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