import pandas as pd
import glob
import platform
from bqskit.ir.circuit import Circuit 
from sersbench._internal import (
    _count_large_gates,
    _chi2_distance,
    _kl_divergence,
    _padded_prob_dist,
)
from io import StringIO
from bqskit.ir.lang import get_language


def generate_comparison_stats(path : str, save_path: str = None):
    """
    Generate statistical comparisons between quantum circuits.

    Given a single QASM file or a directory of QASM files, this function compares 
    each circuit against all others (excluding itself) by computing metrics such as 
    CNOT count, circuit depth, Chi-squared distance, and KL divergence based on 
    their probability distributions.

    Optionally saves comparison results as CSV files per circuit.

    Args:
        path (str): Path to a single .qasm file or a directory containing .qasm files.
        save_path (str, optional): Directory path to save CSV files.

    Returns:
        list of pd.DataFrame: List of DataFrames containing comparison statistics.
    """
    
    df_list = []
    
    if platform.system() == "Windows":
        path = path.replace("\\", "/")
        if save_path is not None:
            save_path = save_path.replace("\\", "/")
    
    circ_locs = ""
    if path.__contains__(".qasm"):
        circ_locs = [path]
    else:
        circ_locs = glob.glob(path + "/*.qasm")
    data = []
    for i, circ_loc in enumerate(circ_locs):
        circ_name = circ_loc.split(".")[0].split("/")[-1]
        for j, othercirc_loc in enumerate(circ_locs): 
            if i == j:
               continue 
            else:
                othercirc_name = othercirc_loc.split(".")[0].split("/")[-1]
                othercirc = Circuit.from_file(othercirc_loc)
                depth = othercirc.depth
                cnot_count = _count_large_gates(othercirc)
                array1, array2 = _padded_prob_dist(circ_loc, othercirc_loc)
                kl = _kl_divergence(array1, array2)
                chi = _chi2_distance(array1, array2) 
                data_dict = {
                    "compared_circuit's_name": othercirc_name,
                    "cnot_count": cnot_count,
                    "depth": depth,
                    "chi_squared": chi, 
                    "kl_divergence": kl 
                    }
                data.append(data_dict)
        df = pd.DataFrame(data)
        if save_path is not None:
            df.to_csv(save_path + "/" + circ_name + ".csv")
            
    return df_list

def csv_string_comparison_stats(circ_files: list, names: list):
    """
    Generate comparison statistics between circuits and return as multiple CSV strings.
    
    Args:
        circ_files: List of circuit file paths
        names: List of circuit names corresponding to circ_files
    
    Returns:
        dict: Dictionary where keys are circuit names and values are CSV strings
              Each CSV contains comparisons of that circuit against all others
    """
    # Handle Windows path separators
    if platform.system() == "Windows":
        circ_files = [path.replace("\\", "/") for path in circ_files]
    
    csv_results = {}
    
    for i, circ_loc in enumerate(circ_files):
        data = []
        circ_name = names[i]
        
        for j, othercirc_loc in enumerate(circ_files): 
            if i == j:
                continue 
            else:
                othercirc_name = names[j]
                lang = get_language("qasm")
                with open(othercirc_loc, "r") as f:
                    qasm_str = f.read()
                othercirc = lang.decode(qasm_str)
                depth = othercirc.depth
                cnot_count = _count_large_gates(othercirc)
                array1, array2 = _padded_prob_dist(circ_loc, othercirc_loc)
                kl = _kl_divergence(array1, array2)
                chi = _chi2_distance(array1, array2) 
                data_dict = {
                    "circ_name": othercirc_name,
                    "cnot_count": cnot_count,
                    "depth": depth,
                    "chi_squared": chi, 
                    "kl_divergence": kl 
                }
                data.append(data_dict)
        
        # Create DataFrame and convert to CSV string
        df = pd.DataFrame(data)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_string = csv_buffer.getvalue()
        
        # Store the CSV string with circuit name as key
        csv_results[circ_name] = csv_string
    
    return csv_results