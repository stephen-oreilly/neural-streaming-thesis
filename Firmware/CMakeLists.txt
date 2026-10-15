cmake_minimum_required(VERSION 3.20.0)

list(APPEND EXTRA_CONF_FILE
    ${CMAKE_CURRENT_SOURCE_DIR}/secrets.conf
)


find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})

project(neural_data_streaming)

target_sources(app PRIVATE
 src/main.c
 src/wifi.c
 src/ns_flash.c)

 target_include_directories(app PRIVATE
    include
)