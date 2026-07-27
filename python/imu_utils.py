from pathlib import Path
import numpy as np

GRAVITY = 9.80665  # m/s²

class IMUDataset:
    def __init__(self, file_path: Path, header: list[str], time: np.ndarray, 
                accel: np.ndarray, gyro: np.ndarray, raw_data: np.ndarray):
        self.file_path = file_path
        self.header = header
        self.time = time # Normalized time in seconds (starts at 0)
        self.accel = accel # Shape: (N, 3) for X, Y, Z accelerometer data
        self.gyro = gyro # Shape: (N, 3) for X, Y, Z gyroscope data
        self.raw_data = raw_data
    
def load_imu_dataset(file_path: Path) -> IMUDataset | None:
    csv_path = Path(file_path)
    if not csv_path.exists():
        print(f"File not found: {csv_path}")
        return None
    
    with csv_path.open(mode='r', encoding='utf-8') as file:
        header_str = file.readline().strip()
        header = header_str.split(',') if header_str else []
        
    try:
        data = np.genfromtxt(csv_path, delimiter=',', skip_header=1)
    
    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return None
    
    if data.size == 0 or len(data.shape) != 2 or data.shape[1] < 7:
        print(f"Invalid or insufficient data in {csv_path}. Expected at least 7 columns.")
        return None
    
    time_seconds = (data[:, 0] - data[0, 0]) / 1e6  # Convert microseconds to seconds
    accel_data = data[:, 1:4]  # Columns for accelerometer data (X, Y, Z)
    gyro_data = data[:, 4:7]   # Columns for gyroscope data (X, Y, Z)
    
    return IMUDataset(
        file_path=csv_path,
        header=header,
        time=time_seconds,
        accel=accel_data,
        gyro=gyro_data,
        raw_data=data
    )