"""
Process utility functions for reconciliation system
"""
from typing import Dict, Any

def get_process_info() -> Dict[str, Any]:
    """Return empty process info dictionary"""
    return {
        'sib_data_available': False,
        'demand_data_available': False,
        'merge_columns_present': False,
        'error_message': None
    }

def update_process_info(result: Dict[str, Any], info: Dict[str, Any]) -> None:
    """Update process info in result dictionary"""
    result['process_info'] = info

def set_error_message(result: Dict[str, Any], message: str) -> None:
    """Set error message in process info"""
    if 'process_info' not in result:
        result['process_info'] = get_process_info()
    result['process_info']['error_message'] = message