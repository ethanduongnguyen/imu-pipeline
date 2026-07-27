from pathlib import Path
import csv
import numpy as np
from imu_utils import load_imu_dataset, GRAVITY

def calibrate_imu_data(input_csv: Path, output_csv: Path):
    # check for input file existence
    dataset = load_imu_dataset(input_csv)
    if dataset is None:
        print(f"Failed to load dataset from {input_csv}. Calibration aborted.")
        return
    
    means = np.mean(dataset.raw_data, axis=0)
    
    # Calculate offsets for accelerometer and gyroscope
    accel_x_offset = means[1]
    accel_y_offset = means[2]
    accel_z_offset = means[3] - GRAVITY
    
    gyro_x_offset = means[4]
    gyro_y_offset = means[5]
    gyro_z_offset = means[6]
    
    offsets = np.array([0, accel_x_offset, accel_y_offset, accel_z_offset, gyro_x_offset, gyro_y_offset, gyro_z_offset, 0])
    
    # Print calibrated offsets
    print(f"Calculated Offsets:")
    print(f"Accel X Offset: {accel_x_offset:.4f} m/s^2 | Accel Y Offset: {accel_y_offset:.4f} m/s^2 | Accel Z Offset: {accel_z_offset:.4f} m/s^2")
    print(f"Gyro X Offset: {gyro_x_offset:.4f} rad/s | Gyro Y Offset: {gyro_y_offset:.4f} rad/s | Gyro Z Offset: {gyro_z_offset:.4f} rad/s")
    
    calibrated_data = dataset.raw_data - offsets
    
    calibrated_data[:, 0] = dataset.raw_data[:, 0]  # Preserve timestamps
    calibrated_data[:, 7] = dataset.raw_data[:, 7]  # Preserve temperature
    
    # # Write calibrated data to output CSV file
    np.savetxt(output_csv, calibrated_data, delimiter=',', header=','.join(dataset.header), comments='', fmt='%.4f')
    print("Calibrated data saved to:", output_csv)
    
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    INPUT_FILE = BASE_DIR / "data" / "raw" / "20260726_234729_static002.csv"
    OUTPUT_FILE = BASE_DIR / "data" / "calibrated" / "20260726_234729_static002_calibrated.csv"

    calibrate_imu_data(INPUT_FILE, OUTPUT_FILE)