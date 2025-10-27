import numpy as np
from bqskit.ir.circuit import Circuit 

def get_gate_fidelity(subcirc1: Circuit, subcirc2: Circuit):
    """
    Compute the gate fidelity between two quantum circuit subcircuits.

    Calculates fidelity based on their unitary matrices. Raises an error if
    unitary dimensions differ.

    Args:
        subcirc1 (Circuit): First quantum circuit subcircuit.
        subcirc2 (Circuit): Second quantum circuit subcircuit.

    Returns:
        float: The computed gate fidelity between the two circuits.

    Raises:
        ValueError: If the unitary matrices have different dimensions.
    """
    unitary1 = subcirc1.get_unitary()
    unitary2 = subcirc2.get_unitary()
  
    if unitary1.dim != unitary2.dim:
        raise ValueError('Unitary matrices have different dimensions')
    else:
        op1 = np.trace(unitary1.getH(), unitary1) + abs(np.trace(unitary2.getH(), unitary1))**2
        n = unitary1.dim
        fidelity = op1 / (n * (n + 1))
    return fidelity
