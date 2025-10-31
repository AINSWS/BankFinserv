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
        """
        Detect columns based on name patterns with aggressive normalization
        Handles: spaces, underscores, hyphens, dots, case variations, trailing spaces
        """
        detected = {}
        
        # Normalize function: remove all spaces, underscores, special chars, lowercase
        def normalize(text):
            if text is None:
                return ""
            normalized = str(text).lower().strip()
            # Remove all special characters and spaces
            for char in [' ', '_', '-', '.', '(', ')', '[', ']', '{', '}', ':', ';', ',', '\t', '\n']:
                normalized = normalized.replace(char, '')
            return normalized
        
        # Normalize actual DataFrame column names
        df_columns_normalized = [normalize(col) for col in df.columns]
        
        for key, pattern_list in patterns.items():
            matches = []
            for pattern in pattern_list:
                pattern_normalized = normalize(pattern)
                for i, col_norm in enumerate(df_columns_normalized):
                    # Check if pattern matches and column hasn't been used yet
                    if pattern_normalized in col_norm and df.columns[i] not in [match for matches_list in detected.values() for match in matches_list]:
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
            'tran_date': ['trandate', 'tran date', 'tran_date', 'transaction date', 'transactiondate', 'transaction_date', 'date', 'txn date', 'txndate'],
            'payer_vpa': ['payervpa', 'payer vpa', 'payer_vpa', 'vpa', 'upi id', 'upiid', 'upi_id'],
            'payer_name': ['payername', 'payer name', 'payer_name', 'name', 'customer name', 'customername', 'customer_name', 'member name', 'membername'],
            'rrn': ['rrn', 'reference retrieval number', 'referenceretrievalnumber', 'reference_retrieval_number', 'txn ref', 'txnref', 'txn_ref', 'transaction reference'],
            'reference_id': ['referenceid', 'reference id', 'reference_id', 'refrence id', 'refrenceid', 'refrence_id', 'refrence number', 'refrencenumber', 'refrence_number', 
                           'loan id', 'loanid', 'loan_id', 'loan number', 'loannumber', 'loan_number', 
                           'lan id', 'lanid', 'lan_id', 'lan number', 'lannumber', 'lan_number'],
            'amount': ['amount', 'value', 'transaction amount', 'transactionamount', 'transaction_amount', 'txn amount', 'txnamount', 'txn_amount', 'total', 'sum']
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
        """Process and clean reference IDs - creates calculated column with calc_ prefix"""
        processed_df = self.sib_qr_df.copy()
        
        # CALCULATED VALUE - cleaned/validated reference ID
        # Use calc_ prefix to distinguish from direct file column
        processed_df['calc_reference_id_clean'] = processed_df[reference_col].apply(self._clean_reference_id)
        
        # Keep reference_id_clean for backward compatibility
        processed_df['reference_id_clean'] = processed_df['calc_reference_id_clean']
        
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