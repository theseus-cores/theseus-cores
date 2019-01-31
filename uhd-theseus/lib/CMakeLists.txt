
########################################################################
# Setup library
########################################################################
include_directories(
    ${UHD_INCLUDE_DIRS}
    ${Boost_INCLUDE_DIRS}
)
link_directories(
  ${UHD_LIBRARY_DIRS}
  ${Boost_LIBRARY_DIRS}
 )

list(APPEND uhd_theseus_sources
	ducddc_block_ctrl_impl.cpp
)

set(uhd_theseus_sources "${uhd_theseus_sources}" PARENT_SCOPE)

add_library(uhd-theseus SHARED ${uhd_theseus_sources})
target_link_libraries(uhd-theseus ${Boost_LIBRARIES} ${ETTUS_LIBRARIES})
set_target_properties(uhd-theseus PROPERTIES DEFINE_SYMBOL "uhd_theseus_EXPORTS")

########################################################################
# Install built library files
########################################################################
install(TARGETS uhd-theseus
    LIBRARY DESTINATION lib${LIB_SUFFIX} # .so/.dylib file
    ARCHIVE DESTINATION lib${LIB_SUFFIX} # .lib file
    RUNTIME DESTINATION bin              # .dll file
)
