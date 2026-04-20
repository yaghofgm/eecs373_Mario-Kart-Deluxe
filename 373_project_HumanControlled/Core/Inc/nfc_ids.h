#ifndef NFC_IDS_H
#define NFC_IDS_H

// Version 1: 4/16/26 @ 12:09 AM

// Includes
#include <stdint.h>
#include <stdbool.h>

// Functions
bool is_match(const uint8_t scanned[7], const uint8_t list[][7], int count);

int identify_tag_color(const uint8_t scanned[7], 
                       const uint8_t green[][7], int g_count,   // Pre-Finish Line (1)
                       const uint8_t yellow[][7], int y_count,  // Finish Line (2)
                       const uint8_t purple[][7], int p_count);   // Power-Ups (3)
                                                                // Other (0)

#endif
