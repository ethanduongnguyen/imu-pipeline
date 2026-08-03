import numpy as np
import pandas as pd
from typing import Tuple

def matlab_round(x: np.ndarray, decimals: int = 2) -> np.ndarray:
    """
    Mimics MATLAB's rounding behavior by rounding to a specified number of decimal places.

    Parameters:
        x (np.ndarray): Input array to be rounded.
        decimals (int): Number of decimal places to round to.

    Returns:
        np.ndarray: Rounded array.
    """
    factor = 10 ** decimals
    return np.trunc(x * factor + np.sign(x) * 0.5) / factor

def matchIMUandVicon(vicon_from_imu: np.ndarray, vicon_data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Translates matchIMUandVicon.m into Python
    Synchronizes IMU timestamps with Vicon data by finding matching spatial data points and calculating a linear fit to align the two datasets.

    Parameters:
        vicon_from_imu (np.ndarray): Timestamps from IMU data, np.ndarray of shape (N, 3) where N is the number of IMU samples
        vicon_data (np.ndarray): Vicon data with timestamps, np.ndarray of shape (M, 3) where M is the number of Vicon samples

    Returns:
        ratio (np.ndarray): Linear regression coefficients [slope, intercept]
        ratio_round (np.ndarray): Rounded linear regression coefficients [slope, intercept]
        id_vicon (np.ndarray): Indices of Vicon data that match the IMU timestamps
        id_imu (np.ndarray): Indices of IMU data that match the Vicon timestamps
    """
    
    imu_round = matlab_round(vicon_from_imu[:, 0:3], 2)  # Round IMU timestamps to 2 decimal places
    vicon_round = matlab_round(vicon_data[:, 0:3], 2)  # Round Vicon timestamps to 2 decimal places
    
    # Find intersecting rows and capture original indices
    df_imu = pd.DataFrame(imu_round, columns=['x', 'y', 'z']).reset_index()
    df_vicon = pd.DataFrame(vicon_round, columns=['x', 'y', 'z']).reset_index()
    
    # Drop duplicating coordinate rows to replicate MATLAB's intersect behavior
    df_imu = df_imu.drop_duplicates(subset=['x', 'y', 'z'], keep='first')
    df_vicon = df_vicon.drop_duplicates(subset=['x', 'y', 'z'], keep='first')
    
    matched = pd.merge(df_imu, df_vicon, on=['x', 'y', 'z'], how='inner', suffixes=('_imu', '_vicon'))
    
    # Extract indices of matched rows
    id_imu = matched['index_imu'].to_numpy() + 1
    id_vicon = matched['index_vicon'].to_numpy() + 1
    
    # Calculate linear regression coefficients to align IMU and Vicon timestamps
    ratio = np.polyfit(id_vicon, id_imu, 1)
    
    ratio_round = np.round(ratio)
    
    return ratio, ratio_round, id_vicon, id_imu