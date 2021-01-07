# -*- coding: utf-8 -*-
"""
Created on Mon Feb 27 13:20:20 2017

@author: phil
"""

import ipdb  # analysis:ignore

from phy_tools.vgen_xilinx import gen_dsp48E1, gen_dsp48E2
from phy_tools.vgen_altera import altera_mult, altera_madd
from phy_tools.adv_pfb import gen_pfb
import phy_tools.vhdl_gen as vhdl_gen
from phy_tools.verilog_gen import gen_ram, gen_axi_fifo, gen_slicer, name_help, gen_rom, ret_addr_width, axi_fifo_inst
from phy_tools.gen_utils import ret_module_name, ret_file_name, ret_valid_path, print_header
from phy_tools.fp_utils import ret_num_bitsU

import numpy as np
from IPython.core.debugger import set_trace

from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    __version__ = today.strftime("%Y.%m.%d")


def gen_single_filter(path, rom_fi, input_width=16, output_width=16, taps_per_phase=24, ram_style='block',
                      pfb_msb=40, tlast=False, tuser_width=0, prefix='', dsp48e2=False, gen_2X=False):
    """
        Generates Verilog for single phase fully non time sliced filter.
    """
    set_trace()

    tup_val =  gen_pfb(path, 1, rom_fi, input_width, output_width, rom_fi.len, False,
                       pfb_msb, tlast, tuser_width, ram_style, prefix, gen_2X, dsp48e2)

    (module_name, tap_ram_name, ram_name) = tup_val
    return (module_name, tap_ram_name, ram_name)

def gen_mac_top(path, prefix='', tuser_width=0, fil_msb=40, num_taps=64, tlast=False, ram_style='block',
                rnd=False, dsp48e2=False):

    """
        Generates top level for MAC based filter.
    """

def gen_dec_filter(path, fil_obj, prefix='', tuser_width=0, tlast=False, ram_style='block', dsp48e2=False,
                   fifo_ram_style='distributed'):

    """
        Generates Verilog code to generat MAC based filter.

        Args:
            path (str):
                Full path to store output files.

            prefix (str):
                Prefix to file names for uniqueness in a large project.

            tuser_width (int):
                Number of TUser bits.

            fil_msb (int):
                Filter MSB location.

            num_taps (int):
                Number of filter taps.

            tlast (bool):
                Indicates whether there a tlast interface or not.

    """

    taps_per_phase = fil_obj.taps_per_phase
    qvec = fil_obj.qvec
    Mmax = fil_obj.M - 1
    pfb_prefix = prefix

    m_bits = ret_num_bitsU(fil_obj.M)
    m_msb = m_bits - 1

    phase_bits = ret_num_bitsU(fil_obj.M - 1)
    phase_msb = phase_bits - 1

    word_bits = 2 * qvec[0]
    word_msb = word_bits - 1

    output_width = fil_obj.qvec_out[0] * 2

    tup_val = gen_pfb(path, Mmax, fil_obj.b_fi, input_width=qvec[0], output_width=48, taps_per_phase=taps_per_phase,
                      tlast=tlast, tuser_width=tuser_width, ram_style='block', dsp48e2=dsp48e2, prefix=pfb_prefix,
                      count_dn=True)

    (pfb_name, tap_ram_name, ram_name) = tup_val

    funcs = ['C', 'C+P', 'C+P+CONCAT']
    accum_name = prefix + 'accum'

    rnd_const = (1 << (fil_obj.lsb - 1)) - 1
    if dsp48e2:
        (int_file, int_name) = gen_dsp48E2(path, accum_name, opcode=funcs, creg=3, concatreg=3, use_ce=0, dither=True)
    else:
        (int_file, int_name) = gen_dsp48E1(path, accum_name, opcode=funcs, creg=3, concatreg=3, use_ce=0)

    path = ret_valid_path(path)

    # generate FIFO code.
    af_thresh = 4
    addr_width = 3
    (_, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, tlast=tlast, almost_full=True, 
                                  ram_style=fifo_ram_style, prefix='')

    print(fifo_name, int_name, pfb_name)
    latency = 1 + 4 # 1 for phase controller, 4 for accumulator delay.
    lat_msb = latency - 1

    file_name = path + '{}dec_fil.v'.format(prefix)
    module_name = ret_module_name(file_name)
    with open(file_name, "w") as fh:

        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// File        : {}.v\n'.format(module_name))
        fh.write('// Description : Top-level controller for Poly-phase downsampling filter.\n')
        fh.write('//\n')
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        if tuser_width:
            fh.write('module {} #( \n'.format(module_name))
            fh.write('    parameter TUSER_WIDTH=32)\n')
        else:
            fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input [{}:0] num_phases,\n'.format(m_msb))
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [{}:0] s_axis_tdata,\n'.format(word_msb))
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        if tuser_width:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    // Filter coefficient reload interface.\n')
        fh.write('    input s_axis_reload_tvalid,\n')
        fh.write('    input [31:0] s_axis_reload_tdata,\n')
        fh.write('    input s_axis_reload_tlast,\n')
        fh.write('    output s_axis_reload_tready,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [{}:0] m_axis_tdata,\n'.format(word_msb))
        if tlast:
            fh.write('    output m_axis_tlast,\n')
        if tuser_width:
            fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('parameter MAX_NUM_PHASES = {}\'d{};\n'.format(m_bits, fil_obj.M))
        fh.write('parameter RND_VALUE = 48\'d{};\n'.format(rnd_const))
        fh.write('\n')
        fh.write('reg [{}:0] phase_ctrl, next_phase_ctrl;\n'.format(phase_msb))
        fh.write('\n')
        fh.write('wire [{}:0] phase_out;\n'.format(phase_msb))
        fh.write('wire pfb_tvalid;\n')
        if tlast:
            fh.write('wire pfb_tlast;\n')
        fh.write('\n')
        fh.write('wire [95:0] pfb_tdata;\n')  # these are fixed since using 2 dsp48
        fh.write('reg [95:0] pfb_tdata_d;\n')
        fh.write('\n')
        if tuser_width:
            fh.write('wire [TUSER_WIDTH-1:0] pfb_tuser;\n')
        fh.write('wire pfb_tready;\n')
        fh.write('\n')
        fh.write('reg [{}:0] phase_max;\n'.format(m_msb))
        fh.write('reg [{}:0] phase_max_slice;\n'.format(phase_msb))
        fh.write('\n')
        fh.write('wire [{}:0] data_bus;\n'.format(word_msb))
        # fh.write('reg [{}:0] data_bus_reg[0:{}];\n'.format(word_msb, lat_msb))
        fh.write('wire dsp_valid;\n')
        fh.write('reg [{}:0] dsp_valid_reg;\n'.format(lat_msb))
        fh.write('\n')
        fh.write('wire almost_full;\n')
        fh.write('wire take_data;\n')
        fh.write('\n')
        fh.write('reg [1:0] opcode_ctrl, next_opcode_ctrl;\n')
        fh.write('\n')
        fh.write('wire [47:0] fil_i, fil_q;\n')
        fh.write('wire [47:0] pout_i, pout_q;\n')
        fh.write('\n')
        if tlast:
            fh.write('reg [{}:0] tlast_d;\n'.format(lat_msb))
        if tuser_width:
            fh.write('reg [TUSER_WIDTH-1:0] tuser_d[0:{}];\n'.format(lat_msb))
        fh.write('\n')
        fh.write('assign fil_i = pfb_tdata_d[95:48];\n')
        fh.write('assign fil_q = pfb_tdata_d[47:0];\n')
        fh.write('assign s_axis_tready = ~almost_full;\n')
        fh.write('assign pfb_tready = ~almost_full;\n')
        fh.write('assign take_data = (s_axis_tvalid & s_axis_tready);\n')
        tup_val = (fil_obj.msb, fil_obj.lsb, fil_obj.msb, fil_obj.lsb)
        fh.write('assign data_bus = {{pout_i[{}:{}], pout_q[{}:{}]}};\n'.format(*tup_val))
        fh.write('assign dsp_valid = (pfb_tvalid == 1\'b1 && phase_out == {}\'d0) ? 1\'b1 : 1\'b0;\n'.format(phase_bits))
        fh.write('\n')
        fh.write('// sync reset process.\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        phase_ctrl <= phase_max_slice;\n')
        fh.write('        opcode_ctrl <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        phase_ctrl <= next_phase_ctrl;\n')
        fh.write('        opcode_ctrl <= next_opcode_ctrl;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// Delay process.\n')
        fh.write('integer m;\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('\n')
        fh.write('    phase_max <= num_phases - 1;\n')
        fh.write('    phase_max_slice <= phase_max[{}:0];\n'.format(phase_msb))
        fh.write('    pfb_tdata_d <= pfb_tdata;\n')
        fh.write('    dsp_valid_reg <= {{dsp_valid_reg[{}:0], dsp_valid}};\n'.format(lat_msb - 1))
        # fh.write('    data_bus_reg[0] <= data_bus;\n')
        # fh.write('    for (m=1; m<{}; m=m+1) begin\n'.format(latency))
        # fh.write('        data_bus_reg[m] <= data_bus_reg[m-1];\n')
        # fh.write('    end\n')
        if tlast:
            fh.write('    tlast_d <= {{tlast_d[{}:0], pfb_tlast}};\n'.format(lat_msb - 1))
        if tuser_width:
            fh.write('    tuser_d[0] <= pfb_tuser;\n')
            fh.write('    for (m=1; m<{}; m=m+1) begin\n'.format(latency))
            fh.write('        tuser_d[m] <= tuser_d[m-1];\n')
            fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// Async process\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_phase_ctrl = phase_ctrl;\n')
        fh.write('    next_opcode_ctrl = opcode_ctrl;\n')
        fh.write('    if (take_data == 1\'b1) begin\n')
        fh.write('        if (phase_ctrl == 0) begin\n')
        fh.write('            next_phase_ctrl = phase_max_slice;\n')
        fh.write('        end else begin\n')
        fh.write('            next_phase_ctrl = phase_ctrl - 1;\n')
        fh.write('        end\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    if (pfb_tvalid == 1\'b1) begin\n')
        fh.write('        // set accumulator to --> C + P + CONCAT for rounding\n')
        fh.write('        if (phase_out == {}\'d0) begin\n'.format(phase_bits))
        fh.write('            next_opcode_ctrl = 2\'d2;\n')
        fh.write('        // set accumulator to --> C\n')
        fh.write('        end else if (phase_out == phase_max_slice) begin\n')
        fh.write('            next_opcode_ctrl = 2\'d0;\n')
        fh.write('        // else set to --> C + P\n')
        fh.write('        end else begin\n')
        fh.write('            next_opcode_ctrl = 2\'d1;\n')
        fh.write('        end\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        if tuser_width:
            fh.write('{} #( \n'.format(pfb_name))
            fh.write('    .TUSER_WIDTH(TUSER_WIDTH))\n')
            fh.write('u_pfb_fil (\n')
        else:
            fh.write('{} u_pfb_fil (\n'.format(pfb_name))
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(sync_reset),\n')
        fh.write('\n')
        fh.write('    .num_phases(num_phases),\n')
        fh.write('    .phase(phase_ctrl),\n')
        fh.write('\n')
        fh.write('    .s_axis_tvalid(take_data),\n')
        fh.write('    .s_axis_tdata(s_axis_tdata),\n')
        if tlast:
            fh.write('    .s_axis_tlast(s_axis_tlast),\n')
        if tuser_width:
            fh.write('    .s_axis_tuser(s_axis_tuser),\n')
        fh.write('    .s_axis_tready(),\n')
        fh.write('\n')
        fh.write('    .s_axis_reload_tvalid(s_axis_reload_tvalid),\n')
        fh.write('    .s_axis_reload_tdata(s_axis_reload_tdata),\n')
        fh.write('    .s_axis_reload_tlast(s_axis_reload_tlast),\n')
        fh.write('    .s_axis_reload_tready(s_axis_reload_tready),\n')
        fh.write('\n')
        fh.write('    .phase_out(phase_out),\n')
        fh.write('    .m_axis_tvalid(pfb_tvalid),\n')
        fh.write('    .m_axis_tdata(pfb_tdata),\n')
        if tlast:
            fh.write('    .m_axis_tlast(pfb_tlast),\n')
        if tuser_width:
            fh.write('    .m_axis_tuser(pfb_tuser),\n')
        fh.write('    .m_axis_tready(pfb_tready)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// I channel accumulator\n')
        fh.write('// Latency = 4.\n')
        fh.write('{} u_accum_i\n'.format(int_name))
        fh.write('(\n')
        fh.write('    .clk(clk),\n')
        fh.write('\n')
        fh.write('    .concat(RND_VALUE),\n')
        fh.write('    .c(fil_i),\n')
        fh.write('    .opcode(opcode_ctrl),\n')
        fh.write('    .p(pout_i)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// Q channel accumulator.\n')
        fh.write('{} u_accum_q\n'.format(int_name))
        fh.write('(\n')
        fh.write('    .clk(clk),\n')
        fh.write('\n')
        fh.write('    .concat(RND_VALUE),\n')
        fh.write('    .c(fil_q),\n')
        fh.write('    .opcode(opcode_ctrl),\n')
        fh.write('    .p(pout_q)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        s_tvalid_str = 'dsp_valid_reg[{}]'.format(lat_msb)
        s_tdata_str = 'data_bus'
        s_tuser_str = None
        m_tuser_str = None
        if tuser_width:
            s_tuser_str = 'tuser_d[{}]'.format(lat_msb)
            m_tuser_str = 'm_axis_tuser'
        s_tlast_str = None
        m_tlast_str = None
        if tlast:
            s_tlast_str = 'tlast_d[{}]'.format(lat_msb)
            m_tlast_str = 'm_axis_tlast'

        almost_full_str = 'almost_full'
        axi_fifo_inst(fh, fifo_name, inst_name='u_axi_fifo', data_width=output_width, af_thresh=af_thresh,
                addr_width=addr_width, tuser_width=tuser_width, tlast=tlast, s_tvalid_str=s_tvalid_str,
                s_tdata_str=s_tdata_str, s_tuser_str=s_tuser_str, s_tlast_str=s_tlast_str,
                s_tready_str='', almost_full_str=almost_full_str, m_tvalid_str='m_axis_tvalid', m_tdata_str='m_axis_tdata',
                m_tuser_str=m_tuser_str, m_tlast_str=m_tlast_str, m_tready_str='m_axis_tready')

        fh.write('\n')
        fh.write('\n')
        fh.write('endmodule\n')



def gen_mac_filter(path, prefix='', qvec=(16, 15), qvec_coef=(25, 24),tuser_width=0, fil_msb=40, fil_lsb=25, 
                   num_coeffs=64, tlast=False, ram_style='block', rnd=False, dsp48e2=False, first_mac=False, 
                   last_mac=False, num_macs=8, fifo_ram_style='distributed',
                   addr_width=3):
    """
        Generates Verilog code to generat MAC based filter.

        Args:
            path (str):
                Full path to store output files.

            prefix (str):
                Prefix to file names for uniqueness in a large project.

            tuser_width (int):
                Number of TUser bits.

            fil_msb (int):
                Filter MSB location.

            num_taps (int):
                Number of filter taps.

            tlast (bool):
                Indicates whether there a tlast interface or not.

    """
    path = ret_valid_path(path)
    file_name = path + '{}mac_filter.v'.format(prefix)
    module_name = ret_module_name(file_name)

    tap_addr_width = ret_num_bitsU(num_coeffs - 1)
    tap_addr_msb = tap_addr_width - 1
    tuser_width = int(tuser_width)
    opcode= ['A*B+C', 'A*B+P'] if not first_mac else ['A*B', 'A*B+P']

    dsp_lat = 2 + 1 + 1 # 2 A/B latency, 1 mult latency, 1 adder latency.
    dlat_msb = dsp_lat - 1
    c_latency  = 3 + 1*first_mac # 3 - RAM latency, 1 for counter updates first mac,
    clat_msb = c_latency - 1
    latency = c_latency + dsp_lat
    lat_msb = latency - 1

    p_width = (fil_msb - fil_lsb + 1)
    p_msb = p_width - 1
    output_width = p_width * 2
    output_msb = output_width - 1
    name = prefix + 'mac'
    b_width = qvec[0]
    a_width = qvec_coef[0]
    input_msb = 2 * qvec[0] - 1
    fifo_name = None

    rnd_s = rnd if last_mac else False
    fifo_name = None
    if dsp48e2:
        (dsp_name, dsp_module_name) = gen_dsp48E2(path, name=name, opcode=opcode, a_width=a_width, b_width=b_width,
                                                  c_width=48, areg=2, breg=2, creg=3, mreg=1, preg=1, p_msb=fil_msb, p_lsb=fil_lsb,
                                                  use_pcout=False, use_ce=True, rnd=rnd_s)

    else:
        (dsp_name, dsp_module_name) = gen_dsp48E1(path, name=name, opcode=opcode, a_width=a_width, b_width=b_width,
                                                  c_width=48, areg=2, breg=2, creg=3, mreg=1, preg=1, p_msb=fil_msb, p_lsb=fil_lsb,
                                                  use_pcout=False, use_ce=True, rnd=rnd_s)

    if last_mac:
        (_, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, tlast=tlast, almost_full=True, almost_empty=False,
                                      count=False, ram_style=fifo_ram_style, prefix='')

    ram_name = gen_ram(path, ram_type='dp', memory_type='read_first', ram_style=ram_style)
    taps_ram_name = gen_ram(path, ram_type='dp', memory_type='write_first', ram_style=ram_style)
    with open(file_name, "w") as fh:
        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('// Implements MAC based filter with run-time loop length.  Taps are configurable.\n')
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        if tuser_width:
            fh.write('#(   parameter TUSER_WIDTH=8)\n')
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        if first_mac:
            fh.write('    input s_axis_tvalid,\n')
            fh.write('    input [{}:0] s_axis_tdata,\n'.format(input_msb))
            fh.write('    output s_axis_tready,\n')
            fh.write('    input [7:0] upper_cnt,\n')
        else:
            fh.write('    input dsb_valid_i,\n')
            fh.write('    input [{}:0] s_axis_tdata,\n'.format(input_msb))
            fh.write('    input [47:0] c_input_i,\n')
            fh.write('    input [47:0] c_input_q,\n')
            fh.write('    input [7:0] wr_addr,\n')
            fh.write('    input [7:0] rd_addr,\n')
            fh.write('    input opcode,\n')
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        if tuser_width:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        fh.write('\n')
        fh.write('    input taps_we,\n')
        fh.write('    input [{}:0] taps_data,\n'.format(a_width - 1))
        fh.write('    input [{}:0] taps_addr,\n'.format(tap_addr_msb))
        fh.write('\n')
        if not last_mac:
            fh.write('    output dsp_valid,\n')
        if first_mac and not last_mac:
            fh.write('    input almost_full,\n')

        if not last_mac:
            if tuser_width:
                fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
            if tlast:
                fh.write('    output m_axis_tlast,\n')

        if last_mac:
            fh.write('    output m_axis_tvalid,\n')
            fh.write('    output [{}:0] m_axis_tdata,\n'.format(output_msb))
            if tlast:
                fh.write('    output m_axis_tlast,\n')
            if tuser_width:
                fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
            fh.write('    input m_axis_tready\n')
        else:
            fh.write('    output opcode_o,\n')
            fh.write('    output [47:0] pouti,\n')
            fh.write('    output [47:0] poutq,\n')
            fh.write('    output [{}:0] data_out,\n'.format(input_msb))
            fh.write('    output [7:0] wr_addr_s,\n')
            fh.write('    output [7:0] rd_addr_s\n')
        fh.write(');\n')
        fh.write('\n')
        if tuser_width:
            fh.write('parameter TUSER_MSB = TUSER_WIDTH - 1;\n')
        fh.write('\n')
        fh.write('wire [{}:0] delay;\n'.format(input_msb))
        if tuser_width:
            fh.write('wire [TUSER_MSB:0] tuser_delay;\n')
        fh.write('\n')
        data_msb = input_msb
        if tlast:
            data_msb += 1
        fh.write('reg [{}:0] cycling_d;\n'. format(lat_msb))
        fh.write('// A(2), B(2), Mult, Adder\n')
        fh.write('reg [{}:0] data_reg[0:{}];\n'.format(data_msb, dlat_msb))  # A(2), B(2), Mult, Adder
        fh.write('reg [{}:0] data_latch = 0;\n'.format(data_msb)) 
        fh.write('reg [{}:0] next_data_latch = 0;\n'.format(data_msb))
        if not last_mac:
            fh.write('reg [47:0] c_reg_i[0:{}];\n'.format(clat_msb))
            fh.write('reg [47:0] c_reg_q[0:{}];\n'.format(clat_msb))
        fh.write('reg [{}:0] next_data_reg = 0;\n'.format(data_msb))
        fh.write('wire [{}:0] taps;\n'.format(a_width-1))
        if tuser_width:
            fh.write('reg [TUSER_MSB:0] tuser_latch = 0;\n')
            fh.write('reg [TUSER_MSB:0] next_tuser_latch = 0;\n')
            fh.write('reg [TUSER_MSB:0] tuser_reg[0:3];\n')
            fh.write('reg [TUSER_MSB:0] next_tuser_reg;\n')
            fh.write('\n')

        if first_mac:
            fh.write('wire take_data;\n')
            fh.write('reg take_data_d1;\n')
            fh.write('reg [{}:0] rd_addr, next_rd_addr;\n'.format(tap_addr_msb))
            fh.write('reg [{}:0] wr_addr, next_wr_addr;\n'.format(tap_addr_msb))
            fh.write('reg [7:0] rd_cnt, next_rd_cnt;\n')
            fh.write('reg startup, next_startup;\n')
            fh.write('\n')
            fh.write('wire addr_reset;\n')
            fh.write('wire cnt_reset;\n')
            fh.write('wire wr_addr_reset;\n')
            fh.write('reg cycling, next_cycling;\n')
            fh.write('wire opcode;\n')
            fh.write('\n')

        if last_mac:
            fh.write('wire [{}:0] pouti, poutq;\n'.format(p_msb))

        fh.write('reg [7:0] wr_addr_d[0:{}];\n'.format(clat_msb))
        fh.write('reg [7:0] rd_addr_d[0:{}];\n'.format(clat_msb))
        if first_mac:
            fh.write('reg [7:0] rd_cnt_d[0:{}];\n'.format(clat_msb))
            fh.write('reg [{}:0] cnt_reset_d;\n'.format(clat_msb))

        if last_mac:
            fh.write('wire [{}:0] data_bus;\n'.format(output_msb))
        fh.write('\n')
        if first_mac:
            fh.write('assign s_axis_tready = (~almost_full & (~cycling | cnt_reset));\n')
            fh.write('assign take_data = (s_axis_tvalid & s_axis_tready);\n')
            fh.write('assign addr_reset = (rd_addr == upper_cnt) ? 1\'b1 : 1\'b0;\n')
            fh.write('assign wr_addr_reset = (wr_addr == upper_cnt) ? 1\'b1 : 1\'b0;\n')
            fh.write('assign cnt_reset = (rd_cnt == upper_cnt) ? 1\'b1 : 1\'b0;\n')
            tup = (clat_msb - 1, clat_msb - 1)
            fh.write('assign opcode = (cycling_d[{}] == 1\'b1 && rd_cnt_d[{}] == 0) ? 1\'b1 : 1\'b0;\n'.format(*tup))

        if last_mac:
            fh.write('assign data_bus = {pouti, poutq};\n')

        lat_tuple = (lat_msb - 1, clat_msb - 1)
        fh.write('assign dsp_valid = (cycling_d[{}] == 1\'b1 && cnt_reset_d[{}] == 1\'b1) ? 1\'b1 : 1\'b0;\n'.format(*lat_tuple))
        # fh.write('assign cycling_o = cycling_d[{}];\n'.format(clat_msb))
        if not last_mac:
            fh.write('assign opcode_o = opcode;\n')
            fh.write('assign wr_addr_s = wr_addr_d[{}];\n'.format(clat_msb))
            fh.write('assign rd_addr_s = rd_addr_d[{}];\n'.format(clat_msb))
            fh.write('assign data_out = data_reg[{}][DATA_WIDTH-1:0];\n'.format(dlat_msb))
            if tuser_width:
                fh.write('assign m_axis_tuser = tuser_reg[{}][TUSER_MSB:0];\n'.format(dlat_msb))
            if tlast:
                fh.write('assign m_axis_tlast = data_reg[{}][DATA_WIDTH];\n'.format(dlat_msb))

        fh.write('\n')
        fh.write('assign s_axis_reload_tready = 1\'b1;\n')
        fh.write('\n')
        fh.write('// read and write address management.\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        if first_mac:
            fh.write('        wr_addr <= 8\'d0;\n')
            fh.write('        rd_addr <= 8\'d0;\n')
            fh.write('        rd_cnt <= 8\'d0;\n')
            fh.write('        cycling <= 1\'b0;\n')
            fh.write('        startup <= 1\'b0;\n')
        for ii in range(dsp_lat):
            fh.write('        data_reg[{}] <= 0;\n'.format(ii))
        if tuser_width:
            for ii in range(dsp_lat):
                fh.write('        tuser_reg[{}] <= 0;\n'.format(ii))

        fh.write('    end else begin\n')
        if first_mac:
            fh.write('        wr_addr <= next_wr_addr;\n')
            fh.write('        rd_addr <= next_rd_addr;\n')
            fh.write('        rd_cnt <= next_rd_cnt;\n')
            fh.write('        cycling <= next_cycling;\n')
            fh.write('        startup <= next_startup;\n')
        fh.write('        data_reg[0] <= next_data_reg;\n')
        for ii in range(1, dsp_lat):
            fh.write('        data_reg[{}] <= data_reg[{}];\n'.format(ii, ii - 1))
        if tuser_width:
            fh.write('        tuser_reg[0] <= next_tuser_reg;\n')
        if tuser_width:
            for ii in range(1, dsp_lat):
                fh.write('        tuser_reg[{}] <= tuser_reg[{}];\n'.format(ii, ii - 1))
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// input and rd addressing.\n')
        if first_mac:
            fh.write('always @*\n')
            fh.write('begin\n')
            fh.write('    next_startup = startup;\n')
            fh.write('    next_cycling = cycling;\n')
            fh.write('    next_rd_cnt = rd_cnt;\n')
            fh.write('    next_rd_addr = rd_addr;\n')
            fh.write('    next_wr_addr = wr_addr;\n')
            fh.write('    next_data_latch = data_latch;\n')
            if tuser_width:
                fh.write('    next_tuser_latch = tuser_latch;\n')
            fh.write('    if (take_data == 1\'b1 || cycling == 1\'b1) begin\n')
            fh.write('        next_cycling = (~cnt_reset | take_data);\n')
            fh.write('        next_startup = 1\'b0;\n')
            fh.write('        if (cnt_reset | startup) begin\n')
            fh.write('            next_rd_cnt = 8\'d0;\n')
            fh.write('        end else begin\n')
            fh.write('            next_rd_cnt = rd_cnt + 1;\n')
            fh.write('        end\n')
            fh.write('\n')
            fh.write('        if (take_data) begin\n')
            if tlast:
                fh.write('            next_data_latch = {s_axis_tlast, s_axis_tdata};\n')
            else:
                fh.write('            next_data_latch = s_axis_tdata;\n')
            if tuser_width:
                fh.write('            next_tuser_latch = s_axis_tuser;\n')
            fh.write('            if (wr_addr_reset) begin\n')
            fh.write('                next_wr_addr = 8\'d0;\n')
            fh.write('            end else begin\n')
            fh.write('                next_wr_addr = wr_addr + 1;\n')
            fh.write('            end\n')
            fh.write('        end\n')
            fh.write('\n')
            fh.write('        if (take_data) begin\n')
            fh.write('            next_rd_addr = wr_addr + 1;\n')
            fh.write('        end else if (addr_reset) begin\n')
            fh.write('            next_rd_addr = 8\'d0;\n')
            fh.write('        end else begin\n')
            fh.write('            next_rd_addr = rd_addr + 1;\n')
            fh.write('        end\n')
            fh.write('    end\n')
            fh.write('end\n')
            fh.write('\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_data_reg = data_reg[0];\n')
        if tuser_width:
            fh.write('    next_tuser_reg = tuser_reg[0];\n')
        tup = (clat_msb - 1, clat_msb - 1)
        fh.write('    if (cycling_d[{}] == 1\'b1 && rd_cnt_d[{}] == 8\'d0) begin\n'.format(*tup))
        fh.write('        next_data_reg[0] = delay;\n')
        if tuser_width:
            fh.write('        next_tuser_reg = tuser_delay;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// logic implements the sample write address pipelining.\n')
#         fh.write('integer n;\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    cycling_d <= {{cycling_d[{}:0], cycling}};\n'.format(lat_msb - 1))
        fh.write('    data_latch <= next_data_latch;\n')
        if tuser_width:
            fh.write('    tuser_latch <= next_tuser_latch;\n')
        fh.write('    take_data_d1 <= take_data;\n')
        if not first_mac:
            fh.write('    c_reg_i[0] <= c_input_i;\n')
            for ii in range(1, c_latency):
                fh.write('    c_reg_i[{}] <= c_reg_i[{}];\n'.format(ii, ii - 1))
            fh.write('\n')
            fh.write('    c_reg_q[0] <= c_input_q;\n')
            for ii in range(1, c_latency):
                fh.write('    c_reg_q[{}] <= c_reg_q[{}];\n'.format(ii, ii - 1))
        fh.write('\n')
        fh.write('    wr_addr_d[0] <= wr_addr;\n')
        for ii in range(1, c_latency):
            fh.write('    wr_addr_d[{}] <= wr_addr_d[{}];\n'.format(ii, ii - 1))
        fh.write('\n')
        fh.write('    rd_addr_d[0] <= rd_addr;\n')
        for ii in range(1, c_latency):
            fh.write('    rd_addr_d[{}] <= rd_addr_d[{}];\n'.format(ii, ii - 1))
        if first_mac:
            fh.write('\n')
            fh.write('    rd_cnt_d[0] <= rd_cnt;\n')
            for ii in range(1, c_latency):
                fh.write('    rd_cnt_d[{}] <= rd_cnt_d[{}];\n'.format(ii, ii - 1))
            fh.write('\n')
            fh.write('    cnt_reset_d <= {{cnt_reset_d[{}:0], cnt_reset}};\n'.format(clat_msb - 1))
        fh.write('end\n')
        fh.write('\n')
        if tuser_width:
            fh.write('// 3 cycle latency\n')
            fh.write('{} #(\n'.format(ram_name))
            fh.write('  .DATA_WIDTH(TUSER_WIDTH),\n')
            fh.write('  .ADDR_WIDTH({}))\n'.format(tap_addr_width))
            fh.write('tuser_ram (\n')
            fh.write('  .clk(clk),\n')
            fh.write('  .wea(take_data_d1),\n')
            fh.write('  .addra(wr_addr),\n')
            fh.write('  .dia(tuser_latch),\n')
            fh.write('  .addrb(rd_addr),\n')
            fh.write('  .dob(tuser_delay)\n')
            fh.write(');\n')
        fh.write('\n')
        fh.write('// 3 cycle latency\n')
        fh.write('{} #(\n'.format(ram_name))
        fh.write('  .DATA_WIDTH({}),\n'.format(data_msb + 1))
        fh.write('  .ADDR_WIDTH({}))\n'.format(tap_addr_width))
        fh.write('sample_ram (\n')
        fh.write('  .clk(clk),\n')
        fh.write('  .wea(take_data_d1),\n')
        fh.write('  .addra(wr_addr),\n')
        fh.write('  .dia(data_latch),\n')
        fh.write('  .addrb(rd_addr),\n')
        fh.write('  .dob(delay)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// Coefficent memories\n')
        fh.write('// latency = 3.\n')
        fh.write('{} #(\n'.format(taps_ram_name))
        fh.write('    .DATA_WIDTH({}),\n'.format(a_width))
        fh.write('    .ADDR_WIDTH({}))\n'.format(tap_addr_width))
        fh.write('taps_ram (\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .wea(taps_we),\n')
        fh.write('    .addra(taps_addr),\n')
        fh.write('    .dia(taps_data),\n')
        fh.write('    .addrb(rd_addr),\n')
        fh.write('    .dob(taps)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        lidx = data_msb
        ridx = b_width
        fh.write('// PFB MAC blocks\n')
        fh.write('{} mac_i (\n'.format(dsp_module_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .ce(cycling_d[2]),\n')
        fh.write('  .a(taps),\n')
        fh.write('  .b(delay[{}:{}]),\n'.format(lidx, ridx))
        if not first_mac:
            fh.write('  .c(c_reg_i[{}]),\n'.format(c_latency - 1))
        fh.write('  .opcode(opcode),\n')
        fh.write('  .p(pouti)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// Latency = 4\n')
        fh.write('{} mac_q (\n'.format(dsp_module_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .ce(cycling_d[2]),\n')
        fh.write('  .a(taps),\n')
        fh.write('  .b(delay[{}:0]),\n'.format(b_width - 1))
        if not first_mac:
            fh.write('  .c(c_reg_q[{}]),\n'.format(c_latency - 1))
        fh.write('  .opcode(opcode),\n')
        fh.write('  .p(poutq)\n')
        fh.write(');\n')
        fh.write('\n')
        if last_mac:
            # insert output fifo.
            data_width = output_width
            s_tdata_str = 'data_bus'
            s_tvalid_str = 'dsp_valid'
            almost_full_str = 'almost_full'
            m_tlast_str = None
            m_tuser_str = None
            s_tuser_str = None
            s_tlast_str = None
            af_thresh = (1 << addr_width) // 2
            if tlast:
                m_tlast_str = 'm_axis_tlast'
                s_tlast_str = 'data_reg[{}][DATA_WIDTH]'.format(dlat_msb)
            if tuser_width:
                m_tuser_str = 'm_axis_tuser'
                s_tuser_str = 'tuser_reg[{}]'.format(dlat_msb)

            axi_fifo_inst(fh, fifo_name, inst_name='u_axi_fifo', data_width=data_width, af_thresh=af_thresh,
                          addr_width=addr_width, tuser_width=tuser_width, tlast=tlast, s_tvalid_str=s_tvalid_str,
                          s_tdata_str=s_tdata_str, s_tuser_str=s_tuser_str, s_tlast_str=s_tlast_str,
                          s_tready_str='', almost_full_str=almost_full_str, m_tvalid_str='m_axis_tvalid', m_tdata_str='m_axis_tdata',
                          m_tuser_str=m_tuser_str, m_tlast_str=m_tlast_str, m_tready_str='m_axis_tready')
        fh.write('\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return (dsp_name, dsp_module_name, file_name, module_name)

# def gen_dec_filter(path, fil_obj, prefix='', tuser_width=0, tlast=False):
#     """
#         Generate Verilog code for creating a Polyphase decimating filter.
#     """

def gen_comb(path, cic_obj, prefix='', tuser_width=0, tlast=False):
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)

    cic_order = cic_obj.N
    input_width = cic_obj.input_width
    depth = cic_obj.M + 1
    addr_bits = ret_addr_width(depth)
    hash = 0
    if tlast:
        hash += 1
    if tuser_width > 0:
        hash += 2

    module_name = '{}comb_M{}_N{}_iw{}_{}'.format(prefix, cic_obj.M, cic_order, input_width, hash)
    file_name = name_help(module_name, path)

    ram_style = 'distributed' if depth <= 32 else 'block'
    (_, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, tlast=tlast, almost_full=False, almost_empty=False,
                                  count=False, max_delay=depth, ram_style=ram_style, prefix='')
    print(fifo_name)
    funcs = 'C-CONCAT'
    (_, dsp_name) = gen_dsp48E1(path, module_name, opcode=funcs, concatreg=2, creg=3, use_ce=False)
    print(dsp_name)

    assert(file_name is not None), 'User must specify File Name'
    with open(file_name, 'w') as fh:
        module_name = ret_module_name(file_name)

        m_bits = ret_num_bitsU(cic_obj.m_max)
        depth_bits = ret_num_bitsU(depth - 1)

        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author : PJV\n')
        fh.write('// File : {}.v\n'.format(module_name))
        fh.write('// Description : Comb Filter.\n')
        fh.write('// The module implements a comb filter using a RAM block and \n')
        fh.write('// a single DSP48A core. \n')
        fh.write('//\n')
        print_header(fh)
        fh.write('\n')
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        if tuser_width:
            fh.write('#(parameter TUSER_WIDTH=8)\n')
        fh.write('(\n')
        fh.write('  input clk,\n')
        fh.write('  input sync_reset,\n')
        fh.write('\n')
        fh.write('  input  [{}:0] msetting,\n'.format(m_bits - 1))
        fh.write('\n')
        fh.write('  input s_axis_tvalid,\n')
        fh.write('  input [47:0] s_axis_tdata,\n')
        fh.write('\n')
        if tlast:
            fh.write('  input s_axis_tlast,\n')
        if tuser_width > 0:
            fh.write('  input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        fh.write('  output m_axis_tvalid,\n')
        if tuser_width:
            fh.write('  output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        if tlast:
            fh.write('  output m_axis_tlast,\n')
        fh.write('  output [47:0] m_axis_tdata\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('localparam TOTAL_DELAY = 10;\n')
        fh.write('wire [47:0] diff_delay;\n')
        fh.write('wire [47:0] comb_out;\n')
        fh.write('wire [{}:0] msetting_s;\n'.format(depth_bits - 1))
        fh.write('\n')
        fh.write('reg [47:0] c_d0, c_d1, c_d2;\n')
        fh.write('\n')
        fh.write('reg [3:0] tvalid_d;\n')
        fh.write('wire tvalid_s;\n')
        fh.write('\n')
        if tlast:
            fh.write('wire tlast_s;\n')
            fh.write('reg [3:0] tlast_d;\n')
        if tuser_width > 0:
            fh.write('wire [TUSER_WIDTH-1:0] tuser_s;\n')
            fh.write('reg [TUSER_WIDTH-1:0] tuser_d0, tuser_d1, tuser_d2, tuser_d3;\n')

        fh.write('assign m_axis_tdata = comb_out;\n')
        fh.write('assign m_axis_tvalid = tvalid_d[3];\n')
        if tlast:
            fh.write('assign m_axis_tlast = tlast_d[3];\n')
        if tuser_width > 0:
            fh.write('assign m_axis_tuser = tuser_d3;\n')
        if depth_bits > m_bits:
            bit_diff = depth_bits - m_bits
            fh.write('assign msetting_s = {{%d{1\'b0}}, msetting};\n' % bit_diff)
        else:
            fh.write('assign msetting_s = msetting;\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    c_d0 <= s_axis_tdata;\n')
        fh.write('    c_d1 <= c_d0;\n')
        fh.write('    c_d2 <= c_d1;\n')
        if tlast:
            fh.write('  	tlast_d <= {tlast_d[2:0], s_axis_tlast};\n')
        if tuser_width > 0:
            fh.write('      tuser_d0 <= tuser_s;\n')
            fh.write('      tuser_d1 <= tuser_d0;\n')
            fh.write('      tuser_d2 <= tuser_d1;\n')
            fh.write('      tuser_d3 <= tuser_d2;\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('//Latency 1\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        tvalid_d <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        tvalid_d <= {tvalid_d[2:0], tvalid_s};\n')
        fh.write('	end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('// Differential Delay. Latency = 3.\n')
        # implement fifo

        print('comb fifo = {}'.format(fifo_name))
        axi_fifo_inst(fh, fifo_name, inst_name='u_diff_delay', data_width=48, af_thresh=None, max_delay=depth,
                      addr_width=addr_bits, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='s_axis_tvalid',
                      s_tdata_str='s_axis_tdata', s_tuser_str='s_axis_tuser', s_tlast_str='s_axis_tlast', delay_str='msetting_s',
                      s_tready_str='', almost_full_str=None, m_tvalid_str='tvalid_s', m_tdata_str='diff_delay',
                      m_tuser_str='tuser_s', m_tlast_str='tlast_s', m_tready_str='1\'b1')


        fh.write('\n')

        # funcs = 'c-concat'
        # mod_name = 'comb'
        # (comb_dsp_file, comb_dsp_name) = gen_dsp48E1(path, mod_name, opcode=funcs, areg=2, breg=2, creg=3,
        #                                              concatreg=3, preg=1, use_ce=False)

        fh.write('// Latency = 4.\n')
        fh.write('// EQ : C - CONCAT\n')

        fh.write('{} u_dsp (\n'.format(dsp_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .c(c_d2), \n')
        fh.write('  .concat(diff_delay), \n')
        fh.write('  .p(comb_out) \n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('endmodule\n')
        fh.close()

    return (file_name, module_name)


def gen_cic_top(path, cic_obj, count_val=1024, qvec_correction=None, prefix='', slice_shift=0,
                max_input=None, tlast=False, tuser_width=0):

    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)
    cic_order = cic_obj.N
    input_width = cic_obj.input_width
    output_width = cic_obj.output_width
    max_diff_delay = cic_obj.M
    max_decimation = cic_obj.r_max
    hash = 0
    if tlast:
        hash += 1
    if tuser_width > 0:
        hash += 2

    module_name = '{}cic_M{}_N{}_R{}_iw{}_{}'.format(prefix, max_diff_delay, cic_order, max_decimation, input_width, hash)
    file_name = name_help(module_name, path)
    if qvec_correction is None:
        qvec_correction = cic_obj.qvec_out

    qvec_msb = qvec_correction[0] - 1

    r_bits = ret_num_bitsU(max_decimation)
    m_bits = ret_num_bitsU(max_diff_delay)

    input_msb = input_width - 1
    output_msb = output_width - 1

    b_max = cic_obj.ret_bmax()
    b_trunc = cic_obj.ret_btrunc(b_max)

    rom_width = qvec_correction[0]
    rom_msb = rom_width - 1

    slice_bits = ret_num_bitsU(b_trunc)
    count_bits = ret_num_bitsU(count_val)
    corr_bits_out = input_width + rom_width
    (corr_gain_fi, offset_fi) = cic_obj.gen_tables()

    if cic_obj.m_max == cic_obj.m_min and cic_obj.r_min == cic_obj.r_max:
        # then only adjusting rate
        rom_sig = '0'
        rom_bits = 1
    elif cic_obj.m_max == cic_obj.m_min:
        rom_sig = 'rate'
        rom_bits = r_bits
    elif cic_obj.r_min == cic_obj.r_max:
        rom_sig = 'msetting'
        rom_bits = m_bits
    else:
        rom_sig = '{msetting, rate}'
        rom_bits = m_bits + r_bits

    int_delay = 5  # 4 for the DSP48 + 1 for ZEROS logic.
    comb_delay = 7
    down_delay = 0
    if cic_obj.r_max > 1:
        down_delay = 1

    int_tot_delay = cic_order * int_delay  # includes muxes.
    comb_tot_delay = cic_order * comb_delay
    delay_slice = 1 + 4  # 1 for slicer 4 for correction multiplier.
    total_delay = int_tot_delay + comb_tot_delay + down_delay + delay_slice #analysis:ignore
    print('total latency = {}'.format(total_delay))
    corr_name = module_name + '_corr'

    funcs = ['CONCAT+P', '0']
    (_, int_name) = gen_dsp48E1(path, module_name, opcode=funcs, creg=0, concatreg=3, use_ce=False)
    (_, corr_rom_name) = gen_rom(path, corr_gain_fi, rom_type='sp', rom_style='block', prefix='{}_correction_'.format(module_name))
    (_, offset_name) = gen_rom(path, offset_fi, rom_type='sp', rom_style='distributed', prefix='{}_offset_'.format(module_name))
    (_, corr_name) = gen_dsp48E1(path, corr_name, opcode='A*B', a_width=output_width, b_width=rom_width, areg=2, breg=2, b_signed=False)
    (_, slicer_name) = gen_slicer(path, input_width=48, output_width=output_width, max_offset=np.max(offset_fi.vec), rev_dir=False)
    (_, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, tlast=tlast, almost_full=True, ram_style='block')

    print(corr_rom_name)
    print(offset_name)
    print(fifo_name)
    print(corr_name)

    addr_width = ret_num_bitsU(2 * total_delay)
    fifo_depth = 1 << addr_width
    af_thresh = fifo_depth - total_delay - 5
    _, comb_name = gen_comb(path, cic_obj, prefix=prefix, tuser_width=tuser_width, tlast=tlast)
    print(comb_name)
    downsamp_name = None
    if cic_obj.r_max > 1:
        downsamp_name = vhdl_gen.gen_axi_downsample(path)
        print(downsamp_name)

    # generate final fifo to create a fully axi compliant interface
    with open(file_name, 'w') as fh:
        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : PJV\n')
        fh.write('// File        : {}\n'.format(module_name))
        fh.write('// Description : CIC Filter module with gain correction and output slicer.\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('\n')
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        if tuser_width:
            fh.write('#(parameter TUSER_WIDTH=8)\n')
        fh.write('(\n')
        fh.write('  input sync_reset, // reset\n')
        fh.write('  input clk,\n')
        fh.write('\n')
        fh.write('  input [{}:0] msetting,\n'.format(m_bits - 1))
        if max_decimation > 1:
            fh.write('  input [{}:0] rate,\n'.format(r_bits - 1))
        fh.write('\n')
        fh.write('  input s_axis_tvalid,\n')
        fh.write('  input [{}:0] s_axis_tdata, \n'.format(input_msb))
        fh.write('\n')
        if tlast:
            fh.write('  input s_axis_tlast,\n')
        if tuser_width > 0:
            fh.write('  input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        fh.write('  output s_axis_tready,')
        fh.write('\n')
        fh.write('  output m_axis_tvalid,\n')
        fh.write('  output [{}:0] m_axis_tdata,\n'.format(output_msb))
        if tuser_width:
            fh.write('  output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        if tlast:
            fh.write(' output m_axis_tlast,\n')
        fh.write('  input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')

        fh.write('wire [{}:0] corr_factor;\n'.format(rom_msb))
        fh.write('wire [{}:0] slice_out_s;\n'.format(output_msb))
        fh.write('wire [{}:0] slice_offset;\n'.format(slice_bits - 1))
        fh.write('\n')
        # fh.write('reg valid_d;\n')
        fh.write('wire [47:0] input_signal;\n')
        fh.write('wire [{}:0] signal_d;\n'.format(output_msb))
        fh.write('wire [0:0] reset;\n')
        fh.write('wire almost_full;\n')
        if cic_obj.r_max > 1:
            fh.write('wire [{}:0] rate_s;\n'.format(r_bits - 1))
            fh.write('localparam [{}:0] RATE_ZERO := 0;\n')
            # str1 = '0' * (r_bits - 1)
            fh.write('localparam [{}:0] RATE_ONE := 1;\n'.format(r_bits-1))
        fh.write('\n')
        for ii in range(cic_order):
            fh.write('reg [47:0] int_signal_{};\n'.format(ii))

        for ii in range(cic_order):
            fh.write('wire [47:0] int_out_signal_{};\n'.format(ii))

        for ii in range(int_tot_delay):
            fh.write('reg int_valid_d{:d};\n'.format(ii))

        if tlast:
            for ii in range(int_tot_delay):
                fh.write('reg int_tlast_d{:d};\n'.format(ii))

        if tuser_width > 0:
            for ii in range(int_tot_delay):
                fh.write('reg [TUSER_WIDTH-1:0] int_tuser_d{:d};\n'.format(ii))

        if cic_obj.r_max > 1:
            fh.write('wire [47:0] down_signal;\n')
            fh.write('wire down_valid;\n')
            if tlast:
                fh.write('wire down_tlast;\n')

        for ii in range(cic_order + 1):
            fh.write('wire [47:0] comb_signal_{};\n'.format(ii))

        fh.write('\n')
        for ii in range(cic_order + 1):
            fh.write('wire comb_valid_{};\n'.format(ii))

        if tlast:
            for ii in range(cic_order + 1):
                if ii == 0:
                    fh.write('wire comb_tlast_{};\n'.format(ii))
                else:
                    fh.write('reg comb_tlast_{};\n'.format(ii))

        if tuser_width > 0:
            for ii in range(cic_order + 1):
                if ii == 0:
                    fh.write('wire [TUSER_WIDTH-1:0] comb_tuser_{};\n'.format(ii))
                else:
                    fh.write('reg [TUSER_WIDTH-1:0] comb_tuser_{};\n'.format(ii))

        if tlast:
            for ii in range(delay_slice):
                fh.write('reg slice_tlast_d{:d};\n'.format(ii))

        if tuser_width > 0:
            for ii in range(delay_slice):
                fh.write('reg [TUSER_WIDTH-1:0] slice_tuser_d{:d};\n'.format(ii))

        fh.write('wire slice_valid;\n')
        for ii in range(delay_slice):
            fh.write('reg slice_valid_d{};\n'.format(ii))

        fh.write('\n')
        fh.write('reg [{}:0] count, next_count;\n'.format(count_bits - 1))
        fh.write('\n')
        fh.write('wire [47:0] signal_out_s;\n')
        fh.write('\n')

        frac_width = qvec_correction[1] + cic_obj.qvec_in[1]
        num_int_bits = cic_obj.qvec_in[0] - cic_obj.qvec_in[1]
        # final result should have same number of integer bits as the input
        lidx = frac_width + num_int_bits - 1  # -1 -> want msb.
        ridx = lidx - output_width + 1
        fh.write('assign reset[0] = sync_reset;\n')
        fh.write('assign s_axis_tready = ~almost_full;\n')
        fh.write('assign signal_d = signal_out_s[{}:{}];\n'.format(lidx, ridx))
        pad_bits = 48 - input_width
        fh.write('assign input_signal = {{{{{}{{s_axis_tdata[{}]}}}},s_axis_tdata}};\n'.format(pad_bits, input_msb))

        if cic_obj.r_max > 1:
            fh.write('assign comb_valid_0 = down_valid;\n')
            fh.write('assign comb_signal_0 = down_signal;\n')
            if tlast:
                fh.write('assign comb_tlast_0 = down_tlast;\n')
            if tuser_width > 0:
                fh.write('assign comb_tuser_0 = down_tuser;\n')

        else:
            fh.write('assign comb_valid_0 = int_valid_d{};\n'.format(int_tot_delay - 1))
            fh.write('assign comb_signal_0 = int_out_signal_{};\n'.format(cic_order - 1))
            if tlast:
                fh.write('assign comb_tlast_0 = int_tlast_d{};\n'.format(int_tot_delay - 1))
            if tuser_width > 0:
                fh.write('assign comb_tuser_0 = int_tuser_d{};\n'.format(int_tot_delay - 1))


        fh.write('\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        for ii in range(cic_order):
            offset = ii * int_delay - 1
            fh.write('   // Logic ensures that the integrators do not integrate stale values\n')
            # analysis:ignore
            if ii == 0:
                str_val = 'if (s_axis_tvalid == 1\'b1 && almost_full == 1\'b0) begin\n'
            else:
                str_val = 'if (int_valid_d{} == 1\'b1) begin\n'.format(offset)
            fh.write('    {}'.format(str_val))
            if ii == 0:
                fh.write('		int_signal_{} <= input_signal;\n'.format(ii))
            else:
                fh.write('		int_signal_{} <= int_out_signal_{};\n'.format(ii, ii))
            fh.write('    end else begin\n')
            fh.write('        int_signal_{} <= 0;\n'.format(ii))
            fh.write('    end\n')
            fh.write('\n')
        fh.write('end\n')
        fh.write('\n')

        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('  if (slice_valid_d{:d} == 1\'b1 && count != 0) begin\n'.format(delay_slice - 2))
        fh.write('    next_count = count - 1;\n')
        fh.write('  end else begin\n')
        fh.write('    next_count = count;\n')
        fh.write('  end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('  int_valid_d0 <= s_axis_tvalid & ~almost_full;\n')
        for ii in range(1, int_tot_delay):
            fh.write('  int_valid_d{} <= int_valid_d{};\n'.format(ii, ii - 1))
        if tlast:
            fh.write('  int_tlast_d0 <= s_axis_tlast;\n')
            for ii in range(1, int_tot_delay):
                fh.write('  int_tlast_d{} <= int_tlast_d{};\n'.format(ii, ii - 1))

        if tuser_width > 0:
            fh.write('  int_tuser_d0 <= s_axis_tuser;\n')
            for ii in range(1, int_tot_delay):
                fh.write('  int_tuser_d{} <= int_tuser_d{};\n'.format(ii, ii - 1))
        fh.write('end\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    slice_valid_d0 <= comb_valid_{};\n'.format(cic_order))
        if tlast:
            fh.write('    slice_tlast_d0 <= comb_tlast_{};\n'.format(cic_order))
        if tuser_width > 0:
            fh.write('    slice_tuser_d0 <= comb_tuser_{};\n'.format(cic_order))
        for ii in range(1, delay_slice - 1):
            fh.write('    slice_valid_d{} <= slice_valid_d{};\n'.format(ii, ii - 1))
        if tlast:
            for ii in range(1, delay_slice):
                fh.write('    slice_tlast_d{} <= slice_tlast_d{};\n'.format(ii, ii - 1))
        if tuser_width > 0:
            for ii in range(1, delay_slice):
                fh.write('    slice_tuser_d{} <= slice_tuser_d{};\n'.format(ii, ii - 1))
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('//Latency 1\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('  if (sync_reset == 1\'b1) begin\n')
        fh.write('      slice_valid_d{} <= 0;\n'.format(delay_slice-1))
        fh.write('      count <= {};\n'.format(count_val))
        if cic_obj.r_max > 1:
            fh.write('      rate_s <= rate;\n')
        fh.write('  end else begin\n')
        fh.write('      if (slice_valid_d{} == 1\'b1) begin\n'.format(delay_slice - 2))
        fh.write('          if (count == 0) begin\n')
        fh.write('              slice_valid_d{} <= 1\'b1;\n'.format(delay_slice - 1))
        fh.write('          end else begin\n')
        fh.write('              count <= count - 1;\n')
        fh.write('          end\n')
        fh.write('      end else begin\n')
        fh.write('          slice_valid_d{} <= 1\'b0;\n'.format(delay_slice - 1))
        fh.write('      end\n')
        if cic_obj.r_max > 1:
            fh.write('      if (rate == 0 || rate = 1) begom\n')
            fh.write('          rate_s <= rate;\n')
            fh.write('      end else begin\n')
            fh.write('          rate_s <= rate - 1);\n')
            fh.write('      end\n')
        fh.write('	end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('//latency = 4.\n')
        for ii in range(cic_order):
            name = 'integrator_section_{}'.format(ii)
            fh.write('{} {} (\n'.format(int_name, name))
            fh.write('  .clk(clk), // input clk\n')
            fh.write('  .opcode(reset),\n')
            fh.write('  .concat(int_signal_{}),\n'.format(ii))
            fh.write('  .p(int_out_signal_{})\n'.format(ii))
            fh.write(');\n')
            fh.write('\n')
        # put in decimator here.
        if cic_obj.r_max > 1:
            fh.write('{}\n'.format(downsamp_name))
            fh.write('#(   .DATA_WIDTH(48),\n')
            if tuser_width > 0:
                fh.write('   .TUSER_WIDTH({}),\n'.format(tuser_width))
            fh.write('   .CNT_BITS({}))\n'.format(r_bits))
            fh.write('u_downsample \n')
            fh.write('(\n')
            fh.write('   .clk(clk),\n')
            fh.write('   .sync_reset(sync_reset),\n')
            fh.write('   .s_axis_tvalid(int_valid_d{}),\n'.format(cic_order - 1))
            if tlast:
                fh.write('   .s_axis_tlast(int_tlast_d{}),\n'.format(int_tot_delay))
            if tuser_width > 0:
                fh.write('   .s_axis_tuser(int_tuser_d{}),\n'.format(int_tot_delay))
            fh.write('   .s_axis_tdata(int_out_signal_{}),\n'.format(cic_order - 1))
            fh.write('   .s_axis_tready(),\n')
            fh.write('   .rate(rate),\n')
            fh.write('   .m_axis_tvalid(down_valid),\n')
            if tlast:
                fh.write('   .m_axis_tlast(down_tlast),\n')
            if tuser_width > 0:
                fh.write('   .m_axis_tlast(down_user),\n')

            fh.write('   .m_axis_tdata(down_signal)\n')
            fh.write('   .m_axis_tready(1\'b1)\n')
            fh.write(');\n')

        fh.write('\n')
        for ii in range(cic_order):
            fh.write('//latency = 10.\n')
            name = 'comb_section_{}'.format(ii)
            if tuser_width > 0:
                fh.write('{}\n'.format(comb_name))
                fh.write('   .TUSER_WIDTH({})),\n'.format(tuser_width))
                fh.write('{}\n'.format(name))
            else:
                fh.write('{} {}\n'.format(comb_name, name))
            fh.write('(\n')
            fh.write('  .clk(clk), \n')
            fh.write('  .sync_reset(sync_reset),\n')
            fh.write('  .msetting(msetting),\n')
            fh.write('  .s_axis_tvalid(comb_valid_{}),\n'.format(ii))
            fh.write('  .s_axis_tdata(comb_signal_{}),\n'.format(ii))
            if tlast:
                fh.write('   .s_axis_tlast(comb_tlast_{}),\n'.format(ii))
            if tuser_width > 0:
                fh.write('   .s_axis_tuser(comb_tuser_{}),\n'.format(ii))

            fh.write('  .m_axis_tvalid(comb_valid_{}),\n'.format(ii + 1))
            if tlast:
                fh.write('   .m_axis_tlast(comb_tlast_{}),\n'.format(ii + 1))
            if tuser_width > 0:
                fh.write('   .m_axis_tuser(comb_tuser_{}),\n'.format(ii + 1))
            fh.write('  .m_axis_tdata(comb_signal_{})\n'.format(ii + 1))
            fh.write(');\n')
            fh.write('\n')

        fh.write('\n')
        fh.write('\n')
        fh.write('{} offset_rom (\n'.format(offset_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .addra({}),\n'.format(rom_sig))
        fh.write('  .doa(slice_offset)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// Latency 1\n')
        fh.write('{} slicer (\n'.format(slicer_name))
        fh.write('  .clk(clk), // clock\n')
        fh.write('  .sync_reset(sync_reset), // reset\n')
        fh.write('\n')
        fh.write('  .slice_offset_i(slice_offset),\n')
        fh.write('  // offset is relative to the base value\n')
        fh.write('\n')
        fh.write('  .valid_i(comb_valid_{}),\n'.format(cic_order))
        fh.write('  .signal_i(comb_signal_{}),\n'.format(cic_order))
        fh.write('\n')
        fh.write('  .valid_o(slice_valid),\n')
        fh.write('  .signal_o(slice_out_s)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('{} corr_factor_rom (\n'.format(corr_rom_name))
        fh.write('  .clk(clk), \n')
        fh.write('  .addra(msetting),\n')
        fh.write('  .doa(corr_factor)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('//Latency = 4\n')
        fh.write('{} correction_multiplier (\n'.format(corr_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .a(slice_out_s),\n')
        fh.write('  .b(corr_factor),\n')
        fh.write('  .p(signal_out_s)\n')
        fh.write(');\n')

        fh.write('\n')
        axi_fifo_inst(fh, fifo_name, inst_name='u_fifo', data_width=output_width, af_thresh=af_thresh,
                      addr_width=addr_width, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='slice_valid_d{}'.format(delay_slice-1),
                      s_tdata_str='signal_d', s_tuser_str='slice_tuser_d({})'.format(delay_slice-1), s_tlast_str='slice_tlast_d({})'.format(delay_slice-1),
                      s_tready_str='', almost_full_str='almost_full', m_tvalid_str='m_axis_tvalid', m_tdata_str='m_axis_tdata',
                      m_tuser_str='m_axis_tuser', m_tlast_str='m_axis_tlast', m_tready_str='m_axis_tready')

        fh.write('\n')
        fh.write('endmodule\n')


    return (file_name, module_name, )
