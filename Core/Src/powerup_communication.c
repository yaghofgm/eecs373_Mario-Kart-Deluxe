#define RX_BUFFER_SIZE 32
char rx_buffer[RX_BUFFER_SIZE];
uint8_t rx_byte;
uint8_t rx_index = 0;
volatile uint8_t data_ready = 0;

// This code receives the uart message, we can then
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart->Instance == USART3) {
        // Ignore newline/carriage return characters from filling up the data buffer
        if (rx_byte != '\n' && rx_byte != '\r') {
            rx_buffer[rx_index++] = rx_byte;

            // Prevent buffer overflow if garbage data is received
            if (rx_index >= RX_BUFFER_SIZE - 1) {
                rx_index = 0;
            }
        }

        // If we received the closing bracket, the message is complete
        if (rx_byte == '}') {
            rx_buffer[rx_index] = '\0'; // Null-terminate the string so sscanf can read it safely
            data_ready = 1;             // Tell the main loop to process it
            rx_index = 0;               // Reset index for the next incoming message
        }

        // IMPORTANT: Re-arm the interrupt to listen for the next byte!
        HAL_UART_Receive_IT(&huart3, &rx_byte, 1);
    }
}

void update_lap_time() {
	// LCD update here
}
