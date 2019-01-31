

########################################################################
# Project setup
########################################################################
CMAKE_MINIMUM_REQUIRED(VERSION 2.8.2)
IF(POLICY CMP0048)
  CMAKE_POLICY(SET CMP0048 NEW) # Suppress Version warnings
ENDIF(POLICY CMP0048)
PROJECT(uhd-theseus CXX C)
ENABLE_TESTING()

find_package(UHD)

#make sure our local CMake Modules path comes first
list(INSERT CMAKE_MODULE_PATH 0 ${CMAKE_SOURCE_DIR}/cmake/Modules)

########################################################################
# UHD Dependency Minimum Versions
########################################################################
# Full C++11 came with GCC 4.7, Clang >= 3.3.0, Apple Clang >= 500
SET(GCC_MIN_VERSION "4.8.0")
SET(CLANG_MIN_VERSION "3.3.0")
SET(APPLECLANG_MIN_VERSION "500")
# Make sure to update the next two in unison:
SET(MSVC_MIN_VERSION "1900")
SET(MSVC_MIN_VERSION_READABLE "14.0")
# Other deps
SET(BOOST_MIN_VERSION "1.53")

########################################################################
# Check Compiler Version
########################################################################
IF(${CMAKE_CXX_COMPILER_ID} STREQUAL "GNU")
    IF(DEFINED CMAKE_CXX_COMPILER_VERSION)
        IF(${CMAKE_CXX_COMPILER_VERSION} VERSION_LESS ${GCC_MIN_VERSION})
            MESSAGE(WARNING "\nThe compiler selected to build UHD (GCC version ${CMAKE_CXX_COMPILER_VERSION} : ${CMAKE_CXX_COMPILER}) is older than that officially supported (${GCC_MIN_VERSION} minimum). This build may or not work. We highly recommend using a more recent GCC version.")
         ENDIF()
    ELSE()
        MESSAGE(WARNING "\nCannot determine the version of the compiler selected to build UHD (GCC : ${CMAKE_CXX_COMPILER}). This build may or not work. We highly recommend using GCC version ${GCC_MIN_VERSION} or more recent.")
    ENDIF()
    SET(CMAKE_CXX_FLAGS_DEBUG "${CMAKE_CXX_FLAGS_DEBUG} -Og")
ELSEIF(${CMAKE_CXX_COMPILER_ID} STREQUAL "Clang")
    EXECUTE_PROCESS(COMMAND
        ${CMAKE_CXX_COMPILER} -v
        RESULT_VARIABLE res ERROR_VARIABLE err
        ERROR_STRIP_TRAILING_WHITESPACE)
    IF(${res} STREQUAL "0")
        # output is in error stream
        STRING(REGEX MATCH "^Apple.*" IS_APPLE ${err})
        IF("${IS_APPLE}" STREQUAL "")
            SET(MIN_VERSION ${CLANG_MIN_VERSION})
            SET(APPLE_STR "")
            # retrieve the compiler's version from it
            STRING(REGEX MATCH "clang version [0-9.]+" CLANG_OTHER_VERSION ${err})
            STRING(REGEX MATCH "[0-9.]+" CLANG_VERSION ${CLANG_OTHER_VERSION})
        ELSE()
            SET(MIN_VERSION ${APPLECLANG_MIN_VERSION})
            SET(APPLE_STR "Apple ")
            # retrieve the compiler's version from it
            STRING(REGEX MATCH "(clang-[0-9.]+)" CLANG_APPLE_VERSION ${err})
            STRING(REGEX MATCH "[0-9.]+" CLANG_VERSION ${CLANG_APPLE_VERSION})
        ENDIF()
        IF(${CLANG_VERSION} VERSION_LESS "${MIN_VERSION}")
            MESSAGE(WARNING "\nThe compiler selected to build UHD (${APPLE_STR}Clang version ${CLANG_VERSION} : ${CMAKE_CXX_COMPILER}) is older than that officially supported (${MIN_VERSION} minimum). This build may or not work. We highly recommend using Apple Clang version ${APPLECLANG_MIN_VERSION} or more recent, or Clang version ${CLANG_MIN_VERSION} or more recent.")
        ENDIF()
    ELSE()
        MESSAGE(WARNING "\nCannot determine the version of the compiler selected to build UHD (${APPLE_STR}Clang : ${CMAKE_CXX_COMPILER}). This build may or not work. We highly recommend using Apple Clang version ${APPLECLANG_MIN_VERSION} or more recent, or Clang version ${CLANG_MIN_VERSION} or more recent.")
    ENDIF()
ELSEIF(MSVC)
    IF(${MSVC_VERSION} VERSION_LESS ${MSVC_MIN_VERSION})
	MESSAGE(FATAL_ERROR "\nMSVC version is less than the required minimum. Required: ${MSVC_MIN_VERSION_READABLE}")
    ENDIF(${MSVC_VERSION} VERSION_LESS ${MSVC_MIN_VERSION})
ENDIF()

IF(CMAKE_VERSION VERSION_LESS "3.1")
    IF(${CMAKE_CXX_COMPILER_ID} STREQUAL "GNU")
        SET(CMAKE_CXX_FLAGS "--std=gnu++11 ${CMAKE_CXX_FLAGS}")
    ELSEIF(${CMAKE_CXX_COMPILER_ID} STREQUAL "Clang")
        IF("${IS_APPLE}" STREQUAL "")
            SET(CMAKE_CXX_FLAGS "-std=c++11 ${CMAKE_CXX_FLAGS}")
        ELSE()
            SET(CMAKE_CXX_FLAGS "-std=c++11 -stdlib=libc++ ${CMAKE_CXX_FLAGS}")
        ENDIF()
    ENDIF()
ELSE()
    SET(CMAKE_CXX_STANDARD 11)
ENDIF()

IF(CMAKE_SYSTEM_NAME STREQUAL "FreeBSD" AND ${CMAKE_CXX_COMPILER_ID} STREQUAL "Clang")
    SET(CMAKE_EXE_LINKER_FLAGS "-lthr ${CMAKE_EXE_LINKER_FLAGS}")
    SET(CMAKE_CXX_FLAGS "-stdlib=libc++ ${CMAKE_CXX_FLAGS}")
ENDIF()

########################################################################
# Install Dirs
########################################################################

SET(RUNTIME_DIR bin)
SET(LIBRARY_DIR lib$)
SET(INCLUDE_DIR include)
SET(PKG_DATA_DIR share/uhd)

########################################################################
# Local Include Dir
########################################################################
include_directories(
    ${CMAKE_SOURCE_DIR}/uhd-theseus/lib
    ${CMAKE_SOURCE_DIR}/uhd-theseus/include
    ${CMAKE_BINARY_DIR}/uhd-theseus/lib
    ${CMAKE_BINARY_DIR}/uhd-theseus/include
    ${Boost_INCLUDE_DIRS}
)

ADD_SUBDIRECTORY(include/theseus)
ADD_SUBDIRECTORY(rfnoc-blocks)
ADD_SUBDIRECTORY(lib)
