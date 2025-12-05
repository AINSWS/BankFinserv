"""
Modular Bank Reconciliation Engine - Main orchestrator for all reconciliation operations
"""

import pandas as pd
import sys
import os
from typing import Dict, Any

# Add processor and analyzer directories to path
current_dir = os.path.dirname(__file__)
sys.path.append(os.path.join(current_dir, 'processors'))
sys.path.append(os.path.join(current_dir, 'analyzers'))
sys.path.append(os.path.join(current_dir, 'exporters'))

# Import with fallback for both PyInstaller and normal execution
try:
    from src.reconciliation.processors.bank_ledger_processor import BankLedgerProcessor
    from src.reconciliation.processors.sib_qr_processor import SIBQRProcessor
    from src.reconciliation.processors.demand_report_processor import DemandReportProcessor
    from src.reconciliation.processors.merge_operations import MergeOperationsHandler
    from src.reconciliation.analyzers.match_finder import MatchFinder
    from src.reconciliation.exporters.export_manager import ExportManager
    from src.reconciliation.processors.phase3_processor import Phase3ReconciliationProcessor
except ModuleNotFoundError:
    from processors.bank_ledger_processor import BankLedgerProcessor
    from processors.sib_qr_processor import SIBQRProcessor
    from processors.demand_report_processor import DemandReportProcessor
    from processors.merge_operations import MergeOperationsHandler
    from analyzers.match_finder import MatchFinder
    from exporters.export_manager import ExportManager
    from processors.phase3_processor import Phase3ReconciliationProcessor

class ModularReconciliationEngine:
    """
    Modular Bank Reconciliation Engine - Main orchestrator
    
    This class coordinates all reconciliation operations using specialized processors:
    - BankLedgerProcessor: Handles bank ledger data processing
    - SIBQRProcessor: Handles SIB QR report processing
    - DemandReportProcessor: Handles demand report processing
    - MergeOperationsHandler: Handles merge operations
    - MatchFinder: Handles transaction matching
    - ExportManager: Handles all export operations
    """
    
    def __init__(self, bank_ledger_df, sib_qr_df, demand_report_df):
        """
        Initialize the modular reconciliation engine
        
        Args:
            bank_ledger_df: Bank ledger DataFrame (Sheet 1)
            sib_qr_df: SIB QR Report DataFrame (Sheet 2)
            demand_report_df: Demand Report DataFrame (Sheet 3)
        """
        # Store original DataFrames
        self.bank_ledger_df = bank_ledger_df
        self.sib_qr_df = sib_qr_df
        self.demand_report_df = demand_report_df
        
        # Initialize processors
        self.bank_processor = BankLedgerProcessor(bank_ledger_df)
        self.sib_processor = SIBQRProcessor(sib_qr_df)
        self.demand_processor = DemandReportProcessor(demand_report_df)
        self.merge_handler = MergeOperationsHandler()
        self.match_finder = MatchFinder()
        self.export_manager = ExportManager()
        self.phase3_processor = Phase3ReconciliationProcessor()
        
        # Cache for reconciliation results (to avoid re-running Phase 3)
        self._cached_reconciliation_result = None
    
    # Bank Ledger Operations
    def extract_bank_ledger_data(self):
        """Process bank ledger data using BankLedgerProcessor"""
        return self.bank_processor.extract_bank_ledger_data()
    
    def create_bank_ledger_pivot_table(self):
        """Create pivot table for bank ledger data"""
        return self.bank_processor.create_bank_ledger_pivot_table()
    
    # SIB QR Report Operations
    def analyze_sib_qr_report(self):
        """Analyze SIB QR report using SIBQRProcessor"""
        return self.sib_processor.analyze_sib_qr_report()
    
    # Demand Report Operations
    def analyze_demand_report(self):
        """Analyze demand report using DemandReportProcessor"""
        return self.demand_processor.analyze_demand_report()
    
    # Merge Operations
    def merge_sib_qr_with_demand_report(self):
        """Merge SIB QR and Demand Report using MergeOperationsHandler"""
        sib_analysis = self.analyze_sib_qr_report()
        demand_analysis = self.analyze_demand_report()
        return self.merge_handler.merge_sib_qr_with_demand_report(sib_analysis, demand_analysis)
    
    def create_merged_data_pivot_table(self):
        """Create pivot table from merged SIB QR + Demand Report data"""
        merged_result = self.merge_sib_qr_with_demand_report()
        return self.merge_handler.create_merged_data_pivot_table(merged_result)
    
    def merge_pivot_tables_comparison(self, include_stage2=True, include_phase3=True):
        """
        Merge Bank Ledger pivot with SIB QR/Demand pivot for reconciliation comparison
        Implements sequential processing:
        1. Stage 1: Initial matching
        2. Stage 2: Group payment processing on mismatches from Stage 1
        3. Stage 3: Advanced matching on remaining mismatches from Stage 2
        
        Args:
            include_stage2: Whether to include Stage 2 group payment processing
            include_phase3: Whether to include Phase 3 bank ledger narration analysis
        """
        try:
            print("\n🔄 Starting Stage 1: Initial Matching...")
            
            # Get both pivot tables
            bank_pivot = self.create_bank_ledger_pivot_table()
            merged_pivot = self.create_merged_data_pivot_table()
            
            # Stage 1: Initial matching using MergeOperationsHandler
            result = self.merge_handler.merge_pivot_tables(bank_pivot, merged_pivot)
            
            if result.get('status') != 'success':
                return result
                
            main_data = result.get('merged_pivot_data')
            if main_data is None or main_data.empty:
                return result
                
            # Get status column name
            status_col = 'reconciliation_status' if 'reconciliation_status' in main_data.columns else 'status'
            
            # Extract mismatches from Stage 1
            stage1_mismatches = main_data[
                main_data[status_col].str.contains('MISMATCH', na=False)
            ].copy()
            
            print(f"✅ Stage 1 Complete - Found {len(stage1_mismatches)} mismatches out of {len(main_data)} total records")
            
            # Stage 2: Group payment processing on mismatches from Stage 1
            if include_stage2 and not stage1_mismatches.empty:
                # Rename columns for Stage 2 processing
                stage1_mismatches = stage1_mismatches.rename(columns={
                    'system_amount': 'system_entry',
                    'qr_amount': 'qr_collection',
                    'group_name': 'group_id'
                })
                
                stage2_result = self.process_stage2_group_payments(stage1_mismatches)
                
                if stage2_result.get('status') == 'success':
                    # Update main data with Stage 2 results
                    newly_matched = stage2_result.get('newly_matched', pd.DataFrame())
                    remaining_mismatches = stage2_result.get('remaining_mismatched', pd.DataFrame())
                    
                    if not newly_matched.empty:
                        # Make sure all needed columns exist
                        required_cols = ['loan_id', 'status', 'qr_collection', 'system_entry', 'difference']
                        if all(col in newly_matched.columns for col in required_cols):
                            # Update matched records in main data
                            for idx, row in newly_matched.iterrows():
                                mask = main_data['loan_id'] == row['loan_id']
                                if any(mask):
                                    # Update the status first
                                    main_data.loc[mask, status_col] = row['status']
                                    
                                    # Update all numeric and relevant columns
                                    for col in ['qr_collection', 'system_entry', 'difference', 'match_type', 'notes']:
                                        if col in row and col in main_data.columns:
                                            main_data.loc[mask, col] = row[col]
                    
                    # Store Stage 2 results
                    result['stage2_results'] = stage2_result
                    
                    # Pass remaining mismatches to Stage 3
                    stage3_input = remaining_mismatches
                else:
                    stage3_input = stage1_mismatches
            else:
                stage3_input = stage1_mismatches
            
            # Stage 3: Advanced matching on remaining mismatches
            phase3_applied = False
            if include_phase3 and not stage3_input.empty:
                print("\n🔄 Starting Stage 3: Advanced Matching...")
                result = self._apply_phase3_to_main_data(result, stage3_input)
                phase3_applied = True
            
            # Update final statistics using the potentially Phase 3-updated data
            final_data = result.get('merged_pivot_data', main_data)
            if 'reconciliation_summary' in result:
                summary = result['reconciliation_summary']
                total_matches = len(final_data[~final_data[status_col].str.contains('MISMATCH', na=False)])
                total_records = len(final_data)
                
                if total_records > 0:
                    match_rate = (total_matches / total_records) * 100
                    summary.update({
                        'total_matches': total_matches,
                        'match_percentage': match_rate
                    })
            
            # Store final data (only if Phase 3 didn't already update it)
            if not phase3_applied:
                result['merged_pivot_data'] = main_data
            
            # IMPORTANT: Cache the result to avoid re-running Phase 3 during export
            self._cached_reconciliation_result = result
            
            return result
            
        except Exception as e:
            print(f"❌ Error in reconciliation process: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'failed',
                'message': f'Error in reconciliation process: {str(e)}',
                'merged_pivot_data': None
            }
    
    def extract_mismatched_analysis(self):
        """
        Perform complete reconciliation analysis with separate mismatched entries extraction
        Enhanced with ±3 tolerance for minor differences
        
        IMPORTANT: Uses cached reconciliation result to preserve Phase 3 updates
        """
        print(f"🔍 Performing complete reconciliation analysis with mismatch extraction...")
        
        result = {
            'status': 'failed',
            'reconciliation_data': None,
            'mismatched_analysis': None,
            'summary_stats': {},
            'debug_info': {}
        }
        
        try:
            # CRITICAL FIX: Use cached result if available to preserve Phase 3 updates
            # Otherwise Phase 3 matches get lost when we re-run reconciliation
            if self._cached_reconciliation_result is not None:
                print(f"   ✓ Using cached reconciliation result (preserves Phase 3 updates)")
                pivot_comparison = self._cached_reconciliation_result
            else:
                print(f"   ⚠️ No cached result, running fresh reconciliation")
                pivot_comparison = self.merge_pivot_tables_comparison()
            
            if pivot_comparison['status'] == 'success':
                # Extract mismatched entries for detailed analysis
                mismatched_analysis = self.merge_handler.extract_mismatched_entries(pivot_comparison)
                
                result = {
                    'status': 'success',
                    'reconciliation_data': pivot_comparison,
                    'mismatched_analysis': mismatched_analysis,
                    'summary_stats': {
                        'total_loans': pivot_comparison['reconciliation_summary']['total_unique_loans'],
                        'perfect_matches': pivot_comparison['reconciliation_summary']['perfect_matches'],
                        'minor_matches': pivot_comparison['reconciliation_summary']['minor_matches'],
                        'amount_mismatches': pivot_comparison['reconciliation_summary']['amount_mismatches'],
                        'match_percentage': pivot_comparison['reconciliation_summary']['match_percentage'],
                        'net_amount_difference': pivot_comparison['reconciliation_summary']['net_amount_difference']
                    },
                    'debug_info': {
                        'minor_difference_tolerance': 3,
                        'reconciliation_method': 'OUTER JOIN with enhanced tolerance',
                        'analysis_timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
                
                print(f"✅ Complete reconciliation analysis finished!")
                print(f"   • Enhanced tolerance: ±3 for minor differences")
                print(f"   • Mismatched entries extracted and categorized")
                
            else:
                result['debug_info']['error_message'] = f"Pivot comparison failed: {pivot_comparison.get('debug_info', {}).get('error_message', 'Unknown error')}"
                
        except Exception as e:
            result['debug_info']['error_message'] = f"Error in reconciliation analysis: {str(e)}"
            
        return result
    

        print(f"🔗 Merging pivot tables: Bank Ledger (Sheet 1) + SIB QR Collection (Sheet 2+3)...")
        
        result = {
            'status': 'failed',
            'merged_pivot_data': None,
            'reconciliation_stats': {},
            'debug_info': {}
        }
        
        try:
            # Get both pivot tables
            print(f"   • Getting Bank Ledger pivot table...")
            bank_pivot_result = self.create_bank_ledger_pivot_table()
            
            print(f"   • Getting Merged SIB QR + Demand pivot table...")
            collection_pivot_result = self.create_merged_data_pivot_table()
            
            if (bank_pivot_result['status'] == 'success' and 
                collection_pivot_result['status'] == 'success'):
                
                bank_pivot_df = bank_pivot_result['pivot_data'].copy()
                collection_pivot_df = collection_pivot_result['pivot_data'].copy()
                
                # Prepare bank ledger pivot (Sheet 1)
                print(f"   • Preparing Bank Ledger data (system amounts)...")
                bank_columns_to_keep = ['loan_id', 'total_amount', 'transaction_count', 'sample_description']
                bank_available_cols = [col for col in bank_columns_to_keep if col in bank_pivot_df.columns]
                
                if 'loan_id' in bank_pivot_df.columns and 'total_amount' in bank_pivot_df.columns:
                    bank_for_merge = bank_pivot_df[bank_available_cols].copy()
                    bank_for_merge = bank_for_merge.rename(columns={
                        'total_amount': 'system_amount',
                        'transaction_count': 'system_transaction_count',
                        'sample_description': 'system_description'
                    })
                    bank_for_merge['loan_id_clean'] = bank_for_merge['loan_id'].str.strip().str.upper()
                else:
                    result['debug_info']['error_message'] = f"Required columns not found in bank pivot. Available: {list(bank_pivot_df.columns)}"
                    return result
                
                # Prepare collection pivot (Sheet 2+3)  
                print(f"   • Preparing Collection data (QR amounts)...")
                
                # Find the loan ID column in collection pivot
                collection_id_col = None
                for col in collection_pivot_df.columns:
                    if any(pattern in col.lower() for pattern in ['loan_id', 'reference_id', 'ref_id']):
                        collection_id_col = col
                        break
                
                if not collection_id_col:
                    collection_id_col = collection_pivot_df.columns[0]  # Use first column as fallback
                
                collection_columns_to_keep = [collection_id_col, 'total_amount', 'transaction_count', 'status', 'member_name', 'branch_name']
                collection_available_cols = [col for col in collection_columns_to_keep if col in collection_pivot_df.columns]
                
                if collection_id_col in collection_pivot_df.columns and 'total_amount' in collection_pivot_df.columns:
                    collection_for_merge = collection_pivot_df[collection_available_cols].copy()
                    
                    # Rename columns
                    rename_mapping = {
                        'total_amount': 'qr_amount',
                        'transaction_count': 'qr_transaction_count',
                        'status': 'qr_status'
                    }
                    
                    # Only rename columns that exist
                    existing_rename = {old: new for old, new in rename_mapping.items() if old in collection_for_merge.columns}
                    collection_for_merge = collection_for_merge.rename(columns=existing_rename)
                    
                    # Standardize the ID column
                    collection_for_merge['loan_id_clean'] = collection_for_merge[collection_id_col].astype(str).str.strip().str.upper()
                    collection_for_merge = collection_for_merge.rename(columns={collection_id_col: 'original_collection_id'})
                else:
                    result['debug_info']['error_message'] = f"Required columns not found in collection pivot. Available: {list(collection_pivot_df.columns)}"
                    return result
                
                # Perform OUTER JOIN merge
                print(f"   • Performing OUTER JOIN merge on loan_id...")
                merged_pivot_df = pd.merge(
                    bank_for_merge,
                    collection_for_merge,
                    on='loan_id_clean',
                    how='outer',
                    suffixes=('_system', '_qr')
                )
                
                # Add reconciliation analysis columns
                print(f"   • Adding reconciliation analysis...")
                merged_pivot_df['system_amount'] = merged_pivot_df['system_amount'].fillna(0)
                merged_pivot_df['qr_amount'] = merged_pivot_df['qr_amount'].fillna(0)
                
                # Calculate differences and reconciliation status
                merged_pivot_df['amount_difference'] = merged_pivot_df['system_amount'] - merged_pivot_df['qr_amount']
                merged_pivot_df['amount_difference_abs'] = merged_pivot_df['amount_difference'].abs()
                merged_pivot_df['amount_match_percentage'] = merged_pivot_df.apply(
                    lambda row: 100.0 if row['system_amount'] == row['qr_amount'] == 0 
                    else (min(row['system_amount'], row['qr_amount']) / max(row['system_amount'], row['qr_amount']) * 100) 
                    if max(row['system_amount'], row['qr_amount']) > 0 else 0, axis=1
                ).round(2)
                
                # Reconciliation status
                def determine_reconciliation_status(row):
                    if row['system_amount'] == 0:
                        return 'QR ONLY - No System Record'
                    elif row['qr_amount'] == 0:
                        return 'SYSTEM ONLY - No QR Collection'
                    elif abs(row['amount_difference']) < 0.01:  # Consider floating point precision
                        return 'PERFECTLY MATCHED'
                    elif row['amount_match_percentage'] >= 95:
                        return 'CLOSELY MATCHED'
                    else:
                        return 'AMOUNT MISMATCH'
                
                merged_pivot_df['final_reconciliation_status'] = merged_pivot_df.apply(determine_reconciliation_status, axis=1)
                
                # Sort by amount difference (largest mismatches first)
                merged_pivot_df = merged_pivot_df.sort_values('amount_difference_abs', ascending=False)
                
                # Calculate reconciliation statistics
                total_records = len(merged_pivot_df)
                perfectly_matched = len(merged_pivot_df[merged_pivot_df['final_reconciliation_status'] == 'PERFECTLY MATCHED'])
                closely_matched = len(merged_pivot_df[merged_pivot_df['final_reconciliation_status'] == 'CLOSELY MATCHED'])
                system_only = len(merged_pivot_df[merged_pivot_df['final_reconciliation_status'] == 'SYSTEM ONLY - No QR Collection'])
                qr_only = len(merged_pivot_df[merged_pivot_df['final_reconciliation_status'] == 'QR ONLY - No System Record'])
                mismatched = len(merged_pivot_df[merged_pivot_df['final_reconciliation_status'] == 'AMOUNT MISMATCH'])
                
                reconciliation_stats = {
                    'total_loan_ids': total_records,
                    'perfectly_matched': perfectly_matched,
                    'closely_matched': closely_matched,
                    'system_only': system_only,
                    'qr_only': qr_only,
                    'amount_mismatched': mismatched,
                    'overall_match_rate': ((perfectly_matched + closely_matched) / total_records * 100) if total_records > 0 else 0,
                    'total_system_amount': merged_pivot_df['system_amount'].sum(),
                    'total_qr_amount': merged_pivot_df['qr_amount'].sum(),
                    'total_amount_difference': merged_pivot_df['amount_difference'].sum(),
                    'largest_difference': merged_pivot_df['amount_difference_abs'].max()
                }
                
                result = {
                    'status': 'success',
                    'merged_pivot_data': merged_pivot_df,
                    'reconciliation_stats': reconciliation_stats,
                    'debug_info': {
                        'bank_pivot_records': len(bank_pivot_df),
                        'collection_pivot_records': len(collection_pivot_df),
                        'merge_method': 'pandas.merge(how="outer")',
                        'merge_key': 'loan_id_clean',
                        'system_amount_source': 'Bank Ledger (Sheet 1)',
                        'qr_amount_source': 'SIB QR + Demand Report (Sheet 2+3)'
                    }
                }
                
                print(f"✅ Pivot tables merged successfully!")
                print(f"   • Total loan IDs: {reconciliation_stats['total_loan_ids']}")
                print(f"   • Perfectly matched: {reconciliation_stats['perfectly_matched']}")
                print(f"   • System only: {reconciliation_stats['system_only']}")
                print(f"   • QR only: {reconciliation_stats['qr_only']}")
                print(f"   • Overall match rate: {reconciliation_stats['overall_match_rate']:.2f}%")
                print(f"   • Total system amount: {reconciliation_stats['total_system_amount']:,.2f}")
                print(f"   • Total QR amount: {reconciliation_stats['total_qr_amount']:,.2f}")
                print(f"   • Amount difference: {reconciliation_stats['total_amount_difference']:,.2f}")
                
            else:
                error_msg = "Failed to create one or both pivot tables"
                if bank_pivot_result['status'] != 'success':
                    error_msg += f" - Bank pivot: {bank_pivot_result.get('debug_info', {}).get('error_message', 'Unknown error')}"
                if collection_pivot_result['status'] != 'success':
                    error_msg += f" - Collection pivot: {collection_pivot_result.get('debug_info', {}).get('error_message', 'Unknown error')}"
                result['debug_info']['error_message'] = error_msg
                
        except Exception as e:
            result['debug_info']['error_message'] = f"Error merging pivot tables: {str(e)}"
            import traceback
            result['debug_info']['traceback'] = traceback.format_exc()
        
        return result
    
    # Match Finding Operations
    def find_matching_transactions(self):
        """Find matching transactions using MatchFinder"""
        bank_analysis = self.extract_bank_ledger_data()
        sib_analysis = self.analyze_sib_qr_report()
        demand_analysis = self.analyze_demand_report()
        return self.match_finder.find_matching_transactions(bank_analysis, sib_analysis, demand_analysis)
    
    # Summary Generation
    def generate_reconciliation_summary(self):
        """Generate comprehensive reconciliation summary"""
        print("🔍 Generating comprehensive reconciliation summary...")
        
        # Get all analyses
        bank_analysis = self.extract_bank_ledger_data()
        sib_analysis = self.analyze_sib_qr_report()
        demand_analysis = self.analyze_demand_report()
        merged_sib_demand = self.merge_sib_qr_with_demand_report()
        matches = self.find_matching_transactions()
        
        # Generate summary statistics
        summary_stats = self._calculate_summary_stats(bank_analysis, sib_analysis, demand_analysis, matches)
        
        # Generate merged pivot analysis
        pivot_comparison = self.merge_pivot_tables_comparison()
        
        return {
            'bank_ledger': bank_analysis,
            'sib_qr_report': sib_analysis,
            'demand_report': demand_analysis,
            'merged_sib_demand': merged_sib_demand,
            'pivot_comparison': pivot_comparison,
            'matches': matches,
            'summary_stats': summary_stats
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
        
        if bank_analysis.get('filtered_data'):
            total_bank_filtered = bank_analysis['filtered_data']['total_rows']
            total_matches = stats['bank_sib_matches'] + stats['bank_demand_matches']
            if total_bank_filtered > 0:
                stats['match_percentage'] = (total_matches / total_bank_filtered) * 100
        
        return stats
    
    def process_stage2_group_payments(self, mismatched_data=None):
        """
        Stage 2 Reconciliation: Process group payments where one member pays for all
        
        Args:
            mismatched_data: DataFrame of mismatched records, if None will extract from current reconciliation
            
        Returns:
            Dict containing newly matched records, remaining mismatches, and analysis
        """
        print("🏪 Starting Stage 2: Group Payment Reconciliation...")
        
        try:
            # Import the group payment processor with fallback
            try:
                from src.reconciliation.processors.group_payment_processor import GroupPaymentProcessor
            except ModuleNotFoundError:
                from processors.group_payment_processor import GroupPaymentProcessor
            
            # Get mismatched data if not provided
            if mismatched_data is None:
                print("   • Extracting mismatched data from current reconciliation...")
                reconciliation_result = self.merge_pivot_tables_comparison(include_stage2=False)  # Prevent recursion
                
                if reconciliation_result.get('status') != 'success':
                    return {
                        'status': 'failed',
                        'message': 'Could not get reconciliation data for Stage 2 processing'
                    }
                
                # Extract mismatched records
                main_data = reconciliation_result.get('merged_pivot_data')
                if main_data is None or main_data.empty:
                    return {
                        'status': 'success',
                        'message': 'No data available for Stage 2 processing',
                        'newly_matched': pd.DataFrame(),
                        'remaining_mismatched': pd.DataFrame(),
                        'group_analysis': {}
                    }
                
                # Filter for mismatched records
                status_col = 'status' if 'status' in main_data.columns else 'reconciliation_status'
                mismatched_data = main_data[
                    main_data[status_col].str.contains('MISMATCH', na=False)
                ].copy()
            
            print(f"   • Found {len(mismatched_data)} mismatched records for group analysis")
            
            # Initialize group payment processor
            group_processor = GroupPaymentProcessor()
            
            # Process group payments
            result = group_processor.process_group_payments(mismatched_data)
            
            # Add summary to result
            if result['status'] == 'success':
                summary = group_processor.get_processing_summary(result)
                print(summary)
                result['summary_text'] = summary
            
            return result
            
        except Exception as e:
            error_msg = f"Error in Stage 2 group payment processing: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            return {
                'status': 'failed',
                'message': error_msg,
                'newly_matched': pd.DataFrame(),
                'remaining_mismatched': pd.DataFrame(),
                'group_analysis': {}
            }
    
    def _apply_stage2_to_main_data(self, reconciliation_result):
        """
        Apply Stage 2 group payment results to the main reconciliation data
        This updates the main dataset with redistributed amounts and new match statuses
        """
        try:
            main_data = reconciliation_result.get('merged_pivot_data')
            if main_data is None or main_data.empty:
                return reconciliation_result
            
            # Run Stage 2 processing (get mismatched data from current result to avoid recursion)
            # CRITICAL: Use reconciliation_status, not status (which is for branch info)
            if 'reconciliation_status' in main_data.columns:
                status_col = 'reconciliation_status'
                mismatched_data = main_data[
                    main_data[status_col].str.contains('MISMATCH', na=False)
                ].copy()
            else:
                # Fallback to status column if reconciliation_status doesn't exist
                status_col = 'status'
                mismatched_data = main_data[
                    main_data[status_col].str.contains('MISMATCH', na=False)
                ].copy()
            
            print(f"🔄 Processing {len(mismatched_data)} mismatched records in Stage 2...")
            
            # Add group_id column if not present (required for group processing)
            if 'group_id' not in mismatched_data.columns and 'loan_id' in mismatched_data.columns:
                mismatched_data['group_id'] = mismatched_data['loan_id'].str.extract(r'([A-Z0-9]+)_\d+')
            
            stage2_result = self.process_stage2_group_payments(mismatched_data)
            
            if stage2_result.get('status') != 'success':
                # If Stage 2 fails, return original data
                print(f"⚠️ Stage 2 processing failed: {stage2_result.get('message', 'Unknown error')}")
                return reconciliation_result
            
            newly_matched = stage2_result.get('newly_matched', pd.DataFrame())
            
            if not newly_matched.empty:
                print(f"✅ Found {len(newly_matched)} group payment matches")
                
                # Create a copy of main data for modification
                updated_main_data = main_data.copy()
                
                # Update records that were resolved in Stage 2
                for _, stage2_record in newly_matched.iterrows():
                    loan_id = stage2_record['loan_id']
                    mask = updated_main_data['loan_id'] == loan_id
                    
                    if any(mask):
                        # Keep original QR collection for audit trail
                        if 'original_qr_collection' not in updated_main_data.columns:
                            updated_main_data['original_qr_collection'] = updated_main_data['qr_collection']
                        
                        # Update all columns from stage2_record
                        for col in stage2_record.index:
                            if col in updated_main_data.columns:
                                updated_main_data.loc[mask, col] = stage2_record[col]
                        
                        # Add reconciliation method info
                        if 'reconciliation_method' not in updated_main_data.columns:
                            updated_main_data['reconciliation_method'] = None
                        updated_main_data.loc[mask, 'reconciliation_method'] = stage2_record.get('reconciliation_method', 'Stage 2: Group Payment')
                
                # Update summary statistics
                if 'reconciliation_summary' in reconciliation_result:
                    summary = reconciliation_result['reconciliation_summary']
                    group_analysis = stage2_result.get('group_analysis', {})
                    
                    # Calculate new match counts using the correct status column
                    status_col = 'status' if 'status' in updated_main_data.columns else 'reconciliation_status'
                    new_matched_count = len(updated_main_data[updated_main_data[status_col].str.contains('MATCHED', na=False)])
                    
                    # Update summary
                    total_records = summary.get('total_unique_loans', len(updated_main_data))
                    summary.update({
                        'group_matches': len(newly_matched),
                        'total_matches': new_matched_count,
                        'match_percentage': (new_matched_count / total_records * 100) if total_records > 0 else 0,
                        'groups_processed': group_analysis.get('total_groups_processed', 0),
                        'group_resolution_rate': group_analysis.get('resolution_rate', 0),
                        'group_amount_resolved': group_analysis.get('total_amount_resolved', 0)
                    })
                
                # Update result with modified data
                reconciliation_result['merged_pivot_data'] = updated_main_data
                reconciliation_result['stage2_results'] = stage2_result
                
                print(f"✅ Updated {len(newly_matched)} records with group payment redistribution")
            else:
                print("ℹ️ No group payment matches found")
            
            # Update the result with modified data
            reconciliation_result['merged_pivot_data'] = updated_main_data
            
            # CRITICAL: Also update simplified_report for export compatibility
            if 'simplified_report' in reconciliation_result:
                # Create new simplified report with Stage 2 updated data
                new_simplified_report = self.merge_handler._create_simplified_final_report(updated_main_data)
                if new_simplified_report is not None:
                    reconciliation_result['simplified_report'] = new_simplified_report
                else:
                    # Fallback: use updated main data directly
                    reconciliation_result['simplified_report'] = updated_main_data
            
            # Update summary statistics
            original_summary = reconciliation_result.get('reconciliation_summary', {})
            stage2_analysis = stage2_result.get('group_analysis', {})
            
            # Calculate new match counts using the correct status column
            if 'reconciliation_status' in updated_main_data.columns:
                calc_status_col = 'reconciliation_status'
            else:
                calc_status_col = 'status'
            
            new_matched_count = len(updated_main_data[updated_main_data[calc_status_col].str.contains('MATCHED', na=False)])
            new_mismatch_count = len(updated_main_data[updated_main_data[calc_status_col].str.contains('MISMATCH', na=False)])
            
            # Update summary
            total_records = original_summary.get('total_unique_loans', len(updated_main_data))
            if total_records > 0:
                new_match_percentage = (new_matched_count / total_records) * 100
            else:
                new_match_percentage = 0
            
            updated_summary = original_summary.copy()
            updated_summary.update({
                'total_matches': new_matched_count,
                'amount_mismatches': new_mismatch_count,
                'match_percentage': new_match_percentage,
                'stage2_groups_processed': stage2_analysis.get('matching_groups_found', 0),
                'stage2_records_resolved': len(newly_matched),
                'stage2_applied': True
            })
            
            reconciliation_result['reconciliation_summary'] = updated_summary
            reconciliation_result['stage2_result'] = stage2_result
            
            print(f"✅ Stage 2 applied: {len(newly_matched)} records updated, "
                  f"match rate improved to {new_match_percentage:.1f}%")
            
            return reconciliation_result
            
        except Exception as e:
            error_msg = f"Error applying Stage 2 to main data: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Return original result if Stage 2 application fails
            return reconciliation_result
    
    def _apply_phase3_to_main_data(self, reconciliation_result, mismatched_data=None):
        """
        Apply Phase 3 narration analysis results to the main reconciliation data
        This processes mismatched records using bank ledger credit/debit analysis
        
        Args:
            reconciliation_result: Current reconciliation result dict
            mismatched_data: Optional DataFrame of mismatches from Stage 2
                           If None, will extract mismatches from main data
        """
        try:
            main_data = reconciliation_result.get('merged_pivot_data')
            if main_data is None or main_data.empty:
                return reconciliation_result

            # Get status column name
            status_col = 'reconciliation_status' if 'reconciliation_status' in main_data.columns else 'status'
            
            # Use provided mismatches or extract from main data
            if mismatched_data is None:
                print("⚠️ No mismatched data provided from Stage 2, extracting from main data")
                mismatched_data = main_data[
                    main_data[status_col].str.contains('MISMATCH', na=False)
                ].copy()
            
            if mismatched_data.empty:
                print("ℹ️ No mismatched records for Phase 3 processing")
                return reconciliation_result
                
            print(f"🔍 Starting Phase 3 processing with {len(mismatched_data)} records")

            # Process bank ledger for Phase 3 analysis
            phase3_ledger_result = self.phase3_processor.process_bank_ledger_phase3(self.bank_ledger_df)
            
            if phase3_ledger_result.get('status') != 'success':
                print("⚠️ Phase 3 bank ledger processing failed, skipping Phase 3")
                return reconciliation_result
            
            # Run Phase 3 reconciliation on mismatched data
            phase3_recon_result = self.phase3_processor.process_phase3_reconciliation(
                mismatched_data,
                phase3_ledger_result['debit_df'],
                phase3_ledger_result['credit_df']
            )
            
            if phase3_recon_result.get('status') != 'success':
                print("⚠️ Phase 3 reconciliation failed, using original data")
                return reconciliation_result

            newly_matched = phase3_recon_result.get('newly_matched', pd.DataFrame())
            
            if newly_matched.empty:
                print("ℹ️ No additional matches found in Phase 3")
                return reconciliation_result

            print(f"🔄 Applying {len(newly_matched)} Phase 3 results to main reconciliation data...")
            
            # Create a copy of main data for modification
            updated_main_data = main_data.copy()
            
            # Update records that were resolved in Phase 3
            for _, phase3_record in newly_matched.iterrows():
                loan_id = str(phase3_record['loan_id'])  # Ensure string type
                
                # Find the matching record in main data
                mask = updated_main_data['loan_id'].astype(str) == loan_id
                matching_rows = updated_main_data[mask]
                
                if not matching_rows.empty:
                    # Update the record with Phase 3 results
                    idx = matching_rows.index[0]
                    
                    # Update BOTH status columns for export compatibility
                    phase3_status = phase3_record['status']
                    updated_main_data.loc[idx, 'status'] = phase3_status
                    updated_main_data.loc[idx, 'reconciliation_status'] = phase3_status
                    updated_main_data.loc[idx, 'reconciliation_method'] = phase3_record.get('reconciliation_method', 'Phase 3: Credit/Debit Analysis')
                    
                    # Add Phase 3 specific columns
                    if 'phase3_debit_total' in phase3_record:
                        updated_main_data.loc[idx, 'phase3_debit_total'] = phase3_record['phase3_debit_total']
                    if 'phase3_credit_total' in phase3_record:
                        updated_main_data.loc[idx, 'phase3_credit_total'] = phase3_record['phase3_credit_total']
                    if 'phase3_difference' in phase3_record:
                        updated_main_data.loc[idx, 'phase3_difference'] = phase3_record['phase3_difference']
                    if 'phase3_match_difference' in phase3_record:
                        updated_main_data.loc[idx, 'phase3_match_difference'] = phase3_record['phase3_match_difference']

            # Update the result with modified data
            reconciliation_result['merged_pivot_data'] = updated_main_data
            
            # Update simplified_report for export compatibility
            if 'simplified_report' in reconciliation_result:
                new_simplified_report = self.merge_handler._create_simplified_final_report(updated_main_data)
                if new_simplified_report is not None:
                    reconciliation_result['simplified_report'] = new_simplified_report
                else:
                    reconciliation_result['simplified_report'] = updated_main_data

            # Update summary statistics
            original_summary = reconciliation_result.get('reconciliation_summary', {})
            phase3_analysis = phase3_recon_result.get('phase3_analysis', {})
            
            # Calculate new match counts using the correct status column
            if 'reconciliation_status' in updated_main_data.columns:
                calc_status_col = 'reconciliation_status'
            else:
                calc_status_col = 'status'
            
            new_matched_count = len(updated_main_data[updated_main_data[calc_status_col].str.contains('MATCHED', na=False)])
            new_mismatch_count = len(updated_main_data[updated_main_data[calc_status_col].str.contains('MISMATCH', na=False)])
            
            # Update summary
            total_records = original_summary.get('total_unique_loans', len(updated_main_data))
            if total_records > 0:
                new_match_percentage = (new_matched_count / total_records) * 100
            else:
                new_match_percentage = 0
            
            updated_summary = original_summary.copy()
            updated_summary.update({
                'total_matches': new_matched_count,
                'amount_mismatches': new_mismatch_count,
                'match_percentage': new_match_percentage,
                'phase3_records_analyzed': phase3_analysis.get('total_analyzed', 0),
                'phase3_records_resolved': len(newly_matched),
                'phase3_resolution_rate': phase3_analysis.get('resolution_rate', 0),
                'phase3_applied': True
            })
            
            reconciliation_result['reconciliation_summary'] = updated_summary
            reconciliation_result['phase3_result'] = phase3_recon_result
            reconciliation_result['phase3_ledger_processing'] = phase3_ledger_result
            
            print(f"✅ Phase 3 applied: {len(newly_matched)} records resolved via credit/debit analysis, "
                  f"match rate improved to {new_match_percentage:.1f}%")
            
            return reconciliation_result
            
        except Exception as e:
            error_msg = f"Error applying Phase 3 to main data: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Return original result if Phase 3 application fails
            return reconciliation_result
    
    # Phase 3 Operations
    def process_phase3_reconciliation(self) -> Dict[str, Any]:
        """
        Execute Phase 3 reconciliation with narration splitting and 
        separate debit/credit loan ID extraction
        
        Returns:
            Dictionary containing debit/credit DataFrames, pivot tables, and summary
        """
        print("🚀 Starting Phase 3: Advanced Bank Ledger Reconciliation...")
        
        try:
            # Process bank ledger with Phase 3 logic
            phase3_result = self.phase3_processor.process_bank_ledger_phase3(self.bank_ledger_df)
            
            if phase3_result['status'] == 'success':
                # Display summary
                summary_text = self.phase3_processor.get_phase3_summary(phase3_result)
                print(summary_text)
            
            return phase3_result
            
        except Exception as e:
            error_msg = f"Error in Phase 3 reconciliation: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'debit_df': pd.DataFrame(),
                'credit_df': pd.DataFrame(),
                'debit_pivot': pd.DataFrame(),
                'credit_pivot': pd.DataFrame(),
                'processing_summary': {}
            }
    
    def get_phase3_debit_data(self) -> pd.DataFrame:
        """Get Phase 3 debit transactions DataFrame"""
        result = self.process_phase3_reconciliation()
        return result.get('debit_df', pd.DataFrame())
    
    def get_phase3_credit_data(self) -> pd.DataFrame:
        """Get Phase 3 credit transactions DataFrame"""
        result = self.process_phase3_reconciliation()
        return result.get('credit_df', pd.DataFrame())
    
    def get_phase3_debit_pivot(self) -> pd.DataFrame:
        """Get Phase 3 debit pivot table (loan_id grouped with sum)"""
        result = self.process_phase3_reconciliation()
        return result.get('debit_pivot', pd.DataFrame())
    
    def get_phase3_credit_pivot(self) -> pd.DataFrame:
        """Get Phase 3 credit pivot table (loan_id grouped with sum)"""
        result = self.process_phase3_reconciliation()
        return result.get('credit_pivot', pd.DataFrame())
    
    # Export Operations
    def export_reconciliation_to_excel(self, output_filename: str = None, output_dir: str = None) -> str:
        """Export complete reconciliation analysis to Excel format"""
        reconciliation_data = self.generate_reconciliation_summary()
        return self.export_manager.export_reconciliation_to_excel(
            reconciliation_data, output_filename, output_dir
        )
    
    def export_individual_sheets(self, sheet_types: list = None, output_dir: str = None) -> dict:
        """Export individual analysis sheets to separate Excel files"""
        bank_analysis = self.extract_bank_ledger_data()
        sib_analysis = self.analyze_sib_qr_report()
        demand_analysis = self.analyze_demand_report()
        merged_data = self.merge_sib_qr_with_demand_report()
        
        return self.export_manager.export_individual_sheets(
            bank_analysis, sib_analysis, demand_analysis, merged_data, sheet_types, output_dir
        )
    
    def create_input_template(self, template_type: str = 'reconciliation', output_dir: str = None) -> str:
        """Create input template files"""
        return self.export_manager.create_input_template(template_type, output_dir)
    
    def export_bank_ledger_with_reconciliation(self, output_filename: str = None, output_dir: str = None) -> str:
        """
        Export bank ledger in original format with reconciliation results
        Adds columns: Credit (QR Collected), Debit (System Required), Difference, Remarks
        Highlights unmatched entries with red background
        
        Args:
            output_filename: Custom filename (optional)
            output_dir: Custom output directory (optional)
            
        Returns:
            str: Path to exported Excel file
        """
        print("🏦 Preparing bank ledger export with reconciliation results...")
        
        # Run reconciliation if not already done
        reconciliation_result = self.merge_pivot_tables_comparison(include_stage2=True, include_phase3=True)
        
        if reconciliation_result.get('status') != 'success':
            print("❌ Reconciliation failed, cannot export")
            return None
        
        # Initialize export manager with fallback
        try:
            from src.reconciliation.exporters.export_manager import ExportManager
        except ModuleNotFoundError:
            from exporters.export_manager import ExportManager
        export_manager = ExportManager(output_dir)
        
        # Export using new bank ledger format
        return export_manager.export_bank_ledger_with_reconciliation(
            bank_processor=self.bank_processor,
            reconciliation_data=reconciliation_result,
            output_filename=output_filename,
            output_dir=output_dir
        )
    
    # Convenience Methods for UI Integration
    def get_processor_status(self):
        """Get status of all processors"""
        return {
            'bank_processor': 'initialized',
            'sib_processor': 'initialized',
            'demand_processor': 'initialized',
            'merge_handler': 'initialized',
            'match_finder': 'initialized',
            'export_manager': 'initialized'
        }
    
    def get_modular_structure_info(self):
        """Get information about the modular structure"""
        return {
            'processors': [
                'BankLedgerProcessor - Handles bank ledger processing',
                'SIBQRProcessor - Handles SIB QR report processing',
                'DemandReportProcessor - Handles demand report processing'
            ],
            'handlers': [
                'MergeOperationsHandler - Handles merge operations',
                'MatchFinder - Handles transaction matching'
            ],
            'managers': [
                'ExportManager - Handles all export operations'
            ],
            'total_components': 6,
            'benefits': [
                'Easier maintenance and development',
                'Clear separation of concerns',
                'Better testability',
                'Modular functionality',
                'Scalable architecture'
            ]
        }
    
    def export_reconciliation_to_excel(self, output_filename: str = None, output_dir: str = None, include_mismatch_analysis: bool = True):
        """
        Complete reconciliation analysis and Excel export in one method
        
        Args:
            output_filename (str): Custom filename for export
            output_dir (str): Custom output directory
            include_mismatch_analysis (bool): Whether to include detailed mismatch analysis
            
        Returns:
            dict: Export result with file path and summary
        """
        print(f"🚀 Starting complete reconciliation analysis and Excel export...")
        
        result = {
            'status': 'failed',
            'export_path': None,
            'summary': {},
            'debug_info': {}
        }
        
        try:
            if include_mismatch_analysis:
                # Get enhanced analysis with mismatched entries
                analysis_result = self.extract_mismatched_analysis()
                
                if analysis_result['status'] == 'success':
                    # Initialize export manager with fallback
                    try:
                        from src.reconciliation.exporters.export_manager import ExportManager
                    except ModuleNotFoundError:
                        from exporters.export_manager import ExportManager
                    export_manager = ExportManager(output_dir)
                    
                    # Export to Excel
                    export_path = export_manager.export_enhanced_reconciliation_to_excel(
                        analysis_result['reconciliation_data'],
                        analysis_result['mismatched_analysis'],
                        output_filename,
                        output_dir
                    )
                    
                    result = {
                        'status': 'success',
                        'export_path': export_path,
                        'summary': analysis_result['summary_stats'],
                        'debug_info': {
                            'export_method': 'enhanced_reconciliation_with_mismatch_analysis',
                            'tolerance_level': '±3',
                            'sheets_created': [
                                'Executive_Summary',
                                'Complete_Reconciliation', 
                                'Perfect_Matches',
                                'Minor_Matches_Tolerance3',
                                'Amount_Mismatches',
                                'Bank_Only_Entries',
                                'QR_Only_Entries'
                            ]
                        }
                    }
                    
                else:
                    result['debug_info']['error_message'] = f"Analysis failed: {analysis_result.get('debug_info', {}).get('error_message', 'Unknown error')}"
                    
            else:
                # Simple pivot table comparison export
                pivot_comparison = self.merge_pivot_tables_comparison()
                
                if pivot_comparison['status'] == 'success':
                    # Initialize export manager with fallback
                    try:
                        from src.reconciliation.exporters.export_manager import ExportManager
                    except ModuleNotFoundError:
                        from exporters.export_manager import ExportManager
                    export_manager = ExportManager(output_dir)
                    
                    # Prepare export data
                    export_data = {'pivot_comparison': pivot_comparison}
                    
                    # Include stage 2 results if available
                    if 'stage2_results' in pivot_comparison:
                        export_data['stage2_results'] = pivot_comparison['stage2_results']
                        print("✅ Including Stage 2 group payment results in export")
                    
                    # Export to Excel
                    export_path = export_manager.export_reconciliation_to_excel(
                        export_data,
                        output_filename,
                        output_dir
                    )
                    
                    result = {
                        'status': 'success',
                        'export_path': export_path,
                        'summary': pivot_comparison['reconciliation_summary'],
                        'debug_info': {
                            'export_method': 'simple_pivot_comparison',
                            'tolerance_level': '±3'
                        }
                    }
                else:
                    result['debug_info']['error_message'] = f"Pivot comparison failed: {pivot_comparison.get('debug_info', {}).get('error_message', 'Unknown error')}"
            
        except Exception as e:
            result['debug_info']['error_message'] = f"Export process failed: {str(e)}"
            
        return result
    
    # Phase 3 Reconciliation Methods
    def process_phase3_bank_ledger(self) -> Dict[str, Any]:
        """Process bank ledger data using Phase 3 methodology"""
        try:
            from .processors.phase3_processor import Phase3ReconciliationProcessor
            
            processor = Phase3ReconciliationProcessor()
            return processor.process_bank_ledger_phase3(self.bank_ledger_df)
            
        except Exception as e:
            error_msg = f"Error in Phase 3 bank ledger processing: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'status': 'error',
                'message': error_msg,
                'debit_df': pd.DataFrame(),
                'credit_df': pd.DataFrame()
            }
    
    def process_phase3_reconciliation(self, mismatched_data: pd.DataFrame = None) -> Dict[str, Any]:
        """
        Phase 3 Reconciliation: Analyze credit/debit differences and match with QR amounts
        
        Args:
            mismatched_data: DataFrame of mismatched records from Phase 2, if None will extract from current reconciliation
            
        Returns:
            Dict containing newly matched records, remaining mismatches, and analysis
        """
        print("🔄 Starting Phase 3: Credit/Debit Reconciliation...")
        
        try:
            from .processors.phase3_processor import Phase3ReconciliationProcessor
            
            # Get mismatched data if not provided
            if mismatched_data is None:
                print("   • Extracting mismatched data from current reconciliation...")
                reconciliation_result = self.merge_pivot_tables_comparison(include_stage2=True)
                
                if reconciliation_result.get('status') != 'success':
                    return {
                        'newly_matched': pd.DataFrame(),
                        'remaining_mismatched': pd.DataFrame(),
                        'phase3_analysis': {'total_analyzed': 0, 'resolved': 0},
                        'status': 'error',
                        'message': 'Could not get reconciliation data for Phase 3 processing'
                    }
                
                main_data = reconciliation_result.get('merged_pivot_data')
                if main_data is None or main_data.empty:
                    return {
                        'newly_matched': pd.DataFrame(),
                        'remaining_mismatched': pd.DataFrame(),
                        'phase3_analysis': {'total_analyzed': 0, 'resolved': 0},
                        'status': 'success',
                        'message': 'No data available for Phase 3 processing',
                    }
                
                # Extract mismatched records
                status_col = 'status' if 'status' in main_data.columns else 'reconciliation_status'
                mismatched_data = main_data[
                    main_data[status_col].str.contains('MISMATCH', na=False)
                ].copy()
            
            print(f"   • Found {len(mismatched_data)} mismatched records for Phase 3 analysis")
            
            if mismatched_data.empty:
                return {
                    'newly_matched': pd.DataFrame(),
                    'remaining_mismatched': pd.DataFrame(),
                    'phase3_analysis': {'total_analyzed': 0, 'resolved': 0},
                    'status': 'success',
                    'message': 'No mismatched records found for Phase 3 processing'
                }
            
            # Process bank ledger to get credit/debit DataFrames
            print("   • Processing bank ledger for credit/debit analysis...")
            phase3_result = self.process_phase3_bank_ledger()
            
            if phase3_result.get('status') != 'success':
                return {
                    'newly_matched': pd.DataFrame(),
                    'remaining_mismatched': mismatched_data.copy(),
                    'phase3_analysis': {'total_analyzed': 0, 'resolved': 0},
                    'status': 'error',
                    'message': f'Phase 3 bank ledger processing failed: {phase3_result.get("message", "Unknown error")}'
                }
            
            # Get debit and credit DataFrames
            debit_df = phase3_result.get('debit_df', pd.DataFrame())
            credit_df = phase3_result.get('credit_df', pd.DataFrame())
            
            if debit_df.empty and credit_df.empty:
                return {
                    'newly_matched': pd.DataFrame(),
                    'remaining_mismatched': mismatched_data.copy(),
                    'phase3_analysis': {'total_analyzed': 0, 'resolved': 0},
                    'status': 'error',
                    'message': 'No credit/debit data extracted from bank ledger'
                }
            
                # Process Phase 3 reconciliation
            processor = Phase3ReconciliationProcessor()
            result = processor.process_phase3_reconciliation(mismatched_data, debit_df, credit_df)
            
            # Generate summary (reduced output)
            if result.get('status') == 'success':
                newly_matched = result.get('newly_matched', pd.DataFrame())
                if not newly_matched.empty:
                    print(f"✓ Phase 3 found {len(newly_matched)} matches")
            
            return result        
        except Exception as e:
            error_msg = f"Error in Phase 3 reconciliation processing: {str(e)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            
            return {
                'newly_matched': pd.DataFrame(),
                'remaining_mismatched': mismatched_data.copy() if mismatched_data is not None else pd.DataFrame(),
                'phase3_analysis': {'total_analyzed': 0, 'resolved': 0},
                'status': 'error',
                'message': error_msg
            }


# Backward compatibility - create alias to original engine name
ReconciliationEngine = ModularReconciliationEngine