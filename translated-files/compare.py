import numpy as np
import scipy.io as sio
from pathlib import Path

def compare_pipeline_data(matlab_filepath, python_filepath, var_name='Data_IMU'):
    print(f"--- Starting Comparison ---")
    
    # 1. Load the original MATLAB data
    try:
        mat_data = sio.loadmat(matlab_filepath)
        mat_matrix = mat_data[var_name]
        print(f"Successfully loaded '{var_name}' from the original MATLAB file.")
    except KeyError:
        print(f"Error: Variable '{var_name}' not found in the original MATLAB file.")
        return
    except Exception as e:
        print(f"Error loading original MATLAB file: {e}")
        return

    # 2. Load the Python-generated .mat data
    try:
        py_data = sio.loadmat(python_filepath)
        py_matrix = py_data[var_name]
        print(f"Successfully loaded '{var_name}' from the Python-generated file.")
    except KeyError:
        print(f"Error: Variable '{var_name}' not found in the Python-generated file.")
        print(f"Variables available: {list(py_data.keys())}")
        return
    except Exception as e:
        print(f"Error loading Python-generated file: {e}")
        return

    # 3. Check if the shapes (dimensions) match
    print("\n--- Shape Check ---")
    print(f"Original MATLAB shape: {mat_matrix.shape}")
    print(f"Python-generated shape: {py_matrix.shape}")
    
    if mat_matrix.shape != py_matrix.shape:
        print("WARNING: Matrix dimensions do not match! Cannot perform direct element-wise comparison.")
        return
    else:
        print("Shapes match perfectly.")

    # 4. Perform numerical comparison
    print("\n--- Value Check ---")
    
    # Using np.allclose to check if they are identical within a standard tolerance
    is_close = np.allclose(mat_matrix, py_matrix, rtol=1e-05, atol=1e-08)
    
    # Calculate the maximum absolute difference
    max_diff = np.max(np.abs(mat_matrix - py_matrix))
    
    if is_close:
        print("RESULT: SUCCESS! The matrices are functionally identical.")
    else:
        print("RESULT: FAILURE. The matrices have differences beyond the acceptable tolerance.")
        
    print(f"Maximum absolute difference between the two matrices: {max_diff}")
    
    # Exact match calculation
    exact_matches = np.sum(mat_matrix == py_matrix)
    total_elements = mat_matrix.size
    print(f"Exact identical elements: {exact_matches} out of {total_elements} ({(exact_matches/total_elements)*100:.2f}%)")

# ==========================================
# Run the comparison
# ==========================================
if __name__ == "__main__":
    # Replace these with your actual file names
    BASE_DIR = Path(__file__).resolve().parent.parent
    MATLAB_FILE = BASE_DIR / 'data' / 'processed' / 'std2KN2.mat' 
    PYTHON_FILE = BASE_DIR / 'data' / 'processed' / '0727_Ethan_data' /'std2KN2_labeled.mat' 
    
    # 'Data_IMU' is the variable name identified from your previous MATLAB file dump
    compare_pipeline_data(str(MATLAB_FILE), str(PYTHON_FILE), var_name='IMU_label')