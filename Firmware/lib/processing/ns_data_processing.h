/*For our initial purposes/commit, we just want to verify that we can pass a pointer to a buffer of data and modify it some way,
and ensure that this can be integrated into the current streaming setup
-> To that end, we will implement an amplitude clipping function and verify that the data at the receiver matches our expectation
*/


#ifndef NS_DATA_PROCESSING
#define NS_DATA_PROCESSING

#include <stdint.h>
#include <stddef.h>



/**
 * @brief Apply symmetric hard clipping to a sample buffer.
 *
 * Limits the amplitude of each sample to the range
 * [-threshold, threshold]. Samples outside this range are
 * replaced with the corresponding limit.
 *
 * The operation is performed in-place, modifying the original buffer.
 *
 * @param buffer    Pointer to the sample buffer.
 * @param n_samples Number of samples in the buffer.
 * @param threshold Maximum permitted absolute sample amplitude.
 *                  Must be non-negative.
 */
void ns_processing_clip(int16_t *buffer,
                        size_t n_samples,
                        int16_t threshold);


#endif