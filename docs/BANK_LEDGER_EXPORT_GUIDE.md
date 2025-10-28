# Bank Ledger Export with Reconciliation Results

## Overview
This feature exports reconciliation results directly in the bank ledger format, making it easy to trace back results to the original bank entries.

## What It Does

### Input
- Original bank ledger data (with narration column)
- Reconciliation results from Stage 1, 2, and 3

### Output
An Excel file with:
- **All original bank ledger columns** (narration, date, reference, etc.)
- **Credit (QR Collected)** - Amount collected via QR payment
- **Debit (System Required)** - Amount that should be paid per system
- **Difference** - Calculated as (Debit - Credit)
- **Remarks** - Match status with visual indicators

### Visual Indicators
- ✓ **GREEN background** = Matched entries
- ✗ **RED background** = Mismatched entries (UNMATCHED)
- **YELLOW background** = Entries without valid loan IDs

## How to Use

### Method 1: Using ModularReconciliationEngine

```python
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

print(f"✅ Exported to: {export_path}")
```

### Method 2: Using Export Manager Directly

```python
from reconciliation.exporters.export_manager import ExportManager
from reconciliation.modular_engine import ModularReconciliationEngine

# Initialize engine and run reconciliation
engine = ModularReconciliationEngine(bank_df, sib_df, demand_df)
recon_result = engine.merge_pivot_tables_comparison(
    include_stage2=True,
    include_phase3=True
)

# Export using export manager
export_mgr = ExportManager(output_dir='exports')
export_path = export_mgr.export_bank_ledger_with_reconciliation(
    bank_processor=engine.bank_processor,
    reconciliation_data=recon_result,
    output_filename='Custom_Name.xlsx'
)
```

## Output File Structure

### Sheet 1: Bank_Ledger_Reconciliation
Contains all bank ledger entries with added reconciliation columns:

| Original Columns... | Credit (QR Collected) | Debit (System Required) | Difference | Remarks |
|--------------------|-----------------------|-------------------------|------------|---------|
| Narration/Date/etc | 5000.00 | 5000.00 | 0.00 | ✓ MATCHED |
| Narration/Date/etc | 3000.00 | 5000.00 | 2000.00 | ✗ MISMATCH - Diff: ₹2000.00 |
| Narration/Date/etc | - | - | - | No loan ID found |

### Sheet 2: Summary
Quick statistics:
- Total Bank Entries
- Matched Entries
- Mismatched Entries
- No Loan ID Found
- Match Rate %

## Features

1. **Traceability**: See reconciliation results directly on bank ledger entries
2. **Visual Highlighting**: Quick identification of mismatches (red background)
3. **Complete Data**: All original bank columns preserved
4. **Summary Stats**: Overview sheet with key metrics
5. **Stage Integration**: Includes results from all 3 reconciliation stages:
   - Stage 1: Direct matching
   - Stage 2: Group payment processing
   - Stage 3: Credit/Debit analysis

## Remarks Column Meanings

| Remark | Meaning |
|--------|---------|
| ✓ MATCHED | Exact match between system and QR amounts |
| ✓ MATCHED - Group Payment (Payer) | Member who paid for the group |
| ✓ MATCHED - Group Payment (Beneficiary) | Member whose payment was covered by another |
| ✓ MATCHED - Credit/Debit Analysis | Matched through Phase 3 analysis |
| ✗ MISMATCH - Diff: ₹X.XX | Amount mismatch with difference shown |
| No loan ID found | Entry without valid loan ID in narration |
| Not in reconciliation | Valid loan ID but not in reconciliation data |

## Benefits

1. **For Accountants**: Easy to verify individual transactions
2. **For Auditors**: Clear trail from bank entry to reconciliation result
3. **For Management**: Visual overview with color coding
4. **For Analysis**: Can filter/sort by Remarks column to focus on issues

## Technical Details

### Column Mapping
- **Credit** = `qr_amount` from reconciliation (amount collected)
- **Debit** = `system_amount` from reconciliation (amount required)
- **Difference** = `amount_difference` from reconciliation
- **Remarks** = Derived from `reconciliation_status` or `status` field

### Processing Flow
1. Extract bank ledger data with narration parsing
2. Split narration to identify loan IDs
3. Run full reconciliation (Stage 1, 2, 3)
4. Map reconciliation results back to original entries using loan IDs
5. Add Credit, Debit, Difference, Remarks columns
6. Apply conditional formatting
7. Export to Excel with summary sheet

## Customization

You can customize the output by modifying `export_bank_ledger_with_reconciliation()` in `export_manager.py`:
- Change color schemes
- Add/remove columns
- Modify remarks text
- Adjust column widths
- Add additional sheets

## Troubleshooting

**Issue**: No Credit/Debit/Difference values shown
- **Solution**: Ensure narration field is properly formatted with loan IDs

**Issue**: All entries show "No loan ID found"
- **Solution**: Check narration splitting delimiter (default is '/')
- Verify loan ID is in 2nd column after split

**Issue**: Export fails
- **Solution**: Ensure reconciliation completed successfully first
- Check that xlsxwriter is installed: `pip install xlsxwriter`

## Next Steps

After exporting:
1. Review red-highlighted (unmatched) entries
2. Investigate mismatches using the Difference column
3. Cross-reference with original source documents
4. Update system or correct data as needed
