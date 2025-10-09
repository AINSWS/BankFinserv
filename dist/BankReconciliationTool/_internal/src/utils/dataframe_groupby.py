"""
DataFrame GroupBy Utility - Dynamic DataFrame Aggregation
"""
import pandas as pd
from typing import List, Dict, Any, Optional, Union
import logging

class DataFrameGroupBy:
    """
    A utility class for dynamic DataFrame grouping and aggregation operations.
    Provides flexible grouping capabilities with multiple aggregation functions.
    """
    
    def __init__(self, validate_columns: bool = True):
        """
        Initialize the DataFrame GroupBy utility.
        
        Args:
            validate_columns: Whether to validate column existence before grouping
        """
        self.validate_columns = validate_columns
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for the groupby utility"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def dynamic_groupby(
        self,
        df: pd.DataFrame,
        group_by_columns: Union[str, List[str]],
        sum_columns: Optional[List[str]] = None,
        count_columns: Optional[List[str]] = None,
        additional_aggregations: Optional[Dict[str, str]] = None,
        include_group_size: bool = True,
        sort_by: Optional[str] = None,
        sort_ascending: bool = False
    ) -> Dict[str, Any]:
        """
        Perform dynamic groupby operations with flexible aggregations.
        
        Args:
            df: DataFrame to group
            group_by_columns: Column(s) to group by
            sum_columns: Columns to sum (numeric aggregation)
            count_columns: Columns to count (count non-null values)
            additional_aggregations: Dict of {column: agg_function} for custom aggregations
            include_group_size: Whether to include group size in results
            sort_by: Column to sort results by
            sort_ascending: Sort order (True for ascending, False for descending)
            
        Returns:
            Dict containing grouped DataFrame and aggregation statistics
        """
        try:
            # Input validation
            if self.validate_columns:
                validation_result = self._validate_groupby_inputs(
                    df, group_by_columns, sum_columns, count_columns
                )
                if not validation_result['valid']:
                    return {
                        'status': 'error',
                        'error_message': validation_result['error_message'],
                        'grouped_df': None,
                        'group_stats': {}
                    }
            
            # Normalize group_by_columns to list
            if isinstance(group_by_columns, str):
                group_by_columns = [group_by_columns]
            
            # Perform groupby operation
            grouped = df.groupby(group_by_columns)
            
            # Build aggregation operations step by step
            agg_operations = {}
            
            # Add sum operations
            if sum_columns:
                for col in sum_columns:
                    if col in df.columns:
                        agg_operations[col] = 'sum'
            
            # Add count operations (use size for each count column)
            count_results = []
            if count_columns:
                for col in count_columns:
                    if col in df.columns:
                        count_df = grouped[col].count().reset_index()
                        count_df = count_df.rename(columns={col: f'{col}_count'})
                        count_results.append(count_df)
            
            # Add custom aggregations
            custom_results = []
            if additional_aggregations:
                for col, func in additional_aggregations.items():
                    if col in df.columns:
                        custom_df = grouped[col].agg(func).reset_index()
                        custom_df = custom_df.rename(columns={col: f'{col}_{func}'})
                        custom_results.append(custom_df)
            
            # Start with basic aggregations
            if agg_operations:
                result_df = grouped.agg(agg_operations).reset_index()
            else:
                # If no aggregations, just get the groups
                result_df = grouped.size().reset_index(name='temp_size')
                result_df = result_df.drop('temp_size', axis=1)
                result_df = result_df.drop_duplicates()
            
            # Merge count results
            for count_df in count_results:
                result_df = result_df.merge(count_df, on=group_by_columns, how='left')
            
            # Merge custom aggregation results
            for custom_df in custom_results:
                result_df = result_df.merge(custom_df, on=group_by_columns, how='left')
            
            # Add group size if requested and not already present
            if include_group_size and 'group_size' not in result_df.columns:
                group_sizes = grouped.size().reset_index(name='group_size')
                result_df = result_df.merge(group_sizes, on=group_by_columns, how='left')
            
            # Sort results if requested
            if sort_by and sort_by in result_df.columns:
                result_df = result_df.sort_values(sort_by, ascending=sort_ascending)
            
            # Calculate group statistics
            group_stats = self._calculate_group_stats(df, grouped, group_by_columns, result_df)
            
            # Add metadata
            result_df['_groupby_timestamp'] = pd.Timestamp.now()
            result_df['_grouped_by'] = str(group_by_columns)
            
            self.logger.info(f"Successfully grouped DataFrame: {len(result_df)} groups created")
            
            return {
                'status': 'success',
                'grouped_df': result_df,
                'group_stats': group_stats,
                'groupby_details': {
                    'group_by_columns': group_by_columns,
                    'sum_columns': sum_columns or [],
                    'count_columns': count_columns or [],
                    'additional_aggregations': additional_aggregations or {},
                    'total_groups': len(result_df),
                    'original_rows': len(df)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error during DataFrame groupby: {str(e)}")
            return {
                'status': 'error',
                'error_message': str(e),
                'grouped_df': None,
                'group_stats': {},
                'groupby_details': {}
            }
    
    def _validate_groupby_inputs(
        self,
        df: pd.DataFrame,
        group_by_columns: Union[str, List[str]],
        sum_columns: Optional[List[str]],
        count_columns: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Validate inputs before grouping"""
        
        # Check if DataFrame is not empty
        if df.empty:
            return {'valid': False, 'error_message': 'DataFrame is empty'}
        
        # Normalize group_by_columns to list for validation
        if isinstance(group_by_columns, str):
            group_by_columns = [group_by_columns]
        
        # Check if groupby columns exist
        available_columns = df.columns.tolist()
        
        for col in group_by_columns:
            if col not in available_columns:
                return {
                    'valid': False,
                    'error_message': f"Group by column '{col}' not found in DataFrame. Available: {available_columns}"
                }
        
        # Check sum columns
        if sum_columns:
            for col in sum_columns:
                if col not in available_columns:
                    return {
                        'valid': False,
                        'error_message': f"Sum column '{col}' not found in DataFrame. Available: {available_columns}"
                    }
                # Check if column is numeric for sum operation
                if not pd.api.types.is_numeric_dtype(df[col]):
                    return {
                        'valid': False,
                        'error_message': f"Sum column '{col}' is not numeric. Type: {df[col].dtype}"
                    }
        
        # Check count columns
        if count_columns:
            for col in count_columns:
                if col not in available_columns:
                    return {
                        'valid': False,
                        'error_message': f"Count column '{col}' not found in DataFrame. Available: {available_columns}"
                    }
        
        return {'valid': True, 'error_message': None}
    
    def _calculate_group_stats(
        self,
        original_df: pd.DataFrame,
        grouped: pd.core.groupby.DataFrameGroupBy,
        group_by_columns: List[str],
        result_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """Calculate detailed group statistics"""
        
        try:
            group_sizes = grouped.size()
            
            return {
                'total_groups': len(result_df),
                'original_rows': len(original_df),
                'group_by_columns': group_by_columns,
                'avg_group_size': group_sizes.mean(),
                'min_group_size': group_sizes.min(),
                'max_group_size': group_sizes.max(),
                'median_group_size': group_sizes.median(),
                'groups_with_single_row': (group_sizes == 1).sum(),
                'largest_groups': group_sizes.nlargest(5).to_dict(),
                'compression_ratio': len(result_df) / len(original_df) * 100
            }
        except Exception as e:
            self.logger.warning(f"Could not calculate group stats: {str(e)}")
            return {
                'total_groups': len(result_df),
                'original_rows': len(original_df),
                'group_by_columns': group_by_columns
            }
    
    def pivot_summary(
        self,
        df: pd.DataFrame,
        index_columns: Union[str, List[str]],
        value_column: str,
        aggfunc: str = 'sum',
        fill_value: Any = 0
    ) -> Dict[str, Any]:
        """
        Create a pivot table summary from DataFrame.
        
        Args:
            df: DataFrame to pivot
            index_columns: Columns to use as index
            value_column: Column to aggregate
            aggfunc: Aggregation function ('sum', 'count', 'mean', etc.)
            fill_value: Value to fill missing data
            
        Returns:
            Dict with pivot table results
        """
        try:
            # Normalize index_columns to list
            if isinstance(index_columns, str):
                index_columns = [index_columns]
            
            # Create pivot table
            pivot_df = df.pivot_table(
                index=index_columns,
                values=value_column,
                aggfunc=aggfunc,
                fill_value=fill_value
            ).reset_index()
            
            return {
                'status': 'success',
                'pivot_df': pivot_df,
                'pivot_stats': {
                    'index_columns': index_columns,
                    'value_column': value_column,
                    'aggregation_function': aggfunc,
                    'total_rows': len(pivot_df),
                    'fill_value': fill_value
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f"Pivot operation failed: {str(e)}",
                'pivot_df': None,
                'pivot_stats': {}
            }
    
    def multi_level_groupby(
        self,
        df: pd.DataFrame,
        level1_columns: Union[str, List[str]],
        level2_columns: Union[str, List[str]],
        aggregation_columns: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Perform multi-level groupby with hierarchical aggregation.
        
        Args:
            df: DataFrame to group
            level1_columns: First level grouping columns
            level2_columns: Second level grouping columns  
            aggregation_columns: Dict of {column: aggregation_function}
            
        Returns:
            Dict with multi-level grouped results
        """
        try:
            # Normalize columns to lists
            if isinstance(level1_columns, str):
                level1_columns = [level1_columns]
            if isinstance(level2_columns, str):
                level2_columns = [level2_columns]
            
            # Level 1 grouping
            level1_result = self.dynamic_groupby(
                df, level1_columns, 
                sum_columns=[col for col, func in aggregation_columns.items() if func == 'sum'],
                count_columns=[col for col, func in aggregation_columns.items() if func == 'count'],
                additional_aggregations={col: func for col, func in aggregation_columns.items() if func not in ['sum', 'count']}
            )
            
            # Level 2 grouping
            level2_result = self.dynamic_groupby(
                df, level1_columns + level2_columns,
                sum_columns=[col for col, func in aggregation_columns.items() if func == 'sum'],
                count_columns=[col for col, func in aggregation_columns.items() if func == 'count'],
                additional_aggregations={col: func for col, func in aggregation_columns.items() if func not in ['sum', 'count']}
            )
            
            return {
                'status': 'success',
                'level1_summary': level1_result,
                'level2_detail': level2_result,
                'hierarchy_info': {
                    'level1_groups': len(level1_result['grouped_df']) if level1_result['status'] == 'success' else 0,
                    'level2_groups': len(level2_result['grouped_df']) if level2_result['status'] == 'success' else 0,
                    'level1_columns': level1_columns,
                    'level2_columns': level2_columns
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error_message': f"Multi-level groupby failed: {str(e)}",
                'level1_summary': None,
                'level2_detail': None
            }


# Convenience functions for common operations
def quick_groupby(
    df: pd.DataFrame,
    group_by: Union[str, List[str]],
    sum_cols: Optional[List[str]] = None,
    count_cols: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Quick groupby function for simple operations.
    Returns only the grouped DataFrame without statistics.
    """
    grouper = DataFrameGroupBy()
    result = grouper.dynamic_groupby(df, group_by, sum_cols, count_cols)
    
    if result['status'] == 'success':
        return result['grouped_df']
    else:
        raise ValueError(f"Groupby failed: {result['error_message']}")


def bank_transaction_summary(
    df: pd.DataFrame,
    group_by_col: str = 'branch_name',
    amount_col: str = 'amount',
    transaction_col: str = 'reference_id'
) -> pd.DataFrame:
    """
    Quick bank transaction summary by branch/group.
    """
    grouper = DataFrameGroupBy()
    result = grouper.dynamic_groupby(
        df=df,
        group_by_columns=group_by_col,
        sum_columns=[amount_col],
        count_columns=[transaction_col],
        sort_by=amount_col,
        sort_ascending=False
    )
    
    if result['status'] == 'success':
        return result['grouped_df']
    else:
        raise ValueError(f"Bank summary failed: {result['error_message']}")


def reconciliation_summary(
    df: pd.DataFrame,
    status_col: str = 'reconciliation_status',
    amount_col: str = 'amount'
) -> pd.DataFrame:
    """
    Quick reconciliation status summary.
    """
    grouper = DataFrameGroupBy()
    result = grouper.dynamic_groupby(
        df=df,
        group_by_columns=status_col,
        sum_columns=[amount_col],
        count_columns=['reference_id'] if 'reference_id' in df.columns else [df.columns[0]],
        sort_by=amount_col,
        sort_ascending=False
    )
    
    if result['status'] == 'success':
        return result['grouped_df']
    else:
        raise ValueError(f"Reconciliation summary failed: {result['error_message']}")