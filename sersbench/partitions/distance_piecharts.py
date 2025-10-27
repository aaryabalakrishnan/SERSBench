from .partition_dist import get_unitary_distances
from sersbench._internal import _analyzeDistances
import glob
from bqskit.ir import Circuit
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import os
from pathlib import Path
import base64
from io import BytesIO


def create_distance_piecharts(path: str, save_path: str = None):
    """
    Analyze partition distances between all pairs of quantum circuits and generate pie charts.

    For every pair of circuits (.qasm files) in the given directory, this function computes
    partition distance statistics (min, max, average), aggregates the data, and saves it
    as a CSV. Then it bins the average distances into predefined ranges and generates
    pie charts visualizing the distribution of these ranges for each pair of circuit partitions.

    Pie charts and CSV files are saved to `save_path` directory, or current directory if None.

    Args:
        path (str): Directory path containing .qasm circuit files.
        save_path (str, optional): Directory to save CSV and PNG files. Defaults to current directory.

    Returns:
        None
    """
    if save_path is None:
        save_path = os.getcwd()
    else:
        os.makedirs(save_path, exist_ok=True)

    circ_locs = glob.glob(f'{path}/*.qasm')
    data_total = []
    
    for circ_loc01 in circ_locs:
        for circ_loc02 in circ_locs:
            circ_1 = Circuit.from_file(circ_loc01)
            circ_2 = Circuit.from_file(circ_loc02)
            data = get_unitary_distances(circ_1, circ_2)
            
            min_vals, max_vals, avg_vals = _analyzeDistances(data)
            
            circ01_name = Path(circ_loc01).stem
            circ02_name = Path(circ_loc02).stem
            
            for x in range(len(min_vals)):
                circ1_str = f"{circ01_name}_{x}"
                temp_dict = {
                    "circ1_name_partition": circ1_str,
                    "circ2_name": circ02_name,
                    "max": max_vals[x],
                    "min": min_vals[x],
                    "avg": avg_vals[x]
                }
                data_total.append(temp_dict)
    
    df = pd.DataFrame(data_total)
    print(df)
    df.to_csv(os.path.join(save_path, "circuit_partition_analysis.csv"))
    
    df['base_circ1'] = df['circ1_name_partition'].apply(
        lambda x: '_'.join(x.split('_')[:2]) if '_' in x else x
    )
    
    bins = [0.0, 0.25, 0.50, 0.75, 0.8, 0.9, 0.95, 0.98, 0.99, 1.0]
    labels = ['0.0-0.25', '0.25-0.50', '0.50-0.75', '0.75-0.8', '0.8-0.9',
              '0.9-0.95', '0.95-0.98', '0.98-0.99', '0.99-1.0']
    
    color_map = {
        '0.0-0.25': "#6C6DB3",
        '0.25-0.50': '#AAC4FF',
        '0.50-0.75': "#D8B2EE",
        '0.75-0.8': "#6C6DB3",
        '0.8-0.9': '#AAC4FF',
        '0.9-0.95': "#00CAFF",
        '0.95-0.98': "#F3D03E",
        '0.98-0.99': "#5EE2D1",
        '0.99-1.0': "#84BD00"
    }
    
    grouped_comparisons = df.groupby(['base_circ1', 'circ2_name'])
    
    for (base_circ1, circ2_name), group in grouped_comparisons:
        if len(group) > 1:
            group['avg_range'] = pd.cut(group['avg'], bins=bins, labels=labels, 
                                      right=True, include_lowest=True)
            range_counts = group['avg_range'].value_counts().sort_index()
            range_counts = range_counts[range_counts > 0]
            
            if not range_counts.empty:
                plt.figure(figsize=(8, 8))
                plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9)
                colors = [color_map[label] for label in range_counts.index]
                plt.tight_layout()
                
                plt.pie(
                    range_counts,
                    colors=colors,
                    labels=range_counts.index,
                    autopct='%1.1f%%',
                    textprops={'fontsize': 12.5}
                )
                
                plt.title(
                    f'Partition Avg Distribution for {base_circ1} vs {circ2_name}',
                    fontsize=12.5, y=1.08, fontweight='bold'
                )
                plt.axis('equal')
                
                filename = f'pie_chart_{base_circ1.replace("-", "_")}_vs_{circ2_name.replace("-", "_")}.png'
                plt.savefig(os.path.join(save_path, filename))
                plt.close()


def create_distance_piecharts_and_csv_strings(path: str, save_path: str = None):
    """
    Analyze partition distances between all pairs of quantum circuits and generate pie charts.

    For every pair of circuits (.qasm files) in the given directory, this function computes
    partition distance statistics (min, max, average), aggregates the data, and generates
    pie charts as base64 strings stored in memory. All files are prepared for download in a zip file.

    Args:
        path (str): Directory path containing .qasm circuit files.
        save_path (str, optional): Not used anymore, kept for compatibility.

    Returns:
        dict: Dictionary containing:
            - 'csv_data': CSV content as string
            - 'pie_charts': Dictionary mapping PNG filenames to base64 encoded PNG strings
    """
    circ_locs = glob.glob(f'{path}/*.qasm')
    data_total = []
    
    for circ_loc01 in circ_locs:
        for circ_loc02 in circ_locs:
            # Skip comparing a circuit against itself
            if circ_loc01 == circ_loc02:
                continue
                
            circ_1 = Circuit.from_file(circ_loc01)
            circ_2 = Circuit.from_file(circ_loc02)
            data = get_unitary_distances(circ_1, circ_2)
            
            min_vals, max_vals, avg_vals = _analyzeDistances(data)
            
            circ01_name = Path(circ_loc01).stem
            circ02_name = Path(circ_loc02).stem
            
            for x in range(len(min_vals)):
                circ1_str = f"{circ01_name}_{x}"
                temp_dict = {
                    "circ1_name_partition": circ1_str,
                    "circ2_name": circ02_name,
                    "max": max_vals[x],
                    "min": min_vals[x],
                    "avg": avg_vals[x]
                }
                data_total.append(temp_dict)
    
    df = pd.DataFrame(data_total)
    
    # Convert DataFrame to CSV string instead of saving to file
    csv_string = df.to_csv(index=False)
    
    df['base_circ1'] = df['circ1_name_partition'].apply(
        lambda x: '_'.join(x.split('_')[:2]) if '_' in x else x
    )
    
    bins = [0.0, 0.25, 0.50, 0.75, 0.8, 0.9, 0.95, 0.98, 0.99, 1.0]
    labels = ['0.0-0.25', '0.25-0.50', '0.50-0.75', '0.75-0.8', '0.8-0.9',
              '0.9-0.95', '0.95-0.98', '0.98-0.99', '0.99-1.0']
    
    color_map = {
        '0.0-0.25': "#6C6DB3",
        '0.25-0.50': '#AAC4FF',
        '0.50-0.75': "#D8B2EE",
        '0.75-0.8': "#6C6DB3",
        '0.8-0.9': '#AAC4FF',
        '0.9-0.95': "#00CAFF",
        '0.95-0.98': "#F3D03E",
        '0.98-0.99': "#5EE2D1",
        '0.99-1.0': "#84BD00"
    }
    
    grouped_comparisons = df.groupby(['base_circ1', 'circ2_name'])
    pie_charts = {}
    
    for (base_circ1, circ2_name), group in grouped_comparisons:
        if len(group) > 1:
            group['avg_range'] = pd.cut(group['avg'], bins=bins, labels=labels, 
                                      right=True, include_lowest=True)
            range_counts = group['avg_range'].value_counts().sort_index()
            range_counts = range_counts[range_counts > 0]
            
            if not range_counts.empty:
                plt.figure(figsize=(8, 8))
                plt.subplots_adjust(left=0.1, right=0.9, bottom=0.1, top=0.9)
                colors = [color_map[label] for label in range_counts.index]
                plt.tight_layout()
                
                plt.pie(
                    range_counts,
                    colors=colors,
                    labels=range_counts.index,
                    autopct='%1.1f%%',
                    textprops={'fontsize': 12.5}
                )
                
                plt.title(
                    f'Partition Avg Distribution for {base_circ1} vs {circ2_name}',
                    fontsize=12.5, y=1.08, fontweight='bold'
                )
                plt.axis('equal')
                
                # Save plot to BytesIO buffer instead of file
                buffer = BytesIO()
                plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
                buffer.seek(0)
                
                # Convert to base64 string
                img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                buffer.close()
                
                # Store in dictionary with filename as key
                filename = f'pie_chart_{base_circ1.replace("-", "_")}_vs_{circ2_name.replace("-", "_")}.png'
                pie_charts[filename] = img_base64
                
                plt.close()
    
    return {
        'csv_data': csv_string,
        'pie_charts': pie_charts
    }