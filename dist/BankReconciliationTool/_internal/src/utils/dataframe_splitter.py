"""
Dynamic DataFrame Utilities - Modular text splitting and processing functions
"""
import pandas as pd
import re
from typing import List, Optional, Dict, Any, Union

class DataFrameSplitter:
    """Utility class for dynamic DataFrame column splitting and processing"""
    
    @staticmethod
    def split_column_by_delimiter(
        df: pd.DataFrame, 
        column_name: str, 
        delimiter: str = "/",
        new_column_names: Optional[List[str]] = None,
        keep_original: bool = True,
        max_splits: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Split a DataFrame column by delimiter into multiple columns
        
        Args:
            df: Input DataFrame
            column_name: Name of column to split
            delimiter: Delimiter to split on (default: "/")
            new_column_names: List of names for new columns. If None, uses split_1, split_2, etc.
            keep_original: Whether to keep the original column
            max_splits: Maximum number of splits to perform
            
        Returns:
            DataFrame with split columns added
        """
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")
        
        result_df = df.copy()
        
        # Perform the split
        split_data = result_df[column_name].astype(str).str.split(delimiter, expand=True, n=max_splits)
        
        # Generate column names if not provided
        if new_column_names is None:
            new_column_names = [f"{column_name}_split_{i+1}" for i in range(split_data.shape[1])]
        else:
            # Ensure we have enough column names
            while len(new_column_names) < split_data.shape[1]:
                new_column_names.append(f"split_{len(new_column_names)+1}")
        
        # Add split columns to result
        for i, col_name in enumerate(new_column_names):
            if i < split_data.shape[1]:
                result_df[col_name] = split_data.iloc[:, i].str.strip()
            else:
                break
        
        # Remove original column if requested
        if not keep_original:
            result_df = result_df.drop(columns=[column_name])
        
        return result_df
    
    @staticmethod
    def smart_column_split(
        df: pd.DataFrame,
        column_name: str,
        delimiter: str = "/",
        expected_parts: List[str] = None,
        auto_detect_structure: bool = True
    ) -> Dict[str, Any]:
        """
        Intelligently split a column and analyze the structure
        
        Args:
            df: Input DataFrame
            column_name: Column to split
            delimiter: Delimiter to use
            expected_parts: Expected column names for split parts
            auto_detect_structure: Whether to auto-detect optimal structure
            
        Returns:
            Dictionary with split DataFrame and analysis info
        """
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")
        
        # Analyze the column structure first
        analysis = DataFrameSplitter.analyze_column_structure(df, column_name, delimiter)
        
        # Use expected parts or auto-detected structure
        if expected_parts:
            column_names = expected_parts
        elif auto_detect_structure and 'suggested_names' in analysis:
            column_names = analysis['suggested_names']
        else:
            column_names = None
        
        # Perform the split
        split_df = DataFrameSplitter.split_column_by_delimiter(
            df, column_name, delimiter, column_names, keep_original=True
        )
        
        return {
            'dataframe': split_df,
            'analysis': analysis,
            'split_columns': column_names or [f"split_{i+1}" for i in range(analysis['max_parts'])],
            'original_column': column_name,
            'delimiter': delimiter
        }
    
    @staticmethod
    def analyze_column_structure(
        df: pd.DataFrame, 
        column_name: str, 
        delimiter: str = "/"
    ) -> Dict[str, Any]:
        """
        Analyze the structure of a delimited column
        
        Args:
            df: Input DataFrame
            column_name: Column to analyze
            delimiter: Delimiter to analyze
            
        Returns:
            Analysis results including part counts, patterns, etc.
        """
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")
        
        column_data = df[column_name].astype(str)
        
        # Count parts for each row
        part_counts = column_data.str.count(delimiter) + 1
        
        # Get sample splits to understand structure
        sample_splits = []
        for value in column_data.head(10):
            if pd.notna(value) and str(value).strip():
                parts = str(value).split(delimiter)
                sample_splits.append([part.strip() for part in parts])
        
        analysis = {
            'total_rows': len(df),
            'non_null_rows': column_data.notna().sum(),
            'min_parts': int(part_counts.min()) if len(part_counts) > 0 else 0,
            'max_parts': int(part_counts.max()) if len(part_counts) > 0 else 0,
            'most_common_parts': int(part_counts.mode().iloc[0]) if len(part_counts) > 0 else 0,
            'part_count_distribution': part_counts.value_counts().to_dict(),
            'sample_splits': sample_splits[:5],
            'delimiter': delimiter,
            'column_name': column_name
        }
        
        # Suggest column names based on common patterns
        if sample_splits:
            max_parts = analysis['max_parts']
            if delimiter == "/" and max_parts >= 4:
                # Common pattern for financial/loan data
                analysis['suggested_names'] = [
                    'description', 'loan_id', 'customer_name', 
                    'group_name', 'branch_name'
                ][:max_parts]
            else:
                analysis['suggested_names'] = [f'part_{i+1}' for i in range(max_parts)]
        
        return analysis
    
    @staticmethod
    def filter_split_data(
        df: pd.DataFrame,
        column_name: str,
        filter_function: callable,
        reason_column: str = "filter_reason"
    ) -> pd.DataFrame:
        """
        Filter split data based on a custom function
        
        Args:
            df: DataFrame with split data
            column_name: Column to filter
            filter_function: Function that returns True for valid entries
            reason_column: Name for column explaining filter reason
            
        Returns:
            DataFrame with filter results added
        """
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")
        
        result_df = df.copy()
        
        # Apply filter function
        def get_filter_result(value):
            try:
                return filter_function(value)
            except:
                return False
        
        def get_filter_reason(value):
            try:
                if pd.isna(value) or not str(value).strip():
                    return "Empty/Null"
                elif filter_function(value):
                    return "Valid"
                else:
                    return "Invalid"
            except Exception as e:
                return f"Error: {str(e)}"
        
        result_df[f'{column_name}_valid'] = result_df[column_name].apply(get_filter_result)
        result_df[reason_column] = result_df[column_name].apply(get_filter_reason)
        
        return result_df
    
    @staticmethod
    def create_loan_id_filter() -> callable:
        """
        Create a filter function specifically for loan IDs
        
        Returns:
            Function that validates loan ID patterns
        """
        def is_valid_loan_id(value):
            if pd.isna(value) or value is None:
                return False
            
            value_str = str(value).strip()
            
            if not value_str:
                return False
            
            # Loan ID validation rules
            has_numbers = bool(re.search(r'\d', value_str))
            is_purely_alpha = value_str.isalpha()
            min_length = len(value_str) >= 2
            
            # Common branch name patterns to exclude
            branch_indicators = ['branch', 'office', 'head', 'main', 'sub', 'regional']
            is_branch_name = any(indicator.lower() in value_str.lower() for indicator in branch_indicators)
            
            return has_numbers and not is_purely_alpha and min_length and not is_branch_name
        
        return is_valid_loan_id
    
    @staticmethod
    def process_narration_field(
        df: pd.DataFrame,
        narration_column: str,
        delimiter: str = "/",
        expected_structure: List[str] = None,
        apply_loan_filter: bool = True
    ) -> Dict[str, Any]:
        """
        Complete processing pipeline for narration field splitting
        
        Args:
            df: Input DataFrame
            narration_column: Name of narration column
            delimiter: Delimiter to split on
            expected_structure: Expected column names after split
            apply_loan_filter: Whether to apply loan ID filtering
            
        Returns:
            Complete processing results
        """
        # Default structure for financial data
        if expected_structure is None:
            expected_structure = ['description', 'loan_id', 'customer_name', 'group_name', 'branch_name']
        
        # Step 1: Analyze structure
        analysis = DataFrameSplitter.analyze_column_structure(df, narration_column, delimiter)
        
        # Step 2: Split the column
        split_result = DataFrameSplitter.smart_column_split(
            df, narration_column, delimiter, expected_structure, auto_detect_structure=True
        )
        
        split_df = split_result['dataframe']
        
        # Step 3: Apply loan ID filtering if requested
        if apply_loan_filter and 'loan_id' in split_df.columns:
            loan_filter = DataFrameSplitter.create_loan_id_filter()
            split_df = DataFrameSplitter.filter_split_data(
                split_df, 'loan_id', loan_filter, 'loan_filter_reason'
            )
        
        # Step 4: Generate summary statistics
        summary = {
            'total_rows': len(df),
            'split_columns': split_result['split_columns'],
            'analysis': analysis,
            'sample_data': split_df.head(5).to_dict('records')
        }
        
        if apply_loan_filter and 'loan_id_valid' in split_df.columns:
            valid_loans = split_df[split_df['loan_id_valid'] == True]
            invalid_loans = split_df[split_df['loan_id_valid'] == False]
            
            summary.update({
                'valid_loan_count': len(valid_loans),
                'invalid_loan_count': len(invalid_loans),
                'loan_success_rate': (len(valid_loans) / len(split_df) * 100) if len(split_df) > 0 else 0,
                'valid_loan_sample': valid_loans.head(3).to_dict('records'),
                'invalid_loan_sample': invalid_loans.head(3).to_dict('records')
            })
        
        return {
            'dataframe': split_df,
            'summary': summary,
            'original_analysis': analysis
        }


# Convenience functions for common use cases
def split_narration_column(
    df: pd.DataFrame, 
    column_name: str, 
    delimiter: str = "/",
    keep_original: bool = True
) -> pd.DataFrame:
    """
    Quick function to split narration column with standard loan structure
    """
    expected_columns = ['description', 'loan_id', 'customer_name', 'group_name', 'branch_name']
    return DataFrameSplitter.split_column_by_delimiter(
        df, column_name, delimiter, expected_columns, keep_original
    )

def analyze_delimited_column(df: pd.DataFrame, column_name: str, delimiter: str = "/") -> Dict[str, Any]:
    """
    Quick function to analyze a delimited column structure
    """
    return DataFrameSplitter.analyze_column_structure(df, column_name, delimiter)