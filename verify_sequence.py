"""
Verify Current Code Sequence Against Requirements
"""
import pandas as pd
import sys
import os

# Add src path for imports
sys.path.append('src')
sys.path.append('src/reconciliation')

def verify_sequence():
    """Verify the current code sequence matches the requirements"""
    print("=== VERIFYING CODE SEQUENCE ===")
    print()
    
    print("REQUIRED SEQUENCE:")
    print("1. Sheet 1: Separate/split narration, filter by loan ID (2nd column), remove branch names")
    print("2. Sheet 1: Take loan ID + amount → create pivot (groupby) → name it 'system_df'")
    print("3. Sheet 2+3: Merge Sheet 3 with Sheet 2 by reference ID") 
    print("4. Sheet 2+3: Take amount + reference ID → create pivot → name it 'qr_df'")
    print("5. Final: Merge system_df with qr_df → sys_amount, qr_amount, difference")
    print("6. Final: Convert NaNs to 0 before calculating difference")
    print()
    
    # Test with real data to verify sequence
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
        
        print("CURRENT SEQUENCE VERIFICATION:")
        print()
        
        # Step 1: Check bank ledger processing
        print("1. BANK LEDGER PROCESSING:")
        bank_result = engine.bank_processor.extract_bank_ledger_data()
        if bank_result.get('parsed_data'):
            parsed_df = bank_result['parsed_data']['dataframe']
            print(f"   ✅ Narration split: Found {len(parsed_df)} loan entries")
            print(f"   ✅ Filtered by loan ID: {bank_result['filtered_data']['total_rows']} rows")
            print(f"   ✅ Sample loan IDs: {parsed_df['loan_id'].head(3).tolist()}")
        
        # Step 2: Check bank pivot creation (system_df)
        print("\n2. SYSTEM_DF CREATION:")
        bank_pivot = engine.create_bank_ledger_pivot_table()
        if bank_pivot.get('status') == 'success':
            system_df = bank_pivot['pivot_data']
            print(f"   ✅ System pivot created: {system_df.shape}")
            print(f"   ✅ Columns: {list(system_df.columns)}")
            print(f"   ✅ Total amount: {system_df['total_amount'].sum():,.2f}")
        
        # Step 3: Check Sheet2+3 merge
        print("\n3. SHEET 2+3 MERGE:")
        merge_result = engine.merge_sib_qr_with_demand_report()
        if merge_result.get('status') == 'success':
            merged_data = merge_result['merged_data']
            print(f"   ✅ QR+Demand merged: {merged_data.shape}")
            print(f"   ✅ Match rate: {merge_result['merge_stats']['match_rate']:.1f}%")
        
        # Step 4: Check QR pivot creation (qr_df)
        print("\n4. QR_DF CREATION:")
        qr_pivot = engine.create_merged_data_pivot_table()
        if qr_pivot.get('status') == 'success':
            qr_df = qr_pivot['pivot_data']
            print(f"   ✅ QR pivot created: {qr_df.shape}")
            print(f"   ✅ Columns: {list(qr_df.columns)}")
            print(f"   ✅ Total amount: {qr_df['total_amount'].sum():,.2f}")
        
        # Step 5: Check final merge (system_df + qr_df)
        print("\n5. FINAL MERGE (SYSTEM + QR):")
        final_result = engine.merge_pivot_tables_comparison()
        if final_result.get('status') == 'success':
            final_df = final_result['merged_pivot_data']
            print(f"   ✅ Final merge completed: {final_df.shape}")
            
            # Check if naming matches requirements
            has_sys_amount = 'system_amount' in final_df.columns
            has_qr_amount = 'qr_amount' in final_df.columns  
            has_difference = 'amount_difference' in final_df.columns
            
            print(f"   {'✅' if has_sys_amount else '❌'} sys_amount column: {has_sys_amount}")
            print(f"   {'✅' if has_qr_amount else '❌'} qr_amount column: {has_qr_amount}")
            print(f"   {'✅' if has_difference else '❌'} difference column: {has_difference}")
            
            if has_sys_amount and has_qr_amount:
                # Check NaN handling
                nan_count_sys = final_df['system_amount'].isna().sum()
                nan_count_qr = final_df['qr_amount'].isna().sum()
                print(f"   {'✅' if nan_count_sys == 0 else '❌'} NaNs in sys_amount: {nan_count_sys}")
                print(f"   {'✅' if nan_count_qr == 0 else '❌'} NaNs in qr_amount: {nan_count_qr}")
        
        print(f"\n6. SUMMARY:")
        print(f"   Total matches: {final_result.get('reconciliation_summary', {}).get('total_matches', 0)}")
        print(f"   Match rate: {final_result.get('reconciliation_summary', {}).get('match_percentage', 0):.1f}%")
        print(f"   Net difference: {final_result.get('reconciliation_summary', {}).get('net_difference', 0):,.2f}")
        
    except Exception as e:
        print(f"Error during verification: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_sequence()