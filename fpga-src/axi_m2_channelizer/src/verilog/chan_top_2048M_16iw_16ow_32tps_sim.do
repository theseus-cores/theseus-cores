
#     Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.  

###############################################################################
#
# Workspace and design setup.
#
###############################################################################
# Name of workspace.
set WORKSPACE "channelizer"

# Name of design in workspace.
set DESIGN "chan_top"

# Root directory for project.
set PROJECT_ROOT $env(HOME)/insert path here

# Aldec Riviera Pro install location.
set ALDEC_HOME $env(ALDEC_HOME)

# Simulation scripts, waveforms, etc.
set PROJ_SIM "$PROJECT_ROOT/sim"

set PROJ_SRC_ROOT "$PROJECT_ROOT/src"

set VIVADO_ROOT "/opt/Xilinx/Vivado/2018.2/"
set GLBL_FILE "$VIVADO_ROOT/data/verilog/src/glbl.v"

###############################################################################
#
# Source locations.
#
###############################################################################
# Verilog source.
set PROJ_SRC "$PROJ_SRC_ROOT/verilog"

###############################################################################
#
# Workspace and project creation.
#
###############################################################################
# End any running simulation.
framework.documents.closeall
catch {
    endsim
}

# Close current workspace.
catch {
    workspace.close
}

# Create workspace if it does not already exist.
if { [ catch { workspace.create $WORKSPACE $PROJ_SIM } ] } {
    puts stdout "Opening workspace $WORKSPACE"
    workspace.open $PROJ_SIM/$WORKSPACE/$WORKSPACE.rwsp
} else {
    puts stdout "Creating workspace $WORKSPACE"
}

catch {
    workspace.design.remove $DESIGN
}

catch {
    file delete -force $PROJ_SIM/$WORKSPACE/$DESIGN
}
catch {
    workspace.design.create $DESIGN . -template $ALDEC_HOME/config/design_templates/default.rdsn }

alib work $PROJ_SIM/$WORKSPACE/$DESIGN/work.lib
set worklib work

###############################################################################
#
# Create and build design and add source files.
#
###############################################################################
# Set design properties.  Refer to $ALDEC_HOME/config/preferences/compilation.pref
# for valid properties.
design.property compilation/verilog/verilog-libraries unisims_ver
design.property compilation/verilog/verilog-libraries glbl
design.property compilation/verilog/enable-incremental-compilation true
design.property compilation/vhdl/enable-incremental-compilation true

#design.file.add $GLBL_FILE
design.file.add $PROJ_SRC/xfft_2048_sim_netlist.v

design.file.add $PROJ_SRC/chan_sim.vh
design.file.add $PROJ_SRC/grc_word_writer.sv
design.file.add $PROJ_SRC/grc_word_reader.sv

# Set dependency on xfft so it is compiled after top.
catch {
    design.dependencies.add channelizer_top.v xfft_2048_sim_netlist.vhd
}

design.file.add $PROJ_SRC/pipe_mux_2048_1.v
design.file.add $PROJ_SRC/downselect_2048.v

design.file.add $PROJ_SRC/dp_block_read_first_ram.v
design.file.add $PROJ_SRC/dp_block_write_first_ram.v
design.file.add $PROJ_SRC/axi_fifo_18.v
design.file.add $PROJ_SRC/axi_fifo_2.v
design.file.add $PROJ_SRC/axi_fifo_3.v
design.file.add $PROJ_SRC/axi_fifo_51.v
design.file.add $PROJ_SRC/axi_fifo_64.v
design.file.add $PROJ_SRC/count_cycle_cw16_18.v
design.file.add $PROJ_SRC/count_cycle_cw16_65.v
design.file.add $PROJ_SRC/count_cycle_cw16_8.v
design.file.add $PROJ_SRC/cic_M256_N1_R1_iw5_0_correction_sp_rom.v
design.file.add $PROJ_SRC/cic_M256_N1_R1_iw5_0_offset_sp_rom.v
design.file.add $PROJ_SRC/dsp48_cic_M256_N1_R1_iw5_0_corr.v
design.file.add $PROJ_SRC/dsp48_cic_M256_N1_R1_iw5_0.v
design.file.add $PROJ_SRC/dsp48_comb_M256_N1_iw5_0.v
design.file.add $PROJ_SRC/dsp48_pfb_mac_0.v
design.file.add $PROJ_SRC/dsp48_pfb_mac.v
design.file.add $PROJ_SRC/dsp48_pfb_rnd.v
design.file.add $PROJ_SRC/comb_M256_N1_iw5_0.v
design.file.add $PROJ_SRC/cic_M256_N1_R1_iw5_0.v
design.file.add $PROJ_SRC/pfb_2048Mmax_16iw_16ow_32tps_dp_rom.v
design.file.add $PROJ_SRC/mem_ctrl_pfb_2048Mmax_16iw_16ow_32tps.v
design.file.add $PROJ_SRC/slicer_48_13.v
design.file.add $PROJ_SRC/pfb_2048Mmax_16iw_16ow_32tps.v
design.file.add $PROJ_SRC/exp_shifter_2048Mmax_16iw_256avg_len.v
design.file.add $PROJ_SRC/input_buffer_1x.v

design.file.add $PROJ_SRC/chan_top_2048M_16iw_16ow_32tps.v
design.file.add $PROJ_SRC/chan_top_2048M_16iw_16ow_32tps_tb.v

design.compile $DESIGN

###############################################################################
#
# Run simulation.
#
###############################################################################
design.simulation.initialize chan_top_2048M_16iw_16ow_32tps_tb glbl

run 4000 us
