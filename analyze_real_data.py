"""
Analyze real data structure to fix column detection
"""
import pandas as pd
import sys
import os

# Add src path for imports
sys.path.append('src')
sys.path.append('src/reconciliation')

def analyze_real_files():
    """Analyze the structure of real data files"""
    print("=== ANALYZING REAL DATA FILES ===")
    print()
    
    # File paths
    bank_file = r'C:\Users\LENOVO\Downloads\14-08 bank ledger format.xlsx'
    qr_file = r'C:\Users\LENOVO\Downloads\14-08-2025 SIB QR CODE REPORT.xlsx'
    demand_file = r'C:\Users\LENOVO\Downloads\Demand Report August (2).csv'
    
    try:
        # Analyze Bank Ledger
        print("1. BANK LEDGER:")
        bank_df = pd.read_excel(bank_file)
        print(f"   Shape: {bank_df.shape}")
        print(f"   Columns: {list(bank_df.columns)}")
        print("   Sample narrations:")
        for i in range(min(5, len(bank_df))):
            print(f"      {i+1}. {bank_df.iloc[i]['Narration']}")
        print()
        
        # Analyze QR Report
        print("2. QR REPORT:")
        qr_df = pd.read_excel(qr_file)
        print(f"   Shape: {qr_df.shape}")
        print(f"   Columns: {list(qr_df.columns)}")
        if 'referenceID' in qr_df.columns:
            print("   Sample referenceIDs:")
            for i in range(min(5, len(qr_df))):
                print(f"      {i+1}. {qr_df.iloc[i]['referenceID']}")
        print()
        
        # Analyze Demand Report
        print("3. DEMAND REPORT:")
        demand_df = pd.read_csv(demand_file)
        print(f"   Shape: {demand_df.shape}")
        print(f"   Key columns: {[col for col in demand_df.columns if any(keyword in col.lower() for keyword in ['loan', 'id', 'amount', 'customer'])]}")
        if 'Loan ID' in demand_df.columns:
            print("   Sample Loan IDs:")
            unique_loans = demand_df['Loan ID'].unique()[:5]
            for i, loan_id in enumerate(unique_loans):
                print(f"      {i+1}. {loan_id}")
        print()
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

def test_with_real_data():
    """Test the reconciliation with real data"""
    print("=== TESTING WITH REAL DATA ===")
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
        
        print(f"Loaded data - Bank: {bank_df.shape}, QR: {qr_df.shape}, Demand: {demand_df.shape}")
        
        # Create engine
        engine = ModularReconciliationEngine(bank_df, qr_df, demand_df)
        
        # Test each processor
        print("\n1. Testing Bank Processor:")
        bank_result = engine.bank_processor.extract_bank_ledger_data()
        print(f"   Status: {bank_result.get('status')}")
        if bank_result.get('status') != 'success':
            print(f"   Error: {bank_result.get('debug_info', {}).get('error_message', 'Unknown')}")
        
        print("\n2. Testing SIB Processor:")
        sib_result = engine.sib_processor.analyze_sib_qr_report()
        print(f"   Status: {sib_result.get('status')}")
        if sib_result.get('status') != 'success':
            print(f"   Error: {sib_result.get('debug_info', {}).get('error_message', 'Unknown')}")
        
        print("\n3. Testing Demand Processor:")
        demand_result = engine.demand_processor.analyze_demand_report()
        print(f"   Status: {demand_result.get('status')}")
        if demand_result.get('status') != 'success':
            print(f"   Error: {demand_result.get('debug_info', {}).get('error_message', 'Unknown')}")
        
        print("\n4. Testing Full Reconciliation:")
        full_result = engine.merge_pivot_tables_comparison()
        print(f"   Status: {full_result.get('status')}")
        if full_result.get('status') == 'success':
            summary = full_result.get('reconciliation_summary', {})
            print(f"   Total loans: {summary.get('total_unique_loans', 0)}")
            print(f"   Matches: {summary.get('total_matches', 0)}")
            print(f"   Match rate: {summary.get('match_percentage', 0):.1f}%")
        else:
            print(f"   Error: {full_result.get('debug_info', {}).get('error_message', 'Unknown')}")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_real_files()
    print("\n" + "="*50 + "\n")
    test_with_real_data()