from sersbench._internal import optimizeBQSkitFromDirectory, optimizeBQSkitFromFile
import json
import os 
import platform


def optimizeBQSkit(qc: str,  save_path: str = None, replace_filter: str = 'always', json_path: str = None, success_threshold: float = 1e-8, 
    partitioner: int = 0, pass_type: int = 0):
    """
    Optimize circuit(s) using BQSkit. Can optimize individual files as well as directories of QASM files.

    Parameters:
        qc (str): Quantum circuit to be optimized. Path to either a QASM file or folder.

        save_path (str): Path to save the optimized quantum circuit in.

        replace_filter (str): A predicate that determines if the resulting circuit, after calling loop_body on a block, 
        should replace the original operation. (Default: always). Currently support for 'less-than', 'always', and 'less-than-multi'.
        
        json_path (str): Path to save JSON file containing informdation about the circuit.

        success_threshold (float): The distance threshold that determines successful termintation. (Default: 1e-8).

        partitioner (int): Partitions circuit into blocks of 3 qubits. Supports ScanPartitioner and QuickPartitioner. 0 for
        ScanPartitioner and 1 for QuickPartitioner. (Default: 0).

        pass_type (int): Optimization algorithm to use. Supports QSearch and LEAP. 0 for QSearch, 1 for LEAP. (Default: 0).
    
        
    If there is a valid directory entered to save the JSON file to, saves JSON of optimization data to json_path. 
    If no directory is entered, returns a list containing the dictionaries that contain information about the optimized circuits.
    Saves circuit(s) to save_path.
    """
    if platform.system() == 'Windows' and save_path is not None:
        save_path = save_path.replace('\\', '/')
    # Function to check if json is not None
    def validJSONInput():
        if isinstance(json_path, str):
            return os.path.isdir(s=json_path)  
        if json_path == None:
            return True
        return False

    # Checks if path is a QASM file and the save directory is valid
    if os.path.isfile(path=qc) and qc.endswith('.qasm') and os.path.isdir(save_path):
        
        # Checks to see if JSON input is correct
        if validJSONInput():
            # Calls optimization function and stores the dictionary returned into a variable
            infoDict = optimizeBQSkitFromFile(qc=qc,
                                save_path=save_path,
                                success_threshold=success_threshold, 
                                partitioner=partitioner, 
                                pass_type=pass_type,
                                replace_filter=replace_filter)
            
            # Checks if the json save path is a valid directory 
            if not json_path == None and os.path.isdir(json_path):

                # Gets the name of the file inputted wihtout the qasm or path
                index = qc.rfind('/')
                qc_name = qc[index+1:len(qc)-5]

                # Saves file as a json 
                file_name = f'{json_path}/{qc_name}_optimized.json'
                with open(file_name, 'w') as json_file:
                    json.dump(infoDict, json_file)
            # If json_path equals None, returns the dictionary instead
            else:
                return infoDict
        # Raises exception if the json save path is invalid
        elif not validJSONInput():
            raise FileNotFoundError(f'The path {json_path} does not exist.')

    # Checks if path is a directory and the save directory is valid
    elif os.path.isdir(s=qc):
        # Checks to see if JSON input is correct
        if validJSONInput():
            # Calls optimization function
            infoDict = optimizeBQSkitFromDirectory(qc=qc, 
                                        save_path=save_path,
                                        success_threshold=success_threshold, 
                                        partitioner=partitioner, 
                                        pass_type=pass_type,
                                        replace_filter=replace_filter)
            # Checks if the json save path is a valid directory 
            if os.path.isdir(s=json_path):

                # Gets the name of the directory inputted wihtout the path
                index = qc.rfind('/')
                qc_name = qc[index+1:]

                # Saves file as a json 
                file_name = f'{json_path}/{qc_name}_optimized.json'
                with open(file_name, 'w') as json_file:
                    json.dump(infoDict, json_file)
            # If json_path equals None, returns the dictionary instead
            else:
                return infoDict
        # Raises exception if the json save path is invalid
        elif not validJSONInput():
            raise FileNotFoundError(f'The path {json_path} does not exist.')
    # Raise exception if path does not exist
    elif not os.path.exists(path=qc):
        raise FileNotFoundError(f'The path {qc} does not exist.')
    
    # Checks if save path is a string and if the directory is invalid
    elif isinstance(save_path,str) and not os.path.isdir(s=save_path):
        raise FileNotFoundError(f'The path {save_path} is invalid.')
    