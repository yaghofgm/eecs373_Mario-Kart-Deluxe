#include "misc.h"
#include "PN532.h"

void do_nfc_and_strip (){
	static uint8_t uid[7] = {0};
	static uint8_t uidLen = 0;
	static uint8_t boost_on = 0;
	static int boost_max_time = 10000;
	static int boost_start_time = 0;
	static int boost_current_time = 0;

	if(PN532_ReadPassiveTargetID(uid, &uidLen) == HAL_OK){
		HAL_Delay(50);
		// Power-Up Trigger (UID: 0x4, 0x59, 0x45, 0x69, 0xBC, 0x2A, 0x81)
		// JC Note: Think that the UID for all of them is 0x2009ffec but the idv uid[i] are dif
//		if( (uid[0] == 0x4) && (uid[1] == 0x59) && (uid[2] == 0x45) && (uid[3] == 0x69) && (uid[4] == 0xBC) && (uid[5] == 0x2A) && (uid[6] == 0x81) ){
		if( (uid[0] == 0x4) && (uid[1] == 0xE8) && (uid[2] == 0xFA) && (uid[3] == 0x68) && (uid[4] == 0xBC) && (uid[5] == 0x2A) && (uid[6] == 0x81) ){
			boost_on = 1;
			boost_start_time = HAL_GetTick();
		}
	} else {
		// Clear
		for(int i = 0; i < 7; i++) uid[i] = 0;
		HAL_Delay(50);
	}

	if(boost_on){
		doStar();
		boost_current_time = HAL_GetTick();
		if((boost_current_time - boost_start_time) >= boost_max_time){
			boost_on = 0;
		}
	}
}
void do_scoreboard (){
	for (int i=0; i<9; i++){
	  Scoreboard_Update(1);
	  HAL_Delay(1000);
	  Scoreboard_Update(2);
	  HAL_Delay(1000);
	}
	Scoreboard_Update(0);
}
