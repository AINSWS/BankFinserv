#!/usr/bin/env python3
"""
Debug specific loan ID 181669 - Why isn't Phase 3 resolving this record?
"""

import pandas as pd
import sys
sys.path.append('src')

from reconciliation.modular_engine import ModularReconciliationEngine

def debug_specific_loan():
    """Debug why loan 181669 is not being resolved by Phase 3"""
    
    print("=== DEBUGGING LOAN 181669 PHASE 3 ISSUE ===\n")
    
    try:
        # Load the actual data files
        bank_ledger_df = pd.read_excel('sample_data.xlsx', sheet_name=0)
        sib_qr_df = pd.read_excel('sample_data.xlsx', sheet_name=1) 
        demand_report_df = pd.read_excel('sample_data.xlsx', sheet_name=2)
        
        print("✅ Loaded actual data files")
        
    except FileNotFoundError:
        print("❌ Could not find sample_data.xlsx, checking for other data files...")
        
        # Try to find Excel files in the directory
        import os
        excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx')]
        print(f"Available Excel files: {excel_files}")
        
        # Check if there are any demo files
        if os.path.exists('exports'):
            export_files = [f for f in os.listdir('exports') if f.endswith('.xlsx')]
            print(f"Export files: {export_files}")
        
        print("Please provide the correct data file path or I'll create a targeted test")
        return
    
    # Create reconciliation engine
    print("\n--- Creating Reconciliation Engine ---")
    engine = ModularReconciliationEngine(bank_ledger_df, sib_qr_df, demand_report_df)
    
    # Step 1: Check if loan 181669 exists in bank ledger
    print(f"\n--- Step 1: Checking Bank Ledger for Loan 181669 ---")
    bank_records = bank_ledger_df[bank_ledger_df['loan_id'] == 181669]
    if not bank_records.empty:
        print(f"✅ Found {len(bank_records)} records in bank ledger for loan 181669")
        print("Bank ledger records:")
        for _, record in bank_records.iterrows():
            narration = record.get('Narration', record.get('narration', 'N/A'))
            debit = record.get('Debit', record.get('debit', 0))
            credit = record.get('Credit', record.get('credit', 0))
            print(f"   • Narration: {narration}")
            print(f"   • Debit: ₹{debit}, Credit: ₹{credit}")
    else:
        print("❌ No records found in bank ledger for loan 181669")
        print("This explains why Phase 3 cannot process this loan!")
        
        # Check if the loan ID might be stored differently
        print("\nChecking for similar loan IDs in bank ledger...")
        if 'loan_id' in bank_ledger_df.columns:
            similar_loans = bank_ledger_df[bank_ledger_df['loan_id'].astype(str).str.contains('181669', na=False)]
            if not similar_loans.empty:
                print("Found similar loan IDs:")
                for loan_id in similar_loans['loan_id'].unique():
                    print(f"   • {loan_id}")
        
        # Check narration for this loan ID
        narration_cols = ['Narration', 'narration', 'description', 'particulars']
        for col in narration_cols:
            if col in bank_ledger_df.columns:
                narration_matches = bank_ledger_df[bank_ledger_df[col].astype(str).str.contains('181669', na=False)]
                if not narration_matches.empty:
                    print(f"\nFound loan 181669 in {col} column:")
                    for _, record in narration_matches.head(3).iterrows():
                        print(f"   • {record[col]}")
                break
    
    # Step 2: Run Phase 3 processing on bank ledger
    print(f"\n--- Step 2: Testing Phase 3 Bank Ledger Processing ---")
    phase3_result = engine.phase3_processor.process_bank_ledger_phase3(bank_ledger_df)
    
    if phase3_result.get('status') == 'success':
        debit_df = phase3_result['debit_df']
        credit_df = phase3_result['credit_df']
        
        print(f"✅ Phase 3 bank ledger processing successful")
        print(f"   • Debit transactions: {len(debit_df)}")
        print(f"   • Credit transactions: {len(credit_df)}")
        
        # Check if loan 181669 appears in debit/credit DataFrames
        debit_181669 = debit_df[debit_df['loan_id'] == '181669']
        credit_181669 = credit_df[credit_df['loan_id'] == '181669']
        
        print(f"\nLoan 181669 in processed data:")
        print(f"   • Debit records: {len(debit_181669)}")
        if not debit_181669.empty:
            total_debit = debit_181669['amount'].sum()
            print(f"     Total debit: ₹{total_debit}")
            for _, record in debit_181669.iterrows():
                print(f"     • ₹{record['amount']} from '{record['original_narration']}'")
        
        print(f"   • Credit records: {len(credit_181669)}")
        if not credit_181669.empty:
            total_credit = credit_181669['amount'].sum()
            print(f"     Total credit: ₹{total_credit}")
            for _, record in credit_181669.iterrows():
                print(f"     • ₹{record['amount']} from '{record['original_narration']}'")
        
        # Calculate the difference if both exist
        if not debit_181669.empty or not credit_181669.empty:
            total_debit = debit_181669['amount'].sum() if not debit_181669.empty else 0
            total_credit = credit_181669['amount'].sum() if not credit_181669.empty else 0
            difference = total_debit - total_credit
            
            print(f"\nPhase 3 Calculation for Loan 181669:")
            print(f"   • Total Debit: ₹{total_debit}")
            print(f"   • Total Credit: ₹{total_credit}")
            print(f"   • Difference (Debit - Credit): ₹{difference}")
            print(f"   • QR Amount from your data: ₹208")
            print(f"   • Match within ±2 tolerance? {abs(difference - 208) <= 2}")
            
            if abs(difference - 208) <= 2:
                print("   ✅ This SHOULD be matched by Phase 3!")
            else:
                print("   ❌ This will NOT be matched by Phase 3 due to amount difference")
                print(f"   • Variance: ₹{abs(difference - 208)}")
        else:
            print("   ❌ No debit or credit records found for loan 181669")
            print("   This explains why Phase 3 cannot resolve this loan")
            
    else:
        print(f"❌ Phase 3 bank ledger processing failed: {phase3_result.get('message')}")
    
    # Step 3: Check the full reconciliation flow
    print(f"\n--- Step 3: Full Reconciliation Flow Test ---")
    full_result = engine.merge_pivot_tables_comparison(include_stage2=True, include_phase3=True)
    
    if full_result.get('status') == 'success':
        main_data = full_result.get('merged_pivot_data')
        if main_data is not None:
            # Find loan 181669 in the results
            loan_181669_result = main_data[main_data['loan_id'] == 181669]
            
            if not loan_181669_result.empty:
                record = loan_181669_result.iloc[0]
                print(f"✅ Found loan 181669 in reconciliation results:")
                print(f"   • System Entry: ₹{record.get('system_amount', record.get('system_entry', 'N/A'))}")
                print(f"   • QR Collection: ₹{record.get('qr_amount', record.get('qr_collection', 'N/A'))}")
                print(f"   • Status: {record.get('status', record.get('reconciliation_status', 'N/A'))}")
                print(f"   • Reconciliation Method: {record.get('reconciliation_method', 'N/A')}")
                
                if 'phase3_debit_total' in record:
                    print(f"   • Phase 3 Debit Total: ₹{record['phase3_debit_total']}")
                if 'phase3_credit_total' in record:
                    print(f"   • Phase 3 Credit Total: ₹{record['phase3_credit_total']}")
                if 'phase3_difference' in record:
                    print(f"   • Phase 3 Difference: ₹{record['phase3_difference']}")
            else:
                print("❌ Loan 181669 not found in reconciliation results!")
                print("Available loan IDs (first 10):")
                print(main_data['loan_id'].head(10).tolist())
    
    # Step 4: Check export data
    print(f"\n--- Step 4: Export Data Check ---")
    if 'simplified_report' in full_result:
        export_data = full_result['simplified_report']
        if export_data is not None and not export_data.empty:
            loan_181669_export = export_data[export_data['loan_id'] == 181669]
            
            if not loan_181669_export.empty:
                record = loan_181669_export.iloc[0]
                print(f"✅ Found loan 181669 in export data:")
                print(f"   • Status: {record.get('status', 'N/A')}")
                print(f"   • Export will show: {record.get('status', 'UNKNOWN')}")
                
                if 'MATCHED' in str(record.get('status', '')):
                    print("   ✅ This loan IS resolved in the export!")
                else:
                    print("   ❌ This loan is NOT resolved in the export")
            else:
                print("❌ Loan 181669 not found in export data!")

if __name__ == "__main__":
    debug_specific_loan()