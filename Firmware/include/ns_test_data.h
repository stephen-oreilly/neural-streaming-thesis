#ifndef NS_TEST_DATA_H
#define NS_TEST_DATA_H

#include <stddef.h>
#include <stdint.h>


/**
 * @brief Generate one period of a signed 16-bit sine wave.
 *
 * Fills the supplied buffer with @p n evenly spaced samples representing
 * one complete sine-wave period.
 *
 * @param buf Pointer to the destination sample buffer.
 * @param n Number of samples to generate.
 */
void test_data_generate_sine(int16_t *buf, size_t n);




#endif