#ifndef WIFI_H
#define WIFI_H

#include <stdbool.h>

int wifi_init(void);
int wifi_connect(void);
void wifi_wait_for_connection(void);
bool wifi_is_connected(void);

#endif