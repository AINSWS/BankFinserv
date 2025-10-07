#!/usr/bin/env python3

import pandas as pd
from src.reconciliation.processors.group_payment_processor import GroupPaymentProcessor

# Create test data based on your example
test_data = pd.DataFrame({
    'loan_id': [182163, 182165, 182162, 182164],
    'customer_name': ['USHA VILAS PANCHAL', 'BHARTI JAYWANT KADAM', 'MANSI SACHIN CHARKARI', 'HEMLATA SUNIL PATIL'],
    'group_id': ['1549 SWATI', '1549 SWATI', '1549 SWATI', '1549 SWATI'],
    'branch': ['CHEMBUR', 'CHEMBUR', 'CHEMBUR', 'CHEMBUR'],
    'system_entry': [3320, 3320, 3100, 3100],
    'qr_collection': [0, 12840, 0, 0],
    'difference': [3320, -9520, 3100, 3100],
    'status': ['MISMATCH - Amount Difference'] * 4
})

print('=== TEST DATA ===')
print(test_data.to_string(index=False))

# Test group payment processor
processor = GroupPaymentProcessor()
result = processor.process_group_payments(test_data)

print('\n=== STAGE 2 RESULT ===')
print(f'Status: {result["status"]}')
print(f'Message: {result["message"]}')

print('\n=== NEWLY MATCHED RECORDS ===')
if not result['newly_matched'].empty:
    cols = ['loan_id', 'customer_name', 'system_entry', 'qr_collection', 'difference', 'status']
    print(result['newly_matched'][cols].to_string(index=False))
else:
    print('No newly matched records')

print('\n=== GROUP ANALYSIS ===')
print(result['group_analysis'])

# Let's also check group totals calculation
print('\n=== GROUP TOTALS CALCULATION ===')
group_totals = processor._calculate_group_totals(test_data)
print(group_totals.to_string(index=False))

print('\n=== MATCHING GROUPS ===')
matching_groups = processor._identify_matching_groups(group_totals)
print(f"Matching groups: {matching_groups}")