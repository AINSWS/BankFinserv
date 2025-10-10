"""
Excel Export Utility for Bank Reconciliation System
==================================================

This module provides comprehensive Excel export functionality for bank reconciliation data.
Supports multiple sheets, custom formatting, summary reports, and detailed transaction exports.

Author: Bank Reconciliation System
Date: October 2025
"""

import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.formatting.rule import ColorScaleRule, CellIsRule
from openpyxl.chart import BarChart, Reference
from datetime import datetime
import os
from typing import Dict, List, Optional, Any, Union
import logging

class ExcelExporter:
    """
    Advanced Excel export utility for bank reconciliation data
    
    Features:
    - Multi-sheet exports with custom formatting
    - Summary dashboards with charts
    - Conditional formatting for data visualization
    - Automated column sizing and styling
    - Export templates for different report types
    """
    
    def __init__(self, output_dir: str = None):
        """
        Initialize Excel Exporter
        
        Args:
            output_dir (str): Directory for output files. Defaults to current directory.
        """
        self.output_dir = output_dir or os.getcwd()
        self.default_styles = self._create_default_styles()
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _create_default_styles(self) -> Dict:
        """Create default styling configurations"""
        return {
            'header': {
                'font': Font(bold=True, color='FFFFFF', size=12),
                'fill': PatternFill(start_color='366092', end_color='366092', fill_type='solid'),
                'alignment': Alignment(horizontal='center', vertical='center'),
                'border': Border(
                    left=Side(style='thin'),
                    right=Side(style='thin'),
                    top=Side(style='thin'),
                    bottom=Side(style='thin')
                )
            },
            'data': {
                'font': Font(size=10),
                'alignment': Alignment(horizontal='left', vertical='center'),
                'border': Border(
                    left=Side(style='thin', color='D3D3D3'),
                    right=Side(style='thin', color='D3D3D3'),
                    top=Side(style='thin', color='D3D3D3'),
                    bottom=Side(style='thin', color='D3D3D3')
                )
            },
            'summary': {
                'font': Font(bold=True, size=11),
                'fill': PatternFill(start_color='E6F3FF', end_color='E6F3FF', fill_type='solid'),
                'alignment': Alignment(horizontal='center', vertical='center')
            },
            'matched': {
                'fill': PatternFill(start_color='C6EFCE', end_color='C6EFCE', fill_type='solid')
            },
            'unmatched': {
                'fill': PatternFill(start_color='FFC7CE', end_color='FFC7CE', fill_type='solid')
            }
        }
    
    def export_reconciliation_report(self, reconciliation_data: Dict, filename: str = None) -> str:
        """
        Export comprehensive reconciliation report to Excel
        
        Args:
            reconciliation_data (Dict): Complete reconciliation data from ReconciliationEngine
            filename (str): Output filename. Auto-generated if not provided.
            
        Returns:
            str: Path to the exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Bank_Reconciliation_Report_{timestamp}.xlsx"
        
        filepath = os.path.join(self.output_dir, filename)
        
        print(f"📊 Exporting reconciliation report to: {filename}")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: Executive Summary
            self._create_summary_sheet(writer, reconciliation_data)
            
            # Sheet 2: Bank Ledger Analysis
            if 'bank_ledger' in reconciliation_data:
                self._export_bank_ledger_sheet(writer, reconciliation_data['bank_ledger'])
            
            # Sheet 3: SIB QR Report Analysis
            if 'sib_qr_report' in reconciliation_data:
                self._export_sib_qr_sheet(writer, reconciliation_data['sib_qr_report'])
            
            # Sheet 4: Demand Report Analysis
            if 'demand_report' in reconciliation_data:
                self._export_demand_report_sheet(writer, reconciliation_data['demand_report'])
            
            # Sheet 5: Merged SIB + Demand Data
            if 'merged_sib_demand' in reconciliation_data:
                self._export_merged_data_sheet(writer, reconciliation_data['merged_sib_demand'])
            
            # Sheet 6: Transaction Matches
            if 'matches' in reconciliation_data:
                self._export_matches_sheet(writer, reconciliation_data['matches'])
        
        # Apply advanced formatting
        self._apply_advanced_formatting(filepath)
        
        print(f"✅ Reconciliation report exported successfully!")
        print(f"📁 File location: {filepath}")
        
        return filepath
    
    def export_enhanced_reconciliation_report(self, reconciliation_result: Dict, mismatched_analysis: Dict = None, filename: str = None) -> str:
        """
        Export enhanced reconciliation report with separate mismatched entries and ±3 tolerance analysis
        
        Args:
            reconciliation_result (Dict): Main reconciliation result from merge_pivot_tables
            mismatched_analysis (Dict): Detailed mismatch analysis from extract_mismatched_entries
            filename (str): Output filename. Auto-generated if not provided.
            
        Returns:
            str: Path to the exported file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Enhanced_Reconciliation_Report_{timestamp}.xlsx"
        
        filepath = os.path.join(self.output_dir, filename)
        
        print(f"📊 Exporting enhanced reconciliation report to: {filename}")
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Sheet 1: Executive Summary with Enhanced Metrics
            self._create_enhanced_summary_sheet(writer, reconciliation_result, mismatched_analysis)
            
            # Sheet 2: Complete Reconciliation Data
            if reconciliation_result.get('merged_pivot_data') is not None:
                df = reconciliation_result['merged_pivot_data'].copy()
                df.to_excel(writer, sheet_name='Complete_Reconciliation', index=False)
                print(f"   ✓ Complete reconciliation data exported ({len(df)} entries)")
            
            # Sheet 3: Perfect Matches
            if mismatched_analysis and mismatched_analysis.get('mismatch_breakdown'):
                perfect_matches = mismatched_analysis['mismatch_breakdown']['perfect_matches']['data']
                if not perfect_matches.empty:
                    perfect_matches.to_excel(writer, sheet_name='Perfect_Matches', index=False)
                    print(f"   ✓ Perfect matches exported ({len(perfect_matches)} entries)")
            
            # Sheet 4: Minor Matches (±3 tolerance)
            if mismatched_analysis and mismatched_analysis.get('mismatch_breakdown'):
                minor_matches = mismatched_analysis['mismatch_breakdown']['minor_matches']['data']
                if not minor_matches.empty:
                    minor_matches.to_excel(writer, sheet_name='Minor_Matches_Tolerance3', index=False)
                    print(f"   ✓ Minor matches exported ({len(minor_matches)} entries)")
            
            # Sheet 5: Amount Mismatches (REQUIRES INVESTIGATION)
            if mismatched_analysis and mismatched_analysis.get('mismatch_breakdown'):
                amount_mismatches = mismatched_analysis['mismatch_breakdown']['amount_mismatches']['data']
                if not amount_mismatches.empty:
                    amount_mismatches.to_excel(writer, sheet_name='Amount_Mismatches', index=False)
                    print(f"   ✓ Amount mismatches exported ({len(amount_mismatches)} entries) - REQUIRES INVESTIGATION")
            
            # Sheet 6: Bank Only Entries
            if mismatched_analysis and mismatched_analysis.get('mismatch_breakdown'):
                bank_only = mismatched_analysis['mismatch_breakdown']['bank_only']['data']
                if not bank_only.empty:
                    bank_only.to_excel(writer, sheet_name='Bank_Only_Entries', index=False)
                    print(f"   ✓ Bank only entries exported ({len(bank_only)} entries)")
            
            # Sheet 7: QR Only Entries
            if mismatched_analysis and mismatched_analysis.get('mismatch_breakdown'):
                qr_only = mismatched_analysis['mismatch_breakdown']['qr_only']['data']
                if not qr_only.empty:
                    qr_only.to_excel(writer, sheet_name='QR_Only_Entries', index=False)
                    print(f"   ✓ QR only entries exported ({len(qr_only)} entries)")
        
        # Apply enhanced formatting
        self._apply_enhanced_reconciliation_formatting(filepath, mismatched_analysis)
        
        print(f"✅ Enhanced reconciliation report exported successfully!")
        print(f"📁 File location: {filepath}")
        print(f"📊 Report includes: Complete data + Separate mismatch categories with ±3 tolerance")
        
        return filepath
    
    def _create_enhanced_summary_sheet(self, writer: pd.ExcelWriter, reconciliation_result: Dict, mismatched_analysis: Dict):
        """Create enhanced summary sheet with detailed mismatch analysis"""
        summary = reconciliation_result.get('reconciliation_summary', {})
        
        # Create enhanced summary data
        summary_data = [
            ['ENHANCED BANK RECONCILIATION REPORT', ''],
            ['Report Generated', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ['Tolerance Level', '±3 (Enhanced from ±1)'],
            ['', ''],
            ['RECONCILIATION OVERVIEW', ''],
            ['Total Unique Loans', summary.get('total_unique_loans', 0)],
            ['Perfect Matches', summary.get('perfect_matches', 0)],
            ['Minor Matches (±3)', summary.get('minor_matches', 0)],
            ['Total Matches', summary.get('total_matches', 0)],
            ['Match Percentage', f"{summary.get('match_percentage', 0):.1f}%"],
            ['', ''],
            ['DISCREPANCIES REQUIRING INVESTIGATION', ''],
            ['Amount Mismatches (>±3)', summary.get('amount_mismatches', 0)],
            ['Bank Only Entries', summary.get('bank_only_entries', 0)],
            ['QR Only Entries', summary.get('qr_only_entries', 0)],
            ['', ''],
            ['FINANCIAL SUMMARY', ''],
            ['Total System Amount', f"₹{summary.get('total_system_amount', 0):,.2f}"],
            ['Total QR Amount', f"₹{summary.get('total_qr_amount', 0):,.2f}"],
            ['Net Difference', f"₹{summary.get('net_amount_difference', 0):,.2f}"],
        ]
        
        # Add detailed mismatch statistics if available
        if mismatched_analysis and mismatched_analysis.get('summary_stats'):
            stats = mismatched_analysis['summary_stats']
            summary_data.extend([
                ['', ''],
                ['DETAILED MISMATCH ANALYSIS', ''],
                ['Total Entries Analyzed', stats.get('total_entries', 0)],
                ['Total Matched Entries', stats.get('total_matched', 0)],
                ['Total Mismatched Entries', stats.get('total_mismatched', 0)],
                ['System Amount Higher', stats.get('system_higher_count', 0)],
                ['QR Amount Higher', stats.get('qr_higher_count', 0)],
            ])
        
        summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Executive_Summary', index=False)
    
    def _apply_enhanced_reconciliation_formatting(self, filepath: str, mismatched_analysis: Dict):
        """Apply enhanced formatting to reconciliation report"""
        try:
            workbook = openpyxl.load_workbook(filepath)
            
            # Format each sheet
            for sheet_name in workbook.sheetnames:
                worksheet = workbook[sheet_name]
                
                if sheet_name == 'Executive_Summary':
                    self._format_summary_sheet(worksheet)
                elif sheet_name == 'Complete_Reconciliation':
                    self._format_reconciliation_sheet(worksheet)
                elif 'Matches' in sheet_name:
                    self._format_matches_sheet(worksheet)
                elif 'Mismatches' in sheet_name:
                    self._format_mismatches_sheet(worksheet)
                else:
                    self._apply_basic_formatting(worksheet)
            
            workbook.save(filepath)
            print(f"   ✓ Enhanced formatting applied to all sheets")
            
        except Exception as e:
            print(f"   ⚠️ Warning: Could not apply enhanced formatting: {str(e)}")
    
    def _create_summary_sheet(self, writer: pd.ExcelWriter, data: Dict):
        """Create executive summary dashboard sheet"""
        summary_stats = data.get('summary_stats', {})
        
        # Create summary DataFrame
        summary_data = [
            ['Report Generated', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            ['', ''],
            ['TRANSACTION COUNTS', ''],
            ['Total Bank Transactions', summary_stats.get('total_bank_transactions', 0)],
            ['Total SIB Transactions', summary_stats.get('total_sib_transactions', 0)],
            ['Total Demand Entries', summary_stats.get('total_demand_entries', 0)],
            ['', ''],
            ['MATCHING RESULTS', ''],
            ['Bank-SIB Matches', summary_stats.get('bank_sib_matches', 0)],
            ['Bank-Demand Matches', summary_stats.get('bank_demand_matches', 0)],
            ['Overall Match Rate', f"{summary_stats.get('match_percentage', 0):.2f}%"],
            ['', ''],
            ['MERGE STATISTICS', ''],
        ]
        
        # Add merge statistics if available
        if 'merged_sib_demand' in data and data['merged_sib_demand'].get('merge_stats'):
            merge_stats = data['merged_sib_demand']['merge_stats']
            summary_data.extend([
                ['SIB-Demand Merge Rate', f"{merge_stats.get('match_rate', 0):.2f}%"],
                ['Merged Records', merge_stats.get('matched_records', 0)],
                ['Unmatched SIB Records', merge_stats.get('unmatched_sib_records', 0)]
            ])
        
        summary_df = pd.DataFrame(summary_data, columns=['Metric', 'Value'])
        summary_df.to_excel(writer, sheet_name='Executive Summary', index=False)
    
    def _export_bank_ledger_sheet(self, writer: pd.ExcelWriter, bank_data: Dict):
        """Export bank ledger analysis to dedicated sheet"""
        if bank_data.get('filtered_data') and bank_data['filtered_data'].get('data') is not None:
            df = bank_data['filtered_data']['data']
            df.to_excel(writer, sheet_name='Bank Ledger', index=False)
            
            # Add analysis summary at the top
            analysis_summary = [
                ['BANK LEDGER ANALYSIS', ''],
                ['Total Transactions', bank_data['filtered_data'].get('total_rows', 0)],
                ['Date Range', f"{bank_data.get('date_range', {}).get('start', 'N/A')} to {bank_data.get('date_range', {}).get('end', 'N/A')}"],
                ['', '']
            ]
            
            # Insert summary at the top
            workbook = writer.book
            worksheet = workbook['Bank Ledger']
            worksheet.insert_rows(1, len(analysis_summary))
            
            for i, (metric, value) in enumerate(analysis_summary, 1):
                worksheet.cell(row=i, column=1, value=metric)
                worksheet.cell(row=i, column=2, value=value)
    
    def _export_sib_qr_sheet(self, writer: pd.ExcelWriter, sib_data: Dict):
        """Export SIB QR report analysis to dedicated sheet"""
        if sib_data.get('processed_data') and sib_data['processed_data'].get('data') is not None:
            df = sib_data['processed_data']['data']
            df.to_excel(writer, sheet_name='SIB QR Report', index=False)
            
            # Add processing statistics
            processing_stats = [
                ['SIB QR REPORT ANALYSIS', ''],
                ['Total Records', sib_data['processed_data'].get('total_rows', 0)],
                ['Valid Loan IDs', sib_data.get('loan_id_stats', {}).get('valid_loan_ids', 0)],
                ['Processing Success Rate', f"{sib_data.get('loan_id_stats', {}).get('success_rate', 0):.2f}%"],
                ['', '']
            ]
            
            workbook = writer.book
            worksheet = workbook['SIB QR Report']
            worksheet.insert_rows(1, len(processing_stats))
            
            for i, (metric, value) in enumerate(processing_stats, 1):
                worksheet.cell(row=i, column=1, value=metric)
                worksheet.cell(row=i, column=2, value=value)
    
    def _export_demand_report_sheet(self, writer: pd.ExcelWriter, demand_data: Dict):
        """Export demand report analysis to dedicated sheet"""
        if demand_data.get('processed_data') and demand_data['processed_data'].get('data') is not None:
            df = demand_data['processed_data']['data']
            df.to_excel(writer, sheet_name='Demand Report', index=False)
    
    def _export_merged_data_sheet(self, writer: pd.ExcelWriter, merged_data: Dict):
        """Export merged SIB + Demand data to dedicated sheet"""
        if merged_data.get('merged_data') is not None:
            df = merged_data['merged_data']
            df.to_excel(writer, sheet_name='Merged SIB+Demand', index=False)
            
            # Add merge statistics
            merge_stats = merged_data.get('merge_stats', {})
            stats_data = [
                ['MERGE ANALYSIS', ''],
                ['Total SIB Records', merge_stats.get('sib_records', 0)],
                ['Total Demand Records', merge_stats.get('demand_records', 0)],
                ['Successful Matches', merge_stats.get('matched_records', 0)],
                ['Match Rate', f"{merge_stats.get('match_rate', 0):.2f}%"],
                ['Unmatched SIB Records', merge_stats.get('unmatched_sib_records', 0)],
                ['', '']
            ]
            
            workbook = writer.book
            worksheet = workbook['Merged SIB+Demand']
            worksheet.insert_rows(1, len(stats_data))
            
            for i, (metric, value) in enumerate(stats_data, 1):
                worksheet.cell(row=i, column=1, value=metric)
                worksheet.cell(row=i, column=2, value=value)
    
    def _export_matches_sheet(self, writer: pd.ExcelWriter, matches_data: Dict):
        """Export transaction matches to dedicated sheet"""
        # Bank-SIB matches
        if matches_data.get('bank_sib_matches'):
            df = pd.DataFrame(matches_data['bank_sib_matches'])
            df.to_excel(writer, sheet_name='Bank-SIB Matches', index=False)
        
        # Bank-Demand matches  
        if matches_data.get('bank_demand_matches'):
            df = pd.DataFrame(matches_data['bank_demand_matches'])
            df.to_excel(writer, sheet_name='Bank-Demand Matches', index=False)
    
    def _apply_advanced_formatting(self, filepath: str):
        """Apply advanced formatting to the exported Excel file"""
        try:
            workbook = openpyxl.load_workbook(filepath)
            
            for sheet_name in workbook.sheetnames:
                worksheet = workbook[sheet_name]
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Apply header formatting
                if worksheet.max_row > 0:
                    for cell in worksheet[1]:
                        if cell.value:
                            cell.font = self.default_styles['header']['font']
                            cell.fill = self.default_styles['header']['fill']
                            cell.alignment = self.default_styles['header']['alignment']
                            cell.border = self.default_styles['header']['border']
                
                # Apply data formatting
                for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row):
                    for cell in row:
                        if cell.value is not None:
                            cell.border = self.default_styles['data']['border']
                            cell.alignment = self.default_styles['data']['alignment']
                            cell.font = self.default_styles['data']['font']
            
            workbook.save(filepath)
            
        except Exception as e:
            self.logger.warning(f"Could not apply advanced formatting: {str(e)}")
    
    def export_dataframe(self, df: pd.DataFrame, filename: str, sheet_name: str = 'Data', 
                        apply_formatting: bool = True) -> str:
        """
        Export a single DataFrame to Excel with optional formatting
        
        Args:
            df (pd.DataFrame): DataFrame to export
            filename (str): Output filename
            sheet_name (str): Sheet name for the data
            apply_formatting (bool): Whether to apply styling
            
        Returns:
            str: Path to exported file
        """
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        if apply_formatting:
            self._apply_advanced_formatting(filepath)
        
        print(f"✅ DataFrame exported to: {filename}")
        return filepath
    
    def export_multiple_dataframes(self, dataframes: Dict[str, pd.DataFrame], 
                                 filename: str, apply_formatting: bool = True) -> str:
        """
        Export multiple DataFrames to different sheets in one Excel file
        
        Args:
            dataframes (Dict[str, pd.DataFrame]): Dictionary of sheet_name -> DataFrame
            filename (str): Output filename
            apply_formatting (bool): Whether to apply styling
            
        Returns:
            str: Path to exported file
        """
        filepath = os.path.join(self.output_dir, filename)
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, df in dataframes.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        if apply_formatting:
            self._apply_advanced_formatting(filepath)
        
        print(f"✅ Multiple DataFrames exported to: {filename}")
        return filepath
    
    def create_template_file(self, template_type: str = 'reconciliation') -> str:
        """
        Create a template Excel file for data input
        
        Args:
            template_type (str): Type of template ('reconciliation', 'bank_ledger', 'sib_qr', 'demand')
            
        Returns:
            str: Path to template file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{template_type}_template_{timestamp}.xlsx"
        filepath = os.path.join(self.output_dir, filename)
        
        templates = {
            'reconciliation': {
                'Bank Ledger': ['Date', 'Description', 'Debit', 'Credit', 'Balance'],
                'SIB QR Report': ['Transaction Date', 'Payer VPA', 'Payer Name', 'RRN', 'Reference ID', 'Amount'],
                'Demand Report': ['Loan ID', 'Branch Name', 'Group Name', 'Member Name', 'Amount Due']
            },
            'bank_ledger': {
                'Bank Ledger': ['Date', 'Description', 'Debit', 'Credit', 'Balance', 'Reference']
            },
            'sib_qr': {
                'SIB QR Report': ['Transaction Date', 'Payer VPA', 'Payer Name', 'RRN', 'Reference ID', 'Amount', 'Status']
            },
            'demand': {
                'Demand Report': ['Loan ID', 'Branch Name', 'Group Name', 'Member Name', 'Amount Due', 'Due Date']
            }
        }
        
        template_sheets = templates.get(template_type, templates['reconciliation'])
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            for sheet_name, columns in template_sheets.items():
                df = pd.DataFrame(columns=columns)
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        self._apply_advanced_formatting(filepath)
        
        print(f"✅ Template created: {filename}")
        return filepath
    
    def _format_summary_sheet(self, worksheet):
        """Format the executive summary sheet"""
        # Header formatting
        for cell in worksheet[1]:
            if cell.value:
                cell.font = Font(bold=True, size=12, color="FFFFFF")
                cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Bold key metrics
        for row in worksheet.iter_rows():
            if row[0].value and any(keyword in str(row[0].value) for keyword in ['OVERVIEW', 'DISCREPANCIES', 'FINANCIAL', 'ANALYSIS']):
                row[0].font = Font(bold=True, size=11, color="000080")
    
    def _format_reconciliation_sheet(self, worksheet):
        """Format the main reconciliation data sheet"""
        # Header row
        for cell in worksheet[1]:
            if cell.value:
                cell.font = Font(bold=True, size=10, color="FFFFFF")
                cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
        
        # Conditional formatting for reconciliation status
        if worksheet.max_row > 1:
            # Find reconciliation_status column
            for col_idx, cell in enumerate(worksheet[1], 1):
                if cell.value and 'reconciliation_status' in str(cell.value).lower():
                    col_letter = openpyxl.utils.get_column_letter(col_idx)
                    
                    # Apply conditional formatting
                    for row in range(2, worksheet.max_row + 1):
                        cell = worksheet[f"{col_letter}{row}"]
                        if cell.value:
                            if "MATCHED - Perfect" in str(cell.value):
                                cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                            elif "MATCHED - Minor" in str(cell.value):
                                cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                            elif "MISMATCH" in str(cell.value):
                                cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    break
    
    def _format_matches_sheet(self, worksheet):
        """Format sheets containing matched entries"""
        # Header formatting
        for cell in worksheet[1]:
            if cell.value:
                cell.font = Font(bold=True, size=10, color="FFFFFF")
                cell.fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
    
    def _format_mismatches_sheet(self, worksheet):
        """Format sheets containing mismatched entries"""
        # Header formatting with red theme for attention
        for cell in worksheet[1]:
            if cell.value:
                cell.font = Font(bold=True, size=10, color="FFFFFF")
                cell.fill = PatternFill(start_color="C5504B", end_color="C5504B", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
    
    def export_enhanced_simplified_report(self, results: Dict, file_path: str) -> str:
        """
        Export enhanced simplified reconciliation report with professional formatting
        
        Args:
            results (Dict): Reconciliation results dictionary
            file_path (str): Full path for the output file
            
        Returns:
            str: Path to exported file
        """
        try:
            print(f"📊 Creating enhanced reconciliation report...")
            
            # Get the main reconciliation data
            main_data = None
            if results:
                for key in ['simplified_report', 'merged_pivot_data', 'comparison_data', 'final_data']:
                    if key in results and results[key] is not None:
                        main_data = results[key]
                        print(f"   Using data from key '{key}', shape: {main_data.shape if hasattr(main_data, 'shape') else 'unknown'}")
                        break
            
            summary = results.get('reconciliation_summary', {}) if results else {}
            
            if main_data is None:
                raise ValueError("No reconciliation data available to export")
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                # Sheet 1: Executive Summary
                self._create_executive_summary_sheet(writer, summary, main_data)
                
                # Sheet 2: All Records with enhanced filtering
                if hasattr(main_data, 'empty') and not main_data.empty:
                    # Add summary columns for better analysis
                    enhanced_data = main_data.copy()
                    
                    # Handle both system_entry/qr_collection and system_amount/qr_amount columns
                    amount_pairs = [
                        ('system_entry', 'qr_collection'),
                        ('system_amount', 'qr_amount')
                    ]
                    
                    for sys_col, qr_col in amount_pairs:
                        if sys_col in enhanced_data.columns and qr_col in enhanced_data.columns:
                            enhanced_data['amount_difference'] = enhanced_data[sys_col] - enhanced_data[qr_col]
                            enhanced_data['abs_difference'] = enhanced_data['amount_difference'].abs()
                            break  # Use first available pair
                            
                    # Find status column
                    status_column = None
                    for col in ['status', 'reconciliation_status']:
                        if col in enhanced_data.columns:
                            status_column = col
                            break
                    
                    # Export complete data
                    enhanced_data.to_excel(writer, sheet_name='All_Records', index=False)
                    print(f"   ✓ All records exported ({len(enhanced_data)} entries)")
                    
                    if status_column:
                        # Sheet 3: Matched Records (all types)
                        matched_df = enhanced_data[enhanced_data[status_column].str.contains('MATCHED|Group Payment', na=False)]
                        if not matched_df.empty:
                            matched_df.to_excel(writer, sheet_name='Matched_Records', index=False)
                            print(f"   ✓ Matched records exported ({len(matched_df)} entries)")
                        
                        # Sheet 4: Group Payment Results
                        group_df = enhanced_data[enhanced_data[status_column].str.contains('Group Payment', na=False)]
                        if not group_df.empty:
                            group_df.to_excel(writer, sheet_name='Group_Payment_Results', index=False)
                            print(f"   ✓ Group payment results exported ({len(group_df)} entries)")
                        
                        # Sheet 5: Bank Only Records (no QR data)
                        bank_only_df = enhanced_data[
                            (enhanced_data['qr_collection'].isna() | (enhanced_data['qr_collection'] == 0)) & 
                            (enhanced_data['system_entry'] > 0)
                        ]
                        if not bank_only_df.empty:
                            bank_only_df.to_excel(writer, sheet_name='Bank_Only_Records', index=False)
                            print(f"   ✓ Bank only records exported ({len(bank_only_df)} entries)")
                        
                        # Sheet 6: QR Only Records (no bank data)
                        qr_only_df = enhanced_data[
                            (enhanced_data['system_entry'].isna() | (enhanced_data['system_entry'] == 0)) & 
                            (enhanced_data['qr_collection'] > 0)
                        ]
                        if not qr_only_df.empty:
                            qr_only_df.to_excel(writer, sheet_name='QR_Only_Records', index=False)
                            print(f"   ✓ QR only records exported ({len(qr_only_df)} entries)")
                        
                        # Sheet 7: Unresolved Mismatches
                        mismatch_df = enhanced_data[
                            enhanced_data[status_column].str.contains('MISMATCH', na=False) & 
                            ~enhanced_data[status_column].str.contains('Group Payment', na=False)
                        ]
                        if not mismatch_df.empty:
                            # Sort by absolute difference (highest first)
                            if 'abs_difference' in mismatch_df.columns:
                                mismatch_df = mismatch_df.sort_values('abs_difference', ascending=False)
                            mismatch_df.to_excel(writer, sheet_name='Unresolved_Mismatches', index=False)
                            print(f"   ✓ Unresolved mismatches exported ({len(mismatch_df)} entries)")
            
            # Apply enhanced formatting
            self._apply_advanced_formatting(file_path)
            
            print(f"✅ Enhanced reconciliation report exported successfully!")
            print(f"📁 File: {file_path}")
            
            return file_path
            
        except Exception as e:
            print(f"❌ Export failed: {str(e)}")
            raise
    
    def _create_executive_summary_sheet(self, writer: pd.ExcelWriter, summary: Dict, main_data: pd.DataFrame):
        """Create an executive summary sheet with key metrics and charts"""
        try:
            # Create summary data
            summary_items = []
            
            # Basic metrics
            total_records = summary.get('total_unique_loans', len(main_data) if main_data is not None else 0)
            perfect_matches = summary.get('perfect_matches', 0)
            minor_matches = summary.get('minor_matches', 0)
            total_matches = summary.get('total_matches', perfect_matches + minor_matches)
            mismatches = summary.get('amount_mismatches', total_records - total_matches)
            match_rate = summary.get('match_percentage', (total_matches / total_records * 100) if total_records > 0 else 0)
            
            summary_items.extend([
                ['📊 RECONCILIATION OVERVIEW', ''],
                ['Total Loan Records', f'{total_records:,}'],
                ['Perfect Matches', f'{perfect_matches:,}'],
                ['Minor Matches (±3 tolerance)', f'{minor_matches:,}'],
                ['Total Matched Records', f'{total_matches:,}'],
                ['Unresolved Mismatches', f'{mismatches:,}'],
                ['Overall Match Rate', f'{match_rate:.2f}%'],
                ['', ''],
                ['💰 AMOUNT ANALYSIS', ''],
                ['Total System Amount', f"₹{summary.get('total_system_amount', 0):,.2f}"],
                ['Total QR Amount', f"₹{summary.get('total_qr_amount', 0):,.2f}"],
                ['Net Difference', f"₹{summary.get('net_difference', 0):,.2f}"],
                ['', '']
            ])
            
            # Add reconciliation method breakdown if available
            if main_data is not None and 'status' in main_data.columns:
                method_counts = main_data['status'].value_counts()
                summary_items.append(['🔧 RECONCILIATION METHODS', ''])
                for method, count in method_counts.items():
                    summary_items.append([method, f'{count:,}'])
                summary_items.append(['', ''])
            
            # Add phase-specific analysis
            if main_data is not None:
                status_col = 'status' if 'status' in main_data.columns else 'reconciliation_status'
                if status_col in main_data.columns:
                    # Count different types of matches
                    phase3_matches = len(main_data[main_data[status_col].str.contains('Phase 3', na=False)])
                    group_payer_matches = len(main_data[main_data[status_col].str.contains('Group Payment \(Payer\)', na=False)])
                    group_beneficiary_matches = len(main_data[main_data[status_col].str.contains('Group Payment \(Beneficiary\)', na=False)])
                    total_group_matches = group_payer_matches + group_beneficiary_matches
                    
                    summary_items.extend([
                        ['📈 ADVANCED RECONCILIATION', ''],
                        ['Phase 3 (Credit/Debit) Matches', f'{phase3_matches:,}'],
                        ['Stage 2 (Group Payment) Details:', ''],
                        ['  • Group Payers', f'{group_payer_matches:,}'],
                        ['  • Group Beneficiaries', f'{group_beneficiary_matches:,}'],
                        ['  • Total Group Payments', f'{total_group_matches:,}'],
                        ['Standard Matches', f'{perfect_matches + minor_matches - phase3_matches - total_group_matches:,}']
                    ])
            
            # Convert to DataFrame
            summary_df = pd.DataFrame(summary_items, columns=['Metric', 'Value'])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            print(f"   ✓ Executive summary created")
            
        except Exception as e:
            print(f"   ⚠️  Could not create executive summary: {str(e)}")
            # Create basic summary as fallback
            basic_summary = pd.DataFrame([
                ['Total Records', total_records],
                ['Matched Records', total_matches],
                ['Match Rate', f"{match_rate:.2f}%"]
            ], columns=['Metric', 'Value'])
            basic_summary.to_excel(writer, sheet_name='Summary', index=False)
    
    def _apply_basic_formatting(self, worksheet):
        """Apply basic formatting to any sheet"""
        # Header formatting
        for cell in worksheet[1]:
            if cell.value:
                cell.font = Font(bold=True, size=10)
                cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")


# Example usage and testing functions
def test_excel_exporter():
    """Test function for ExcelExporter"""
    exporter = ExcelExporter()
    
    # Create sample data
    sample_data = {
        'summary_stats': {
            'total_bank_transactions': 1500,
            'total_sib_transactions': 1200,
            'total_demand_entries': 800,
            'bank_sib_matches': 950,
            'bank_demand_matches': 780,
            'match_percentage': 75.5
        },
        'merged_sib_demand': {
            'merge_stats': {
                'sib_records': 1200,
                'demand_records': 800,
                'matched_records': 720,
                'match_rate': 60.0,
                'unmatched_sib_records': 480
            }
        }
    }
    
    # Test export
    output_file = exporter.export_reconciliation_report(sample_data, 'test_report.xlsx')
    print(f"Test export completed: {output_file}")
    
    # Test template creation
    template_file = exporter.create_template_file('reconciliation')
    print(f"Template created: {template_file}")


if __name__ == "__main__":
    test_excel_exporter()