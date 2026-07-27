import serial
import csv
import time
import datetime
from pathlib import Path

def serial_data_logger():
    # Update these to match ESP32 connection
    PORT = 'COM4'
    BAUD_RATE = 115200
    TARGET_SAMPLE_COUNT = 2000

    project_root = Path(__file__).resolve().parent.parent
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

    # Define the experiment name and timestamp for the output file
    experiment_name = "static002"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    FILE_NAME = raw_data_dir / f"{timestamp}_{experiment_name}.csv"

    # Close serial monitor in Arduino IDE before running this script
    ser = serial.Serial(PORT, BAUD_RATE, timeout = 1)

    # Reset ESP32 by toggling DTR
    ser.dtr = False # triggers EN/RST pin on ESP32
    time.sleep(0.1)
    ser.dtr = True
    time.sleep(2)  # Wait for the serial connection to initialize

    ser.reset_input_buffer()

    with open(FILE_NAME, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        writer.writerow(["Time (us)", "AccelX (m/s^2)", "AccelY (m/s^2)", "AccelZ (m/s^2)", "GyroX (rad/s)", "GyroY (rad/s)", "GyroZ (rad/s)", "Temp (C)"])
        
        samples_collected = 0
        collecting = True
        
        while collecting:
            raw_line = ser.readline().decode('utf-8', errors = 'ignore').strip()
            
            if not raw_line:
                continue  # Skip empty lines
                
            parts = raw_line.split(',')
            if raw_line.startswith("Time") and len(parts) == 8:  # Header row
                writer.writerow(parts)  # Write header row
                print(f"Header: {parts}")
                continue
                
            elif len(parts) == 8:  # Expecting 8 values: Time, AccelX, AccelY, AccelZ, GyroX, GyroY, GyroZ, Temp
                try:
                    row_data = [float(value) for value in parts]
                    
                    writer.writerow(row_data)
                    samples_collected += 1
                    print(f"Sample {samples_collected}/{TARGET_SAMPLE_COUNT}: {row_data}")
                    
                    if samples_collected >= TARGET_SAMPLE_COUNT:
                        collecting = False  # Stop collecting after reaching target
                    
                except ValueError:
                    print(f"Invalid data format: {raw_line}")
                    pass

    ser.close()
    print(f"Data collection complete. {samples_collected} samples saved to {FILE_NAME}.")

if __name__ == "__main__":
    serial_data_logger()