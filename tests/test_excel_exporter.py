"""
Test script for Excel Exporter utility
=====================================

This script tests the Excel export functionality with sample data.
Run this to verify the exporter is working correctly.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

import pandas as pd
from utils.excel_exporter import ExcelExporter
from datetime import datetime, timedelta
import random

def create_sample_reconciliation_data():
    """Create comprehensive sample data for testing"""
    
    # Sample bank ledger data
    bank_data = []
    for i in range(100):
        bank_data.append({
            'Date': (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
            'Description': f'Transaction {i+1}',
            'Debit': random.randint(1000, 50000) if random.choice([True, False]) else None,
            'Credit': random.randint(1000, 50000) if random.choice([True, False]) else None,
            'Balance': random.randint(10000, 500000),
            'Reference': f'REF{i+1:04d}'
        })
    
    # Sample SIB QR data
    sib_data = []
    for i in range(80):
        sib_data.append({
            'Transaction Date': (datetime.now() - timedelta(days=random.randint(1, 25))).strftime('%Y-%m-%d'),
            'Payer VPA': f'user{i+1}@paytm',
            'Payer Name': f'Customer {i+1}',
            'RRN': f'RRN{i+1:08d}',
            'Reference ID': f'LOAN{i+1:06d}',
            'Amount': random.randint(5000, 100000),
            'Status': random.choice(['Success', 'Pending'])
        })
    
    # Sample demand report data
    demand_data = []
    branches = ['Branch A', 'Branch B', 'Branch C', 'Branch D']
    groups = ['Group 1', 'Group 2', 'Group 3', 'Group 4', 'Group 5']
    
    for i in range(60):
        demand_data.append({
            'Loan ID': f'LOAN{i+1:06d}',
            'Branch Name': random.choice(branches),
            'Group Name': random.choice(groups),
            'Member Name': f'Member {i+1}',
            'Amount Due': random.randint(5000, 75000),
            'Due Date': (datetime.now() + timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
        })
    
    # Create merged data (simulate successful merge)
    merged_data = []
    for i in range(50):  # 50 successful matches
        sib_record = sib_data[i] if i < len(sib_data) else sib_data[0]
        demand_record = demand_data[i] if i < len(demand_data) else demand_data[0]
        
        merged_record = {**sib_record, **demand_record}
        merged_data.append(merged_record)
    
    # Create sample reconciliation result
    return {
        'bank_ledger': {
            'filtered_data': {
                'data': pd.DataFrame(bank_data),
                'total_rows': len(bank_data)
            },
            'date_range': {
                'start': '2025-09-01',
                'end': '2025-10-06'
            }
        },
        'sib_qr_report': {
            'processed_data': {
                'data': pd.DataFrame(sib_data),
                'total_rows': len(sib_data)
            },
            'loan_id_stats': {
                'valid_loan_ids': 78,
                'success_rate': 97.5
            }
        },
        'demand_report': {
            'processed_data': {
                'data': pd.DataFrame(demand_data),
                'total_rows': len(demand_data)
            }
        },
        'merged_sib_demand': {
            'status': 'success',
            'merged_data': pd.DataFrame(merged_data),
            'merge_stats': {
                'sib_records': len(sib_data),
                'demand_records': len(demand_data),
                'matched_records': len(merged_data),
                'match_rate': (len(merged_data) / len(sib_data)) * 100,
                'unmatched_sib_records': len(sib_data) - len(merged_data),
                'merge_efficiency': 85.5
            }
        },
        'matches': {
            'bank_sib_matches': [
                {'bank_ref': f'REF{i:04d}', 'sib_rrn': f'RRN{i:08d}', 'amount': random.randint(5000, 50000)}
                for i in range(1, 26)  # 25 matches
            ],
            'bank_demand_matches': [
                {'bank_ref': f'REF{i:04d}', 'loan_id': f'LOAN{i:06d}', 'amount': random.randint(5000, 50000)}
                for i in range(1, 21)  # 20 matches
            ]
        },
        'summary_stats': {
            'total_bank_transactions': len(bank_data),
            'total_sib_transactions': len(sib_data),
            'total_demand_entries': len(demand_data),
            'bank_sib_matches': 25,
            'bank_demand_matches': 20,
            'match_percentage': 45.0
        }
    }

def test_excel_export():
    """Test the Excel export functionality"""
    print("🧪 Testing Excel Exporter...")
    
    # Create output directory for tests
    test_output_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'test_exports')
    
    # Initialize exporter
    exporter = ExcelExporter(output_dir=test_output_dir)
    
    # Create sample data
    print("📊 Creating sample reconciliation data...")
    sample_data = create_sample_reconciliation_data()
    
    # Test 1: Full reconciliation report export
    print("\n1️⃣ Testing full reconciliation report export...")
    report_file = exporter.export_reconciliation_report(
        sample_data, 
        'test_reconciliation_report.xlsx'
    )
    print(f"✅ Full report exported: {report_file}")
    
    # Test 2: Single DataFrame export
    print("\n2️⃣ Testing single DataFrame export...")
    single_df_file = exporter.export_dataframe(
        sample_data['sib_qr_report']['processed_data']['data'],
        'test_sib_data.xlsx',
        'SIB QR Data'
    )
    print(f"✅ Single DataFrame exported: {single_df_file}")
    
    # Test 3: Multiple DataFrames export
    print("\n3️⃣ Testing multiple DataFrames export...")
    multiple_dfs = {
        'Bank Ledger': sample_data['bank_ledger']['filtered_data']['data'],
        'SIB QR Report': sample_data['sib_qr_report']['processed_data']['data'],
        'Demand Report': sample_data['demand_report']['processed_data']['data']
    }
    multi_df_file = exporter.export_multiple_dataframes(
        multiple_dfs,
        'test_multiple_sheets.xlsx'
    )
    print(f"✅ Multiple DataFrames exported: {multi_df_file}")
    
    # Test 4: Template creation
    print("\n4️⃣ Testing template creation...")
    template_file = exporter.create_template_file('reconciliation')
    print(f"✅ Template created: {template_file}")
    
    # Test 5: Individual sheet templates
    print("\n5️⃣ Testing individual templates...")
    for template_type in ['bank_ledger', 'sib_qr', 'demand']:
        template_file = exporter.create_template_file(template_type)
        print(f"✅ {template_type} template created: {os.path.basename(template_file)}")
    
    print(f"\n🎉 All tests completed successfully!")
    print(f"📁 Check the test exports in: {test_output_dir}")
    
    return True

if __name__ == "__main__":
    try:
        test_excel_export()
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()