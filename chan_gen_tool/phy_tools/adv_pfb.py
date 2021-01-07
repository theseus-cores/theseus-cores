#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Wed Sept 25 7:09:28 2019

@author: phil
"""

import numpy as np
from phy_tools.gen_utils import ret_module_name, ret_valid_path
from phy_tools.vgen_xilinx import gen_dsp48E1, gen_dsp48E2
from phy_tools.verilog_gen import gen_ram, gen_axi_fifo, name_help, gen_rom, axi_fifo_inst
from phy_tools.verilog_gen import gen_pipe_mux
from phy_tools import fp_utils
from phy_tools.fp_utils import ret_num_bitsU, bin_to_udec
from collections import OrderedDict

from IPython.core.debugger import set_trace

import os
import ipdb

from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError: 
    from datetime import date                                                                        
    today = date.today()                                                                                
    __version__ = today.strftime("%Y.%m.%d")
    
chan_dict = OrderedDict([(8, 32), (16, 16), (32, 16), (64, 8), (128, 4), (256, 4), (512, 2)])

def ret_offset(chan_dict, chan_number):

    chan_prop_dict = calc_bit_widths(chan_dict)
    chan_str = chan_prop_dict['Sub Chan Map'][chan_number]
    sub_chan_offset = chan_prop_dict['Sub Chan Offset'][chan_number]
    prefix = chan_str[:len([True for value in chan_str if value == '1'])]
    chan_bits = len([True for value in chan_str if value == 'C'])
    phase_bits = len([True for value in chan_str if value == 'x'])

    offset = bin_to_udec(prefix) << (phase_bits + chan_bits)
    # find offset
    offset += sub_chan_offset << phase_bits
    return offset

def calc_bit_widths(chan_dict=chan_dict):
    # sort dictionary
    sorted_keys = sorted(chan_dict.keys())
    chan_dict_s = OrderedDict([(key, chan_dict[key]) for key in sorted_keys])

    num_fft_sizes = len(chan_dict_s)
    num_channels = 0
    Mmax = 0
    taps_per_column = 0
    comb_bits = []
    num_addrs = []

    for value in chan_dict_s.items():
        num_channels += value[1]
        Mmax = value[0] if value[0] > Mmax else Mmax
        temp = ret_num_bitsU(value[1] - 1) + ret_num_bitsU(value[0] - 1)
        comb_bits.append(temp)
        num_addrs.append(value[0] * value[1])
        taps_per_column += value[0]

    addr_space = np.sum(num_addrs)
    addr_bits = ret_num_bitsU(addr_space - 1)
    tap_bits = ret_num_bitsU(taps_per_column - 1)
    phase_bits = ret_num_bitsU(np.max([*chan_dict_s]))

    # determine samp_addr map.
    curr_count = None
    old_width = None
    map_vec = []
    for curr_depth in num_addrs:
        curr_width = ret_num_bitsU(curr_depth - 1)
        map_bits = addr_bits - curr_width
        format_str = '0{}b'.format(map_bits)
        if curr_count is None:
            curr_count = 2 ** map_bits - 1
            old_width = map_bits
        else:
            if old_width == map_bits:
                curr_count -= 1
            else:
                curr_count = (curr_count >> 1) - 1
                old_width = map_bits

        map_vec.append(format(curr_count, format_str))

    # generate sub_chan map
    offset = 0
    offset_map = []
    sub_chan_bits = []
    phase_bits = []
    for i, (key, value) in enumerate(chan_dict_s.items()):
        offset_map.append(offset)
        temp = ret_num_bitsU(value - 1)
        sub_chan_bits.append(temp)
        phase_bits.append(addr_bits - temp - len(map_vec[i]))
        offset += value

    chan_map = []
    sub_chan_map = []
    sub_chan_offset = []
    addr_prepend = []
    for chan_num in range(num_channels):
        # index of offset that is <= chan_num
        idx = len([True for value in offset_map if value <= chan_num]) - 1
        temp = map_vec[idx] + 'C'*sub_chan_bits[idx] + 'x'*phase_bits[idx]
        chan_map.append(idx)
        addr_prepend.append(map_vec[idx])
        sub_chan_map.append(temp)
        sub_chan_offset.append(chan_num - offset_map[idx])

    ret_dict = {'Num Channels': num_channels, 'Mmax': Mmax, 'Addr Bits': addr_bits, 'Map Vec': map_vec, 'Tap Bits': tap_bits,
                'Chan Dict': chan_dict_s, 'Offset Map': offset_map, 'Sub Chan Map': sub_chan_map, 'Phase Bits': phase_bits,
                'Chan Map': chan_map, 'Sub Chan Offset': sub_chan_offset, 'FFT Bits': phase_bits,
                'Addr Prepend': addr_prepend, 'Sub Chan Bits': sub_chan_bits}

    return ret_dict
    # return num_channels, Mmax, addr_bits, map_vec, tap_bits, chan_dict, offset_map, chan_map, phase_bits

def pipe_helper(fh, push_idx, mod_latency, name='num_phases'):
    fh.write('//{}_pipe_proc\n'.format(name))
    fh.write('integer j;\n')
    fh.write('always @*\n')
    fh.write('begin\n')
    fh.write('    next_{}_d[0] = {};\n'.format(name, name))
    fh.write('    for (j=1; j<{}; j=j+1) begin\n'.format(push_idx + 1))
    fh.write('        next_{}_d[j] = {}_d[j-1];\n'.format(name, name))
    fh.write('    end;\n')
    fh.write('    if (tvalid_d[{}] == 1\'b1) begin\n'.format(push_idx))
    fh.write('        for (j={}; j<{}; j=j+1) begin\n'.format(push_idx + 1, mod_latency))
    fh.write('            next_{}_d[j] = {}_d[j-1];\n'.format(name, name))
    fh.write('        end;\n')
    fh.write('    end else begin\n')
    fh.write('        for (j={}; j<{}; j=j+1) begin\n'.format(push_idx + 1, mod_latency))
    fh.write('            next_{}_d[j] = {}_d[j];\n'.format(name, name))
    fh.write('        end;\n')
    fh.write('    end\n')
    fh.write('end\n')

def reset_helper(fh, mod_latency, name='num_phases'):
    fh.write('        for (m=0; m<{}; m=m+1) begin\n'.format(mod_latency))
    fh.write('            {}_d[m] <= 0;\n'.format(name))
    fh.write('        end\n')

def reg_helper(fh, mod_latency, name='num_phases'):
    fh.write('        for (m=0; m<{}; m=m+1) begin\n'.format(mod_latency))
    fh.write('            {}_d[m] <= next_{}_d[m];\n'.format(name, name))
    fh.write('        end\n')

def gen_pfb(path, Mmax, rom_fi, input_width=16, output_width=16, taps_per_phase=24, interp_fil=False,
            pfb_msb=40, tlast=False, tuser_width=0, ram_style='block', prefix='', gen_2X=False, dsp48e2=False,
            count_dn=False):

    tap_width = rom_fi.word_length
    path = ret_valid_path(path)
    assert(path is not None), 'User must specify directory'
    if gen_2X:
        file_name = '{}pfb_2x_{}Mmax_{}iw_{}ow_{}tps.v'.format(prefix, Mmax, input_width, output_width, taps_per_phase)
    else:
        file_name = '{}pfb_{}Mmax_{}iw_{}ow_{}tps.v'.format(prefix, Mmax, input_width, output_width, taps_per_phase)
    file_name = os.path.join(path, file_name)
    module_name = ret_module_name(file_name)

    phase_bits = ret_num_bitsU(Mmax - 1)
    phase_msb = np.max((0, phase_bits - 1))
    mem_msb = phase_msb + 1 + gen_2X
    word_msb = input_width * 2 - 1
    out_msb = output_width * 2 - 1
    taps_msb = tap_width - 1
    we_bits = ret_num_bitsU(taps_per_phase - 1)
    taps_addr_msb = phase_msb + we_bits
    addr_bits = phase_bits + 1 + gen_2X
    addr_msb = addr_bits - 1
    ram_depth = 2 ** addr_bits
    ram_width = input_width * 2
    phase_depth = 2 ** phase_bits

    rnd_latency = 0 if dsp48e2 else 1

    samp_latency = 1 + (3 * gen_2X)
    ram_latency = 3
    arm_latency = taps_per_phase + 6 + rnd_latency
    tvalid_len = samp_latency + ram_latency + rnd_latency
    mod_latency = arm_latency + samp_latency
    pfb_lsb = pfb_msb - output_width + 1


    delay_name = gen_ram(path, ram_type='dp', memory_type='read_first', ram_style=ram_style)
    if interp_fil:
        ram_name = gen_ram(path, ram_type='dp', memory_type='read_first', ram_style='distributed')
    else:
        ram_name = gen_ram(path, ram_type='dp', memory_type='read_first', ram_style=ram_style)

    tap_ram_name = gen_ram(path, ram_type='dp', memory_type='write_first', ram_style=ram_style)
    mem_ctrl_name = gen_mem_ctrl(path, '{}'.format(module_name), rom_fi, num_taps=taps_per_phase)
    _, fifo_name = gen_axi_fifo(path, tuser_width=tuser_width, tlast=tlast, almost_full=True, ram_style='block', prefix='')
    rnd_name = None
    if dsp48e2:
        _, dsp_name0 = gen_dsp48E2(path, name=prefix + 'pfb_mac_0', opcode='A*B', a_width=25, b_width=input_width, areg=2, breg=2, mreg=1, preg=1, use_ce=True, use_pcout=True)
        _, dsp_name = gen_dsp48E2(path, name=prefix + 'pfb_mac', opcode='PCIN+A*B', a_width=25, b_width=input_width, areg=2, breg=2, mreg=1, preg=1, use_ce=True, use_pcout=True)
        if pfb_lsb > 0:
            _, rnd_name = gen_dsp48E2(path, name=prefix + 'pfb_rnd', opcode='PCIN+A*B', a_width=25, b_width=input_width, use_ce=True, rnd=True, p_msb=pfb_msb, p_lsb=pfb_lsb, creg=0, preg=1)
    else:
        _, dsp_name0 = gen_dsp48E1(path, name=prefix + 'pfb_mac_0', opcode='A*B', a_width=25, b_width=input_width, areg=2, breg=2, mreg=1, preg=1, use_ce=True, use_pcout=True)
        _, dsp_name = gen_dsp48E1(path, name=prefix + 'pfb_mac', opcode='PCIN+A*B', a_width=25, b_width=input_width, areg=2, breg=2, mreg=1, preg=1, use_ce=True, use_pcout=True)
        if pfb_lsb > 0:
            _, rnd_name = gen_dsp48E1(path, name=prefix + 'pfb_rnd', opcode='PCIN', a_width=25, b_width=input_width, use_ce=True, rnd=True, p_msb=pfb_msb, p_lsb=pfb_lsb, creg=0, preg=1)

    if pfb_lsb <= 0:
        rnd_name = dsp_name

    with open(file_name, "w") as fh:
        m_text = 'M/2' if gen_2X else 'M'
        fh.write('/*****************************************************************************/\n')
        fh.write('// Implements the {} PFB architecture referenced in the\n'.format(m_text))
        fh.write('// "A Versatile Multichannel Filter Bank with Multiple Channel Bandwidths" paper.\n')
        fh.write('// This architecture has been mapped to the Xilinx architecture.\n')
        fh.write('// This represents a fully pipelined design that maximizes the FMax potential of the design.\n')
        fh.write('// It is important to understand that filter arms are loaded sequentially. This is referenced in\n')
        fh.write('// the diagram by the incremental changes in the phase subscript through each subsequent delay\n')
        fh.write('// register. The nth index is only updated once per revolution of the filter bank.\n')
        fh.write('//\n')
        fh.write('// It is best to refer to the attached document to understand the layout of the logic. This module\n')
        fh.write('// currently implements {} taps per phase.\n'.format(taps_per_phase))
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        if tuser_width:
            fh.write('module {} #( \n'.format(module_name))
            fh.write('    parameter TUSER_WIDTH=32)\n')
        else:
            fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input [{}:0] num_phases,\n'.format(phase_bits))
        fh.write('    input [{}:0] phase,\n'.format(phase_msb))
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [{}:0] s_axis_tdata,\n'.format(word_msb))
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        if tuser_width:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    input s_axis_reload_tvalid,\n')
        fh.write('    input [31:0] s_axis_reload_tdata,\n')
        fh.write('    input s_axis_reload_tlast,\n')
        fh.write('    output s_axis_reload_tready,\n')
        fh.write('\n')
        fh.write('    output [{}:0] phase_out,\n'.format(phase_msb))
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [{}:0] m_axis_tdata,\n'.format(out_msb))
        if tlast:
            fh.write('    output m_axis_tlast,\n')
        if tuser_width:
            fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        if tuser_width > 0:
            fh.write('localparam TUSER_MSB = TUSER_WIDTH - 1;\n')
        fh.write('wire [{}:0] taps[0:{}];\n'.format(taps_msb, taps_per_phase - 1))
        fh.write('wire [47:0] pcouti[0:{}];\n'.format(taps_per_phase - 1 - dsp48e2))
        fh.write('wire [47:0] pcoutq[0:{}];\n'.format(taps_per_phase - 1 - dsp48e2))
        fh.write('wire [{}:0] pouti, poutq;\n'.format(output_width - 1))
        fh.write('\n')
        fh.write('wire [{}:0] delay[0:{}];\n\n'.format(word_msb, taps_per_phase - 1))
        if gen_2X:
            fh.write('wire [{}:0] delay_sig;\n'.format(word_msb))
            fh.write('reg [{}:0] phase_mux_d[0:2];\n'.format(phase_msb))
            fh.write('reg [{}:0] input_sig_d1, input_sig_d2, input_sig_d3;\n'.format(word_msb))
            fh.write('wire bot_half;\n')
            fh.write('\n')
        fh.write('reg [{}:0] phase_d[0:{}];\n'.format(phase_msb, arm_latency - 1))
        fh.write('reg [{}:0] tvalid_d;\n'.format(tvalid_len - 1))
        fh.write('reg [{}:0] tvalid_pipe, next_tvalid_pipe;\n'.format(mod_latency-1))
        if tlast:
            fh.write('reg [{}:0] tlast_d, next_tlast_d;\n'.format(mod_latency - 1))
        if tuser_width:
            fh.write('reg [TUSER_MSB:0] tuser_d[0:{}];\n'.format(mod_latency - 1))
        fh.write('\n')
        fh.write('reg [{}:0] wr_addr_d[0:{}];\n'.format(mem_msb, taps_per_phase * 3 - 1))
        fh.write('\n')
        fh.write('reg [{}:0] sig, next_sig;\n'.format(word_msb))
        fh.write('reg [{}:0] sig_d1, sig_d2, sig_d3;\n'.format(word_msb))
        fh.write('reg [{}:0] rd_addr, next_rd_addr;\n'.format(mem_msb))
        fh.write('reg [{}:0] wr_addr, next_wr_addr;\n'.format(mem_msb))
        fh.write('reg [{}:0] rd_addr_d[0:{}];\n'.format(mem_msb, taps_per_phase - 2))
        fh.write('\n')
        fh.write('reg [{}:0] next_rd_addr_d[0:{}];\n'.format(mem_msb, taps_per_phase - 2))
        fh.write('\n')
        fh.write('reg [{}:0] offset_cnt, next_offset_cnt;\n'.format(int(gen_2X)))
        fh.write('reg [{}:0] offset_cnt_prev, next_offset_cnt_prev;\n'.format(int(gen_2X)))
        fh.write('\n')
        fh.write('wire [{}:0] rom_addr;\n'.format(phase_msb))
        fh.write('wire [{}:0] rom_data;\n'.format(tap_width-1))
        fh.write('wire [{}:0] rom_we;\n'.format(taps_per_phase-1))
        fh.write('\n')
        fh.write('reg [{}:0] phase_max;\n'.format(phase_bits))
        fh.write('reg [{}:0] phase_max_slice;\n'.format(phase_msb))
        if gen_2X:
            fh.write('reg [{}:0] phase_half;\n'.format(phase_msb))
        fifo_width = 2 * output_width + phase_bits
        fh.write('wire [{}:0] fifo_tdata, m_axis_tdata_s;\n'.format(fifo_width-1))
        fh.write('wire fifo_tvalid;\n')
        fh.write('wire almost_full;\n')
        fh.write('wire take_data;\n')
        fh.write('\n')
        fh.write('assign take_data = (s_axis_tvalid & ~almost_full);\n')
        fh.write('assign m_axis_tdata = m_axis_tdata_s[{}:{}];\n'.format(fifo_width-1, phase_bits))
        fh.write('assign s_axis_tready = ~almost_full;\n')
        fh.write('assign fifo_tvalid = tvalid_d[{}] & tvalid_pipe[{}];\n'.format(tvalid_len - 1, mod_latency - 1))
        fh.write('assign phase_out = m_axis_tdata_s[{}:0];\n'.format(phase_bits - 1))
        fh.write('assign fifo_tdata = {{pouti, poutq, phase_d[{}]}};\n'.format(arm_latency - 1))
        if gen_2X:
            fh.write('assign bot_half = ((phase_mux_d[2] & phase_half[{}:0]) != 0) ? 1\'b1 : 1\'b0;\n'.format(phase_msb))
        fh.write('\n')
        fh.write('\n')
        fh.write('// logic implements the sample write address pipelining.\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('\n')
        fh.write('    phase_max <= num_phases - 1;\n')
        fh.write('    phase_max_slice <= phase_max[{}:0];\n'.format(phase_msb))
        if gen_2X:
            fh.write('    phase_half <= num_phases >> 1;\n')
        fh.write('\n')
        # need to compute subtraction.
        if gen_2X:
            fh.write('    phase_mux_d[0] <= phase;\n')
            fh.write('    phase_mux_d[1] <= phase_mux_d[0];\n')
            fh.write('    phase_mux_d[2] <= phase_mux_d[1] & phase_max_slice;\n')
            fh.write('\n')
            fh.write('    input_sig_d1 <= s_axis_tdata;\n')
            fh.write('    input_sig_d2 <= input_sig_d1;\n')
            fh.write('    input_sig_d3 <= input_sig_d2;\n')
        fh.write('    phase_d[0] <= rd_addr[{}:0];\n'.format(phase_msb))
        fh.write('    phase_d[1] <= phase_d[0] & phase_max_slice;\n')
        fh.write('    phase_d[2] <= phase_d[1];\n')
        if tuser_width:
            fh.write('    tuser_d[0] <= s_axis_tuser;\n')
            fh.write('    tuser_d[1] <= tuser_d[0];\n')
            fh.write('    tuser_d[2] <= tuser_d[1];\n')

        fh.write('    sig_d1 <= sig;\n')
        fh.write('    sig_d2 <= sig_d1;\n')
        fh.write('    sig_d3 <= sig_d2;\n')
        fh.write('\n')
        fh.write('    wr_addr_d[0] <= wr_addr;\n')
        if gen_2X:
            t_val = (mem_msb, mem_msb, phase_msb)
            fh.write('    wr_addr_d[3] <= {{~rd_addr[{}], rd_addr[{}], rd_addr[{}:0]}};\n'.format(*t_val))
            for i in range(taps_per_phase - 2):
                idx = i * 3 + 6
                t_val = (idx, i, mem_msb, i, mem_msb, i, phase_msb)
                fh.write('    wr_addr_d[{}] <= {{~rd_addr_d[{}][{}], rd_addr_d[{}][{}], rd_addr_d[{}][{}:0]}};\n'.format(*t_val))
        else:
            t_val = (mem_msb, phase_msb)
            fh.write('    wr_addr_d[3] <= {{~rd_addr[{}], rd_addr[{}:0]}};\n'.format(*t_val))
            for i in range(taps_per_phase - 2):
                idx = i * 3 + 6
                t_val = (idx, i, mem_msb, i, phase_msb)
                fh.write('    wr_addr_d[{}] <= {{~rd_addr_d[{}][{}], rd_addr_d[{}][{}:0]}};\n'.format(*t_val))
        fh.write('\n')
        for i in range(taps_per_phase):
            for j in range(1, 3):
                lidx = j + i * 3
                ridx = lidx - 1
                fh.write('    wr_addr_d[{}] <= wr_addr_d[{}];\n'.format(lidx, ridx))
        fh.write('end\n')
        fh.write('\n')

        fh.write('//tvalid_pipe_proc\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        push_idx = tvalid_len - 2
        fh.write('    next_tvalid_pipe[{}:0] = {{tvalid_pipe[{}:0], (s_axis_tvalid & ~almost_full)}};\n'.format(push_idx, push_idx - 1))
        fh.write('    if (tvalid_d[{}] == 1\'b1) begin\n'.format(push_idx))
        fh.write('        next_tvalid_pipe[{}:{}] = {{tvalid_pipe[{}:{}],tvalid_pipe[{}]}};\n'.format(mod_latency -1, push_idx + 1, mod_latency - 2, push_idx + 1, push_idx))
        fh.write('    end else begin\n')
        fh.write('        next_tvalid_pipe[{}:{}] = tvalid_pipe[{}:{}];\n'.format(mod_latency - 1, push_idx + 1, mod_latency - 1, push_idx + 1))
        fh.write('    end\n')
        fh.write('end\n')
        if tlast:
            fh.write('\n')
            fh.write('//tlast_proc \n')
            fh.write('always @*\n')
            fh.write('begin\n')
            fh.write('    next_tlast_d[{}:0] = {{tlast_d[{}:0], s_axis_tlast}};\n'.format(push_idx, push_idx - 1))
            fh.write('    if (tvalid_d[{}] == 1\'b1) begin\n'.format(push_idx))
            fh.write('        next_tlast_d[{}:{}] = {{tlast_d[{}:{}], tlast_d[{}]}};\n'.format(mod_latency -1, push_idx + 1, mod_latency - 2, push_idx + 1, push_idx))
            fh.write('    end else begin\n')
            fh.write('        next_tlast_d[{}:{}] = tlast_d[{}:{}];\n'.format(mod_latency - 1, push_idx + 1, mod_latency - 1, push_idx + 1))
            fh.write('    end\n')
            fh.write('end\n')
        fh.write('\n')
        fh.write('// clock and reset process.\n')
        fh.write('integer m;\n')
        fh.write('always @(posedge clk, posedge sync_reset)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        offset_cnt <= 1;  // this ensures that the first read / write is to offset 0.\n')
        fh.write('        offset_cnt_prev <= 0;\n')
        fh.write('        sig <= 0;\n')
        fh.write('        tvalid_d <= 0;\n')
        fh.write('        tvalid_pipe <= 0;\n')
        if tlast:
            fh.write('        tlast_d <= 0;\n')
        fh.write('        for (m=0; m<{}; m=m+1) begin\n'.format(taps_per_phase - 1))
        fh.write('            rd_addr_d[m] <= 0;\n')
        fh.write('        end\n')
        fh.write('        rd_addr <= 0;\n')
        fh.write('        wr_addr <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        offset_cnt <= next_offset_cnt;\n')
        fh.write('        offset_cnt_prev <= next_offset_cnt_prev;\n')
        fh.write('        sig <= next_sig;\n')
        fh.write('        tvalid_d <= {{tvalid_d[{}:0], (s_axis_tvalid & ~almost_full)}};\n'.format(tvalid_len - 2))
        fh.write('        tvalid_pipe <= next_tvalid_pipe;\n')
        if tlast:
            fh.write('        tlast_d <= next_tlast_d;\n')
        fh.write('        for (m=0; m<{}; m=m+1) begin\n'.format(taps_per_phase - 1))
        fh.write('            rd_addr_d[m] <= next_rd_addr_d[m];\n')
        fh.write('        end\n')
        fh.write('        rd_addr <= next_rd_addr;\n')
        fh.write('        wr_addr <= next_wr_addr;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('integer n;\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (tvalid_d[{}] == 1\'b1) begin\n'.format(push_idx))
        fh.write('        for (n=3; n<{}; n=n+1) begin\n'.format(arm_latency + 1))
        fh.write('            phase_d[n] <= phase_d[n - 1];\n')
        fh.write('        end\n')
        if tuser_width:
            fh.write('        for (n=3; n<{}; n=n+1) begin\n'.format(arm_latency + 1))
            fh.write('            tuser_d[n] <= tuser_d[n-1];\n')
            fh.write('        end\n')
        fh.write('    end\n')
        fh.write('end\n\n')
        fh.write('// read and write address update logic.\n')
        fh.write('integer p;\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_offset_cnt = offset_cnt;\n')
        fh.write('    next_offset_cnt_prev = offset_cnt_prev;\n')
        fh.write('    next_rd_addr = rd_addr;\n')
        fh.write('    next_wr_addr = wr_addr;\n')
        fh.write('    // increment offset count once per cycle through the PFB arms.\n')
        if gen_2X:
            fh.write('    if (tvalid_d[2] == 1\'b1) begin\n')
            if count_dn:
                fh.write('        if (phase_mux_d[2] == phase_max_slice) begin\n')
            else:
                fh.write('        if (phase_mux_d[2] == {}\'d0) begin\n'.format(phase_bits))
            fh.write('            next_offset_cnt_prev = offset_cnt;\n')
            fh.write('            next_offset_cnt = offset_cnt + 1;\n')
            fh.write('            next_wr_addr = {offset_cnt + 1, phase_mux_d[2]};\n')
            fh.write('            next_rd_addr = {offset_cnt, phase_mux_d[2]};\n')
            fh.write('        end else begin\n')
            fh.write('            next_rd_addr = {offset_cnt_prev, phase_mux_d[2]};\n')
            fh.write('            next_wr_addr = {offset_cnt, phase_mux_d[2]};\n')
            fh.write('        end\n')
        else:
            fh.write('    if (take_data == 1\'b1) begin\n')
            if count_dn:
                fh.write('        if (phase == phase_max_slice) begin\n')
            else:
                fh.write('        if (phase == {}\'d0) begin\n'.format(phase_bits))
            fh.write('            next_offset_cnt_prev = offset_cnt;\n')
            fh.write('            next_offset_cnt = offset_cnt + 1;\n')
            fh.write('            next_wr_addr = {offset_cnt + 1, phase};\n')
            fh.write('            next_rd_addr = {offset_cnt, phase};\n')
            fh.write('        end else begin\n')
            fh.write('            next_rd_addr = {offset_cnt_prev, phase};\n')
            fh.write('            next_wr_addr = {offset_cnt, phase};\n')
            fh.write('        end\n')
        fh.write('    end\n')
        fh.write('\n')
        if gen_2X:
            fh.write('    if (tvalid_d[2] == 1\'b1) begin\n')
            fh.write('        if (bot_half == 1\'b1) begin\n')
            fh.write('            next_sig = delay_sig;\n')
            fh.write('        end else begin\n')
            fh.write('            next_sig = input_sig_d3;\n')
            fh.write('        end\n')
            fh.write('    end else begin\n')
            fh.write('        next_sig = sig;\n')
            fh.write('    end\n')
        else:
            fh.write('    if (take_data == 1\'b1) begin\n')
            fh.write('        next_sig = s_axis_tdata;\n')
            fh.write('    end else begin\n')
            fh.write('        next_sig = sig;\n')
            fh.write('    end\n')
        fh.write('\n')
        fh.write('    // shift through old values.\n')
        if gen_2X:
            fh.write('    if (tvalid_d[2] == 1\'b1) begin\n')
        else:
            fh.write('    if (take_data == 1\'b1) begin\n')
        fh.write('        next_rd_addr_d[0] = rd_addr;\n')
        fh.write('        for (p=1; p<{}; p=p+1) begin\n'.format(taps_per_phase - 1))
        fh.write('            next_rd_addr_d[p] = rd_addr_d[p-1];\n')
        fh.write('        end\n')
        fh.write('    end else begin\n')
        fh.write('        for (p=0; p<{}; p=p+1) begin\n'.format(taps_per_phase - 1))
        fh.write('            next_rd_addr_d[p] = rd_addr_d[p];\n')
        fh.write('        end\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('{} tap_ctrl\n'.format(mem_ctrl_name))
        fh.write('(\n')
        fh.write('  .clk(clk),\n')
        fh.write('  .sync_reset(sync_reset),\n')
        fh.write('\n')
        fh.write('  .s_axis_reload_tdata(s_axis_reload_tdata),\n')
        fh.write('  .s_axis_reload_tlast(s_axis_reload_tlast),\n')
        fh.write('  .s_axis_reload_tvalid(s_axis_reload_tvalid),\n')
        fh.write('  .s_axis_reload_tready(s_axis_reload_tready),\n')
        fh.write('\n')
        fh.write('  .taps_addr(rom_addr),\n')
        fh.write('  .taps_we(rom_we),\n')
        fh.write('  .taps_douta(rom_data)\n')
        fh.write(');\n\n')
        if gen_2X:
            # generate dual port ram.
            fh.write('// 3 cycle latency.\n')
            fh.write('{} #(\n'.format(delay_name))
            fh.write('  .DATA_WIDTH({}),\n'.format(ram_width))
            fh.write('  .ADDR_WIDTH({}))\n'.format(phase_bits))
            fh.write('sample_delay (\n'.format(delay_name))
            fh.write('  .clk(clk), \n')
            fh.write('  .wea(tvalid_d[0]),\n')
            fh.write('  .addra(phase_mux_d[0][{}:0]),\n'.format(phase_msb))
            fh.write('  .dia(input_sig_d1),\n')
            fh.write('  .addrb(phase[{}:0]),\n'.format(phase_msb))
            fh.write('  .dob(delay_sig)\n')
            fh.write(');\n')
            fh.write('\n')

        if interp_fil:
            ram_msb = int(gen_2X)
            fh.write('// 3 cycle latency\n')
            fh.write('{} #(\n'.format(ram_name))
            fh.write('  .DATA_WIDTH({}),\n'.format(ram_width))
            fh.write('  .ADDR_WIDTH({}))\n'.format(ram_msb + 1))
            fh.write('sample_ram_0 (\n')
            fh.write('  .clk(clk), \n')
            fh.write('  .wea(tvalid_d[{}]), \n'.format(push_idx))
            fh.write('  .addra(wr_addr_d[2][{}:0]),\n'.format(ram_msb))
            fh.write('  .dia(sig_d3), \n')
            fh.write('  .addrb(rd_addr[{}:0]),\n'.format(ram_msb))
            fh.write('  .dob(delay[0])\n')
            fh.write(');\n')
            fh.write('\n')
            fh.write('genvar i;\n')
            fh.write('generate\n')
            fh.write('    for (i=1; i<{}; i=i+1) begin : TAP_DELAY\n'.format(taps_per_phase))
            fh.write('        {} #(\n'.format(ram_name))
            fh.write('          .DATA_WIDTH({}),\n'.format(ram_width))
            fh.write('          .ADDR_WIDTH({}))\n'.format(ram_msb + 1))
            fh.write('        sample_ram_inst (\n')
            fh.write('          .clk(clk),\n')
            fh.write('          .wea(tvalid_d[{}]),\n'.format(push_idx))
            fh.write('          .addra(wr_addr_d[i*3+2][{}:0]),\n'.format(ram_msb))
            fh.write('          .dia(delay[i-1]),\n')
            fh.write('          .addrb(rd_addr_d[i-1][{}:0]),\n'.format(ram_msb))
            fh.write('          .dob(delay[i])\n')
            fh.write('        );\n')
            fh.write('    end\n')
            fh.write('endgenerate\n')
        else:
            fh.write('// 3 cycle latency\n')
            fh.write('{} #(\n'.format(ram_name))
            fh.write('  .DATA_WIDTH({}),\n'.format(ram_width))
            fh.write('  .ADDR_WIDTH({}))\n'.format(addr_bits))
            fh.write('sample_ram_0 (\n')
            fh.write('  .clk(clk), \n')
            fh.write('  .wea(tvalid_d[{}]), \n'.format(push_idx))
            fh.write('  .addra(wr_addr_d[2][{}:0]),\n'.format(addr_msb))
            fh.write('  .dia(sig_d3), \n')
            fh.write('  .addrb(rd_addr[{}:0]),\n'.format(addr_msb))
            fh.write('  .dob(delay[0])\n')
            fh.write(');\n')
            fh.write('\n')
            fh.write('genvar i;\n')
            fh.write('generate\n')
            fh.write('    for (i=1; i<{}; i=i+1) begin : TAP_DELAY\n'.format(taps_per_phase))
            fh.write('        {} #(\n'.format(ram_name))
            fh.write('          .DATA_WIDTH({}),\n'.format(ram_width))
            fh.write('          .ADDR_WIDTH({}))\n'.format(addr_bits))
            fh.write('        sample_ram_inst (\n')
            fh.write('          .clk(clk),\n')
            fh.write('          .wea(tvalid_d[{}]),\n'.format(push_idx))
            fh.write('          .addra(wr_addr_d[i*3+2][{}:0]),\n'.format(addr_msb))
            fh.write('          .dia(delay[i-1]),\n')
            fh.write('          .addrb(rd_addr_d[i-1][{}:0]),\n'.format(addr_msb))
            fh.write('          .dob(delay[i])\n')
            fh.write('        );\n')
            fh.write('    end\n')
            fh.write('endgenerate\n')
        fh.write('\n')
        fh.write('// Coefficent memories\n')
        fh.write('// latency = 3.\n')
        tap_addr_bits = int(np.log2(phase_depth))
        fh.write('{} #(\n'.format(tap_ram_name))
        fh.write('    .DATA_WIDTH({}),\n'.format(tap_width))
        fh.write('    .ADDR_WIDTH({}))\n'.format(tap_addr_bits))
        fh.write('pfb_taps_0 (\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .wea(rom_we[0]),\n')
        fh.write('    .addra(rom_addr),\n')
        fh.write('    .dia(rom_data),\n')
        fh.write('    .addrb(rd_addr[{}:0]),\n'.format(phase_msb))
        fh.write('    .dob(taps[0])\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('genvar nn;\n')
        fh.write('generate\n')
        fh.write('    for (nn=1; nn<{}; nn=nn+1) begin : COEFFS\n'.format(taps_per_phase))
        fh.write('        {} #(\n'.format(tap_ram_name))
        fh.write('            .DATA_WIDTH({}),\n'.format(tap_width))
        fh.write('            .ADDR_WIDTH({}))\n'.format(tap_addr_bits))
        fh.write('        pfb_taps_nn\n')
        fh.write('        (\n')
        fh.write('            .clk(clk),\n')
        fh.write('            .wea(rom_we[nn]),\n')
        fh.write('            .addra(rom_addr),\n')
        fh.write('            .dia(rom_data),\n')
        fh.write('            .addrb(rd_addr_d[nn-1][{}:0]),\n'.format(phase_msb))
        fh.write('            .dob(taps[nn])\n')
        fh.write('        );\n')
        fh.write('    end\n')
        fh.write('endgenerate\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('// PFB MAC blocks\n')
        pad = 18 - input_width
        fh.write('{} pfb_mac_i_start (\n'.format(dsp_name0))
        fh.write('  .clk(clk),\n')
        fh.write('  .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('  .a(taps[0]),\n')
        fh.write('  .b(delay[0][{}:{}]),\n'.format(word_msb, input_width))
        fh.write('  .pcout(pcouti[0]),\n')
        fh.write('  .p()\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// Latency = 4\n')
        fh.write('{} pfb_mac_q_start (\n'.format(dsp_name0))
        fh.write('  .clk(clk),\n')
        fh.write('  .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('  .a(taps[0]),\n')
        fh.write('  .b(delay[0][{}:0]),\n'.format(input_width - 1))
        fh.write('  .pcout(pcoutq[0]),\n')
        fh.write('  .p()\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('genvar j;\n')
        fh.write('generate\n')
        fh.write('    for (j=1; j<{}; j=j+1) begin : MAC\n'.format(taps_per_phase - int(dsp48e2)))
        fh.write('        {} pfb_mac_i\n'.format(dsp_name))
        fh.write('        (\n')
        fh.write('          .clk(clk),\n')
        fh.write('          .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('          .pcin(pcouti[j-1]),\n')
        fh.write('          .a(taps[j]),\n')
        fh.write('          .b(delay[j][{}:{}]),\n'.format(word_msb, input_width))  #analysis:ignore
        fh.write('          .pcout(pcouti[j]),\n')
        fh.write('          .p()\n')
        fh.write('        );\n')
        fh.write('\n')
        fh.write('        {} pfb_mac_q\n'.format(dsp_name))
        fh.write('        (\n')
        fh.write('          .clk(clk),\n')
        fh.write('          .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('          .pcin(pcoutq[j-1]),\n')
        fh.write('          .a(taps[j]),\n')
        fh.write('          .b(delay[j][{}:0]),\n'.format(input_width - 1))  #analysis:ignore
        fh.write('          .pcout(pcoutq[j]),\n')
        fh.write('          .p()\n')
        fh.write('        );\n')
        fh.write('    end\n')
        fh.write('endgenerate\n')
        fh.write('\n')
        if dsp48e2:
            fh.write('{} pfb_rnd_i\n'.format(rnd_name))
            fh.write('(\n')
            fh.write('    .clk(clk),\n')
            fh.write('    .ce(tvalid_d[{}]),\n'.format(push_idx))
            fh.write('    .pcin(pcouti[{}]),\n'.format(taps_per_phase - 2))
            fh.write('    .a(taps[{}]),\n'.format(taps_per_phase - 1))
            fh.write('    .b(delay[{}][{}:{}]),\n'.format(taps_per_phase - 1, word_msb, input_width))
            fh.write('    .pcout(),\n')
            fh.write('    .p(pouti)\n')
            fh.write(');\n')
            fh.write('\n')
            fh.write('{} pfb_rnd_q\n'.format(rnd_name))
            fh.write('(\n')
            fh.write('    .clk(clk),\n')
            fh.write('    .ce(tvalid_d[{}]),\n'.format(push_idx))
            fh.write('    .pcin(pcoutq[{}]),\n'.format(taps_per_phase - 2))
            fh.write('    .a(taps[{}]),\n'.format(taps_per_phase - 1))
            fh.write('    .b(delay[{}][{}:0]),\n'.format(taps_per_phase - 1, input_width - 1))
            fh.write('    .pcout(),\n')
            fh.write('    .p(poutq)\n')
            fh.write(');\n')
            fh.write('\n')
        else:
            fh.write('{} pfb_rnd_i\n'.format(rnd_name))
            fh.write('(\n')
            fh.write('    .clk(clk),\n')
            fh.write('    .ce(tvalid_d[{}]),\n'.format(push_idx))
            fh.write('    .pcin(pcouti[{}]),\n'.format(taps_per_phase - 1))
            fh.write('    .p(pouti)\n')
            fh.write(');\n')
            fh.write('\n')
            fh.write('{} pfb_rnd_q\n'.format(rnd_name))
            fh.write('(\n')
            fh.write('    .clk(clk),\n')
            fh.write('    .ce(tvalid_d[{}]),\n'.format(push_idx))
            fh.write('    .pcin(pcoutq[{}]),\n'.format(taps_per_phase - 1))
            fh.write('    .p(poutq)\n')
            fh.write(');\n')
            fh.write('\n')

        axi_fifo_inst(fh, fifo_name, inst_name='u_fifo', data_width=fifo_width, af_thresh=16,
                      addr_width=6, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='fifo_tvalid',
                      s_tdata_str='fifo_tdata', s_tuser_str='tuser_d[{}]'.format(mod_latency-1), s_tlast_str='tlast_d[{}]'.format(mod_latency-1),
                      s_tready_str='', almost_full_str='almost_full', m_tvalid_str='m_axis_tvalid', m_tdata_str='m_axis_tdata_s',
                      m_tuser_str='m_axis_tuser', m_tlast_str='m_axis_tlast', m_tready_str='m_axis_tready')

        fh.write('\n')
        fh.write('endmodule\n')

    return (module_name, tap_ram_name, ram_name)

def gen_multich_pfb(path, Mmax, rom_fi, input_width=16, output_width=16, taps_per_phase=24,
                    chan_dict=chan_dict, pfb_msb=40, tlast=False, tuser_width=0,
                    ram_style='block', prefix='', gen_2X=False):


    num_fft_sizes = len(chan_dict)
    num_channels = 0
    Mmax = 0
    for value in chan_dict.items():
        num_channels += value[1]
        Mmax = value[0] if value[0] > Mmax else Mmax

    tap_width = rom_fi.word_length
    path = ret_valid_path(path)
    assert(path is not None), 'User must specify directory'
    if gen_2X:
        file_name = '{}multich_pfb_2x_{}iw_{}ow_{}tps.v'.format(prefix, input_width, output_width, taps_per_phase)
    else:
        file_name = '{}multich_pfb_{}iw_{}ow_{}tps.v'.format(prefix, input_width, output_width, taps_per_phase)
    file_name = os.path.join(path, file_name)
    module_name = ret_module_name(file_name)

    num_channels, num_fft_sizes, Mmax, addr_bits, map_vec, tap_bits = calc_bit_widths(chan_dict)

    sub_chan_bits = fp_utils.ret_num_bitsU(num_channels - 1)
    sub_chan_msb = sub_chan_bits - 1

    chan_map_bits = 3
    chan_map_msb = chan_map_bits - 1

    phase_bits = int(np.ceil(np.log2(Mmax)))
    phase_msb = phase_bits - 1

    addr_msb = addr_bits - 1
    mem_msb = addr_msb + 1 + gen_2X

    phase_bits = ret_num_bitsU(Mmax)
    phase_msb = phase_bits - 1
    word_msb = input_width * 2 - 1
    out_msb = output_width * 2 - 1
    taps_msb = tap_width - 1
    we_bits = ret_num_bitsU(taps_per_phase - 1)
    taps_addr_msb = phase_msb + we_bits
    ram_depth = 2 ** addr_bits
    ram_width = input_width * 2
    phase_depth = 2 ** phase_bits

    fifo_width = 2 * output_width + sub_chan_bits + phase_bits + phase_bits

    rnd_latency = 1
    samp_latency = 1 + (3 * gen_2X)
    ram_latency = 3
    arm_latency = taps_per_phase + 6 + rnd_latency
    tvalid_len = samp_latency + ram_latency + rnd_latency
    mod_latency = arm_latency + samp_latency
    pfb_lsb = pfb_msb - output_width + 1

    delay_name = gen_ram(path, ram_type='dp', memory_type='read_first', ram_style=ram_style)
    ram_name = gen_ram(path, ram_type='dp', memory_type='read_first', ram_style=ram_style)
    tap_ram_name = gen_ram(path, ram_type='dp', memory_type='write_first', ram_style=ram_style)
    mem_ctrl_name = gen_mem_ctrl(path, '{}'.format(module_name), rom_fi, num_taps=taps_per_phase)
    _, fifo_name = gen_axi_fifo(path, tuser_width=tuser_width, tlast=tlast, almost_full=True, ram_style='block', prefix='')
    _, dsp_name0 = gen_dsp48E1(path, name='pfb_mac_0', opcode='A*B', a_width=25, b_width=input_width, areg=2, breg=2, mreg=1, preg=1, use_ce=True, use_pcout=True)
    _, dsp_name = gen_dsp48E1(path, name='pfb_mac', opcode='PCIN+A*B', a_width=25, b_width=input_width, areg=2, breg=2, mreg=1, preg=1, use_ce=True, use_pcout=True)
    _, rnd_name = gen_dsp48E1(path, name='pfb_rnd', opcode='PCIN', a_width=25, b_width=input_width, use_ce=True, rnd=True, p_msb=pfb_msb, p_lsb=pfb_lsb, creg=0, preg=1)


    with open(file_name, "w") as fh:
        m_text = 'M/2' if gen_2X else 'M'
        fh.write('/*****************************************************************************/\n')
        fh.write('// Implements the {} PFB architecture referenced in the\n'.format(m_text))
        fh.write('// "A Versatile Multichannel Filter Bank with Multiple Channel Bandwidths" paper.\n')
        fh.write('// This architecture has been mapped to the Xilinx architecture.\n')
        fh.write('// This represents a fully pipelined design that maximizes the FMax potential of the design.\n')
        fh.write('// It is important to understand that filter arms are loaded sequentially. This is referenced in\n')
        fh.write('// the diagram by the incremental changes in the phase subscript through each subsequent delay\n')
        fh.write('// register. The nth index is only updated once per revolution of the filter bank.\n')
        fh.write('//\n')
        fh.write('// It is best to refer to the attached document to understand the layout of the logic. This module\n')
        fh.write('// currently implements {} taps per phase.\n'.format(taps_per_phase))
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        if tuser_width:
            fh.write('module {} #( \n'.format(module_name))
            fh.write('    parameter TUSER_WIDTH=32)\n')
        else:
            fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input [{}:0] phase_size,\n'.format(phase_msb))
        fh.write('    input [{}:0] phase,\n'.format(phase_msb))
        fh.write('    input [{}:0] samp_addr,\n'.format(addr_msb))
        fh.write('    input [{}:0] sub_chan,\n'.format(sub_chan_msb))
        fh.write('    input [2:0] channel_map,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [{}:0] s_axis_tdata,\n'.format(word_msb))
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        if tuser_width:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    input [31:0] s_axis_reload_tdata,\n')
        fh.write('    input s_axis_reload_tlast,\n')
        fh.write('    input s_axis_reload_tvalid,\n')
        fh.write('    output s_axis_reload_tready,\n')
        fh.write('\n')
        fh.write('    output [{}:0] phase_out,\n'.format(phase_msb))
        fh.write('    output [{}:0] phase_size_out,\n'.format(phase_msb))
        fh.write('    output [{}:0] sub_chan_out,\n'.format(sub_chan_msb))
        fh.write('    output [2:0] channel_map_out,\n'.format(channel_map_msb))
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [{}:0] m_axis_tdata,\n'.format(out_msb))
        if tlast:
            fh.write('    output m_axis_tlast,\n')
        if tuser_width:
            fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')

        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        if tuser_width > 0:
            fh.write('localparam TUSER_MSB = TUSER_WIDTH - 1;\n')
        fh.write('wire [{}:0] taps[0:{}];\n'.format(taps_msb, taps_per_phase - 1))
        fh.write('wire [47:0] pcouti[0:{}];\n'.format(taps_per_phase - 1))
        fh.write('wire [47:0] pcoutq[0:{}];\n'.format(taps_per_phase - 1))
        fh.write('wire [{}:0] pouti, poutq;\n'.format(output_width - 1))
        fh.write('\n')
        fh.write('wire [{}:0] delay[0:{}];\n\n'.format(word_msb, taps_per_phase - 1))
        fh.write('reg [{}:0] phase_d[0:{}];\n'.format(phase_msb, arm_latency - 1))
        fh.write('reg [{}:0] tap_phase_d[0:{}];\n'.format(phase_bits, arm_latency - 1))
        fh.write('reg [{}:0] tap_phase, next_tap_phase;\n'.format(phase_bits))
        fh.write('reg [{}:0] curr_phase, next_curr_phase;\n'.format(phase_msb))
        fh.write('reg [{}:0] phase_size_d[0:{}];\n'.format(phase_msb, mod_latency - 1))
        fh.write('reg [{}:0] sub_chan_d[0:{}];\n'.format(sub_chan_msb, mod_latency - 1))
        fh.write('reg [{}:0] channel_map_d[0:{}];\n'.format(chan_map_msb, mod_latency - 1))
        fh.write('\n')
        if gen_2X:
            fh.write('wire [{}:0] delay_sig;\n'.format(word_msb))
            fh.write('reg [{}:0] phase_mux_d[0:2];\n'.format(phase_msb))
            fh.write('reg [{}:0] tap_phase_mux_d[0:2];\n'.format(phase_bits))
            fh.write('reg [{}:0] samp_addr_mux_d[0:2];\n'.format(addr_msb))
            fh.write('\n')
            fh.write('reg [{}:0] input_sig_d1, input_sig_d2, input_sig_d3;\n'.format(word_msb))
            fh.write('wire bot_half;\n')
            fh.write('\n')
        fh.write('reg [{}:0] tvalid_d;\n'.format(tvalid_len - 1))
        fh.write('reg [{}:0] tvalid_pipe, next_tvalid_pipe;\n'.format(mod_latency-1))
        if tlast:
            fh.write('reg [{}:0] tlast_d, next_tlast_d;\n'.format(mod_latency - 1))
        if tuser_width:
            fh.write('reg [TUSER_MSB:0] tuser_d[0:{}];\n'.format(mod_latency - 1))
        fh.write('\n')
        fh.write('reg [{}:0] wr_addr_d[0:{}];\n'.format(mem_msb, taps_per_phase * 3 - 1))
        fh.write('\n')
        fh.write('reg [{}:0] sig, next_sig;\n'.format(word_msb))
        fh.write('reg [{}:0] sig_d1, sig_d2, sig_d3;\n'.format(word_msb))
        fh.write('reg [{}:0] rd_addr, next_rd_addr;\n'.format(mem_msb))
        fh.write('reg [{}:0] wr_addr, next_wr_addr;\n'.format(mem_msb))
        fh.write('reg [{}:0] rd_addr_d[0:{}];\n'.format(mem_msb, taps_per_phase - 2))
        fh.write('\n')
        fh.write('reg [{}:0] next_rd_addr_d[0:{}];\n'.format(mem_msb, taps_per_phase - 2))
        fh.write('\n')
        fh.write('reg [{}:0] offset_cnt, next_offset_cnt;\n'.format(int(gen_2X)))
        fh.write('reg [{}:0] offset_cnt_prev, next_offset_cnt_prev;\n'.format(int(gen_2X)))
        fh.write('\n')
        fh.write('wire [{}:0] rom_addr;\n'.format(phase_msb))
        fh.write('wire [{}:0] rom_data;\n'.format(tap_width-1))
        fh.write('wire [{}:0] rom_we;\n'.format(taps_per_phase-1))
        fh.write('\n')
        fh.write('reg [{}:0] phase_max;\n'.format(phase_msb))
        fh.write('reg [{}:0] phase_max_slice;\n'.format(phase_msb - 1))
        fh.write('reg [{}:0] phase_half, phase_half_d1, phase_half_d2;\n'.format(phase_msb))
        fh.write('wire [{}:0] fifo_tdata, m_axis_tdata_s;\n'.format(fifo_width-1))
        fh.write('wire fifo_tvalid;\n')
        fh.write('wire almost_full;\n')
        fh.write('wire take_data;\n')
        fh.write('\n')
        fh.write('assign take_data = (s_axis_tvalid & ~almost_full);\n')
        ridx = phase_bits + phase_bits + sub_chan_bits + map_bits
        lidx = fifo_width - 1
        fh.write('assign m_axis_tdata = m_axis_tdata_s[{}:{}];\n'.format(lidx, ridx))
        fh.write('assign s_axis_tready = ~almost_full;\n')
        fh.write('assign fifo_tvalid = tvalid_d[{}] & tvalid_pipe[{}];\n'.format(tvalid_len - 1, mod_latency - 1))
        fh.write('assign phase_out = m_axis_tdata_s[{}:0];\n'.format(phase_bits - 1))
        lidx = phase_bits + phase_bits - 1
        fh.write('assign phase_size_out = m_axis_tdata_s[{}:{}];\n'.format(lidx, phase_bits))
        ridx = lidx + 1
        lidx = lidx + sub_chan_bits
        fh.write('assign sub_chan_out = m_axis_tdata_s[{}:{}];\n'.format(lidx, ridx))
        ridx = lidx + 1
        lidx = lidx + 3
        fh.write('assign channel_map_out = m_axis_tdata_s[{}:{}];\n'.format(lidx, ridx))
        t_val = (mod_latency-1, mod_latency-1, arm_latency - 1)
        fh.write('assign fifo_tdata = {{pouti, poutq, sub_chan_d[{}], phase_size_d[{}], phase_d[{}]}};\n'.format(*t_val))
        if gen_2X:
            fh.write('assign bot_half = ((phase_mux_d[2] & phase_half_d2[{}:0]) != 0) ? 1\'b1 : 1\'b0;\n'.format(phase_msb, phase_msb))
        fh.write('\n')
        fh.write('\n')
        fh.write('// logic implements the sample write address pipelining.\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('\n')
        fh.write('    phase_max <= phase_size - 1;\n')
        fh.write('    phase_max_slice <= phase_max[{}:0];\n'.format(phase_msb))
        fh.write('    phase_half <= phase_size >> 1;\n')
        fh.write('    phase_half_d1 <= phase_half;\n')
        fh.write('    phase_half_d2 <= phase_half_d1;\n')
        fh.write('\n')
        # need to compute subtraction.
        if gen_2X:
            fh.write('    phase_mux_d[0] <= phase;\n')
            fh.write('    phase_mux_d[1] <= phase_mux_d[0];\n')
            fh.write('    phase_mux_d[2] <= phase_mux_d[1] & phase_max_slice;\n')
            fh.write('\n')
            fh.write('    samp_addr_mux_d[0] <= samp_addr;\n')
            fh.write('    samp_addr_mux_d[1] <= samp_addr_mux_d[0];\n')
            fh.write('    samp_addr_mux_d[2] <= samp_addr_mux_d[1] & phase_max_slice;\n')
            fh.write('\n')
            fh.write('    case (channel_map):\n')
            fh.write('        3\'d0:\n')
            fh.write('        begin\n')
            fh.write('            tap_phase_mux_d[0] <= phase;\n')
            fh.write('        end\n')
            fh.write('        3\'d1:\n')
            fh.write('        begin\n')
            fh.write('            tap_phase_mux_d[0] <= phase + 512;\n')
            fh.write('        end\n')
            fh.write('        3\'d2:\n')
            fh.write('        begin\n')
            fh.write('            tap_phase_mux_d[0] <= phase + 768;\n')
            fh.write('        end\n')
            fh.write('        3\'d3:\n')
            fh.write('        begin\n')
            fh.write('            tap_phase_mux_d[0] <= phase + 896;\n')
            fh.write('        end\n')
            fh.write('        3\'d4:\n')
            fh.write('        begin\n')
            fh.write('            tap_phase_mux_d[0] <= phase + 960;\n')
            fh.write('        end\n')
            fh.write('        3\'d5:\n')
            fh.write('        begin\n')
            fh.write('            tap_phase_mux_d[0] <= phase + 992;\n')
            fh.write('        end\n')
            fh.write('        3\'d6:\n')
            fh.write('        begin\n')
            fh.write('            tap_phase_mux_d[0] <= phase + 1008;\n')
            fh.write('        end\n')
            fh.write('        default:\n')
            fh.write('        begin\n')
            fh.write('            tap_phase_mux_d[0] <= phase;\n')
            fh.write('        end\n')
            fh.write('    endcase\n')
            fh.write('    tap_phase_mux_d[1] <= tap_phase_mux_d[0];\n')
            fh.write('    tap_phase_mux_d[2] <= tap_phase_mux_d[1];\n')
            fh.write('\n')
            fh.write('    input_sig_d1 <= s_axis_tdata;\n')
            fh.write('    input_sig_d2 <= input_sig_d1;\n')
            fh.write('    input_sig_d3 <= input_sig_d2;\n')
            fh.write('\n')

        fh.write('    phase_d[0] <= curr_phase;\n'.format(phase_msb))
        fh.write('    phase_d[1] <= phase_d[0];\n')
        fh.write('    phase_d[2] <= phase_d[1];\n')
        fh.write('\n')
        fh.write('    tap_phase_d[0] <= tap_phase;\n'.format(phase_msb))
        fh.write('    tap_phase_d[1] <= tap_phase_d[0];\n')
        fh.write('    tap_phase_d[2] <= tap_phase_d[1];\n')
        fh.write('\n')
        if tuser_width:
            fh.write('    tuser_d[0] <= s_axis_tuser;\n')
            fh.write('    tuser_d[1] <= tuser_d[0];\n')
            fh.write('    tuser_d[2] <= tuser_d[1];\n')
            fh.write('    tuser_d[3] <= tuser_d[2];\n')

        fh.write('    sig_d1 <= sig;\n')
        fh.write('    sig_d2 <= sig_d1;\n')
        fh.write('    sig_d3 <= sig_d2;\n')
        fh.write('\n')
        fh.write('    wr_addr_d[0] <= wr_addr;\n')
        if gen_2X:
            t_val = (mem_msb, mem_msb, addr_msb)
            fh.write('    wr_addr_d[3] <= {{~rd_addr[{}], rd_addr[{}], rd_addr[{}:0]}};\n'.format(*t_val))
            for i in range(taps_per_phase - 2):
                idx = i * 3 + 6
                t_val = (idx, i, mem_msb, i, mem_msb, i, addr_msb)
                fh.write('    wr_addr_d[{}] <= {{~rd_addr_d[{}][{}], rd_addr_d[{}][{}], rd_addr_d[{}][{}:0]}};\n'.format(*t_val))
        else:
            t_val = (mem_msb, addr_msb)
            fh.write('    wr_addr_d[3] <= {{~rd_addr[{}], rd_addr[{}:0]}};\n'.format(*t_val))
            for i in range(taps_per_phase - 2):
                idx = i * 3 + 6
                t_val = (idx, i, mem_msb, i, addr_msb)
                fh.write('    wr_addr_d[{}] <= {{~rd_addr_d[{}][{}], rd_addr_d[{}][{}:0]}};\n'.format(*t_val))
        fh.write('\n')
        for i in range(taps_per_phase):
            for j in range(1, 3):
                lidx = j + i * 3
                ridx = lidx - 1
                fh.write('    wr_addr_d[{}] <= wr_addr_d[{}];\n'.format(lidx, ridx))
        fh.write('end\n')
        fh.write('\n')

        fh.write('//tvalid_pipe_proc\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        push_idx = tvalid_len - 2
        fh.write('    next_tvalid_pipe[{}:0] = {{tvalid_pipe[{}:0], (s_axis_tvalid & ~almost_full)}};\n'.format(push_idx, push_idx - 1))
        fh.write('    if (tvalid_d[{}] == 1\'b1) begin\n'.format(push_idx))
        fh.write('        next_tvalid_pipe[{}:{}] = {{tvalid_pipe[{}:{}], tvalid_pipe[{}]}};\n'.format(mod_latency -1, push_idx + 1, mod_latency - 2, push_idx + 1, push_idx))
        fh.write('    end else begin\n')
        fh.write('        next_tvalid_pipe[{}:{}] = tvalid_pipe[{}:{}];\n'.format(mod_latency - 1, push_idx + 1, mod_latency - 1, push_idx + 1))
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        pipe_helper(fh, push_idx, mod_latency, name='phase_size')
        fh.write('\n')
        pipe_helper(fh, push_idx, mod_latency, name='sub_chan')
        fh.write('\n')
        pipe_helper(fh, push_idx, mod_latency, name='channel_map')
        fh.write('\n')
        if tlast:
            fh.write('\n')
            fh.write('//tlast_proc \n')
            fh.write('always @*\n')
            fh.write('begin\n')
            fh.write('    next_tlast_d[{}:0] = {{tlast_d[{}:0], s_axis_tlast}};\n'.format(push_idx, push_idx - 1))
            fh.write('    if (tvalid_d[{}] == 1\'b1) begin\n'.format(push_idx))
            fh.write('        next_tlast_d[{}:{}] = {{tlast_d[{}:{}], tlast_d[{}]}};\n'.format(mod_latency -1, push_idx + 1, mod_latency - 2, push_idx + 1, push_idx))
            fh.write('    end else begin\n')
            fh.write('        next_tlast_d[{}:{}] = tlast_d[{}:{}];\n'.format(mod_latency - 1, push_idx + 1, mod_latency - 1, push_idx + 1))
            fh.write('    end\n')
            fh.write('end\n')
        fh.write('\n')
        fh.write('// clock and reset process.\n')
        fh.write('integer m;\n')
        fh.write('always @(posedge clk, posedge sync_reset)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        offset_cnt <= 1;  // this ensures that the first read / write is to offset 0.\n')
        fh.write('        offset_cnt_prev <= 0;\n')
        fh.write('        tap_phase <= 0;\n')
        fh.write('        curr_phase <= 0;\n')
        fh.write('        sig <= 0;\n')
        fh.write('        tvalid_d <= 0;\n')
        fh.write('        tvalid_pipe <= 0;\n')
        if tlast:
            fh.write('        tlast_d <= 0;\n')
        fh.write('        for (m=0; m<{}; m=m+1) begin\n'.format(taps_per_phase - 1))
        fh.write('            rd_addr_d[m] <= 0;\n')
        fh.write('        end\n')

        reset_helper(fh, mod_latency, name='phase_size')
        fh.write('\n')
        reset_helper(fh, mod_latency, name='sub_chan')
        fh.write('\n')
        fh.write('        rd_addr <= 0;\n')
        fh.write('        wr_addr <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        offset_cnt <= next_offset_cnt;\n')
        fh.write('        offset_cnt_prev <= next_offset_cnt_prev;\n')
        fh.write('        tap_phase <= next_tap_phase;\n')
        fh.write('        curr_phase <= next_curr_phase;\n')
        fh.write('        sig <= next_sig;\n')
        fh.write('        tvalid_d <= {{tvalid_d[{}:0], (s_axis_tvalid & ~almost_full)}};\n'.format(tvalid_len - 2))
        fh.write('        tvalid_pipe <= next_tvalid_pipe;\n')
        if tlast:
            fh.write('        tlast_d <= next_tlast_d;\n')
        fh.write('        for (m=0; m<{}; m=m+1) begin\n'.format(taps_per_phase - 1))
        fh.write('            rd_addr_d[m] <= next_rd_addr_d[m];\n')
        fh.write('        end\n')
        reg_helper(fh, mod_latency, name='phase_size')
        fh.write('\n')
        reg_helper(fh, mod_latency, name='sub_chan')
        fh.write('\n')
        reg_helper(fh, mod_latency, name='sub_chan')
        fh.write('\n')
        reg_helper(fh, mod_latency, name='channel_map')
        fh.write('\n')
        fh.write('        rd_addr <= next_rd_addr;\n')
        fh.write('        wr_addr <= next_wr_addr;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('integer m;\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (tvalid_d[{}] == 1\'b1) begin\n'.format(push_idx))
        fh.write('        for (m=3; m<{}; m=m+1) begin\n'.format(arm_latency))
        fh.write('            phase_d[m+1] <= phase_d[m];\n')
        fh.write('            tap_phase_d[m+1] <= tap_phase_d[m];\n')
        fh.write('        end\n')
        if tuser_width:
            for ii in range(tvalid_len - 1, mod_latency):
                fh.write('        tuser_d[{}] <= tuser_d[{}];\n'.format(ii, ii - 1))
        fh.write('    end\n')
        fh.write('end\n\n')
        fh.write('// read and write address update logic.\n')
        fh.write('integer n;\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_offset_cnt = offset_cnt;\n')
        fh.write('    next_offset_cnt_prev = offset_cnt_prev;\n')
        fh.write('    next_rd_addr = rd_addr;\n')
        fh.write('    next_wr_addr = wr_addr;\n')
        fh.write('    // increment offset count once per cycle through the PFB arms.\n')
        if gen_2X:
            fh.write('    if (tvalid_d[2] == 1\'b1) begin\n')
            fh.write('        next_curr_phase = phase_mux_d[2];\n')
            fh.write('        next_tap_phase = tap_phase_mux_d[2];\n')
            fh.write('        if (phase_mux_d[2] == {}\'d0) begin\n'.format(phase_bits))
            fh.write('            next_offset_cnt_prev = offset_cnt;\n')
            fh.write('            next_offset_cnt = offset_cnt + 1;\n')
            fh.write('            next_wr_addr = {offset_cnt + 1, samp_addr_mux_d[2]};\n')
            fh.write('            next_rd_addr = {offset_cnt, samp_addr_mux_d[2]};\n')
            fh.write('        end else begin\n')
            fh.write('            next_rd_addr = {offset_cnt_prev, samp_addr_mux_d[2]};\n')
            fh.write('            next_wr_addr = {offset_cnt, samp_addr_mux_d[2]};\n')
            fh.write('        end\n')
        else:
            fh.write('    if (take_data == 1\'b1) begin\n')
            fh.write('        if (phase == {}\'d0) begin\n'.format(phase_bits))
            fh.write('            next_offset_cnt_prev = offset_cnt;\n')
            fh.write('            next_offset_cnt = offset_cnt + 1;\n')
            fh.write('            next_wr_addr = {offset_cnt + 1, phase};\n')
            fh.write('            next_rd_addr = {offset_cnt, phase};\n')
            fh.write('        end else begin\n')
            fh.write('            next_rd_addr = {offset_cnt_prev, phase};\n')
            fh.write('            next_wr_addr = {offset_cnt, phase};\n')
            fh.write('        end\n')
        fh.write('    end\n')
        fh.write('\n')
        if gen_2X:
            fh.write('    if (tvalid_d[2] == 1\'b1) begin\n')
            fh.write('        if (bot_half == 1\'b1) begin\n')
            fh.write('            next_sig = delay_sig;\n')
            fh.write('        end else begin\n')
            fh.write('            next_sig = input_sig_d3;\n')
            fh.write('        end\n')
            fh.write('    end else begin\n')
            fh.write('        next_sig = sig;\n')
            fh.write('    end\n')
        else:
            fh.write('    if (take_data == 1\'b1) begin\n')
            fh.write('        next_sig = s_axis_tdata;\n')
            fh.write('    end else begin\n')
            fh.write('        next_sig = sig;\n')
            fh.write('    end\n')
        fh.write('\n')
        fh.write('    // shift through old values.\n')
        if gen_2X:
            fh.write('    if (tvalid_d[2] == 1\'b1) begin\n')
        else:
            fh.write('    if (take_data == 1\'b1) begin\n')
        fh.write('        next_rd_addr_d[0] = rd_addr;\n')
        fh.write('        for (n=1; n<{}; n=n+1) begin\n'.format(taps_per_phase - 1))
        fh.write('            next_rd_addr_d[n] = rd_addr_d[n-1];\n')
        fh.write('        end\n')
        fh.write('    end else begin\n')
        fh.write('        for (n=0; n<{}; n=n+1) begin\n'.format(taps_per_phase - 1))
        fh.write('            next_rd_addr_d[n] = rd_addr_d[n];\n')
        fh.write('        end\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('{} tap_ctrl\n'.format(mem_ctrl_name))
        fh.write('(\n')
        fh.write('  .clk(clk),\n')
        fh.write('  .sync_reset(sync_reset),\n')
        fh.write('\n')
        fh.write('  .s_axis_reload_tdata(s_axis_reload_tdata),\n')
        fh.write('  .s_axis_reload_tlast(s_axis_reload_tlast),\n')
        fh.write('  .s_axis_reload_tvalid(s_axis_reload_tvalid),\n')
        fh.write('  .s_axis_reload_tready(s_axis_reload_tready),\n')
        fh.write('\n')
        fh.write('  .taps_addr(rom_addr),\n')
        fh.write('  .taps_we(rom_we),\n')
        fh.write('  .taps_douta(rom_data)\n')
        fh.write(');\n\n')
        if gen_2X:
            # generate dual port ram.
            fh.write('// 3 cycle latency.\n')
            fh.write('{} #(\n'.format(delay_name))
            fh.write('  .DATA_WIDTH({}),\n'.format(ram_width))
            fh.write('  .ADDR_WIDTH({}))\n'.format(addr_bits))
            fh.write('sample_delay (\n'.format(delay_name))
            fh.write('  .clk(clk), \n')
            fh.write('  .wea(tvalid_d[0]),\n')
            fh.write('  .addra(samp_addr_mux_d[0]),\n')
            fh.write('  .dia(input_sig_d1),\n')
            fh.write('  .addrb(samp_addr),\n')
            fh.write('  .dob(delay_sig)\n')
            fh.write(');\n')
            fh.write('\n')
        fh.write('// 3 cycle latency\n')
        fh.write('{} #(\n'.format(ram_name))
        fh.write('  .DATA_WIDTH({}),\n'.format(ram_width))
        fh.write('  .ADDR_WIDTH({}))\n'.format(addr_bits))
        fh.write('sample_ram_0 (\n')
        fh.write('  .clk(clk), \n')
        fh.write('  .wea(tvalid_d[{}]), \n'.format(push_idx))
        fh.write('  .addra(wr_addr_d[2][{}:0]),\n'.format(addr_msb))
        fh.write('  .dia(sig_d3), \n')
        fh.write('  .addrb(rd_addr[{}:0]),\n'.format(addr_msb))
        fh.write('  .dob(delay[0])\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('genvar i;\n')
        fh.write('generate\n')
        fh.write('    for (i=1; i<{}; i=i+1) begin : TAP_DELAY\n'.format(taps_per_phase))
        fh.write('        {} #(\n'.format(ram_name))
        fh.write('          .DATA_WIDTH({}),\n'.format(ram_width))
        fh.write('          .ADDR_WIDTH({}))\n'.format(addr_bits))
        fh.write('        sample_ram_inst (\n')
        fh.write('          .clk(clk),\n')
        fh.write('          .wea(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('          .addra(wr_addr_d[i*3+2][{}:0]),\n'.format(addr_msb))
        fh.write('          .dia(delay[i-1]),\n')
        fh.write('          .addrb(rd_addr_d[i-1][{}:0]),\n'.format(addr_msb))
        fh.write('          .dob(delay[i])\n')
        fh.write('        );\n')
        fh.write('    end\n')
        fh.write('endgenerate\n')
        fh.write('\n')
        fh.write('// Coefficent memories\n')
        fh.write('// latency = 3.\n')
        tap_addr_bits = int(np.log2(phase_depth))
        fh.write('{} #(\n'.format(tap_ram_name))
        fh.write('    .DATA_WIDTH({}),\n'.format(tap_width))
        fh.write('    .ADDR_WIDTH({}))\n'.format(tap_bits))
        fh.write('pfb_taps_0 (\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .wea(rom_we[0]),\n')
        fh.write('    .addra(rom_addr),\n')
        fh.write('    .dia(rom_data),\n')
        fh.write('    .addrb(tap_phase[{}:0]),\n'.format(tap_bits - 1))
        fh.write('    .dob(taps[0])\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('genvar nn;\n')
        fh.write('generate\n')
        fh.write('    for (nn=1; nn<{}; nn=nn+1) begin : COEFFS\n'.format(taps_per_phase))
        fh.write('        {} #(\n'.format(tap_ram_name))
        fh.write('            .DATA_WIDTH({}),\n'.format(tap_width))
        fh.write('            .ADDR_WIDTH({}))\n'.format(tap_bits))
        fh.write('        pfb_taps_nn\n')
        fh.write('        (\n')
        fh.write('            .clk(clk),\n')
        fh.write('            .wea(rom_we[nn]),\n')
        fh.write('            .addra(rom_addr),\n')
        fh.write('            .dia(rom_data),\n')
        fh.write('            .addrb(tap_phase_d[nn-1][{}:0]),\n'.format(tap_bits - 1))
        fh.write('            .dob(taps[nn])\n')
        fh.write('        );\n')
        fh.write('    end\n')
        fh.write('endgenerate\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('// PFB MAC blocks\n')
        pad = 18 - input_width
        fh.write('{} pfb_mac_i_start (\n'.format(dsp_name0))
        fh.write('  .clk(clk),\n')
        fh.write('  .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('  .a(taps[0]),\n')
        fh.write('  .b(delay[0][{}:{}]),\n'.format(word_msb, input_width))
        fh.write('  .pcout(pcouti[0]),\n')
        fh.write('  .p()\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// Latency = 4\n')
        fh.write('{} pfb_mac_q_start (\n'.format(dsp_name0))
        fh.write('  .clk(clk),\n')
        fh.write('  .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('  .a(taps[0]),\n')
        fh.write('  .b(delay[0][{}:0]),\n'.format(input_width - 1))
        fh.write('  .pcout(pcoutq[0]),\n')
        fh.write('  .p()\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('genvar j;\n')
        fh.write('generate\n')
        fh.write('    for (j=1; j<{}; j=j+1) begin : MAC\n'.format(taps_per_phase))
        fh.write('        {} pfb_mac_i\n'.format(dsp_name))
        fh.write('        (\n')
        fh.write('          .clk(clk),\n')
        fh.write('          .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('          .pcin(pcouti[j-1]),\n')
        fh.write('          .a(taps[j]),\n')
        fh.write('          .b(delay[j][{}:{}]),\n'.format(word_msb, input_width))  #analysis:ignore
        fh.write('          .pcout(pcouti[j]),\n')
        fh.write('          .p()\n')
        fh.write('        );\n')
        fh.write('\n')
        fh.write('        {} pfb_mac_q\n'.format(dsp_name))
        fh.write('        (\n')
        fh.write('          .clk(clk),\n')
        fh.write('          .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('          .pcin(pcoutq[j-1]),\n')
        fh.write('          .a(taps[j]),\n')
        fh.write('          .b(delay[j][{}:0]),\n'.format(input_width - 1))  #analysis:ignore
        fh.write('          .pcout(pcoutq[j]),\n')
        fh.write('          .p()\n')
        fh.write('        );\n')
        fh.write('    end\n')
        fh.write('endgenerate\n')
        fh.write('\n')
        fh.write('{} pfb_rnd_i (\n'.format(rnd_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('  .pcin(pcouti[{}]),\n'.format(taps_per_phase - 1))
        fh.write('  .p(pouti)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('{} pfb_rnd_q (\n'.format(rnd_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .ce(tvalid_d[{}]),\n'.format(push_idx))
        fh.write('  .pcin(pcoutq[{}]),\n'.format(taps_per_phase - 1))
        fh.write('  .p(poutq)\n')
        fh.write(');\n')
        fh.write('\n')

        axi_fifo_inst(fh, fifo_name, inst_name='u_fifo', data_width=fifo_width, af_thresh=16,
                      addr_width=6, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='fifo_tvalid',
                      s_tdata_str='fifo_tdata', s_tuser_str='tuser_d[{}]'.format(mod_latency-1), s_tlast_str='tlast_d[{}]'.format(mod_latency-1),
                      s_tready_str='', almost_full_str='almost_full', m_tvalid_str='m_axis_tvalid', m_tdata_str='m_axis_tdata_s',
                      m_tuser_str='m_axis_tuser', m_tlast_str='m_axis_tlast', m_tready_str='m_axis_tready')

        fh.write('\n')
        fh.write('endmodule\n')

    return (module_name, tap_ram_name, ram_name)

def gen_mem_ctrl(path, name, rom_fi, num_taps=32):
    """
        Generates memory controller logic for configuring coefficient RAMs inside filter ARM

        Args:
            path (str) :

    """

    tap_width = rom_fi.word_length
    tap_msb = tap_width - 1
    file_name = 'mem_ctrl_{}.v'.format(name)
    file_name = os.path.join(path, file_name)
    module_name = ret_module_name(file_name)

    _, rom_name = gen_rom(path, rom_fi, prefix='{}_'.format(name), rom_type='dp', write_access=True)

    addr_bits = int(np.ceil(np.log2(rom_fi.len)))
    addr_msb = addr_bits - 1
    top_bits = int(np.ceil(np.log2(num_taps)))
    bot_msb = addr_bits - top_bits - 1
    roll_over = rom_fi.len - 2
    case_len = 1 << top_bits
    with open(file_name, 'w') as fh:

        fh.write('//***************************************************************************--\n')
        fh.write('//\n')
        fh.write('// Author : PJV\n')
        fh.write('// File : {}.v\n'.format(module_name))
        fh.write('// Description : Memory controller used to load default coefficients into PFB.\n')
        fh.write('// It also provides interface for loading new coefficients.\n')
        fh.write('//\n')
        fh.write('//***************************************************************************--\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input s_axis_reload_tvalid,\n')
        fh.write('    input [31:0] s_axis_reload_tdata,\n')
        fh.write('    input s_axis_reload_tlast,\n')
        fh.write('    output s_axis_reload_tready,\n')
        fh.write('\n')
        fh.write('    output [{}:0] taps_addr,\n'.format(bot_msb))
        fh.write('    output [{}:0] taps_we,\n'.format(num_taps-1))
        fh.write('    output [{}:0] taps_douta\n'.format(tap_msb))
        fh.write('\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('reg [{}:0] wr_addr, next_wr_addr;\n'.format(addr_msb))
        fh.write('reg [{}:0] wr_data, next_wr_data;\n'.format(tap_msb))
        fh.write('\n')
        fh.write('reg [{}:0] taps_addr_d1, taps_addr_d2, taps_addr_d3;\n'.format(addr_msb))
        fh.write('reg [{}:0] taps_addr_int, next_taps_addr;\n'.format(addr_msb))
        fh.write('reg [{}:0] taps_we_s, next_taps_we;\n'.format(num_taps - 1))
        fh.write('\n')
        fh.write('reg sync_reset_d1;\n')
        fh.write('\n')
        fh.write('reg reload_tready = 1\'b0;\n')
        fh.write('reg next_reload_tready;\n')
        fh.write('reg next_config, config_s;\n')
        fh.write('reg config_d1, config_d2, config_d3;\n')
        fh.write('\n')
        fh.write('reg new_coeffs, next_new_coeffs;\n')
        fh.write('wire tap_take;\n')
        fh.write('reg we;\n')
        fh.write('\n')
        fh.write('assign taps_addr = taps_addr_d3;\n')
        fh.write('assign taps_we = taps_we_s;\n')
        fh.write('assign tap_take = reload_tready & s_axis_reload_tvalid;\n')
        fh.write('assign s_axis_reload_tready = reload_tready;\n')
        fh.write('// assign taps_dina = taps_dina_s;\n')
        fh.write('\n')
        fh.write('localparam S_CONFIG = 0, S_IDLE = 1;\n')
        fh.write('reg state = S_CONFIG;\n')
        fh.write('reg next_state;\n')
        fh.write('reg state_d1 = S_IDLE;\n')
        fh.write('\n')
        fh.write('// clock and reset process\n')
        fh.write('always @(posedge clk, posedge sync_reset)\n')
        fh.write('begin\n')
        fh.write('	if (sync_reset == 1\'b1) begin\n')
        fh.write('          new_coeffs <= 1\'b1;\n')
        fh.write('          wr_addr <= 0;\n')
        fh.write('          wr_data <= 0;\n')
        fh.write('          taps_we_s <= 0;\n')
        fh.write('          taps_addr_int <= 0;\n')
        fh.write('          reload_tready <= 1\'b0;\n')
        fh.write('          state <= S_CONFIG;\n')
        fh.write('          state_d1 <= S_IDLE;\n')
        fh.write('          config_s <= 1\'b0;\n')
        fh.write('	end else begin\n')
        fh.write('          new_coeffs <= next_new_coeffs;\n')
        fh.write('          wr_addr <= next_wr_addr;\n')
        fh.write('          wr_data <= next_wr_data;\n')
        fh.write('          taps_we_s <= next_taps_we;\n')
        fh.write('          taps_addr_int <= next_taps_addr;\n')
        fh.write('          reload_tready <= next_reload_tready;\n')
        fh.write('          state <= next_state;\n')
        fh.write('          state_d1 <= state;\n')
        fh.write('          config_s <= next_config;\n')
        fh.write('	end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// delay process.\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        # fh.write('    state_d1 <= state;\n')
        fh.write('    taps_addr_d1 <= taps_addr_int;\n')
        fh.write('    taps_addr_d2 <= taps_addr_d1;\n')
        fh.write('    taps_addr_d3 <= taps_addr_d2;\n')
        fh.write('    config_d1 <= config_s;\n')
        fh.write('    config_d2 <= config_d1;\n')
        fh.write('    config_d3 <= config_d2;\n')
        fh.write('    we <= tap_take;\n')
        fh.write('    sync_reset_d1 <= sync_reset;\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// state machine.\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_state = state;\n')
        fh.write('    next_taps_addr = taps_addr_int;\n')
        fh.write('    next_reload_tready = reload_tready;\n')
        fh.write('    next_config = 1\'b0;\n')
        fh.write('    case(state)\n')
        fh.write('        S_CONFIG :\n')
        fh.write('        begin\n')
        fh.write('            if (taps_addr_int == {}\'d{}) begin\n'.format(addr_bits, roll_over))
        fh.write('                next_state = S_IDLE;\n')
        fh.write('            end\n')
        fh.write('            if (state_d1 == S_IDLE) begin\n')
        fh.write('                next_taps_addr = 0;\n')
        fh.write('            end else begin\n')
        fh.write('                next_taps_addr = taps_addr_int + 1;\n')
        fh.write('            end\n')
        fh.write('            next_config = 1\'b1;\n')
        fh.write('        end\n')
        fh.write('        S_IDLE :\n')
        fh.write('        begin\n')
        fh.write('            if (sync_reset == 1\'b1 && sync_reset_d1 == 1\'b0) begin\n')
        fh.write('                next_state = S_CONFIG;\n')
        fh.write('                next_reload_tready = 1\'b0;\n')
        fh.write('            end else if (tap_take == 1\'b1 && s_axis_reload_tlast == 1\'b1) begin\n')
        fh.write('                next_state = S_CONFIG;\n')
        fh.write('                next_reload_tready = 1\'b0;\n')
        fh.write('            end else begin\n')
        fh.write('                next_state = S_IDLE;\n')
        fh.write('                next_reload_tready = 1\'b1;\n')
        fh.write('            end\n')
        fh.write('        end\n')
        fh.write('        default :\n')
        fh.write('        begin\n')
        fh.write('        end\n')
        fh.write('    endcase\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// write enable muxing .\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_wr_addr = wr_addr;\n')
        fh.write('    next_wr_data = wr_data;\n')
        fh.write('\n')
        fh.write('    next_new_coeffs = new_coeffs;\n')
        fh.write('    if (tap_take == 1\'b1) begin\n')
        fh.write('        next_wr_data = s_axis_reload_tdata[{}:0];\n'.format(tap_msb))
        fh.write('        if (new_coeffs == 1\'b1) begin\n')
        fh.write('            next_wr_addr = 0;\n')
        fh.write('            next_new_coeffs = 1\'b0;\n')
        fh.write('        end else begin\n')
        fh.write('            next_wr_addr = wr_addr + 1;\n')
        fh.write('            if (s_axis_reload_tlast == 1\'b1) begin\n')
        fh.write('                next_new_coeffs = 1\'b1;\n')
        fh.write('            end\n')
        fh.write('        end\n')
        fh.write('    end\n')
        fh.write('    // implements the write address pointer for tap updates.\n')
        fh.write('    if (config_d2 == 1\'b1) begin\n')
        fh.write('        case (taps_addr_d2[{}:{}])\n'.format(addr_msb, bot_msb + 1))
        for i in range(num_taps):
            offset = 1 << i
            fh.write('            {}\'d{}: next_taps_we = {}\'d{};\n'.format(top_bits, i, num_taps, offset))
        fh.write('            default: next_taps_we = {}\'d0;\n'.format(num_taps))
        fh.write('        endcase\n')
        fh.write('    end else begin\n')
        fh.write('        next_taps_we = {}\'d0;\n'.format(num_taps))
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// 3 cycle latency.\n')
        fh.write('{} coeff_mem (\n'.format(rom_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .wea(we),\n')
        fh.write('  .addra(wr_addr),\n')
        fh.write('  .dia(wr_data),\n')
        fh.write('  .addrb(taps_addr_int),\n')
        fh.write('  .dob(taps_douta)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return module_name


def gen_down_select(path, name='downselect', num_channels=512, tuser_width=24):
    file_name = '{}.v'.format(name)
    file_name = os.path.join(path, file_name)
    module_name = ret_module_name(file_name)
    tuser_msb = tuser_width - 1
    chan_msb = num_channels - 1
    addr_msb = int(np.ceil(np.log2(num_channels - 1))) - 1
    select_lines = int(np.ceil(np.log2(num_channels / 32)))
    num_selects = int(np.ceil(num_channels / 32))
    select_msb = select_lines - 1
    # generate mux - return delay value.
    print("==========================")
    print(" pipelined mux")
    print("")
    input_width = num_channels
    mux_out, pipe_latency = gen_pipe_mux(path, input_width, 1, mux_bits=3, one_hot=False, one_hot_out=False)
    print(mux_out)
    print("==========================")
    print("")

    with open(file_name, 'w') as fh:

        fh.write('//***************************************************************************--\n')
        fh.write('//\n')
        fh.write('// Author : PJV\n')
        fh.write('// File : {}.v\n'.format(module_name))
        fh.write('// Description : Module performs downselection of channel based on a selection\n')
        fh.write('// mask set from a FIFO interface\n')
        fh.write('//\n')
        fh.write('//***************************************************************************--\n')
        fh.write('\n')
        fh.write('// no timescale needed\n')
        fh.write('//\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('#(parameter DATA_WIDTH = 32)\n')
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [DATA_WIDTH-1:0] s_axis_tdata,\n')
        fh.write('    input [{}:0] s_axis_tuser,\n'.format(tuser_msb))
        fh.write('    input s_axis_tlast,\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    input eob_tag,\n')
        fh.write('\n')
        fh.write('    // down selection FIFO interface\n')
        fh.write('    input s_axis_select_tvalid,\n')
        fh.write('    input [31:0] s_axis_select_tdata,\n')
        fh.write('    input s_axis_select_tlast,\n')
        fh.write('    output s_axis_select_tready,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [DATA_WIDTH-1:0] m_axis_tdata,\n')
        fh.write('    output [{}:0] m_axis_tuser,\n'.format(tuser_msb))
        fh.write('    output m_axis_tlast,\n')
        fh.write('    output eob_downselect,\n')
        fh.write('    input m_axis_tready\n')
        fh.write('\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// downselection registers.\n')
        fh.write('reg [{}:0] select_reg = {}\'d0;\n'.format(chan_msb, num_channels))
        fh.write('reg [{}:0] next_select_reg = {}\'d0;\n'.format(chan_msb, num_channels))
        fh.write('reg [{}:0] select_addr, next_select_addr;\n'.format(select_msb))
        fh.write('reg select_take_d1;\n')
        fh.write('reg [31:0] select_dina, next_select_dina;\n')
        fh.write('wire select_take;\n')
        fh.write('reg select_tready;\n')
        fh.write('\n')
        fh.write('reg load_done, next_load_done, load_done_d1;\n')
        fh.write('\n')
        fh.write('reg [{}:0] take_d;\n'.format(pipe_latency - 1))
        fh.write('reg [{}:0] tlast_d;\n'.format(pipe_latency))
        fh.write('reg [{}:0] eob_tag_d;\n'.format(pipe_latency))
        fh.write('reg [DATA_WIDTH-1:0] tdata_d[0:{}];\n'.format(pipe_latency))
        fh.write('reg [{}:0] tuser_d[0:{}];\n'.format(tuser_msb, pipe_latency))
        fh.write('wire [{}:0] tuser_s, m_axis_tuser_s;\n'.format(tuser_width))
        fh.write('reg push, next_push;\n')
        fh.write('\n')
        fh.write('wire mask_value;\n')
        fh.write('\n')
        fh.write('// bit count registers.\n')
        fh.write('reg new_mask, next_new_mask;\n')
        fh.write('\n')
        fh.write('wire [{}:0] curr_channel, chan_out;\n'.format(addr_msb))
        fh.write('wire almost_full;\n')
        fh.write('wire take_data;\n')
        fh.write('\n')
        fh.write('// down selection signals.\n')
        fh.write('assign select_take = s_axis_select_tvalid & select_tready;\n')
        fh.write('assign take_data = s_axis_tvalid & ~almost_full & load_done_d1;\n')
        fh.write('assign s_axis_tready = ~almost_full & load_done_d1;\n')
        fh.write('assign curr_channel = s_axis_tuser[{}:0];\n'.format(addr_msb))
        fh.write('assign s_axis_select_tready = select_tready;\n')
        fh.write('assign tuser_s = {{eob_tag_d[{}], tuser_d[{}]}};\n'.format(pipe_latency, pipe_latency))
        fh.write('assign eob_downselect = m_axis_tuser_s[{}];\n'.format(tuser_width))
        fh.write('assign m_axis_tuser = m_axis_tuser_s[{}:0];\n'.format(tuser_msb))
        fh.write('\n')
        fh.write('always @(posedge clk, posedge sync_reset)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        select_tready <= 1\'b0;\n')
        fh.write('        select_addr <= {}\'d0;\n'.format(select_lines))
        fh.write('        select_dina <= 32\'d0;\n')
        fh.write('        new_mask <= 1\'b1;\n')
        fh.write('        load_done <= 1\'b0;\n')
        fh.write('        push <= 1\'b0;\n')
        fh.write('    end else begin\n')
        fh.write('        select_tready <= 1\'b1;\n')
        fh.write('        select_addr <= next_select_addr;\n')
        fh.write('        select_dina <= next_select_dina;\n')
        fh.write('        new_mask <= next_new_mask;\n')
        fh.write('        load_done <= next_load_done;\n')
        fh.write('        push <= next_push;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('integer n;\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    select_reg <= next_select_reg;\n')
        fh.write('    select_take_d1 <= select_take;\n')
        fh.write('    load_done_d1 <= load_done;\n')
        fh.write('\n')
        fh.write('    take_d <= {{take_d[{}:0], take_data}};\n'.format(pipe_latency - 2))
        fh.write('    tlast_d <= {{tlast_d[{}:0], s_axis_tlast}};\n'.format(pipe_latency - 1))
        fh.write('    eob_tag_d <= {{eob_tag_d[{}:0], eob_tag}};\n'.format(pipe_latency - 1))
        fh.write('\n')
        fh.write('    tdata_d[0] <= s_axis_tdata;\n')
        fh.write('    tuser_d[0] <= s_axis_tuser;\n')
        fh.write('    for (n=1;n<{}; n=n+1) begin\n'.format(pipe_latency + 1))
        fh.write('        tdata_d[n] <= tdata_d[n-1];\n')
        fh.write('        tuser_d[n] <= tuser_d[n-1];\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('// down selection register writes\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_select_addr = select_addr;\n')
        fh.write('    next_select_dina = select_dina;\n')
        fh.write('    next_new_mask = new_mask;\n')
        fh.write('    next_load_done = load_done;\n')
        fh.write('    if (select_take == 1\'b1) begin\n')
        fh.write('        next_select_dina = s_axis_select_tdata;\n')
        fh.write('        if (new_mask == 1\'b1) begin\n')
        fh.write('            next_select_addr = 0;\n')
        fh.write('            next_new_mask = 1\'b0;\n')
        fh.write('            next_load_done = 1\'b0;\n')
        fh.write('        end else begin\n')
        fh.write('            next_select_addr = select_addr + 1;\n')
        fh.write('            if (s_axis_select_tlast == 1\'b1) begin\n')
        fh.write('                next_new_mask = 1\'b1;\n')
        fh.write('                next_load_done = 1\'b1;\n')
        fh.write('            end\n')
        fh.write('        end\n')
        fh.write('    end\n')
        fh.write('    // implements the write address pointer for tap updates.\n')
        fh.write('    next_select_reg = select_reg;\n')
        fh.write('    if (select_take_d1 == 1\'b1) begin\n')
        fh.write('        case (select_addr)\n')
        for i in range(num_selects):
            lidx = 31 + i * 32
            ridx = i * 32
            fh.write('            {}\'d{}: next_select_reg[{}:{}] = select_dina;\n'.format(select_lines, i, lidx, ridx))
        fh.write('            default: next_select_reg[31:0] = select_dina;\n')
        fh.write('        endcase\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// selection logic.\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_push = 1\'b0;\n')
        fh.write('    if (take_d[{}] == 1\'b1 && mask_value == 1\'b1) begin  // output fifo is not full and not loading new select_reg.\n'.format(pipe_latency - 1))
        fh.write('        next_push = 1\'b1;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('// 4 tick delay\n')
        fh.write('{} u_pipe_mux\n'.format(ret_module_name(mux_out)))
        fh.write('(\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(sync_reset),\n')
        fh.write('    .valid_i(1\'b1),\n')
        fh.write('    .sel(curr_channel),\n')
        fh.write('    .input_word(select_reg),\n')
        fh.write('    .valid_o(),\n')
        fh.write('    .sel_o(chan_out),\n')
        fh.write('    .output_word(mask_value)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('// Output fifo\n')
        fh.write('axi_fifo_51 #(\n')
        fh.write('    .DATA_WIDTH(32),\n')
        fh.write('    .ALMOST_FULL_THRESH(20),\n')
        fh.write('    .TUSER_WIDTH({}),\n'.format(tuser_width + 1))
        fh.write('    .ADDR_WIDTH(5))\n')
        fh.write('u_fifo(\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(sync_reset),\n')
        fh.write('    .s_axis_tvalid(push),\n')
        fh.write('    .s_axis_tdata(tdata_d[{}]),\n'.format(pipe_latency))
        fh.write('    .s_axis_tlast(tlast_d[{}]),\n'.format(pipe_latency))
        fh.write('    .s_axis_tuser(tuser_s),\n')
        fh.write('    .s_axis_tready(),\n')
        fh.write('    .almost_full(almost_full),\n')
        fh.write('    .m_axis_tvalid(m_axis_tvalid),\n')
        fh.write('    .m_axis_tdata(m_axis_tdata),\n')
        fh.write('    .m_axis_tlast(m_axis_tlast),\n')
        fh.write('    .m_axis_tuser(m_axis_tuser_s),\n')
        fh.write('    .m_axis_tready(m_axis_tready));\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return file_name


def gen_exp_shift_rtl(path, chan_obj, cic_obj):
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)

    iw = chan_obj.qvec[0]

    avg_len = cic_obj.M
    avg_bits = ret_num_bitsU(avg_len)

    data_width = iw * 2
    Mmax = chan_obj.Mmax

    filter_bits = cic_obj.qvec_out[0]
    fft_bits = ret_num_bitsU(Mmax)
    fft_msb = ret_num_bitsU(Mmax - 1) - 1

    idx_bytes = int(np.ceil(ret_num_bitsU(Mmax - 1) / 8.))
    tuser_bits = idx_bytes * 8 + 8
    

    # ipdb.set_trace()
    mod_name = 'exp_shifter_{}Mmax_{}iw_{}avg_len'.format(Mmax, iw, avg_len)

    file_name = name_help(mod_name, path)

    with open(file_name, 'w') as fh:

        fh.write('//*****************************************************************************\n')
        fh.write('//\n')
        fh.write('// Since the fft is block floating point the apparent signal amplitude can be shifted\n')
        fh.write('// in consecutive fft blocks.  The Exponent shifter, exp_shifter, implements a simple\n')
        fh.write('// low pass filtering the shift signal and provides gain correction mechanism for mitigating\n')
        fh.write('// the amplitude shifts caused by the fft module.  The module also provides buffering\n')
        fh.write('// and flow control logic so that it can directly connected to the rest of the\n')
        fh.write('// infrastructure.\n')
        fh.write('//*****************************************************************************\n')
        fh.write('\n')
        fh.write('// no timescale needed\n')
        fh.write('\n')
        fh.write('module {}#(\n'.format(mod_name))
        fh.write('    parameter HEAD_ROOM = 7\'d2)\n')
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [{}:0] s_axis_tdata,\n'.format(data_width - 1))
        fh.write('    input [{}:0] s_axis_tuser,\n'.format(tuser_bits - 1))
        fh.write('    input s_axis_tlast,\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    input [{}:0] fft_size,\n'.format(fft_bits - 1))
        fh.write('    input [{}:0] avg_len,\n'.format(avg_bits - 1))
        fh.write('    output eob_tag,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [{}:0] m_axis_tdata,\n'.format(data_width - 1))
        fh.write('    output [{}:0] m_axis_tuser,\n'.format(tuser_bits - 1))
        fh.write('    output m_axis_tlast,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('wire s_axis_tready_s;  // delay signals\n')
        fh.write('\n')
        fh.write('reg [{}:0] tdatai[0:22];\n'.format(iw - 1))
        fh.write('reg [{}:0] tdataq[0:22];\n'.format(iw - 1))
        fh.write('\n')
        fh.write('reg [{}:0] tuser_d[0:23];\n'.format(tuser_bits - 1))
        fh.write('reg [23:0] tlast_d;\n')
        fh.write('reg [23:0] take_d;\n')
        fh.write('\n')
        fh.write('wire [47:0] pcorr_i, pcorr_q;\n')
        fh.write('wire filter_tready;\n')
        fh.write('reg [{}:0] i_val, next_i_val;\n'.format(iw - 1))
        fh.write('reg [{}:0] q_val, next_q_val;\n'.format(iw - 1))
        fh.write('wire [{}:0] fifo_tdata;\n'.format(data_width - 1))
        fh.write('wire [4:0] filter_tdata;\n')
        fh.write('wire filter_tvalid, filter_out_tvalid;\n')
        fh.write('wire [{}:0] filter_out_tdata;\n'.format(filter_bits - 1))
        fh.write('reg [{}:0] filter_d, next_filter_d;\n'.format(filter_bits - 1))
        fh.write('wire [4:0] filter_whole;\n')
        fh.write('reg [4:0] filter_whole_d;\n')
        fh.write('\n')
        fh.write('wire chan_0;\n')
        fh.write('wire [{}:0] fft_bin;\n'.format(fft_msb))
        fh.write('\n')
        fh.write('reg signed [5:0] sub_out, next_sub_out;\n')
        fh.write('reg signed [6:0] shift_val;\n')
        fh.write('\n')
        fh.write('wire [4:0] curr_shift;\n')
        fh.write('wire almost_full;\n')
        fh.write('wire take;\n')
        fh.write('wire [{}:0] m_axis_tuser_s;\n'.format(tuser_bits - 1))
        fh.write('\n')
        fh.write('assign take = (s_axis_tvalid == 1\'b1 && s_axis_tready_s == 1\'b1) ? 1\'b1 : 1\'b0;\n')
        fh.write('assign s_axis_tready_s = (almost_full == 1\'b0) ? 1\'b1 : 1\'b0;\n')
        fh.write('assign s_axis_tready = s_axis_tready_s;\n')
        fh.write('assign fft_bin = tuser_d[20][{}:0];\n'.format(fft_msb))
        lidx = cic_obj.qvec_out[0] - 1
        ridx = cic_obj.qvec_out[1]
        fh.write('assign filter_whole = filter_d[{}:{}];\n'.format(lidx, ridx))
        fh.write('\n')
        fh.write('assign eob_tag = m_axis_tuser_s[{}];\n'.format(tuser_bits - 1))
        fh.write('assign m_axis_tuser = m_axis_tuser_s;\n')
        fh.write('assign fifo_tdata = {i_val, q_val};\n')
        fh.write('\n')
        fh.write('assign chan_0 = (fft_bin == {}\'d0 && take_d[20] == 1\'b1) ? 1\'b1 : 1\'b0;\n'.format(fft_msb + 1))
        fh.write('\n')
        ridx = idx_bytes * 8
        lidx = ridx + 4
        fh.write('assign filter_tdata = s_axis_tuser[{}:{}];\n'.format(lidx, ridx))
        fh.write('assign filter_tvalid = (take == 1\'b1 && s_axis_tuser[{}:0] == {}\'d0) ? 1\'b1 : 1\'b0;\n'.format(fft_msb, fft_msb + 1))
        fh.write('assign curr_shift = tuser_d[20][{}:{}];\n'.format(lidx, ridx))
        fh.write('\n')
        pad_size = (48 - iw) // 2
        fh.write(
            'assign pcorr_i = {{ {{{}{{tdatai[22][{}]}}}}, tdatai[22], {{{{{}{{tdatai[22][0]}}}}}} }};\n'.format(pad_size, iw-1, pad_size))
        fh.write(
            'assign pcorr_q = {{ {{{}{{tdataq[22][{}]}}}}, tdataq[22], {{{{{}{{tdataq[22][0]}}}}}} }};\n'.format(pad_size, iw-1, pad_size))
        fh.write('\n')
        fh.write('\n')
        fh.write('  // main clock process\n')
        fh.write('always @(posedge clk, posedge sync_reset) begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        filter_d <= 0;\n')
        fh.write('        i_val <= 0;\n')
        fh.write('        q_val <= 0;\n')
        fh.write('        sub_out <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        filter_d <= next_filter_d;\n')
        fh.write('        i_val <= next_i_val;\n')
        fh.write('        q_val <= next_q_val;\n')
        fh.write('        sub_out <= next_sub_out;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('integer m;\n')
        fh.write('always @(posedge clk) begin\n')
        fh.write('    shift_val <= $signed({{1{sub_out[5]}},sub_out}) - $signed(HEAD_ROOM);\n')
        fh.write('    take_d <= {take_d[22:0], take};\n')
        fh.write('    tlast_d <= {tlast_d[22:0], s_axis_tlast};\n')
        fh.write('\n')
        fh.write('    tdatai[0] <= s_axis_tdata[31:16];\n')
        fh.write('    tdataq[0] <= s_axis_tdata[15:0];\n')
        fh.write('    for (m=1; m<23; m=m+1) begin\n')
        fh.write('        tdatai[m] <= tdatai[m-1];\n')
        fh.write('        tdataq[m] <= tdataq[m-1];\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    tuser_d[0] <= {{s_axis_tlast, s_axis_tuser[{}:0]}};\n'.format(tuser_bits - 2))
        fh.write('    for (m=1; m<24; m=m+1) begin\n')
        fh.write('        tuser_d[m] <= tuser_d[m-1];\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    filter_whole_d <= filter_whole;\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    // 1 tick delay\n')
        fh.write('    next_filter_d = filter_d;\n')
        fh.write('    if (filter_tvalid == 1\'b1) begin\n')
        fh.write('        next_filter_d = filter_out_tdata;\n')
        fh.write('    end\n')
        fh.write('    next_sub_out = sub_out;\n')
        fh.write('    if (chan_0 == 1\'b1) begin\n')
        fh.write(
            '        next_sub_out = $signed({{1{curr_shift[4]}} ,curr_shift}) - $signed({{1{filter_whole_d[4]}}, filter_whole_d});\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('  // latency = 1\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    case(shift_val)\n')
        for i in range(8):
            lidx = pad_size + iw - 1 - i
            ridx = pad_size - i
            fh.write('        7\'d{} :\n'.format(i))
            fh.write('        begin\n')
            fh.write('            next_i_val = pcorr_i[{}:{}];\n'.format(lidx, ridx))
            fh.write('            next_q_val = pcorr_q[{}:{}];\n'.format(lidx, ridx))
            fh.write('        end\n')

        for i in range(1, 8):
            lidx = pad_size + iw - 1 + i
            ridx = pad_size + i
            fh.write('        -7\'d{} :\n'.format(i))
            fh.write('        begin\n')
            fh.write('            next_i_val = pcorr_i[{}:{}];\n'.format(lidx, ridx))
            fh.write('            next_q_val = pcorr_q[{}:{}];\n'.format(lidx, ridx))
            fh.write('        end\n')

        fh.write('        default :\n')
        fh.write('        begin\n')
        fh.write('            if (shift_val[6] == 1\'b1) begin\n')
        lidx = pad_size + iw - 1 + 7
        ridx = pad_size + 7
        fh.write('                next_i_val = pcorr_i[{}:{}];\n'.format(lidx, ridx))
        fh.write('                next_q_val = pcorr_q[{}:{}];\n'.format(lidx, ridx))
        fh.write('            end else begin\n')
        lidx = pad_size + iw - 1 - 7
        ridx = pad_size - 7
        fh.write('                next_i_val = pcorr_i[{}:{}];\n'.format(lidx, ridx))
        fh.write('                next_q_val = pcorr_q[{}:{}];\n'.format(lidx, ridx))
        fh.write('            end\n')
        fh.write('        end\n')
        fh.write('    endcase\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// 20 tick delay\n')
        fh.write('cic_M{}_N1_R1_iw5_0 u_avg_filter(\n'.format(avg_len))
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(sync_reset),\n')
        fh.write('    .msetting(avg_len),\n')
        fh.write('    .s_axis_tvalid(filter_tvalid),\n')
        fh.write('    .s_axis_tdata(filter_tdata),\n')
        fh.write('    .s_axis_tready(filter_tready),\n')
        fh.write('    .m_axis_tvalid(filter_out_tvalid),\n')
        fh.write('    .m_axis_tready(1\'b1),\n')
        fh.write('    .m_axis_tdata(filter_out_tdata));\n')
        fh.write('\n')
        fh.write('// Output fifo\n')
        fh.write('axi_fifo_51 #(\n')
        fh.write('    .DATA_WIDTH({}),\n'.format(data_width))
        fh.write('    .ALMOST_FULL_THRESH(16),\n')
        fh.write('    .TUSER_WIDTH({}),\n'.format(tuser_bits))
        fh.write('    .ADDR_WIDTH(6))\n')
        fh.write('u_fifo(\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(sync_reset),\n')
        fh.write('    .s_axis_tvalid(take_d[23]),\n')
        fh.write('    .s_axis_tdata(fifo_tdata),\n')
        fh.write('    .s_axis_tlast(tlast_d[23]),\n')
        fh.write('    .s_axis_tuser(tuser_d[23]),\n')
        fh.write('    .s_axis_tready(),\n')
        fh.write('    .almost_full(almost_full),\n')
        fh.write('    .m_axis_tvalid(m_axis_tvalid),\n')
        fh.write('    .m_axis_tdata(m_axis_tdata),\n')
        fh.write('    .m_axis_tlast(m_axis_tlast),\n')
        fh.write('    .m_axis_tuser(m_axis_tuser_s),\n')
        fh.write('    .m_axis_tready(m_axis_tready));\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return file_name


def gen_sim_vh(path):
    """
        Helper function generates chan_sim.vh file.

    """
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)
    mod_name = 'chan_sim.vh'

    file_name = path + mod_name

    with open(file_name, 'w') as fh:
        fh.write('//\n')
        fh.write('// Macros used only in Simulation\n')
        fh.write('//\n')
        fh.write('//\n')
        fh.write('`ifndef SIM_BIN_WRITE\n')
        fh.write('//`define SIM_BIN_WRITE 1\n')
        fh.write('`endif\n')



# def gen_sim_vh(path):
    
#     assert(path is not None), 'User must specify Path'
#     path = ret_valid_path(path)

#     mod_name = 'chan_sim.vh'
#     file_name = name_help(mod_name, path)
#     with open(file_name, 'w') as fh:    
#         fh.write('`ifndef SIM_BIN_WRITE\n')
#         fh.write('`define SIM_BIN_WRITE 1\n')
#         fh.write('`endif\n')

