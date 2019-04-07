#
# Copyright 2016 Ettus Research
#

#-------------------------------------------------
# Top-of-Makefile
#-------------------------------------------------
# Define BASE_DIR to point to the "top" dir
UHD_FPGA_DIR = /home/phil/git_clones/fpga
BASE_DIR = ${UHD_FPGA_DIR}/usrp3/top

$(info BASE_DIR="$(BASE_DIR)")
# Include viv_sim_preample after defining BASE_DIR
include $(BASE_DIR)/../tools/make/viv_sim_preamble.mak

# -------------------------------------------------------------------
# Setup simulation
# -------------------------------------------------------------------
# Define part using PART_ID (<device>/<package>/<speedgrade>)
# and architecture (zynq, kintex7, or artix7)
# User can override these if needed
ARCH = zynq
PART_ID = xc7z020/clg484/-3

#-------------------------------------------------
# IP Specific
#-------------------------------------------------
# If simulation contains IP, define the IP_DIR and point
# it to the base level IP directory
LIB_IP_DIR = $(BASE_DIR)/../lib/ip
IP_DIR = $(LIB_IP_DIR)
SIM_DIR = $(abspath ./)

CHAN_RFNOC_DIR = $(abspath ../../m2_channelizer)
CHAN_IP_DIR = $(abspath ../../../fpga-src/axi_m2_channelizer/ip)
CHAN_SRC_DIR = $(abspath ../../../fpga-src/axi_m2_channelizer/src/verilog)

$(info CHAN_IP_DIR="$(CHAN_IP_DIR)")
$(info CHAN_SRC_DIR="$(CHAN_SRC_DIR)")
$(info SIM_DIR="$(SIM_DIR)")
# Include makefiles and sources for all IP components
# *after* defining the RFNOC_PFB_CHANNELIZER_DIR
include $(CHAN_IP_DIR)/xfft/Makefile.inc
# binary input and taps files

DESIGN_SRCS += $(abspath \
$(LIB_IP_CHANNELIZER_XFFT_SRCS))

#-------------------------------------------------
# Testbench Specific
#-------------------------------------------------
# Define only one toplevel module
SIM_TOP = noc_block_channelizer_tb
SIM_RUNTIME_US = 20000
#
# $(SIM_DIR)/chan_rfnoc_sim.vh \
# Add test bench, user design under test, and
# additional user created files
SIM_SRCS = $(abspath ./noc_block_channelizer_tb.sv \
$(SIM_DIR)/chan_rfnoc_sim.vh \
$(SIM_DIR)/sig_tones_input.bin \
$(SIM_DIR)/M_8_taps.bin \
$(CHAN_SRC_DIR)/dp_block_read_first_ram.v \
$(CHAN_SRC_DIR)/dp_block_write_first_ram.v \
$(CHAN_SRC_DIR)/axi_fifo_2.v \
$(CHAN_SRC_DIR)/axi_fifo_3.v \
$(CHAN_SRC_DIR)/axi_fifo_18.v \
$(CHAN_SRC_DIR)/axi_fifo_19.v \
$(CHAN_SRC_DIR)/axi_fifo_51.v \
$(CHAN_SRC_DIR)/axi_fifo_80.v \
$(CHAN_SRC_DIR)/count_cycle_cw16_8.v \
$(CHAN_SRC_DIR)/count_cycle_cw16_18.v \
$(CHAN_SRC_DIR)/slicer_48_13.v \
$(CHAN_SRC_DIR)/dsp48_cic_M256_N1_R1_iw5_0_corr.v \
$(CHAN_SRC_DIR)/dsp48_cic_M256_N1_R1_iw5_0.v \
$(CHAN_SRC_DIR)/dsp48_comb_M256_N1_iw5_0.v \
$(CHAN_SRC_DIR)/dsp48_integrator_section_0.v \
$(CHAN_SRC_DIR)/dsp48_output_add.v \
$(CHAN_SRC_DIR)/dsp48_pfb_mac_0.v \
$(CHAN_SRC_DIR)/dsp48_pfb_mac.v \
$(CHAN_SRC_DIR)/dsp48_pfb_rnd.v \
$(CHAN_SRC_DIR)/cic_M256_N1_R1_iw5_0_correction_sp_rom.v \
$(CHAN_SRC_DIR)/cic_M256_N1_R1_iw5_0_offset_sp_rom.v \
$(CHAN_SRC_DIR)/comb_M256_N1_iw5_0.v \
$(CHAN_SRC_DIR)/cic_M256_N1_R1_iw5_0.v \
$(CHAN_SRC_DIR)/circ_buffer.v \
$(CHAN_SRC_DIR)/exp_shifter.v \
$(CHAN_SRC_DIR)/input_buffer.v \
$(CHAN_SRC_DIR)/pfb_2x_16iw_16ow_32tps.v \
$(SIM_DIR)/grc_word_writer.sv \
$(CHAN_SRC_DIR)/channelizer_top.v \
$(CHAN_RFNOC_DIR)/noc_block_channelizer.v \
)

# MODELSIM_USER_DO = $(abspath wave.do)

#-------------------------------------------------
# Bottom-of-Makefile
#-------------------------------------------------
# Include all simulator specific makefiles here
# Each should define a unique target to simulate
# e.g. xsim, vsim, etc and a common "clean" target
include $(BASE_DIR)/../tools/make/viv_simulator.mak
