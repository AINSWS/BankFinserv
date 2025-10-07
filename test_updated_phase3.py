import pandas as pd
import sys
import os

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from reconciliation.processors.phase3_processor import Phase3ReconciliationProcessor

def test_updated_phase3_processor():
    """Test the updated Phase 3 processor with loan 181669"""
    
    print("🔧 Testing updated Phase 3 processor with loan 181669...")
    
    # Load the bank ledger data
    bank_ledger_file = 'src/bankLeasure.xlsx'
    
    try:
        # Read the bank ledger data (Sheet1 has the transaction details)
        bank_ledger_df = pd.read_excel(bank_ledger_file, sheet_name='Sheet1')
        print(f"✅ Loaded bank ledger: {bank_ledger_df.shape[0]} transactions")
        
        # Initialize Phase 3 processor
        processor = Phase3ReconciliationProcessor()
        
        # Process the bank ledger
        print(f"\n🔄 Running Phase 3 bank ledger processing...")
        phase3_result = processor.process_bank_ledger_phase3(bank_ledger_df)
        
        if phase3_result['status'] == 'success':
            print(f"✅ Phase 3 processing successful!")
            
            debit_df = phase3_result['debit_df']
            credit_df = phase3_result['credit_df']
            
            print(f"\n📊 Processing Results:")
            print(f"   • Debit transactions: {len(debit_df)}")
            print(f"   • Credit transactions: {len(credit_df)}")
            
            # Check for loan 181669 specifically
            print(f"\n🎯 Checking for loan 181669:")
            
            # Check debit transactions
            debit_181669 = debit_df[debit_df['loan_id'] == '181669'] if not debit_df.empty else pd.DataFrame()
            print(f"   Debit transactions for 181669: {len(debit_181669)}")
            if not debit_181669.empty:
                total_debit = debit_181669['amount'].sum()
                print(f"   Total debit amount: ₹{total_debit}")
                for _, row in debit_181669.iterrows():
                    print(f"     ₹{row['amount']} - {row['original_narration'][:80]}...")
            
            # Check credit transactions
            credit_181669 = credit_df[credit_df['loan_id'] == '181669'] if not credit_df.empty else pd.DataFrame()
            print(f"   Credit transactions for 181669: {len(credit_181669)}")
            if not credit_181669.empty:
                total_credit = credit_181669['amount'].sum()
                print(f"   Total credit amount: ₹{total_credit}")
                for _, row in credit_181669.iterrows():
                    print(f"     ₹{row['amount']} - {row['original_narration'][:80]}...")
            
            # Calculate net difference
            total_debit_181669 = debit_181669['amount'].sum() if not debit_181669.empty else 0
            total_credit_181669 = credit_181669['amount'].sum() if not credit_181669.empty else 0
            net_difference = total_credit_181669 - total_debit_181669
            
            print(f"\n💰 Loan 181669 Phase 3 Analysis:")
            print(f"   Total Debit: ₹{total_debit_181669}")
            print(f"   Total Credit: ₹{total_credit_181669}")
            print(f"   Net Difference (Credit - Debit): ₹{net_difference}")
            
            # QR amount from the data
            qr_amount = 208.0
            print(f"   QR Amount: ₹{qr_amount}")
            print(f"   Difference from QR: ₹{abs(net_difference - qr_amount)}")
            print(f"   Within ±2 tolerance: {abs(net_difference - qr_amount) <= 2}")
            
            if abs(net_difference - qr_amount) <= 2:
                print("   ✅ Phase 3 should now resolve this loan!")
            else:
                print("   ❌ Phase 3 still won't resolve this loan")
                
            # Show some sample debit and credit transactions for debugging
            if not debit_df.empty:
                print(f"\n📋 Sample debit transactions:")
                sample_debits = debit_df.head(5)
                for _, row in sample_debits.iterrows():
                    print(f"   Loan {row['loan_id']}: ₹{row['amount']} - {row['original_narration'][:60]}...")
            
            if not credit_df.empty:
                print(f"\n📋 Sample credit transactions:")
                sample_credits = credit_df.head(5)
                for _, row in sample_credits.iterrows():
                    print(f"   Loan {row['loan_id']}: ₹{row['amount']} - {row['original_narration'][:60]}...")
        
        else:
            print(f"❌ Phase 3 processing failed: {phase3_result['message']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_updated_phase3_processor()