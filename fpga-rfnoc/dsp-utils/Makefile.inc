# RFNoC-specific Makefile for OOT repos

# Save path
THESEUS_DSPUTILS_DIR := $(OOT_DIR)

# Append RFNoC source files
RFNOC_SRCS += $(addprefix $(THESEUS_DSPUTILS_DIR)/, \
noc_block_ducddc.v \
)
