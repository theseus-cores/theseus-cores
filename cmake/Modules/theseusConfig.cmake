INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_THESEUS theseus)

FIND_PATH(
    THESEUS_INCLUDE_DIRS
    NAMES theseus/api.h
    HINTS $ENV{THESEUS_DIR}/include
        ${PC_THESEUS_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    THESEUS_LIBRARIES
    NAMES gnuradio-theseus
    HINTS $ENV{THESEUS_DIR}/lib
        ${PC_THESEUS_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/theseusTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(THESEUS DEFAULT_MSG THESEUS_LIBRARIES THESEUS_INCLUDE_DIRS)
MARK_AS_ADVANCED(THESEUS_LIBRARIES THESEUS_INCLUDE_DIRS)
