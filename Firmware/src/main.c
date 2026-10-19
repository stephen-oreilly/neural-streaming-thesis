#include "wifi.h"
#include "ns_flash.h"
#include "ns_test_data.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/socket.h>
#include <string.h>


#define NUM_SAMPLES 512
#define RECEIVER_IP "192.168.0.19"

#define N_PACKETS       10
#define SAMPLES_PER_PKT 512
#define BYTES_PER_SAMPLE 2

#define PACKET_BYTES (SAMPLES_PER_PKT * BYTES_PER_SAMPLE)


LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);


// Temporary helper function
// Want to fill flash with a large number of periods of a single sine wave

static int fill_flash_with_sine(void)
{
    int16_t buffer[NUM_SAMPLES];

    test_data_generate_sine(buffer, NUM_SAMPLES);

    size_t flash_size = ns_flash_get_size();
    size_t buffer_size = sizeof(buffer);

	// int err = ns_flash_erase(0, flash_size);
	// if(err != 0){
	// 	LOG_ERR("Error in fill_flash_with_sine() - could not erase flash memory before write.");
	// }

    for (size_t offset = 0; offset < flash_size; offset += buffer_size) {

        size_t bytes_to_write = buffer_size;

        if (offset + bytes_to_write > flash_size) {
            bytes_to_write = flash_size - offset;
        }

        int err = ns_flash_write(offset, buffer, bytes_to_write);

        if (err) {
            return err;
        }
    }

    return 0;
}


int main(void)
{

	// Step 1) Initialise and fill external flash
	int err = ns_flash_init();

	if (err) {
		LOG_ERR("Failed to initialise external flash.");
		return 0;
	}




	// err = fill_flash_with_sine();
	// 	if (err) {
	// 	LOG_ERR("fill_flash_with_sine() function failed.");	
	// 	return 0;
	// }


	// LOG_INF("fill_flash_with_sine() executed successfully");



	// Step 2) Establish wifi connection
    wifi_init();
	k_sleep(K_SECONDS(3));   //Magic number - works for now, need to replace with event driven timing

    err = wifi_connect();
    if (err) {
        LOG_ERR("main(): Wi-Fi connection request failed: %d", err);
        return err;
    }

    LOG_INF("Waiting for Wi-Fi connection...");
    wifi_wait_for_connection();    
    LOG_INF("Wi-Fi connected successfully");


	
	//Step 3) Establish connection with receiver with Zephyr socket API
	int sock = zsock_socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

	if (sock < 0) {
		LOG_ERR("Failed to create socket");
		return sock;
	}

	struct sockaddr_in dest_addr = {0};

	dest_addr.sin_family = AF_INET;
	dest_addr.sin_port = htons(5000);

	err = zsock_inet_pton(AF_INET,
							RECEIVER_IP,
							&dest_addr.sin_addr);

	if (err != 1) {
		LOG_ERR("Invalid IP address");
		zsock_close(sock);
		return -1;
	}


	//Step 4) Read data from flash and send to receiver
	uint8_t tx_buf[PACKET_BYTES];

	for (uint32_t i = 0; i < N_PACKETS; i++) {

		uint32_t flash_offset = i * PACKET_BYTES;

		err = ns_flash_read(flash_offset,
							tx_buf,
							PACKET_BYTES);

		if (err) {
			LOG_ERR("Flash read failed at packet %u", i);
			break;
		}


		ssize_t sent = zsock_sendto(sock,
									tx_buf,
									PACKET_BYTES,
									0,
									(struct sockaddr *)&dest_addr,
									sizeof(dest_addr));

		if (sent != PACKET_BYTES) {
			LOG_ERR("Packet %u did not send correct number of bytes", i);
			zsock_close(sock);
			break;
		}

		LOG_INF("Sent packet %u (%d bytes)", i, sent);
	}



	zsock_close(sock);



    return 0;
}



