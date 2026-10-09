#include "wifi.h"

#include <string.h>
#include <errno.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/net_if.h>
#include <zephyr/net/net_mgmt.h>
#include <zephyr/net/wifi_mgmt.h>
#include <zephyr/net/wifi_credentials.h>


LOG_MODULE_REGISTER(wifi, LOG_LEVEL_INF);

// Define event mask - used to keep track of all relevant events
#define EVENT_MASK (NET_EVENT_L4_CONNECTED | NET_EVENT_L4_DISCONNECTED)


// Creating callback object for network connection
static struct net_mgmt_event_callback wifi_cb;

// Bool for keeping track of connection status
static bool connected;

// Semaphore for signalling wifi connection to main()
K_SEM_DEFINE(network_ready_sem, 0, 1);



/**
 * @brief Handle network management events.
 *
 * Called by Zephyr's network management subsystem when one of the
 * registered events in EVENT_MASK occurs.
 *
 * On NET_EVENT_L4_CONNECTED:
 * - Mark the network as connected.
 * - Signal waiting application code using network_ready_sem.
 *
 * On NET_EVENT_L4_DISCONNECTED:
 * - Mark the network as disconnected.
 * - Reset network_ready_sem.
 *
 * @param cb         Pointer to the registered network management callback.
 * @param mgmt_event Network management event that triggered the callback.
 * @param iface      Network interface associated with the event.
 */
static void net_mgmt_event_handler(
    struct net_mgmt_event_callback *cb,
    uint64_t mgmt_event,
    struct net_if *iface)
{

    ARG_UNUSED(cb);
    ARG_UNUSED(iface);

    /* Ignore events outside our event mask. */
    if ((mgmt_event & EVENT_MASK) != mgmt_event) {
        return;
    }

    if (mgmt_event == NET_EVENT_L4_CONNECTED) {
        LOG_INF("net_mgmt_event_handler(): Network connected");

        connected = true;

        /* Wake any thread waiting for network connectivity. */
        k_sem_give(&network_ready_sem);

        return;
    }

    if (mgmt_event == NET_EVENT_L4_DISCONNECTED) {
        LOG_INF("Network disconnected");

        connected = false;

        /* Network is no longer in the ready state. */
        k_sem_reset(&network_ready_sem);

        return;
    }
}


/**
 * @brief Initialize Wi-Fi event handling.
 *
 * Registers the network management callback used to monitor
 * connection and disconnection events.
 *
 * This function does not initiate a Wi-Fi connection.
 *
 * @return 0 on success.
 */
int wifi_init(void)
{
    connected = false;

    net_mgmt_init_event_callback(
        &wifi_cb,
        net_mgmt_event_handler,
        EVENT_MASK
    );

    net_mgmt_add_event_callback(&wifi_cb);

    LOG_INF("Function wifi_init(): Wi-Fi event handler initialized");

    return 0;
}




/**
 * @brief Initiate a Wi-Fi connection.
 *
 * Gets the Wi-Fi network interface, fills the connection parameters
 * such as SSID, password, security mode, channel, and band, then sends
 * a NET_REQUEST_WIFI_CONNECT request through Zephyr's Network Management API.
 *
 * This function only starts the connection attempt. Connection success
 * is reported later through the registered network event callback -> see wifi_init().
 *
 * @return 0 if the connection request was submitted successfully,
 *         otherwise a negative error code.
 */
int wifi_connect(void)
{
    struct wifi_connect_req_params params;  //wifi_connect_req_params is a Zephyr structure used for passing params to a net_mgmt() API

    struct net_if *iface = net_if_get_first_wifi();  //returns a pointer to an active wifi NW interface in Zephyr. Get Zephyr's software representation of the Wi-Fi network interface.

    if (iface == NULL) {
        LOG_ERR("Function wifi_connect() - no wifi interfaces can be found.");
        return -ENODEV;
    }

    /* Fill connection settings. */
    memset(&params, 0, sizeof(params));

    params.ssid = CONFIG_WIFI_CREDENTIALS_STATIC_SSID;
    params.ssid_length = strlen(params.ssid);

    params.psk = CONFIG_WIFI_CREDENTIALS_STATIC_PASSWORD;
    params.psk_length = strlen(params.psk);

    params.channel = WIFI_CHANNEL_ANY;
    params.security = WIFI_SECURITY_TYPE_PSK;
    params.mfp = WIFI_MFP_OPTIONAL;
    params.timeout = SYS_FOREVER_MS;
    params.band = WIFI_FREQ_BAND_UNKNOWN;

    int err =  net_mgmt(
        NET_REQUEST_WIFI_CONNECT,
        iface,
        &params,
        sizeof(params)
    );

    if(err){
        LOG_ERR("Function wifi_connect(): Connecting to Wi-Fi failed, err: %d", err);
	    return err;
    }

    return 0;

}



/**
 * @brief Wait for network 
 *
 * Registers the network management callback used to monitor
 * connection and disconnection events.
 *
 * This function does not initiate a Wi-Fi connection.
 *
 * @return 0 on success.
 */
void wifi_wait_for_connection(void){
    k_sem_take(&network_ready_sem, K_FOREVER);
}


bool wifi_is_connected(void){
    return connected;
}




