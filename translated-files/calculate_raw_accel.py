import numpy as np
from scipy.spatial.transform import Rotation as R

def calculate_raw_accel(rpy_deg: np.ndarray, accel: np.ndarray) -> np.ndarray:
    """
    Translates calculate_rawAccel.m into Python
    Isolates linear acceleration by removing global gravity vector

    Parameters:
        rpy_deg (np.ndarray): Roll, pitch, and yaw angles in degrees, np.ndarray of shape (N, 3) where N is the number of samples
        accel (np.ndarray): Measured acceleration in the world frame, np.ndarray of shape (N, 3) where N is the number of samples

    Returns:
        raw_accel (np.ndarray): Isolated linear acceleration in the body frame, np.ndarray of shape (N, 3) where N is the number of samples
    """
    
    # Extract angles (Column 0: Roll, Column 1: Pitch, Column 2: Yaw)
    roll = rpy_deg[:, 0]
    pitch = rpy_deg[:, 1]
    yaw = rpy_deg[:, 2]
    
    # Stack columns into YPR format (Yaw, Pitch, Roll) for rotation
    ypr = np.column_stack((yaw, pitch, roll))
    
    # Create rotation matrices
    rotations = R.from_euler('ZYX', ypr, degrees=True)
    
    # Define global acceleration vector (gravity) in the world frame
    gravity = np.array([0, 0, 9.81])  # Gravity vector in m/s^2
    
    g_body = rotations.inv().apply(gravity)  # Transform gravity to the body frame
    
    # Calculate raw acceleration in the body frame
    raw_accel = -accel - g_body  # Subtract gravity from measured acceleration
    
    return raw_accel