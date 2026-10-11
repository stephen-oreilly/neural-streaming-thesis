#include "wifi.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/socket.h>


LOG_MODULE_REGISTER(main, LOG_LEVEL_INF);

int main(void)
{


	// Establish wifi connection
    wifi_init();
	k_sleep(K_SECONDS(3));   //Magic number - works for now, need to replace with event driven timing

    int err = wifi_connect();
    if (err) {
        LOG_ERR("main(): Wi-Fi connection request failed: %d", err);
        return err;
    }

    LOG_INF("Waiting for Wi-Fi connection...");
    wifi_wait_for_connection();   //function will 
    LOG_INF("Wi-Fi connected successfully");


	//Testing UDP data sending abilities:
	int sock = zsock_socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);

	if (sock < 0) {
		LOG_ERR("Failed to create socket");
		return sock;
	}

	struct sockaddr_in dest_addr = {0};

	dest_addr.sin_family = AF_INET;
	dest_addr.sin_port = htons(5000);

	err = zsock_inet_pton(AF_INET,
							"192.168.1.196",
							&dest_addr.sin_addr);

	if (err != 1) {
		LOG_ERR("Invalid IP address");
		zsock_close(sock);
		return -1;
	}

	char message[] = "Hello from board";

	int bytes_sent = zsock_sendto(sock,
								message,
								strlen(message),
								0,
								(struct sockaddr *)&dest_addr,
								sizeof(dest_addr));

	if (bytes_sent < 0) {
		LOG_ERR("send failed");
		zsock_close(sock);
		return bytes_sent;
	}

	LOG_INF("Sent %d bytes", bytes_sent);

	zsock_close(sock);



    return 0;
}