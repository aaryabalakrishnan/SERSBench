import pandas as pd
import glob
from bqskit.ir import Circuit
from bqskit.compiler import Compiler
from bqskit.passes import QuickPartitioner
from sersbench._internal import _count_large_gates
import os
import platform

def partition_data(circuit: str, csv_save_path: str = None, png_save_path: str = None):
    """
    Partition quantum circuits and extract partition statistics.

    Processes a single QASM file or all QASM files in a directory. For each circuit,
    partitions it using QuickPartitioner, then gathers CNOT gate counts and depth
    for each partition.

    Saves results as CSV and bar plot PNGs if save paths are provided.

    Args:
        circuit (str): Path to a single .qasm file or a directory containing .qasm files.
        csv_save_path (str, optional): Directory path to save CSV files.
        png_save_path (str, optional): Directory path to save bar plot PNG images.

    Returns:
        list of pd.DataFrame: List of DataFrames with partition info per circuit.
            Each DataFrame columns:
                - circ_path: Circuit file path
                - partition_num: Partition index
                - cnot: Number of large (CNOT) gates in partition
                - depth: Partition circuit depth
    """
    
    if platform.system() == "Windows":
        circuit = circuit.replace("\\", "/")
    circ_locs = glob.glob(f"{circuit}/*.qasm") if os.path.isdir(circuit) else [circuit]
    df_list = []
    for circ_loc in circ_locs:
        circ_name = circ_loc.split(".")[0].split("/")[-1]
        circ = Circuit.from_file(circ_loc)
        workflow= [QuickPartitioner()]
        with Compiler() as compiler: 
            parted_circuit = compiler.compile(circ, workflow)
        data = []
        for i, partition in enumerate(parted_circuit):
            subcirc = partition.gate._circuit 
            num_gates = _count_large_gates(subcirc)
            depth = subcirc.depth
            data_dict = {"circ_path": circ_loc, "partition_num": i, "cnot": num_gates, "depth": depth}  
            data.append(data_dict)
        df = pd.DataFrame(data)
        df_list.append(df)
        
        if csv_save_path is not None:
            df.to_csv(f"{csv_save_path}/{circ_name}.csv")
        
        if png_save_path is not None:
            sorted_df=df.sort_values("cnot")
            df['cnot'].value_counts()[sorted_df.cnot.unique()].plot(kind='bar').get_figure().savefig(f"{png_save_path}/{circ_name}_cnot.png")
            sorted_df=df.sort_values("depth")
            df['depth'].value_counts()[sorted_df.depth.unique()].plot(kind='bar').get_figure().savefig(f"{png_save_path}/{circ_name}_depth.png")
    
    return df_list
