
target_sources(app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/ns_data_processing.c
)

target_include_directories(app PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)
