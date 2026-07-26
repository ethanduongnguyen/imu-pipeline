# Experiment 2

July 25, 2026

## Objective

Collect a sample of 2000 IMU readings and log it into a CSV file using Python

## Hardware

- ESP32
- MPU6050
- Arduino IDE
- Visual Studio Code

## Software 

See python / imu-logger.py

## Procedure

1. Connect ESP32 and IMU6050 to laptop using USB to establish serial connection.
2. Run imu-logger.py.

## Results

Successfully collected a sample size of 2000 IMU readings. The CSV file is accurate and includes proper headings for each column.

Example entries from CSV file:

Time (us),AccelX (m/s^2),AccelY (m/s^2),AccelZ (m/s^2),GyroX (rad/s),GyroY (rad/s),GyroZ (rad/s),Temp (C)
1871954.0,0.34,-0.02,9.35,-0.04,0.03,-0.01,27.64
1894953.0,0.22,0.03,9.23,-0.05,0.03,-0.01,27.78
1917954.0,0.3,-0.01,9.31,-0.04,0.02,-0.01,27.68
1940953.0,0.32,0.04,9.27,-0.04,0.03,-0.01,27.78
1963954.0,0.3,0.03,9.24,-0.04,0.03,-0.01,27.73
1986954.0,0.4,0.07,9.26,-0.04,0.03,-0.01,27.64
2009954.0,0.36,0.02,9.13,-0.04,0.03,-0.01,27.82

## Conclusion

The Python serial logger is successfully communicating with the ESP32. The next step is to calibrate the IMU using the data collected. We will also edit the Python logger script to collect at a user-determined interval, determined by a keyboard interruption. 

## Future Work

 - Calibrate accelerometer and gyroscope
 - Modify Python script to stop recording at a user-defined interval via keyboard interrupt
 - Visualize IMU data using Python plotting tools