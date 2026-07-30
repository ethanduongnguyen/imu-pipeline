import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from dataset import load_imu_dataset, GRAVITY

def plot_sensor_axes(axis, time, sensor_data, title, y_label, is_accel = True):
    axis.plot(time, sensor_data[:, 0], label='X', color='r', alpha=0.8)
    axis.plot(time, sensor_data[:, 1], label='Y', color='g', alpha=0.8)
    axis.plot(time, sensor_data[:, 2], label='Z', color='b', alpha=0.8)
    
    # Reference lines for accelerometer data
    axis.axhline(0, color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
    if is_accel:
        axis.axhline(GRAVITY, color='orange', linestyle='--', linewidth=0.5, alpha=0.7, label=f'Gravity ({GRAVITY:.2f} m/s²)')
    
    axis.set_title(title, fontsize = 12, fontweight = 'bold')
    axis.set_ylabel(y_label)
    axis.grid(True, linestyle='--', alpha=0.5)
    axis.legend(loc='upper right', fontsize = 'small')

def plot_imu_datasets(*csv_files: Path, output_plot: Path = None, title: str = "IMU Data Visualization"):
    datasets = [load_imu_dataset(file) for file in csv_files]
    valid_datasets = [ds for ds in datasets if ds is not None]
    
    if not valid_datasets: 
        print("No valid CSV files provided for plotting.")
        return
    
    num_cols = len(valid_datasets)
    
    fig, axes = plt.subplots(
        nrows = 2,
        ncols = num_cols,
        figsize = (6 * num_cols, 10),
        sharex = True,
        squeeze = False
    )
    
    fig.suptitle(title, fontsize = 16, fontweight = 'bold')
    
    for col_idx, dataset in enumerate(valid_datasets):
        label = dataset.file_path.stem.replace('_', ' ').title()
        
        # Row 0: Accelerometer Data
        plot_sensor_axes(axes[0, col_idx],
                         dataset.time, 
                         dataset.accel,
                         f"Accelerometer Data\n{label}", 
                         "Acceleration (m/s²)", 
                         is_accel=True
                         )
        
        plot_sensor_axes(axes[1, col_idx],
                        dataset.time,
                        dataset.gyro,
                        f"Gyroscope Data\n{label}",
                        "Angular Velocity (rad/s)",
                        is_accel=False
                        )
        axes[1, col_idx].set_xlabel("Time (s)")
    
    plt.tight_layout()
    
    if output_plot:
        output_plot.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_plot, dpi=300, bbox_inches='tight')
        print(f"Plot saved successfully to: {output_plot.resolve()}")
        
    plt.show()
    
if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent.parent
    
    RAW_FILE = BASE_DIR / "data" / "raw" / "20260729_190825_dynamic001.csv"
    PROCESSED_FILE = BASE_DIR / "data" / "processed" / "20260729_190825_dynamic001_processed.csv"
    PROCESSED_FILE_2 = BASE_DIR / "data" / "processed" / "20260729_190825_dynamic001_processed_2.csv"
    
    plot_imu_datasets(
        RAW_FILE,
        PROCESSED_FILE,
        PROCESSED_FILE_2,
        output_plot = BASE_DIR / "data" / "plots" / "imu_data_comparison_dynamic001.png",
        title = "IMU Data Comparison: Raw vs Processed"
        )