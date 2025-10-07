#!/usr/bin/env python3

import pandas as pd
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from reconciliation.processors.phase3_processor import Phase3ReconciliationProcessor

print("=== TESTING PHASE 3 RECONCILIATION PROCESSOR ===")

# Create sample bank ledger data
sample_data = pd.DataFrame({
    'narration': [
        'TRANSFER/182163/182164/LOAN_PAYMENT',
        'PAYMENT/182165/182162/GROUP_SETTLEMENT', 
        'DEPOSIT/182167/182168/INTEREST',
        'WITHDRAWAL/182169//PROCESSING_FEE',  # Missing credit loan ID
        'REFUND//182170/REFUND_PROCESS',      # Missing debit loan ID
        'INVALID_FORMAT',                      # No '/' delimiter
        ''                                     # Empty narration
    ],
    'debit': [5000, 0, 2000, 1500, 0, 3000, 0],      # Debit amounts
    'credit': [0, 8000, 0, 0, 2500, 0, 1000],        # Credit amounts
    'date': ['2025-01-01'] * 7,
    'branch': ['MAIN'] * 7
})

print("\n=== SAMPLE BANK LEDGER DATA ===")
print(sample_data.to_string(index=False))

# Test Phase 3 processor
processor = Phase3ReconciliationProcessor()
result = processor.process_bank_ledger_phase3(sample_data)

print(f"\n=== PROCESSING RESULT ===")
print(f"Status: {result['status']}")
print(f"Message: {result['message']}")

if result['status'] == 'success':
    print(f"\n=== DEBIT DATAFRAME ===")
    debit_df = result['debit_df']
    if not debit_df.empty:
        print(debit_df.to_string(index=False))
    else:
        print("No debit transactions found")
    
    print(f"\n=== CREDIT DATAFRAME ===")
    credit_df = result['credit_df']
    if not credit_df.empty:
        print(credit_df.to_string(index=False))
    else:
        print("No credit transactions found")
    
    print(f"\n=== DEBIT PIVOT TABLE ===")
    debit_pivot = result['debit_pivot']
    if not debit_pivot.empty:
        print(debit_pivot.to_string(index=False))
    else:
        print("No debit pivot data")
    
    print(f"\n=== CREDIT PIVOT TABLE ===")
    credit_pivot = result['credit_pivot']
    if not credit_pivot.empty:
        print(credit_pivot.to_string(index=False))
    else:
        print("No credit pivot data")
    
    print(f"\n=== PROCESSING SUMMARY ===")
    summary_text = processor.get_phase3_summary(result)
    print(summary_text)

print(f"\n=== EXPECTED RESULTS ===")
print("Debit transactions should extract loan IDs from 2nd position (index 1):")
print("- 182163 with ₹5,000 (from 'TRANSFER/182163/182164/LOAN_PAYMENT')")
print("- 182167 with ₹2,000 (from 'DEPOSIT/182167/182168/INTEREST')")
print("- 182169 with ₹1,500 (from 'WITHDRAWAL/182169//PROCESSING_FEE')")
print()
print("Credit transactions should extract loan IDs from 3rd position (index 2):")
print("- 182162 with ₹8,000 (from 'PAYMENT/182165/182162/GROUP_SETTLEMENT')")  
print("- 182170 with ₹2,500 (from 'REFUND//182170/REFUND_PROCESS')")
print()
print("Invalid/missing data should be skipped gracefully.")