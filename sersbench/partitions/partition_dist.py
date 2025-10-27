from bqskit.ir import Circuit                 
import glob
from sersbench._internal import _analyzeDistances
from bqskit.passes import QuickPartitioner
from bqskit.compiler import Compiler

def get_unitary_distances(circ1: Circuit, circ2: Circuit):
    """
    Compute pairwise unitary distances between partitions of two quantum circuits.

    Partitions each circuit using QuickPartitioner, then calculates the distance 
    between every partition pair. If partitions differ in dimension, distance=1.0.

    Args:
        circ1 (Circuit): First quantum circuit.
        circ2 (Circuit): Second quantum circuit.

    Returns:
        list of list of float: Nested list where each inner list contains distances 
        from one partition of circ1 to all partitions of circ2.
    """
    workflow = [QuickPartitioner()]
    with Compiler() as compiler:
        parted_circuit1 = compiler.compile(circ1, workflow)
        parted_circuit2 = compiler.compile(circ2, workflow)
    
    data = []

    for part1 in parted_circuit1:
        distances = []
        for part2 in parted_circuit2:
            if part1.dim != part2.dim:
                distances.append(1.0)
                continue
            distance = part1.get_unitary().get_distance_from(part2.get_unitary())
            distances.append(distance)
        
        data.append(distances)

    return data


def get_partition_distance_data(path: str):
    """
    Compute partition distance statistics for all unique circuit pairs in a directory.

    Loads all .qasm files in the given directory, computes partition-wise unitary distances
    between each unique pair of circuits, then analyzes minimum, maximum, and average 
    distances per partition.

    Args:
        path (str): Directory containing .qasm circuit files.

    Returns:
        list of dict: Each dict represents a circuit pair comparison with:
            - 'circuit1': Path to first circuit
            - 'circuit2': Path to second circuit
            - 'partitions': List of dicts with keys 'partition_id', 'min_distance', 
              'max_distance', and 'avg_distance' for each partition
    """
    circ_locs = glob.glob(f'{path}/*.qasm')
    results = []
    print(circ_locs)
    for i in range(len(circ_locs)):
        for j in range(i+1, len(circ_locs)):
            circ_loc1 = circ_locs[i]
            circ_loc2 = circ_locs[j]
            
            circ_1 = Circuit.from_file(circ_loc1)
            circ_2 = Circuit.from_file(circ_loc2)
            data = get_unitary_distances(circ_1, circ_2)

            min_vals, max_vals, avg_vals = _analyzeDistances(data)
        
            comparison_result = {
                'circuit1': circ_loc1,
                'circuit2': circ_loc2,
                'partitions': []
            }
        
            for k in range(len(min_vals)):
                partition_data = {
                    'partition_id': k,
                    'min_distance': min_vals[k],
                    'max_distance': max_vals[k],
                    'avg_distance': avg_vals[k]
                }
                comparison_result['partitions'].append(partition_data)
            
            results.append(comparison_result)

    return results
