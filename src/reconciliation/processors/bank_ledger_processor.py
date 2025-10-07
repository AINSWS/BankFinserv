"""
Bank Ledger Processor - Handles bank ledger data processing and analysis
"""

import pandas as pd
import sys
import os

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from dataframe_splitter import DataFrameSplitter
from dataframe_groupby import DataFrameGroupBy

class BankLedgerProcessor:
    """
    Handles all bank ledger (Sheet 1) processing operations:
    - Column detection and extraction
    - Narration parsing and splitting
    - Loan ID filtering and validation
    - Pivot table creation and grouping
    """
    
    def __init__(self, bank_ledger_df: pd.DataFrame):
        self.bank_ledger_df = bank_ledger_df
        self.splitter = DataFrameSplitter()
        self.groupby_processor = DataFrameGroupBy()
    
    def detect_columns(self, df: pd.DataFrame, patterns: dict) -> dict:
        """Detect columns based on name patterns"""
        detected = {}
        df_columns_lower = [col.lower() for col in df.columns]
        
        for key, pattern_list in patterns.items():
            matches = []
            for pattern in pattern_list:
                for i, col in enumerate(df_columns_lower):
                    if pattern.lower() in col and df.columns[i] not in [match for matches_list in detected.values() for match in matches_list]:
                        matches.append(df.columns[i])
                        break
            if matches:
                detected[key] = matches
        
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
    
    def _parse_narration_field(self, df: pd.DataFrame, narration_col: str, amount_col: str):
        """Parse narration field using DataFrameSplitter and filter loan IDs"""
        expected_structure = ['description', 'loan_id', 'customer_name', 'group_name', 'branch']
        
        # Use DataFrameSplitter to split narration
        split_result = self.splitter.process_narration_field(
            df, 
            narration_col, 
            delimiter='/',
            expected_structure=expected_structure,
            apply_loan_filter=True
        )
        
        if 'dataframe' in split_result:
            parsed_df = split_result['dataframe'].copy()
            
            # The splitter already added loan_id_valid column, so we can use it directly
            # Add loan_id_clean for additional processing if needed
            if 'loan_id' in parsed_df.columns and 'loan_id_valid' in parsed_df.columns:
                parsed_df['loan_id_clean'] = parsed_df.apply(
                    lambda row: row['loan_id'] if row['loan_id_valid'] else None, axis=1
                )
            
            return parsed_df
        else:
            # Fallback to basic processing if splitter fails
            return df.copy()
    
    def _is_valid_loan_id(self, loan_id: str) -> bool:
        """Validate if a string is a valid loan ID"""
        if pd.isna(loan_id) or loan_id is None:
            return False
        
        loan_id_str = str(loan_id).strip()
        
        # Basic validation rules
        if len(loan_id_str) < 3:
            return False
        
        # Must contain at least one number
        if not any(char.isdigit() for char in loan_id_str):
            return False
        
        # Cannot be purely alphabetic
        if loan_id_str.isalpha():
            return False
        
        # Filter out common branch name patterns
        branch_patterns = ['branch', 'office', 'head', 'main', 'sub', 'regional']
        loan_id_lower = loan_id_str.lower()
        
        for pattern in branch_patterns:
            if pattern in loan_id_lower:
                return False
        
        return True
    
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
                            # Check for group-related columns to preserve
                            additional_aggs = {'description': 'first'}
                            if 'group_name' in valid_loans_df.columns:
                                additional_aggs['group_name'] = 'first'
                            if 'customer_name' in valid_loans_df.columns:
                                additional_aggs['customer_name'] = 'first'
                            if 'branch' in valid_loans_df.columns:
                                additional_aggs['branch'] = 'first'
                                
                            # Find the narration column to count transactions
                            narration_col = bank_analysis['filtered_data']['narration_column']
                            
                            groupby_result = self.groupby_processor.dynamic_groupby(
                                valid_loans_df,
                                group_by_columns=['loan_id'],
                                sum_columns=[amount_col],
                                count_columns=[narration_col],  # Count transactions using narration column
                                additional_aggregations=additional_aggs,
                                sort_by=f'{amount_col}',
                                sort_ascending=False
                            )
                            
                            if groupby_result['status'] == 'success':
                                pivot_df = groupby_result['grouped_df']
                                
                                # Rename columns for clarity
                                column_mapping = {
                                    f'{amount_col}': 'total_amount',
                                    f'{narration_col}_count': 'transaction_count',
                                    'description_first': 'sample_description'
                                }
                                
                                # Add group-related column mappings if they exist
                                if 'group_name_first' in pivot_df.columns:
                                    column_mapping['group_name_first'] = 'group_name'
                                if 'customer_name_first' in pivot_df.columns:
                                    column_mapping['customer_name_first'] = 'customer_name'
                                if 'branch_first' in pivot_df.columns:
                                    column_mapping['branch_first'] = 'branch_name'
                                
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
                                        'total_transactions': groupby_result['group_stats']['original_rows'],
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