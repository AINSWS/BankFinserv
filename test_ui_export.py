#!/usr/bin/env python3
"""Test the actual UI export method with our simple data"""

import pandas as pd
import sys
import os
sys.path.insert(0, 'src')

# Create test data with the same structure as your reconciliation results
test_data = pd.DataFrame({
    'loan_id': [181669, 181670, 181671, 181672],
    'customer_name': ['VAISHALI SANTOSH GAYAKWAD', 'Customer 2', 'Customer 3', 'Customer 4'],
    'status': ['MATCHED - Perfect Match', 'MATCHED - Phase 3', 'MATCHED - Group Payment', 'MISMATCH - Amount'],
    'system_amount': [6565.0, 3200.0, 2730.0, 1800.0],
    'qr_amount': [6565.0, 3200.0, 2730.0, 0.0],
    'branch': ['CHIPLUN', 'MUMBAI', 'PUNE', 'DELHI'],
    'group_name': ['CHI-33-CHI SUNITA SATISH GAYAKWAD', 'Group 2', 'Group 3', 'Group 4']
})

sample_summary = {
    'total_unique_loans': 4,
    'perfect_matches': 1,
    'minor_matches': 0,
    'total_matches': 3,
    'amount_mismatches': 1,
    'match_percentage': 75.0
}

results = {'simplified_report': test_data, 'reconciliation_summary': sample_summary}

# Test the export directly
try:
    print("🧪 Testing UI export method...")
    
    # Import the UI class
    from ui_modular import BankReconciliationUI
    
    # Create a mock UI instance
    ui = BankReconciliationUI()
    
    # Mock the file dialog to return a test file path
    import tkinter.filedialog as filedialog
    import unittest.mock
    
    test_file_path = "test_ui_export.xlsx"
    
    with unittest.mock.patch.object(filedialog, 'asksaveasfilename', return_value=test_file_path):
        with unittest.mock.patch('tkinter.messagebox.showinfo'):
            ui._export_simple_results(results)
    
    print(f"✅ Export completed! Check file: {test_file_path}")
    
    # Verify the file exists and check its contents
    if os.path.exists(test_file_path):
        excel_file = pd.ExcelFile(test_file_path)
        print(f"📋 Sheets created: {excel_file.sheet_names}")
        for sheet in excel_file.sheet_names:
            df = pd.read_excel(test_file_path, sheet_name=sheet)
            print(f"   • {sheet}: {len(df)} rows")
    else:
        print("❌ Export file not found!")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()