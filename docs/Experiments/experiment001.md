# **Experiment 001**

## Date

July 24, 2026

## Objective

Verify communication between ESP32 microcontroller and MPU6050 inertial measurement unit (IMU), and collect initial accelerometer and gyroscope readings

## Hardware

- ESP32 development board
- MPU6050
- Breadboard
- Jumper wires
- Arduino IDE
- Adafruit MPU6050 library

## Software Configuration

- Acceleromoter Range: +/- 8G
- Gyroscope Range: +/- 500 degrees/s
- Serial Communication Baud Rate: 115200
- Sampling Inteval: approximately 100 ms (~10 Hz)

## Procedure

1. Connected the MPU6050 to ESP32 using I2C communication.
2. Initialized MPU6050 using Adafruit MPU6050 Arduino library.
3. Configured accelerometer and gyroscope ranges.
4. Read acceleration and angular velocity data through ESP32 serial monitor.
5. Observed sensor output while the IMU remained flat and stationary.

## Results

The MPU6050 successfully initialized and streamed sensor data. 

Example stationary measurements:

Accelerometer: 

- X: ~1.6 m/s^2
- Y: ~-0.2 m/s^2
- Z: ~9.1 m/s^2

Gyroscope:

- X: ~-0.04 rad/s
- Y: ~0.03 rad/s
- Z: ~-0.01 rad/s

## Observations

The accelerometer readings did not align perfectly with the expected stationary values of:

- X: 0 m/s^2
- Y: 0 m/s^2
- Z: 9.81 m/s^2

This was expected, as the MPU6050 was slightly tilted during the soldering process. This caused gravity to be distributed across multiple axes. The gyroscope readings remained close to while stationary, indicating that the sensor was functioning correctly. 

## Conclusions

The MPU6050 and ESP32 are communicating successfully. The next step is the convert the serial output into timestamped CSV data for automated data collection and analysis. 

## Future Work

- Add microsecond timestamps to each IMU sample
- Output data in CSV format
- Create a Python serial logger
- Calibrate accelerometer and gyroscope
- Visualize IMU data using Python plotting tools