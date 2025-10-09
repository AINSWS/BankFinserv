"""
Match Finder - Handles finding matches between different reports
"""

import pandas as pd

class MatchFinder:
    """
    Handles finding matches between different reports:
    - Bank ledger vs SIB QR matches
    - Bank ledger vs Demand report matches
    - Cross-validation and statistics
    """
    
    def __init__(self):
        pass
    
    def find_matching_transactions(self, bank_analysis, sib_analysis, demand_analysis):
        """Find matching transactions between files"""
        matches = {
            'bank_sib_matches': [],
            'bank_demand_matches': [],
            'sib_demand_matches': [],
            'unmatched_bank': [],
            'unmatched_sib': [],
            'unmatched_demand': []
        }
        
        # Simple amount-based matching (can be enhanced)
        if (bank_analysis.get('filtered_data') and 
            sib_analysis.get('detected_columns', {}).get('amount') and
            demand_analysis.get('detected_columns', {}).get('amount')):
            
            # Extract amounts for comparison
            bank_df = bank_analysis['filtered_data']['dataframe']
            sib_df = sib_analysis['processed_data']['dataframe'] if sib_analysis.get('processed_data') else pd.DataFrame()
            demand_df = demand_analysis['processed_data']['dataframe'] if demand_analysis.get('processed_data') else pd.DataFrame()
            
            # Find Bank-SIB matches
            matches['bank_sib_matches'] = self._find_bank_sib_matches(bank_df, sib_df, bank_analysis, sib_analysis)
            
            # Find Bank-Demand matches
            matches['bank_demand_matches'] = self._find_bank_demand_matches(bank_df, demand_df, bank_analysis, demand_analysis)
            
        return matches
    
    def _find_bank_sib_matches(self, bank_df, sib_df, bank_analysis, sib_analysis):
        """Find matches between bank ledger and SIB QR report"""
        matches = []
        
        if bank_df.empty or sib_df.empty:
            return matches
        
        try:
            bank_amount_col = bank_analysis['filtered_data']['amount_column']
            sib_amount_col = sib_analysis['detected_columns']['amount'][0]
            
            # Simple amount-based matching
            for _, bank_row in bank_df.iterrows():
                bank_amount = bank_row.get(bank_amount_col, 0)
                
                # Look for matching amounts in SIB data
                sib_matches = sib_df[sib_df[sib_amount_col] == bank_amount]
                
                for _, sib_row in sib_matches.iterrows():
                    match_info = {
                        'bank_reference': bank_row.get(bank_analysis['filtered_data'].get('reference_column'), 'N/A'),
                        'sib_rrn': sib_row.get('rrn', 'N/A'),
                        'amount': bank_amount,
                        'match_type': 'amount_exact'
                    }
                    matches.append(match_info)
                    
        except Exception as e:
            print(f"Error finding bank-SIB matches: {str(e)}")
        
        return matches
    
    def _find_bank_demand_matches(self, bank_df, demand_df, bank_analysis, demand_analysis):
        """Find matches between bank ledger and demand report"""
        matches = []
        
        if bank_df.empty or demand_df.empty:
            return matches
        
        try:
            bank_amount_col = bank_analysis['filtered_data']['amount_column']
            demand_amount_col = demand_analysis['detected_columns']['amount'][0] if demand_analysis.get('detected_columns', {}).get('amount') else None
            
            if not demand_amount_col:
                return matches
            
            # Simple amount-based matching
            for _, bank_row in bank_df.iterrows():
                bank_amount = bank_row.get(bank_amount_col, 0)
                
                # Look for matching amounts in demand data
                demand_matches = demand_df[demand_df[demand_amount_col] == bank_amount]
                
                for _, demand_row in demand_matches.iterrows():
                    match_info = {
                        'bank_reference': bank_row.get(bank_analysis['filtered_data'].get('reference_column'), 'N/A'),
                        'demand_loan_id': demand_row.get('loan_id_clean', 'N/A'),
                        'amount': bank_amount,
                        'match_type': 'amount_exact'
                    }
                    matches.append(match_info)
                    
        except Exception as e:
            print(f"Error finding bank-demand matches: {str(e)}")
        
        return matches