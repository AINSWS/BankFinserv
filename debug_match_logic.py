import pandas as pd

print("=== DEBUGGING MATCH ISSUE ===")

# Create test data that should have matches
test_data = pd.DataFrame({
    'loan_id': ['L001', 'L002', 'L003', 'L004', 'L005'],
    'system_amount': [1000, 2000, 3000, 4000, 5000],
    'qr_amount': [1000, 2001, 3002, 4005, 0],  # Mix of perfect, minor, mismatch, no QR
    'reconciliation_status': ['', '', '', '', '']
})

print("Test data:")
print(test_data[['loan_id', 'system_amount', 'qr_amount']])

# Apply the same logic as in merge_operations.py
def get_reconciliation_status(row):
    system_amt = row['system_amount']
    qr_amt = row['qr_amount']
    difference = system_amt - qr_amt
    
    if difference == 0:
        return "MATCHED - Perfect Match"
    elif abs(difference) <= 2:  # Banking standard
        return "MATCHED - Minor Difference"
    else:
        return "MISMATCH - Amount Difference"

test_data['reconciliation_status'] = test_data.apply(get_reconciliation_status, axis=1)

print("\nAfter applying banking tolerance (±2):")
print(test_data[['loan_id', 'system_amount', 'qr_amount', 'reconciliation_status']])

# Count matches
perfect_matches = len(test_data[test_data['reconciliation_status'] == 'MATCHED - Perfect Match'])
minor_matches = len(test_data[test_data['reconciliation_status'] == 'MATCHED - Minor Difference'])
mismatches = len(test_data[test_data['reconciliation_status'] == 'MISMATCH - Amount Difference'])
total_matches = perfect_matches + minor_matches

print(f"\nMatch Summary:")
print(f"Perfect matches: {perfect_matches}")
print(f"Minor matches (≤2): {minor_matches}")
print(f"Total matches: {total_matches}")
print(f"Mismatches: {mismatches}")
print(f"Match rate: {total_matches/len(test_data)*100:.1f}%")

# Test UI filtering logic
matched_df = test_data[test_data['reconciliation_status'].str.contains('MATCHED', na=False)]
mismatch_df = test_data[test_data['reconciliation_status'].str.contains('MISMATCH', na=False)]

print(f"\nUI would show:")
print(f"Matched records: {len(matched_df)}")
print(f"Mismatched records: {len(mismatch_df)}")

if len(matched_df) == 0:
    print("❌ PROBLEM: UI filtering is not finding matches!")
else:
    print("✅ UI filtering should work correctly")

# Test the specific difference values that might be in your data
print(f"\nTesting different amounts (tolerance ±2):")
for diff in [0, 1, 2, 3, 5, 10]:
    base = 1000
    amount2 = base + diff
    result = "MATCH" if diff <= 2 else "MISMATCH"
    print(f"  {base} vs {amount2} (diff +{diff}) → {result}")
    
    amount2 = base - diff  
    result = "MATCH" if diff <= 2 else "MISMATCH"
    print(f"  {base} vs {amount2} (diff -{diff}) → {result}")