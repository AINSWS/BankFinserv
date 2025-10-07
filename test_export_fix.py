#!/usr/bin/env python3

import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from reconciliation.modular_engine import ModularReconciliationEngine

print("=== TESTING STAGE 2 EXPORT FIX ===")

# Create test data exactly like your example
test_bank_data = pd.DataFrame({
    'loan_id': [182163, 182165, 182162, 182164],
    'customer_name': ['USHA VILAS PANCHAL', 'BHARTI JAYWANT KADAM', 'MANSI SACHIN CHARKARI', 'HEMLATA SUNIL PATIL'],
    'group_id': ['1549 SWATI', '1549 SWATI', '1549 SWATI', '1549 SWATI'],
    'branch': ['CHEMBUR', 'CHEMBUR', 'CHEMBUR', 'CHEMBUR'],
    'system_entry': [3320, 3320, 3100, 3100]
})

test_qr_data = pd.DataFrame({
    'loan_id': [182165],  # Only BHARTI has QR payment
    'customer_name': ['BHARTI JAYWANT KADAM'],
    'qr_collection': [12840]
})

# Create engine and load data
engine = ModularReconciliationEngine()
engine.load_bank_ledger_data(test_bank_data)
engine.load_sib_qr_data(test_qr_data)

print("--- Testing Export Data with Stage 2 ---")
result_with_stage2 = engine.merge_pivot_tables_comparison(include_stage2=True)

print(f"Result keys: {list(result_with_stage2.keys())}")

# Check if simplified_report has Stage 2 updates
if 'simplified_report' in result_with_stage2:
    export_data = result_with_stage2['simplified_report']
    print(f"Export data shape: {export_data.shape}")
    
    # Filter for our test group
    group_data = export_data[export_data['group_id'] == '1549 SWATI']
    if not group_data.empty:
        print("\n=== EXPORT DATA FOR GROUP 1549 SWATI ===")
        cols = ['loan_id', 'customer_name', 'system_entry', 'qr_collection', 'difference', 'status']
        available_cols = [col for col in cols if col in group_data.columns]
        print(group_data[available_cols].to_string(index=False))
        
        # Check if redistributed amounts are present
        bharti_qr = group_data[group_data['customer_name'].str.contains('BHARTI')]['qr_collection'].iloc[0] if len(group_data[group_data['customer_name'].str.contains('BHARTI')]) > 0 else None
        usha_qr = group_data[group_data['customer_name'].str.contains('USHA')]['qr_collection'].iloc[0] if len(group_data[group_data['customer_name'].str.contains('USHA')]) > 0 else None
        
        print(f"\n=== VERIFICATION ===")
        print(f"BHARTI QR: {bharti_qr} (should be 3320, not 12840)")
        print(f"USHA QR: {usha_qr} (should be 3320, not 0)")
        
        if bharti_qr == 3320 and usha_qr == 3320:
            print("✅ SUCCESS: Stage 2 results are correctly included in export data!")
        else:
            print("❌ ISSUE: Stage 2 results are not in export data")
    else:
        print("❌ Group 1549 SWATI not found in export data")
        
else:
    print("❌ No simplified_report in result")

# Also check merged_pivot_data
if 'merged_pivot_data' in result_with_stage2:
    main_data = result_with_stage2['merged_pivot_data']
    group_data = main_data[main_data['group_id'] == '1549 SWATI']
    if not group_data.empty:
        print("\n=== MERGED_PIVOT_DATA FOR GROUP 1549 SWATI ===")
        cols = ['loan_id', 'customer_name', 'system_entry', 'qr_collection', 'difference', 'status']
        available_cols = [col for col in cols if col in group_data.columns]
        print(group_data[available_cols].to_string(index=False))