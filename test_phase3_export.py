"""Quick test to verify Phase 3 results are in export"""
import pandas as pd
import sys
sys.path.insert(0, 'src')

from reconciliation.modular_engine import ModularReconciliationEngine

print("Loading data files...")
# Load your actual data files
bank_df = pd.read_excel('examples/Bank Ledger.xlsx')  # Adjust path as needed
sib_df = pd.read_excel('examples/SIB Leisure.xlsx')   # Adjust path as needed  
demand_df = pd.read_excel('examples/Demand Report.xlsx')  # Adjust path as needed

print("\nInitializing reconciliation engine...")
engine = ModularReconciliationEngine(bank_df, sib_df, demand_df)

print("\n" + "="*80)
print("Running complete reconciliation with export...")
print("="*80)

# This will run reconciliation AND export
result = engine.export_reconciliation_to_excel(
    output_filename='Phase3_Test_Export.xlsx',
    output_dir='exports'
)

print("\n" + "="*80)
print("EXPORT RESULT:")
print("="*80)
print(f"Status: {result['status']}")
print(f"Export Path: {result.get('export_path')}")
print(f"\nSummary:")
for key, value in result.get('summary', {}).items():
    print(f"  {key}: {value}")

print("\n✅ Check the exported file for:")
print("   1. Amount_Mismatches sheet should have 35 records (not 40)")
print("   2. Advanced_Matches_Phase3_Stage2 sheet should have 5 Phase 3 + 2 Stage 2 = 7 records")
print("   3. Executive_Summary should show correct match counts")
