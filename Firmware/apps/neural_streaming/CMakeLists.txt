
cmake_minimum_required(VERSION 3.20.0)

list(APPEND EXTRA_CONF_FILE
    ${CMAKE_CURRENT_SOURCE_DIR}/secrets.conf
)


find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(neural_streaming)

# Firmware root directory
set(FIRMWARE_ROOT ${CMAKE_CURRENT_SOURCE_DIR}/../..)

# Application sources
target_sources(app PRIVATE
    src/main.c
)

# Shared components
add_subdirectory(
    ${FIRMWARE_ROOT}/lib/flash
    ${CMAKE_CURRENT_BINARY_DIR}/lib_flash
)

add_subdirectory(
    ${FIRMWARE_ROOT}/lib/processing
    ${CMAKE_CURRENT_BINARY_DIR}/lib_processing
)

add_subdirectory(
    ${FIRMWARE_ROOT}/lib/test_data
    ${CMAKE_CURRENT_BINARY_DIR}/lib_test_data
)

add_subdirectory(
    ${FIRMWARE_ROOT}/lib/wifi
    ${CMAKE_CURRENT_BINARY_DIR}/lib_wifi
)
