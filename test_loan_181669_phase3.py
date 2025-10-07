import pandas as pd
import sys
import os

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from reconciliation.processors.phase3_processor import Phase3ReconciliationProcessor

def test_loan_181669_phase3():
    """Test Phase 3 specifically with loan 181669 from bankLeasure.xlsx"""
    
    print("🔍 Testing Phase 3 with loan 181669 from bankLeasure.xlsx...")
    
    # Load the actual bank ledger data
    bank_ledger_file = 'src/bankLeasure.xlsx'
    
    try:
        # Read the bank ledger data (Sheet1 has the transaction details)
        bank_ledger_df = pd.read_excel(bank_ledger_file, sheet_name='Sheet1')
        print(f"✅ Loaded bank ledger: {bank_ledger_df.shape[0]} transactions")
        
        # Read the reconciliation data (Sheet2 has the loan details)
        recon_df = pd.read_excel(bank_ledger_file, sheet_name='Sheet2')
        print(f"✅ Loaded reconciliation data: {recon_df.shape[0]} loans")
        
        # Filter for loan 181669
        loan_181669_data = recon_df[recon_df['lan'] == 181669].copy()
        
        if loan_181669_data.empty:
            print("❌ Loan 181669 not found in reconciliation data")
            return
            
        print(f"\n📊 Loan 181669 Details:")
        loan_row = loan_181669_data.iloc[0]
        print(f"   Loan ID: {loan_row['lan']}")
        print(f"   Customer: {loan_row['Customer Name']}")
        print(f"   System Entry: ₹{loan_row['System Entry']}")
        print(f"   QR Collection: ₹{loan_row['QR Cllollection']}")
        print(f"   Difference: ₹{loan_row['Difference']}")
        
        # Test Phase 3 processor
        processor = Phase3ReconciliationProcessor()
        
        # Process Phase 3 for this specific loan
        print(f"\n🔧 Running Phase 3 analysis for loan 181669...")
        
        # Create a small test dataset with just this loan
        test_data = pd.DataFrame({
            'loan_id': [181669],
            'system_amount': [6565.0],
            'qr_amount': [208.0],
            'status': ['MISMATCH'],
            'customer_name': [loan_row['Customer Name']],
            'group_name': [loan_row['Group']],
            'branch': [loan_row['Branch']]
        })
        
        print("   Test data created:")
        print(test_data.to_string())
        
        # Process Phase 3
        phase3_result = processor.process_phase3_reconciliation(test_data, bank_ledger_df)
        
        print(f"\n📋 Phase 3 Results:")
        print(f"   Records processed: {len(phase3_result)}")
        
        if not phase3_result.empty:
            result_row = phase3_result.iloc[0]
            print(f"   Final Status: {result_row['status']}")
            if 'reconciliation_status' in result_row:
                print(f"   Reconciliation Status: {result_row['reconciliation_status']}")
            if 'phase3_debit_total' in result_row:
                print(f"   Phase 3 Debit Total: ₹{result_row['phase3_debit_total']}")
            if 'phase3_credit_total' in result_row:
                print(f"   Phase 3 Credit Total: ₹{result_row['phase3_credit_total']}")
            if 'phase3_difference' in result_row:
                print(f"   Phase 3 Difference: ₹{result_row['phase3_difference']}")
            
            print(f"\n📊 Full result:")
            print(result_row.to_string())
        
        # Also check the bank ledger transactions for this loan
        print(f"\n🏦 Bank Ledger Transactions for loan 181669:")
        loan_transactions = bank_ledger_df[
            bank_ledger_df['Narration'].astype(str).str.contains('181669', na=False)
        ]
        
        total_debit = loan_transactions['Debit'].fillna(0).sum()
        total_credit = loan_transactions['Credit'].fillna(0).sum()
        net_difference = total_credit - total_debit
        
        print(f"   Total Debit: ₹{total_debit}")
        print(f"   Total Credit: ₹{total_credit}")
        print(f"   Net Difference (Credit - Debit): ₹{net_difference}")
        print(f"   QR Amount: ₹{loan_row['QR Cllollection']}")
        print(f"   Match within ±2 tolerance: {abs(net_difference - loan_row['QR Cllollection']) <= 2}")
        
        print(f"\n💡 Analysis:")
        if abs(net_difference - loan_row['QR Cllollection']) <= 2:
            print("   ✅ Phase 3 should resolve this loan - net difference matches QR amount!")
        else:
            print(f"   ❌ Phase 3 won't resolve - net difference (₹{net_difference}) doesn't match QR (₹{loan_row['QR Cllollection']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_loan_181669_phase3()