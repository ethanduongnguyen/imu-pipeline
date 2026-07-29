import serial
import csv
import time
import datetime
from pathlib import Path

def serial_data_logger():
    # Update these to match ESP32 connection
    PORT = 'COM4'
    BAUD_RATE = 115200

    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

    # Define the experiment name and timestamp for the output file
    experiment_name = "dynamic001"
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    FILE_NAME = RAW_DATA_DIR / f"{timestamp}_{experiment_name}.csv"

    # Close serial monitor in Arduino IDE before running this script
    ser = serial.Serial(PORT, BAUD_RATE, timeout = 1)

    # Reset ESP32 by toggling DTR
    ser.dtr = False # triggers EN/RST pin on ESP32
    time.sleep(0.1)
    ser.dtr = True
    time.sleep(2)  # Wait for the serial connection to initialize

    ser.reset_input_buffer()
    
    samples_collected = 0

    try:
        with open(FILE_NAME, mode='w', newline='') as file:
            writer = csv.writer(file)
            
            writer.writerow(["Time (us)", "AccelX (m/s^2)", "AccelY (m/s^2)", "AccelZ (m/s^2)", "GyroX (rad/s)", "GyroY (rad/s)", "GyroZ (rad/s)", "Temp (C)"])
            
            print(f"Logging data to {FILE_NAME.name}...")
            print(f"Press CTRL+C to stop data collection")
            
            while True:
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
                        
                    except ValueError:
                        print(f"Invalid data format: {raw_line}")
                        pass
                
    except KeyboardInterrupt:
        print("Stopping data collection...")
              
    finally:          
        ser.close()
        print(f"Data collection complete. {samples_collected} samples saved to {FILE_NAME}.")

if __name__ == "__main__":
    serial_data_logger()