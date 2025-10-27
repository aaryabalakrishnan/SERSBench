from bqskit.ir import Circuit, Operation
from bqskit.passes import QuickPartitioner
from bqskit.compiler import Compiler
import numpy as np
from scipy.stats import entropy

def _count_large_gates(circuit_like: Operation | list[Operation]):

    if isinstance(circuit_like, Operation):
        operation = circuit_like
        num_large_gates = 0
        for gate in operation.gate._circuit.gate_set:
            if gate.num_qudits == 1:
                continue
            num_large_gates += operation.gate._circuit.count(gate)
    elif isinstance(circuit_like, Circuit):
        circuit = circuit_like
        num_large_gates = 0
        for gate in circuit.gate_set:
            if gate.num_qudits == 1:
                continue
            num_large_gates += circuit.count(gate)
    else:
        operations = circuit_like
        num_large_gates = 0
        for operation in operations:
            for gate in operation.gate._circuit.gate_set:
                if gate.num_qudits == 1:
                    continue
                num_large_gates += operation.gate._circuit.count(gate)

    return num_large_gates
  
def _padded_prob_dist(loc1, loc2):
  list_of_arrays = []
  circ_locs = [loc1, loc2]
  for circ_loc in circ_locs:
      circ_name = circ_loc.split(".")[0].split("/")[-1]
      circ = Circuit.from_file(circ_loc)
      workflow = [QuickPartitioner()]
      with Compiler() as compiler: 
          parted_circuit = compiler.compile(circ, workflow)
      freq_dict = {}
      cxcount_list = []
      prob_dist_array = []
      for i, partition in enumerate(parted_circuit): 
          subcirc = partition.gate._circuit 
          num_gates = _count_large_gates(subcirc)
          cxcount_list.append(num_gates)
      for num in cxcount_list: #list of frequency of number of cnots
              if num in freq_dict:
                  freq_dict[num] += 1
              else:
                  freq_dict[num] = 1 
      for key, value in freq_dict.items(): #normalizes in freq_dict
          freq_dict[key] = value / sum(freq_dict.values()) 
      for i in range(max(freq_dict) + 1): #makes probability distribution array
          if i in freq_dict:
              prob_dist_array.append(freq_dict[i])
          else:
              prob_dist_array.append(0)
      list_of_arrays.append(prob_dist_array)
  max_length = max(len(array) for array in list_of_arrays)
  for i in range(len(list_of_arrays)): #pads arrays to same length
          while len(list_of_arrays[i]) < max_length:
              list_of_arrays[i].append(0)
  return list_of_arrays[0],list_of_arrays[-1]


def _kl_divergence(p, q):
  epsilon = 1e-10
  p_smooth = np.array(p) + epsilon
  q_smooth = np.array(q) + epsilon
  p_smooth = p_smooth / np.sum(p_smooth)
  q_smooth = q_smooth / np.sum(q_smooth)
  kl = entropy(p_smooth, q_smooth)
  print("KL divergence is", kl)
  return kl
      
def _chi2_distance(a, b):
  hist1 = np.asarray(a, dtype=float)
  hist2 = np.asarray(b, dtype=float)

  numerator = (hist1 - hist2) ** 2
  denominator = hist1 + hist2
  non_zero_indices = denominator != 0

  chi = 0.5 * np.sum(numerator[non_zero_indices] / denominator[non_zero_indices])
  print("Chi2 divergence is", chi)
  return chi

def _analyzeDistances(data):
    min_list = []
    max_list= []
    avg =[]

    for distances in data:
        min_list.append(min(distances))
        max_list.append(max(distances))
        avg.append(sum(distances) / len(distances))
    
    return min_list, max_list, avg