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
        """Detect columns based on name patterns - returns first match for each field"""
        detected = {}
        df_columns_lower = [col.lower() for col in df.columns]
        used_columns = set()  # Track already used columns
        
        for key, pattern_list in patterns.items():
            for pattern in pattern_list:
                for i, col in enumerate(df_columns_lower):
                    if pattern.lower() in col and df.columns[i] not in used_columns:
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
            'loan_id': ['loan id', 'loan_id', 'loanid', 'lan_id', 'lanid', 'loan_no', 'account_no'],
            'branch_name': ['branch', 'mbri_name', 'branchname', 'branch_name', 'office'],
            'group_name': ['group no', 'group_no', 'groupno', 'mgi_name', 'group_name', 'group', 'group_id'],
            'member_name': ['mvi name', 'mvi_name', 'mviname', 'mmi_name', 'member_name', 'mamber_name', 'customer_name', 'name'],
            'amount': ['mldi_amount', 'textbox40', 'outstanding', 'balance', 'demand_amount', 'mls_rdamount', 'amount'],
            'due_date': ['due_date', 'maturity_date', 'payment_date']
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
        
        # Clean loan_id column
        if detected_columns.get('loan_id'):
            loan_id_col = detected_columns['loan_id']  # Single string, not list
            extracted_df['loan_id_clean'] = extracted_df[loan_id_col].apply(self._clean_loan_id)
        
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