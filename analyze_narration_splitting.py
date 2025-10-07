import pandas as pd
import numpy as np

def analyze_bank_ledger_narration():
    """Analyze how narration field should be split for credit/debit processing"""
    
    print("🔍 Analyzing bank ledger narration splitting for loan 181669...")
    
    # Load the bank ledger data
    bank_ledger_file = 'src/bankLeasure.xlsx'
    
    try:
        # Read the bank ledger data (Sheet1 has the transaction details)
        bank_ledger_df = pd.read_excel(bank_ledger_file, sheet_name='Sheet1')
        print(f"✅ Loaded bank ledger: {bank_ledger_df.shape[0]} transactions")
        print(f"📋 Columns: {list(bank_ledger_df.columns)}")
        
        # Filter for loan 181669 transactions
        loan_181669_transactions = bank_ledger_df[
            bank_ledger_df['Narration'].astype(str).str.contains('181669', na=False)
        ].copy()
        
        print(f"\n🎯 Found {len(loan_181669_transactions)} transactions for loan 181669:")
        
        for idx, row in loan_181669_transactions.iterrows():
            print(f"\n📄 Transaction {idx + 1}:")
            print(f"   Date: {row['Transaction Date']}")
            print(f"   Ledger Head: {row['Ledger Head']}")
            print(f"   Narration: {row['Narration']}")
            print(f"   Debit: {row['Debit']}")
            print(f"   Credit: {row['Credit']}")
            
            # Split the narration by '/'
            narration_parts = str(row['Narration']).split('/')
            print(f"   Narration Split ({len(narration_parts)} parts): {narration_parts}")
            
            # Check which column contains the loan ID
            for i, part in enumerate(narration_parts):
                if '181669' in str(part):
                    print(f"   ✅ Loan ID found in position {i}: '{part.strip()}'")
            
            # Determine if this is debit or credit
            transaction_type = "DEBIT" if pd.notna(row['Debit']) and row['Debit'] != 0 else "CREDIT"
            print(f"   Transaction Type: {transaction_type}")
            
            if transaction_type == "DEBIT":
                if len(narration_parts) > 2:
                    print(f"   Expected loan ID in position 2 (for DEBIT): '{narration_parts[2].strip() if len(narration_parts) > 2 else 'N/A'}'")
                else:
                    print(f"   ⚠️ Not enough parts for DEBIT loan ID extraction")
            elif transaction_type == "CREDIT":
                if len(narration_parts) > 3:
                    print(f"   Expected loan ID in position 3 (for CREDIT): '{narration_parts[3].strip() if len(narration_parts) > 3 else 'N/A'}'")
                else:
                    print(f"   ⚠️ Not enough parts for CREDIT loan ID extraction")
        
        # Now let's test the splitting logic for all transactions
        print(f"\n🔧 Testing narration splitting logic on full dataset...")
        
        # Process debit transactions (loan ID in 2nd position after split)
        debit_transactions = bank_ledger_df[
            (pd.notna(bank_ledger_df['Debit'])) & 
            (bank_ledger_df['Debit'] != 0)
        ].copy()
        
        print(f"📊 Total debit transactions: {len(debit_transactions)}")
        
        debit_loan_ids = []
        for _, row in debit_transactions.iterrows():
            narration_parts = str(row['Narration']).split('/')
            if len(narration_parts) > 2:
                potential_loan_id = narration_parts[2].strip()
                # Check if it's a valid loan ID (numeric)
                if potential_loan_id.isdigit():
                    debit_loan_ids.append({
                        'loan_id': int(potential_loan_id),
                        'debit_amount': row['Debit'],
                        'narration': row['Narration']
                    })
        
        print(f"   ✅ Extracted {len(debit_loan_ids)} valid debit loan IDs")
        
        # Check if 181669 is in debit transactions
        debit_181669 = [x for x in debit_loan_ids if x['loan_id'] == 181669]
        print(f"   Loan 181669 in debit transactions: {len(debit_181669)}")
        for d in debit_181669:
            print(f"     Debit: ₹{d['debit_amount']} - {d['narration'][:100]}...")
        
        # Process credit transactions (loan ID in 3rd position after split)
        credit_transactions = bank_ledger_df[
            (pd.notna(bank_ledger_df['Credit'])) & 
            (bank_ledger_df['Credit'] != 0)
        ].copy()
        
        print(f"\n📊 Total credit transactions: {len(credit_transactions)}")
        
        credit_loan_ids = []
        for _, row in credit_transactions.iterrows():
            narration_parts = str(row['Narration']).split('/')
            if len(narration_parts) > 3:
                potential_loan_id = narration_parts[3].strip()
                # Check if it's a valid loan ID (numeric)
                if potential_loan_id.isdigit():
                    credit_loan_ids.append({
                        'loan_id': int(potential_loan_id),
                        'credit_amount': row['Credit'],
                        'narration': row['Narration']
                    })
        
        print(f"   ✅ Extracted {len(credit_loan_ids)} valid credit loan IDs")
        
        # Check if 181669 is in credit transactions
        credit_181669 = [x for x in credit_loan_ids if x['loan_id'] == 181669]
        print(f"   Loan 181669 in credit transactions: {len(credit_181669)}")
        for c in credit_181669:
            print(f"     Credit: ₹{c['credit_amount']} - {c['narration'][:100]}...")
        
        # Calculate net difference for loan 181669
        total_debit_181669 = sum([d['debit_amount'] for d in debit_181669])
        total_credit_181669 = sum([c['credit_amount'] for c in credit_181669])
        net_difference = total_credit_181669 - total_debit_181669
        
        print(f"\n💰 Loan 181669 Summary:")
        print(f"   Total Debit: ₹{total_debit_181669}")
        print(f"   Total Credit: ₹{total_credit_181669}")
        print(f"   Net Difference (Credit - Debit): ₹{net_difference}")
        
        # From the reconciliation data, QR amount is 208
        qr_amount = 208.0
        print(f"   QR Amount: ₹{qr_amount}")
        print(f"   Difference from QR: ₹{abs(net_difference - qr_amount)}")
        print(f"   Within ±2 tolerance: {abs(net_difference - qr_amount) <= 2}")
        
        if abs(net_difference - qr_amount) <= 2:
            print("   ✅ Phase 3 should resolve this loan!")
        else:
            print("   ❌ Phase 3 won't resolve this loan")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_bank_ledger_narration()