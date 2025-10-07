"""
Excel Export Integration Example
===============================

This example shows how to use the Excel export functionality
in your bank reconciliation application.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
from reconciliation.engine import ReconciliationEngine
from utils.excel_exporter import ExcelExporter

def example_usage():
    """Example of how to use Excel export in your application"""
    
    # Sample data (replace with your actual data loading)
    print("📂 Loading sample data...")
    
    # Create sample DataFrames (replace with your actual data)
    bank_data = pd.DataFrame({
        'Date': ['2025-10-01', '2025-10-02', '2025-10-03'],
        'Description': ['Transaction 1', 'Transaction 2', 'Transaction 3'],
        'Debit': [10000, None, 15000],
        'Credit': [None, 8000, None],
        'Balance': [50000, 58000, 43000]
    })
    
    sib_data = pd.DataFrame({
        'Transaction Date': ['2025-10-01', '2025-10-02'],
        'Payer VPA': ['user1@paytm', 'user2@gpay'],
        'Payer Name': ['Customer 1', 'Customer 2'],
        'RRN': ['RRN001', 'RRN002'],
        'Reference ID': ['LOAN001', 'LOAN002'],
        'Amount': [10000, 8000]
    })
    
    demand_data = pd.DataFrame({
        'Loan ID': ['LOAN001', 'LOAN002', 'LOAN003'],
        'Branch Name': ['Branch A', 'Branch B', 'Branch A'],
        'Group Name': ['Group 1', 'Group 2', 'Group 1'],
        'Member Name': ['Member 1', 'Member 2', 'Member 3'],
        'Amount Due': [10000, 8000, 12000]
    })
    
    # Initialize reconciliation engine
    print("🔧 Initializing reconciliation engine...")
    engine = ReconciliationEngine(bank_data, sib_data, demand_data)
    
    # Method 1: Export complete reconciliation report
    print("\n📊 Method 1: Export complete reconciliation report")
    output_file = engine.export_reconciliation_to_excel(
        output_filename="my_reconciliation_report.xlsx",
        output_dir="./exports"
    )
    print(f"Complete report saved to: {output_file}")
    
    # Method 2: Export individual sheets
    print("\n📊 Method 2: Export individual analysis sheets")
    individual_exports = engine.export_individual_sheets(
        sheet_types=['bank_ledger', 'sib_qr', 'merged_data'],
        output_dir="./individual_exports"
    )
    print("Individual exports:")
    for sheet_type, path in individual_exports.items():
        print(f"  - {sheet_type}: {path}")
    
    # Method 3: Direct ExcelExporter usage for custom exports
    print("\n📊 Method 3: Custom export using ExcelExporter directly")
    exporter = ExcelExporter(output_dir="./custom_exports")
    
    # Export multiple DataFrames to one file
    custom_data = {
        'Raw Bank Data': bank_data,
        'Raw SIB Data': sib_data,
        'Raw Demand Data': demand_data
    }
    custom_file = exporter.export_multiple_dataframes(
        custom_data, 
        "raw_data_export.xlsx"
    )
    print(f"Custom export saved to: {custom_file}")
    
    # Method 4: Create templates
    print("\n📊 Method 4: Create input templates")
    template_file = exporter.create_template_file('reconciliation')
    print(f"Template created: {template_file}")
    
    print("\n✅ All export examples completed successfully!")
    print("\n📁 Check the following directories for exports:")
    print("  - ./exports/ - Complete reconciliation reports")
    print("  - ./individual_exports/ - Individual analysis sheets")
    print("  - ./custom_exports/ - Custom exports and templates")


if __name__ == "__main__":
    try:
        example_usage()
    except Exception as e:
        print(f"❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()