import pandas as pd
import os

def search_loan_in_files():
    """Search for loan 181669 in available Excel files"""
    files_to_check = [
        'exports/Demo_Enhanced_Reconciliation_Report.xlsx',
        'test_simplified_export.xlsx'
    ]
    
    target_loan = '181669'
    found_files = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"\n🔍 Checking {file_path}...")
            try:
                # Try reading all sheets
                xl_file = pd.ExcelFile(file_path)
                print(f"   Sheets: {xl_file.sheet_names}")
                
                for sheet_name in xl_file.sheet_names:
                    df = pd.read_excel(file_path, sheet_name=sheet_name)
                    print(f"   Sheet '{sheet_name}': {df.shape[0]} rows, {df.shape[1]} columns")
                    
                    # Look for the loan ID in all columns
                    for col in df.columns:
                        if df[col].astype(str).str.contains(target_loan, na=False).any():
                            matching_rows = df[df[col].astype(str).str.contains(target_loan, na=False)]
                            print(f"   ✅ Found loan {target_loan} in sheet '{sheet_name}', column '{col}':")
                            print(f"      Matching rows: {len(matching_rows)}")
                            print(matching_rows.head())
                            found_files.append((file_path, sheet_name, col))
                            
            except Exception as e:
                print(f"   ❌ Error reading {file_path}: {e}")
        else:
            print(f"   ❌ File not found: {file_path}")
    
    if not found_files:
        print(f"\n❌ Loan {target_loan} not found in any available files")
        
        # Let's also check what loans are actually in the files
        print("\n📊 Sample loan IDs from available files:")
        for file_path in files_to_check:
            if os.path.exists(file_path):
                try:
                    df = pd.read_excel(file_path, sheet_name=0)  # First sheet
                    # Look for loan ID column
                    for col in df.columns:
                        if 'loan' in col.lower() or 'id' in col.lower():
                            sample_loans = df[col].dropna().astype(str).head(10).tolist()
                            print(f"   {file_path} - {col}: {sample_loans}")
                            break
                except Exception as e:
                    print(f"   Error sampling {file_path}: {e}")
    else:
        print(f"\n✅ Found loan {target_loan} in {len(found_files)} locations")

if __name__ == "__main__":
    search_loan_in_files()