#
# Copyright 2019 Theseus Cores
#

########################################################################
# Initialize project
########################################################################
cmake_minimum_required(VERSION 3.8)
project(theseus-cores)

IF(EXISTS "${CMAKE_BINARY_DIR}/../conanbuildinfo.cmake")
  include(${CMAKE_BINARY_DIR}/../conanbuildinfo.cmake)
  conan_basic_setup()
  conan_set_find_library_paths()
ENDIF()

# Install to PyBOMBS target prefix if defined
if(DEFINED ENV{PYBOMBS_PREFIX})
    set(CMAKE_INSTALL_PREFIX $ENV{PYBOMBS_PREFIX})
    message(STATUS "PyBOMBS installed GNU Radio. Setting CMAKE_INSTALL_PREFIX to $ENV{PYBOMBS_PREFIX}")
endif()

# Select the release build type by default to get optimization flags
if(NOT CMAKE_BUILD_TYPE)
   set(CMAKE_BUILD_TYPE "Release")
   message(STATUS "Build type not specified: defaulting to release.")
endif(NOT CMAKE_BUILD_TYPE)
set(CMAKE_BUILD_TYPE ${CMAKE_BUILD_TYPE} CACHE STRING "")

# Make sure our local CMake Modules path comes first
# list(INSERT CMAKE_MODULE_PATH 0 ${CMAKE_SOURCE_DIR}/cmake/Modules)

cmake_policy(SET CMP0011 NEW)

# Enable generation of compile_commands.json for code completion engines
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

########################################################################
# Install Dirs
########################################################################

SET(RUNTIME_DIR bin)
SET(LIBRARY_DIR lib$)
SET(INCLUDE_DIR include)
SET(PKG_DATA_DIR share/uhd)

# find_package(gnuradio-ettus REQUIRED)
# find_package(gnuradio-fft REQUIRED)

########################################################################
# Conditionally include desired components
########################################################################

# Check for UHD
IF(NOT DEFINED ENABLE_UHD)
    set(ENABLE_UHD "ON")
ENDIF()
IF(ENABLE_UHD)
    add_subdirectory(uhd-theseus)
ENDIF(ENABLE_UHD)

# Check for Gnuradio
IF(NOT DEFINED ENABLE_GNURADIO)
    set(ENABLE_GNURADIO "ON")
ENDIF()
IF(ENABLE_GNURADIO)
    IF(ENABLE_UHD)
        add_subdirectory(gr-theseus)
    ELSE(ENABLE_UHD)
        message(FATAL_ERROR "ENABLE_UHD required in order to run with ENABLE_GNURADIO")
    ENDIF(ENABLE_UHD)
ENDIF(ENABLE_GNURADIO)
