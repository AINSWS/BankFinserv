"""
Test script for the new bank ledger export functionality
This demonstrates how to export reconciliation results in bank ledger format
"""

import pandas as pd
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_bank_ledger_export():
    """Test the new bank ledger export with reconciliation results"""
    
    print("=" * 80)
    print("Testing Bank Ledger Export with Reconciliation Results")
    print("=" * 80)
    
    # This assumes you have already loaded your data files
    # You would replace these with your actual file paths
    
    print("\n📝 Instructions:")
    print("1. Load your bank ledger Excel file (Sheet 1)")
    print("2. Load your SIB QR report Excel file (Sheet 2)")
    print("3. Load your Demand report Excel file (Sheet 3)")
    print("\n4. Then call:")
    print("   engine = ModularReconciliationEngine(bank_df, sib_df, demand_df)")
    print("   export_path = engine.export_bank_ledger_with_reconciliation()")
    print("\n5. The output will have:")
    print("   - All original bank ledger columns")
    print("   - Credit (QR Collected) - Amount collected via QR")
    print("   - Debit (System Required) - Amount that should be paid")
    print("   - Difference - Debit minus Credit")
    print("   - Remarks - Match status with symbols:")
    print("     ✓ = Matched (green background)")
    print("     ✗ = Mismatched (RED background)")
    print("     No loan ID = Entry without valid loan ID (yellow background)")
    
    print("\n" + "=" * 80)
    print("Example Code:")
    print("=" * 80)
    
    example_code = """
from reconciliation.modular_engine import ModularReconciliationEngine
import pandas as pd

# Load your data
bank_ledger_df = pd.read_excel('your_file.xlsx', sheet_name='Sheet1')
sib_qr_df = pd.read_excel('your_file.xlsx', sheet_name='Sheet2')
demand_df = pd.read_excel('your_file.xlsx', sheet_name='Sheet3')

# Initialize engine
engine = ModularReconciliationEngine(bank_ledger_df, sib_qr_df, demand_df)

# Export bank ledger with reconciliation results
export_path = engine.export_bank_ledger_with_reconciliation(
    output_filename='Bank_Ledger_with_Results.xlsx',
    output_dir='exports'
)

print(f"Exported to: {export_path}")
"""
    
    print(example_code)
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    test_bank_ledger_export()
