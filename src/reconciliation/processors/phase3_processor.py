"""
Phase 3 Reconciliation Processor

This processor handles advanced bank ledger processing where:
- Narration field is split by '/' delimiter
- 2nd column after split contains loan ID for debit transactions
- 3rd column after split contains loan ID for credit transactions
- Creates separate DataFrames for debit and credit processing
"""

import pandas as pd
import logging
from typing import Dict, List, Tuple, Any, Optional

class Phase3ReconciliationProcessor:
    """
    Handles Phase 3 reconciliation with narration splitting and 
    separate debit/credit loan ID extraction
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def process_bank_ledger_phase3(self, bank_ledger_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process bank ledger for Phase 3 reconciliation
        
        Args:
            bank_ledger_df: DataFrame with columns including narration, debit, credit
        
        Returns:
            Dictionary containing:
            - debit_df: DataFrame with loan_id and debit amounts
            - credit_df: DataFrame with loan_id and credit amounts
            - debit_pivot: Pivoted debit data (loan_id groupby with sum)
            - credit_pivot: Pivoted credit data (loan_id groupby with sum)
            - processing_summary: Summary of processing results
        """
        
        if bank_ledger_df is None or bank_ledger_df.empty:
            return {
                'status': 'error',
                'message': 'Bank ledger data is empty or None',
                'debit_df': pd.DataFrame(),
                'credit_df': pd.DataFrame(),
                'debit_pivot': pd.DataFrame(),
                'credit_pivot': pd.DataFrame(),
                'processing_summary': {}
            }
        
        try:
            print("🔄 Starting Phase 3: Advanced Bank Ledger Processing...")
            
            # Step 1: Identify required columns
            narration_col = self._find_column(bank_ledger_df, ['narration', 'description', 'particulars'])
            debit_col = self._find_column(bank_ledger_df, ['debit', 'dr', 'debit_amount'])
            credit_col = self._find_column(bank_ledger_df, ['credit', 'cr', 'credit_amount'])
            
            if not all([narration_col, debit_col, credit_col]):
                missing = []
                if not narration_col: missing.append('narration')
                if not debit_col: missing.append('debit')
                if not credit_col: missing.append('credit')
                
                return {
                    'status': 'error',
                    'message': f'Required columns not found: {", ".join(missing)}',
                    'debit_df': pd.DataFrame(),
                    'credit_df': pd.DataFrame(),
                    'debit_pivot': pd.DataFrame(),
                    'credit_pivot': pd.DataFrame(),
                    'processing_summary': {}
                }
            
            print(f"   • Narration column: {narration_col}")
            print(f"   • Debit column: {debit_col}")
            print(f"   • Credit column: {credit_col}")
            
            # Step 2: Process narration splitting and loan ID extraction
            debit_df, credit_df = self._extract_loan_ids_from_narration(
                bank_ledger_df, narration_col, debit_col, credit_col
            )
            
            # Step 3: Create pivot tables
            debit_pivot = self._create_pivot_table(debit_df, 'debit')
            credit_pivot = self._create_pivot_table(credit_df, 'credit')
            
            # Step 4: Generate summary
            processing_summary = {
                'total_records_processed': len(bank_ledger_df),
                'debit_transactions': len(debit_df),
                'credit_transactions': len(credit_df),
                'unique_debit_loans': len(debit_pivot) if not debit_pivot.empty else 0,
                'unique_credit_loans': len(credit_pivot) if not credit_pivot.empty else 0,
                'total_debit_amount': debit_df['amount'].sum() if not debit_df.empty and 'amount' in debit_df.columns else 0,
                'total_credit_amount': credit_df['amount'].sum() if not credit_df.empty and 'amount' in credit_df.columns else 0
            }
            
            print(f"✅ Phase 3 Processing Complete!")
            print(f"   • Total records: {processing_summary['total_records_processed']}")
            print(f"   • Debit transactions: {processing_summary['debit_transactions']}")
            print(f"   • Credit transactions: {processing_summary['credit_transactions']}")
            print(f"   • Unique debit loans: {processing_summary['unique_debit_loans']}")
            print(f"   • Unique credit loans: {processing_summary['unique_credit_loans']}")
            
            return {
                'status': 'success',
                'message': 'Phase 3 processing completed successfully',
                'debit_df': debit_df,
                'credit_df': credit_df,
                'debit_pivot': debit_pivot,
                'credit_pivot': credit_pivot,
                'processing_summary': processing_summary
            }
            
        except Exception as e:
            error_msg = f"Error in Phase 3 processing: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {
                'status': 'error',
                'message': error_msg,
                'debit_df': pd.DataFrame(),
                'credit_df': pd.DataFrame(),
                'debit_pivot': pd.DataFrame(),
                'credit_pivot': pd.DataFrame(),
                'processing_summary': {}
            }
    
    def _find_column(self, df: pd.DataFrame, possible_names: List[str]) -> Optional[str]:
        """Find column by checking multiple possible names (case insensitive)"""
        for col in df.columns:
            for name in possible_names:
                if name.lower() in col.lower():
                    return col
        return None
    
    def _extract_loan_ids_from_narration(self, df: pd.DataFrame, narration_col: str, 
                                       debit_col: str, credit_col: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Extract loan IDs from narration field and create separate debit/credit DataFrames
        
        Updated logic to handle multiple narration formats:
        - For DEBIT: Look for loan ID in position 1 or 2 after split
        - For CREDIT: Look for loan ID in position 2 or 3 after split, or embedded in text
        """
        
        debit_records = []
        credit_records = []
        
        print(f"   • Processing {len(df)} records for narration splitting...")
        
        for idx, row in df.iterrows():
            try:
                narration = str(row[narration_col]) if pd.notna(row[narration_col]) else ""
                debit_amount = row[debit_col] if pd.notna(row[debit_col]) else 0
                credit_amount = row[credit_col] if pd.notna(row[credit_col]) else 0
                
                # Skip if narration is empty
                if not narration or narration == "nan":
                    continue
                
                # Split narration by '/'
                narration_parts = narration.split('/')
                
                # Process debit transactions (non-zero debit amount)
                if debit_amount and debit_amount > 0:
                    loan_id_debit = self._extract_loan_id_from_parts(narration_parts, narration, 'debit')
                    if loan_id_debit:
                        debit_records.append({
                            'loan_id': loan_id_debit,
                            'amount': float(debit_amount),
                            'transaction_type': 'debit',
                            'original_narration': narration,
                            'row_index': idx
                        })
                
                # Process credit transactions (non-zero credit amount)
                if credit_amount and credit_amount > 0:
                    loan_id_credit = self._extract_loan_id_from_parts(narration_parts, narration, 'credit')
                    if loan_id_credit:
                        credit_records.append({
                            'loan_id': loan_id_credit,
                            'amount': float(credit_amount),
                            'transaction_type': 'credit',
                            'original_narration': narration,
                            'row_index': idx
                        })
                            
            except Exception as e:
                self.logger.warning(f"Error processing row {idx}: {e}")
                continue
        
        # Create DataFrames
        debit_df = pd.DataFrame(debit_records)
        credit_df = pd.DataFrame(credit_records)
        
        print(f"   • Extracted {len(debit_records)} debit transactions")
        print(f"   • Extracted {len(credit_records)} credit transactions")
        
        return debit_df, credit_df
    
    def _extract_loan_id_from_parts(self, narration_parts: List[str], full_narration: str, transaction_type: str) -> Optional[str]:
        """
        Extract loan ID from narration parts based on transaction type
        
        Args:
            narration_parts: List of parts after splitting narration by '/'
            full_narration: Original full narration text
            transaction_type: 'debit' or 'credit'
        
        Returns:
            Loan ID as string if found, None otherwise
        """
        import re
        
        if transaction_type == 'debit':
            # For DEBIT: Try position 1 first, then position 2
            for pos in [1, 2]:
                if len(narration_parts) > pos:
                    potential_id = narration_parts[pos].strip()
                    if potential_id.isdigit() and len(potential_id) >= 5:  # Valid loan ID
                        return potential_id
                        
        elif transaction_type == 'credit':
            # For CREDIT: Try position 2, then 3, then search for embedded loan ID
            for pos in [2, 3]:
                if len(narration_parts) > pos:
                    potential_id = narration_parts[pos].strip()
                    if potential_id.isdigit() and len(potential_id) >= 5:  # Valid loan ID
                        return potential_id
            
            # If not found in standard positions, search for embedded loan ID in first part
            if narration_parts:
                # Look for patterns like "RD AMOUNT WITHDRAW FROM 181669"
                loan_id_match = re.search(r'\b(\d{6})\b', narration_parts[0])
                if loan_id_match:
                    return loan_id_match.group(1)
        
        return None
    
    def _create_pivot_table(self, df: pd.DataFrame, transaction_type: str) -> pd.DataFrame:
        """Create pivot table by grouping loan_id and summing amounts"""
        
        if df.empty:
            print(f"   • No {transaction_type} data to pivot")
            return pd.DataFrame()
        
        try:
            # Group by loan_id and sum amounts
            pivot_df = df.groupby('loan_id')['amount'].sum().reset_index()
            pivot_df.columns = ['loan_id', f'{transaction_type}_amount']
            
            print(f"   • Created {transaction_type} pivot: {len(pivot_df)} unique loan IDs")
            print(f"   • Total {transaction_type} amount: ₹{pivot_df[f'{transaction_type}_amount'].sum():,.2f}")
            
            return pivot_df
            
        except Exception as e:
            self.logger.error(f"Error creating {transaction_type} pivot table: {e}")
            return pd.DataFrame()
    
    def get_phase3_summary(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary of Phase 3 processing"""
        
        if result['status'] != 'success':
            return f"❌ Phase 3 processing failed: {result['message']}"
        
        summary = result['processing_summary']
        
        summary_text = f"🔄 Phase 3: Advanced Bank Ledger Processing\n"
        summary_text += f"   • Total records processed: {summary['total_records_processed']}\n"
        summary_text += f"   • Debit transactions extracted: {summary['debit_transactions']}\n"
        summary_text += f"   • Credit transactions extracted: {summary['credit_transactions']}\n"
        summary_text += f"   • Unique debit loan IDs: {summary['unique_debit_loans']}\n"
        summary_text += f"   • Unique credit loan IDs: {summary['unique_credit_loans']}\n"
        summary_text += f"   • Total debit amount: ₹{summary['total_debit_amount']:,.2f}\n"
        summary_text += f"   • Total credit amount: ₹{summary['total_credit_amount']:,.2f}\n"
        
        return summary_text
    
    def process_phase3_reconciliation(self, 
                                    mismatched_data: pd.DataFrame,
                                    debit_df: pd.DataFrame, 
                                    credit_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Process Phase 3 reconciliation by matching credit/debit differences with QR amounts
        
        Args:
            mismatched_data: DataFrame with mismatched records from Phase 2
            debit_df: DataFrame with loan_id and debit amounts from bank ledger
            credit_df: DataFrame with loan_id and credit amounts from bank ledger
        
        Returns:
            Dictionary containing newly matched records and analysis
        """
        
        if mismatched_data.empty:
            return {
                'newly_matched': pd.DataFrame(),
                'remaining_mismatched': mismatched_data.copy(),
                'phase3_analysis': {'total_analyzed': 0, 'resolved': 0},
                'status': 'success',
                'message': 'No mismatched data for Phase 3 processing'
            }
        
        try:
            print("🔄 Phase 3: Analyzing credit/debit differences...")
            
            newly_matched_records = []
            processed_loan_ids = set()
            
            # Process each mismatched record
            for _, record in mismatched_data.iterrows():
                loan_id = str(record['loan_id'])  # Convert to string for consistency
                # Try multiple column names for QR amount
                qr_amount = record.get('qr_amount', record.get('qr_collection', 0))
                print(f"   Processing loan {loan_id}: QR={qr_amount} (type: {type(qr_amount)})")
                
                # Calculate credit/debit difference for this loan ID
                credit_debit_result = self._calculate_credit_debit_difference(
                    loan_id, debit_df, credit_df
                )
                

                if credit_debit_result['found']:
                    credit_debit_difference = credit_debit_result['difference']
                    
                    # Debug output
                    print(f"   • Loan {loan_id}: Debit=₹{credit_debit_result['total_debit']}, Credit=₹{credit_debit_result['total_credit']}, Diff=₹{credit_debit_difference}, QR=₹{qr_amount}")
                    
                    # Check if credit/debit difference matches QR amount within tolerance
                    amount_difference = abs(credit_debit_difference - qr_amount)
                    
                    if amount_difference <= 2:  # Banking tolerance
                        # Match found! Create resolved record
                        resolved_record = record.copy()
                        resolved_record['phase3_credit_total'] = credit_debit_result['total_credit']
                        resolved_record['phase3_debit_total'] = credit_debit_result['total_debit']
                        resolved_record['phase3_difference'] = credit_debit_difference
                        resolved_record['phase3_match_difference'] = amount_difference
                        resolved_record['status'] = 'MATCHED - Phase 3 Credit/Debit Analysis'
                        resolved_record['reconciliation_method'] = 'Phase 3: Credit/Debit Matching'
                        
                        newly_matched_records.append(resolved_record.to_dict())
                        processed_loan_ids.add(loan_id)
                        
                        print(f"✅ Phase 3 Match: Loan {loan_id} - QR: ₹{qr_amount}, C/D Diff: ₹{credit_debit_difference}, Variance: ₹{amount_difference}")
            
            # Create results
            newly_matched_df = pd.DataFrame(newly_matched_records) if newly_matched_records else pd.DataFrame()
            remaining_mismatched_df = mismatched_data[~mismatched_data['loan_id'].isin(processed_loan_ids)].copy()
            
            # Generate analysis
            phase3_analysis = {
                'total_analyzed': len(mismatched_data),
                'resolved': len(newly_matched_records),
                'remaining_mismatched': len(remaining_mismatched_df),
                'resolution_rate': (len(newly_matched_records) / len(mismatched_data)) * 100 if len(mismatched_data) > 0 else 0
            }
            
            print(f"📊 Phase 3 Results: {len(newly_matched_records)} resolved, {len(remaining_mismatched_df)} still mismatched")
            
            return {
                'newly_matched': newly_matched_df,
                'remaining_mismatched': remaining_mismatched_df,
                'phase3_analysis': phase3_analysis,
                'status': 'success',
                'message': f'Phase 3 processed {len(mismatched_data)} records, resolved {len(newly_matched_records)}'
            }
            
        except Exception as e:
            self.logger.error(f"Error in Phase 3 processing: {e}", exc_info=True)
            return {
                'newly_matched': pd.DataFrame(),
                'remaining_mismatched': mismatched_data.copy(),
                'phase3_analysis': {'total_analyzed': 0, 'resolved': 0},
                'status': 'error',
                'message': f'Error in Phase 3 processing: {str(e)}'
            }
    
    def _calculate_credit_debit_difference(self, 
                                         loan_id: str, 
                                         debit_df: pd.DataFrame, 
                                         credit_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate the difference between total credits and debits for a loan ID
        
        Args:
            loan_id: The loan ID to analyze
            debit_df: DataFrame with debit transactions
            credit_df: DataFrame with credit transactions
        
        Returns:
            Dictionary with calculation results
        """
        try:

            # Get all debit transactions for this loan ID
            debit_records = debit_df[debit_df['loan_id'] == loan_id]
            total_debit = debit_records['amount'].sum() if not debit_records.empty else 0
            
            # Get all credit transactions for this loan ID
            credit_records = credit_df[credit_df['loan_id'] == loan_id]
            total_credit = credit_records['amount'].sum() if not credit_records.empty else 0
            
            # Calculate difference (debit - credit)
            # When debit > credit, customer owes money (positive difference should match QR collection)
            difference = total_debit - total_credit
            
            # Check if we found any transactions
            found = not debit_records.empty or not credit_records.empty
            
            return {
                'found': found,
                'total_debit': total_debit,
                'total_credit': total_credit,
                'difference': difference,
                'debit_count': len(debit_records),
                'credit_count': len(credit_records)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating credit/debit for loan {loan_id}: {e}")
            return {
                'found': False,
                'total_debit': 0,
                'total_credit': 0,
                'difference': 0,
                'debit_count': 0,
                'credit_count': 0
            }
    
    def get_phase3_reconciliation_summary(self, result: Dict[str, Any]) -> str:
        """Generate human-readable summary of Phase 3 reconciliation results"""
        
        if result['status'] != 'success':
            return f"❌ Phase 3 reconciliation failed: {result['message']}"
        
        analysis = result['phase3_analysis']
        newly_matched = len(result['newly_matched'])
        remaining_mismatched = len(result['remaining_mismatched'])
        
        summary = f"🔄 Phase 3: Credit/Debit Analysis Results:\n"
        summary += f"   • Records analyzed: {analysis.get('total_analyzed', 0)}\n"
        summary += f"   • Resolved by Phase 3: {newly_matched}\n"
        summary += f"   • Still mismatched: {remaining_mismatched}\n"
        summary += f"   • Resolution rate: {analysis.get('resolution_rate', 0):.1f}%\n"
        
        return summary