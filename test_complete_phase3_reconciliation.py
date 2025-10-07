import pandas as pd
import sys
import os

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from reconciliation.processors.phase3_processor import Phase3ReconciliationProcessor

def test_complete_phase3_reconciliation():
    """Test the complete Phase 3 reconciliation process with loan 181669"""
    
    print("🔧 Testing complete Phase 3 reconciliation process...")
    
    # Load the bank ledger data
    bank_ledger_file = 'src/bankLeasure.xlsx'
    
    try:
        # Read the bank ledger data (Sheet1 has the transaction details)
        bank_ledger_df = pd.read_excel(bank_ledger_file, sheet_name='Sheet1')
        print(f"✅ Loaded bank ledger: {bank_ledger_df.shape[0]} transactions")
        
        # Read the reconciliation data (Sheet2 has the loan details)
        recon_df = pd.read_excel(bank_ledger_file, sheet_name='Sheet2')
        print(f"✅ Loaded reconciliation data: {recon_df.shape[0]} loans")
        
        # Initialize Phase 3 processor
        processor = Phase3ReconciliationProcessor()
        
        # Step 1: Process the bank ledger
        print(f"\n🔄 Step 1: Processing bank ledger...")
        phase3_result = processor.process_bank_ledger_phase3(bank_ledger_df)
        
        if phase3_result['status'] != 'success':
            print(f"❌ Bank ledger processing failed: {phase3_result['message']}")
            return
            
        debit_df = phase3_result['debit_df']
        credit_df = phase3_result['credit_df']
        
        # Step 2: Create test data for loan 181669
        print(f"\n🔄 Step 2: Creating test data for loan 181669...")
        
        # Filter for loan 181669 from reconciliation data
        loan_181669_data = recon_df[recon_df['lan'] == 181669].copy()
        
        if loan_181669_data.empty:
            print("❌ Loan 181669 not found in reconciliation data")
            return
            
        loan_row = loan_181669_data.iloc[0]
        
        # Create mismatched data DataFrame for Phase 3 testing
        mismatched_data = pd.DataFrame({
            'loan_id': [181669],
            'system_amount': [6565.0],
            'qr_amount': [208.0],  # This should match the debit-credit difference
            'status': ['MISMATCH'],
            'customer_name': [loan_row['Customer Name']],
            'group_name': [loan_row['Group']],
            'branch': [loan_row['Branch']]
        })
        
        print("   Created mismatched data:")
        print(mismatched_data.to_string())
        
        # Step 3: Run Phase 3 reconciliation
        print(f"\n🔄 Step 3: Running Phase 3 reconciliation...")
        
        reconciliation_result = processor.process_phase3_reconciliation(
            mismatched_data, 
            debit_df, 
            credit_df
        )
        
        print(f"\n📋 Phase 3 Reconciliation Results:")
        print(f"   Status: {reconciliation_result['status']}")
        
        newly_matched = reconciliation_result['newly_matched']
        print(f"   Newly matched records: {len(newly_matched)}")
        
        if not newly_matched.empty:
            print("   ✅ Loan 181669 was successfully resolved by Phase 3!")
            resolved_record = newly_matched.iloc[0]
            print(f"   New Status: {resolved_record['status']}")
            print(f"   Phase 3 Debit Total: ₹{resolved_record['phase3_debit_total']}")
            print(f"   Phase 3 Credit Total: ₹{resolved_record['phase3_credit_total']}")
            print(f"   Phase 3 Difference: ₹{resolved_record['phase3_difference']}")
            print(f"   QR Amount: ₹{resolved_record['qr_amount']}")
            print(f"   Match Difference: ₹{resolved_record['phase3_match_difference']}")
        else:
            print("   ❌ Loan 181669 was not resolved by Phase 3")
            remaining = reconciliation_result['remaining_mismatched']
            if not remaining.empty:
                print("   Remaining mismatched records:")
                print(remaining.to_string())
        
        # Manual verification
        print(f"\n🔍 Manual Verification:")
        loan_181669_debits = debit_df[debit_df['loan_id'] == '181669']
        loan_181669_credits = credit_df[credit_df['loan_id'] == '181669']
        
        total_debit = loan_181669_debits['amount'].sum() if not loan_181669_debits.empty else 0
        total_credit = loan_181669_credits['amount'].sum() if not loan_181669_credits.empty else 0
        difference = total_debit - total_credit
        
        print(f"   Loan 181669 Manual Calculation:")
        print(f"   Total Debit: ₹{total_debit}")
        print(f"   Total Credit: ₹{total_credit}")
        print(f"   Difference (Debit - Credit): ₹{difference}")
        print(f"   QR Amount: ₹208")
        print(f"   Match: {abs(difference - 208) <= 2}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_complete_phase3_reconciliation()