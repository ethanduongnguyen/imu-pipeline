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

  Serial.print("Initiliazing MPU6050...");

  if (!mpu.begin()){
    Serial.print("Failed to find MPU6050 chip.");
    while(1){
      delay(10);
    }
  }
  Serial.print("MPU6050 found!");
  
  // Sensor Range Configurations

  // Set Acceleration Range: +/- 2G, 4G, 8G, or 16G
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);

  // Set Gyroscope Range: +/- 250, 500, 1000, or 2000 deg/s
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);

  delay(100);
}

void loop() {
  // put your main code here, to run repeatedly:
  sensors_event_t a,g, temp;
  mpu.getEvent(&a, &g, &temp);

  Serial.print("Accel X: "); Serial.print(a.acceleration.x);
  Serial.print(" | Accel Y: "); Serial.print(a.acceleration.y);
  Serial.print(" | Accel Z: "); Serial.println(a.acceleration.z);

  // Print Gyroscope Values (rad/s)
  Serial.print("Gyro X: "); Serial.print(g.gyro.x);
  Serial.print(" | Gyro Y: "); Serial.print(g.gyro.y);
  Serial.print(" | Gyro Z: "); Serial.println(g.gyro.z);         

  Serial.println("-----------------------------------------------");
  delay(100);
}