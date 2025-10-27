from sersbench._internal import _load_calibration_data
import matplotlib.pyplot as plt
from typing import Optional, Tuple, List, Dict, Any, Union
import io
import base64
from pathlib import Path

def get_avg_ecr_gate_error(data_dir: Union[str, Path] = "data") -> Optional[Dict[str, List[float]]]:
    """Calculate average ECR gate error across all calibrations.
    
    Args:
        data_dir: Directory containing JSON calibration files
        
    Returns:
        Dictionary with 'calibration_numbers' and 'average_errors' lists, or None if no data found
    """
    calibrations = _load_calibration_data(data_dir)
    if not calibrations:
        return None
    
    results = {'calibration_numbers': [], 'average_errors': []}
    
    for cal in calibrations:
        ecr_errors = []
        for gate in cal['gates']:
            if (gate.get("gate") == "ecr" and 
                gate.get("parameters") and 
                gate["parameters"][0].get("name") == "gate_error"):
                ecr_errors.append(gate["parameters"][0]["value"])
        
        if ecr_errors:
            results['calibration_numbers'].append(cal['calibration_number'])
            results['average_errors'].append(sum(ecr_errors) / len(ecr_errors))
    
    return results if results['calibration_numbers'] else None

def get_specific_gate_error(q1: int, q2: int, data_dir: Union[str, Path] = "data") -> Optional[Dict[str, Any]]:
    """Get gate error for a specific qubit pair across calibrations.
    
    Args:
        q1: First qubit number
        q2: Second qubit number  
        data_dir: Directory containing JSON calibration files
        
    Returns:
        Dictionary with 'calibration_numbers', 'gate_errors', and 'qubit_pair', or None if no data found
    """
    calibrations = _load_calibration_data(data_dir)
    if not calibrations:
        return None
    
    results = {'calibration_numbers': [], 'gate_errors': [], 'qubit_pair': [q1, q2]}
    
    for cal in calibrations:
        for gate in cal['gates']:
            qubits = gate.get("qubits", [])
            if (len(qubits) == 2 and 
                (qubits == [q1, q2] or qubits == [q2, q1]) and
                gate.get("parameters") and 
                gate["parameters"][0].get("name") == "gate_error"):
                
                results['calibration_numbers'].append(cal['calibration_number'])
                results['gate_errors'].append(gate["parameters"][0]["value"])
                break
    
    return results if results['calibration_numbers'] else None

def get_available_qubit_pairs(data_dir: Union[str, Path] = "data") -> List[Tuple[int, int]]:
    """Discover all available two-qubit gate pairs in the calibration data.
    
    Args:
        data_dir: Directory containing JSON calibration files
        
    Returns:
        Sorted list of tuples representing available qubit pairs
    """
    calibrations = _load_calibration_data(data_dir)
    if not calibrations:
        return []
    
    pairs = set()
    for cal in calibrations:
        for gate in cal['gates']:
            qubits = gate.get("qubits", [])
            if len(qubits) == 2:
                pairs.add(tuple(sorted(qubits)))
    
    return sorted(list(pairs))

def get_all_gate_errors(data_dir: Union[str, Path] = "data", max_pairs: int = 20) -> Dict[str, Any]:
    """Comprehensive analysis of all gate errors in the dataset.
    
    Args:
        data_dir: Directory containing JSON calibration files
        max_pairs: Maximum number of qubit pairs to analyze for specific gate errors
        
    Returns:
        Dictionary containing average ECR errors, available pairs, and specific gate error data
    """
    available_pairs = get_available_qubit_pairs(data_dir)
    
    return {
        'avg_ecr_error': get_avg_ecr_gate_error(data_dir),
        'available_qubit_pairs': available_pairs,
        'specific_gate_errors': {
            f"{q1}_{q2}": get_specific_gate_error(q1, q2, data_dir) 
            for q1, q2 in available_pairs[:max_pairs]
        }
    }

def plot_avg_ecr_error(data: Dict[str, List[float]], 
                      save_path: Optional[Union[str, Path]] = None,
                      return_base64: bool = False,
                      show: bool = False,
                      figsize: Tuple[int, int] = (10, 6)) -> Optional[str]:
    """Create a plot of average ECR gate errors over calibrations.
    
    Args:
        data: Output from get_avg_ecr_gate_error()
        save_path: Directory to save plot image (optional)
        return_base64: If True, return base64-encoded plot image
        show: If True, display plot interactively
        figsize: Figure size as (width, height) tuple
        
    Returns:
        Base64-encoded plot string if return_base64=True, otherwise None
    """
    
    if not data or not data.get('calibration_numbers'):
        return None
    
    plt.figure(figsize=figsize)
    plt.plot(data['calibration_numbers'], data['average_errors'], 
            marker='o', linewidth=1, color='mediumpurple')
    plt.xticks(rotation=25)
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.xlabel('Calibration Number', fontweight='bold')
    plt.ylabel('Average Gate Error', fontweight='bold')
    plt.title('Average ECR Gate Error over Calibrations', fontweight='bold')
    plt.tight_layout()
    
    result = None
    if return_base64:
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        result = base64.b64encode(buffer.getvalue()).decode()
    
    if save_path:
        plt.savefig(Path(save_path) / "avg_ecr_gate_error.png", dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return result

def plot_specific_gate_error(data: Dict[str, Any],
                            save_path: Optional[Union[str, Path]] = None,
                            return_base64: bool = False,
                            show: bool = False,
                            figsize: Tuple[int, int] = (10, 6)) -> Optional[str]:
    """Create a plot of gate errors for a specific qubit pair over calibrations.
    
    Args:
        data: Output from get_specific_gate_error()
        save_path: Directory to save plot image (optional)
        return_base64: If True, return base64-encoded plot image
        show: If True, display plot interactively
        figsize: Figure size as (width, height) tuple
        
    Returns:
        Base64-encoded plot string if return_base64=True, otherwise None
    """
    
    if not data or not data.get('calibration_numbers'):
        return None
    
    q1, q2 = data['qubit_pair']
    
    plt.figure(figsize=figsize)
    plt.plot(data['calibration_numbers'], data['gate_errors'], 
            marker='o', linewidth=1)
    plt.xticks(rotation=25)
    plt.grid(True, linestyle='-', alpha=0.7)
    plt.xlabel('Calibration Number', fontweight='bold')
    plt.ylabel('Gate Error', fontweight='bold')
    plt.title(f'Gate Error for Qubits {q1}-{q2} over Calibrations', fontweight='bold')
    plt.tight_layout()
    
    result = None
    if return_base64:
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        result = base64.b64encode(buffer.getvalue()).decode()
    
    if save_path:
        plt.savefig(Path(save_path) / f"gate_error_{q1}_{q2}.png", dpi=300, bbox_inches='tight')
    
    if show:
        plt.show()
    else:
        plt.close()
    
    return result

def create_gate_error_report(data_dir: Union[str, Path] = "data",
                           output_dir: Optional[Union[str, Path]] = None,
                           include_plots: bool = True,
                           max_pairs: int = 10) -> Dict[str, Any]:
    """Generate a comprehensive gate error analysis report.
    
    Args:
        data_dir: Directory containing JSON calibration files
        output_dir: Directory to save plots (if include_plots=True)
        include_plots: Whether to generate and save plot files
        max_pairs: Maximum number of specific qubit pairs to analyze
        
    Returns:
        Dictionary containing summary statistics and all gate error data
    """
    
    all_data = get_all_gate_errors(data_dir, max_pairs)
    
    report = {
        'summary': {
            'total_qubit_pairs': len(all_data['available_qubit_pairs']),
            'has_avg_ecr_data': all_data['avg_ecr_error'] is not None
        },
        'data': all_data
    }
    
    if include_plots and output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if all_data['avg_ecr_error']:
            plot_avg_ecr_error(all_data['avg_ecr_error'], save_path=output_path)
        
        for pair_key, pair_data in all_data['specific_gate_errors'].items():
            if pair_data:
                plot_specific_gate_error(pair_data, save_path=output_path)
    
    return report

def analyze_gate_error_trends(data: Dict[str, List[float]]) -> Dict[str, float]:
    """Analyze statistical trends in gate error data over time.
    
    Args:
        data: Output from get_avg_ecr_gate_error() or similar
        
    Returns:
        Dictionary with trend analysis including slope, min/max errors, and statistics
    """
    if not data or not data.get('average_errors') or len(data['average_errors']) < 2:
        return {}
    
    errors = data['average_errors']
    
    trend = (errors[-1] - errors[0]) / len(errors)
    avg_error = sum(errors) / len(errors)
    min_error = min(errors)
    max_error = max(errors)
    error_range = max_error - min_error
    
    return {
        'trend': trend,  # positive = increasing, negative = decreasing
        'average_error': avg_error,
        'min_error': min_error,
        'max_error': max_error,
        'error_range': error_range,
        'total_calibrations': len(errors)
    }