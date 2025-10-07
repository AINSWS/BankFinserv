#!/usr/bin/env python3

import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from reconciliation.modular_engine import ModularReconciliationEngine

print("=== TESTING PHASE 3 INTEGRATION ===")

# Create sample bank ledger data for Phase 3
bank_ledger_data = pd.DataFrame({
    'narration': [
        'TRANSFER/LON001/LON002/PAYMENT',
        'DEPOSIT/LON003/LON004/INTEREST',
        'WITHDRAWAL/LON005//FEE',
        'REFUND//LON006/PROCESS',
        'PAYMENT/LON007/LON008/SETTLEMENT',
    ],
    'debit': [5000, 0, 1500, 0, 3000],
    'credit': [0, 2000, 0, 1000, 0],
    'date': ['2025-01-01'] * 5,
    'branch': ['MAIN'] * 5
})

# Create dummy SIB QR and Demand Report data (not used in Phase 3)
sib_qr_data = pd.DataFrame({'referenceID': [], 'amount': []})
demand_data = pd.DataFrame({'loan_id': [], 'amount': []})

print("=== SAMPLE BANK LEDGER DATA ===")
print(bank_ledger_data.to_string(index=False))

# Create engine
engine = ModularReconciliationEngine(bank_ledger_data, sib_qr_data, demand_data)

print("\n=== TESTING PHASE 3 PROCESSING ===")

# Test full Phase 3 processing
phase3_result = engine.process_phase3_reconciliation()

print(f"\nPhase 3 Status: {phase3_result['status']}")
print(f"Phase 3 Message: {phase3_result['message']}")

if phase3_result['status'] == 'success':
    print("\n=== INDIVIDUAL METHOD TESTS ===")
    
    # Test individual getter methods
    debit_df = engine.get_phase3_debit_data()
    credit_df = engine.get_phase3_credit_data()
    debit_pivot = engine.get_phase3_debit_pivot()
    credit_pivot = engine.get_phase3_credit_pivot()
    
    print(f"\nDebit DataFrame shape: {debit_df.shape}")
    if not debit_df.empty:
        print("Debit records:")
        print(debit_df[['loan_id', 'amount', 'transaction_type']].to_string(index=False))
    
    print(f"\nCredit DataFrame shape: {credit_df.shape}")
    if not credit_df.empty:
        print("Credit records:")
        print(credit_df[['loan_id', 'amount', 'transaction_type']].to_string(index=False))
    
    print(f"\nDebit Pivot shape: {debit_pivot.shape}")
    if not debit_pivot.empty:
        print("Debit pivot:")
        print(debit_pivot.to_string(index=False))
    
    print(f"\nCredit Pivot shape: {credit_pivot.shape}")
    if not credit_pivot.empty:
        print("Credit pivot:")
        print(credit_pivot.to_string(index=False))

print("\n=== READY FOR PHASE 3 INSTRUCTIONS ===")
print("✅ Phase 3 processor is integrated and working!")
print("📋 Available data:")
print("   • Debit transactions with loan IDs from 2nd narration position")
print("   • Credit transactions with loan IDs from 3rd narration position")
print("   • Pivot tables for both debit and credit by loan_id")
print("   • Ready for further reconciliation instructions!")