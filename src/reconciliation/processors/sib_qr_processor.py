"""
SIB QR Report Processor - Handles SIB QR report data processing and analysis
"""

import pandas as pd
import sys
import os

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

# Import with fallback for both PyInstaller and normal execution
try:
    from src.utils.dataframe_splitter import DataFrameSplitter
except ModuleNotFoundError:
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
                unique_loan_ids = processed_df['reference_id_clean'].nunique()
                
                # Detect TRUE duplicates - same RRN/transaction ID appearing multiple times
                # (NOT same loan_id - multiple payments per loan is valid!)
                duplicate_analysis = self._analyze_transaction_duplicates(processed_df)
                
                result['loan_id_stats'] = {
                    'total_rows': total_rows,
                    'valid_loan_ids': valid_loans,
                    'invalid_loan_ids': total_rows - valid_loans,
                    'success_rate': (valid_loans / total_rows * 100) if total_rows > 0 else 0,
                    'unique_loan_ids': unique_loan_ids,
                    'duplicate_transactions': duplicate_analysis['duplicate_count'],
                    'loans_with_multiple_payments': duplicate_analysis['loans_with_multiple_payments']
                }
                
                # Store duplicate details for debugging
                result['duplicate_analysis'] = duplicate_analysis
                
                # Print warning only if TRUE duplicates found (same transaction twice)
                if duplicate_analysis['duplicate_count'] > 0:
                    print(f"⚠️ WARNING: Found {duplicate_analysis['duplicate_count']} DUPLICATE TRANSACTIONS (same RRN)!")
                    print(f"   These may cause incorrect QR totals.")
                
                # Info about multiple payments (this is normal)
                if duplicate_analysis['loans_with_multiple_payments'] > 0:
                    print(f"ℹ️ INFO: {duplicate_analysis['loans_with_multiple_payments']} loans have multiple payments (normal - partial EMI payments)")
        
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
    
    def _analyze_transaction_duplicates(self, processed_df: pd.DataFrame) -> dict:
        """
        Analyze for TRUE duplicates - same transaction (RRN) appearing multiple times.
        Multiple payments for same loan_id is VALID (partial EMI payments).
        
        Returns:
            Dictionary with duplicate transaction analysis
        """
        result = {
            'duplicate_count': 0,
            'duplicate_transactions': [],
            'loans_with_multiple_payments': 0,
            'multiple_payment_details': []
        }
        
        try:
            # Find RRN column (unique transaction identifier)
            rrn_col = None
            for col in processed_df.columns:
                col_lower = col.lower().replace(' ', '').replace('_', '')
                if 'rrn' in col_lower or 'transactionid' in col_lower or 'txnid' in col_lower:
                    rrn_col = col
                    break
            
            # Check for TRUE duplicates (same RRN appearing twice = same transaction recorded twice)
            if rrn_col and rrn_col in processed_df.columns:
                rrn_counts = processed_df[rrn_col].value_counts()
                duplicate_rrns = rrn_counts[rrn_counts > 1]
                
                if not duplicate_rrns.empty:
                    result['duplicate_count'] = len(duplicate_rrns)
                    result['duplicate_transactions'] = duplicate_rrns.to_dict()
            
            # Count loans with multiple payments (this is NORMAL, not an error)
            if 'reference_id_clean' in processed_df.columns:
                loan_counts = processed_df['reference_id_clean'].value_counts()
                loans_multiple = loan_counts[loan_counts > 1]
                result['loans_with_multiple_payments'] = len(loans_multiple)
                
                # Store details of loans with multiple payments for info
                if not loans_multiple.empty:
                    result['multiple_payment_details'] = loans_multiple.head(10).to_dict()
                    
        except Exception as e:
            print(f"⚠️ Error in duplicate analysis: {e}")
        
        return result