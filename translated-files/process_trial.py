import numpy as np
import scipy.io as sio
import pandas as pd
from pathlib import Path
from typing import Tuple
from scipy.signal import butter, filtfilt
from calculate_raw_accel import calculate_raw_accel
from matchIMUandVicon import matchIMUandVicon
from split_vicon_csv import split_vicon_csv

def load_imu_txt(txt_path: Path) -> np.ndarray:
    """
    Loads the raw IMU txt and mimics the way that MATLAB does it -- finds the widest row and pads all shorter rows with NaN (Not a Number)
    """
    
    with open(txt_path, 'r') as f:
        lines = f.readlines()

    rows = [line.strip().split(',') for line in lines if line.strip() != '']
    if not rows:
        raise ValueError(f"No data found in {txt_path}")

    max_width = max(len(row) for row in rows)
    data = np.full((len(rows), max_width), np.nan)

    for i, row in enumerate(rows):
        for j, val in enumerate(row):
            try:
                data[i, j] = float(val)
            except ValueError:
                data[i, j] = np.nan  # e.g. the leading 'frame\tfrequency\tVicon\tIMU0' text token

    return data

def process_trial(filename_base: str, trial_subfolder: str, calib_file: str = 'calibrate.mat') -> Tuple[np.ndarray, np.ndarray, np.ndarray, Tuple[np.ndarray, np.ndarray], np.ndarray, np.ndarray]:
    """
    Translates processTrial.m into Python
    Loads raw IMU and Vicon data, applies calibration, synchronizes timestamps, and calculates raw acceleration and knee angular velocities
    Returns a unified IMU feature array

    Parameters:
        filename_base (str): Base filename for the trial data (without extension)
        calib_file (str): Filename for the calibration data (default is 'calibration.mat') 
    """
    BASE_DIR  = Path(__file__).resolve().parent.parent
    TARGET_DIR = BASE_DIR / 'data' /'raw' / trial_subfolder
    
    print(f"Processing trial data for {filename_base} from {TARGET_DIR.resolve()}")
    
    txt_path = TARGET_DIR / f"{filename_base}.txt"
    calib_path = BASE_DIR / 'data' / 'raw' / trial_subfolder / calib_file
    
    # Split Vicon CSV into two tables, by default it searches for a second table header called 'Trajectories'
    df_joints, df_trajectories = split_vicon_csv(filename_base, trial_subfolder)
    
    # Load the data from IMU and Vicon
    trial_imu = load_imu_txt(txt_path)
    trial_vicon_trajectories = df_trajectories.to_numpy(dtype=float)
    
    
    # Load MATLAB calibration file
    calib_data = sio.loadmat(calib_path, struct_as_record=False, squeeze_me=True)
    r_cal = calib_data['R_cal']
    
    if trial_imu is None or trial_vicon_trajectories is None or calib_data is None:
        raise ValueError("One or more data files could not be loaded. Please check the file paths and formats.")
    
    trial_vicon_from_imu = trial_imu[:, 2:50]
    
    idx = np.where(trial_vicon_trajectories[:, 0] == 1)[0]
    trial_vicon_all = trial_vicon_trajectories[idx[0]:, :]
    trial_vicon = trial_vicon_all[:, 2:]
    
    trial_vicon_joints_raw = df_joints.to_numpy(dtype=float)
    idx_joints = np.where(trial_vicon_joints_raw[:, 0] == 1)[0]
    trial_vicon_joints = trial_vicon_joints_raw[idx_joints[0]:,2:]
    
    # Time synchronization between IMU and Vicon
    ratio, ratio_round, id_vicon, id_imu = matchIMUandVicon(trial_vicon_from_imu[:, 0:3], trial_vicon[:, 0:3])
    m, b = ratio[0], ratio[1]
    alignment_ids = (id_vicon, id_imu)
    
    # Create time arrays
    fs_v = 100.0  # Vicon sampling frequency
    n_v = trial_vicon.shape[0]
    n_i = trial_imu.shape[0]
    
    t_vicon = np.arange(1, n_v + 1) / fs_v
    idx_imu = np.arange(1, n_i + 1)
    
    t_imu_as_vicon = ((idx_imu - b) / m) / fs_v
    
    # Create mask to trim IMU data to match Vicon time range
    mask = (t_imu_as_vicon >= t_vicon[0]) & (t_imu_as_vicon <= t_vicon[-1])
    # print(f"n_v = {n_v}")
    # print(f"n_i = {n_i}")
    # print(f"m = {m:.10f}, b = {b:.10f}")
    # print(f"mask.sum() = {mask.sum()}")
    # print(f"t_vicon[0] = {t_vicon[0]:.10f}, t_vicon[-1] = {t_vicon[-1]:.10f}")
    # print(f"first/last idx_imu in mask: {idx_imu[mask][0]} / {idx_imu[mask][-1]}")
    
    fc = 5 # Cutoff frequency
    b_butter, a_butter = butter(2, fc / (fs_v / 2.0), btype ='low')
    
    knee_L_raw = trial_vicon_joints[:, 0]
    knee_R_raw = trial_vicon_joints[:, 5]
    
    knee_L_clean = pd.Series(knee_L_raw).interpolate(method='linear').ffill().bfill().to_numpy()
    knee_R_clean = pd.Series(knee_R_raw).interpolate(method='linear').ffill().bfill().to_numpy()
    
    knee_L_filt = filtfilt(b_butter, a_butter, knee_L_clean)
    knee_R_filt = filtfilt(b_butter, a_butter, knee_R_clean)
    
    knee_vel_L = np.gradient(knee_L_filt) * fs_v
    knee_vel_R = np.gradient(knee_R_filt) * fs_v
    vicon_knee_vel = np.column_stack([knee_vel_L, knee_vel_R])
       
    # Extract and format IMU data (Torso, Left Shank, Right Shank)
    imu_dict = {}
    sensor_names = ['Torso', 'Leftshank', 'Rightshank']
    
    for i, name in enumerate(sensor_names):
        start_col = 50 + i*9
        end_col = start_col + 9
        
        # Apply mask immediately to trim length
        sensor_data = trial_imu[mask, start_col:end_col]
        
        omega = sensor_data[:, 0:3]  # Angular velocity
        accel = sensor_data[:, 3:6] * 9.81 # Linear acceleration
        rpy = sensor_data[:, 6:9]  # Roll, pitch, yaw in degrees
        
        # Calculate raw acceleration
        acc_raw = calculate_raw_accel(rpy, accel)
        
        # Apply calibration rotation matrix
        calib_matrix = getattr(r_cal, name)
        acc_raw_calibrated = acc_raw @ calib_matrix.T
        omega_calibrated = omega @ calib_matrix.T
        
        imu_dict[name] = {
            'acc_raw': acc_raw_calibrated,
            'omega': omega_calibrated,
            'rpy': rpy
        }
        
    data_imu = np.hstack([
        imu_dict['Torso']['acc_raw'], imu_dict['Torso']['omega'], imu_dict['Torso']['rpy'],
        imu_dict['Leftshank']['acc_raw'], imu_dict['Leftshank']['omega'], imu_dict['Leftshank']['rpy'], 
        imu_dict['Rightshank']['acc_raw'], imu_dict['Rightshank']['omega'], imu_dict['Rightshank']['rpy']
    ])
    
    print(f"Processed trial data for {filename_base}. Output shape: {data_imu.shape}")
    
    t_imu_masked = t_imu_as_vicon[mask]
    
    # np.savetxt("data_imu_python.csv", data_imu, delimiter=",", fmt="%.4f")
    
    return data_imu, trial_vicon_joints, vicon_knee_vel, alignment_ids, t_imu_masked, t_vicon

if __name__ == "__main__":
    processed_data = process_trial(
        filename_base='welding123',
        trial_subfolder='0727_Xinyan_data'
    )