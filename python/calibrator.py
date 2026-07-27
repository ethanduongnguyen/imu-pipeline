from pathlib import Path
import csv
import numpy as np

INPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "raw" / "20260725_221826_calibration.csv"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "data" / "calibrated" / "20260725_221826_calibration_calibrated.csv"
gravity = 9.80665

def calibrate_imu_data(input_file, output_file):
    # check for input file existence
    if not input_file.exists():
        print(f"Input file {input_file} does not exist.")
        return
    
    # read input CSV file and section column data into lists
    with open(input_file, mode='r') as file:
        
        # read header
        header_str = file.readline().strip()
        header = header_str.split(',')  
        
    try:
        IMU_data = np.loadtxt(input_file, delimiter=',', skiprows=1)
    
    except Exception as e:
        print(f"Error reading input file: {e}")
        return
    
    if IMU_data.size == 0:
        print("No data found in the input file.")
        return
    
    total_samples = IMU_data.shape[0]
    
    means = np.mean(IMU_data, axis=0)
    
    # Calculate offsets for accelerometer and gyroscope
    accel_x_offset = means[1]
    accel_y_offset = means[2]
    accel_z_offset = means[3] - gravity
    
    gyro_x_offset = means[4]
    gyro_y_offset = means[5]
    gyro_z_offset = means[6]
    
    offsets = np.array([0, accel_x_offset, accel_y_offset, accel_z_offset, gyro_x_offset, gyro_y_offset, gyro_z_offset, 0])
    
    # Print calibrated offsets
    print(f"Calculated Offsets:")
    print(f"Accel X Offset: {accel_x_offset:.4f} m/s^2 | Accel Y Offset: {accel_y_offset:.4f} m/s^2 | Accel Z Offset: {accel_z_offset:.4f} m/s^2")
    print(f"Gyro X Offset: {gyro_x_offset:.4f} rad/s | Gyro Y Offset: {gyro_y_offset:.4f} rad/s | Gyro Z Offset: {gyro_z_offset:.4f} rad/s")
    
    calibrated_data = IMU_data - offsets
    
    calibrated_data[:, 0] = IMU_data[:, 0]  # Preserve timestamps
    calibrated_data[:, 7] = IMU_data[:, 7]  # Preserve temperature
    
    # # Write calibrated data to output CSV file
    np.savetxt(output_file, calibrated_data, delimiter=',', header=','.join(header), comments='', fmt='%.4f')
    print("Calibrated data saved to:", output_file)
    
if __name__ == "__main__":
    calibrate_imu_data(INPUT_FILE, OUTPUT_FILE)