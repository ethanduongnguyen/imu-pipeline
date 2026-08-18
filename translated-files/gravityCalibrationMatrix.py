import numpy as np
from scipy.spatial.transform import Rotation as R

def gravityCalibrationMatrix(g_ref: np.ndarray) -> np.ndarray:
    """
    Translates gravityCalibrationMatrix.m into Python
    Calculates a rotation matrix to align a reference gravity vector with the ideal negative z-axis 

    Parameters:
        g_ref (np.ndarray): Reference gravity vector in the body frame (3x1)

    Returns:
        R_cal: Rotation matrix of shape (3,3) representing the calibration rotation matrix
    """
    
    u = g_ref / np.linalg.norm(g_ref)  # Normalize the reference gravity vector
    
    v = np.array([0, 0, -1])  # Ideal gravity vector in the body frame (negative z-axis)
    
    k_cross = np.cross(u, v)  # Cross product to find the axis of rotation
    if np.linalg.norm(k_cross) < 1e-8:  # Check if u and v are aligned
        return np.eye(3)  # Return identity matrix if they are aligned
    
    rot, _ = R.align_vectors([v], [u])  # Align u to v using scipy's Rotation.align_vectors
    
    R_cal = rot.as_matrix()  # Convert the rotation to a matrix