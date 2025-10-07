#!/usr/bin/env python3
"""
Debug Phase 3 Integration - Check if Phase 3 is being called and processing records
"""

import pandas as pd
import sys
import os
sys.path.append('src')

from reconciliation.modular_engine import ModularReconciliationEngine

def create_test_data_with_phase3_scenarios():
    """Create test data that will definitely trigger Phase 3 processing"""
    
    # Bank Ledger Data with narration that can be parsed
    bank_ledger_data = {
        'Date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
        'Narration': [
            'EMI/182163/LOAN-PAYMENT',      # Will create debit for 182163
            'PAYMENT/182163/CREDIT-ADJ',    # Will create credit for 182163
            'EMI/182165/BHARTI-PAYMENT',    # Will create debit for 182165
            'REFUND/182165/PARTIAL-REF',    # Will create credit for 182165
            'OTHER/999999/NOT-LOAN'         # Won't match any loan
        ],
        'Debit': [3320, 0, 5000, 0, 1000],
        'Credit': [0, 300, 0, 1680, 0],
        'loan_id': [182163, 182163, 182165, 182165, 999999]
    }
    bank_ledger_df = pd.DataFrame(bank_ledger_data)
    
    # SIB QR Data - designed to test Phase 3 matching
    sib_qr_data = {
        'referenceID': ['182163', '182165', '999999'],
        'amount': [3020, 3320, 1000],  # Should match credit/debit differences!
        'payerName': ['Test User 1', 'Test User 2', 'Test User 3']
    }
    sib_qr_df = pd.DataFrame(sib_qr_data)
    
    # Demand Report Data
    demand_data = {
        'loan_id': ['182163', '182165', '999999'],
        'customer_name': ['USHA VILAS PANCHAL', 'BHARTI JAYWANT KADAM', 'TEST USER'],
        'group_id': ['1549 SWATI', '1549 SWATI', 'TEST GROUP'],
        'branch': ['SWATI', 'SWATI', 'TEST']
    }
    demand_df = pd.DataFrame(demand_data)
    
    return bank_ledger_df, sib_qr_df, demand_df

def test_phase3_integration():
    """Test if Phase 3 integration is working"""
    
    print("=== PHASE 3 INTEGRATION DEBUG TEST ===\n")
    
    # Create test data
    bank_ledger_df, sib_qr_df, demand_df = create_test_data_with_phase3_scenarios()
    
    print("--- Test Data Created ---")
    print(f"Bank Ledger: {len(bank_ledger_df)} records")
    print(f"SIB QR: {len(sib_qr_df)} records") 
    print(f"Demand Report: {len(demand_df)} records\n")
    
    # Create reconciliation engine
    print("--- Creating Reconciliation Engine ---")
    engine = ModularReconciliationEngine(bank_ledger_df, sib_qr_df, demand_df)
    
    # Test 1: Base reconciliation (no Stage 2, no Phase 3)
    print("\n--- TEST 1: Base Reconciliation (Phase 1 only) ---")
    result_base = engine.merge_pivot_tables_comparison(include_stage2=False, include_phase3=False)
    
    if result_base.get('status') == 'success':
        main_data_base = result_base.get('merged_pivot_data')
        if main_data_base is not None:
            print(f"✅ Base reconciliation successful: {len(main_data_base)} records")
            
            # Check for mismatches
            print(f"   Available columns: {list(main_data_base.columns)}")
            if 'reconciliation_status' in main_data_base.columns:
                print(f"   Reconciliation status values: {main_data_base['reconciliation_status'].unique()}")
                mismatched_base = main_data_base[main_data_base['reconciliation_status'].str.contains('MISMATCH', na=False)]
                matched_base = main_data_base[main_data_base['reconciliation_status'].str.contains('MATCHED', na=False)]
            else:
                print(f"   Status column values: {main_data_base['status'].unique()}")
                mismatched_base = main_data_base[main_data_base['status'].str.contains('MISMATCH', na=False)]
                matched_base = main_data_base[main_data_base['status'].str.contains('MATCHED', na=False)]
            
            print(f"   • MATCHED records: {len(matched_base)}")
            print(f"   • MISMATCHED records: {len(mismatched_base)}")
            
            if len(mismatched_base) > 0:
                print("\n   Mismatched Records:")
                for _, row in mismatched_base.iterrows():
                    system_amt = row.get('system_amount', row.get('system_entry', 0))
                    qr_amt = row.get('qr_amount', row.get('qr_collection', 0))
                    diff = row.get('amount_difference', row.get('difference', 0))
                    print(f"   • Loan {row['loan_id']}: System=₹{system_amt}, QR=₹{qr_amt}, Diff=₹{diff}")
        else:
            print("❌ No main data in base result")
    else:
        print(f"❌ Base reconciliation failed: {result_base.get('message', 'Unknown error')}")
        return
    
    # Test 2: With Phase 3 enabled
    print("\n--- TEST 2: With Phase 3 Integration ---")
    result_with_phase3 = engine.merge_pivot_tables_comparison(include_stage2=False, include_phase3=True)
    
    if result_with_phase3.get('status') == 'success':
        main_data_phase3 = result_with_phase3.get('merged_pivot_data')
        if main_data_phase3 is not None:
            print(f"✅ Phase 3 reconciliation completed: {len(main_data_phase3)} records")
            
            # Check for Phase 3 results
            if 'reconciliation_status' in main_data_phase3.columns:
                mismatched_phase3 = main_data_phase3[main_data_phase3['reconciliation_status'].str.contains('MISMATCH', na=False)]
                matched_phase3 = main_data_phase3[main_data_phase3['reconciliation_status'].str.contains('MATCHED', na=False)]
                phase3_matched = main_data_phase3[main_data_phase3['reconciliation_status'].str.contains('Phase 3', na=False)]
            else:
                mismatched_phase3 = main_data_phase3[main_data_phase3['status'].str.contains('MISMATCH', na=False)]
                matched_phase3 = main_data_phase3[main_data_phase3['status'].str.contains('MATCHED', na=False)]
                phase3_matched = main_data_phase3[main_data_phase3['status'].str.contains('Phase 3', na=False)]
            
            print(f"   • MATCHED records: {len(matched_phase3)}")
            print(f"   • Phase 3 MATCHED records: {len(phase3_matched)}")
            print(f"   • MISMATCHED records: {len(mismatched_phase3)}")
            
            # Check if Phase 3 resolved any records
            improvement = len(matched_phase3) - len(matched_base)
            if improvement > 0:
                print(f"   ✅ Phase 3 resolved {improvement} additional records!")
                
                if len(phase3_matched) > 0:
                    print("\n   Phase 3 Matched Records:")
                    for _, row in phase3_matched.iterrows():
                        status_msg = row.get('status', 'Unknown')
                        method_msg = row.get('reconciliation_method', 'Unknown method')
                        print(f"   • Loan {row['loan_id']}: {status_msg}")
                        print(f"     Method: {method_msg}")
                        if 'phase3_debit_total' in row:
                            print(f"     Debit: ₹{row['phase3_debit_total']}, Credit: ₹{row['phase3_credit_total']}, Diff: ₹{row['phase3_difference']}")
            else:
                print(f"   ⚠️ Phase 3 did not resolve any additional records")
                
            # Check if Phase 3 result data exists
            if 'phase3_result' in result_with_phase3:
                phase3_result = result_with_phase3['phase3_result']
                print(f"\n   Phase 3 Processing Details:")
                print(f"   • Status: {phase3_result.get('status', 'Unknown')}")
                print(f"   • Message: {phase3_result.get('message', 'No message')}")
                
                if 'phase3_analysis' in phase3_result:
                    analysis = phase3_result['phase3_analysis']
                    print(f"   • Records analyzed: {analysis.get('total_analyzed', 0)}")
                    print(f"   • Records resolved: {analysis.get('resolved', 0)}")
                    print(f"   • Resolution rate: {analysis.get('resolution_rate', 0):.1f}%")
            else:
                print("   ⚠️ No phase3_result data found in result")
                
        else:
            print("❌ No main data in Phase 3 result")
    else:
        print(f"❌ Phase 3 reconciliation failed: {result_with_phase3.get('message', 'Unknown error')}")
    
    # Test 3: Check export data
    print("\n--- TEST 3: Export Data Check ---")
    if 'simplified_report' in result_with_phase3:
        export_data = result_with_phase3['simplified_report']
        if export_data is not None and not export_data.empty:
            print(f"✅ Export data available: {len(export_data)} records")
            
            export_phase3_matched = export_data[export_data['status'].str.contains('Phase 3', na=False)]
            print(f"   • Phase 3 matched in export: {len(export_phase3_matched)}")
            
            if len(export_phase3_matched) > 0:
                print("   ✅ Phase 3 matches ARE in export data!")
                for _, row in export_phase3_matched.iterrows():
                    print(f"   • Export Loan {row['loan_id']}: {row['status']}")
            else:
                print("   ❌ Phase 3 matches NOT in export data")
                print("   Available status values in export:")
                for status in export_data['status'].unique():
                    count = len(export_data[export_data['status'] == status])
                    print(f"     • '{status}': {count} records")
                    
                # Also check reconciliation_status if it exists
                if 'reconciliation_status' in export_data.columns:
                    print("   Available reconciliation_status values in export:")
                    for status in export_data['reconciliation_status'].unique():
                        count = len(export_data[export_data['reconciliation_status'] == status])
                        print(f"     • '{status}': {count} records")
        else:
            print("   ❌ No export data available")
    else:
        print("   ❌ No simplified_report in result")

if __name__ == "__main__":
    test_phase3_integration()