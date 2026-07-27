import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

GRAVITY  = 9.80665  # m/s²

def plot_sensor_axes(axis, time, data_x, data_y, data_z, title, y_label, is_accel = True):
    axis.plot(time, data_x, label='X', color='r', alpha=0.8)
    axis.plot(time, data_y, label='Y', color='g', alpha=0.8)
    axis.plot(time, data_z, label='Z', color='b', alpha=0.8)
    
    # Reference lines for accelerometer data
    axis.axhline(0, color='gray', linestyle='--', linewidth=0.5, alpha=0.7)
    if is_accel:
        axis.axhline(GRAVITY, color='orange', linestyle='--', linewidth=0.5, alpha=0.7, label=f'Gravity ({GRAVITY:.2f} m/s²)')
    
    axis.set_title(title, fontsize = 12, fontweight = 'bold')
    axis.set_ylabel(y_label)
    axis.grid(True, linestyle='--', alpha=0.5)
    axis.legend(loc='upper right', fontsize = 'small')

def plot_imu_datasets(*csv_files: Path, output_plot: Path = None, title: str = "IMU Data Visualization"):
    valid_files = [file for file in csv_files if file.exists()]
    
    if not valid_files: 
        print("No valid CSV files provided for plotting.")
        return
    
    num_datasets = len(valid_files)
    
    fig, axes = plt.subplots(
        nrows = 2,
        ncols = num_datasets,
        figsize = (6 * num_datasets, 10),
        sharex = True,
        squeeze = False
    )
    
    fig.suptitle(title, fontsize = 16, fontweight = 'bold')
    
    for col_idx, file_path in enumerate(valid_files):
        try:
            data = np.loadtxt(file_path, delimiter=',', skiprows=1)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
        
        if data.size == 0:
            print(f"No data found in {file_path}.")
            continue
        
        time = (data[:, 0] - data[0,0]) / 1e6  # Convert microseconds to seconds
        accel_x, accel_y, accel_z = data[:, 1], data[:, 2], data[:, 3]
        gyro_x, gyro_y, gyro_z = data[:, 4], data[:, 5], data[:, 6]
        
        file_label = file_path.stem.replace('_', ' ').title()
        
        plot_sensor_axes(axes[0, col_idx],
                         time, 
                         accel_x,
                         accel_y,
                         accel_z,
                         f"Accelerometer Data\n{file_label}", 
                         "Acceleration (m/s²)", 
                         is_accel=True
                         )
        
        plot_sensor_axes(axes[1, col_idx],
                        time,
                        gyro_x,
                        gyro_y,
                        gyro_z,
                        f"Gyroscope Data\n{file_label}",
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
    
    RAW_FILE = BASE_DIR / "data" / "raw" / "20260726_225143_static001.csv"
    CALIBRATED_FILE = BASE_DIR / "data" / "calibrated" / "20260726_225143_static001_calibrated.csv"
    
    plot_imu_datasets(
        RAW_FILE,
        CALIBRATED_FILE,
        output_plot = BASE_DIR / "data" / "plots" / "imu_data_comparison.png",
        title = "IMU Data Comparison: Raw vs Calibrated"
        )