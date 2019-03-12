# RFNoC-specific Makefile for OOT repos

# Save path
THESEUS_CHANNELIZER_DIR := $(OOT_DIR)

# Append RFNoC source files
RFNOC_SRCS += $(addprefix $(THESEUS_CHANNELIZER_DIR)/, \
noc_block_channelizer.v \
)

# Include IP
include $(abspath $(THESEUS_CHANNELIZER_DIR)/../../fpga-src/axi_m2_channelizer/xfft/Makefile.inc)
LIB_OOT_IP_XCI_SRCS = $(LIB_IP_CHANNELIZER_XFFT_SRCS)
LIB_OOT_IP_SYNTH_OUTPUTS = $(LIB_IP_CHANNELIZER_XFFT_OUTS)
LIB_IP_XCI_SRCS += $(LIB_IP_CHANNELIZER_XFFT_SRCS)

# Include fpga-src files
RFNOC_SRCS += $(addprefix $(THESEUS_CHANNELIZER_DIR)/../../fpga-src/axi_m2_channelizer/src/verilog, \
dp_block_read_first_ram.v, \
dp_block_write_first_ram.v, \
axi_fifo_2.v, \
axi_fifo_3.v, \
axi_fifo_18.v, \
axi_fifo_19.v, \
axi_fifo_51.v, \
axi_fifo_80.v, \
count_cycle_cw16_8.v, \
count_cycle_cw16_18.v, \
slicer_48_13.v, \
dsp48_cic_M256_N1_R1_iw5_0_corr.v, \
dsp48_cic_M256_N1_R1_iw5_0.v, \
dsp48_comb_M256_N1_iw5_0.v, \
dsp48_integrator_section_0.v, \
dsp48_output_add.v, \
dsp48_pfb_mac_0.v, \
dsp48_pfb_mac.v, \
dsp48_pfb_rnd.v, \
cic_M256_N1_R1_iw5_0_correction_sp_rom.v, \
cic_M256_N1_R1_iw5_0_offset_sp_rom.v, \
comb_M256_N1_iw5_0.v, \
cic_M256_N1_R1_iw5_0.v, \
circ_buffer.v, \
exp_shifter.v, \
input_buffer.v, \
pfb_2x_16iw_16ow_32tps.v, \
channelizer_top.v, \
noc_block_channelizer.v, \
)
