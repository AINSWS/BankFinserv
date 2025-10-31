"""
Demand Report Processor - Handles demand report data processing and analysis
"""

import pandas as pd

class DemandReportProcessor:
    """
    Handles all Demand Report (Sheet 3) processing operations:
    - Column detection and extraction
    - Data validation and cleaning
    - Branch, group, and member information processing
    """
    
    def __init__(self, demand_report_df: pd.DataFrame):
        self.demand_report_df = demand_report_df
    
    def detect_columns(self, df: pd.DataFrame, patterns: dict) -> dict:
        """
        Detect columns based on name patterns with aggressive normalization
        Handles: spaces, underscores, hyphens, dots, case variations, trailing spaces
        Returns single column name per field (not list)
        """
        detected = {}
        used_columns = set()
        
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
            for pattern in pattern_list:
                pattern_normalized = normalize(pattern)
                for i, col_norm in enumerate(df_columns_normalized):
                    if pattern_normalized in col_norm and df.columns[i] not in used_columns:
                        detected[key] = df.columns[i]  # Return single column name
                        used_columns.add(df.columns[i])
                        break
                if key in detected:  # Found a match, move to next field
                    break
        
        return detected
    
    def analyze_demand_report(self):
        """
        Analyze Demand Report (Sheet 3) structure:
        Expected to have loan_id, branch_name, group_name, member_name, amount fields
        Used for merging with SIB QR report based on loan_id
        """
        column_patterns = {
            'loan_id': ['loan id', 'loanid', 'loan_id', 'lan id', 'lanid', 'lan_id', 'loan no', 'loanno', 'loan_no', 'account no', 'accountno', 'account_no', 'loan number'],
            'branch_name': ['branch', 'branch name', 'branchname', 'mbri name', 'mbriname', 'mbri_name', 'branch_name', 'office', 'office name'],
            'group_name': ['group no', 'groupno', 'group_no', 'mgi name', 'mginame', 'mgi_name', 'group name', 'groupname', 'group_name', 'group', 'group id', 'groupid', 'group_id'],
            'member_name': ['mvi name', 'mviname', 'mvi_name', 'mmi name', 'mminame', 'mmi_name', 'member name', 'membername', 'member_name', 'mamber name', 'mambername', 'mamber_name', 'customer name', 'customername', 'customer_name', 'name'],
            'amount': ['mldi amount', 'mldiamount', 'mldi_amount', 'textbox40', 'outstanding', 'balance', 'demand amount', 'demandamount', 'demand_amount', 'mls rdamount', 'mlsrdamount', 'mls_rdamount', 'amount', 'total'],
            'due_date': ['due date', 'duedate', 'due_date', 'maturity date', 'maturitydate', 'maturity_date', 'payment date', 'paymentdate', 'payment_date']
        }
        
        detected_columns = self.detect_columns(self.demand_report_df, column_patterns)
        
        result = {
            'detected_columns': detected_columns,
            'total_rows': len(self.demand_report_df),
            'total_columns': len(self.demand_report_df.columns),
            'sample_data': self.demand_report_df.head(5).to_dict('records') if len(self.demand_report_df) > 0 else [],
            'processed_data': None,
            'status': 'success' if detected_columns.get('loan_id') else 'partial'
        }
        
        # Extract key columns for merging
        if detected_columns.get('loan_id'):
            extracted_df = self._extract_demand_report_data(detected_columns)
            
            result['processed_data'] = {
                'dataframe': extracted_df,
                'total_rows': len(extracted_df),
                'loan_id_column': detected_columns['loan_id'][0],
                'sample_data': extracted_df.head(5).to_dict('records')
            }
        
        return result
    
    def _extract_demand_report_data(self, detected_columns):
        """Extract and clean key columns from demand report"""
        # Get the columns we need for merging
        columns_to_extract = []
        
        # Always include loan_id (now single column name, not list)
        if detected_columns.get('loan_id'):
            columns_to_extract.append(detected_columns['loan_id'])
        
        # Include other important columns if available
        for key in ['branch_name', 'group_name', 'member_name', 'amount', 'due_date']:
            if detected_columns.get(key):
                columns_to_extract.append(detected_columns[key])
        
        # Remove duplicates while preserving order
        columns_to_extract = list(dict.fromkeys(columns_to_extract))
        
        # Extract the DataFrame
        extracted_df = self.demand_report_df[columns_to_extract].copy()
        
        # CALCULATED VALUE - Clean loan_id column
        # Use calc_ prefix to distinguish from direct file column
        if detected_columns.get('loan_id'):
            loan_id_col = detected_columns['loan_id']  # Single string, not list
            extracted_df['calc_loan_id_clean'] = extracted_df[loan_id_col].apply(self._clean_loan_id)
            # Keep loan_id_clean for backward compatibility
            extracted_df['loan_id_clean'] = extracted_df['calc_loan_id_clean']
        
        return extracted_df
    
    def _clean_loan_id(self, loan_id):
        """Clean and standardize loan ID"""
        if pd.isna(loan_id) or loan_id is None:
            return None
        
        loan_str = str(loan_id).strip().upper()
        
        # Basic validation
        if len(loan_str) < 3:
            return None
        
        return loan_str if loan_str else None