#include <Adafruit_Sensor.h>
#include <Adafruit_MPU6050.h>
#include <Wire.h>

Adafruit_MPU6050 mpu;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  while(!Serial){
    delay(10);
  }
  Wire.begin(21, 22);

  Serial.print("Initiliazing MPU6050...");

  if (!mpu.begin()){
    Serial.print("Failed to find MPU6050 chip.");
    while(1){
      delay(10);
    }
  }
  Serial.println(" MPU6050 found!");
  
  // Sensor Range Configurations

  // Set Acceleration Range: +/- 2G, 4G, 8G, or 16G
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);

  // Set Gyroscope Range: +/- 250, 500, 1000, or 2000 deg/s
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);

  // Sensor reading heading
  Serial.println("Time (us), Accel X (m/s^2), Accel Y (m/s^2), Accel Z (m/s^2), Gyro X (rad/s), Gyro Y (rad/s), Gyro Z (rad/s), Temperature (C)");
  
  delay(100);
}

void readIMU() {
  sensors_event_t a,g, temp;
  mpu.getEvent(&a, &g, &temp);

  unsigned long timestamp = micros();
  Serial.print(timestamp); Serial.print(",");
  Serial.print(a.acceleration.x); Serial.print(",");
  Serial.print(a.acceleration.y); Serial.print(",");
  Serial.print(a.acceleration.z); Serial.print(",");
  Serial.print(g.gyro.x); Serial.print(",");
  Serial.print(g.gyro.y); Serial.print(",");
  Serial.print(g.gyro.z); Serial.print(",");
  Serial.println(temp.temperature);

  delay(20);
}

void loop() {
  // put your main code here, to run repeatedly:
  readIMU();
}