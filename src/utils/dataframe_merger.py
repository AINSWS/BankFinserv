"""
DataFrame Merger Utility - Dynamic DataFrame Merging
"""
import pandas as pd
from typing import Optional, Dict, Any, Tuple, List
import logging

class DataFrameMerger:
    """
    A utility class for dynamic DataFrame merging operations.
    Provides flexible merging capabilities with detailed merge statistics and validation.
    """
    
    def __init__(self, validate_columns: bool = True, case_sensitive: bool = False):
        """
        Initialize the DataFrame merger.
        
        Args:
            validate_columns: Whether to validate column existence before merging
            case_sensitive: Whether column matching should be case sensitive
        """
        self.validate_columns = validate_columns
        self.case_sensitive = case_sensitive
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the merger"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def dynamic_merge(
        self,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        left_column: str,
        right_column: str,
        how: str = 'inner',
        suffixes: Tuple[str, str] = ('_left', '_right'),
        validate_data: bool = True
    ) -> Dict[str, Any]:
        """
        Dynamically merge two DataFrames based on specified columns.
        
        Args:
            left_df: First DataFrame to merge
            right_df: Second DataFrame to merge
            left_column: Column name in left DataFrame to merge on
            right_column: Column name in right DataFrame to merge on
            how: Type of merge ('inner', 'outer', 'left', 'right')
            suffixes: Suffixes for overlapping column names
            validate_data: Whether to validate data before merging
            
        Returns:
            Dict containing merged DataFrame and merge statistics
        """
        try:
            # Input validation
            if validate_data:
                validation_result = self._validate_merge_inputs(
                    left_df, right_df, left_column, right_column
                )
                if not validation_result['valid']:
                    return {
                        'status': 'error',
                        'error_message': validation_result['error_message'],
                        'merged_df': None,
                        'merge_stats': {}
                    }
            
            # Prepare columns for merging
            left_col, right_col = self._prepare_merge_columns(
                left_df, right_df, left_column, right_column
            )
            
            # Store original sizes
            left_size = len(left_df)
            right_size = len(right_df)
            
            # Perform the merge
            # Use many-to-one (m:1) for SIB QR (many transactions) + Demand (one per loan_id)
            # This ensures each SIB transaction gets enriched with loan info, not duplicated
            try:
                merged_df = pd.merge(
                    left_df,
                    right_df,
                    left_on=left_col,
                    right_on=right_col,
                    how=how,
                    suffixes=suffixes,
                    validate='m:1'  # Many-to-one: many SIB transactions to one Demand entry per loan
                )
            except pd.errors.MergeError as e:
                # If m:1 fails (right has duplicates), log warning and deduplicate right
                self.logger.warning(f"Many-to-one merge failed: {e}. Deduplicating right DataFrame...")
                right_df_dedup = right_df.drop_duplicates(subset=[right_col], keep='first')
                merged_df = pd.merge(
                    left_df,
                    right_df_dedup,
                    left_on=left_col,
                    right_on=right_col,
                    how=how,
                    suffixes=suffixes,
                    validate='m:1'
                )
            
            # Calculate merge statistics
            merge_stats = self._calculate_merge_stats(
                left_df, right_df, merged_df, left_col, right_col, how
            )
            
            # Add merge metadata
            merged_df['_merge_timestamp'] = pd.Timestamp.now()
            merged_df['_merge_type'] = how
            merged_df['_left_source'] = f"merge_on_{left_col}"
            merged_df['_right_source'] = f"merge_on_{right_col}"
            
            self.logger.info(f"Successfully merged DataFrames: {merge_stats['match_rate']:.1f}% match rate")
            
            return {
                'status': 'success',
                'merged_df': merged_df,
                'merge_stats': merge_stats,
                'merge_details': {
                    'left_column': left_col,
                    'right_column': right_col,
                    'merge_type': how,
                    'suffixes': suffixes,
                    'original_left_size': left_size,
                    'original_right_size': right_size,
                    'merged_size': len(merged_df)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error during DataFrame merge: {str(e)}")
            return {
                'status': 'error',
                'error_message': str(e),
                'merged_df': None,
                'merge_stats': {},
                'merge_details': {}
            }
    
    def _validate_merge_inputs(
        self,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        left_column: str,
        right_column: str
    ) -> Dict[str, Any]:
        """Validate inputs before merging"""
        
        # Check if DataFrames are not empty
        if left_df.empty:
            return {'valid': False, 'error_message': 'Left DataFrame is empty'}
        
        if right_df.empty:
            return {'valid': False, 'error_message': 'Right DataFrame is empty'}
        
        # Check if columns exist
        if self.validate_columns:
            left_cols = left_df.columns.tolist()
            right_cols = right_df.columns.tolist()
            
            # Handle case sensitivity
            if not self.case_sensitive:
                left_cols_lower = [col.lower() for col in left_cols]
                right_cols_lower = [col.lower() for col in right_cols]
                
                if left_column.lower() not in left_cols_lower:
                    return {
                        'valid': False,
                        'error_message': f"Column '{left_column}' not found in left DataFrame. Available: {left_cols}"
                    }
                
                if right_column.lower() not in right_cols_lower:
                    return {
                        'valid': False,
                        'error_message': f"Column '{right_column}' not found in right DataFrame. Available: {right_cols}"
                    }
            else:
                if left_column not in left_cols:
                    return {
                        'valid': False,
                        'error_message': f"Column '{left_column}' not found in left DataFrame. Available: {left_cols}"
                    }
                
                if right_column not in right_cols:
                    return {
                        'valid': False,
                        'error_message': f"Column '{right_column}' not found in right DataFrame. Available: {right_cols}"
                    }
        
        return {'valid': True, 'error_message': None}
    
    def _prepare_merge_columns(
        self,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        left_column: str,
        right_column: str
    ) -> Tuple[str, str]:
        """Prepare column names for merging (handle case sensitivity)"""
        
        if not self.case_sensitive:
            # Find actual column names (case-insensitive)
            left_cols = {col.lower(): col for col in left_df.columns}
            right_cols = {col.lower(): col for col in right_df.columns}
            
            actual_left_col = left_cols.get(left_column.lower(), left_column)
            actual_right_col = right_cols.get(right_column.lower(), right_column)
            
            return actual_left_col, actual_right_col
        
        return left_column, right_column
    
    def _calculate_merge_stats(
        self,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        merged_df: pd.DataFrame,
        left_col: str,
        right_col: str,
        merge_type: str
    ) -> Dict[str, Any]:
        """Calculate detailed merge statistics"""
        
        left_size = len(left_df)
        right_size = len(right_df)
        merged_size = len(merged_df)
        
        # Get unique values in merge columns
        left_unique = left_df[left_col].nunique()
        right_unique = right_df[right_col].nunique()
        
        # Calculate matches based on merge type
        if merge_type == 'inner':
            matches = merged_size
            unmatched_left = left_size - matches
            unmatched_right = right_size - matches
        elif merge_type == 'left':
            matches = merged_df[right_col].notna().sum()
            unmatched_left = 0
            unmatched_right = right_size - matches
        elif merge_type == 'right':
            matches = merged_df[left_col].notna().sum()
            unmatched_left = left_size - matches
            unmatched_right = 0
        else:  # outer
            matches = merged_df[[left_col, right_col]].dropna().shape[0]
            unmatched_left = merged_df[left_col].isna().sum()
            unmatched_right = merged_df[right_col].isna().sum()
        
        # Calculate match rate
        total_records = max(left_size, right_size)
        match_rate = (matches / total_records * 100) if total_records > 0 else 0
        
        return {
            'left_records': left_size,
            'right_records': right_size,
            'merged_records': merged_size,
            'matched_records': matches,
            'unmatched_left_records': unmatched_left,
            'unmatched_right_records': unmatched_right,
            'left_unique_values': left_unique,
            'right_unique_values': right_unique,
            'match_rate': match_rate,
            'merge_type': merge_type,
            'merge_efficiency': matches / merged_size * 100 if merged_size > 0 else 0
        }
    
    def analyze_merge_potential(
        self,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        left_column: str,
        right_column: str
    ) -> Dict[str, Any]:
        """
        Analyze the potential for merging two DataFrames without actually merging.
        
        Returns detailed analysis of merge compatibility and expected results.
        """
        try:
            # Validate inputs
            validation = self._validate_merge_inputs(left_df, right_df, left_column, right_column)
            if not validation['valid']:
                return {
                    'status': 'error',
                    'error_message': validation['error_message']
                }
            
            # Prepare columns
            left_col, right_col = self._prepare_merge_columns(
                left_df, right_df, left_column, right_column
            )
            
            # Get column data
            left_values = left_df[left_col].dropna()
            right_values = right_df[right_col].dropna()
            
            # Analyze overlap
            left_set = set(left_values.astype(str))
            right_set = set(right_values.astype(str))
            
            common_values = left_set.intersection(right_set)
            left_only = left_set - right_set
            right_only = right_set - left_set
            
            # Calculate statistics
            overlap_percentage = len(common_values) / len(left_set) * 100 if left_set else 0
            
            return {
                'status': 'success',
                'analysis': {
                    'left_column': left_col,
                    'right_column': right_col,
                    'left_total_values': len(left_values),
                    'right_total_values': len(right_values),
                    'left_unique_values': len(left_set),
                    'right_unique_values': len(right_set),
                    'common_values': len(common_values),
                    'left_only_values': len(left_only),
                    'right_only_values': len(right_only),
                    'overlap_percentage': overlap_percentage,
                    'data_types': {
                        'left': str(left_df[left_col].dtype),
                        'right': str(right_df[right_col].dtype)
                    },
                    'sample_common_values': list(common_values)[:10],
                    'sample_left_only': list(left_only)[:5],
                    'sample_right_only': list(right_only)[:5]
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f"Error analyzing merge potential: {str(e)}"
            }
    
    def multi_column_merge(
        self,
        left_df: pd.DataFrame,
        right_df: pd.DataFrame,
        left_columns: List[str],
        right_columns: List[str],
        how: str = 'inner',
        suffixes: Tuple[str, str] = ('_left', '_right')
    ) -> Dict[str, Any]:
        """
        Merge DataFrames on multiple columns.
        
        Args:
            left_df: First DataFrame
            right_df: Second DataFrame
            left_columns: List of column names in left DataFrame
            right_columns: List of column names in right DataFrame
            how: Type of merge
            suffixes: Suffixes for overlapping columns
            
        Returns:
            Dict with merge results and statistics
        """
        try:
            if len(left_columns) != len(right_columns):
                return {
                    'status': 'error',
                    'error_message': 'Left and right column lists must have the same length'
                }
            
            # Validate all columns exist
            for col in left_columns:
                if col not in left_df.columns:
                    return {
                        'status': 'error',
                        'error_message': f"Column '{col}' not found in left DataFrame"
                    }
            
            for col in right_columns:
                if col not in right_df.columns:
                    return {
                        'status': 'error',
                        'error_message': f"Column '{col}' not found in right DataFrame"
                    }
            
            # Perform merge
            merged_df = pd.merge(
                left_df,
                right_df,
                left_on=left_columns,
                right_on=right_columns,
                how=how,
                suffixes=suffixes
            )
            
            # Calculate basic stats
            merge_stats = {
                'left_records': len(left_df),
                'right_records': len(right_df),
                'merged_records': len(merged_df),
                'merge_columns_left': left_columns,
                'merge_columns_right': right_columns,
                'merge_type': how
            }
            
            return {
                'status': 'success',
                'merged_df': merged_df,
                'merge_stats': merge_stats
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f"Multi-column merge error: {str(e)}"
            }


# Convenience functions for common operations
def quick_merge(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    left_column: str,
    right_column: str,
    how: str = 'inner'
) -> pd.DataFrame:
    """
    Quick merge function for simple operations.
    Returns only the merged DataFrame without statistics.
    """
    merger = DataFrameMerger()
    result = merger.dynamic_merge(left_df, right_df, left_column, right_column, how)
    
    if result['status'] == 'success':
        return result['merged_df']
    else:
        raise ValueError(f"Merge failed: {result['error_message']}")


def analyze_merge_compatibility(
    left_df: pd.DataFrame,
    right_df: pd.DataFrame,
    left_column: str,
    right_column: str
) -> Dict[str, Any]:
    """
    Quick analysis of merge compatibility between two DataFrames.
    """
    merger = DataFrameMerger()
    return merger.analyze_merge_potential(left_df, right_df, left_column, right_column)