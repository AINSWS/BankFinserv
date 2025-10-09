"""
Stage 2 Group Payment Reconciliation Processor

This processor handles cases where one person in a group pays on behalf of everyone.
It analyzes mismatched records to find group-wise payment patterns and redistributes
QR amounts based on system entry requirements.
"""

import pandas as pd
import logging
from typing import Dict, List, Tuple, Any

class GroupPaymentProcessor:
    """
    Handles Stage 2 reconciliation for group payments where one member
    pays for the entire group
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_group_payments(self, mismatched_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Process mismatched records to identify and resolve group payments
        
        Args:
            mismatched_data: DataFrame with mismatched records containing:
                - loan_id, customer_name, group_id, system_entry, qr_collection, difference
        
        Returns:
            Dictionary containing:
            - newly_matched: Records that can now be matched after group processing
            - remaining_mismatched: Records that still don't match
            - group_analysis: Summary of group payment patterns found
        """
        
        if mismatched_data.empty:
            return {
                'newly_matched': pd.DataFrame(),
                'remaining_mismatched': mismatched_data.copy(),
                'group_analysis': {},
                'status': 'success',
                'message': 'No mismatched data to process'
            }
        
        try:
            # Step 1: Group by group_id and calculate totals
            group_summary = self._calculate_group_totals(mismatched_data)
            
            # Step 2: Identify groups where total QR matches total system requirement
            matching_groups = self._identify_matching_groups(group_summary)
            
            # Step 3: Process each matching group and redistribute payments
            newly_matched_records = []
            processed_loan_ids = set()
            
            for group_id in matching_groups:
                group_records = mismatched_data[mismatched_data['group_id'] == group_id].copy()
                redistributed_records = self._redistribute_group_payments(group_records)
                
                newly_matched_records.extend(redistributed_records)
                processed_loan_ids.update(group_records['loan_id'].tolist())
            
            # Step 4: Create results
            newly_matched_df = pd.DataFrame(newly_matched_records) if newly_matched_records else pd.DataFrame()
            remaining_mismatched_df = mismatched_data[~mismatched_data['loan_id'].isin(processed_loan_ids)].copy()
            
            # Step 5: Generate analysis summary
            group_analysis = self._generate_group_analysis(matching_groups, group_summary, len(newly_matched_records))
            
            return {
                'newly_matched': newly_matched_df,
                'remaining_mismatched': remaining_mismatched_df,
                'group_analysis': group_analysis,
                'status': 'success',
                'message': f'Processed {len(matching_groups)} groups, resolved {len(newly_matched_records)} records'
            }
            
        except Exception as e:
            self.logger.error(f"Error in group payment processing: {e}", exc_info=True)
            return {
                'newly_matched': pd.DataFrame(),
                'remaining_mismatched': mismatched_data.copy(),
                'group_analysis': {},
                'status': 'error',
                'message': f'Error processing group payments: {str(e)}'
            }
    
    def _calculate_group_totals(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate total system_entry and qr_collection for each group"""
        
        group_totals = data.groupby('group_id').agg({
            'system_entry': 'sum',
            'qr_collection': 'sum',
            'loan_id': 'count'  # Number of members in group
        }).reset_index()
        
        group_totals.columns = ['group_id', 'total_system_entry', 'total_qr_collection', 'member_count']
        group_totals['group_difference'] = group_totals['total_qr_collection'] - group_totals['total_system_entry']
        
        return group_totals
    
    def _identify_matching_groups(self, group_summary: pd.DataFrame, tolerance: int = 2) -> List[str]:
        """
        Identify groups where total QR collection matches total system requirement
        within banking tolerance (±1, ±2)
        """
        
        matching_groups = []
        
        for _, row in group_summary.iterrows():
            group_diff = abs(row['group_difference'])
            
            # Check if group total matches within banking tolerance
            if group_diff <= tolerance:
                matching_groups.append(row['group_id'])
                self.logger.info(f"Group {row['group_id']}: Total system={row['total_system_entry']}, "
                               f"Total QR={row['total_qr_collection']}, Diff={row['group_difference']} (MATCH)")
        
        return matching_groups
    
    def _redistribute_group_payments(self, group_records: pd.DataFrame) -> List[Dict]:
        """
        Redistribute QR payments within a group based on individual system_entry amounts
        """
        
        total_qr = group_records['qr_collection'].sum()
        total_system = group_records['system_entry'].sum()
        
        redistributed_records = []
        
        for _, record in group_records.iterrows():
            # Calculate proportional QR amount based on system_entry
            if total_system > 0:
                proportional_qr = (record['system_entry'] / total_system) * total_qr
            else:
                proportional_qr = 0
            
            # Create new record with redistributed QR amount
            new_record = record.to_dict()
            new_record['original_qr_collection'] = record['qr_collection']  # Keep original for audit
            new_record['qr_collection'] = round(proportional_qr, 2)
            new_record['difference'] = new_record['qr_collection'] - record['system_entry']
            
            # Update status based on new difference
            if abs(new_record['difference']) <= 2:  # Banking tolerance
                new_record['status'] = 'MATCHED - Group Payment Redistribution'
                new_record['reconciliation_method'] = 'Stage 2: Group Payment'
            else:
                new_record['status'] = 'MISMATCH - Group Payment (Still Unresolved)'
                new_record['reconciliation_method'] = 'Stage 2: Group Payment (Partial)'
            
            redistributed_records.append(new_record)
        
        return redistributed_records
    
    def _generate_group_analysis(self, matching_groups: List[str], group_summary: pd.DataFrame, 
                                resolved_records: int) -> Dict[str, Any]:
        """Generate summary analysis of group payment processing"""
        
        analysis = {
            'total_groups_analyzed': len(group_summary),
            'matching_groups_found': len(matching_groups),
            'records_resolved': resolved_records,
            'group_details': []
        }
        
        # Add details for each matching group
        for group_id in matching_groups:
            group_info = group_summary[group_summary['group_id'] == group_id].iloc[0]
            
            analysis['group_details'].append({
                'group_id': group_id,
                'member_count': int(group_info['member_count']),
                'total_system_entry': float(group_info['total_system_entry']),
                'total_qr_collection': float(group_info['total_qr_collection']),
                'group_difference': float(group_info['group_difference'])
            })
        
        return analysis
    
    def get_processing_summary(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary of group processing results"""
        
        if result['status'] != 'success':
            return f"❌ Group processing failed: {result['message']}"
        
        analysis = result['group_analysis']
        newly_matched = len(result['newly_matched'])
        remaining_mismatched = len(result['remaining_mismatched'])
        
        summary = f"🏪 Stage 2 Group Payment Analysis:\n"
        summary += f"   • Groups analyzed: {analysis.get('total_groups_analyzed', 0)}\n"
        summary += f"   • Groups with matching totals: {analysis.get('matching_groups_found', 0)}\n"
        summary += f"   • Records resolved: {newly_matched}\n"
        summary += f"   • Records still mismatched: {remaining_mismatched}\n"
        
        if analysis.get('group_details'):
            summary += f"\n📋 Resolved Groups:\n"
            for group in analysis['group_details']:
                summary += f"   • Group {group['group_id']}: {group['member_count']} members, "
                summary += f"₹{group['total_system_entry']:.0f} system, ₹{group['total_qr_collection']:.0f} QR "
                summary += f"(diff: ₹{group['group_difference']:.0f})\n"
        
        return summary