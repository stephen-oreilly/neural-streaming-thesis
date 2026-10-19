#ifndef FLASH_H
#define FLASH_H

#include <stddef.h>
#include <stdint.h>


/**
 * @brief Initialise the external flash memory.
 *
 * Checks that the external flash device is available and ready for use.
 * This function should be called once before any read, write, or erase
 * operations are attempted.
 *
 * @return 0 on success, or a negative error code on failure.
 */
int ns_flash_init(void);


/**
 * @brief Write data to external flash memory.
 *
 * Writes @p len bytes from the memory location pointed to by @p data
 * into external flash, starting at the specified byte @p offset.
 *
 * The flash region being written to may need to be erased beforehand,
 * depending on its current contents.
 *
 * @param offset Byte offset from the beginning of external flash.
 * @param data   Pointer to the data to be written.
 * @param len    Number of bytes to write.
 *
 * @return 0 on success, or a negative error code on failure.
 */
int ns_flash_write(uint32_t offset, const void *data, size_t len);


/**
 * @brief Read data from external flash memory.
 *
 * Reads @p len bytes from external flash, starting at the specified
 * byte @p offset, and copies them into the buffer pointed to by @p buffer.
 *
 * The destination buffer must be large enough to hold @p len bytes.
 *
 * @param offset Byte offset from the beginning of external flash.
 * @param buffer Pointer to the destination buffer.
 * @param len    Number of bytes to read.
 *
 * @return 0 on success, or a negative error code on failure.
 */
int ns_flash_read(uint32_t offset, void *buffer, size_t len);


/**
 * @brief Erase a region of external flash memory.
 *
 * Erases the flash region beginning at @p offset for @p len bytes.
 *
 * Flash memory generally has erase-size alignment requirements, so
 * @p offset and @p len may need to correspond to complete erase sectors.
 *
 * After erasure, erased bytes will normally read back as 0xFF.
 *
 * @param offset Byte offset from the beginning of external flash.
 * @param len    Number of bytes to erase.
 *
 * @return 0 on success, or a negative error code on failure.
 */
int ns_flash_erase(uint32_t offset, size_t len);


#endif /* FLASH_H */



/**
 * @brief Return number of bytes in external flash memory
 * 
 * 
 * @return number of bytes
 */
size_t ns_flash_get_size(void);