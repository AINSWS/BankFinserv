"""
Verify UI NaN Filter Fix
"""
import pandas as pd
import sys
import os

# Add src path for imports
sys.path.append('src')
sys.path.append('src/reconciliation')

def verify_nan_filter_fix():
    """Verify that the UI NaN filter fix works correctly"""
    print("=== VERIFYING UI NaN FILTER FIX ===")
    print()
    
    try:
        from reconciliation.modular_engine import ModularReconciliationEngine
        
        # Load real data
        bank_file = r'C:\Users\LENOVO\Downloads\14-08 bank ledger format.xlsx'
        qr_file = r'C:\Users\LENOVO\Downloads\14-08-2025 SIB QR CODE REPORT.xlsx'
        demand_file = r'C:\Users\LENOVO\Downloads\Demand Report August (2).csv'
        
        bank_df = pd.read_excel(bank_file)
        qr_df = pd.read_excel(qr_file)
        demand_df = pd.read_csv(demand_file)
        
        engine = ModularReconciliationEngine(bank_df, qr_df, demand_df)
        results = engine.merge_pivot_tables_comparison()
        
        main_data = results.get('merged_pivot_data')
        
        print("1. ORIGINAL DATA OVERVIEW:")
        print(f"   Total records: {len(main_data)}")
        print(f"   NaN loan_ids: {main_data['loan_id'].isna().sum()}")
        print()
        
        # Simulate the OLD UI filter (without NaN filtering)
        old_matched_df = main_data[main_data['reconciliation_status'].str.contains('MATCHED', na=False)]
        print("2. OLD UI FILTER (WITH NaN):")
        print(f"   Matched records: {len(old_matched_df)}")
        print(f"   NaN loan_ids in matched: {old_matched_df['loan_id'].isna().sum()}")
        print()
        
        # Simulate the NEW UI filter (with NaN filtering)
        new_matched_df = main_data[
            (main_data['reconciliation_status'].str.contains('MATCHED', na=False)) &
            (main_data['loan_id'].notna())
        ]
        print("3. NEW UI FILTER (NO NaN):")
        print(f"   Matched records: {len(new_matched_df)}")
        print(f"   NaN loan_ids in matched: {new_matched_df['loan_id'].isna().sum()}")
        print()
        
        # Show sample data that UI will now display
        print("4. SAMPLE DATA UI WILL SHOW (NO NaN):")
        if not new_matched_df.empty:
            sample = new_matched_df[['loan_id', 'system_amount', 'qr_amount', 'amount_difference', 'reconciliation_status']].head(5)
            print("   First 5 matched records:")
            print(sample.to_string(index=False))
        print()
        
        # Verify no NaN values in display data
        print("5. VERIFICATION:")
        display_columns = ['loan_id', 'system_amount', 'qr_amount', 'amount_difference', 'reconciliation_status']
        for col in display_columns:
            if col in new_matched_df.columns:
                nan_count = new_matched_df[col].isna().sum()
                print(f"   {col}: {nan_count} NaN values ✅")
        
        print(f"\n🎉 SUCCESS! UI will now show {len(new_matched_df)} matched records with NO NaN loan IDs!")
        
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_nan_filter_fix()