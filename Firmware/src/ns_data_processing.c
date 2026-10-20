#include "ns_data_processing.h"



void ns_processing_clip(int16_t *buffer,
                        size_t n_samples,
                        int16_t threshold)
                        {
                             for (size_t i = 0; i < n_samples; i++) {
                                if (buffer[i] > threshold) {
                                    buffer[i] = threshold;
                                }
                                else if (buffer[i] < -threshold) {
                                    buffer[i] = -threshold;
                                }

                        }

                    }
