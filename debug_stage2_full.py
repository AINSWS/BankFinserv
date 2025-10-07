#!/usr/bin/env python3

import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from reconciliation.modular_engine import ModularReconciliationEngine

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

print("=== TESTING FULL RECONCILIATION WITH STAGE 2 ===")
print("\n--- Bank Data ---")
print(test_bank_data.to_string(index=False))

print("\n--- QR Data ---")
print(test_qr_data.to_string(index=False))

# Create engine and load data
engine = ModularReconciliationEngine()

print("\n--- Loading Bank Data ---")
engine.load_bank_ledger_data(test_bank_data)

print("\n--- Loading QR Data ---")
engine.load_sib_qr_data(test_qr_data)

print("\n--- Running Reconciliation WITHOUT Stage 2 ---")
result_without_stage2 = engine.merge_pivot_tables_comparison(include_stage2=False)

print(f"Status: {result_without_stage2['status']}")
if 'merged_pivot_data' in result_without_stage2:
    data = result_without_stage2['merged_pivot_data']
    print(f"Records: {len(data)}")
    if not data.empty:
        cols = ['loan_id', 'customer_name', 'system_entry', 'qr_collection', 'difference', 'status']
        available_cols = [col for col in cols if col in data.columns]
        print(data[available_cols].to_string(index=False))

print("\n--- Running Reconciliation WITH Stage 2 ---")
result_with_stage2 = engine.merge_pivot_tables_comparison(include_stage2=True)

print(f"Status: {result_with_stage2['status']}")
if 'merged_pivot_data' in result_with_stage2:
    data = result_with_stage2['merged_pivot_data']
    print(f"Records: {len(data)}")
    if not data.empty:
        cols = ['loan_id', 'customer_name', 'system_entry', 'qr_collection', 'difference', 'status']
        available_cols = [col for col in cols if col in data.columns]
        print(data[available_cols].to_string(index=False))

print("\n--- Stage 2 Result Analysis ---")
if 'stage2_result' in result_with_stage2:
    stage2_info = result_with_stage2['stage2_result']
    print(f"Stage 2 Status: {stage2_info.get('status', 'Not found')}")
    print(f"Stage 2 Message: {stage2_info.get('message', 'Not found')}")
    
print("\n--- Summary Comparison ---")
summary_without = result_without_stage2.get('reconciliation_summary', {})
summary_with = result_with_stage2.get('reconciliation_summary', {})

print(f"Without Stage 2 - Matches: {summary_without.get('total_matches', 0)}, Match %: {summary_without.get('match_percentage', 0):.1f}%")
print(f"With Stage 2 - Matches: {summary_with.get('total_matches', 0)}, Match %: {summary_with.get('match_percentage', 0):.1f}%")
print(f"Stage 2 Records Resolved: {summary_with.get('stage2_records_resolved', 0)}")