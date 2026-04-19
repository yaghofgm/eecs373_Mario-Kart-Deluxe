#ifndef VROOM_H
#define VROOM_H

// Includes
#include<stdint.h>
#include "main.h"
#include "BNO055_STM32.h"

// Functions
void motor_a_set (int speed);
void motor_b_set (int speed);
void test_motor_set ();
void drive (int w, int speed);
void test_drive (void);
int32_t read_IMU ();
void test_IMU ();
int32_t read_adc(void);
void test_read_adc(void);
void test_adc_IMU(void);
void drive_controller ();

#endif
