#include "PN532.h"

static I2C_HandleTypeDef *pn532_i2c;
static HAL_StatusTypeDef PN532_WaitReady(uint32_t timeout);
static HAL_StatusTypeDef PN532_WriteCommand(uint8_t *cmd, uint8_t cmdlen);
static HAL_StatusTypeDef PN532_ReadAck(void);
static HAL_StatusTypeDef PN532_ReadResponse(uint8_t *buf, uint8_t *outLen);

// Make sure device is ready
HAL_StatusTypeDef PN532_Init(I2C_HandleTypeDef *hi2c){
	pn532_i2c = hi2c;
	HAL_Delay(100);

	// Debug: confirm PN532 is visible on the I2C bus before doing anything
	if (HAL_I2C_IsDeviceReady(pn532_i2c, PN532_Addr, 3, 100) != HAL_OK){
		return HAL_ERROR;
	}

	return PN532_SAMConfig();
}

// Startup Config
HAL_StatusTypeDef PN532_SAMConfig(void){

	// Command
	uint8_t cmd[] = {
			PN532_CMD_SAM_Config,
			0x01,   // Normal mode
			0x14,   // Timeout 50ms * 20 = 1000ms
			0x01    // IRQ enabled
	};

	// Write Command
	if (PN532_WriteCommand(cmd, sizeof(cmd)) != HAL_OK){
		return HAL_ERROR;
	}

	// Check Acknowledge
	if (PN532_ReadAck() != HAL_OK){
		return HAL_ERROR;
	}

	// FIX: Must wait for PN532 to be ready before reading the response
	if (PN532_WaitReady(1000) != HAL_OK){
		return HAL_ERROR;
	}

	// Read Response
	uint8_t resp[16];
	uint8_t len;
	return PN532_ReadResponse(resp, &len);
}

// Read Tag
HAL_StatusTypeDef PN532_ReadPassiveTargetID(uint8_t *uid, uint8_t *uidLength){

	// Commands
	uint8_t cmd[] = {
			PN532_CMD_InListPassiveTarget,
			0x01,   // Max 1 target
			0x00    // 106 kbps ISO14443A
	};

	// Write Command
	if (PN532_WriteCommand(cmd, sizeof(cmd)) != HAL_OK){
		return HAL_ERROR;
	}

	// Check Acknowledge
	if (PN532_ReadAck() != HAL_OK){
		return HAL_ERROR;
	}

	// Wait Ready (Swapped from 3k)
	if (PN532_WaitReady(3000) != HAL_OK){
		return HAL_ERROR;
	}

	// Read Response
	uint8_t resp[64];
	uint8_t len = 0;
	if (PN532_ReadResponse(resp, &len) != HAL_OK){
		return HAL_ERROR;
	}

	// FIX: PN532_ReadResponse already strips the TFI (D5) byte, so:
	// resp[0] = 0x4B  (InListPassiveTarget response code)
	// resp[1] = nTargets
	// resp[2] = Tg (target number)
	// resp[3] = SENS_RES high
	// resp[4] = SENS_RES low
	// resp[5] = SEL_RES
	// resp[6] = NfcIdLength
	// resp[7..] = UID bytes

	// Check for response code (InListPassiveTarget)
	if (resp[0] != 0x4B){
		return HAL_ERROR;
	}

	// No targets found
	if (resp[1] == 0){
		return HAL_ERROR;
	}

	// Check response length
	*uidLength = resp[6];
	if (*uidLength == 0 || *uidLength > 10){
		return HAL_ERROR;
	}

	// Update UID
	for (uint8_t i = 0; i < *uidLength; i++){
		uid[i] = resp[7 + i];
	}

	// Done :)
	return HAL_OK;
}

// Wait Ready
static HAL_StatusTypeDef PN532_WaitReady(uint32_t timeout){

	uint32_t start = HAL_GetTick();
	uint8_t status = 0x00;

	// NEW
	//uint8_t cmd = 0x02;

	while ((HAL_GetTick() - start) < timeout){
		// NEW
		//if(HAL_I2C_Master_Transmit(pn532_i2c,PN532_Addr,&cmd,1,50)){
		//	continue;
		//}

		// A NACK here just means the PN532 is busy — keep polling
	     HAL_StatusTypeDef ret = HAL_I2C_Master_Receive(pn532_i2c, PN532_Addr, &status, 1, 50);
	     if (ret == HAL_OK && status == 0x01){
	    	 return HAL_OK;
	     }

	     // Slight Delay
	     HAL_Delay(10);
	 }

	return HAL_TIMEOUT;

}

// Write Command
static HAL_StatusTypeDef PN532_WriteCommand(uint8_t *cmd, uint8_t cmdlen){

	// Initialize Stuff
	uint8_t frame[64];
	uint8_t len = cmdlen + 1;           // Data length = cmd bytes + TFI
	uint8_t checksum = PN532_STM2PN;   // Checksum starts with TFI

	// Preamble
	frame[0] = PN532_Preamble;

	// Start Bytes
	frame[1] = PN532_Start_Code_1;
	frame[2] = PN532_Start_Code_2;

	// Length
	frame[3] = len;

	// LCS (Length Checksum)
	frame[4] = ~len + 1;

	// TFI (host --> PN532)
	frame[5] = PN532_STM2PN;

	// Data
	for (uint8_t i = 0; i < cmdlen; i++){
		frame[6 + i] = cmd[i];
		checksum += cmd[i];
	}

	// DCS (Data Checksum)
	frame[6 + cmdlen] = ~checksum + 1;

	// Postamble
	frame[7 + cmdlen] = PN532_Postamble;

	// Send
	return HAL_I2C_Master_Transmit(pn532_i2c,PN532_Addr,frame,8 + cmdlen,1000);
}

// Read Acknowledge
static HAL_StatusTypeDef PN532_ReadAck(void){

	// Temporary
	uint8_t tmp[7];

	// Wait for Ready
	if (PN532_WaitReady(1000) != HAL_OK){
		return HAL_TIMEOUT;
	}

	// Read
	if (HAL_I2C_Master_Receive(pn532_i2c, PN532_Addr, tmp, 7, 1000) != HAL_OK){
		return HAL_ERROR;
	}

	// tmp[0] = I2C status byte (must be 0x01 = ready)
	if (tmp[0] != 0x01){
		return HAL_ERROR;
	}

	// tmp[1..6] = ACK frame: 00 00 FF 00 FF 00
	uint8_t *ack = &tmp[1];
	if (	ack[0] == 0x00 && ack[1] == 0x00 && ack[2] == 0xFF &&
			ack[3] == 0x00 && ack[4] == 0xFF && ack[5] == 0x00){
		// Complete :)
		return HAL_OK;
	}

	// Done (ACK failed)
	return HAL_ERROR;
}

static HAL_StatusTypeDef PN532_ReadResponse(uint8_t *buf, uint8_t *outLen){

	// Temporary
	uint8_t tmp[64];

	// 1. Wait until PN532 is ready
	if (PN532_WaitReady(1000) != HAL_OK){
		return HAL_TIMEOUT;
	}

	// 2. Read full I2C frame (includes leading status byte)
	if (HAL_I2C_Master_Receive(pn532_i2c, PN532_Addr, tmp, sizeof(tmp), 1000) != HAL_OK){
		return HAL_ERROR;
	}

	// 3. Skip I2C status byte — frame starts at tmp[1]
	uint8_t *frame = &tmp[1];

	// 4. Validate preamble and start codes
	if (frame[0] != 0x00 || frame[1] != 0x00 || frame[2] != 0xFF){
		return HAL_ERROR;
	}

	// 5. Validate length checksum: LEN + LCS must equal 0x00
	uint8_t len = frame[3];
	uint8_t lcs = frame[4];
	if ((uint8_t)(len + lcs) != 0x00){
		return HAL_ERROR;
	}

	// 6. Validate TFI: must be D5 (PN532 -> host)
 	if (frame[5] != PN532_PN2STM){
 		return HAL_ERROR;
 	}

 	// 7. Data length = LEN - 1 (subtract TFI byte)
 	//    buf will NOT include the TFI byte — callers must account for this
 	uint8_t dataLen = len - 1;
 	*outLen = dataLen;

 	// 8. Copy payload into output buffer
 	for (uint8_t i = 0; i < dataLen; i++){
      buf[i] = frame[6 + i];
 	}
 	return HAL_OK;
}

