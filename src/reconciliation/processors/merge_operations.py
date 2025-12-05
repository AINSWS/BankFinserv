"""
Merge Operations Handler - Handles merging operations between different reports
"""

import pandas as pd
import sys
import os
import logging

# Add utils directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'utils'))

# Import with fallback for both PyInstaller and normal execution
try:
    from src.utils.dataframe_merger import DataFrameMerger
    from src.utils.dataframe_groupby import DataFrameGroupBy
except ModuleNotFoundError:
    from dataframe_merger import DataFrameMerger
    from dataframe_groupby import DataFrameGroupBy

class MergeOperationsHandler:
    """
    Handles all merge operations between different reports:
    - SIB QR + Demand Report merging
    - Pivot table creation from merged data
    - Match finding and statistics
    """
    
    def __init__(self):
        self.merger = DataFrameMerger()
        self.groupby_processor = DataFrameGroupBy()
    
    def merge_sib_qr_with_demand_report(self, sib_analysis, demand_analysis):
        """
        Merge SIB QR Report (Sheet 2) with Demand Report (Sheet 3) using DataFrameMerger
        Uses dynamic merging with LEFT JOIN to preserve all SIB QR transactions
        """
        print(f"🔗 Starting SIB QR + Demand Report merge using DataFrameMerger...")
        
        result = {
            'status': 'failed',
            'merged_data': None,
            'merge_stats': {
                'sib_records': 0,
                'demand_records': 0,
                'matched_records': 0,
                'unmatched_sib_records': 0,
                'match_rate': 0,
                'merge_efficiency': 0
            },
            'debug_info': {}
        }
        
        try:
            if (sib_analysis.get('processed_data') and 
                demand_analysis.get('processed_data') and
                sib_analysis['processed_data'].get('dataframe') is not None and
                demand_analysis['processed_data'].get('dataframe') is not None):
                
                sib_df = sib_analysis['processed_data']['dataframe']
                demand_df = demand_analysis['processed_data']['dataframe']
                
                if not sib_df.empty and not demand_df.empty:
                    # Get merge columns dynamically
                    sib_merge_col = self._get_sib_merge_column(sib_df)
                    demand_merge_col = self._get_demand_merge_column(demand_df)
                    
                    if sib_merge_col and demand_merge_col:
                        print(f"   • SIB QR merge column: {sib_merge_col}")
                        print(f"   • Demand Report merge column: {demand_merge_col}")
                        
                        # Ensure consistent data types for merging
                        sib_df = sib_df.copy()
                        demand_df = demand_df.copy()
                        
                        # Convert both merge columns to string to avoid int64/object mismatch
                        sib_df[sib_merge_col] = sib_df[sib_merge_col].astype(str).str.strip()
                        demand_df[demand_merge_col] = demand_df[demand_merge_col].astype(str).str.strip()
                        
                        print(f"   • Converted merge columns to string for consistency")
                        
                        # Use DataFrameMerger for the merge operation
                        merge_result = self.merger.dynamic_merge(
                            left_df=sib_df,
                            right_df=demand_df,
                            left_column=sib_merge_col,
                            right_column=demand_merge_col,
                            how='left',  # LEFT JOIN to preserve all SIB QR records
                            validate_data=True
                        )
                        
                        if merge_result['status'] == 'success':
                            merged_df = merge_result['merged_df']
                            merge_stats = merge_result['merge_stats']
                            
                            print(f"✅ DataFrameMerger successful!")
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
    
    def create_merged_data_pivot_table(self, merged_result):
        """
        Create pivot table from merged SIB QR + Demand Report data:
        Group by reference_id (loan_id) and sum amounts
        """
        print(f"📊 Creating pivot table from merged SIB QR + Demand Report data...")
        
        result = {
            'status': 'failed',
            'pivot_data': None,
            'summary_stats': {},
            'debug_info': {}
        }
        
        try:
            if merged_result['status'] == 'success' and merged_result.get('merged_data') is not None:
                merged_df = merged_result['merged_data']
                
                # Find amount and reference ID columns
                amount_col = self._find_amount_column(merged_df)
                ref_id_col = self._find_reference_id_column(merged_df)
                
                # CRITICAL: If no amount column found, return empty pivot
                if amount_col is None:
                    print(f"   ⚠️ ERROR: No SIB QR amount column found! Cannot create QR pivot.")
                    result['debug_info']['error_message'] = "No SIB QR amount column found in merged data"
                    # Return empty pivot with correct structure
                    empty_pivot = pd.DataFrame(columns=['loan_id', 'total_amount', 'transaction_count'])
                    result['status'] = 'success'
                    result['pivot_data'] = empty_pivot
                    result['summary_stats'] = {'total_unique_loans': 0, 'total_amount': 0}
                    return result
                
                if amount_col and ref_id_col:
                    # Find a different column to count (not the same as group column)
                    count_col = None
                    for col in merged_df.columns:
                        if col != ref_id_col and col in merged_df.columns:
                            count_col = col
                            break
                    
                    # If no other column found, use amount column for counting
                    if not count_col:
                        count_col = amount_col
                    
                    # Create pivot table using DataFrameGroupBy
                    groupby_result = self.groupby_processor.dynamic_groupby(
                        merged_df,
                        group_by_columns=[ref_id_col],
                        sum_columns=[amount_col],
                        count_columns=[count_col],
                        additional_aggregations={
                            col: 'first' for col in [
                                'reconciliation_status', 'member_name', 'branch_name', 
                                'group_name', 'mgi_name', 'group_no', 'group_id'
                            ] if col in merged_df.columns
                        },
                        sort_by=amount_col,
                        sort_ascending=False
                    )
                    
                    if groupby_result['status'] == 'success':
                        pivot_df = groupby_result['grouped_df']
                        
                        # Rename columns for clarity
                        column_mapping = {
                            amount_col: 'total_amount',
                            f'{count_col}_count': 'transaction_count',
                            'reconciliation_status_first': 'status',
                            'member_name_first': 'member_name',
                            'branch_name_first': 'branch_name'
                        }
                        
                        # Add group-related column mappings if they exist in pivot_df
                        if 'group_name_first' in pivot_df.columns:
                            column_mapping['group_name_first'] = 'group_name'
                        if 'mgi_name_first' in pivot_df.columns:
                            column_mapping['mgi_name_first'] = 'group_name_demand'
                        if 'group_no_first' in pivot_df.columns:
                            column_mapping['group_no_first'] = 'group_no'
                        if 'group_id_first' in pivot_df.columns:
                            column_mapping['group_id_first'] = 'group_id'
                        
                        # Apply renaming for existing columns
                        existing_columns = {old: new for old, new in column_mapping.items() if old in pivot_df.columns}
                        if existing_columns:
                            pivot_df = pivot_df.rename(columns=existing_columns)
                        
                        # Add percentage calculation
                        if 'total_amount' in pivot_df.columns:
                            pivot_df['amount_percentage'] = (pivot_df['total_amount'] / pivot_df['total_amount'].sum() * 100).round(2)
                        
                        result = {
                            'status': 'success',
                            'pivot_data': pivot_df,
                            'summary_stats': {
                                'total_unique_loans': len(pivot_df),
                                'total_transactions': groupby_result['group_stats']['original_rows'],
                                'total_amount': pivot_df['total_amount'].sum() if 'total_amount' in pivot_df.columns else 0,
                                'matched_loans': len(pivot_df[pivot_df.get('status', '').str.contains('MATCHED', na=False)]) if 'status' in pivot_df.columns else 0,
                                'unmatched_loans': len(pivot_df[pivot_df.get('status', '').str.contains('UNMATCHED', na=False)]) if 'status' in pivot_df.columns else 0
                            },
                            'debug_info': {
                                'amount_column': amount_col,
                                'reference_id_column': ref_id_col,
                                'groupby_method': 'DataFrameGroupBy.dynamic_groupby'
                            }
                        }
                        
                        print(f"✅ Pivot table created successfully!")
                        print(f"   • {result['summary_stats']['total_unique_loans']} unique loan IDs")
                        print(f"   • {result['summary_stats']['total_transactions']} total transactions")
                        print(f"   • Total amount: {result['summary_stats']['total_amount']:,.2f}")
                        
                    else:
                        result['debug_info']['error_message'] = f"GroupBy operation failed: {groupby_result.get('error_message', 'Unknown error')}"
                else:
                    result['debug_info']['error_message'] = f"Required columns not found. Amount: {amount_col}, Reference: {ref_id_col}"
            else:
                result['debug_info']['error_message'] = "Merged data not available or merge failed"
                
        except Exception as e:
            result['debug_info']['error_message'] = f"Error creating pivot table: {str(e)}"
            
        return result
    
    def _get_sib_merge_column(self, sib_df):
        """Get the merge column from SIB QR Report DataFrame - handles calc_ prefixed columns"""
        if sib_df is None or sib_df.empty:
            return None
            
        # Common patterns for loan ID in SIB reports
        # Priority: cleaned columns first, then raw columns
        loan_id_patterns = ['calc_reference_id_clean', 'reference_id_clean', 
                           'referenceID', 'reference_id', 'loan_id', 'loanid', 'lan_id', 'lanid']
        
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
        """Get the merge column from Demand Report DataFrame - handles calc_ prefixed columns"""
        if demand_df is None or demand_df.empty:
            return None
            
        # Common patterns for loan ID in demand reports
        # Priority: cleaned columns first, then raw columns
        loan_id_patterns = ['calc_loan_id_clean', 'loan_id_clean', 
                           'loan_id', 'loanid', 'lan_id', 'lanid', 'loan_no', 'account_no']
        
        for pattern in loan_id_patterns:
            matching_cols = [col for col in demand_df.columns if pattern.lower() in col.lower()]
            if matching_cols:
                return matching_cols[0]
        
        # Fallback: look for any column with 'id' or 'no' in name
        id_columns = [col for col in demand_df.columns if any(term in col.lower() for term in ['id', 'no'])]
        if id_columns:
            return id_columns[0]
            
        return None
    
    def merge_pivot_tables(self, bank_pivot_result, merged_pivot_result):
        """
        Merge two pivot tables (Bank Ledger + SIB QR/Demand) with reference to loan_id
        Rename amount columns as 'system_amount' and 'qr_amount'
        """
        print(f"🔗 Merging Bank Ledger and SIB QR/Demand pivot tables...")
        
        result = {
            'status': 'failed',
            'merged_pivot_data': None,
            'reconciliation_summary': {},
            'debug_info': {}
        }
        
        try:
            if (bank_pivot_result['status'] == 'success' and 
                merged_pivot_result['status'] == 'success' and
                bank_pivot_result.get('pivot_data') is not None and
                merged_pivot_result.get('pivot_data') is not None):
                
                bank_pivot_df = bank_pivot_result['pivot_data'].copy()
                merged_pivot_df = merged_pivot_result['pivot_data'].copy()
                
                # Rename amount columns for clarity
                if 'total_amount' in bank_pivot_df.columns:
                    bank_pivot_df = bank_pivot_df.rename(columns={'total_amount': 'system_amount'})
                
                if 'total_amount' in merged_pivot_df.columns:
                    merged_pivot_df = merged_pivot_df.rename(columns={'total_amount': 'qr_amount'})
                
                # Find the loan_id column in both DataFrames
                bank_loan_col = self._find_loan_id_column(bank_pivot_df)
                merged_loan_col = self._find_loan_id_column(merged_pivot_df)
                
                if bank_loan_col and merged_loan_col:
                    # Perform LEFT JOIN to prioritize bank ledger records
                    merged_pivot_comparison = self.merger.dynamic_merge(
                        left_df=bank_pivot_df,
                        right_df=merged_pivot_df,
                        left_column=bank_loan_col,
                        right_column=merged_loan_col,
                        how='left',  # LEFT JOIN to keep all bank transactions
                        validate_data=True
                    )
                    
                    if merged_pivot_comparison['status'] == 'success':
                        comparison_df = merged_pivot_comparison['merged_df']
                        
                        # Add reconciliation analysis columns
                        comparison_df['system_amount'] = comparison_df['system_amount'].fillna(0)
                        comparison_df['qr_amount'] = comparison_df['qr_amount'].fillna(0)
                        
                        # Calculate differences and reconciliation status
                        comparison_df['amount_difference'] = comparison_df['system_amount'] - comparison_df['qr_amount']
                        comparison_df['abs_difference'] = comparison_df['amount_difference'].abs()
                        
                        # Determine reconciliation status - strict banking standards
                        def get_reconciliation_status(row):
                            system_amt = row['system_amount']
                            qr_amt = row['qr_amount']  # Will be 0 if loan not in SIB QR
                            difference = system_amt - qr_amt
                            
                            # IMPORTANT: If QR amount is 0 but system has amount,
                            # this means loan is NOT in SIB QR report - mark as NO QR COLLECTION
                            if system_amt > 0 and qr_amt == 0:
                                return "MISMATCH - No QR Collection"
                            elif system_amt == 0 and qr_amt > 0:
                                return "MISMATCH - No System Entry"
                            elif system_amt == 0 and qr_amt == 0:
                                return "MISMATCH - No Data"  # Should not happen normally
                            elif difference == 0:
                                return "MATCHED - Perfect Match"
                            elif abs(difference) == 1 or abs(difference) == 2:  # STRICTLY only ±1, ±2 allowed
                                return "MATCHED - Minor Difference"
                            else:
                                return "MISMATCH - Amount Difference"
                        
                        comparison_df['reconciliation_status'] = comparison_df.apply(get_reconciliation_status, axis=1)
                        
                        # Calculate summary statistics - simple system vs QR comparison
                        total_loans = len(comparison_df)
                        perfect_matches = len(comparison_df[comparison_df['reconciliation_status'] == 'MATCHED - Perfect Match'])
                        minor_matches = len(comparison_df[comparison_df['reconciliation_status'] == 'MATCHED - Minor Difference'])
                        mismatches = len(comparison_df[comparison_df['reconciliation_status'] == 'MISMATCH - Amount Difference'])
                        
                        # Total matches (including test tolerance)
                        total_matches = perfect_matches + minor_matches
                        
                        # Count records with/without QR amounts for analysis
                        records_with_qr = len(comparison_df[comparison_df['qr_amount'] > 0])
                        records_without_qr = len(comparison_df[comparison_df['qr_amount'] == 0])
                        
                        total_system_amount = comparison_df['system_amount'].sum()
                        total_qr_amount = comparison_df['qr_amount'].sum()
                        total_difference = total_system_amount - total_qr_amount
                        
                        reconciliation_summary = {
                            'total_unique_loans': total_loans,
                            'perfect_matches': perfect_matches,
                            'minor_matches': minor_matches,
                            'total_matches': total_matches,
                            'amount_mismatches': mismatches,
                            'records_with_qr': records_with_qr,
                            'records_without_qr': records_without_qr,
                            'match_percentage': (total_matches / total_loans * 100) if total_loans > 0 else 0,
                            'total_system_amount': total_system_amount,
                            'total_qr_amount': total_qr_amount,
                            'net_difference': total_difference,
                            'absolute_difference': abs(total_difference)
                        }
                        
                        result = {
                            'status': 'success',
                            'merged_pivot_data': comparison_df,
                            'reconciliation_summary': reconciliation_summary,
                            'simplified_report': self._create_simplified_final_report(comparison_df),
                            'debug_info': {
                                'bank_pivot_loans': len(bank_pivot_df),
                                'qr_pivot_loans': len(merged_pivot_df),
                                'total_comparison_loans': total_loans,
                                'merge_method': 'DataFrameMerger.dynamic_merge with LEFT JOIN',
                                'amount_columns': {'system': 'system_amount', 'qr': 'qr_amount'}
                            }
                        }
                        
                        print(f"✅ Pivot tables merged successfully!")
                        print(f"   • Total unique loans: {total_loans}")
                        print(f"   • Perfect matches: {perfect_matches}")
                        print(f"   • Minor differences (±1,±2): {minor_matches}")
                        print(f"   • Total matches: {total_matches} ({total_matches/total_loans*100:.1f}%)")
                        print(f"   • Records with QR amounts: {records_with_qr}")
                        print(f"   • Records without QR amounts: {records_without_qr}")
                        print(f"   • Amount mismatches: {mismatches}")
                        print(f"   • Net difference: {total_difference:,.2f}")
                        
                    else:
                        result['debug_info']['error_message'] = f"Merge operation failed: {merged_pivot_comparison.get('error_message', 'Unknown error')}"
                else:
                    result['debug_info']['error_message'] = f"Loan ID columns not found. Bank: {bank_loan_col}, QR: {merged_loan_col}"
            else:
                result['debug_info']['error_message'] = "One or both pivot table operations failed"
                
        except Exception as e:
            result['debug_info']['error_message'] = f"Error merging pivot tables: {str(e)}"
            
        return result
    
    def extract_mismatched_entries(self, reconciliation_result):
        """
        Extract and analyze mismatched entries from reconciliation result
        Returns detailed breakdown of different types of mismatches
        """
        print(f"🔍 Extracting mismatched entries for detailed analysis...")
        
        result = {
            'status': 'failed',
            'mismatched_entries': None,
            'mismatch_breakdown': {},
            'summary_stats': {},
            'debug_info': {}
        }
        
        try:
            if (reconciliation_result['status'] == 'success' and 
                reconciliation_result.get('merged_pivot_data') is not None):
                
                full_df = reconciliation_result['merged_pivot_data'].copy()
                
                # DEBUG: Show what statuses exist in the data
                print(f"\n🔍 DEBUG - Reconciliation Status Distribution:")
                if 'reconciliation_status' in full_df.columns:
                    status_counts = full_df['reconciliation_status'].value_counts()
                    for status, count in status_counts.items():
                        print(f"   • {status}: {count}")
                
                # Extract different types of mismatched entries
                # Use string matching to capture all matched records (including Phase 3 and Stage 2)
                perfect_matches = full_df[full_df['reconciliation_status'] == 'MATCHED - Perfect Match'].copy()
                minor_matches = full_df[full_df['reconciliation_status'] == 'MATCHED - Minor Difference'].copy()
                
                # Capture all other matched records (Phase 3, Stage 2, etc.)
                other_matched = full_df[
                    (full_df['reconciliation_status'].str.contains('MATCHED', na=False)) & 
                    (~full_df['reconciliation_status'].isin(['MATCHED - Perfect Match', 'MATCHED - Minor Difference']))
                ].copy()
                
                # Extract mismatches - only records that contain 'MISMATCH' or 'ONLY'
                amount_mismatches = full_df[full_df['reconciliation_status'] == 'MISMATCH - Amount Difference'].copy()
                bank_only = full_df[full_df['reconciliation_status'] == 'BANK_ONLY - No QR Collection'].copy()
                qr_only = full_df[full_df['reconciliation_status'] == 'QR_ONLY - No Bank Entry'].copy()
                
                # DEBUG: Verify the counts
                print(f"\n🔍 DEBUG - Extracted Breakdown Counts:")
                print(f"   • amount_mismatches DataFrame: {len(amount_mismatches)} rows")
                print(f"   • other_matched DataFrame: {len(other_matched)} rows")
                print(f"   • bank_only DataFrame: {len(bank_only)} rows")
                print(f"   • qr_only DataFrame: {len(qr_only)} rows")
                
                # Add additional analysis columns to mismatched entries
                if not amount_mismatches.empty:
                    amount_mismatches['difference_category'] = amount_mismatches['amount_difference'].apply(
                        lambda x: 'High Difference (>10)' if abs(x) > 10 
                                else 'Medium Difference (4-10)' if abs(x) > 3 
                                else 'Low Difference (<4)'
                    )
                    amount_mismatches['system_higher'] = amount_mismatches['amount_difference'] > 0
                
                # Create mismatch breakdown
                mismatch_breakdown = {
                    'perfect_matches': {
                        'count': len(perfect_matches),
                        'data': perfect_matches,
                        'total_system_amount': perfect_matches['system_amount'].sum() if not perfect_matches.empty else 0,
                        'total_qr_amount': perfect_matches['qr_amount'].sum() if not perfect_matches.empty else 0
                    },
                    'minor_matches': {
                        'count': len(minor_matches),
                        'data': minor_matches,
                        'total_system_amount': minor_matches['system_amount'].sum() if not minor_matches.empty else 0,
                        'total_qr_amount': minor_matches['qr_amount'].sum() if not minor_matches.empty else 0,
                        'total_difference': minor_matches['amount_difference'].sum() if not minor_matches.empty else 0
                    },
                    'other_matches': {
                        'count': len(other_matched),
                        'data': other_matched,
                        'total_system_amount': other_matched['system_amount'].sum() if not other_matched.empty else 0,
                        'total_qr_amount': other_matched['qr_amount'].sum() if not other_matched.empty else 0,
                        'total_difference': other_matched['amount_difference'].sum() if not other_matched.empty else 0,
                        'description': 'Phase 3, Stage 2, and other advanced matches'
                    },
                    'amount_mismatches': {
                        'count': len(amount_mismatches),
                        'data': amount_mismatches,
                        'total_system_amount': amount_mismatches['system_amount'].sum() if not amount_mismatches.empty else 0,
                        'total_qr_amount': amount_mismatches['qr_amount'].sum() if not amount_mismatches.empty else 0,
                        'total_difference': amount_mismatches['amount_difference'].sum() if not amount_mismatches.empty else 0,
                        'avg_difference': amount_mismatches['amount_difference'].mean() if not amount_mismatches.empty else 0
                    },
                    'bank_only': {
                        'count': len(bank_only),
                        'data': bank_only,
                        'total_amount': bank_only['system_amount'].sum() if not bank_only.empty else 0
                    },
                    'qr_only': {
                        'count': len(qr_only),
                        'data': qr_only,
                        'total_amount': qr_only['qr_amount'].sum() if not qr_only.empty else 0
                    }
                }
                
                # Overall summary statistics
                summary_stats = {
                    'total_entries': len(full_df),
                    'total_matched': len(perfect_matches) + len(minor_matches) + len(other_matched),
                    'total_mismatched': len(amount_mismatches) + len(bank_only) + len(qr_only),
                    'match_percentage': ((len(perfect_matches) + len(minor_matches) + len(other_matched)) / len(full_df) * 100) if len(full_df) > 0 else 0,
                    'mismatch_percentage': ((len(amount_mismatches) + len(bank_only) + len(qr_only)) / len(full_df) * 100) if len(full_df) > 0 else 0,
                    'system_higher_count': len(amount_mismatches[amount_mismatches['amount_difference'] > 0]) if not amount_mismatches.empty else 0,
                    'qr_higher_count': len(amount_mismatches[amount_mismatches['amount_difference'] < 0]) if not amount_mismatches.empty else 0
                }
                
                result = {
                    'status': 'success',
                    'mismatched_entries': amount_mismatches,  # Main mismatched entries
                    'mismatch_breakdown': mismatch_breakdown,
                    'summary_stats': summary_stats,
                    'debug_info': {
                        'minor_difference_tolerance': 3,
                        'extraction_method': 'reconciliation_status_filtering',
                        'categories_extracted': list(mismatch_breakdown.keys())
                    }
                }
                
                print(f"✅ Mismatch analysis completed!")
                print(f"   • Total entries: {summary_stats['total_entries']}")
                print(f"   • Perfect matches: {mismatch_breakdown['perfect_matches']['count']}")
                print(f"   • Minor matches: {mismatch_breakdown['minor_matches']['count']} (tolerance: ±3)")
                print(f"   • Other matches: {mismatch_breakdown['other_matches']['count']} (Phase 3, Stage 2)")
                print(f"   • Amount mismatches: {mismatch_breakdown['amount_mismatches']['count']}")
                print(f"   • Bank only: {mismatch_breakdown['bank_only']['count']}")
                print(f"   • QR only: {mismatch_breakdown['qr_only']['count']}")
                print(f"   • Match rate: {summary_stats['match_percentage']:.1f}%")
                
            else:
                result['debug_info']['error_message'] = "Invalid reconciliation result provided"
                
        except Exception as e:
            result['debug_info']['error_message'] = f"Error extracting mismatched entries: {str(e)}"
            
        return result
    
    def _find_loan_id_column(self, df):
        """Find loan_id column in DataFrame - handles calc_ prefixed columns"""
        # Priority 1: Standard loan_id (already renamed from calc_loan_id in pivot)
        # Priority 2: Cleaned columns (calc_loan_id_clean, loan_id_clean)
        # Priority 3: Other variations
        loan_id_patterns = ['loan_id', 'calc_loan_id_clean', 'loan_id_clean', 
                           'calc_reference_id_clean', 'reference_id_clean',
                           'reference_id', 'referenceID', 'loanid', 'lan_id', 'lanid']
        
        for pattern in loan_id_patterns:
            matching_cols = [col for col in df.columns if pattern.lower() in col.lower()]
            if matching_cols:
                return matching_cols[0]
        
        return None
    
    def _find_amount_column(self, df):
        """Find amount column in DataFrame - for SIB QR merged data
        
        IMPORTANT: Only use SIB QR amount columns, NOT Demand Report amounts!
        Demand Report is only for enrichment (group/branch info), not amounts.
        """
        # ONLY use SIB QR amount columns - DO NOT fall back to demand report amounts!
        # The order matters - check most specific patterns first
        sib_qr_amount_patterns = [
            'amount',           # SIB QR Report amount
            'txn_amount',       # Transaction amount from SIB
            'transaction_amount',
            'value',            # Generic value from SIB
        ]
        
        # Patterns to EXCLUDE (Demand Report columns)
        exclude_patterns = ['mldi', 'demand', 'outstanding', 'balance', 'mls']
        
        for pattern in sib_qr_amount_patterns:
            matching_cols = [col for col in df.columns if pattern.lower() in col.lower()]
            # Filter out demand report columns
            matching_cols = [col for col in matching_cols 
                           if not any(excl in col.lower() for excl in exclude_patterns)]
            if matching_cols:
                return matching_cols[0]
        
        print(f"   ⚠️ WARNING: No SIB QR amount column found! QR amounts will be 0.")
        return None
    
    def _find_reference_id_column(self, df):
        """Find reference ID column in DataFrame - handles calc_ prefixed columns"""
        # Priority 1: Look for cleaned/calculated columns (calc_reference_id_clean, reference_id_clean)
        ref_patterns = ['reference_id_clean', 'calc_reference_id_clean', 'loan_id_clean', 'calc_loan_id_clean',
                       'reference_id', 'referenceID', 'loan_id', 'loanid', 'lan_id', 'lanid']
        
        for pattern in ref_patterns:
            matching_cols = [col for col in df.columns if pattern.lower() in col.lower()]
            if matching_cols:
                return matching_cols[0]
        
        return None
    
    def _create_simplified_final_report(self, merged_df):
        """Create simplified final report with only essential columns"""
        try:
            if merged_df is None or merged_df.empty:
                return None
            
            # Essential columns mapping
            simplified_columns = {
                'loan_id': 'loan_id',
                'customer_name': 'customer_name', 
                'group_id': 'group_id',
                'branch': 'branch_name',
                'system_entry': 'system_amount',
                'qr_collection': 'qr_amount', 
                'difference': 'amount_difference'
            }
            
            # Build the simplified DataFrame
            simplified_data = {}
            
            # Map existing columns to simplified structure
            for simple_col, source_col in simplified_columns.items():
                if source_col in merged_df.columns:
                    simplified_data[simple_col] = merged_df[source_col]
                else:
                    # Handle missing columns with fallbacks
                    if simple_col == 'customer_name' and 'member_name' in merged_df.columns:
                        simplified_data[simple_col] = merged_df['member_name']
                    elif simple_col == 'group_id' and 'group_name' in merged_df.columns:
                        simplified_data[simple_col] = merged_df['group_name']
                    elif simple_col == 'branch' and 'branch_name_left' in merged_df.columns:
                        simplified_data[simple_col] = merged_df['branch_name_left']
                    elif simple_col == 'system_entry' and 'system_amount' not in merged_df.columns:
                        # Try alternative amount columns
                        amount_cols = ['total_amount', 'amount', 'debit', 'credit']
                        for col in amount_cols:
                            if col in merged_df.columns:
                                simplified_data[simple_col] = merged_df[col]
                                break
                        else:
                            simplified_data[simple_col] = 0
                    elif simple_col == 'qr_collection' and 'qr_amount' not in merged_df.columns:
                        simplified_data[simple_col] = 0
                    elif simple_col == 'difference' and 'amount_difference' not in merged_df.columns:
                        # Calculate difference if not available
                        system_amt = simplified_data.get('system_entry', 0)
                        qr_amt = simplified_data.get('qr_collection', 0)
                        if isinstance(system_amt, pd.Series) and isinstance(qr_amt, pd.Series):
                            simplified_data[simple_col] = system_amt - qr_amt
                        else:
                            simplified_data[simple_col] = 0
                    else:
                        # Default empty values
                        simplified_data[simple_col] = None
            
            # Create simplified DataFrame
            simplified_df = pd.DataFrame(simplified_data)
            
            # Clean up data types and formatting
            if 'system_entry' in simplified_df.columns:
                simplified_df['system_entry'] = pd.to_numeric(simplified_df['system_entry'], errors='coerce').fillna(0)
            if 'qr_collection' in simplified_df.columns:
                simplified_df['qr_collection'] = pd.to_numeric(simplified_df['qr_collection'], errors='coerce').fillna(0)
            if 'difference' in simplified_df.columns:
                simplified_df['difference'] = pd.to_numeric(simplified_df['difference'], errors='coerce').fillna(0)
            
            # Add reconciliation status for easier filtering
            if 'reconciliation_status' in merged_df.columns:
                simplified_df['status'] = merged_df['reconciliation_status']
            
            return simplified_df
            
        except Exception as e:
            logging.error(f"Error creating simplified report: {e}", exc_info=True)
            return None