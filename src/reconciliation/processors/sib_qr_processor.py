"""
SIB QR Report Processor - Handles SIB QR report data processing and analysis
"""

import pandas as pd
import sys
import os

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

from dataframe_splitter import DataFrameSplitter

class SIBQRProcessor:
    """
    Handles all SIB QR Report (Sheet 2) processing operations:
    - Column detection and extraction
    - Reference ID processing and cleaning
    - Data validation and statistics
    """
    
    def __init__(self, sib_qr_df: pd.DataFrame):
        self.sib_qr_df = sib_qr_df
        self.splitter = DataFrameSplitter()
    
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
            'processed_data': None,
            'loan_id_stats': None,
            'status': 'success' if detected_columns.get('reference_id') and detected_columns.get('amount') else 'partial'
        }
        
        # Process reference IDs if found
        if detected_columns.get('reference_id'):
            reference_col = detected_columns['reference_id'][0]
            
            # Extract and process the data
            processed_df = self._process_reference_ids(reference_col)
            
            result['processed_data'] = {
                'dataframe': processed_df,
                'reference_id_column': reference_col,
                'total_rows': len(processed_df),
                'sample_data': processed_df.head(5).to_dict('records')
            }
            
            # Calculate loan ID statistics
            if 'reference_id_clean' in processed_df.columns:
                valid_loans = processed_df['reference_id_clean'].notna().sum()
                total_rows = len(processed_df)
                
                result['loan_id_stats'] = {
                    'total_rows': total_rows,
                    'valid_loan_ids': valid_loans,
                    'invalid_loan_ids': total_rows - valid_loans,
                    'success_rate': (valid_loans / total_rows * 100) if total_rows > 0 else 0,
                    'unique_loan_ids': processed_df['reference_id_clean'].nunique()
                }
        
        return result
    
    def _process_reference_ids(self, reference_col: str):
        """Process and clean reference IDs using DataFrameSplitter"""
        processed_df = self.sib_qr_df.copy()
        
        # Apply basic reference ID cleaning
        # Since SIB QR reference IDs are usually already clean, we'll validate and clean them directly
        processed_df['reference_id_clean'] = processed_df[reference_col].apply(self._clean_reference_id)
        
        clean_result = {
            'status': 'success',
            'processed_data': processed_df
        }
            
        return processed_df
    
    def _clean_reference_id(self, ref_id):
        """Clean and validate reference ID"""
        if pd.isna(ref_id) or ref_id is None:
            return None
        
        ref_str = str(ref_id).strip().upper()
        
        # Basic validation
        if len(ref_str) < 3:
            return None
        
        # Remove common prefixes/suffixes if needed
        # This can be customized based on your data patterns
        return ref_str if ref_str else None