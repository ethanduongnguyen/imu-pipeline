# Experiment 2

July 29, 2026

## Objective

Collect dynamic IMU readings and successfully run data through IMU pipeline

## Hardware

- ESP32
- MPU6050
- Arduino IDE
- Visual Studio Code

## Software 

- imu-logger.py
- filters.py
- calibration.py
- imu-plotter.py
- process_data.py
- dataset.py

## Procedure

1. Connect ESP32 and IMU6050 to laptop using USB to establish serial connection.
2. Run imu-logger.py.
3. Move IMU in random directions continuously. 
4. Stop collecting data.
5. Run collected raw data through IMU pipeline. 
6. Plot raw IMU data against data processed with a moving average filter and exponential moving average filter.

## Results

Successfully collected a dynamic sample of IMU readings. The CSV file is accurate and includes proper headings for each column. The data flows smoothly through the IMU pipeline, going through calibration, filtering, and plotting.

## Conclusion

The IMU pipeline is successful and efficient as of current progress. The plots demonstrate smoothing of both accelerometer and gyroscope readings, indicating that the filters are working as expected. 

## Future Work

 - Add a Butterworth filter to the filters script
 - Create new script for sensor fusion, utilzing a complementary filter, Madgwick filter, and extended Kalman filter