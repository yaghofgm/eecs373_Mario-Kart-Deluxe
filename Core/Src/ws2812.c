#include "ws2812.h"
#include <string.h>

static TIM_HandleTypeDef *_htim;
static uint32_t dma_buf[DMA_BUF_SIZE];

void ws2812_init(TIM_HandleTypeDef *htim) {
    _htim = htim;
    // Start with all LEDs off
    memset(dma_buf, 0, sizeof(dma_buf));
}

// [G7 G6 G5 G4 G3 G2 G1 G0 | R7 R6 R5 R4 R3 R2 R1 R0 | B7 B6 B5 B4 B3 B2 B1 B0] 24 bits, 8 bits per color

void ws2812_set_pixel(uint8_t index, uint8_t r, uint8_t g, uint8_t b) {
    if (index >= NUM_LEDS) return;

    uint8_t colors[3] = {g, r, b};  // GRB order!
    uint32_t *p = &dma_buf[index * 24]; //get to the dma position of the current led. do the g, then r, then b

    for (int c = 0; c < 3; c++) {
        for (int bit = 7; bit >= 0; bit--) {
            *p++ = (colors[c] & (1 << bit)) ? T1H : T0H; //smart, increase p, decrease the bit.
        }
    }
}

void ws2812_show(void) {
    // Reset pulses at the end — CCR=0 means line stays low
    memset(&dma_buf[NUM_LEDS * 24], 0, RESET_PULSES * sizeof(uint32_t));

    HAL_TIM_PWM_Start_DMA( //?????
        _htim,
        TIM_CHANNEL_3,
        (uint32_t*)dma_buf,
        DMA_BUF_SIZE
    );
}
