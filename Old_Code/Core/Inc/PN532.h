#ifndef PN532_H
#define PN532_H

// Includes
#include "main.h"
#include "stdio.h"

// Address
#define PN532_Addr 0x48

// Constants - Frame
#define PN532_Preamble 0x00
#define PN532_Start_Code_1 0x00
#define PN532_Start_Code_2  0xFF
#define PN532_Postamble 0x00

// Constants - Sending
#define PN532_STM2PN 0xD4
#define PN532_PN2STM 0xD5

// Commands
#define PN532_CMD_SAM_Config 0x14
#define PN532_CMD_InListPassiveTarget 0x4A

// Functions
HAL_StatusTypeDef PN532_Init(I2C_HandleTypeDef *hi2c);
HAL_StatusTypeDef PN532_SAMConfig(void);
HAL_StatusTypeDef PN532_ReadPassiveTargetID(uint8_t *uid, uint8_t *uidLength);

#endif

