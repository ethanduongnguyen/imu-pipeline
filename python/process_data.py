from pathlib import Path
from dataset import load_imu_dataset
from calibration import loadOffsets, applyOffsets
from filters import ExponentialMovingAverage, MovingAverage

def run_processing_pipeline():
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Define file paths
    RAW_DATA_FILE = BASE_DIR / "data" / "raw" / "20260729_190825_dynamic001.csv"
    OFFSETS_FILE = BASE_DIR / "data" / "calibration" / "sensor_offsets.json"
    PROCESSED_FILE = BASE_DIR / "data" / "processed" / "20260729_190825_dynamic001_processed_2.csv"
    
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
    
    # Apply filters. Select filter from filters.py script
    
    # print("Applying Moving Average filter...")
    # MovingAverageFilter = MovingAverage(window_size= 5, num_channels = 3)
    
    # dataset.accel = MovingAverageFilter.apply(dataset.accel)
    
    # MovingAverageFilter.reset()
    # dataset.gyro = MovingAverageFilter.apply(dataset.gyro)
    
    # dataset.metadata["filtering"] = {
    #     "applied": True,
    #     "accel_filter": MovingAverageFilter.getMetadata(),
    #     "gyro_filter": MovingAverageFilter.getMetadata()
    # }
    
    print("Applying Expoential Moving Average filter...")
    ExponentialMovingAverageFilter = ExponentialMovingAverage(alpha = 0.5)
    
    dataset.accel = ExponentialMovingAverageFilter.apply(dataset.accel)
    ExponentialMovingAverageFilter.reset()
    dataset.gyro = ExponentialMovingAverageFilter.apply(dataset.gyro)
    
    dataset.metadata["filtering"] = {
        "applied": True,
        "accel_filter" : ExponentialMovingAverageFilter.getMetadata(),
        "gyro_filter": ExponentialMovingAverageFilter.getMetadata()
    }
    
    dataset.saveDataset(PROCESSED_FILE)
    
if __name__ == '__main__':
    run_processing_pipeline()