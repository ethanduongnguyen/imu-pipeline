from pathlib import Path
import json
import numpy as np
from dataset import load_imu_dataset, GRAVITY, IMUDataset

def computeOffsets(dataset: IMUDataset) -> dict:
    # Computes IMU offsets assuming a static trial with Z pointing up (acceleration in m/s^2 and gyroscope in rad/s)
    means = np.mean(dataset.raw_data, axis = 0)
    
    offsets = {
        "accel_x": float(means[1]),
        "accel_y": float(means[2]),
        "accel_z": float(means[3] - GRAVITY),
        "gyro_x": float(means[4]),
        "gyro_y": float(means[5]),
        "gyro_z": float(means[6])
    }
    return offsets

def saveOffsets(offsets: dict, output_json: Path):
    # Saves calculated offsets to a JSON file
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w', encoding='utf-8') as file:
        json.dump(offsets, file, indent=4)
    print(f"Offsets successfully saved to: {output_json}")
    
def loadOffsets(input_json: Path) -> dict:
    # Loads calibration offsets from JSON file
    if not input_json.exists:
        print(f"Calibration file not found: {input_json}")
        return None
    
    with open(input_json, 'r', encoding='utf-8') as file:
        offsets = json.load(file)
    return offsets

def applyOffsets(dataset: IMUDataset, offsets: dict):
    # Applies offsets to dataset
    offset_array = np.array([
        0, 
        offsets["accel_x"],  offsets["accel_y"],  offsets["accel_z"],
        offsets["gyro_x"], offsets["gyro_y"], offsets["gyro_z"],
        0
    ])
    
    dataset.raw_data -= offset_array
    
    # Update sliced values
    dataset.accel = dataset.raw_data[:, 1:4]
    dataset.gyro = dataset.raw_data[:, 4:7]
    print("Calibration offsets applied successfully.")
    
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    STATIC_FILE = BASE_DIR / "data" / "raw" / "20260726_234729_static002.csv"
    OFFSETS_FILE = BASE_DIR / "data" / "calibrated" / "sensor_offsets.json"

    static_dataset = load_imu_dataset(STATIC_FILE)
    if static_dataset:
        calculated_offsets = computeOffsets(static_dataset)
        saveOffsets(calculated_offsets, OFFSETS_FILE)