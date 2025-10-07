import pandas as pd
import os

def search_loan_in_bank_ledger():
    """Search for loan 181669 in bankLeasure.xlsx"""
    file_path = 'src/bankLeasure.xlsx'
    target_loan = '181669'
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"🔍 Checking {file_path} for loan {target_loan}...")
    
    try:
        # Try reading all sheets
        xl_file = pd.ExcelFile(file_path)
        print(f"📋 Sheets available: {xl_file.sheet_names}")
        
        found_loan = False
        
        for sheet_name in xl_file.sheet_names:
            print(f"\n📊 Analyzing sheet '{sheet_name}':")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            print(f"   Shape: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"   Columns: {list(df.columns)}")
            
            # Look for the loan ID in all columns
            for col in df.columns:
                if df[col].astype(str).str.contains(target_loan, na=False).any():
                    matching_rows = df[df[col].astype(str).str.contains(target_loan, na=False)]
                    print(f"\n✅ Found loan {target_loan} in column '{col}':")
                    print(f"   Number of matching rows: {len(matching_rows)}")
                    
                    # Show the matching rows with all columns
                    for idx, row in matching_rows.iterrows():
                        print(f"\n   Row {idx + 1}:")
                        for column in df.columns:
                            print(f"     {column}: {row[column]}")
                    
                    found_loan = True
                    
                    # Also show some context - rows before and after
                    if len(matching_rows) > 0:
                        first_match_idx = matching_rows.index[0]
                        context_start = max(0, first_match_idx - 2)
                        context_end = min(len(df), first_match_idx + 3)
                        context_df = df.iloc[context_start:context_end]
                        
                        print(f"\n📝 Context around loan {target_loan}:")
                        print(context_df.to_string())
        
        if not found_loan:
            print(f"\n❌ Loan {target_loan} not found in {file_path}")
            
            # Show sample data from each sheet
            print(f"\n📊 Sample data from each sheet:")
            for sheet_name in xl_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                print(f"\n   Sheet '{sheet_name}' - First 3 rows:")
                print(df.head(3).to_string())
        
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")

if __name__ == "__main__":
    search_loan_in_bank_ledger()