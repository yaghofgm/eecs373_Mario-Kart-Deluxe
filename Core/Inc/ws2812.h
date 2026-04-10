#ifndef WS2812_H
#define WS2812_H

#include "stm32l4xx_hal.h"
#include <stdint.h>

#define NUM_LEDS     15          // change to your strip length
#define RESET_PULSES 60          // 60 × 1.25µs = 75µs > 50µs reset

#define T0H  6 //about 0.35 us, is 0.375 us
#define T1H  14 //about 0.937 us, is 0.937 us
//for the resets, it should be all zeros
//#define TRH 0

// Total DMA buffer: 24 bits per LED + reset
#define DMA_BUF_SIZE (NUM_LEDS * 24 + RESET_PULSES)

void ws2812_init(TIM_HandleTypeDef *htim);
void ws2812_set_pixel(uint8_t index, uint8_t r, uint8_t g, uint8_t b);
void ws2812_show(void);
void doStar(void);

#endif
