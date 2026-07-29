from pathlib import Path
from dataset import load_imu_dataset
from calibration import loadOffsets, applyOffsets
from filters import ExponentialMovingAverage, MovingAverage

def run_processing_pipeline():
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Define file paths
    RAW_DATA_FILE = BASE_DIR / "data" / "raw" / ""
    OFFSETS_FILE = BASE_DIR / "data" / "calibration" / "sensor_offsets.json"
    PROCESSED_FILE = BASE_DIR / "data" / "processed" / ""
    
    # Load raw dataset
    print(f"Loading raw dataset from {RAW_DATA_FILE.name}")
    dataset = load_imu_dataset(RAW_DATA_FILE)
    if dataset is None:
        print(f"Could not find raw data file: {RAW_DATA_FILE}")
        return
    
    # Apply offset calibration to dataset
    print("Applying calibration...")
    offsets = loadOffsets(OFFSETS_FILE)
    if offsets is None:
        print("Aborting pipeline: Offsets missing.")
        return
    applyOffsets(dataset, offsets)
    
    # Apply filters
    print("Applying Exponential Moving Average filter...")
    ema_filter = ExponentialMovingAverage(alpha = 0.85)
    
    dataset.accel = ema_filter.apply(dataset.accel)
    
    ema_filter.reset()
    dataset.gyro = ema_filter.apply(dataset.gyro)
    
    dataset.saveDataset(PROCESSED_FILE)
    
if __name__ == '__main__':
    run_processing_pipeline()