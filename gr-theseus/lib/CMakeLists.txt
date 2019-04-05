# Copyright 2011,2012 Free Software Foundation, Inc.
#
# This file is part of GNU Radio
#
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.

########################################################################
# Setup library
########################################################################
include(GrPlatform) #define LIB_SUFFIX

include_directories(${Boost_INCLUDE_DIR})
link_directories(${Boost_LIBRARY_DIRS})
list(APPEND gr_theseus_sources
  theseus_generic_impl.cc
)

# NOTE: I couldnt figure out how to properly link gnuradio's swig library with
# uhd-theseus such that block controllers are imported correctly into a flowgraph...
# So I'm just adding them here I suppose. This seems to do the trick...
# TODO: Figure out how to link the generated swig with RFNOC block controllers
list(APPEND uhd_theseus_sources
  ${CMAKE_SOURCE_DIR}/uhd-theseus/lib/ddc_1_to_n_block_ctrl_impl.cpp
  ${CMAKE_SOURCE_DIR}/uhd-theseus/lib/ducddc_block_ctrl_impl.cpp
)

set(gr_theseus_sources "${gr_theseus_sources} ${uhd_theseus_sources}" PARENT_SCOPE)
if(NOT gr_theseus_sources)
    MESSAGE(STATUS "No C++ sources... skipping lib/")
    return()
endif(NOT gr_theseus_sources)

add_library(gnuradio-theseus SHARED ${gr_theseus_sources} ${uhd_theseus_sources})
target_link_libraries(gnuradio-theseus
  ${Boost_LIBRARIES}
  ${GNURADIO_ALL_LIBRARIES}
  ${ETTUS_LIBRARIES}
)
set_target_properties(gnuradio-theseus PROPERTIES DEFINE_SYMBOL "gnuradio_theseus_EXPORTS")

if(APPLE)
    set_target_properties(gnuradio-theseus PROPERTIES
        INSTALL_NAME_DIR "${CMAKE_INSTALL_PREFIX}/lib"
    )
endif(APPLE)

########################################################################
# Install built library files
########################################################################
install(TARGETS gnuradio-theseus
    LIBRARY DESTINATION lib${LIB_SUFFIX} # .so/.dylib file
    ARCHIVE DESTINATION lib${LIB_SUFFIX} # .lib file
    RUNTIME DESTINATION bin              # .dll file
)
