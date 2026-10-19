#include "ns_flash.h"

#include <errno.h>

#include <zephyr/device.h>
#include <zephyr/devicetree.h>
#include <zephyr/drivers/flash.h>
#include <zephyr/logging/log.h>


LOG_MODULE_REGISTER(ns_flash, LOG_LEVEL_INF);


/* External MX25R64 SPI-NOR flash defined by the board devicetree. */
#define FLASH_NODE DT_NODELABEL(mx25r64)
#define NS_FLASH_SIZE_BYTES (DT_PROP(FLASH_NODE, size) / 8)

/* Zephyr device object used for all flash operations in this module. */
static const struct device *flash_dev = DEVICE_DT_GET(FLASH_NODE);


int ns_flash_init(void)
{
    if (!device_is_ready(flash_dev)) {
        LOG_ERR("External flash device is not ready");
        return -ENODEV;
    }

    LOG_INF("External flash initialised");

    return 0;
}


int ns_flash_write(uint32_t offset, const void *data, size_t len)
{
    int err = flash_write(flash_dev, offset, data, len);

    if (err) {
        LOG_ERR("Flash write failed: %d", err);
        return err;
    }

    LOG_DBG("Wrote %zu bytes at offset 0x%08x", len, offset);

    return 0;
}


int ns_flash_read(uint32_t offset, void *buffer, size_t len)
{
    int err = flash_read(flash_dev, offset, buffer, len);

    if (err) {
        LOG_ERR("Flash read failed: %d", err);
        return err;
    }

    LOG_DBG("Read %zu bytes at offset 0x%08x", len, offset);

    return 0;
}


int ns_flash_erase(uint32_t offset, size_t len)
{
    int err = flash_erase(flash_dev, offset, len);

    if (err) {
        LOG_ERR("Flash erase failed: %d", err);
        return err;
    }

    LOG_DBG("Erased %zu bytes at offset 0x%08x", len, offset);

    return 0;
}


size_t ns_flash_get_size(void)
{
    return NS_FLASH_SIZE_BYTES;
}