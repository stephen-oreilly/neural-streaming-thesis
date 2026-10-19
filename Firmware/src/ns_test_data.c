#include "ns_test_data.h"

#include <math.h>
#include <zephyr/logging/log.h>

#define SINE_AMPLITUDE 30000.0f
#define PI 3.14159265358979323846f

LOG_MODULE_REGISTER(ns_test_data, LOG_LEVEL_INF);

void test_data_generate_sine(int16_t *buf, size_t n)
{
    if ((buf == NULL) || (n == 0)) {
        return;
    }

    for (size_t i = 0; i < n; i++) {
        float phase = 2.0f * PI * (float)i / (float)n;

        buf[i] = (int16_t)(SINE_AMPLITUDE * sinf(phase));

        // LOG_INF("Sample %u: %d", (unsigned int)i, buf[i]);
    }
}