

########################################################################
# Install RFNOC Block definitions
########################################################################
FILE(GLOB xml_files "*.xml")

install(FILES
	${xml_files}
    DESTINATION ${PKG_DATA_DIR}/rfnoc/blocks
    COMPONENT headers
)
