import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple

def split_vicon_csv(filename_base: str, trial_subfolder: str, second_table_header: str='Trajectories') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Splits a CSV file into two separate tables based on a specified header for the second table.

    Parameters:
        filename_base (str): Base name of the CSV file.
        trial_subfolder (str): Subfolder within the data directory.
        second_table_header (str): The header that indicates the start of the second table.
        output_dir (str): Directory where the split CSV files will be saved.
        second_table_header (str): The header that indicates the start of the second table.

    Returns:
        tuple: Two pandas DataFrames containing the data from the first and second tables, respectively.
    """
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    FILE_DIR = BASE_DIR / 'data' / 'raw' / trial_subfolder
    
    print(f"Splitting CSV file for {filename_base} from {FILE_DIR.resolve()}")
    
    csv_path = FILE_DIR / f"{filename_base}.csv"
    split_row_index = None
    
    with open(csv_path, 'r') as file:
        lines = file.readlines()
    
    # Scan file to see where second table begins
    with open(csv_path, 'r') as file:
        for i, line in enumerate(file):
            if second_table_header in line:
                split_row_index = i
                print(f"Found header '{second_table_header}' at row {split_row_index}. Splitting the file into two tables.")
                break
            
    if split_row_index is not None:
        joints_output_path = FILE_DIR / f"{filename_base}_joints.csv"
        trajectories_output_path = FILE_DIR / f"{filename_base}_trajectories.csv"
        
        with open(joints_output_path, 'w') as f_out:
            f_out.writelines(lines[:split_row_index])
            
        with open(trajectories_output_path, 'w') as f_out:
            f_out.writelines(lines[split_row_index:])
        
        # Read the first table (Joints) and the second table (Trajectories) into separate DataFrames
        df_joints = pd.read_csv(joints_output_path, skiprows=4)
        df_trajectories = pd.read_csv(trajectories_output_path, skiprows=4)
        
        # print(f"First table (Joints) shape: {df_joints.shape}. Saved to: {joints_output_path.resolve()}")
        # print(f"Second table (Trajectories) shape: {df_trajectories.shape}. Saved to: {trajectories_output_path.resolve()}")
        
        return df_joints, df_trajectories
    else:
        print(f"Header '{second_table_header}' not found in the CSV file. No split performed.")
        
if __name__ == "__main__":
    # Example usage
    filename_base = "std2KN1"
    trial_subfolder = "0727_Ethan_data"
    second_table_header = "Trajectories"
    
    split_vicon_csv(filename_base, trial_subfolder, second_table_header)
    