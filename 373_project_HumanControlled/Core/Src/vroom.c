#include "vroom.h"

//DRV8833 has IN1 as forward and IN2 as backward.
// IN1=PD15=CH4, IN2=PD14=CH3
//speed is -100 to 100
void motor_a_set (int speed){
	speed = speed > 100 ? 100 : (speed < -100 ? -100 : speed);
	if (speed > 0) {
	   //IN1, IN2 = 1,0; PC0, PC1
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_0, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_1, GPIO_PIN_RESET);
		//ENA = PWM , PF8 TIM5_CH3
		TIM5->CCR3 = speed;
	} else if (speed < 0) {
		 //IN1, IN2 = 0,1; PC0, PC1
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_0, GPIO_PIN_RESET);
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_1, GPIO_PIN_SET);
		//ENB = PWM , PF9 TIM5_CH3
		TIM5->CCR3 = -speed;
	} else {
		TIM5->CCR3 = 0;      // stop
	}
}
void motor_b_set (int speed){
	speed = speed > 100 ? 100 : (speed < -100 ? -100 : speed);
	if (speed > 0) {
	   //IN3, IN4 = 1,0; PC3, PC4
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_3, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_4, GPIO_PIN_RESET);
		//ENB = PWM , PF9 TIM5_CH4
		TIM5->CCR4 = speed;
	} else if (speed < 0) {
		 //IN1, IN2 = 0,1; PC0, PC1
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_3, GPIO_PIN_RESET);
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_4, GPIO_PIN_SET);
		//ENB = PWM , PF9 TIM5_CH4
		TIM5->CCR4 = -speed;
	} else {
		TIM5->CCR4 = 0;      // stop
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_3, GPIO_PIN_SET);
		HAL_GPIO_WritePin(GPIOC, GPIO_PIN_4, GPIO_PIN_SET);
	}
}
void test_motor_set (){
	motor_a_set(10);
	HAL_Delay(2000);
	motor_a_set(100);
	HAL_Delay(4000);
	motor_a_set(-50);
	HAL_Delay(2000);
	motor_a_set(-100);
	HAL_Delay(2000);
	motor_a_set(0);
	HAL_Delay(8000);

	motor_b_set(10);
	HAL_Delay(2000);
	motor_b_set(100);
	HAL_Delay(4000);
	motor_b_set(-50);
	HAL_Delay(2000);
	motor_b_set(-100);
	HAL_Delay(2000);
	motor_b_set(0);
	HAL_Delay(2000);

}
static float robot_width=0.1; //10cm
//w is rad per sec, w=0 straight, w>0 is go to left, and w<0 is go to right
//speed is -100 to 100.
void drive (int w, int speed){
	motor_a_set(speed-w*robot_width);
	motor_b_set(speed+w*robot_width);
}
void test_drive (void){
	drive(0, 20);
	HAL_Delay(500);
	drive(200, 0);
	HAL_Delay(500);
}
int32_t read_IMU (){
	static BNO055_Sensors_t sensors = {0};
	static BNO055_Sensors_t sensors_old = {0};
	ReadData(&sensors, SENSOR_EULER | SENSOR_LINACC);
	if (sensors.Euler.Z > sensors_old.Euler.Z + 100) sensors.Euler.Z = sensors_old.Euler.Z;
	sensors_old=sensors;
	return (int32_t)sensors.Euler.Z;
}
void test_IMU (){
	  printf("pitch: %ld deg\n", read_IMU());
}
extern ADC_HandleTypeDef hadc1;
// Returns -4 to 27 based on scaled down and offset Raw 12-bit ADC value (0–4095) from PB0 / ADC1_IN15
int32_t read_adc(void) {
    HAL_ADC_Start(&hadc1);
    HAL_ADC_PollForConversion(&hadc1, HAL_MAX_DELAY);
    return (int32_t)(2750-HAL_ADC_GetValue(&hadc1))/100;
}
void test_read_adc(void){
	printf("joystick data: %ld\n", read_adc() );
}
void test_adc_IMU(void){
	printf("pitch: %ld deg, joystick data: %ld\n", read_IMU(), read_adc());
}
void drive_controller (){
	int32_t speed = read_adc()*4;
	int32_t w_speed = read_IMU()*4;
	drive(w_speed,speed);
	printf("speed: %ld , ang_speed: %ld\n", speed, w_speed);
//	HAL_Delay(500);
}
