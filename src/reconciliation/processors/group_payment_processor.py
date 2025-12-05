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
        
        # Ensure required columns exist
        required_columns = ['group_id', 'system_entry', 'qr_collection']
        if not all(col in data.columns for col in required_columns):
            self.logger.error(f"Missing required columns. Available columns: {data.columns.tolist()}")
            return pd.DataFrame()  # Return empty DataFrame if required columns are missing
        
        try:
            # Calculate group totals with error handling
            group_totals = data.groupby('group_id').agg({
                'system_entry': 'sum',
                'qr_collection': 'sum',
                'loan_id': 'count'  # Number of members in group
            }).reset_index()
            
            group_totals.columns = ['group_id', 'total_system_entry', 'total_qr_collection', 'member_count']
            
            # Calculate group difference (QR - System)
            group_totals['group_difference'] = (
                group_totals['total_qr_collection'] - group_totals['total_system_entry']
            ).round(2)  # Round to avoid floating point issues
            
            # Add percentage difference for analysis
            group_totals['difference_percentage'] = (
                (group_totals['group_difference'] / group_totals['total_system_entry']) * 100
            ).round(2)
            
            # Filter out invalid groups (e.g., single member groups)
            valid_groups = group_totals[
                (group_totals['member_count'] > 1) &  # More than one member
                (group_totals['total_system_entry'] > 0) &  # Has system entries
                (group_totals['total_qr_collection'] > 0)   # Has QR collections
            ]
            
            self.logger.info(f"Found {len(valid_groups)} valid groups for processing")
            return valid_groups
            
        except Exception as e:
            self.logger.error(f"Error calculating group totals: {e}")
            return pd.DataFrame()
        
        return group_totals
    
    def _identify_matching_groups(self, group_summary: pd.DataFrame) -> List[str]:
        """
        Identify groups where total QR collection matches total system requirement
        ONLY match groups where the totals are equal (within ±3 tolerance)
        """
        matching_groups = []
        TOLERANCE = 3  # Allow only ±3 difference
        
        for _, row in group_summary.iterrows():
            # A group is considered matching ONLY if:
            # 1. The total QR collection equals total system requirement (within ±3)
            # 2. Has more than 1 member (actual group)
            # 3. Both system and QR have positive values
            difference = abs(row['total_qr_collection'] - row['total_system_entry'])
            
            if (row['total_qr_collection'] > 0 and 
                row['total_system_entry'] > 0 and
                row['member_count'] > 1 and
                difference <= TOLERANCE):  # Only match if totals are equal within tolerance
                matching_groups.append(row['group_id'])
                self.logger.info(f"Group {row['group_id']}: Members={row['member_count']}, "
                               f"System={row['total_system_entry']}, QR={row['total_qr_collection']}, "
                               f"Diff={row['group_difference']} (MATCHED)")
            else:
                self.logger.debug(f"Group {row['group_id']}: Skipped - Diff={difference:.2f} exceeds tolerance")
        
        return matching_groups
    
    def _redistribute_group_payments(self, group_records: pd.DataFrame) -> List[Dict]:
        """
        Redistribute QR payments within a group based on individual system_entry amounts.
        Handles cases where one member pays for multiple members.
        """
        if group_records.empty:
            return []
            
        total_qr = group_records['qr_collection'].sum()
        total_system = group_records['system_entry'].sum()
        TOLERANCE = 3  # Allow only ±3 difference
        
        # Skip if either total is 0 or if totals don't match within tolerance
        if total_qr == 0 or total_system == 0 or abs(total_qr - total_system) > TOLERANCE:
            self.logger.debug(f"Skipping group redistribution: QR={total_qr}, System={total_system}, Diff={abs(total_qr - total_system)}")
            return []
            
        redistributed_records = []
        
        # Find who made the payments
        payers = group_records[group_records['qr_collection'] > 0]
        
        # If we have a clear group payment pattern (some members paid, others didn't)
        if not payers.empty and len(payers) < len(group_records):
            self.logger.info(f"Found group payment pattern: {len(payers)} payer(s) for {len(group_records)} members")
            
            for _, record in group_records.iterrows():
                new_record = record.to_dict()
                new_record['original_qr_collection'] = record['qr_collection']  # Keep original for audit
                
                if record['qr_collection'] > 0:
                    # This member paid more than their share
                    new_record['status'] = 'MATCHED - Group Payment (Payer)'
                    new_record['reconciliation_method'] = 'Stage 2: Group Payment'
                    new_record['qr_collection'] = record['system_entry']  # Adjust to their required amount
                    new_record['difference'] = 0  # Since we match exactly
                else:
                    # This member didn't pay but was paid for
                    new_record['qr_collection'] = record['system_entry']  # They get matched for their system amount
                    new_record['difference'] = 0  # Since we match exactly
                    new_record['status'] = 'MATCHED - Group Payment (Beneficiary)'
                    new_record['reconciliation_method'] = 'Stage 2: Group Payment'
                
                redistributed_records.append(new_record)
        else:
            # Default case: proportional distribution
            for _, record in group_records.iterrows():
                proportional_qr = (record['system_entry'] / total_system) * total_qr if total_system > 0 else 0
                
                new_record = record.to_dict()
                new_record['original_qr_collection'] = record['qr_collection']
                new_record['qr_collection'] = round(proportional_qr, 2)
                new_record['difference'] = new_record['qr_collection'] - record['system_entry']
                
                if abs(new_record['difference']) <= 2:
                    new_record['status'] = 'MATCHED - Group Payment (Proportional)'
                    new_record['reconciliation_method'] = 'Stage 2: Group Payment'
                else:
                    new_record['status'] = 'MISMATCH - Group Payment (Unresolved)'
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
        
        # Only show summary count, not individual groups (to reduce log verbosity)
        if analysis.get('group_details'):
            total_groups = len(analysis['group_details'])
            summary += f"   • ✅ {total_groups} groups resolved via group payment matching\n"
        
        return summary