import numpy as np
import scipy.io as sio
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional
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


def load_nuc_csv(nuc_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Parses the new NUC CSV format.
    Extracts the 27 IMU channels, 3 Vicon sync channels, and ONNX activity predictions.
    """
    df_nuc = pd.read_csv(nuc_path)
    trial_imu = df_nuc.loc[:, 'imu_0':'imu_26'].ffill().bfill().to_numpy(dtype=float)
    trial_vicon_from_imu = df_nuc.loc[:, 'vicon_0':'vicon_2'].ffill().bfill().to_numpy(dtype=float)
    
    if 'activity_pred' in df_nuc.columns:
        nuc_predictions = df_nuc['activity_pred'].ffill().bfill().to_numpy(dtype=float)
    else:
        nuc_predictions = None
        
    return trial_imu, trial_vicon_from_imu, nuc_predictions


def process_trial(filename_base: str, trial_subfolder: str, calib_file: str = 'calibrate.mat') -> Tuple[np.ndarray, np.ndarray, np.ndarray, Tuple[np.ndarray, np.ndarray], np.ndarray, np.ndarray, Optional[np.ndarray]]:
    """
    Loads raw IMU/NUC and Vicon data, applies calibration, synchronizes timestamps, 
    and calculates raw acceleration. Auto-detects between _NUC.csv and .txt formats.
    """
    BASE_DIR = Path(__file__).resolve().parent.parent
    TARGET_DIR = BASE_DIR / 'data' / 'raw' / trial_subfolder
    
    nuc_path = TARGET_DIR / f"{filename_base}_NUC.csv"
    txt_path = TARGET_DIR / f"{filename_base}.txt"
    calib_path = BASE_DIR / 'data' / 'raw' / trial_subfolder / calib_file
    
    # Split Vicon CSV
    df_joints, df_trajectories = split_vicon_csv(filename_base, trial_subfolder)
    
    # --- AUTO-DETECT FILE FORMAT ---
    if nuc_path.exists():
        print(f"Found NUC file. Loading data from {nuc_path.name}...")
        trial_imu, trial_vicon_from_imu, nuc_predictions = load_nuc_csv(nuc_path)
        
    elif txt_path.exists():
        print(f"NUC file not found. Falling back to legacy {txt_path.name}...")
        # Use your custom NaN-padding function here
        trial_imu_raw = load_imu_txt(txt_path) 
        
        # Extract the same exact array blocks so downstream code works seamlessly
        trial_vicon_from_imu = trial_imu_raw[:, 2:5]
        trial_imu = trial_imu_raw[:, 50:77] # Slices out the 27 IMU columns
        nuc_predictions = None
        
    else:
        raise FileNotFoundError(f"Neither {nuc_path.name} nor {txt_path.name} could be found in {TARGET_DIR}.")
    # -------------------------------
    
    trial_vicon_trajectories = df_trajectories.to_numpy(dtype=float)
    
    # Load MATLAB calibration file
    calib_data = sio.loadmat(calib_path, struct_as_record=False, squeeze_me=True)
    r_cal = calib_data['R_cal']
    
    idx = np.where(trial_vicon_trajectories[:, 0] == 1)[0]
    trial_vicon_all = trial_vicon_trajectories[idx[0]:, :]
    trial_vicon = trial_vicon_all[:, 2:]
    
    trial_vicon_joints_raw = df_joints.to_numpy(dtype=float)
    idx_joints = np.where(trial_vicon_joints_raw[:, 0] == 1)[0]
    trial_vicon_joints = trial_vicon_joints_raw[idx_joints[0]:, 2:]
    
    # Time synchronization
    ratio, ratio_round, id_vicon, id_imu = matchIMUandVicon(trial_vicon_from_imu, trial_vicon[:, 0:3])
    m, b = ratio[0], ratio[1]
    alignment_ids = (id_vicon, id_imu)
    
    # Create time arrays
    fs_v = 100.0 # Vicon sampling frequency
    n_v = trial_vicon.shape[0]
    n_i = trial_imu.shape[0]
    
    t_vicon = np.arange(1, n_v + 1) / fs_v
    idx_imu = np.arange(1, n_i + 1)
    t_imu_as_vicon = ((idx_imu - b) / m) / fs_v
    
    mask = (t_imu_as_vicon >= t_vicon[0]) & (t_imu_as_vicon <= t_vicon[-1])
    
    # Calculate Knee Angular Velocity
    fc = 5.0 
    b_butter, a_butter = butter(2, fc / (fs_v / 2.0), btype='low')
    
    knee_L_raw = trial_vicon_joints[:, 0]
    knee_R_raw = trial_vicon_joints[:, 5]
    
    knee_L_clean = pd.Series(knee_L_raw).interpolate(method='linear').ffill().bfill().to_numpy()
    knee_R_clean = pd.Series(knee_R_raw).interpolate(method='linear').ffill().bfill().to_numpy()
    
    knee_L_filt = filtfilt(b_butter, a_butter, knee_L_clean)
    knee_R_filt = filtfilt(b_butter, a_butter, knee_R_clean)
    
    knee_vel_L = np.gradient(knee_L_filt) * fs_v
    knee_vel_R = np.gradient(knee_R_filt) * fs_v
    vicon_knee_vel = np.column_stack([knee_vel_L, knee_vel_R])
    
    # Process IMU Data (Safely processes the standardized 27-column trial_imu block)
    imu_dict = {}
    sensor_names = ['Torso', 'Leftshank', 'Rightshank']
    
    for i, name in enumerate(sensor_names):
        start_col = i * 9
        end_col = start_col + 9
        
        sensor_data = trial_imu[mask, start_col:end_col]
        
        omega = sensor_data[:, 0:3] 
        accel = sensor_data[:, 3:6] * 9.81
        rpy = sensor_data[:, 6:9]
        
        acc_raw = calculate_raw_accel(rpy, accel)
        
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
    
    t_imu_masked = t_imu_as_vicon[mask]
    nuc_predictions_masked = nuc_predictions[mask] if nuc_predictions is not None else None
    
    print(f"Processed trial data for {filename_base}. Output shape: {data_imu.shape}")
    
    return data_imu, trial_vicon_joints, vicon_knee_vel, alignment_ids, t_imu_masked, t_vicon, nuc_predictions_masked

if __name__ == "__main__":
    processed_data = process_trial(
        filename_base='Activity_detect',
        trial_subfolder='0817_data'
    )