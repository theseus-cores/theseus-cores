# RFNoC-specific Makefile for OOT repos

# Save path
THESEUS_DSPUTILS_DIR := $(OOT_DIR)
THESEUS_UTILS_SRC := $(OOT_DIR)/../../fpga-src/utils

# Append RFNoC source files
RFNOC_SRCS += $(addprefix $(THESEUS_DSPUTILS_DIR)/, \
noc_block_ducddc.v \
noc_block_ddc_1_to_n.v \
)

RFNOC_SRCS += $(addprefix $(THESEUS_UTILS_SRC)/, \
multi_split_stream.v \
)
