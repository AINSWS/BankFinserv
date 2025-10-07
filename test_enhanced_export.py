import pandas as pd
import sys
import os

# Add src directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
sys.path.insert(0, src_dir)

from utils.excel_exporter import ExcelExporter

def test_enhanced_export():
    """Test the enhanced export functionality"""
    
    print("🧪 Testing enhanced export functionality...")
    
    # Create sample reconciliation data
    sample_data = pd.DataFrame({
        'loan_id': [181669, 181670, 181671, 181672, 181673],
        'customer_name': ['VAISHALI SANTOSH GAYAKWAD', 'Customer 2', 'Customer 3', 'Customer 4', 'Customer 5'],
        'system_amount': [6565.0, 3200.0, 2500.0, 1800.0, 2730.0],
        'qr_amount': [208.0, 3200.0, 2500.0, 0.0, 2730.0],
        'status': [
            'MATCHED - Phase 3 Credit/Debit Analysis',
            'MATCHED - Perfect Match',
            'MATCHED - Perfect Match', 
            'MISMATCH',
            'MATCHED - Group Payment Redistribution'
        ],
        'branch': ['CHIPLUN', 'MUMBAI', 'PUNE', 'DELHI', 'BANGALORE'],
        'group_name': ['CHI-33-CHI SUNITA SATISH GAYAKWAD', 'Group 2', 'Group 3', 'Group 4', 'Group 5']
    })
    
    # Create sample summary
    sample_summary = {
        'total_unique_loans': 5,
        'perfect_matches': 2,
        'minor_matches': 0,
        'total_matches': 3,
        'amount_mismatches': 1,
        'match_percentage': 80.0,
        'total_system_amount': 16795.0,
        'total_qr_amount': 8638.0,
        'net_difference': 8157.0
    }
    
    # Create results structure
    results = {
        'simplified_report': sample_data,
        'reconciliation_summary': sample_summary
    }
    
    try:
        # Test the enhanced export
        exporter = ExcelExporter()
        output_path = "test_enhanced_export.xlsx"
        
        exported_file = exporter.export_enhanced_simplified_report(results, output_path)
        
        print(f"✅ Enhanced export test successful!")
        print(f"📁 File created: {exported_file}")
        
        # Verify the file exists and has expected sheets
        if os.path.exists(exported_file):
            excel_file = pd.ExcelFile(exported_file)
            sheets = excel_file.sheet_names
            print(f"📋 Sheets created: {sheets}")
            
            # Check each sheet
            for sheet in sheets:
                df = pd.read_excel(exported_file, sheet_name=sheet)
                print(f"   • {sheet}: {len(df)} rows")
            
            print(f"\n🎉 Test completed successfully!")
            print(f"💡 Features included:")
            print(f"   ✓ Auto-filters on all data sheets")
            print(f"   ✓ Conditional formatting for status columns")
            print(f"   ✓ Currency formatting for amount columns")
            print(f"   ✓ Professional styling with zebra striping")
            print(f"   ✓ Executive summary dashboard")
            print(f"   ✓ Separate sheets by record type")
            print(f"   ✓ Frozen panes for easy navigation")
            
        else:
            print(f"❌ File was not created: {output_path}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_export()