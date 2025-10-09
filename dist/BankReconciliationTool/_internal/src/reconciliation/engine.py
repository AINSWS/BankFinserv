"""
Bank Reconciliation Logic and Operations
"""
import pandas as pd
import sys
import os

# Add src directory to path for absolute imports
import sys
import os
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from utils.dataframe_splitter import DataFrameSplitter
from utils.dataframe_merger import DataFrameMerger
from utils.dataframe_groupby import DataFrameGroupBy
from utils.excel_exporter import ExcelExporter

class ReconciliationEngine:
    """Handles bank reconciliation operations"""
    
    def __init__(self, bank_ledger_df, sib_qr_df, demand_report_df):
        self.bank_ledger_df = bank_ledger_df
        self.sib_qr_df = sib_qr_df
        self.demand_report_df = demand_report_df
        self.excel_exporter = ExcelExporter()
        self.groupby_processor = DataFrameGroupBy()
        
    def detect_columns(self, df, column_types):
        """Detect columns based on common naming patterns"""
        detected = {}
        
        for col in df.columns:
            col_lower = col.lower()
            
            for col_type, keywords in column_types.items():
                if any(keyword in col_lower for keyword in keywords):
                    if col_type not in detected:
                        detected[col_type] = []
                    detected[col_type].append(col)
        
        return detected
    
    def extract_bank_ledger_data(self):
        """
        Process bank ledger with specific parsing logic:
        1. Extract narration and rate columns from sheet 1
        2. Split narration by '/' delimiter
        3. Extract: description, loan_id, customer_name, group_name, branch
        4. Filter loan_id column to keep only actual loan IDs (remove branch names)
        """
        column_patterns = {
            'narration': ['narration', 'description', 'particulars', 'details', 'remark'],
            'amount': ['amount', 'rate', 'value', 'debit', 'credit', 'dr', 'cr'],
            'date': ['date', 'transaction_date', 'value_date', 'posting_date'],
            'reference': ['reference', 'ref', 'transaction_id', 'txn_id', 'cheque_no']
        }
        
        detected_columns = self.detect_columns(self.bank_ledger_df, column_patterns)
        
        result = {
            'detected_columns': detected_columns,
            'filtered_data': None,
            'parsed_data': None,
            'status': 'success' if detected_columns.get('narration') and detected_columns.get('amount') else 'partial'
        }
        
        # Process if key columns are found
        if detected_columns.get('narration') and detected_columns.get('amount'):
            narration_col = detected_columns['narration'][0]
            amount_col = detected_columns['amount'][0]
            
            # Step 1: Create separate DataFrame with narration and rate
            columns_to_extract = [narration_col, amount_col]
            if detected_columns.get('date'):
                columns_to_extract.append(detected_columns['date'][0])
            if detected_columns.get('reference'):
                columns_to_extract.append(detected_columns['reference'][0])
            
            filtered_df = self.bank_ledger_df[columns_to_extract].copy()
            filtered_df = filtered_df.dropna(subset=[narration_col, amount_col])
            
            # Step 2-4: Parse narration and filter loan IDs
            parsed_df = self._parse_narration_field(filtered_df, narration_col, amount_col)
            
            result['filtered_data'] = {
                'dataframe': filtered_df,
                'narration_column': narration_col,
                'amount_column': amount_col,
                'date_column': detected_columns.get('date', [None])[0],
                'reference_column': detected_columns.get('reference', [None])[0],
                'total_rows': len(filtered_df),
                'sample_data': filtered_df.head(3).to_dict('records')
            }
            
            result['parsed_data'] = {
                'dataframe': parsed_df,
                'total_rows': len(parsed_df),
                'valid_loan_entries': len(parsed_df[parsed_df['loan_id_valid'] == True]) if 'loan_id_valid' in parsed_df.columns else 0,
                'filtered_out_entries': len(parsed_df[parsed_df['loan_id_valid'] == False]) if 'loan_id_valid' in parsed_df.columns else 0,
                'sample_valid_loans': parsed_df[parsed_df['loan_id_valid'] == True].head(3).to_dict('records') if 'loan_id_valid' in parsed_df.columns else [],
                'sample_filtered_out': parsed_df[parsed_df['loan_id_valid'] == False].head(2).to_dict('records') if 'loan_id_valid' in parsed_df.columns else []
            }
        
        return result
    
    def analyze_sib_qr_report(self):
        """
        Analyze SIB QR Report (Sheet 2) structure:
        Expected columns: tranDate, payerVpa, payerName, rrn, referenceID, amount
        referenceID refers to loan ID for matching with demand report
        """
        column_patterns = {
            'tran_date': ['trandate', 'tran_date', 'transaction_date', 'date'],
            'payer_vpa': ['payervpa', 'payer_vpa', 'vpa', 'upi_id'],
            'payer_name': ['payername', 'payer_name', 'name', 'customer_name'],
            'rrn': ['rrn', 'reference_retrieval_number', 'txn_ref'],
            'reference_id': ['referenceid', 'reference_id', 'refrence_id', 'refrence_number', 'loan_id', 'lanid'],
            'amount': ['amount', 'value', 'transaction_amount', 'txn_amount']
        }
        
        detected_columns = self.detect_columns(self.sib_qr_df, column_patterns)
        
        result = {
            'detected_columns': detected_columns,
            'total_rows': len(self.sib_qr_df),
            'total_columns': len(self.sib_qr_df.columns),
            'sample_data': self.sib_qr_df.head(5).to_dict('records') if len(self.sib_qr_df) > 0 else [],
            'processed_data': None,
            'status': 'success' if detected_columns.get('reference_id') and detected_columns.get('amount') else 'partial'
        }
        
        # Process SIB QR data if key columns found
        if detected_columns.get('reference_id') and detected_columns.get('amount'):
            processed_df = self._process_sib_qr_data(detected_columns)
            
            result['processed_data'] = {
                'dataframe': processed_df,
                'total_rows': len(processed_df),
                'reference_id_column': detected_columns['reference_id'][0],
                'amount_column': detected_columns['amount'][0],
                'sample_data': processed_df.head(5).to_dict('records')
            }
        
        return result
    
    def analyze_demand_report(self):
        """
        Analyze Demand Report (Sheet 3) structure:
        Extract: Mlai_id/loanID, MBRI_Name/branchname, MGI_Name/group name, MMI_Name/member name
        Create separate DataFrame for merging with SIB QR report
        """
        column_patterns = {
            'loan_id': ['mmi id1', 'mmi_id1', 'mmid1', 'mlai_id', 'loanid', 'loan_id', 'account_no', 'loan_no'],
            'branch_name': ['branch', 'mbri_name', 'branchname', 'branch_name', 'office'],
            'group_name': ['group no', 'group_no', 'groupno', 'mgi_name', 'group_name', 'group', 'group_id'],
            'member_name': ['mvi name', 'mvi_name', 'mviname', 'mmi_name', 'member_name', 'mamber_name', 'customer_name', 'name'],
            'amount': ['textbox40', 'amount', 'outstanding', 'balance', 'demand_amount'],
            'due_date': ['due_date', 'maturity_date', 'payment_date']
        }
        
        detected_columns = self.detect_columns(self.demand_report_df, column_patterns)
        
        result = {
            'detected_columns': detected_columns,
            'total_rows': len(self.demand_report_df),
            'total_columns': len(self.demand_report_df.columns),
            'sample_data': self.demand_report_df.head(5).to_dict('records') if len(self.demand_report_df) > 0 else [],
            'extracted_data': None,
            'status': 'success' if detected_columns.get('loan_id') else 'partial'
        }
        
        # Extract key columns for merging
        if detected_columns.get('loan_id'):
            extracted_df = self._extract_demand_report_data(detected_columns)
            
            result['extracted_data'] = {
                'dataframe': extracted_df,
                'total_rows': len(extracted_df),
                'loan_id_column': detected_columns['loan_id'][0],
                'sample_data': extracted_df.head(5).to_dict('records')
            }
        
        return result
    
    def find_matching_transactions(self):
        """Find matching transactions between files"""
        bank_analysis = self.extract_bank_ledger_data()
        sib_analysis = self.analyze_sib_qr_report()
        demand_analysis = self.analyze_demand_report()
        
        matches = {
            'bank_sib_matches': [],
            'bank_demand_matches': [],
            'sib_demand_matches': [],
            'unmatched_bank': [],
            'unmatched_sib': [],
            'unmatched_demand': []
        }
        
        # Simple amount-based matching (can be enhanced)
        if (bank_analysis['filtered_data'] and 
            sib_analysis['detected_columns'].get('amount') and
            demand_analysis['detected_columns'].get('amount')):
            
            bank_df = bank_analysis['filtered_data']['dataframe']
            bank_amounts = bank_df[bank_analysis['filtered_data']['amount_column']].astype(float, errors='ignore')
            
            sib_amount_col = sib_analysis['detected_columns']['amount'][0]
            sib_amounts = self.sib_qr_df[sib_amount_col].astype(float, errors='ignore')
            
            demand_amount_col = demand_analysis['detected_columns']['amount'][0]
            demand_amounts = self.demand_report_df[demand_amount_col].astype(float, errors='ignore')
            
            # Find matches (simplified logic - can be enhanced with date, reference matching)
            for i, bank_amount in enumerate(bank_amounts):
                if pd.notna(bank_amount):
                    # Check SIB matches
                    sib_matches = self.sib_qr_df[abs(sib_amounts - bank_amount) < 0.01]
                    if len(sib_matches) > 0:
                        matches['bank_sib_matches'].append({
                            'bank_row': i,
                            'bank_amount': bank_amount,
                            'sib_matches': len(sib_matches)
                        })
                    
                    # Check Demand matches
                    demand_matches = self.demand_report_df[abs(demand_amounts - bank_amount) < 0.01]
                    if len(demand_matches) > 0:
                        matches['bank_demand_matches'].append({
                            'bank_row': i,
                            'bank_amount': bank_amount,
                            'demand_matches': len(demand_matches)
                        })
        
        return matches
    
    def _parse_narration_field(self, df, narration_col, amount_col):
        """
        Parse narration field using dynamic DataFrameSplitter utility
        Expected format: description/loan_id/customer_name/group_name/branch
        
        Uses DataFrameSplitter for flexible column splitting with advanced filtering
        """
        try:
            # Initialize the dynamic splitter
            splitter = DataFrameSplitter()
            
            # Use the process_narration_field method for comprehensive processing
            result = splitter.process_narration_field(
                df=df,
                narration_column=narration_col,
                delimiter='/',
                expected_structure=['description', 'loan_id', 'customer_name', 'group_name', 'branch'],
                apply_loan_filter=True
            )
            
            if 'dataframe' in result:
                processed_df = result['dataframe']
                
                # Add debugging information from the splitter
                summary = result.get('summary', {})
                print(f"   📊 Narration Processing Stats (DataFrameSplitter):")
                print(f"      • Total rows processed: {summary.get('total_rows', len(df))}")
                print(f"      • Valid loan IDs found: {summary.get('valid_loan_count', 0)}")
                print(f"      • Invalid loan entries: {summary.get('invalid_loan_count', 0)}")
                print(f"      • Success rate: {summary.get('loan_success_rate', 0):.1f}%")
                
                # Convert to match legacy format for compatibility
                if 'loan_id_valid' in processed_df.columns:
                    processed_df['loan_id_original'] = processed_df.get('loan_id', '')
                    processed_df['filter_reason'] = processed_df.get('loan_filter_reason', 'Valid')
                
                return processed_df
            else:
                print(f"   ⚠️ DataFrameSplitter failed: {result['error_message']}")
                print(f"   🔄 Falling back to legacy parsing method...")
                return self._legacy_parse_narration_field(df, narration_col, amount_col)
                
        except Exception as e:
            print(f"   ❌ Error using DataFrameSplitter: {str(e)}")
            print(f"   🔄 Falling back to legacy parsing method...")
            return self._legacy_parse_narration_field(df, narration_col, amount_col)
    
    def _legacy_parse_narration_field(self, df, narration_col, amount_col):
        """
        Legacy narration parsing method (fallback)
        Parse narration field by splitting on '/' delimiter
        Expected format: description/loan_id/customer_name/group_name/branch
        """
        parsed_df = df.copy()
        
        # Split narration by '/' delimiter
        narration_parts = parsed_df[narration_col].astype(str).str.split('/', expand=True)
        
        # Assign column names based on expected structure
        column_names = ['description', 'loan_id', 'customer_name', 'group_name', 'branch']
        
        for i, col_name in enumerate(column_names):
            if i < narration_parts.shape[1]:
                parsed_df[col_name] = narration_parts[i].str.strip()
            else:
                parsed_df[col_name] = None
        
        # Process loan_id column to filter valid loan IDs
        if 'loan_id' in parsed_df.columns:
            parsed_df = self._filter_loan_ids(parsed_df)
        
        return parsed_df
    
    def dynamic_column_split(self, df, column_name, delimiter='/', expected_columns=None, filter_options=None):
        """
        Use DataFrameSplitter for dynamic column splitting with custom parameters
        
        Args:
            df: DataFrame to process
            column_name: Column to split
            delimiter: Split delimiter (default: '/')
            expected_columns: List of expected column names after split
            filter_options: Dict with filtering options
            
        Returns:
            Dict with processing results
        """
        try:
            splitter = DataFrameSplitter()
            
            # Use smart column split for flexible processing
            result = splitter.smart_column_split(
                df=df,
                column_name=column_name,
                delimiter=delimiter,
                expected_parts=expected_columns or [],
                auto_detect_structure=True
            )
            
            if 'dataframe' in result:
                split_df = result['dataframe']
                
                # Apply custom filtering if provided
                if filter_options:
                    for filter_column, filter_params in filter_options.items():
                        if filter_column in split_df.columns:
                            filter_result = splitter.filter_split_data(
                                split_df, 
                                filter_column, 
                                **filter_params
                            )
                            if filter_result['status'] == 'success':
                                split_df = filter_result['filtered_df']
                
                return {
                    'status': 'success',
                    'processed_df': split_df,
                    'split_stats': result.get('summary', {}),
                    'original_method': 'DataFrameSplitter'
                }
            else:
                return {
                    'status': 'error',
                    'error_message': result.get('error_message', 'DataFrameSplitter processing failed'),
                    'original_method': 'DataFrameSplitter'
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f"Dynamic column split failed: {str(e)}",
                'original_method': 'DataFrameSplitter'
            }
    
    def _filter_loan_ids(self, df):
        """
        Filter loan_id column to keep only actual loan IDs and remove branch names
        Loan IDs are typically numeric or alphanumeric patterns
        Branch names are typically text-only
        """
        import re
        
        df = df.copy()
        
        def is_valid_loan_id(value):
            if pd.isna(value) or value is None:
                return False
            
            value_str = str(value).strip()
            
            # Skip empty values
            if not value_str:
                return False
            
            # Loan ID validation patterns:
            # 1. Contains numbers (loan IDs usually have numeric components)
            # 2. Not purely alphabetic (branch names are usually text-only)
            # 3. Minimum length requirements
            # 4. Exclude common branch indicators
            
            has_numbers = bool(re.search(r'\d', value_str))
            is_purely_alpha = value_str.isalpha()
            min_length = len(value_str) >= 3
            
            # Common branch name patterns to exclude
            branch_indicators = ['branch', 'office', 'head', 'main', 'sub', 'regional']
            is_branch_name = any(indicator.lower() in value_str.lower() for indicator in branch_indicators)
            
            # Valid loan ID criteria
            return has_numbers and not is_purely_alpha and min_length and not is_branch_name
        
        # Apply loan ID validation
        df['loan_id_valid'] = df['loan_id'].apply(is_valid_loan_id)
        df['loan_id_original'] = df['loan_id'].copy()  # Keep original for reference
        
        # Add reason for filtering (for debugging)
        def get_filter_reason(value):
            if pd.isna(value) or not str(value).strip():
                return "Empty/Null"
            value_str = str(value).strip()
            if not re.search(r'\d', value_str):
                return "No numbers"
            if value_str.isalpha():
                return "Only alphabetic"
            if len(value_str) < 3:
                return "Too short"
            branch_indicators = ['branch', 'office', 'head', 'main', 'sub', 'regional']
            if any(indicator.lower() in value_str.lower() for indicator in branch_indicators):
                return "Branch indicator"
            return "Valid"
        
        df['filter_reason'] = df['loan_id'].apply(get_filter_reason)
        
        return df
    
    def _process_sib_qr_data(self, detected_columns):
        """
        Process SIB QR Report data for merging
        Extract key columns: tranDate, payerVpa, payerName, rrn, referenceID, amount
        """
        sib_df = self.sib_qr_df.copy()
        
        # Build column mapping
        column_mapping = {}
        for key, column_list in detected_columns.items():
            if column_list:
                column_mapping[key] = column_list[0]
        
        # Select and rename columns
        columns_to_extract = []
        renamed_columns = {}
        
        for key, original_col in column_mapping.items():
            if original_col in sib_df.columns:
                columns_to_extract.append(original_col)
                renamed_columns[original_col] = key
        
        if columns_to_extract:
            processed_df = sib_df[columns_to_extract].copy()
            processed_df = processed_df.rename(columns=renamed_columns)
            
            # Clean reference_id column for matching
            if 'reference_id' in processed_df.columns:
                processed_df['reference_id_clean'] = processed_df['reference_id'].astype(str).str.strip()
                processed_df['reference_id_clean'] = processed_df['reference_id_clean'].str.upper()
            
            return processed_df
        
        return pd.DataFrame()
    
    def _extract_demand_report_data(self, detected_columns):
        """
        Extract key data from Demand Report for merging:
        Mlai_id/loanID, MBRI_Name/branchname, MGI_Name/group name, MMI_Name/member name
        """
        demand_df = self.demand_report_df.copy()
        
        # Build column mapping
        column_mapping = {}
        for key, column_list in detected_columns.items():
            if column_list:
                column_mapping[key] = column_list[0]
        
        # Select key columns for merging
        key_columns = ['loan_id', 'branch_name', 'group_name', 'member_name']
        columns_to_extract = []
        renamed_columns = {}
        
        for key in key_columns:
            if key in column_mapping and column_mapping[key] in demand_df.columns:
                original_col = column_mapping[key]
                columns_to_extract.append(original_col)
                renamed_columns[original_col] = key
        
        if columns_to_extract:
            extracted_df = demand_df[columns_to_extract].copy()
            extracted_df = extracted_df.rename(columns=renamed_columns)
            
            # Clean loan_id for matching
            if 'loan_id' in extracted_df.columns:
                extracted_df['loan_id_clean'] = extracted_df['loan_id'].astype(str).str.strip()
                extracted_df['loan_id_clean'] = extracted_df['loan_id_clean'].str.upper()
                
            # Remove duplicates based on loan_id
            if 'loan_id' in extracted_df.columns:
                extracted_df = extracted_df.drop_duplicates(subset=['loan_id'], keep='first')
            
            return extracted_df
        
        return pd.DataFrame()
    
    def merge_sib_qr_with_demand_report(self):
        """
        Merge SIB QR Report (Sheet 2) with Demand Report (Sheet 3) using DataFrameMerger
        Uses dynamic merging with LEFT JOIN to preserve all SIB QR transactions
        """
        print(f"🔗 Starting SIB QR + Demand Report merge using DataFrameMerger...")
        
        # Get processed data from both reports
        sib_analysis = self.analyze_sib_qr_report()
        demand_analysis = self.analyze_demand_report()
        
        result = {
            'status': 'failed',
            'merged_data': None,
            'merge_stats': {
                'sib_records': 0,
                'demand_records': 0,
                'matched_records': 0,
                'unmatched_sib_records': 0,
                'match_rate': 0.0
            },
            'debug_info': {
                'sib_data_available': False,
                'demand_data_available': False,
                'merge_columns_present': False,
                'error_message': None,
                'merger_method': 'DataFrameMerger'
            }
        }
        
        try:
            # Check if both datasets have required data
            if (sib_analysis.get('processed_data') and 
                demand_analysis.get('extracted_data')):
                
                sib_df = sib_analysis['processed_data']['dataframe'].copy()
                demand_df = demand_analysis['extracted_data']['dataframe'].copy()
                
                result['debug_info']['sib_data_available'] = not sib_df.empty
                result['debug_info']['demand_data_available'] = not demand_df.empty
                
                if not sib_df.empty and not demand_df.empty:
                    # Initialize DataFrameMerger
                    merger = DataFrameMerger(validate_columns=True, case_sensitive=False)
                    
                    # Determine merge columns
                    sib_merge_col = self._get_sib_merge_column(sib_df)
                    demand_merge_col = self._get_demand_merge_column(demand_df)
                    
                    print(f"   • SIB QR merge column: {sib_merge_col}")
                    print(f"   • Demand Report merge column: {demand_merge_col}")
                    
                    result['debug_info']['merge_columns_present'] = (
                        sib_merge_col is not None and demand_merge_col is not None
                    )
                    
                    if sib_merge_col and demand_merge_col:
                        # Perform dynamic merge using LEFT JOIN (preserve all SIB QR records)
                        merge_result = merger.dynamic_merge(
                            left_df=sib_df,              # PRIMARY: SIB QR transactions (preserve all)
                            right_df=demand_df,          # REFERENCE: Demand report data (enrichment)
                            left_column=sib_merge_col,   # SIB QR reference/loan ID
                            right_column=demand_merge_col, # Demand report loan ID
                            how='left',                  # LEFT JOIN - preserve all SIB QR records
                            suffixes=('_sib', '_demand'),
                            validate_data=True
                        )
                        
                        if merge_result['status'] == 'success':
                            merged_df = merge_result['merged_df']
                            merge_stats = merge_result['merge_stats']
                            
                            print(f"   ✅ DataFrameMerger successful!")
                            print(f"      • SIB QR Records: {merge_stats['left_records']}")
                            print(f"      • Demand Records: {merge_stats['right_records']}")
                            print(f"      • Matched Records: {merge_stats['matched_records']}")
                            print(f"      • Match Rate: {merge_stats['match_rate']:.1f}%")
                            
                            # Add reconciliation status based on merge results
                            merged_df['reconciliation_status'] = merged_df.apply(
                                lambda row: 'MATCHED - Branch Info Available' if pd.notna(row.get(demand_merge_col)) 
                                else 'UNMATCHED - No Branch Info', axis=1
                            )
                            
                            # Prepare result data with enhanced structure
                            result = {
                                'status': 'success',
                                'merged_data': merged_df,  # Return DataFrame directly for export compatibility
                                'detailed_data': {
                                    'total_rows': len(merged_df),
                                    'sample_data': merged_df.head(5).to_dict('records'),
                                    'matched_sample': merged_df[merged_df['reconciliation_status'].str.contains('MATCHED')].head(3).to_dict('records'),
                                    'unmatched_sample': merged_df[merged_df['reconciliation_status'].str.contains('UNMATCHED')].head(2).to_dict('records')
                                },
                                'merge_stats': {
                                    'sib_records': merge_stats['left_records'],
                                    'demand_records': merge_stats['right_records'],
                                    'matched_records': merge_stats['matched_records'],
                                    'unmatched_sib_records': merge_stats['unmatched_left_records'],
                                    'match_rate': merge_stats['match_rate'],
                                    'merge_efficiency': merge_stats.get('merge_efficiency', 0)
                                },
                            'debug_info': result['debug_info']
                        }
                    else:
                        result['debug_info']['error_message'] = "Merge columns not found after processing"
                else:
                    result['debug_info']['error_message'] = "One or both DataFrames are empty"
            else:
                result['debug_info']['error_message'] = "Required data not available from analysis"
                
        except Exception as e:
            result['debug_info']['error_message'] = f"Error during merge: {str(e)}"
        
        return result
    
    def generate_reconciliation_summary(self):
        """Generate comprehensive reconciliation summary"""
        bank_analysis = self.extract_bank_ledger_data()
        sib_analysis = self.analyze_sib_qr_report()
        demand_analysis = self.analyze_demand_report()
        merged_sib_demand = self.merge_sib_qr_with_demand_report()
        matches = self.find_matching_transactions()
        
        return {
            'bank_ledger': bank_analysis,
            'sib_qr_report': sib_analysis,
            'demand_report': demand_analysis,
            'merged_sib_demand': merged_sib_demand,
            'matches': matches,
            'summary_stats': self._calculate_summary_stats(bank_analysis, sib_analysis, demand_analysis, matches)
        }
    
    def _calculate_summary_stats(self, bank_analysis, sib_analysis, demand_analysis, matches):
        """Calculate summary statistics"""
        stats = {
            'total_bank_transactions': len(self.bank_ledger_df),
            'total_sib_transactions': len(self.sib_qr_df),
            'total_demand_entries': len(self.demand_report_df),
            'bank_sib_matches': len(matches['bank_sib_matches']),
            'bank_demand_matches': len(matches['bank_demand_matches']),
            'match_percentage': 0
        }
        
        if bank_analysis['filtered_data']:
            total_bank_filtered = bank_analysis['filtered_data']['total_rows']
            total_matches = stats['bank_sib_matches'] + stats['bank_demand_matches']
            if total_bank_filtered > 0:
                stats['match_percentage'] = (total_matches / total_bank_filtered) * 100
        
        return stats
    
    def _get_sib_merge_column(self, sib_df):
        """Get the merge column from SIB QR Report DataFrame"""
        if sib_df is None or sib_df.empty:
            return None
            
        # Common patterns for loan ID in SIB reports
        loan_id_patterns = ['referenceID', 'reference_id', 'loan_id', 'loanid', 'lan_id', 'lanid']
        
        for pattern in loan_id_patterns:
            matching_cols = [col for col in sib_df.columns if pattern.lower() in col.lower()]
            if matching_cols:
                return matching_cols[0]
        
        # Fallback: look for any column with 'id' in name
        id_columns = [col for col in sib_df.columns if 'id' in col.lower()]
        if id_columns:
            return id_columns[0]
            
        return None
    
    def _get_demand_merge_column(self, demand_df):
        """Get the merge column from Demand Report DataFrame"""
        if demand_df is None or demand_df.empty:
            return None
            
        # Common patterns for loan ID in demand reports
        loan_id_patterns = ['loan_id', 'loanid', 'lan_id', 'lanid', 'loan_no', 'account_no']
        
        for pattern in loan_id_patterns:
            matching_cols = [col for col in demand_df.columns if pattern.lower() in col.lower()]
            if matching_cols:
                return matching_cols[0]
        
        # Fallback: look for any column with 'id' or 'no' in name
        id_columns = [col for col in demand_df.columns if any(term in col.lower() for term in ['id', 'no'])]
        if id_columns:
            return id_columns[0]
            
        return None
    
    def create_bank_ledger_pivot_table(self):
        """
        Create pivot table equivalent for bank ledger data:
        Group by loan_id and sum amounts from filtered Sheet 1 results
        """
        print(f"📊 Creating bank ledger pivot table (loan_id groupby with amount sum)...")
        
        # Get filtered bank ledger data
        bank_analysis = self.extract_bank_ledger_data()
        
        result = {
            'status': 'failed',
            'pivot_data': None,
            'summary_stats': {},
            'debug_info': {}
        }
        
        try:
            if bank_analysis['status'] == 'success' and bank_analysis.get('parsed_data'):
                parsed_df = bank_analysis['parsed_data']['dataframe']
                
                # Filter to keep only valid loan IDs
                if 'loan_id_valid' in parsed_df.columns:
                    valid_loans_df = parsed_df[parsed_df['loan_id_valid'] == True].copy()
                    
                    if len(valid_loans_df) > 0:
                        # Check if required columns exist
                        amount_col = bank_analysis['filtered_data']['amount_column']
                        
                        if 'loan_id' in valid_loans_df.columns and amount_col in valid_loans_df.columns:
                            print(f"   • Processing {len(valid_loans_df)} valid loan entries")
                            print(f"   • Grouping by loan_id and summing {amount_col}")
                            
                            # Create pivot table using DataFrameGroupBy utility
                            groupby_result = self.groupby_processor.dynamic_groupby(
                                valid_loans_df,
                                group_by_columns=['loan_id'],
                                sum_columns=[amount_col],
                                count_columns=['loan_id'],
                                additional_aggregations={'description': 'first'},
                                sort_by=f'{amount_col}',
                                sort_ascending=False
                            )
                            
                            if groupby_result['status'] == 'success':
                                pivot_df = groupby_result['grouped_df']
                                
                                # Rename columns for clarity
                                column_mapping = {
                                    f'{amount_col}_sum': 'total_amount',
                                    f'{amount_col}_count': 'transaction_count',
                                    f'{amount_col}_mean': 'average_amount',
                                    'description_first': 'sample_description'
                                }
                                
                                # Apply column renaming if columns exist
                                existing_columns = {old: new for old, new in column_mapping.items() if old in pivot_df.columns}
                                if existing_columns:
                                    pivot_df = pivot_df.rename(columns=existing_columns)
                                
                                # Add additional calculated fields
                                if 'total_amount' in pivot_df.columns:
                                    pivot_df['amount_percentage'] = (pivot_df['total_amount'] / pivot_df['total_amount'].sum() * 100).round(2)
                                
                                result = {
                                    'status': 'success',
                                    'pivot_data': pivot_df,
                                    'summary_stats': {
                                        'total_unique_loans': len(pivot_df),
                                        'total_transactions': groupby_result['group_stats']['total_rows'],
                                        'total_amount': pivot_df['total_amount'].sum() if 'total_amount' in pivot_df.columns else 0,
                                        'average_loan_amount': pivot_df['total_amount'].mean() if 'total_amount' in pivot_df.columns else 0,
                                        'max_loan_amount': pivot_df['total_amount'].max() if 'total_amount' in pivot_df.columns else 0,
                                        'min_loan_amount': pivot_df['total_amount'].min() if 'total_amount' in pivot_df.columns else 0
                                    },
                                    'debug_info': {
                                        'original_entries': len(parsed_df),
                                        'valid_loan_entries': len(valid_loans_df),
                                        'filtered_out_entries': len(parsed_df) - len(valid_loans_df),
                                        'groupby_method': 'DataFrameGroupBy.dynamic_groupby',
                                        'group_columns': ['loan_id'],
                                        'sum_columns': [amount_col],
                                        'count_columns': ['loan_id'],
                                        'additional_aggregations': {'description': 'first'}
                                    }
                                }
                                
                                print(f"✅ Pivot table created successfully!")
                                print(f"   • {result['summary_stats']['total_unique_loans']} unique loan IDs")
                                print(f"   • {result['summary_stats']['total_transactions']} total transactions")
                                print(f"   • Total amount: {result['summary_stats']['total_amount']:,.2f}")
                                
                            else:
                                result['debug_info']['error_message'] = f"GroupBy operation failed: {groupby_result.get('error_message', 'Unknown error')}"
                        else:
                            result['debug_info']['error_message'] = f"Required columns not found. Available: {list(valid_loans_df.columns)}"
                    else:
                        result['debug_info']['error_message'] = "No valid loan entries found after filtering"
                        
                else:
                    result['debug_info']['error_message'] = "loan_id_valid column not found in parsed data"
            else:
                result['debug_info']['error_message'] = f"Bank analysis failed or no parsed data available. Status: {bank_analysis['status']}"
                
        except Exception as e:
            result['debug_info']['error_message'] = f"Error creating pivot table: {str(e)}"
            
        return result
    
    def create_merged_data_pivot_table(self):
        """
        Create pivot table from merged SIB QR + Demand Report data:
        Group by loan_id/reference_id and sum amounts
        """
        print(f"📊 Creating pivot table from merged SIB QR + Demand Report data...")
        
        # Get merged data
        merged_result = self.merge_sib_qr_with_demand_report()
        
        result = {
            'status': 'failed',
            'pivot_data': None,
            'summary_stats': {},
            'debug_info': {}
        }
        
        try:
            if merged_result['status'] == 'success' and merged_result.get('merged_data') is not None:
                merged_df = merged_result['merged_data']
                
                print(f"   • Processing {len(merged_df)} merged records")
                
                # Identify loan ID and amount columns
                loan_id_col = None
                amount_col = None
                
                # Look for loan ID column (various possible names)
                loan_id_patterns = ['reference_id', 'referenceID', 'loan_id', 'lan_id', 'reference_id_clean', 'loan_id_clean']
                for pattern in loan_id_patterns:
                    if pattern in merged_df.columns:
                        loan_id_col = pattern
                        break
                
                # Look for amount column
                amount_patterns = ['amount', 'transaction_amount', 'txn_amount', 'value']
                for pattern in amount_patterns:
                    if pattern in merged_df.columns:
                        amount_col = pattern
                        break
                
                if loan_id_col and amount_col:
                    print(f"   • Using loan ID column: {loan_id_col}")
                    print(f"   • Using amount column: {amount_col}")
                    
                    # Filter out rows with null loan IDs
                    valid_merged_df = merged_df.dropna(subset=[loan_id_col]).copy()
                    
                    if len(valid_merged_df) > 0:
                        print(f"   • {len(valid_merged_df)} records with valid loan IDs")
                        
                        # Use DataFrameGroupBy to create pivot table
                        groupby_result = self.groupby_processor.dynamic_groupby(
                            valid_merged_df,
                            group_by_columns=[loan_id_col],
                            sum_columns=[amount_col],
                            count_columns=[loan_id_col],
                            additional_aggregations={
                                'branch_name': 'first',  # Get branch name
                                'member_name': 'first',  # Get member name
                                'group_name': 'first',   # Get group name
                                'reconciliation_status': 'first'  # Get reconciliation status
                            },
                            sort_by=amount_col,
                            sort_ascending=False
                        )
                        
                        if groupby_result['status'] == 'success':
                            pivot_df = groupby_result['grouped_df']
                            
                            # Rename columns for clarity
                            column_mapping = {
                                f'{amount_col}': 'total_amount',
                                f'{loan_id_col}_count': 'transaction_count',
                                'branch_name_first': 'branch_name',
                                'member_name_first': 'member_name',
                                'group_name_first': 'group_name',
                                'reconciliation_status_first': 'reconciliation_status'
                            }
                            
                            # Apply column renaming if columns exist
                            existing_columns = {old: new for old, new in column_mapping.items() if old in pivot_df.columns}
                            if existing_columns:
                                pivot_df = pivot_df.rename(columns=existing_columns)
                            
                            # Add percentage calculation
                            if 'total_amount' in pivot_df.columns:
                                total_sum = pivot_df['total_amount'].sum()
                                if total_sum > 0:
                                    pivot_df['amount_percentage'] = (pivot_df['total_amount'] / total_sum * 100).round(2)
                            
                            # Add loan status based on reconciliation
                            if 'reconciliation_status' in pivot_df.columns:
                                pivot_df['loan_status'] = pivot_df['reconciliation_status'].apply(
                                    lambda x: 'MATCHED' if 'MATCHED' in str(x) else 'UNMATCHED'
                                )
                            
                            # Calculate summary statistics
                            total_amount = pivot_df['total_amount'].sum() if 'total_amount' in pivot_df.columns else 0
                            matched_loans = len(pivot_df[pivot_df.get('loan_status', '') == 'MATCHED']) if 'loan_status' in pivot_df.columns else 0
                            unmatched_loans = len(pivot_df[pivot_df.get('loan_status', '') == 'UNMATCHED']) if 'loan_status' in pivot_df.columns else 0
                            
                            result = {
                                'status': 'success',
                                'pivot_data': pivot_df,
                                'summary_stats': {
                                    'total_unique_loans': len(pivot_df),
                                    'total_transactions': groupby_result['group_stats']['total_rows'],
                                    'total_amount': total_amount,
                                    'average_loan_amount': pivot_df['total_amount'].mean() if 'total_amount' in pivot_df.columns else 0,
                                    'max_loan_amount': pivot_df['total_amount'].max() if 'total_amount' in pivot_df.columns else 0,
                                    'min_loan_amount': pivot_df['total_amount'].min() if 'total_amount' in pivot_df.columns else 0,
                                    'matched_loans': matched_loans,
                                    'unmatched_loans': unmatched_loans,
                                    'match_rate': (matched_loans / len(pivot_df) * 100) if len(pivot_df) > 0 else 0
                                },
                                'debug_info': {
                                    'original_merged_records': len(merged_df),
                                    'valid_loan_records': len(valid_merged_df),
                                    'loan_id_column': loan_id_col,
                                    'amount_column': amount_col,
                                    'groupby_method': 'DataFrameGroupBy.dynamic_groupby',
                                    'merge_source': 'SIB QR + Demand Report'
                                }
                            }
                            
                            print(f"✅ Merged data pivot table created successfully!")
                            print(f"   • {result['summary_stats']['total_unique_loans']} unique loan IDs")
                            print(f"   • {result['summary_stats']['total_transactions']} total transactions")
                            print(f"   • Total amount: {result['summary_stats']['total_amount']:,.2f}")
                            print(f"   • Matched loans: {result['summary_stats']['matched_loans']}")
                            print(f"   • Unmatched loans: {result['summary_stats']['unmatched_loans']}")
                            print(f"   • Match rate: {result['summary_stats']['match_rate']:.1f}%")
                            
                        else:
                            result['debug_info']['error_message'] = f"GroupBy operation failed: {groupby_result.get('error_message', 'Unknown error')}"
                    
                    else:
                        result['debug_info']['error_message'] = "No records with valid loan IDs found"
                
                else:
                    result['debug_info']['error_message'] = f"Required columns not found. Loan ID patterns tried: {loan_id_patterns}, Amount patterns tried: {amount_patterns}"
                    result['debug_info']['available_columns'] = list(merged_df.columns)
            
            else:
                result['debug_info']['error_message'] = f"Merge operation failed or no merged data available. Status: {merged_result['status']}"
                
        except Exception as e:
            result['debug_info']['error_message'] = f"Error creating merged data pivot table: {str(e)}"
            
        return result
    
    def export_reconciliation_to_excel(self, output_filename: str = None, output_dir: str = None) -> str:
        """
        Export complete reconciliation analysis to Excel format
        
        Args:
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
        
        # Generate comprehensive reconciliation data
        reconciliation_data = self.generate_reconciliation_summary()
        
        # Export to Excel
        export_path = self.excel_exporter.export_reconciliation_report(
            reconciliation_data, 
            output_filename
        )
        
        print(f"✅ Reconciliation data exported successfully!")
        print(f"📁 Export location: {export_path}")
        
        return export_path
    
    def export_individual_sheets(self, sheet_types: list = None, output_dir: str = None) -> dict:
        """
        Export individual analysis sheets to separate Excel files
        
        Args:
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
                    bank_analysis = self.extract_bank_ledger_data()
                    if bank_analysis.get('filtered_data') and bank_analysis['filtered_data'].get('data') is not None:
                        filename = f"bank_ledger_analysis.xlsx"
                        path = self.excel_exporter.export_dataframe(
                            bank_analysis['filtered_data']['data'], 
                            filename, 
                            'Bank Ledger Analysis'
                        )
                        export_paths[sheet_type] = path
                
                elif sheet_type == 'sib_qr':
                    sib_analysis = self.analyze_sib_qr_report()
                    if sib_analysis.get('processed_data') and sib_analysis['processed_data'].get('data') is not None:
                        filename = f"sib_qr_analysis.xlsx"
                        path = self.excel_exporter.export_dataframe(
                            sib_analysis['processed_data']['data'], 
                            filename, 
                            'SIB QR Analysis'
                        )
                        export_paths[sheet_type] = path
                
                elif sheet_type == 'demand_report':
                    demand_analysis = self.analyze_demand_report()
                    if demand_analysis.get('processed_data') and demand_analysis['processed_data'].get('data') is not None:
                        filename = f"demand_report_analysis.xlsx"
                        path = self.excel_exporter.export_dataframe(
                            demand_analysis['processed_data']['data'], 
                            filename, 
                            'Demand Report Analysis'
                        )
                        export_paths[sheet_type] = path
                
                elif sheet_type == 'merged_data':
                    merged_data = self.merge_sib_qr_with_demand_report()
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