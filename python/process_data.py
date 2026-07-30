from pathlib import Path
from dataset import load_imu_dataset
from calibration import loadOffsets, applyOffsets
from filters import ExponentialMovingAverage, MovingAverage, ZeroPhaseButterworth

def run_processing_pipeline():
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    # Define file paths
    RAW_DATA_FILE = BASE_DIR / "data" / "raw" / "20260729_190825_dynamic001.csv"
    OFFSETS_FILE = BASE_DIR / "data" / "calibration" / "sensor_offsets.json"
    PROCESSED_FILE = BASE_DIR / "data" / "processed" / "20260729_190825_dynamic001_processed_3.csv"
    
    # Load raw dataset
    print(f"Loading raw dataset from {RAW_DATA_FILE.name}")
    dataset = load_imu_dataset(RAW_DATA_FILE)
    if dataset is None:
        print(f"Could not find raw data file: {RAW_DATA_FILE}")
        return
    
    # Calculate sampling rate
    fs = dataset.sampling_rate
    print(f"Detected sampling rate: {fs:.2f} Hz")
    
    # Apply offset calibration to dataset
    print("Applying calibration...")
    offsets = loadOffsets(OFFSETS_FILE)
    if offsets is None:
        print("Aborting pipeline: Offsets missing.")
        return
    applyOffsets(dataset, offsets)
    
    # Apply filters. Select filter from filters.py script
    
    print("Applying filter...")
    MovingAverageFilter = MovingAverage(window_size = 5, num_channels=3)
    ExponentialMovingAverageFilter = ExponentialMovingAverage(alpha = 0.5)
    ButterworthFilter = ZeroPhaseButterworth(cutoff_freq = 10, sampling_rate = fs, order=4)
    
    dataset.accel = ButterworthFilter.apply(dataset.accel)
    # ExponentialMovingAverageFilter.reset()
    dataset.gyro = ButterworthFilter.apply(dataset.gyro)
    
    dataset.metadata["filtering"] = {
        "applied": True,
        "accel_filter" : ButterworthFilter.getMetadata(),
        "gyro_filter": ButterworthFilter.getMetadata()
    }
    
    dataset.saveDataset(PROCESSED_FILE)
    
if __name__ == '__main__':
    run_processing_pipeline()