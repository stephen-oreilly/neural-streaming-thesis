#include "wifi.h"

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

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


	




    return 0;
}