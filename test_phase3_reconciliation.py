#!/usr/bin/env python3

import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from reconciliation.modular_engine import ModularReconciliationEngine

print("=== PHASE 3 RECONCILIATION TEST ===")
print()

# Create test bank ledger data with narration splitting
test_bank_data = pd.DataFrame({
    'Date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04'],
    'Narration': [
        'EMI/182163/LOAN-PAYMENT',  # Debit for loan 182163
        'PAYMENT/182163/CREDIT-ADJ',  # Credit for loan 182163  
        'EMI/182165/BHARTI-PAYMENT',  # Debit for loan 182165
        'REFUND/182165/PARTIAL-REF'   # Credit for loan 182165
    ],
    'Debit': [3320, 0, 5000, 0],
    'Credit': [0, 300, 0, 1680]
})

# Create test mismatched data from Phase 2
test_mismatched_data = pd.DataFrame({
    'loan_id': [182163, 182165],
    'customer_name': ['USHA VILAS PANCHAL', 'BHARTI JAYWANT KADAM'],
    'group_id': ['1549 SWATI', '1549 SWATI'],
    'system_entry': [3020, 3320],
    'qr_collection': [0, 3320], 
    'difference': [3020, 0],
    'status': ['MISMATCH - Amount Difference', 'MISMATCH - Amount Difference']
})

print("--- Test Bank Ledger Data ---")
print(test_bank_data.to_string(index=False))

print("\n--- Test Mismatched Data from Phase 2 ---")
print(test_mismatched_data.to_string(index=False))

print("\n--- Testing Phase 3 Processing ---")

# Create engine with test data - need dummy data for required parameters
dummy_qr_data = pd.DataFrame({'referenceID': ['test'], 'amount': [0]})
dummy_demand_data = pd.DataFrame({'loan_id': ['test'], 'amount': [0]})

engine = ModularReconciliationEngine(test_bank_data, dummy_qr_data, dummy_demand_data)

# Test Phase 3 bank ledger processing
print("\n1. Processing bank ledger for credit/debit extraction...")
phase3_result = engine.process_phase3_bank_ledger()

if phase3_result['status'] == 'success':
    debit_df = phase3_result['debit_df']
    credit_df = phase3_result['credit_df']
    
    print("\n--- Debit DataFrame ---")
    print(debit_df.to_string(index=False))
    
    print("\n--- Credit DataFrame ---")
    print(credit_df.to_string(index=False))
    
    # Test Phase 3 reconciliation
    print("\n2. Running Phase 3 reconciliation...")
    
    from reconciliation.processors.phase3_processor import Phase3ReconciliationProcessor
    processor = Phase3ReconciliationProcessor()
    
    reconciliation_result = processor.process_phase3_reconciliation(
        test_mismatched_data, debit_df, credit_df
    )
    
    print(f"\nPhase 3 Status: {reconciliation_result['status']}")
    print(f"Message: {reconciliation_result['message']}")
    
    newly_matched = reconciliation_result['newly_matched']
    remaining_mismatched = reconciliation_result['remaining_mismatched']
    
    if not newly_matched.empty:
        print("\n--- Newly Matched Records ---")
        cols = ['loan_id', 'customer_name', 'qr_collection', 'phase3_debit_total', 'phase3_credit_total', 'phase3_difference', 'status']
        available_cols = [col for col in cols if col in newly_matched.columns]
        print(newly_matched[available_cols].to_string(index=False))
    
    if not remaining_mismatched.empty:
        print("\n--- Still Mismatched Records ---")
        print(remaining_mismatched[['loan_id', 'customer_name', 'qr_collection', 'difference', 'status']].to_string(index=False))
    
    # Show analysis
    analysis = reconciliation_result['phase3_analysis']
    print(f"\n--- Phase 3 Analysis ---")
    print(f"Total analyzed: {analysis['total_analyzed']}")
    print(f"Resolved: {analysis['resolved']}")
    print(f"Still mismatched: {analysis['remaining_mismatched']}")
    print(f"Resolution rate: {analysis['resolution_rate']:.1f}%")

else:
    print(f"❌ Phase 3 bank ledger processing failed: {phase3_result['message']}")

print("\n--- Expected Behavior ---")
print("For loan 182163:")
print("• Debit total: ₹3,320 (from EMI/182163/LOAN-PAYMENT)")
print("• Credit total: ₹300 (from PAYMENT/182163/CREDIT-ADJ)")
print("• Difference: ₹3,020 (3320 - 300)")
print("• QR Amount: ₹0")
print("• Should NOT match (₹3,020 ≠ ₹0)")
print()
print("For loan 182165:")
print("• Debit total: ₹5,000 (from EMI/182165/BHARTI-PAYMENT)")
print("• Credit total: ₹1,680 (from REFUND/182165/PARTIAL-REF)")
print("• Difference: ₹3,320 (5000 - 1680)")
print("• QR Amount: ₹3,320")
print("• Should MATCH (₹3,320 = ₹3,320)")
print()
print("Phase 3 reconciliation looks for cases where:")
print("(Debit Total - Credit Total) ≈ QR Amount within ±2 tolerance")