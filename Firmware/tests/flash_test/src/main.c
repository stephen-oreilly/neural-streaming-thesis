// Test program to check that we can write arbitrary data to flash memory using ns_flash API. 
// Writes NUM_SAMPLES of a sine wave to flash starting at FLASH_OFFSET bytes location in memory
// Reads sample back into a separate read buffer and checks that write_buffer = read_buffer

#include <math.h>
#include <stdint.h>
#include <string.h>

#include <zephyr/kernel.h>
#include <zephyr/logging/log.h>

#include "ns_flash.h"


LOG_MODULE_REGISTER(flash_test, LOG_LEVEL_INF);


#define NUM_SAMPLES         128
#define SINE_AMPLITUDE      10000

#define FLASH_OFFSET        0
#define FLASH_ERASE_SIZE    4096

#define PI 3.14159265358979323846f


int main(void)
{
    int err;

    int16_t write_buffer[NUM_SAMPLES];
    int16_t read_buffer[NUM_SAMPLES];


    err = ns_flash_init();
    if (err) {
        LOG_ERR("Flash initialisation failed: %d", err);
        return err;
    }


    /* Generate one complete sine-wave period. */
    for (int i = 0; i < NUM_SAMPLES; i++) {

        float phase = (2.0f * PI * i) / NUM_SAMPLES;

        write_buffer[i] =
            (int16_t)(SINE_AMPLITUDE * sinf(phase));
    }


    /* Erase the flash region before writing. */
    err = ns_flash_erase(FLASH_OFFSET, FLASH_ERASE_SIZE);
    if (err) {
        LOG_ERR("Flash erase failed: %d", err);
        return err;
    }


    /* Write sine-wave samples to flash. */
    err = ns_flash_write(
        FLASH_OFFSET,
        write_buffer,
        sizeof(write_buffer)
    );

    if (err) {
        LOG_ERR("Flash write failed: %d", err);
        return err;
    }


    /* Clear read buffer so old RAM contents cannot mask problems. */
    memset(read_buffer, 0, sizeof(read_buffer));


    /* Read samples back from flash. */
    err = ns_flash_read(
        FLASH_OFFSET,
        read_buffer,
        sizeof(read_buffer)
    );

    if (err) {
        LOG_ERR("Flash read failed: %d", err);
        return err;
    }


    /* Verify that written and read data match. */
    for (int i = 0; i < NUM_SAMPLES; i++) {

        if (write_buffer[i] != read_buffer[i]) {

            LOG_ERR(
                "Mismatch at sample %d: wrote %d, read %d",
                i,
                write_buffer[i],
                read_buffer[i]
            );

            return -1;
        }
    }


    LOG_INF("Flash test passed");
    LOG_INF("Successfully wrote and read back %zu bytes",
            sizeof(write_buffer));

    return 0;
}