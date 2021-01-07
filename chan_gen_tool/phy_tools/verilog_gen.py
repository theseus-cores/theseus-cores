#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author: pjvalla
"""
import os

import numpy as np

from itertools import count
import copy
import ipdb  # analysis:ignore

from phy_tools import fp_utils
from phy_tools.fp_utils import ret_num_bitsU
from phy_tools.gen_utils import ret_module_name, ret_file_name, ret_valid_path, print_header
from phy_tools.vgen_xilinx import gen_dsp48E1
from phy_tools.vgen_altera import altera_mult, altera_madd

# from dsp_opts import opcode_opts
import numpy as np  #analysis:ignore
import datetime

from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    __version__ = today.strftime("%Y.%m.%d")


def adder_pipeline(cnt_width):
    return int(np.ceil((cnt_width - 1) / 8.))


def name_help(mod_name, path=None):
    if path is not None:
        file_name = path + mod_name + '.v'
    else:
        file_name = './' + mod_name + '.v'

    return file_name

def ret_addr_width(depth):
    fifo_depth = 2 ** int(np.ceil(np.log2(depth)))
    if fifo_depth < 8:
        fifo_depth = 8
    fifo_addr_width = int(np.log2(fifo_depth))

    return fifo_addr_width


def logic_rst(fh, prefix='a_d', cnt=1, sp=''):
    for jj in range(cnt):
        fh.write('{}{}[{}] <= 0;\n'.format(sp, prefix, jj))


def logic_gate(fh, prefix='a_d', str_val='a', cnt=1, sp=''):
    for jj in range(cnt):
        rside = str_val if (jj == 0) else '{}[{}]'.format(prefix, jj - 1)
        fh.write('{}{}[{}] <= {};\n'.format(sp, prefix, jj, rside))


def gen_cnt_sigs(fh, prefix='cnt', pdelay=2):
    for jj in range(pdelay):
        fh.write('reg [8:0] {}_nib{}, next_{}_nib{};\n'.format(prefix, jj, prefix, jj))

    fh.write('\n')
    for jj in range(pdelay - 1):
        for nn in range(pdelay - jj - 1):
            # fh.write('reg [8:0] {}_nib{}_d{}, next_{}_nib{}_d{};\n'.format(prefix, jj, nn, prefix, jj, nn))
            fh.write('reg [7:0] {}_nib{}_d{};\n'.format(prefix, jj, nn))
        fh.write('\n')

def gen_cnt_rst(fh, prefix='cnt', pdelay=2, sp='', reset_list=None):
    for jj in range(pdelay):
        if reset_list is None:
            fh.write('{}{}_nib{} <= 0;\n'.format(sp, prefix, jj))
        else:
            fh.write('{}{}_nib{} <= {};\n'.format(sp, prefix, jj, reset_list[jj]))

def gen_cnt_regs(fh, prefix='cnt', pdelay=2):
    for jj in range(pdelay):
        fh.write('        {}_nib{} <= next_{}_nib{};\n'.format(prefix, jj, prefix, jj))


def gen_cnt_delay(fh, prefix='cnt', pdelay=2, tab=''):
    for jj in range(pdelay - 1):
        for nn in range(pdelay - jj - 1):
            if nn == 0:
                fh.write('    {}{}_nib{}_d{} <= {}_nib{}[7:0];\n'.format(tab, prefix, jj, nn, prefix, jj))
            else:
                fh.write('    {}{}_nib{}_d{} <= {}_nib{}_d{};\n'.format(tab, prefix, jj, nn, prefix, jj, nn - 1))
        fh.write('\n')


def gen_cnt_fback(fh, prefix='cnt', pdelay=2):
    for jj in range(pdelay):
            fh.write('    next_{}_nib{} = {}_nib{};\n'.format(prefix, jj, prefix, jj))


def gen_cnt_vec(prefix='cnt', pdelay=2, max_width=16):
    str_val = ''
    for jj in reversed(range(pdelay - 1)):
        delay_val = pdelay - 2 - jj
        str_val = str_val + ', {}_nib{}_d{}[7:0]'.format(prefix, jj, delay_val)

    remain_val = 7 - (pdelay * 8 - max_width)
    str_val = '{{{}_nib{}[{}:0]'.format(prefix, pdelay - 1, remain_val) + str_val + '};\n'

    return str_val


def pad_str(pad, prefix, input_msb, input_lsb):
    if pad > 0:
        pad_str = '{{{}{{{}[{}]}}, {}[{}:{}]}}'.format(pad, prefix, input_msb, prefix, input_msb, input_lsb)
    else:
        pad_str = '{}[{}:{}]'.format(prefix, input_msb, input_lsb)
    return pad_str


def gen_occ_logic(fh, tot_latency, start_sig=False):
    str_val = ''
    if start_sig:
        str_val = ' && (start_sig == 1\'b1 || (gate_latch == 1\'b1 && final_cnt == 1\'b0))'
    fh.write('    if (take_data == 1\'b1 {}) begin\n'.format(str_val))
    fh.write('        next_occ_reg[0] = take_data;\n')
    for jj in range(1, tot_latency):
        fh.write('        next_occ_reg[{}] = occ_reg[{}];\n'.format(jj, jj - 1))
    fh.write('    end else if (send_data == 1\'b1) begin\n')
    fh.write('        next_occ_reg[0] = 1\'b0;\n')
    for jj in range(1, tot_latency):
        fh.write('        next_occ_reg[{}] = occ_reg[{}];\n'.format(jj, jj - 1))
    fh.write('    end\n')
    fh.write('end\n')

def axi_fifo_inst(fh, fifo_name, data_width, addr_width, af_thresh=None, ae_thresh=None, inst_name='u_fifo', tuser_width=0, tlast=False,
                  s_tvalid_str='s_axis_tvalid', s_tdata_str='s_axis_tdata', s_tlast_str='s_axis_tlast', max_delay=0,
                  s_tuser_str='s_axis_tuser', s_tready_str='', almost_full_str='almost_full', delay_str=None,
                  m_tvalid_str='m_axis_tvalid', m_tlast_str='m_axis_tlast', m_tuser_str='m_axis_tuser',
                  m_tdata_str='m_axis_tdata', m_tready_str='m_axis_tready'):

    fh.write('{} #(\n'.format(fifo_name))
    fh.write('    .DATA_WIDTH({}),\n'.format(data_width))
    if af_thresh is not None:
        fh.write('    .ALMOST_FULL_THRESH({}),\n'.format(af_thresh))
    if ae_thresh is not None:
        fh.write('    .ALMOST_EMPTY_THRESH({}),\n'.format(ae_thresh))
    if tuser_width > 0:
        fh.write('    .TUSER_WIDTH(TUSER_WIDTH),\n')
    fh.write('    .ADDR_WIDTH({}))\n'.format(addr_width))
    fh.write('{}\n'.format(inst_name))
    fh.write('(\n')
    fh.write('    .clk(clk),\n')
    fh.write('    .sync_reset(sync_reset),\n')
    fh.write('\n')
    fh.write('    .s_axis_tvalid({}),\n'.format(s_tvalid_str))
    fh.write('    .s_axis_tdata({}),\n'.format(s_tdata_str))
    if tuser_width > 0:
        fh.write('    .s_axis_tuser({}),\n'.format(s_tuser_str))
    if tlast:
        fh.write('    .s_axis_tlast({}),\n'.format(s_tlast_str))

    fh.write('    .s_axis_tready({}),\n'.format(s_tready_str))
    if af_thresh is not None:
        fh.write('\n')
        fh.write('    .almost_full({}),\n'.format(almost_full_str))
    if max_delay > 0:
        fh.write('\n')
        fh.write('    .delay({}),\n'.format(delay_str))
    fh.write('\n')
    fh.write('    .m_axis_tvalid({}),\n'.format(m_tvalid_str))
    fh.write('    .m_axis_tdata({}),\n'.format(m_tdata_str))
    if tuser_width > 0:
        fh.write('    .m_axis_tuser({}),\n'.format(m_tuser_str))
    if tlast:
        fh.write('    .m_axis_tlast({}),\n'.format(m_tlast_str))
    fh.write('    .m_axis_tready({})\n'.format(m_tready_str))
    fh.write(');\n')

def ret_mult_eight(input_val):
    return int(np.ceil(input_val / 8.)) * 8

def gen_cordic(path, qvec_in=(16, 15), output_width=16, num_iters=6, function='vector', prefix='', tuser_width=0, tlast=False):
    """
        Generates logic for Cordic core. User specifies bitwidths and number of iterations

        ==========
        Parameters
        ==========

            qvec_in : Input quantization vector.
            output_width : I and Q output widths.
            num_iters : number of cordic rotations (includes coarse correction)
            function : String specifying Cordic function approximation.
            prefix : Naming prefix.

    """
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)
    input_width = qvec_in[0]

    mod_name = '{}cordic_{}_{}iw_{}iters'.format(prefix, function, input_width, num_iters)
    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)

    input_msb = 2 * qvec_in[0] - 1
    frac_bits = qvec_in[0] - qvec_in[1]
    output_msb = 2 * output_width - 1
    corr_qvec = (25, 25 - frac_bits)
    angle_qvec = (output_width, output_width - frac_bits)
    int_msb = output_width - 1
    tot_latency = num_iters + 4 + 1
    fifo_addr_width = ret_addr_width(tot_latency * 2)
    almost_full_thresh = 1 << (fifo_addr_width - 1)

    with open(file_name, "w") as fh:

        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : PJV\n')
        fh.write('// File        : {}\n'.format(mod_name))
        fh.write('// Description : Cordic ({} operation).\n'.format(function))
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('module {}\n'.format(mod_name))
        if tuser_width:
            fh.write('#(   parameter TUSER_WIDTH=8)\n')
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [{}:0] s_axis_tdata,\n'.format(input_msb))
        if tuser_width:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        if tlast:
            fh.write('    input s_axis_tlast;\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        if tuser_width:
            fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        if tlast:
            fh.write('    output m_axis_tlast;\n')
        fh.write('    output [{}:0] m_axis_tdata,  // Magnitude and Phase vectors\n'.format(output_msb))
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        if tuser_width:
            fh.write('parameter TUSER_MSB = TUSER_WIDTH - 1;\n')
            fh.write('reg [TUSER_MSB:0] tuser_reg[0:{}];\n'.format(tot_latency - 1))
        if tlast:
            fh.write('reg [{}:0] tlast_d;\n'.format(tot_latency - 1))
        for ii in range(1, num_iters):
            fh.write('reg signed [{}:0] x_{}, next_x_{};\n'.format(int_msb, ii, ii))
        for ii in range(1, num_iters):
            fh.write('reg signed [{}:0] y_{}, next_y_{};\n'.format(int_msb, ii, ii))
        for ii in range(1, num_iters):
            fh.write('reg signed [{}:0] z_{}, next_z_{};\n'.format(int_msb, ii, ii))
        fh.write('\n')
        fh.write('wire signed [{}:0] x_0, y_0, z_0;\n'.format(int_msb))
        fh.write('\n')
        # corr_value = 1. / np.sqrt(1. + 2. ** (-2. * num_iters))
        corr_value = np.prod([1. / np.sqrt(1. + 2. ** (-2. * n_val)) for n_val in range(num_iters)])
        corr_fi = fp_utils.sfi(vec=corr_value, qvec=corr_qvec)
        # print(corr_fi.vec)
        fh.write('wire signed [24:0] CORD_CORR = 25\'d{};\n'.format(corr_fi.vec[0]))
        fh.write('\n')
        angle_values = [.5, -.5, 0]
        angle_fi = fp_utils.sfi(angle_values, qvec=angle_qvec)
        fh.write('wire signed [{}:0] PI_OVER2 = {}\'d{};\n'.format(int_msb, output_width, angle_fi.vec[0]))
        fh.write('wire signed [{}:0] NEG_PI_OVER2 = {}\'d{};\n'.format(int_msb, output_width, angle_fi.udec[1]))
        fh.write('wire signed [{}:0] ZERO = {}\'d{};\n'.format(int_msb, output_width, angle_fi.vec[2]))
        fh.write('\n')
        fh.write('reg [{}:0] valid_d, next_valid_d;\n'.format(tot_latency - 1))
        fh.write('reg [{}:0] angle, next_angle;\n'.format(int_msb))
        fh.write('reg [{}:0] angle_d1, angle_d2, angle_d3, angle_d4;\n'.format(int_msb))
        fh.write('\n')
        fh.write('wire take_data;\n')
        fh.write('wire almost_full;\n')
        # fh.write('wire ce;\n')
        # fh.write('reg ce_d0;\n')
        fh.write('\n')
        atan_values = [np.arctan(2. ** -n) for n in range(num_iters - 1)]
        atan_fi = fp_utils.sfi(atan_values, qvec=angle_qvec)
        for ii in range(num_iters - 1):
            fh.write('wire [{}:0] atan_val_{} = {}\'d{};\n'.format(int_msb, ii, output_width, atan_fi.vec[ii]))
        fh.write('\n')
        fh.write('reg opcode0, next_opcode0;\n')
        fh.write('reg opcode1, next_opcode1;\n')
        fh.write('wire [{}:0] fifo_tdata;\n'.format(input_width * 2 - 1))
        fh.write('\n')
        # fh.write('reg [24:0] a_term, next_a_term;\n')
        fh.write('reg [17:0] b_termx, next_b_termx;\n')
        fh.write('reg [17:0] b_termy, next_b_termy;\n')
        fh.write('\n')
        fh.write('wire [47:0] x_corr, y_corr;\n')
        fh.write('\n')
        fh.write('wire [17:0] i_input, q_input;\n')
        fh.write('\n')
        fh.write('assign take_data = s_axis_tvalid & s_axis_tready & !sync_reset;\n')
        # fh.write('assign send_data = (m_axis_tready & occ_reg[{}]) | (~occ_reg[{}] && occ_reg != 0);\n'.format(tot_latency - 1, tot_latency - 1))  #analysis:ignore
        fh.write('assign s_axis_tready = ~almost_full;\n')
        # fh.write('assign ce = send_data;\n')
        # fh.write('assign m_axis_tvalid = occ_reg[{}];\n'.format(tot_latency - 1))
        fh.write('assign fifo_tdata = {{z_{}, x_{}}};\n'.format(num_iters - 1, num_iters - 1))
        pad = 18 - input_width
        if pad > 0:
            tup_value0 = (pad, input_width - 1, input_width - 1)
            tup_value1 = (pad, input_msb, input_msb, input_width)
            fh.write('assign i_input = {{{{{}{{s_axis_tdata[{}]}}}},s_axis_tdata[{}:0]}};\n'.format(*tup_value0))
            fh.write('assign q_input = {{{{{}{{s_axis_tdata[{}]}}}},s_axis_tdata[{}:{}]}};\n'.format(*tup_value1))
        else:
            tup_value0 = (input_width - 1)
            tup_value1 = (input_msb, input_width)
            # ipdb.set_trace()
            fh.write('assign i_input = s_axis_tdata[{}:0];\n'.format(input_width - 1))
            fh.write('assign q_input = s_axis_tdata[{}:{}];\n'.format(*tup_value1))

        # fh.write('assign s_axis_tready = (~occ_reg[{}] | m_axis_tready) ? 1\'b1 : 1\'b0;\n'.format(tot_latency - 1))
        fh.write('\n')
        mult_frac = corr_qvec[1] + qvec_in[1]
        mult_msb = mult_frac + frac_bits
        rindx = mult_msb - output_width + 1
        fh.write('assign x_0 = x_corr[{}:{}];\n'.format(mult_msb, rindx))
        fh.write('assign y_0 = y_corr[{}:{}];\n'.format(mult_msb, rindx))
        fh.write('assign z_0 = angle_d4;\n')
        fh.write('\n')
        # fh.write('always @*\n')
        # fh.write('begin\n')
        # # fh.write('    next_occ_reg = occ_reg;\n')
        # fh.write('    next_angle_d0 = angle_d0;\n')
        # fh.write('    next_angle_d1 = angle_d1;\n')
        # fh.write('    next_angle_d2 = angle_d2;\n')
        # fh.write('    next_angle_d3 = angle_d3;\n')
        # fh.write('    if (send_data == 1\'b1) begin\n')
        # fh.write('        next_angle_d0 = angle;\n')
        # fh.write('        next_angle_d1 = angle_d0;\n')
        # fh.write('        next_angle_d2 = angle_d1;\n')
        # fh.write('        next_angle_d3 = angle_d2;\n')
        # fh.write('    end\n')
        # fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        angle <= 0;\n')
        fh.write('\n')
        fh.write('    end else begin\n')
        fh.write('        angle <= next_angle;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')

        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    angle_d1 <= angle;\n')
        fh.write('    angle_d2 <= angle_d1;\n')
        fh.write('    angle_d3 <= angle_d2;\n')
        fh.write('    angle_d4 <= angle_d3;\n')
        if tuser_width:
            fh.write('    tuser_reg[0] <= s_axis_tuser;\n')
            for ii in range(1, tot_latency):
                fh.write('    tuser_reg[{}] <= tuser_reg[{}];\n'.format(ii, ii - 1))
        if tlast:
            fh.write('    tlast_d <= {{tlast_d[{}:0], s_axis_tlast}};\n'.format(tot_latency - 2))

        fh.write('    valid_d <= {{valid_d[{}:0], take_data}};\n'.format(tot_latency - 2))
        fh.write('end\n')
        fh.write('// two functions A*B and -A*B\n')
        funcs = ['A*B', '-A*B']
        (dsp_file, dsp_name) = gen_dsp48E1(path, mod_name, opcode=funcs, areg=2, breg=2, use_ce=False)
        print(dsp_name)
        fh.write('// latency = 4\n')
        fh.write('{} x_mac (\n'.format(dsp_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .opcode(opcode0),\n')
        fh.write('  .a(CORD_CORR),\n')
        fh.write('  .b(b_termx),\n')
        fh.write('  .p(x_corr)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('{} y_mac (\n'.format(dsp_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .opcode(opcode1),\n')
        fh.write('  .a(CORD_CORR),\n')
        fh.write('  .b(b_termy),\n')
        fh.write('  .p(y_corr)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        for ii in range(1, num_iters):
            fh.write('    x_{} <= next_x_{};\n'.format(ii, ii))
        fh.write('\n')
        for ii in range(1, num_iters):
            fh.write('    y_{} <= next_y_{};\n'.format(ii, ii))
        fh.write('\n')
        for ii in range(1, num_iters):
            fh.write('    z_{} <= next_z_{};\n'.format(ii, ii))
        fh.write('\n')
        fh.write('    a_term <= next_a_term;\n')
        fh.write('    b_termx <= next_b_termx;\n')
        fh.write('    b_termy <= next_b_termy;\n')
        fh.write('    opcode0 <= next_opcode0;\n')
        fh.write('    opcode1 <= next_opcode1;\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('\n')
        for ii in range(1, num_iters):
            fh.write('    next_x_{} = x_{};\n'.format(ii, ii))
        fh.write('\n')
        for ii in range(1, num_iters):
            fh.write('    next_y_{} = y_{};\n'.format(ii, ii))
        fh.write('\n')
        for ii in range(1, num_iters):
            fh.write('    next_z_{} = z_{};\n'.format(ii, ii))
        fh.write('\n')
        fh.write('    next_opcode0 = opcode0;\n')
        fh.write('    next_opcode1 = opcode1;\n')
        fh.write('\n')
        fh.write('    if (i_input[{}] == 1\'b1 && q_input[{}] == 1\'b1) begin\n'.format(int_msb, int_msb))
        fh.write('        next_b_termx = q_input;\n')
        fh.write('        next_b_termy = i_input;\n')
        fh.write('        next_opcode0 = 1\'b1;\n')
        fh.write('        next_opcode1 = 1\'b0;\n')
        fh.write('        next_angle = NEG_PI_OVER2;\n')
        fh.write('\n')
        fh.write('    end else if (i_input[{}] == 1\'b1 && q_input[{}] == 1\'b0) begin\n'.format(int_msb, int_msb))
        fh.write('        next_b_termx = q_input;\n')
        fh.write('        next_b_termy = i_input;\n')
        fh.write('        next_opcode0 = 1\'b0;\n')
        fh.write('        next_opcode1 = 1\'b1;\n')
        fh.write('        next_angle = PI_OVER2;\n')
        fh.write('    end else begin\n')
        fh.write('        next_b_termx = i_input;\n')
        fh.write('        next_b_termy = q_input;\n')
        fh.write('        next_opcode0 = 1\'b0;\n')
        fh.write('        next_opcode1 = 1\'b0;\n')
        fh.write('        next_angle = ZERO;\n')
        fh.write('    end\n')
        fh.write('\n')
        # fh.write('    if (send_data == 1\'b1) begin\n')
        for ii in range(1, num_iters):
            fh.write('    if (y_{}[{}] == 1\'b1) begin\n'.format(ii - 1, int_msb))
            fh.write('        next_x_{} = x_{} - (y_{} >>> {});\n'.format(ii, ii - 1, ii - 1, ii))
            fh.write('        next_y_{} = y_{} + (x_{} >>> {});\n'.format(ii, ii - 1, ii - 1, ii))
            fh.write('        next_z_{} = z_{} - atan_val_{};\n'.format(ii, ii - 1, ii - 1))
            fh.write('    end else begin\n')
            fh.write('        next_x_{} = x_{} + (y_{} >>> {});\n'.format(ii, ii - 1, ii - 1, ii))
            fh.write('        next_y_{} = y_{} - (x_{} >>> {});\n'.format(ii, ii - 1, ii - 1, ii))
            fh.write('        next_z_{} = z_{} + atan_val_{};\n'.format(ii, ii - 1, ii - 1))
            fh.write('    end\n')
        fh.write('\n')
        # fh.write('    end\n')
        fh.write('\n')
        fh.write('end\n\n')
        # insert axi fifo for interface compliance
        (_, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, tlast=tlast, almost_full=True, almost_empty=False,
                                      count=False, max_delay=0, ram_style='distributed', prefix='')
        print(fifo_name)

        axi_fifo_inst(fh, fifo_name, inst_name='axi_fifo', data_width=input_width*2, af_thresh=almost_full_thresh,
                      addr_width=fifo_addr_width, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='valid_d[{}]'.format(tot_latency-1),
                      s_tdata_str='fifo_tdata', s_tuser_str='tuser_reg[{}]'.format(tot_latency-1), s_tlast_str='tlast_d[{}]'.format(tot_latency-1),
                      s_tready_str='', almost_full_str='almost_full', m_tvalid_str='m_axis_tvalid', m_tdata_str='m_axis_tdata',
                      m_tuser_str='m_axis_tuser', m_tlast_str='m_axis_tlast', m_tready_str='m_axis_tready')

        fh.write('\n')
        fh.write('endmodule\n')

    return module_name

def gen_mod_logic(path, mod_value=3):
    """
        Generates logic for aligned modulus operator.  Uses fixed modulus value (for now)
        Logic assums 8 bit input count sequence and generates fully pipelined modulus logic.
        AXI interface is used.

        ==========
        Parameters
        ==========

            mod_value : integer value that defined the modulus value.

    """
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)
    mod_name = 'modulus_{}'.format(mod_value)

    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)

    def gen_regs(prefix, num_regs):
        str_val = '{}_0'.format(prefix)
        for ii in range(1, num_regs):
            str_val += ', {}_{}'.format(prefix, ii)

        return str_val

    num_shifts = 8 - ret_num_bitsU(mod_value)
    num_subs = num_shifts + 1
    with open(file_name, "w") as fh:

        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : PJV\n')
        fh.write('// File        : {}\n'.format(module_name))
        fh.write('// Description : Pipelined modulus operator.\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('module mod_8w\n')
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [7:0] s_count,\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [7:0] m_count,\n')
        fh.write('    output roll_over,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        str_val = gen_regs('sub', num_subs)
        fh.write('reg [8:0] {};\n'.format(str_val))
        str_val = gen_regs('next_sub', num_subs)
        fh.write('reg [8:0] {};\n'.format(str_val))
        str_val = gen_regs('pass', num_subs)
        fh.write('reg [8:0] {};\n'.format(str_val))
        str_val = gen_regs('next_pass', num_subs)
        fh.write('reg [8:0] {};\n'.format(str_val))

        fh.write('\n')
        fh.write('wire take_data;\n')
        fh.write('wire send_data;\n')
        fh.write('\n')
        for ii in range(num_subs):
            fh.write('wire [7:0] mod_val_{} = 8\'d{} << {};\n'.format(ii, mod_value, num_shifts - ii))
        fh.write('reg [{}:0] occ_reg, next_occ_reg;\n'.format(num_subs))
        fh.write('reg [{}:0] roll_over_reg, next_roll_over_reg;\n'.format(num_subs - 1))
        fh.write('\n')
        fh.write('reg [7:0] output_value, next_output_value;\n')
        fh.write('\n')
        fh.write('assign take_data = s_axis_tvalid & s_axis_tready & !sync_reset;\n')
        fh.write('assign send_data = (m_axis_tready & occ_reg[{}]) | (~occ_reg[{}] && occ_reg != 0);\n'.format(num_shifts, num_shifts))  #analysis:ignore
        fh.write('assign m_axis_tvalid = occ_reg[{}];\n'.format(num_shifts))
        fh.write('assign roll_over = roll_over_reg[{}];\n'.format(num_subs - 1))
        fh.write('assign m_count = output_value;\n')
        fh.write('\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_occ_reg = occ_reg;\n')
        fh.write('    if (take_data == 1\'b1 ) begin\n')
        fh.write('        next_occ_reg[0] = take_data;\n')
        fh.write('        next_occ_reg[{}:1] = occ_reg[{}:0];\n'.format(num_shifts, num_shifts - 1))
        fh.write('    end else if (send_data == 1\'b1) begin\n')
        fh.write('        next_occ_reg[0] = 1\'b0;\n')
        fh.write('        next_occ_reg[{}:1] = occ_reg[{}:0];\n'.format(num_shifts, num_shifts - 1))
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        occ_reg <= 0;\n')
        fh.write('        output_value <= 0;\n')
        fh.write('        roll_over_reg <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        occ_reg <= next_occ_reg;\n')
        fh.write('        output_value <= next_output_value;\n')
        fh.write('        roll_over_reg <= next_roll_over_reg;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        for ii in range(num_subs):
            fh.write('    pass_{} <= next_pass_{};\n'.format(ii, ii))
        fh.write('\n')
        for ii in range(num_subs):
            fh.write('    sub_{} <= next_sub_{};\n'.format(ii, ii))
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('\n')
        fh.wrtie('    next_roll_over_reg = roll_over_reg;\n')
        for ii in range(num_subs):
            fh.write('    next_pass_{} = pass_{};\n'.format(ii, ii))
        fh.write('\n')
        for ii in range(num_subs):
            fh.write('    next_sub_{} = sub_{};\n'.format(ii, ii))
        fh.write('\n')
        fh.write('    next_output_value = output_value;\n')
        fh.write('\n')
        fh.write('    if (send_data) begin\n')
        fh.write('        next_pass_0 = {1\'b0, s_count};\n')
        for ii in range(1, num_subs):
            fh.write('        next_pass_{} = pass_{};\n'.format(ii, ii - 1))
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    if (send_data == 1\'b1) begin\n')
        fh.write('        next_sub_0 = s_count - mod_val_0;\n')
        for ii in range(1, num_subs):
            fh.write('        if (sub_{}[8] == 1\'b1) begin\n'.format(ii - 1))
            fh.write('            next_sub_{} = pass_{} - mod_val_{};\n'.format(ii, ii - 1, ii))
            fh.write('            next_roll_over_reg[{}] = 1\'b1;\n'.format(ii - 1))
            fh.write('        end else begin\n')
            fh.write('            next_sub_{} = sub_{} - mod_val_{};\n'.format(ii, ii - 1, ii))
            if ii == 1:
                fh.write('            next_roll_over_reg[{}] = 1\'b0;\n'.format(ii - 1))
            else:
                fh.write('            next_roll_over_reg[{}] = roll_over_reg[{}];\n'.format(ii - 1, ii - 2))
            fh.write('        end\n')
        fh.write('\n')
        fh.write('        if (sub_{}[8] == 1\'b1) begin\n'.format(num_shifts))
        fh.write('            next_output_value = pass_{};\n'.format(num_shifts))
        fh.write('            next_roll_over_reg[{}] = roll_over_reg[{}];\n'.format(num_subs - 1, num_subs - 2))
        fh.write('        end else begin\n')
        fh.write('            next_output_value = sub_{}[7:0];\n'.format(num_shifts))
        fh.write('            next_roll_over_reg[{}] = 1\'b1;\n'.format(num_subs - 1))
        fh.write('        end\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('endmodule\n')


def gen_complex_mult(path, input_width=16, b_width=25, output_width=16, tuser_width=0,
                     tlast=False, slice_msb=31, slice_lsb=16, almost_full_thresh=None):
    """
        Generates logic to align pipelined complex multiplier.

        ==========
        Parameters
        ==========

            input_width : data width for input I and Q
            output_width : data_width for output I and Q
            tot_latency : pads logic with additional pipelining for a total latency = tot_latency.  Note is tot_latency
                            is < minimum pipelining, then tot_latency = minimum pipelining.
    """
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)

    mod_name = 'complex_mult_iw{}_ow{}'.format(input_width, output_width)
    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)
    iword_msb = b_width * 2 - 1
    oword_msb = output_width * 2 - 1
    oword_width = oword_msb + 1
    input_msb = input_width * 2 - 1
#    output_msb = output_width - 1
    tuser_msb = tuser_width - 1
    fifo_addr_width = 4
    if almost_full_thresh is None:
        almost_full_thresh = 1 << (fifo_addr_width - 1)
#    tot_latency = 6
    with open(file_name, "w") as fh:
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author : PJV\n')
        fh.write('// File : %s\n' % module_name)
        fh.write('// Description : Implement AXI compliant Complex Multiplier. Uses 4 DSP48s.\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [{}:0] s_axis_tdata_0,\n'.format(input_msb))
        fh.write('    input [{}:0] s_axis_tdata_1,\n'.format(iword_msb))
        if tuser_width > 0:
            fh.write('    input [{}:0] s_axis_tuser,\n'.format(tuser_msb))
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    output [{}:0] m_axis_tdata,\n'.format(oword_msb))
        if tuser_width > 0:
            fh.write('    output [{}:0] m_axis_tuser,\n'.format(tuser_msb))
        if tlast:
            fh.write('    output m_axis_tlast,\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('wire [47:0] pcout_ar_br, pcout_ar_bi, i_term, q_term;\n')
        fh.write('\n')
        fh.write('wire [24:0] ar, ai;\n')
        fh.write('wire [17:0] br, bi;\n')
        fh.write('wire [{}:0] fifo_tdata;\n'.format(oword_msb))
        fh.write('reg [4:0] valid_d;\n')
        fh.write('wire almost_full;\n')
        if tuser_width > 0:
            fh.write('reg [4:0] tuser_d [{}:0];\n'.format(tuser_width - 1))
        fh.write('wire take_data;\n')
        fh.write('\n')
        pad = 18 - input_width
        if pad > 0:
            fh.write('assign bi = {{{{{}{{s_axis_tdata_0[{}]}}}}, s_axis_tdata_0[{}:0]}};\n'.format(pad, input_width-1, input_width-1))
            fh.write('assign br = {{{{{}{{s_axis_tdata_0[{}]}}}}, s_axis_tdata_0[{}:{}]}};\n'.format(pad, input_msb, input_msb, input_width))  #analysis:ignore
        else:
            fh.write('assign bi = s_axis_tdata_0[{}:0];\n'.format(input_width-1))
            fh.write('assign br = s_axis_tdata_0[{}:{}];\n'.format(input_msb, input_width))  #analysis:ignore
        pad = 25 - b_width
        if pad > 0:
            fh.write('assign ar = {{{}{{s_axis_tdata_1[{}]}}}}, s_axis_tdata_1[{}:{}]}};\n'.format(pad, iword_msb, iword_msb, b_width))  #analysis:ignore
            fh.write('assign ai = {{{{{}{{s_axis_tdata_1[{}]}}}}, s_axis_tdata_1[{}:0]}};\n'.format(pad, b_width - 1, b_width - 1))
        else:
            fh.write('assign ar = s_axis_tdata_1[{}:{}];\n'.format(iword_msb, b_width))  #analysis:ignore
            fh.write('assign ai = s_axis_tdata_1[{}:0];\n'.format(b_width - 1))

        fh.write('assign take_data = s_axis_tvalid & s_axis_tready and !sync_reset;\n')
        fh.write('assign s_axis_tready = ~almost_full;\n')
        slice_str = '{}:{}'.format(slice_msb, slice_lsb)
        fh.write('assign fifo_tdata = {{q_term[{}], i_term[{}]}};\n'.format(slice_str, slice_str))
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('	if (sync_reset == 1\'b1) begin\n')
        fh.write('        valid_d <= 0;\n')
        fh.write('	end else begin\n')
        fh.write('        valid_d <= {valid_d[3:0], take_data};\n')
        fh.write('	end\n')
        fh.write('end\n')
        fh.write('\n')
        if tlast:
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            fh.write('    tlast_d <= {tlast_d[3:0], s_axis_tlast};\n')
            fh.write('end\n')
            fh.write('\n')
        if tuser_width > 0:
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            fh.write('    tlast_d[0] <= s_axis_user;\n')
            fh.write('    tlast_d[1] <= tlast_d[0];\n')
            fh.write('    tlast_d[2] <= tlast_d[1];\n')
            fh.write('    tlast_d[3] <= tlast_d[2];\n')
            fh.write('    tlast_d[4] <= tlast_d[3];\n')
            fh.write('end\n')
            fh.write('\n')
        dsp_name = 'cm_mult_0'
        dsp_name = gen_dsp48E1(path, name=dsp_name, opcode='A*B', a_width=25, b_width=18, areg=2, breg=2, mreg=1, preg=1,
                               use_ce=False, use_pcout=True)[1]
        print(dsp_name)
        fh.write('{} ar_br (\n'.format(dsp_name))
        # fh.write('    // this is rounded. a and b delay = 2.\n')
        fh.write('  .clk(clk),\n')
        fh.write('  .a(ar),\n')
        fh.write('  .b(br),\n')
        fh.write('  .pcout(pcout_ar_br),\n')
        fh.write('  .p()\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('{} ar_bi (\n'.format(dsp_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .a(ar),\n')
        fh.write('  .b(bi),\n')
        fh.write('  .pcout(pcout_ar_bi),\n')
        fh.write('  .p()\n')
        fh.write(');\n')
        fh.write('\n')
        dsp_name = 'cm_pcin_minus'

        dsp_name = gen_dsp48E1(path, name=dsp_name, opcode='PCIN-A*B', a_width=25, b_width=18, areg=3, breg=3, mreg=1,
                               preg=1, use_ce=False, use_pcout=True)[1]
        print(dsp_name)
        fh.write('{} ai_bi (\n'.format(dsp_name))
        # fh.write('    // this is rounded. a and b delay = 3.\n')
        fh.write('  .clk(clk),\n')
        fh.write('  .a(ai),\n')
        fh.write('  .b(bi),\n')
        fh.write('  .pcin(pcout_ar_br),\n')
        fh.write('  .pcout(),\n')
        fh.write('  .p(i_term)\n')
        fh.write(');\n')
        fh.write('\n')
        dsp_name = 'cm_pcin_plus'
        dsp_name = gen_dsp48E1(path, name=dsp_name, opcode='PCIN+A*B', a_width=25, b_width=18, areg=3, breg=3, mreg=1,
                               preg=1, use_ce=False, use_pcout=True)[1]
        print(dsp_name)
        fh.write('{} ai_br (\n'.format(dsp_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .a(ai),\n')
        fh.write('  .b(br),\n')
        fh.write('  .pcin(pcout_ar_bi),\n')
        fh.write('  .pcout(),\n')
        fh.write('  .p(q_term)\n')
        fh.write(');\n')
        fh.write('\n\n')
        # put in axi fifo here.
        (_, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, almost_full=4, ram_style='distributed', tlast=tlast)
        print(fifo_name)

        axi_fifo_inst(fh, fifo_name, inst_name='axi_fifo', data_width=oword_width, af_thresh=almost_full_thresh,
                      addr_width=fifo_addr_width, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='valid_d[4]',
                      s_tdata_str='fifo_tdata', s_tuser_str='tuser_d[4]', s_tlast_str='tlast_d[4]',
                      s_tready_str='', almost_full_str='almost_full', m_tvalid_str='m_axis_tvalid', m_tdata_str='m_axis_tdata',
                      m_tuser_str='m_axis_tuser', m_tlast_str='m_axis_tlast', m_tready_str='m_axis_tready')

        fh.write('\n')
        #
        fh.write('endmodule\n')

    return (module_name, file_name)

def gen_aligned_cnt(path, cnt_width=16, tuser_width=0, tlast=False, incr=1, tot_latency=None, start_sig=False,
                    cycle=False, upper_cnt=False, prefix='', dwn_cnt=False, load=False, dport=True, startup=True,
                    almost_full_thresh=None, fifo_addr_width=None, use_af=False, gate=False):
    """
        Generates logic to align pipelined counter with a data stream.

        ==========
        Parameters
        ==========

            cnt_width : counter width.
            tot_latency : pads logic with additional pipelining for a total latency = tot_latency.  Note if tot_latency
                            is < minimum pipelining, then tot_latency = minimum pipelining.
            start_sig : start signal used to gate logic.  Logic will not drive the output until a start signal is
                        received.
            startup : Option ensure that data is not valid until valid data is read from the internal FIFO.
            upper_cnt : (optional) counts number of cycles through lower counter.
            cycle : indicates that the system should cycle through the last n values for each new value.  This
                    is useful for MAC base filtering.
    """

    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)

    if dport is False:
        tlast = False
        tuser_width = 0

    cnt_width = int(np.ceil(cnt_width / 8.)) * 8
    pdelay = adder_pipeline(cnt_width)

    id_val = 0
    if tlast:
        id_val += 1
    if start_sig:
        id_val += 2
    if upper_cnt:
        id_val += 4
    if dwn_cnt:
        id_val += 8
    if use_af is True:
        id_val += 16

    if load:
        id_val += 32

    if tuser_width > 0:
        id_val += 64

    if gate:
        id_val += 128
    if tot_latency:
        id_val += 256 + tot_latency

    assert(path is not None), 'User must specify Path'
    if cycle:
        mod_name = 'process_cycle_cw{}_{}'.format(cnt_width, id_val)
    else:
        mod_name = 'count_cycle_cw{}_{}'.format(cnt_width, id_val)

    if len(prefix) > 0:
        mod_name = prefix + '_' + mod_name

    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)

    # generate axi_fifo
    if use_af is False:
        fifo_depth = 2 ** int(np.ceil(np.log2(pdelay*2)))
        if fifo_depth < 8:
            fifo_depth = 8
        fifo_addr_width = int(np.log2(fifo_depth))
        almost_full_thresh = 2 ** fifo_addr_width - pdelay - 1
    else:
        assert(almost_full_thresh is not None), 'User must specify almost_full_thresh when using af'
        assert(fifo_addr_width is not None), 'User must specify fifo_addr_width when using af'

    (_, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, almost_full=almost_full_thresh, ram_style='distributed', tlast=tlast)
    if tot_latency is not None:
        pad = tot_latency - pdelay
        if pad < 0:
            pad = 0
            tot_latency = pdelay
    else:
        tot_latency = pdelay
        pad = 0

    if dwn_cnt:
        roll_over_str = 'cnt_nib0[7:0] == 0'
        for jj in range(1, pdelay):
            roll_over_str = roll_over_str + ' && next_cnt_nib{}[7:0] == 0'.format(jj)

        roll_over_strs = []
        for ii in range(1, pdelay):
            temp = 'cnt_nib0_d{}[7:0] == 0'.format(ii - 1)
            for jj in range(1, pdelay):
                if jj >= ii:
                    temp = temp + ' && cnt_nib{}[7:0] == 0'.format(jj)
                else:
                    temp = temp + ' && cnt_nib{}_d{} ==`` 0'.format(jj, ii - jj - 1)
            roll_over_strs.append(temp)

    else:
        roll_over_str = 'cnt_nib0[7:0] == mask0'
        for jj in range(1, pdelay):
            roll_over_str = roll_over_str + ' && next_cnt_nib{}[7:0] == mask{}'.format(jj, jj)

        roll_over_strs = []
        for ii in range(1, pdelay):
            temp = 'cnt_nib0_d{} == mask0'.format(ii - 1)
            for jj in range(1, pdelay):
                if jj >= ii:
                    temp = temp + ' && cnt_nib{}[7:0] == mask{}'.format(jj, jj)
                else:
                    temp = temp + ' && cnt_nib{}_d{} == mask{}'.format(jj, ii - jj - 1, jj)
            roll_over_strs.append(temp)

    cnt_msb = cnt_width - 1
    # tuser_msb = tuser_width - 1
    remain_val = 7 - (pdelay * 8 - cnt_width)
    pad_bits = (pdelay * 8 - cnt_width)
    int_cnt_msb = cnt_msb + pad_bits
    with open(file_name, "w") as fh:
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author : PJV\n')
        fh.write('// File : {}\n'.format(module_name))
        fh.write('// Description : Implement simple count / data alignment logic while optimizing pipelining.\n')
        fh.write('//                Useful for aligning data with addition of metadata\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        if dport:
            fh.write('module {} #( \n'.format(module_name))
            if tuser_width == 0:
                fh.write('    parameter DATA_WIDTH=32)\n')
            else:
                fh.write('    parameter DATA_WIDTH=32,\n')
                fh.write('    parameter TUSER_WIDTH=32)\n')
        else:
            fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        if dport:
            fh.write('    input [DATA_WIDTH-1:0] s_axis_tdata,\n')
        fh.write('    input [{}:0] cnt_limit,\n'.format(cnt_msb))
        if tuser_width > 0:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        fh.write('    output s_axis_tready,\n')
        if load:
            fh.write('    input [{}:0] load_value,\n'.format(cnt_msb))
            fh.write('    input load,\n')
        if incr > 1:
            fh.write('    input [7:0] incr,\n')
        if start_sig:
            fh.write('    input start_sig,\n'.format(cnt_msb))
        if upper_cnt:
            fh.write('    input [7:0] uroll_over,\n')

        if use_af:
            fh.write('    output af,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        if dport:
            fh.write('    output [DATA_WIDTH-1:0] m_axis_tdata,\n')
        fh.write('    output m_axis_final_cnt,\n')
        if tuser_width > 0:
            fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        fh.write('    output [{}:0] count,\n'.format(cnt_msb))
        if upper_cnt:
            fh.write('    output [7:0] upper_cnt,\n')
        if tlast:
            fh.write('    output m_axis_tlast,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        if dport:
            fh.write('localparam DATA_MSB = DATA_WIDTH - 1;\n')
        if tuser_width > 0:
            fh.write('localparam TUSER_MSB = TUSER_WIDTH - 1;\n')
        if load:
            fh.write('wire load_cnt;\n')
            for jj in range(pdelay - 1):
                fh.write('reg load_reg_d{};\n'.format(jj))
            fh.write('\n')
            fh.write('wire [{}:0] load_value0;\n'.format(int_cnt_msb))
            for jj in range(pdelay - 1):
                fh.write('reg [{}:0] loadv_d{};\n'.format(int_cnt_msb, jj))

        if dport:
            for jj in range(tot_latency):
                fh.write('reg [DATA_MSB:0] data_d{};\n'.format(jj))

        for jj in range(tot_latency):
            fh.write('reg [15:0] cnt_limit_d{};\n'.format(jj))

        if tuser_width > 0:
            fh.write('reg [TUSER_MSB:0] tuser_d[0:{}];\n'.format(tot_latency - 1))
        if tlast:
            fh.write('reg [{}:0] tlast_d;\n'.format(tot_latency - 1))

        if upper_cnt:
            for jj in range(tot_latency):
                fh.write('reg [7:0] upper_cnt_d{};\n'.format(jj))

        if gate:
            fh.write('reg active_frame, next_active_frame;\n')

        fh.write('\n')
        if startup:
            fh.write('reg startup, next_startup;\n')
        fh.write('wire almost_full;\n')
        fh.write('\n')

        fh.write('wire m_fifo_tvalid;\n')
        if dport:
            fh.write('wire [DATA_WIDTH + {}:0] m_fifo_tdata;\n'.format(cnt_width))
        else:
            fh.write('wire [{}:0] m_fifo_tdata;\n'.format(cnt_width))
        fh.write('wire m_fifo_tready;\n')

        if tuser_width > 0:
            fh.write('wire [TUSER_MSB:0] m_fifo_tuser;\n')

        if tlast:
            fh.write('wire m_fifo_tlast;\n')

        gen_cnt_sigs(fh, prefix='cnt', pdelay=pdelay)
        for nn in range(pad):
            fh.write('reg [{}:0] count_d{}, next_count_d{};\n'.format(cnt_msb, nn, nn))

        fh.write('wire [{}:0] count_s;\n'.format(cnt_msb))
        fh.write('reg reset_cnt, next_reset_cnt;\n')
        if cycle:
            fh.write('reg cycling, next_cycling;\n')
        for jj in range(pdelay - 2):
            fh.write('reg reset_cnt_d{};\n'.format(jj))
        fh.write('\n')
        for jj in range(pdelay):
            fh.write('wire [7:0] mask{};\n'.format(jj))
        fh.write('\n')
        fh.write('wire take_data, tready_s;\n')

        fh.write('wire final_cnt, cnt_reset;\n')
        fh.write('wire fifo_tready;\n')
        fh.write('wire [DATA_WIDTH + {}:0] fifo_tdata;\n'.format(cnt_width))
        for ii in range(pdelay - 1):
            fh.write('wire cnt_reset_{};\n'.format(ii))
        for jj in range(pdelay):
            fh.write('reg take_d{};\n'.format(jj))

        if start_sig:
            fh.write('wire new_cnt;\n')
            for jj in range(pdelay - 1):
                fh.write('reg new_cnt_d{};\n'.format(jj))
        fh.write('\n')
        if dport:
            fh.write('assign fifo_tdata = {{final_cnt, count_s, data_d{}}};\n'.format(pdelay - 1))
        else:
            fh.write('assign fifo_tdata = {{final_cnt, count_s}};\n')

        fh.write('assign m_axis_tvalid = m_fifo_tvalid;\n')
        if dport:
            fh.write('assign m_axis_tdata = m_fifo_tdata[DATA_MSB:0];\n')
        fh.write('assign m_fifo_tready = m_axis_tready;\n')
        if dport:
            fh.write('assign m_axis_final_cnt = m_fifo_tdata[DATA_WIDTH + {}];\n'.format(cnt_width))
        else:
            fh.write('assign m_axis_final_cnt = m_fifo_tdata[{}];\n'.format(cnt_width))

        if tlast:
            fh.write('assign m_axis_tlast = m_fifo_tlast;\n')
        if tuser_width > 0:
            fh.write('assign m_axis_tuser = m_fifo_tuser;\n')
        if use_af:
            if cycle:
                fh.write('assign tready_s = (fifo_tready & (~cycling | cnt_reset)) ? 1\'b1 : 1\'b0;\n'.format(pdelay - 1))  #analysis:ignore
            else:
                fh.write('assign tready_s = fifo_tready;\n')
            fh.write('assign af = almost_full;\n')
        else:
            if cycle:
                fh.write('assign tready_s = (~almost_full & (~cycling | cnt_reset)) ? 1\'b1 : 1\'b0;\n'.format(pdelay - 1))  #analysis:ignore
            else:
                fh.write('assign tready_s = ~almost_full;\n')

        if gate:
            fh.write('assign take_data = s_axis_tvalid & tready_s & !sync_reset & (active_frame | start_sig);\n')
        else:
            fh.write('assign take_data = s_axis_tvalid & tready_s & !sync_reset;\n')
        fh.write('assign s_axis_tready = tready_s;\n')
        cnt = startup + start_sig + load
        str_val = ''
        if cnt > 0:
            str_val = '& '
        if cnt > 1:
            str_val += '('
        if startup:
            str_val += 'startup'
            if cnt > 1:
                str_val += ' | '

        if start_sig:
            str_val += 'start_sig'

        if load:
            if cnt > 1:
                str_val += ' | '
            str_val += 'load'

        if cnt > 1:
            str_val += ')'

        if start_sig:
            fh.write('assign new_cnt = (take_data {});\n'.format(str_val)) # ? 1\'b1 : 1\'b0;\n'.format(str_val))
        if load:
            fh.write('assign load_cnt = (take_data {});\n'.format(str_val)) # ? 1\'b1 : 1\'b0;\n'.format(str_val))

        if upper_cnt:
            fh.write('assign upper_cnt = upper_cnt_d{};\n'.format(tot_latency - 1))
        str_val = ''

        if dwn_cnt:
            fh.write('assign final_cnt = (count_s == 0) ? 1\'b1 : 1\'b0;\n')
        else:
            fh.write('assign final_cnt = (count_s == cnt_limit_d{}) ? 1\'b1 : 1\'b0;\n'.format(pdelay - 1))
        for ii, str_val in enumerate(roll_over_strs):
            fh.write('assign cnt_reset_{} = ({}) ? 1\'b1 : 1\'b0;\n'.format(ii, str_val))

        fh.write('assign cnt_reset = ({}) ? 1\'b1 : 1\'b0;\n'.format(roll_over_str))
        fh.write('\n')
        str_val = ''
        for jj in reversed(range(pdelay - 1)):
            delay_val = pdelay - 2 - jj
            str_val = str_val + ', cnt_nib{}_d{}'.format(jj, delay_val)
        str_val = '{{cnt_nib{}[{}:0]'.format(pdelay - 1, remain_val) + str_val + '};\n'
        fh.write('assign count_s = {}'.format(str_val))
        if dport:
            fh.write('assign count = m_fifo_tdata[DATA_WIDTH + {}:DATA_WIDTH];\n'.format(cnt_msb))
        else:
            fh.write('assign count = m_fifo_tdata[{}:0];\n'.format(cnt_msb))
        fh.write('\n')
        reset_list = []
        for jj in range(pdelay):
            lidx = jj * 8 + 7
            ridx = lidx - 7
            if jj == pdelay - 1 and remain_val != 7:
                fh.write('assign mask{} = {{{}\'d0, cnt_limit[{}:{}]}};\n'.format(jj, 7 - remain_val, cnt_msb, ridx))
            else:
                fh.write('assign mask{} = cnt_limit[{}:{}];\n'.format(jj, lidx, ridx))
            reset_list.append('{{1\'b0, mask{}}}'.format(jj))

        if load:
            if remain_val != 7:
                fh.write('assign load_value0 = {{{}\'d0, load_value}};\n'.format(pad_bits))
            else:
                fh.write('assign load_value0 = load_value;\n')
        fh.write('\n')
        sp = '        '
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset) begin\n')
        fh.write('        reset_cnt <= 1\'b0;\n')
        if cycle:
            fh.write('        cycling <= 1\'b0;\n')
        if dwn_cnt:
            gen_cnt_rst(fh, prefix='cnt', pdelay=pdelay, sp=sp, reset_list=reset_list)
        else:
            gen_cnt_rst(fh, prefix='cnt', pdelay=pdelay, sp=sp)
        if gate:
            fh.write('        active_frame <= 1\'b0;\n')
        for jj in range(pad):
            fh.write('        count_d{} <= 0;\n'.format(jj))
        if upper_cnt:
            logic_rst(fh, prefix='upper_cnt_d', cnt=tot_latency, sp='        ')
        if startup:
            fh.write('        startup <= 1\'b1;\n')
        fh.write('    end else begin\n')
        fh.write('        reset_cnt <= next_reset_cnt;\n')
        if cycle:
            fh.write('        cycling <= next_cycling;\n')
        gen_cnt_regs(fh, 'cnt', pdelay)
        if gate:
            fh.write('        active_frame <= next_active_frame;\n')
        if upper_cnt:
            logic_gate(fh, prefix='upper_cnt_d', str_val='next_upper_cnt', cnt=tot_latency, sp='        ')
        if startup:
            fh.write('        startup <= next_startup;\n')
        for jj in range(pad):
            fh.write('        count_d{} <= next_count_d{};\n'.format(jj, jj))
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        if pdelay > 0:
            fh.write('// delay process\n')
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            gen_cnt_delay(fh, 'cnt', pdelay, tab='')
            fh.write('    cnt_limit_d0 <= cnt_limit;\n')
            for jj in range(pdelay - 1):
                fh.write('    cnt_limit_d{} <= cnt_limit_d{};\n'.format(jj+1, jj))
            if start_sig:
                for jj in range(pdelay - 1):
                    if jj == 0:
                        fh.write('    new_cnt_d0 <= new_cnt;\n')
                    else:
                        fh.write('    new_cnt_d{} <= new_cnt_d{};\n'.format(jj, jj - 1))
                fh.write('\n')
            if dport:
                fh.write('    data_d0 <= s_axis_tdata;\n')
                for jj in range(1, tot_latency):
                    fh.write('    data_d{} <= data_d{};\n'.format(jj, jj-1))

            if tuser_width > 0:
                fh.write('    tuser_d[0] <= s_axis_tuser;\n')
                for jj in range(1, tot_latency):
                    fh.write('    tuser_d[{}] <= tuser_d[{}];\n'.format(jj, jj - 1))

            if tlast:
                fh.write('    tlast_d[0] <= s_axis_tlast;\n')
                for jj in range(1, tot_latency):
                    fh.write('    tlast_d[{}] <= tlast_d[{}];\n'.format(jj, jj - 1))

            if pdelay > 2:
                fh.write('    reset_cnt_d0 <= reset_cnt;\n')
                for jj in range(1, pdelay - 2):
                    fh.write('    reset_cnt_d{} <= reset_cnt_d{};\n'.format(jj, jj - 1))

                fh.write('\n')
                if load:
                    fh.write('    load_reg_d0 <= load_cnt;\n')
                    for jj in range(1, pdelay - 1):
                        fh.write('    load_reg_d{} <= load_reg_d{};\n'.format(jj, jj - 1))
                    fh.write('\n')
                    fh.write('    loadv_d0 <= load_value0;\n')
                    for jj in range(1, pdelay - 1):
                        fh.write('    loadv_d{} <= loadv_d{};\n'.format(jj, jj - 1))
                fh.write('\n')


            for jj in range(pdelay):
                if jj == 0:
                    if cycle:
                        fh.write('    take_d0 <= take_data | cycling;\n')
                    else:
                        fh.write('    take_d0 <= take_data;\n')
                else:
                    fh.write('    take_d{} <= take_d{};\n'.format(jj, jj - 1))
            fh.write('end\n')

        if gate:
            fh.write('\n')
            fh.write('always @*\n')
            fh.write('begin\n')
            fh.write('    next_active_frame = active_frame;\n')
            fh.write('    if (take_data) begin\n')
            fh.write('        if (start_sig) begin\n')
            fh.write('            next_active_frame = 1\'b1;\n')
            fh.write('        end else if (final_cnt) begin\n')
            fh.write('            next_active_frame = 1\'b0;\n')
            fh.write('        end\n')
            fh.write('    end\n')
            fh.write('end\n')
        fh.write('\n')
        fh.write('// input and count process;\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        gen_cnt_fback(fh, 'cnt', pdelay)
        fh.write('    next_reset_cnt = reset_cnt;\n')
        if startup:
            fh.write('    next_startup = startup;\n')
        if cycle:
            fh.write('    next_cycling = cycling;\n')

        if cycle:
            fh.write('    if (take_data | cycling) begin\n')
        else:
            fh.write('    if (take_data) begin\n')

        str_val = ''
        if startup:
            str_val = ' | startup'
        if start_sig:
            str_val = ' | new_cnt'
        if load:
            str_val = ' | load_cnt'
        if cycle:
            fh.write('        next_cycling = (~cnt_reset | take_data);\n')
        fh.write('        next_reset_cnt = cnt_reset;\n')
        fh.write('        if (cnt_reset{}) begin\n'.format(str_val))
        if load:

            fh.write('            if (load) begin\n')
            fh.write('                next_cnt_nib0 = {1\'b0, load_value0[7:0]};\n')
            fh.write('            end else begin\n')
            if dwn_cnt:
                fh.write('                next_cnt_nib0 = {1\'b0, mask0};\n')
            else:
                fh.write('                next_cnt_nib0 = 0;\n')
            fh.write('            end\n')

        else:
            if dwn_cnt:
                fh.write('            next_cnt_nib0 = {1\'b0, mask0};\n')
            else:
                fh.write('            next_cnt_nib0 = 0;\n')
        fh.write('        end else begin\n')
        ar_str = '-' if dwn_cnt else '+'
        if incr == 1:
            fh.write('            next_cnt_nib0 = cnt_nib0[7:0] {} 1;\n'.format(ar_str))
        else:
            fh.write('            next_cnt_nib0 = cnt_nib0[7:0] {} incr;\n'.format(ar_str))
        fh.write('        end\n')
        if startup:
            fh.write('        next_startup = 1\'b0;\n')
        fh.write('    end\n')
        fh.write('\n')

        for jj in range(1, pdelay):
            str_val = ''
            if start_sig:
                str_val = str_val + ' | new_cnt_d{}'.format(jj - 1)
            if load:
                str_val += ' | load_reg_d{}'.format(jj - 1)
            if jj == 1:
                fh.write('    if (reset_cnt{} | cnt_reset_{}) begin\n'.format(str_val, jj - 1))
            else:
                fh.write('    if (reset_cnt_d{}{} | cnt_reset_{}) begin\n'.format(jj - 2, str_val, jj - 1))
            if load:
                lidx = jj * 8 + 7
                ridx = jj * 8
                fh.write('        if (load_reg_d{}) begin\n'.format(jj - 1))
                fh.write('            next_cnt_nib{} = {{1\'b0, loadv_d{}[{}:{}]}};\n'.format(jj, jj - 1, lidx, ridx))
                fh.write('        end else begin\n')
                if dwn_cnt:
                    fh.write('            next_cnt_nib{} = {{1\'b0, mask{}}};\n'.format(jj, jj))
                else:
                    fh.write('            next_cnt_nib{} = 0;\n'.format(jj))
                fh.write('        end\n')
            else:
                if dwn_cnt:
                    fh.write('        next_cnt_nib{} = {{1\'b0, mask{}}};\n'.format(jj, jj))
                else:
                    fh.write('        next_cnt_nib{} = 0;\n'.format(jj))
            fh.write('    end else if (take_d{}) begin\n'.format(jj - 1))
            ar_str = '-' if dwn_cnt else '+'
            fh.write('        next_cnt_nib{} = cnt_nib{}[7:0] {} cnt_nib{}[8];\n'.format(jj, jj, ar_str, jj - 1))
            fh.write('    end\n\n')
        fh.write('end\n')
        if upper_cnt:
            fh.write('// upper_cnt process;\n')
            fh.write('always @*\n')
            fh.write('begin\n')
            fh.write('    next_upper_cnt = upper_cnt_d0;\n')
            if start_sig:
                fh.write('    if (take_d{} | new_cnt) begin\n'.format(pdelay - 1))  # analysis:ignore
            elif cycle:
                fh.write('    if (take_d{}| cycling) begin\n'.format(pdelay - 1))
            else:
                fh.write('    if (take_d{}) begin\n'.format(pdelay - 1))
            str_val = ''
            if start_sig:
                str_val = ' | new_cnt'
            fh.write('            next_upper_cnt = 0;\n')
            fh.write('        if (final_cnt {}) begin\n'.format(str_val))
            if (start_sig):
                fh.write('            if ((upper_cnt == uroll_over) | new_cnt) begin\n')
            else:
                fh.write('            if (upper_cnt == uroll_over) begin\n')
            fh.write('                next_upper_cnt = 0;\n')
            fh.write('            end else begin\n')
            fh.write('                next_upper_cnt = upper_cnt + 1;\n')
            fh.write('            end\n')
            fh.write('        end\n')
            fh.write('    end\n')
            fh.write('end\n')
        fh.write('\n')
        if pad:
            fh.write('// output process\n')
            fh.write('always @*\n')
            fh.write('begin\n')
        if pad > 0:
            fh.write('    next_count_d0 = count_s;\n')
        for jj in range(1, pad):
            fh.write('    next_count_d{} = count_d{};\n'.format(jj, jj - 1))
        str_val = ''
        if pad:
            fh.write('end\n')
        fh.write('\n')
        if dport:
            data_width = 'DATA_WIDTH + {}'.format(cnt_width+1)
        else:
            data_width = '{}'.format(cnt_width+1)
        axi_fifo_inst(fh, fifo_name, inst_name='u_fifo', data_width=data_width, af_thresh=almost_full_thresh,
                      addr_width=fifo_addr_width, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='take_d{}'.format(pdelay-1),
                      s_tdata_str='fifo_tdata', s_tuser_str='tuser_d[{}]'.format(pdelay-1), s_tlast_str='tlast_d[{}]'.format(pdelay-1),
                      s_tready_str='fifo_tready', almost_full_str='almost_full', m_tvalid_str='m_fifo_tvalid', m_tdata_str='m_fifo_tdata',
                      m_tuser_str='m_fifo_tuser', m_tlast_str='m_fifo_tlast', m_tready_str='m_fifo_tready')

        fh.write('\n')
        fh.write('endmodule\n')

    return module_name, fifo_name

def gen_var_delay(path, cnt_width=16, tuser_width=0, tlast=False, prefix='', mem_depth=(1 << 12)):
    """
        Generates logic to align pipelined counter with a data stream.

        ==========
        Parameters
        ==========

            cnt_width : counter width.
    """

    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)

    cnt_width = int(np.ceil(cnt_width / 8.)) * 8
    pdelay = adder_pipeline(cnt_width)
    
    max_cnt = mem_depth - 1
    mem_addr_bits = ret_num_bitsU(max_cnt)

    # generate offset adder
    sub_str, adder_latency = gen_adder(path, cnt_width, cnt_width, subtract=True)
    # generate block ram.
    ram_str = gen_ram(path, ram_type='dp', memory_type='read_first', ram_style='block')
    print(sub_str, ram_str)
    id_val = 0
    if tlast:
        id_val += 1
    if tuser_width > 0:
        id_val += 2

    assert(path is not None), 'User must specify Path'

    mod_name = 'var_delay_cw{}_{}'.format(cnt_width, id_val)

    if len(prefix) > 0:
        mod_name = prefix + '_' + mod_name

    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)

    tot_latency = adder_latency + 3 # 3 for the RAM block
    ram_bits = tuser_width + int(tlast)

    fifo_depth = 2 ** int(np.ceil(np.log2(tot_latency * 2)))
    ram_style = 'distributed'
    if fifo_depth < 8:
        fifo_depth = 8
    fifo_addr_width = int(np.log2(fifo_depth))
    almost_full_thresh = (2 ** fifo_addr_width) - tot_latency - 1
    # generate axi_fifo
    _, fifo_name = gen_axi_fifo(path, tuser_width=tuser_width, almost_full=almost_full_thresh, ram_style=ram_style, tlast=tlast)

    # gen count cycle in for input count alignment
    ccycle_name, _ = gen_aligned_cnt(path, cnt_width=16, tuser_width=tuser_width, tlast=tlast, startup=True)
    cnt_msb = cnt_width - 1
    with open(file_name, "w") as fh:
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author : PJV\n')
        fh.write('// File : {}\n'.format(module_name))
        fh.write('// Description : Implement simple count / data alignment logic while optimizing pipelining.\n')
        fh.write('//                Useful for aligning data with addition of metadata\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('module {} #( \n'.format(module_name))
        if tuser_width == 0:
            fh.write('    parameter DATA_WIDTH=32)\n')
        else:
            fh.write('    parameter DATA_WIDTH=32,\n')
            fh.write('    parameter TUSER_WIDTH=32)\n')
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [DATA_WIDTH-1:0] s_axis_tdata,\n')
        fh.write('    input [{}:0] offset,\n'.format(cnt_msb))
        if tuser_width > 0:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        fh.write('    output s_axis_tready,\n')

        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [DATA_WIDTH-1:0] m_axis_tdata,\n')
        if tuser_width > 0:
            fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        fh.write('    output [{}:0] count,\n'.format(cnt_msb))
        if tlast:
            fh.write('    output m_axis_tlast,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('localparam DATA_MSB = DATA_WIDTH - 1;\n')
        if tuser_width > 0:
            fh.write('localparam TUSER_MSB = TUSER_WIDTH - 1;\n')

        fh.write('\n')
        fh.write('reg [DATA_MSB:0] data_d[0:{}];\n'.format(adder_latency - 1))

        if tuser_width > 0:
            fh.write('reg [TUSER_MSB:0] tuser_d[0:{}];\n'.format(adder_latency - 1))
        if tlast:
            fh.write('reg [{}:0] tlast_d;\n'.format(adder_latency - 1))

        fh.write('\n')
        fh.write('wire almost_full;\n')
        fh.write('\n')

        fh.write('wire [{}:0] count;\n'.format(cnt_width-1))
        fh.write('wire count_tready;\n')
        fh.write('wire [DATA_WIDTH-1:0] count_tdata;\n')
        if tuser_width:
            fh.write('wire [TUSER_WIDTH-1:0] count_tuser;\n')

        if tlast:
            fh.write('wire count_tlast;\n')

        fh.write('reg [{}:0] count_d[0:{}];\n'.format(cnt_msb, adder_latency - 1))
        fh.write('wire [{}:0] offset_count_s;\n'.format(cnt_msb + 1))
        fh.write('wire [{}:0] rd_addr, wr_addr;\n'.format(mem_addr_bits - 1))
        fh.write('\n')
        if ram_bits > 1:
            fh.write('wire [(DATA_WIDTH + {}):0] wr_tdata, rd_tdata;\n'.format(ram_bits - 1))
        elif ram_bits == 1:
            fh.write('wire [DATA_WIDTH:0] wr_tdata;\n')
        else:
            fh.write('wire [(DATA_WIDTH - 1):0] wr_tdata;\n')
        fh.write('reg take_d[{}:0];\n'.format(tot_latency - 1))
        fh.write('\n')
        idx = adder_latency - 1
        tlast_idx = 'DATA_WIDTH'
        if tlast and tuser_width:
            tlast_idx = 'DATA_WIDTH + {}'.format(tuser_width)
            fh.write('assign wr_tdata = {{tlast_d[{}], tuser_d[{}], data_d[{}]}};\n'.format(idx, idx, idx))
        elif tlast:
            fh.write('assign wr_tdata = {{tlast_d[{}], data_d[{}]}};\n'.format(idx, idx))
        elif tuser_width:
            fh.write('assign wr_tdata = {{tuser_d[{}], data_d[{}]}};\n'.format(idx, idx))
        else:
            fh.write('assign wr_tdata = {{data_d[{}]}};\n'.format(idx))

        fh.write('assign count_tready = ~almost_full;\n')
        fh.write('assign rd_addr = offset_count_s[{}:0];\n'.format(mem_addr_bits - 1))
        fh.write('assign wr_addr = count_d[{}][{}:0];\n'.format(adder_latency - 1, mem_addr_bits - 1))
        fh.write('\n')
        fh.write('\n')
        if pdelay > 0:
            fh.write('// delay process\n')
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            fh.write('    count_d[0] <= count;\n')
            for jj in range(1, adder_latency):
                fh.write('    count_d[{}] <= count_d[{}];\n'.format(jj, jj - 1))

            fh.write('    data_d[0] <= count_tdata;\n')
            for jj in range(1, adder_latency):
                fh.write('    data_d[{}] <= data_d[{}];\n'.format(jj, jj-1))

            if tuser_width > 0:
                fh.write('    tuser_d[0] <= count_tuser;\n')
                for jj in range(1, adder_latency):
                    fh.write('    tuser_d[{}] <= tuser_d[{}];\n'.format(jj, jj - 1))

            if tlast:
                fh.write('    tlast_d[0] <= count_tlast;\n')
                for jj in range(1, adder_latency):
                    fh.write('    tlast_d[{}] <= tlast_d[{}];\n'.format(jj, jj - 1))

            fh.write('    take_d <= {{take_d[{}:0], count_tvalid & count_tready}};\n'.format(tot_latency - 2))
            fh.write('end\n')
            fh.write('\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('{} #(\n'.format(ccycle_name))
        if tuser_width:
            fh.write('    .DATA_WIDTH(DATA_WIDTH),\n')
            fh.write('    .TUSER_WIDTH(TUSER_WIDTH))\n')
        else:
            fh.write('    .DATA_WIDTH(DATA_WIDTH))\n')
        fh.write('u_count_align\n')
        fh.write('(\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(sync_reset),\n')
        fh.write('    .s_axis_tvalid(s_axis_tvalid),\n')
        fh.write('    .s_axis_tdata(s_axis_tdata),\n')
        if tlast:
            fh.write('    .s_axis_tlast(s_axis_tlast),\n')
        if tuser_width:
            fh.write('    .s_axis_tuser(s_axis_tuser),\n')
        fh.write('    .s_axis_tready(s_axis_tready),\n')
        fh.write('\n')
        fh.write('    .cnt_limit({}\'d{}),\n'.format(cnt_width, max_cnt))
        fh.write('    .m_axis_tvalid(count_tvalid),\n')
        fh.write('    .m_axis_tdata(count_tdata),\n')
        if tuser_width:
            fh.write('    .m_axis_tuser(count_tuser),\n')
        if tlast:
            fh.write('    .m_axis_tlast(count_tlast),\n')
        fh.write('    .m_axis_final_cnt(),')
        fh.write('    .count(count),\n')
        fh.write('    .m_axis_tready(count_tready)\n')
        fh.write(');\n\n')
        fh.write('\n')
        fh.write('{} u_offset\n'.format(sub_str))
        fh.write('(\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .valid_i(1\'b1),\n')
        fh.write('    .a(count),\n'.format(cnt_msb))
        fh.write('    .b(offset),\n')
        fh.write('    .valid_o(),\n')
        fh.write('    .c(offset_count_s)\n')
        fh.write(');\n\n')

        fh.write('{} #(\n'.format(ram_str))
        fh.write('    .DATA_WIDTH(DATA_WIDTH + {}),\n'.format(ram_bits))
        fh.write('    .ADDR_WIDTH({}))\n'.format(mem_addr_bits))
        fh.write('u_ram\n')
        fh.write('(\n')
        fh.write('  .clk(clk),\n')
        fh.write('\n')
        fh.write('  .wea(take_d[{}]),\n'.format(adder_latency - 1))
        fh.write('  .addra(wr_addr),\n')
        fh.write('  .addrb(rd_addr),\n')
        fh.write('  .dia(wr_tdata),\n')
        fh.write('  .dob(rd_tdata)\n')
        fh.write(');\n')
        fh.write('\n\n')
        axi_fifo_inst(fh, fifo_name, inst_name='u_fifo', data_width='DATA_WIDTH', af_thresh=almost_full_thresh,
                      addr_width=fifo_addr_width, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='take_d[{}]'.format(tot_latency-1),
                      s_tdata_str='rd_tdata[{}:0]'.format('DATA_MSB'), s_tuser_str='rd_tdata[{}:{}]'.format('TUSER_MSB+DATA_WIDTH', 'DATA_WIDTH'), s_tlast_str='rd_tdata[{}]'.format(tlast_idx),
                      s_tready_str='', almost_full_str='almost_full', m_tvalid_str='m_axis_tvalid', m_tdata_str='m_axis_tdata',
                      m_tuser_str='m_axis_tuser', m_tlast_str='m_axis_tlast', m_tready_str='m_axis_tready')
        fh.write('\n')
        fh.write('endmodule\n')

    return module_name, fifo_name, ram_str


def gen_axi_accum(path, a_width=16, cnt_width=16, tuser_width=0, tlast=False, signeda=True, start_sig=False):
    """
        Generates logic to align pipelined counter with a data stream.

        ==========
        Parameters
        ==========

            word_width : data width for both input and output busses.
            cnt_width : counter width.
            tot_latency : pads logic with additional pipelining for a total latency = tot_latency.  Note is tot_latency
                            is < minimum pipelining, then tot_latency = minimum pipelining.
            start_sig : start signal used to gate logic.  Logic will not drive the output until a start signal is
                        received.
    """
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)
    max_width = int(np.ceil(np.log2(2**a_width * 2**cnt_width)))
    mod_name = 'axi_accum_iw{}_cw{}'.format(a_width, cnt_width)

    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)
    pdelay = adder_pipeline(max_width)
    pdelay_data = adder_pipeline(a_width)
    pdelay_cnt = adder_pipeline(cnt_width)
    tot_latency = pdelay
    tuser_msb = tuser_width - 1

    pad_cnt = pdelay - pdelay_cnt

    roll_over_str = 'cnt_nib0[7:0] == mask0'
    for jj in range(1, pdelay_cnt):
        roll_over_str = roll_over_str + ' && cnt_nib{}[7:0] == mask{}'.format(jj, jj)

    word_msb = a_width - 1
    cnt_msb = cnt_width - 1
    max_msb = max_width - 1
    ar_str = '+'
    subtract = False
    apad = 8 * pdelay - a_width

    fifo_width = max_width + cnt_width
    # generate axi_fifo
    fifo_depth = 2 ** int(np.ceil(np.log2(tot_latency*2)))
    fifo_addr_width = ret_addr_width(fifo_depth)
    (_, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, almost_full=pdelay, ram_style='distributed', tlast=tlast)

    with open(file_name, "w") as fh:

        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : PJV\n')
        fh.write('// File        : {}\n'.format(module_name))
        fh.write('// Description : Implement simple count / data alignment logic while optimizing pipelining.\n')
        fh.write('//                Useful for aligning data with addition of metadata\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [{}:0] a,\n'.format(word_msb))
        if tuser_width > 0:
            fh.write('    input [{}:0] s_axis_user,\n'.format(tuser_width - 1))
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        fh.write('')
        fh.write('    input [{}:0] cnt_limit,\n'.format(cnt_msb))
        if start_sig:
            fh.write('    input start_sig,\n'.format(cnt_msb))
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        if tuser_width > 0:
            fh.write('    output [{}:0] m_axis_tuser,\n'.format(tuser_width - 1))
        if tlast:
            fh.write('    output m_axis_tlast,\n')
        fh.write('    output [{}:0] m_axis_tdata,\n'.format(word_msb))
        fh.write('    output [{}:0] accum_out,\n'.format(max_msb))
        fh.write('    output [{}:0] count,\n'.format(cnt_msb))
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')

        fh.write('\n')
        if tuser_width > 0:
            for jj in range(tot_latency):
                fh.write('reg [{}:0] data_d{}, next_data_d{};\n'.format(word_msb, jj, jj))
        fh.write('\n')
        if start_sig:
            fh.write('reg gate_latch, next_gate_latch;\n')

        fh.write('reg startup, next_startup;\n')
        fh.write('\n')
        for jj in range(pdelay):
            idx = 8 if (jj == 0) else 9
            fh.write('reg [{}:0] accum_nib{}, next_accum_nib{};\n'.format(idx, jj, jj))

        for jj in range(pdelay):
            for nn in range(pdelay - jj - 1):
                fh.write('reg [8:0] accum_nib{}_d{}, next_accum_nib{}_d{};\n'.format(jj, nn, jj, nn))

        fh.write('wire m_fifo_tvalid;\n')
        fh.write('wire [{}:0] m_fifo_tdata;\n'.format(fifo_width - 1))
        fh.write('wire m_fifo_tready;\n')

        if tuser_width > 0:
            fh.write('reg [{}:0] tuser_d[0:{}];\n'.format(tuser_msb, tot_latency - 1))
            fh.write('reg [{}:0] next_tuser_d[0:{}];\n'.format(tuser_msb, tot_latency - 1))
            fh.write('wire [{}:0] m_fifo_tuser;\n'.format(tuser_width - 1))

        if tlast:
            fh.write('reg [{}:0] tlast_d;\n'.format(tot_latency - 1))
            fh.write('reg [{}:0] next_tlast_d;\n'.format(tot_latency - 1))
            fh.write('wire m_fifo_tlast;\n')

        gen_cnt_sigs(fh, prefix='cnt', pdelay=pdelay_cnt)
        for nn in range(pad_cnt):
            fh.write('reg [{}:0] count_d{}, next_count_d{};\n'.format(cnt_msb, nn, nn))

        if pdelay_data > 1:
            for ii in range(1, pdelay_data):
                fh.write('reg [{}:0] adelay_{}, next_adelay_{};\n'.format(a_width, ii - 1, ii - 1))

        fh.write('wire [{}:0] count_s;\n'.format(cnt_msb))
        fh.write('wire [{}:0] accum_s;\n'.format(max_msb))
        fh.write('reg reset_cnt, next_reset_cnt;\n')
        for jj in range(pdelay - 1):
            fh.write('reg reset_cnt_d{};\n'.format(jj))
        fh.write('\n')
        for jj in range(pdelay):
            fh.write('wire [7:0] mask{};\n'.format(jj))
        fh.write('\n')
        fh.write('wire take_data;\n')
        fh.write('wire new_cnt;\n')
        # if start_sig is True:
        fh.write('wire final_cnt;\n')
        fh.write('reg final_cnt_latch, next_final_cnt_latch;\n')
        for jj in range(pdelay - 1):
            fh.write('reg take_d{};\n'.format(jj))

        for jj in range(pdelay - 1):
            fh.write('reg new_cnt_d{};\n'.format(jj))
        fh.write('\n')
        fh.write('assign m_axis_tvalid = occ_reg[{}];\n'.format(tot_latency - 1))
        fh.write('assign m_axis_tdata = data_d{};\n'.format(tot_latency - 1))
        remain_val = 7 - (pdelay * 8 - max_width)
        fh.write('assign m_axis_tvalid = m_fifo_tvalid;\n')
        fh.write('assign accum_out = m_fifo_tdata[{}:0];\n'.format(max_width - 1))
        fh.write('assign count = m_fifo_tdata[{}:{}];\n'.format(fifo_width - 1, max_width))
        fh.write('assign m_fifo_tready = m_axis_tready;\n')
        if tlast:
            fh.write('assign m_axis_tlast = m_fifo_tlast;\n')
        if tuser_width > 0:
            fh.write('assign m_axis_tuser = m_fifo_tuser;\n')
        fh.write('assign s_axis_tready = ~almost_full;\n')
        fh.write('assign take_data = s_axis_tvalid & s_axis_tready & !sync_reset;\n')
        if start_sig:
            fh.write('assign new_cnt = (take_data == 1\'b1 && start_sig == 1\'b1) ? 1\'b1 : 1\'b0;\n')
        str_val = ''
        fh.write('assign final_cnt = ({}) ? 1\'b1 : 1\'b0;\n'.format(roll_over_str))
        fh.write('\n')
        str_val = gen_cnt_vec('accum', pdelay, max_width)
        fh.write('assign accum_s = {}'.format(str_val))
        str_val = gen_cnt_vec('cnt', pdelay_cnt, cnt_width)
        fh.write('assign count_s = {}'.format(str_val))
        for jj in range(pdelay_cnt):
            lidx = jj * 8 + 7
            ridx = lidx - 7
            if jj == pdelay - 1 and remain_val != 7:
                fh.write('assign mask{} = {{{}\'d0, cnt_limit[{}:{}]}};\n'.format(jj, 7 - remain_val, cnt_msb, ridx))
            else:
                fh.write('assign mask{} = cnt_limit[{}:{}];\n'.format(jj, lidx, ridx))

        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('	if (sync_reset == 1\'b1) begin\n')
        fh.write('        reset_cnt <= 1\'b0;\n')
        fh
        for jj in range(pdelay):
            fh.write('        accum_nib{} <= 0;\n'.format(jj))

        gen_cnt_rst(fh, 'cnt', pdelay_cnt)
        if tuser_width:
            logic_rst(fh, prefix='tuser_d', cnt=tot_latency, sp='        ')
        if tlast:
            fh.write('        tlast_d <= 0;\n')
        for jj in range(pad_cnt):
            fh.write('        count_d{} <= 0;\n'.format(jj))
        if start_sig:
            fh.write('        gate_latch <= 1\'b0;\n')
        fh.write('        final_cnt_latch <= 1\'b0;\n')
        fh.write('        startup <= 1\'b1;\n')
        fh.write('	end else begin\n')
        fh.write('        reset_cnt <= next_reset_cnt;\n')
        for jj in range(pdelay):
            fh.write('        accum_nib{} <= next_accum_nib{};\n'.format(jj, jj))
        gen_cnt_regs(fh, 'cnt', pdelay_cnt)
        if tuser_width > 0:
            for jj in range(tot_latency):
                fh.write('        tuser_d[{}] <= next_tuser_d[{}];\n'.format(jj, jj))
        if tlast:
            for jj in range(tot_latency):
                fh.write('        tlast_d[{}] <= next_tlast_d[{}];\n'.format(jj, jj))
        if start_sig:
            fh.write('        gate_latch <= next_gate_latch;\n')
        fh.write('        startup <= next_startup;\n')
        for jj in range(pad_cnt):
            fh.write('        count_d{} <= next_count_d{};\n'.format(jj, jj))
        fh.write('        final_cnt_latch <= next_final_cnt_latch;\n')
        fh.write('	end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('// delay process\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        for ii in range(pdelay_data - 1):
            fh.write('    adelay_{} = next_adelay_{};\n'.format(ii, ii))
        for jj in range(pdelay):
            for nn in range(pdelay - jj - 1):
                if nn == 0:
                    fh.write('    accum_nib{}_d{} <= accum_nib{};\n'.format(jj, nn, jj))
                else:
                    fh.write('    accum_nib{}_d{} <= accum_nib{}_d{};\n'.format(jj, nn, jj, nn - 1))

        gen_cnt_delay(fh, 'cnt', pdelay_cnt)
        if start_sig:
            for jj in range(pdelay - 1):
                if jj == 0:
                    fh.write('    new_cnt_d0 <= new_cnt;\n')
                else:
                    fh.write('    new_cnt_d{} <= new_cnt_d{};\n'.format(jj, jj - 1))
            for jj in range(pdelay - 1):
                if jj == 0:
                    fh.write('    gate_latch_d0 <= gate_latch;\n')
                else:
                    fh.write('    gate_latch_d{} <= gate_latch_d{};\n'.format(jj, jj - 1))
        fh.write('\n')

        if pdelay > 2:
            fh.write('    reset_cnt_d0 <= reset_cnt;\n')
            for jj in range(1, pdelay - 2):
                fh.write('    reset_cnt_d{} <= reset_cnt_d{};\n'.format(jj, jj - 1))

        for jj in range(pdelay):
            if jj == 0:
                fh.write('    take_d0 <= take_data;\n')
            else:
                fh.write('    take_d{} <= take_d{};\n'.format(jj, jj - 1))
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('// input and count process;\n')
        fh.write('always @*\n')
        fh.write('begin\n')

        gen_cnt_fback(fh, 'cnt', pdelay_cnt)
        fh.write('    next_reset_cnt = reset_cnt;\n')
        fh.write('    next_startup = startup;\n')
        fh.write('    next_final_cnt_latch = final_cnt_latch;\n')
        if start_sig:
            fh.write('    next_gate_latch = gate_latch;\n')
            fh.write('    if ((take_data == 1\'b1) && (new_cnt == 1\'b1 || gate_latch == 1\'b1)) begin\n')  # analysis:ignore
        else:
            fh.write('    if (take_data == 1\'b1) begin\n')
        fh.write('        next_reset_cnt = 1\'b0;\n')
        str_val = 'startup'
        if start_sig:
            str_val = 'new_cnt'

        fh.write('        if (final_cnt_latch == 1\'b1 || {} == 1\'b1) begin\n'.format(str_val))
        fh.write('            next_reset_cnt = 1\'b1;\n')
        fh.write('        end\n')
        fh.write('        if (final_cnt_latch == 1\'b1 || {} == 1\'b1) begin\n'.format(str_val))
        fh.write('            next_cnt_nib0 = 0;\n')
        fh.write('        end else begin\n')
        fh.write('            next_cnt_nib0 = cnt_nib0[7:0] + 1;\n')
        fh.write('        end\n')
        fh.write('        if (final_cnt == 1\'b1) begin\n')
        fh.write('            next_final_cnt_latch = 1\'b1;\n')
        fh.write('        end else if (final_cnt_latch == 1\'b1) begin\n')
        fh.write('            next_final_cnt_latch = 1\'b0;\n')
        fh.write('        end\n')
        fh.write('        next_startup = 1\'b0;\n')
        if start_sig:
            fh.write('        if (new_cnt == 1\'b1) begin\n')
            fh.write('            next_gate_latch = 1\'b1;\n')
            fh.write('        end else if (final_cnt == 1\'b1) begin\n')
            fh.write('            next_gate_latch = 1\'b0;\n')
            fh.write('        end\n')
        fh.write('    end\n')
        fh.write('\n')

        for jj in range(1, pdelay_cnt):
            str_val = ''
            if start_sig:
                str_val = str_val + ' || new_cnt_d{} == 1\'b1'.format(jj - 1)
            if jj == 1:
                fh.write('    if (reset_cnt == 1\'b1 {}) begin\n'.format(str_val))
            else:
                fh.write('    if (reset_cnt_d{} == 1\'b1 {}) begin\n'.format(jj - 1, str_val))
            fh.write('        next_cnt_nib{} = 0;\n'.format(jj))
            fh.write('    end else if (take_d{} == 1\'b1) begin\n'.format(jj - 1))
            fh.write('        next_cnt_nib{} = cnt_nib{} + cnt_nib{}[8];\n'.format(jj, jj, jj - 1))
            fh.write('    end\n')

        fh.write('end\n')
        fh.write('\n')
        fh.write('// count process\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        for jj in range(tot_latency):
            fh.write('    next_data_d{} = data_d{};\n'.format(jj, jj))

        for jj in range(pad_cnt):
            fh.write('    next_count_d{} = count_d{};\n'.format(jj, jj))

        fh.write('    if (take_data == 1\'b1) begin\n'.format(str_val))
        fh.write('        next_data_d0 = s_axis_tdata;\n')
        for jj in range(1, tot_latency):
            fh.write('        next_data_d{} = data_d{};\n'.format(jj, jj - 1))
        if pad_cnt > 0:
            fh.write('        next_count_d0 = count_s;\n')
        for jj in range(1, pad_cnt):
            fh.write('        next_count_d{} = count_d{};\n'.format(jj, jj - 1))
        fh.write('    end\n')
        str_val = ''
        fh.write('end\n')
        fh.write('// accumulate process\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        for jj in range(pdelay):
            fh.write('    next_accum_nib{} = accum_nib{};\n'.format(jj, jj))
        for ii in range(pdelay):
            for jj in range(pdelay - ii - 1):
                fh.write('    next_accum_delay{}_{} = accum_delay{}_{};\n'.format(ii, jj, ii, jj))

        for ii in range(pdelay - 1):
            fh.write('    next_adelay_{} = adelay_{};\n'.format(ii, ii))

        for ii in range(pdelay):
            idx = 8 if (ii == 1) else 9
            str_val = 'startup'
            reset_str = 'reset_cnt'
            if ii > 0:
                reset_str = 'reset_cnt_d{}'.format(ii)
            if ii == 0:
                fh.write('    if (take_data == 1\'b1) begin\n')
                fh.write('        if (final_cnt == 1\'b1 || {} == 1\'b1) begin\n'.format(str_val))
                fh.write('            next_accum_nib{} <= {{1\'b0, a[7:0]}};\n'.format(ii))
                fh.write('        end else begin\n')
                fh.write('            next_accum_nib{} <= {{1\'b0, a[7:0]}} {} {{1\'b0, accum_nib0[7:0]}};\n'.format(ii, ar_str))  #analysis:ignore
                fh.write('        end\n')
                fh.write('    end\n')
            elif ii >= pdelay_cnt:
                lidxa = ii * 8 + 7
                ridx = ii * 8
                prev = ii - 1
                lidxb = a_width - 1
                apad = lidxa - lidxb
                if apad > 8:
                    apad = 8
                if signeda is True:
                    if apad > 0:
                        pada = '{}{{adelay_{}[{}]}}'.format(apad, prev, lidxb)
                    else:
                        pada = 'adelay_{}[{}]'.format(prev, lidxb)
                else:
                    if apad > 0:
                        pada = '{}{{1\'b0}}'.format(apad)
                    else:
                        pada = '1\'b0'
                stra = ''
                if subtract:
                    strac = ', 1\'b0'
                else:
                    strac = ', accum_nib{}[{}]'.format(prev, 8)
                strb = 'accum_nib{}[7:0]'.format(ii)
                strad = ', accum_nib{}[{}]'.format(prev, 8)
                if signeda:
                    padb = 'accum_nib{}[{}]'.format(ii, 8)
                else:
                    padb = '1\'b0'
                t_val = (ii, pada, stra, strac, ar_str, padb, strb, strad)
                fh.write('    if ({} == 1\'b1) begin\n'.format(reset_str))
                fh.write('        next_accum_nib{} <= 0;\n'.format(ii))
                fh.write('    end else begin\n')
                fh.write('        next_accum_nib{} <= {{{}{}{}}} {} {{{}, {}{}}};\n'.format(*t_val))  #analysis:ignore
                fh.write('    end\n')

            else:
                lidx = ii * 8 + 7
                ridx = ii * 8
                prev = ii - 1
                if subtract:
                    t_val = (ii, prev, lidx, ridx, ar_str, prev, prev, idx)
                    fh.write('    if ({} == 1\'b1) begin\n'.format(reset_str))
                    fh.write('        next_accum_nib{} <= 0;\n'.format(ii))
                    fh.write('    end else begin\n')
                    fh.write('        next_accum_nib{} <= {{1\'b0, adelay_{}[{}:{}], 1\'b0}} {} {{1\'b0, accum_nib{}[7:0], accum_nib{}[{}]}};\n'.format(*t_val))  #analysis:ignore
                    fh.write('    end\n')
                else:
                    t_val = (ii, prev, lidx, ridx, prev, ar_str, prev, prev, idx)
                    fh.write('    if ({} == 1\'b1) begin\n'.format(reset_str))
                    fh.write('        next_accum_nib{} <= 0;\n'.format(ii))
                    fh.write('    end else begin\n')
                    fh.write('        next_accum_nib{} <= {{1\'b0, adelay_{}[{}:{}], accum_nib{}[8]}} {} {{1\'b0, accum_nib{}[7:0], accum_nib{}[{}]}};\n'.format(*t_val))  #analysis:ignore
                    fh.write('    end\n')

        for ii in range(pdelay - 1):
            if ii == 0:
                fh.write('    next_adelay_{} <= a;\n'.format(ii))
            else:
                fh.write('    next_adelay_{} <= adelay_{};\n'.format(ii, ii - 1))

        for ii in range(pdelay - 1):
            for jj in range(pdelay - ii - 1):
                if jj == 0:
                    fh.write('    next_accum_delay{}_{} <= accum_nib{};\n'.format(ii, jj, ii))
                else:
                    fh.write('    next_accum_delay{}_{} <= accum_delay{}_{};\n'.format(ii, jj, ii, jj - 1))
        fh.write('end\n')
        fh.write('// output process\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        if tuser_width > 0:
            fh.write('    next_tuser_d[0] = s_axis_tuser;\n')
            for jj in range(1, tot_latency):
                fh.write('    next_tuser_d[{}] = tuser_d[{}];\n'.format(jj, jj - 1))
        if tlast:
            fh.write('    next_tlast_d[0] = s_axis_tlast;\n')
            for jj in range(1, tot_latency):
                fh.write('    next_tlast_d[{}] = tlast_d[{}];\n'.format(jj, jj - 1))
        fh.write('end\n')
        fh.write('\n')
        if start_sig:
            s_tvalid_str = 'take_d{} & gate_latch_d{}'.format(pdelay - 1, pdelay - 2)
        else:
            s_tvalid_str = 'take_d{}'.format(pdelay - 1)

        s_tdata_str = '{{count_s, accum_s}}'
        s_tuser_str = 'tuser_d[{}]'.format(pdelay - 1)
        s_tlast_str = 'tlast_d[{}]'.format(pdelay - 1)
        m_tvalid_str = 'm_fifo_tvalid'
        m_tready_str = 'm_fifo_tready'
        m_tlast_str = 'm_fifo_tlast'
        m_tuser_str = 'm_fifo_tuser'
        m_tdata_str = 'm_fifo_tdata'
        almost_full_str = 'almost_full'
        axi_fifo_inst(fh, fifo_name, inst_name='axi_fifo', data_width=fifo_width, af_thresh=pdelay,
                      addr_width=fifo_addr_width, tuser_width=tuser_width, tlast=tlast, s_tvalid_str=s_tvalid_str,
                      s_tdata_str=s_tdata_str, s_tuser_str=s_tuser_str, s_tlast_str=s_tlast_str,
                      s_tready_str='', almost_full_str=almost_full_str, m_tvalid_str=m_tvalid_str, m_tdata_str=m_tdata_str,
                      m_tuser_str=m_tuser_str, m_tlast_str=m_tlast_str, m_tready_str=m_tready_str)

        fh.write('\n')
        fh.write('endmodule\n')

    return module_name


def gen_axi_adder(path=None, a_width=16, b_width=16, subtract=False, word_width=16, tuser_width=0, tlast=False,
                  signeda=False, signedb=False, accum=False):
    """
        Generates pipelined adder logic with AXI flow control.  It is not an entire module, just the
        necessary logic for the adder

    """

    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)

    a_width = ret_mult_eight(a_width)
    b_width = ret_mult_eight(b_width)

    max_width = np.max((a_width, b_width)) + 1
    out_msb = max_width - 1
    pdelay = adder_pipeline(max_width - 1)

    signa_str = ''
    if signeda:
        signa_str = ' signed '

    signb_str = ''
    if signedb:
        signb_str = ' signed '

    sign_str = ''
    if signedb or signeda:
        sign_str = ' signed '

    word_msb = word_width - 1

    data_width = word_width + tuser_width + int(tlast)
    data_msb = data_width - 1

    id_val = 0
    if word_width == 0:
        id_val += 1

    if tlast:
        id_val += 2

    id_val += (tuser_width << 2)

    if subtract is True:
        ar_str = '-'
        mod_str = 'axi_sub_{}_{}_{}'.format(a_width, b_width, id_val)
    else:
        ar_str = '+'
        mod_str = 'axi_add_{}_{}_{}'.format(a_width, b_width, id_val)

    if path is not None:
        file_name = path + '/' + mod_str + '.v'
    else:
        file_name = './' + mod_str + '.v'

    tuser_msb = 0
    if tuser_width > 0:
        tuser_msb = tuser_width - 1

    tdata_msb = word_width - 1
    tot_latency = pdelay

    fifo_width = word_width + max_width
    # generate axi_fifo

    fifo_depth = 2 ** int(np.ceil(np.log2(pdelay*2)))
    if fifo_depth < 8:
        fifo_depth = 8
    fifo_addr_width = int(np.log2(fifo_depth))
    (_, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, almost_full=pdelay, ram_style='distributed', tlast=tlast)

    module_name = ret_module_name(file_name)
    extra_bits = tuser_width + tlast
    with open(file_name, "w") as fh:

        fh.write('/*\n')
        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : PJV\n')
        fh.write('// File        : {}\n'.format(module_name))
        fh.write('// Description : Generates Adder/Subtract with AXI interface,  code. \n')
        fh.write('//                Useful for aligning data with addition of metadata\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('#(parameter DATA_WIDTH=32)\n')
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('    \n')
        fh.write('    input s_axis_tvalid,\n')
        if word_width > 0:
            fh.write('    input [DATA_WIDTH-1:0] s_axis_tdata,\n')
        fh.write('    input [{}:0] a,\n'.format(a_width - 1))
        fh.write('    input [{}:0] b,\n'.format(b_width - 1))
        fh.write('    output s_axis_tready,\n')
        if tlast:
            fh.write('    input  s_axis_tlast,\n')
        if tuser_width > 0:
            if tuser_width == 1:
                fh.write('    input s_axis_tuser,\n')
            else:
                fh.write('    input [{}:0] s_axis_tuser,\n'.format(tuser_msb))

        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')

        fh.write('    output [{}:0] c,\n'.format(out_msb))
        if word_width > 0:
            fh.write('    output [DATA_MSB:0] m_axis_tdata,\n')

        if tlast:
            fh.write('    output m_axis_tlast,\n')

        if tuser_width > 0:
            if tuser_width == 1:
                fh.write('    output m_axis_tuser,\n')
            else:
                fh.write('    output [{}:0] m_axis_tuser,\n'.format(tuser_msb))
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('localparam DATA_MSB = DATA_WIDTH - 1;\n')
        # create partial adder registers.
        for ii in range(pdelay):
            if ii == 0:
                fh.write('reg{} [8:0] padd_{} = 0;\n'.format(sign_str, ii))
            else:
                fh.write('reg{} [9:0] padd_{} = 0;\n'.format(sign_str, ii))
        fh.write('\n')
        if word_width > 0:
            fh.write('wire [(DATA_MSB + {}):0] input_data;\n'.format(out_msb))
        fh.write('\n')
        for ii in range(pdelay):
            for jj in range(pdelay - ii - 1):
                fh.write('reg{} [8:0] padd_delay{}_{} = 0;\n'.format(sign_str, ii, jj))
        fh.write('\n')
        # create input register delays.
        if pdelay > 1:
            for ii in range(1, pdelay):
                fh.write('reg{} [{}:0] adelay_{};\n'.format(signa_str, a_width, ii - 1, ii - 1))
                fh.write('reg{} [{}:0] bdelay_{};\n'.format(signb_str, b_width, ii - 1, ii - 1))

        fh.write('\n')
        fh.write('wire m_fifo_tvalid;\n')
        fh.write('wire [(DATA_WIDTH + {}):0] m_fifo_tdata;\n'.format(out_msb))
        fh.write('wire m_fifo_tready;\n')
        fh.write('\n')
        fh.write('wire [{}:0] c_sig;\n'.format(out_msb))
        fh.write('\n')

        if tuser_width > 0:
            fh.write('wire [{}:0] m_fifo_tuser;\n'.format(tuser_width - 1))

        if tlast:
            fh.write('wire m_fifo_tlast;\n')

        fh.write('wire take_data;\n')

        fh.write('\n')
        for jj in range(pdelay):
            fh.write('reg take_d{};\n'.format(jj))

        if word_width > 0:
            for jj in range(pdelay):
                fh.write('reg [DATA_MSB:0] data_d{};\n'.format(jj))

        fh.write('\n')
        fh.write('assign m_axis_tvalid = m_fifo_tvalid;\n')
        if word_width > 0:
            fh.write('assign m_axis_tdata = m_fifo_tdata[DATA_MSB:0];\n')
        fh.write('assign m_fifo_tready = m_axis_tready;\n')
        str_val = ''
        if word_width > 0:
            str_val = ', s_axis_tdata'
        if tlast and tuser_width > 0:
            fh.write('assign input_data = {{s_axis_tlast{}, s_axis_tdata}};\n'.format(str_val))
        elif tlast:
            fh.write('assign input_data = {{s_axis_tlast{}}};\n'.format(str_val))
        elif tuser_width > 0:
            fh.write('assign input_data = {{s_axis_tuser{}}};\n'.format(str_val))
        else:
            if word_width > 0:
                fh.write('assign input_data = s_axis_tdata;\n')

        fh.write('assign c = m_fifo_tdata[(DATA_WIDTH + {}):DATA_WIDTH];\n'.format(out_msb))
        if tlast:
            fh.write('assign m_axis_tlast = m_fifo_tlast;\n')
        if tuser_width > 0:
            fh.write('assign m_axis_tuser = m_fifo_tuser;\n')
        fh.write('assign s_axis_tready = ~almost_full;\n')
        fh.write('assign take_data = s_axis_tvalid & s_axis_tready & !sync_reset;\n')

        str_val = 'assign c_sig = {{'
        for ii in reversed(range(pdelay)):
            if ii == pdelay - 1:
                str_val += 'padd_{}[9:1]'.format(ii)
            elif ii == 0:
                str_val += 'padd_delay0_{}[7:0]'.format(pdelay - 2)
            else:
                str_val += 'padd_delay{}_{}[8:1]'.format(ii, pdelay - ii - 2)

            if ii == 0:
                str_val += '}};\n'
            else:
                str_val += ', '

        fh.write('{}'.format(str_val))
        fh.write('\n')

        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')

        for ii in range(pdelay):
            idx = 8 if (ii == 1) else 9
            if ii == 0:
                # if signeda is True:
                #     pada = 'a[7]'
                # else:
                #     pada = '1\'b0'
                #
                # if signedb is True:
                #     padb = 'b[7]''
                # else:
                #     padb = '1\'b0'

                fh.write('    padd_{} <= {{1\'b0, a[7:0]}} {} {{1\'b0, b[7:0]}};\n'.format(ii, ar_str))
            elif ii == (pdelay - 1):
                lidxa = a_width - 1
                ridx = (pdelay - 1) * 8
                lidxb = b_width - 1
                prev = pdelay - 2

                if signeda is True:
                    pada = 'adelay_{}[{}]'.format(pdelay - 2, lidxa)
                else:
                    pada = '1\'b0'

                if signedb is True:
                    padb = 'bdelay_{}[{}]'.format(pdelay - 2, lidxb)
                else:
                    padb = '1\'b0'

                stra = 'adelay_{}[{}:{}]'.format(prev, lidxa, ridx)
                if subtract:
                    strac = ', 1\'b0'
                else:
                    strac = ', padd_{}[{}]'.format(prev, idx)
                strb = 'bdelay_{}[{}:{}]'.format(prev, lidxb, ridx)
                strad = ', padd_{}[{}]'.format(prev, idx)
                t_val = (ii, pada, stra, strac, ar_str, padb, strb, strad)
                fh.write('    padd_{} <= {{{}, {}{}}} {} {{{}, {}{}}};\n'.format(*t_val))  #analysis:ignore

            else:
                lidx = ii * 8 + 7
                ridx = ii * 8
                prev = ii - 1
                if subtract:
                    t_val = (ii, prev, lidx, ridx, ar_str, prev, lidx, ridx, prev, idx)
                    fh.write('    padd_{} <= {{1\'b0, adelay_{}[{}:{}], 1\'b0}} {} {{1\'b0, bdelay_{}[{}:{}], padd_{}[{}]}};\n'.format(*t_val))  #analysis:ignore
                else:
                    t_val = (ii, prev, lidx, ridx, prev, idx, ar_str, prev, lidx, ridx, prev, idx)
                    fh.write('    padd_{} <= {{1\'b0, adelay_{}[{}:{}], padd_{}[{}]}} {} {{1\'b0, bdelay_{}[{}:{}], padd_{}[{}]}};\n'.format(*t_val))  #analysis:ignore

        for ii in range(pdelay - 1):
            if ii == 0:
                fh.write('    adelay_{} <= a;\n'.format(ii))
                fh.write('    bdelay_{} <= b;\n'.format(ii))
            else:
                fh.write('    adelay_{} <= adelay_{};\n'.format(ii, ii - 1))
                fh.write('    bdelay_{} <= bdelay_{};\n'.format(ii, ii - 1))

        for ii in range(pdelay - 1):
            for jj in range(pdelay - ii - 1):
                if jj == 0:
                    fh.write('    padd_delay{}_{} <= padd_{};\n'.format(ii, jj, ii))
                else:
                    fh.write('    padd_delay{}_{} <= padd_delay{}_{};\n'.format(ii, jj, ii, jj - 1))
        fh.write('end\n')
        fh.write('// output process\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')

        if word_width > 0:
            fh.write('    data_d0 <= input_data;\n')
            for jj in range(1, pdelay):
                fh.write('    data_d{} <= data_d{};\n'.format(jj, jj - 1))
        fh.write('    take_d0 <= take_data;\n')
        for jj in range(1, pdelay):
            fh.write('    take_d{} <= take_d{};\n'.format(jj, jj - 1))
        fh.write('end\n')
        fh.write('\n')
        almost_full_thresh = 1 << (fifo_addr_width - 1)
        if word_width > 0:
            tdata_str = '{{c_sig, data_d{}[DATA_MSB:0]}}'.format(pdelay - 1)
        else:
            tdata_str = 'c_sig'
        tuser_str = 'data_d{}[DATA_MSB + {}:DATA_WIDTH]'.format(pdelay - 1, tuser_width)
        tlast_str = 'data_d{}[DATA_WIDTH + {}]'.format(pdelay - 1, tuser_width)
        axi_fifo_inst(fh, fifo_name, inst_name='axi_fifo', data_width='DATA_WIDTH + {}'.format(out_msb), af_thresh=almost_full_thresh,
                      addr_width=fifo_addr_width, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='take_d{}'.format(pdelay-1),
                      s_tdata_str=tdata_str, s_tuser_str=tuser_str, s_tlast_str=tlast_str,
                      s_tready_str='', almost_full_str='almost_full', m_tvalid_str='m_fifo_tvalid', m_tdata_str='m_fifo_tdata',
                      m_tuser_str='m_fifo_tuser', m_tlast_str='m_fifo_tlast', m_tready_str='m_fifo_tready')

        fh.write('\n')
        fh.write('endmodule\n')

    return (mod_str, pdelay, fifo_name)


def gen_adder(path=None, a_width=16, b_width=16, subtract=False, signeda=False,
              signedb=False, tot_latency=None, accum=False):
    """
        Generates pipelined adder logic.  It is not an entire module, just the
        necessary logic for the adder

    """
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)
    a_width = ret_mult_eight(a_width)
    b_width = ret_mult_eight(b_width)
    max_width = np.max((a_width, b_width)) + 1

    out_msb = max_width - 1
    num_clocks = int(np.ceil((max_width - 1) / 8.))

    if accum is False:
        if subtract is True:
            ar_str = '-'
            mod_str = 'sub_{}_{}_l{}'.format(a_width, b_width, num_clocks)
        else:
            ar_str = '+'
            mod_str = 'add_{}_{}_l{}'.format(a_width, b_width, num_clocks)
    else:
        ar_str = '+'
        mod_str = 'accum_{}_l{}'.format(a_width, num_clocks)

    if path is not None:
        file_name = path + '/' + mod_str + '.v'
    else:
        file_name = './' + mod_str + '.v'

    pdelay = adder_pipeline(max_width)
    if tot_latency is not None:
        pad = tot_latency - pdelay
        if pad < 0:
            pad = 0
            tot_latency = pdelay
    else:
        tot_latency = pdelay
        pad = 0

    mod_name = ret_module_name(file_name)
    with open(file_name, "w") as fh:
        fh.write('/*****************************************************************************/\n')
        fh.write('//')
        fh.write('// Author      : Python Generated\n')
        fh.write('// File        : {}\n'.format(mod_name))
        fh.write('// Description : Implements a fully pipelined adder.\n')
        fh.write('//\n')
        fh.write('//\n')
        fh.write('//\n')
        fh.write('// LICENSE     : SEE LICENSE FILE AGREEMENT,\n')
        fh.write('//\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')

        fh.write('module {}\n'.format(mod_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        # fh.write('    input sync_reset,\n')
        fh.write('    input valid_i,\n')
        fh.write('    input [{}:0] a,\n'.format(a_width - 1))
        if accum is False:
            fh.write('    input [{}:0] b,\n'.format(b_width - 1))
        fh.write('    output valid_o,\n')
        fh.write('    output [{}:0] c\n'.format(out_msb))
        fh.write(');\n')
        fh.write('\n')
        # create partial adder registers.
        for ii in range(num_clocks):
            if ii == 0:
                fh.write('reg [8:0] padd_{} = 9\'d0;\n'.format(ii))
            else:
                fh.write('reg [9:0] padd_{} = 10\'d0;\n'.format(ii))

        for ii in range(num_clocks):
            for jj in range(num_clocks - ii - 1):
                if ii == 0:
                    fh.write('reg [7:0] padd_delay{}_{};\n'.format(ii, jj))
                else:
                    fh.write('reg [8:0] padd_delay{}_{};\n'.format(ii, jj))


        # create input register delays.
        if num_clocks > 1:
            for ii in range(1, num_clocks):
                fh.write('reg [{}:0] adelay_{} = 0;\n'.format(a_width - 1, ii - 1))
                if accum is False:
                    fh.write('reg [{}:0] bdelay_{};\n'.format(b_width - 1, ii - 1))

            fh.write('reg [{}:0] valid_d;\n'.format(num_clocks - 1))
        else:
            fh.write('reg valid_d;\n')

        if num_clocks > 1:
            fh.write('assign valid_o = valid_d[{}];\n'.format(num_clocks - 1))
        else:
            fh.write('assign valid_o = valid_d;\n')

        # lidx = np.min((num_clocks * 8 - 1, max_width - 1)) - (num_clocks - 1) * 8
        str_val = 'assign c = {'
        for ii in reversed(range(num_clocks)):
            if ii == num_clocks - 1:
                str_val += 'padd_{}[9:1]'.format(ii)
            elif ii == 0:
                str_val += 'padd_delay0_{}[7:0]'.format(num_clocks - 2)
            else:
                str_val += 'padd_delay{}_{}[8:1]'.format(ii, num_clocks - ii - 2)

            if ii == 0:
                str_val += '};\n'
            else:
                str_val += ', '

        fh.write('{}'.format(str_val))
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        tb = ""
        if accum:
            tb = "    "
            
        for ii in range(num_clocks):

            if num_clocks == 1:
                if accum:
                    fh.write('    if (valid_i == 1\'b1) begin;\n')
                fh.write('{}    valid_d <= valid_i;\n'.format(tb))
            else:
                if ii == 0:
                    if accum:
                        fh.write('    if (valid_i == 1\'b1) begin;\n')
                    fh.write('{}    valid_d[{}] <= valid_i;\n'.format(tb, ii))
                else:
                    if accum:
                        fh.write('    if (valid_d[{}] == 1\'b1) begin;\n'.format(ii - 1))
                    fh.write('{}    valid_d[{}] <= valid_d[{}];\n'.format(tb, ii, ii - 1))
#         for ii in range(num_clocks):
            idx = 8 if (ii == 1) else 9
            if ii == 0:
                if accum is True:
                    fh.write('{}    padd_{} <= {{1\'b0, a[7:0]}} {} padd_0;\n'.format(tb, ii, ar_str))
                else:
                    fh.write('{}    padd_{} <= {{1\'b0, a[7:0]}} {} {{1\'b0, b[7:0]}};\n'.format(tb, ii, ar_str))
            elif ii == (num_clocks - 1):
                lidxa = a_width - 1
                ridx = (num_clocks - 1) * 8
                lidxb = b_width - 1
                prev = num_clocks - 2

                if signeda is True:
                    pada = 'adelay_{}[{}]'.format(pdelay - 2, lidxa)
                else:
                    pada = '1\'b0'

                if accum is False:
                    if signedb is True:
                        padb = 'bdelay_{}[{}]'.format(pdelay - 2, lidxb)
                    else:
                        padb = '1\'b0'
                else:
                    padb = 'padd_{}[{}]'.format(ii, idx)

                stra = 'adelay_{}[{}:{}]'.format(prev, lidxa, ridx)
                if subtract:
                    strac = ', 1\'b0'
                else:
                    strac = ', padd_{}[{}]'.format(prev, idx)
                if accum is False:
                    strb = 'bdelay_{}[{}:{}]'.format(prev, lidxb, ridx)
                    strad = ', padd_{}[{}]'.format(prev, idx)
                    t_val = (tb, ii, pada, stra, strac, ar_str, padb, strb, strad)
                    fh.write('{}    padd_{} <= {{{}, {}{}}} {} {{{{{}}}, {}{}}};\n'.format(*t_val))  #analysis:ignore
                else:
                    strb = 'padd_{}'.format(ii)
                    t_val = (tb, ii, pada, stra, strac, ar_str, strb)
                    fh.write('{}    padd_{} <= {{{}, {}{}}} {} {};\n'.format(*t_val))  #analysis:ignore
            else:
                lidx = ii * 8 + 7
                ridx = ii * 8
                prev = ii - 1
                if accum is True:
                    strb = 'padd_{}'.format(ii)
                    t_val = (tb, ii, prev, lidx, ridx, ar_str, strb)
                    fh.write('{}    padd_{} <= {{1\'b0, adelay_{}[{}:{}], 1\'b0}} {} {};\n'.format(*t_val))
                else:
                    if subtract:
                        t_val = (tb, ii, prev, lidx, ridx, ar_str, prev, lidx, ridx, prev, idx)
                        fh.write('{}    padd_{} <= {{1\'b0, adelay_{}[{}:{}], 1\'b0}} {} {{1\'b0, bdelay_{}[{}:{}], padd_{}[{}]}};\n'.format(*t_val))  #analysis:ignore
                    else:
                        t_val = (tb, ii, prev, lidx, ridx, prev, idx, ar_str, prev, lidx, ridx, prev, idx)
                        fh.write('{}    padd_{} <= {{1\'b0, adelay_{}[{}:{}], padd_{}[{}]}} {} {{1\'b0, bdelay_{}[{}:{}], padd_{}[{}]}};\n'.format(*t_val))  #analysis:ignore

#         for ii in range(num_clocks - 1):
            if ii == 0:
                fh.write('{}    adelay_{} <= a;\n'.format(tb, ii))
                if accum is False:
                    fh.write('{}    bdelay_{} <= b;\n'.format(tb, ii))
            elif ii < num_clocks - 1:
                fh.write('{}    adelay_{} <= adelay_{};\n'.format(tb, ii, ii - 1))
                if accum is False:
                    fh.write('{}    bdelay_{} <= bdelay_{};\n'.format(tb, ii, ii - 1))

#         for ii in range(num_clocks - 1):
            for jj in range(num_clocks - ii - 1):
                if jj == 0:
                    if ii == 0:
                        fh.write('{}    padd_delay{}_{} <= padd_{}[7:0];\n'.format(tb, ii, jj, ii))
                    else:
                        fh.write('{}    padd_delay{}_{} <= padd_{}[8:0];\n'.format(tb, ii, jj, ii))

                elif ii < num_clocks - 1:
                    fh.write('{}    padd_delay{}_{} <= padd_delay{}_{};\n'.format(tb, ii, jj, ii, jj - 1))
    
            if accum:
                fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return (mod_str, num_clocks)


def gen_pipe_logic(path, input_width, l_func='xor', file_path=None):
    '''
        Function generates Verilog module of a fully pipelined logic
        function.
        The inputs should be a single concatenated signal.

        ==========
        Parameters
        ==========

            * input_width (int)
                input vector width
            * l_func (str)
                Logic operator to be fully pipelined.
            * file_path (str)
                Default current working directory.
        =======
        Returns
        =======

            Verilog file that implements a fully pipelined multiplexer.

    '''
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)
    mod_name = ('pipe_%s_%d.v' % (l_func, input_width))
    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)

    num_stages = fp_utils.nextpow2(input_width)

    gates = []
    rem_gates = []
    num_bits = copy.copy(input_width)
    for stage in range(num_stages):
        temp = int(np.ceil(num_bits / 2.))
        rem_gates.append(num_bits % 2)
        gates.append(temp)
        num_bits = temp

    logic_str = '&'
    if (l_func.lower() == 'xor'):
        logic_str = '^'
    with open(file_name, "w") as fh:
        fh.write('/*****************************************************************************/\n')
        fh.write('//')
        fh.write('// Author      : Python Generated\n')
        fh.write('// File        : ' + file_name + '\n')
        fh.write('// Description : Implements a pipelined {}.\n'.format(l_func))
        fh.write('//\n')
        fh.write('//\n')
        fh.write('//\n')
        fh.write('// LICENSE     : SEE LICENSE FILE AGREEMENT,\n')
        fh.write('//\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('    input valid_i,\n')
        fh.write('    input [{}:0] input_word,\n'.format(input_width - 1))
        fh.write('    output valid_o,\n')
        fh.write('    output output_word\n')
        fh.write(');\n')
        fh.write('\n')

        for (ii, regs) in enumerate(gates):
            for idx in range(regs):
                fh.write('reg {}_{}_{};\n'.format(l_func, ii, idx))

        fh.write('\n')
        for idx in range(num_stages):
            fh.write('reg valid{};\n'.format(idx))

        fh.write('\n')
        fh.write('assign valid_o = valid{};\n'.format(num_stages - 1))
        lidx = num_stages - 1
        fh.write('assign output_word = {}_{}_{};\n'.format(l_func, lidx, 0))
        fh.write('\n')
        fh.write('always @(posedge clk) begin\n')
        fh.write('    if (sync_reset) begin\n')
        for idx in range(num_stages):
            fh.write('        valid%d <= 1\'b0;\n' % idx)
        fh.write('    end else begin\n')
        for idx in range(num_stages):
            if (idx == 0):
                fh.write('        valid0 <= valid_i;\n')
            else:
                fh.write('        valid{} <= valid{};\n'.format(idx, idx - 1))
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')

        fh.write('\n')
        fh.write('always @(posedge clk) begin\n')
        for (ii, regs, remain_gates) in zip(count(), gates, rem_gates):
            for idx in range(regs):
                lidx = idx * 2
                ridx = lidx + 1
                insert_reg = False
                if (idx == regs - 1):
                    if (remain_gates != 0):
                        insert_reg = True
                if ii == 0:
                    if (insert_reg):
                        fh.write('    {}_{}_{} <= input_word[{}];\n'.format(l_func, ii, idx, lidx))
                    else:
                        fh.write('    {}_{}_{} <= input_word[{}] {} input_word[{}];\n'.format(l_func, ii, idx, lidx, logic_str, ridx))  #analysis:ignore
                else:
                    if (insert_reg):
                        fh.write('    {}_{}_{} <= {}_{}_{};\n'.format(l_func, ii, idx, l_func, ii - 1, lidx))
                    else:
                        fh.write('    {}_{}_{} <= {}_{}_{} {} {}_{}_{};\n'.format(l_func, ii, idx, l_func, ii - 1, lidx, logic_str, l_func, ii - 1, ridx))  #analysis:ignore
            fh.write('\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('endmodule\n')


# def gen_count_items(input_width, count_width, latency=2, path=None, c_str=None):
#     """
#         Generates the count items module.
#     """
#     mod_str = 'count_items_iw{}_cw{}'.format(input_width, count_width)
#     input_msb = input_width - 1
#     count_msb = count_width - 1
#     lat_bits = fp_utils.ret_num_bitsU(latency)
#     reset_str = fp_utils.dec_to_ubin(latency - 1, num_bits=lat_bits)[0]
#     count_name = 'counter_w{}_l{}'.format(count_width, latency)
#     if path is not None:
#         file_name = path + '/' + mod_str + '.v'
#     else:
#         file_name = './' + mod_str
#     with open(file_name, "wb") as fh:
#
#         fh.write('//***************************************************************************/\n')
#         fh.write('//\n')
#         fh.write('// Author      : Phil Vallance\n')
#         fh.write('// File        : {}.v\n'.format(mod_str))
#         fh.write('// Description : Module time aligns a count sequence with the incoming data.\n')
#         fh.write('//               Using a pipelined counter coure.\n')
#         fh.write('//\n')
#         fh.write('//\n')
#         fh.write('//This software is property of Vallance Engineering, LLC and may\n')
#         fh.write('//not be used, reviewed, or distributed without prior written consent.\n')
#         fh.write('//                                                        (c) 2016\n')
#         fh.write('//***************************************************************************/\n')
#         fh.write('\n')
#         fh.write('module {}\n'.format(mod_str))
#         fh.write('(\n')
#         fh.write('	input sync_reset,\n')
#         fh.write('	input clk,\n')
#         fh.write('	input valid_i,\n')
#         fh.write('	input reset_cnt,\n')
#         fh.write('	input [{}:0] data_i,\n'.format(input_msb))
#         fh.write('	output valid_o,\n')
#         fh.write('	output [{}:0] count_o,\n'.format(count_msb))
#         fh.write('	output [{}:0] data_o\n'.format(input_msb))
#         fh.write(');\n')
#         fh.write('\n')
#         fh.write('\n')
#         fh.write('wire [{}:0] cnt;\n'.format(count_msb))
#         fh.write('reg [{}:0] l_value = {}\'d0;\n'.format(count_msb, count_width))
#         fh.write('\n')
#         for i in range(latency):
#             fh.write('reg [{}:0] out_d{}, next_out_d{};\n'.format(input_msb, i, i))
#         fh.write('\n')
#         fh.write('reg [{}:0] init_cnt, next_init_cnt;\n'.format(lat_bits - 1))
#         fh.write('reg count_valid, next_count_valid;\n')
#         fh.write('reg first_flag, next_first_flag;\n')
#         fh.write('wire reset_cnt_s;\n')
#         fh.write('\n')
#         fh.write('assign valid_o = count_valid;\n')
#         fh.write('assign data_o = out_d{};\n'.format(latency - 1))
#         fh.write('assign count_o = cnt;\n')
#         fh.write('assign reset_cnt_s = 1\'b1 ? (first_flag == 1\'b1 && valid_i == 1\'b1) : reset_cnt;\n')
#         fh.write('\n')
#         fh.write('\n')
#         fh.write('// do a reset\n')
#         fh.write('always @(posedge clk)\n')
#         fh.write('begin\n')
#         fh.write('    if (sync_reset == 1\'b1) begin\n')
#         fh.write('	    init_cnt <= {}\'b{};\n'.format(lat_bits, reset_str))
#         fh.write('        count_valid <= 1\'b0;\n')
#         fh.write('        first_flag <= 1\'b1;\n')
#         for i in range(latency):
#             fh.write('        out_d{} <= 0;\n'.format(i))
#         fh.write('    end else begin\n')
#         for i in range(latency):
#             fh.write('        out_d{} <= next_out_d{};\n'.format(i, i))
#         fh.write('        init_cnt <= next_init_cnt;\n')
#         fh.write('        first_flag <= next_first_flag;\n')
#         fh.write('        count_valid <= next_count_valid;\n')
#         fh.write('    end\n')
#         fh.write('end\n')
#         fh.write('\n')
#         fh.write('always @*\n')
#         fh.write('begin\n')
#         for i in range(latency):
#             fh.write('    next_out_d{} = out_d{};\n'.format(i, i))
#         fh.write('    next_init_cnt = init_cnt;\n')
#         fh.write('    next_count_valid = 1\'b0;\n')
#         fh.write('    next_first_flag = first_flag;\n')
#         fh.write('    if (valid_i == 1\'b1) begin\n')
#         fh.write('        next_out_d0 = data_i;\n')
#         fh.write('        next_first_flag = 1\'b0;\n')
#         for i in range(1, latency):
#             fh.write('        next_out_d{} = out_d{};\n'.format(i, i - 1))
#         fh.write('        if (init_cnt != 0) begin\n')
#         fh.write('            next_init_cnt = init_cnt - 1;\n')
#         fh.write('        end\n')
#         fh.write('\n')
#         fh.write('        if (init_cnt == 0 && valid_i == 1\'b1) begin\n')
#         fh.write('            next_count_valid = 1\'b1;\n')
#         fh.write('	    end\n')
#         fh.write('	end\n')
#         fh.write('end\n')
#         fh.write('\n')
#         fh.write('{} {} (\n'.format(count_name, count_name))
#         fh.write('  .CLK(clk), \n')
#         fh.write('  .CE(valid_i), \n')
#         fh.write('  .SCLR(sync_reset), \n')
#         fh.write('  .LOAD(reset_cnt_s), \n')
#         fh.write('  .L(l_value), \n')
#         fh.write('  .Q(cnt)\n')
#         fh.write(');\n')
#         fh.write('\n')
#         fh.write('endmodule\n')
#
#     if c_str is not None:
#         c_str.write('##################################################\n')
#         c_str.write('{} Cores\n'.format(mod_str))
#         c_str.write('##################################################\n')
#         c_str.write('############################\n')
#         c_str.write('Counter\n')
#         c_str.write('Latency = {}\n'.format(latency))
#         c_str.write('Block Name = {}\n'.format(count_name))
#         c_str.write('Use CE\n')
#         c_str.write('Use Load\n')
#         c_str.write('Use Sync Reset\n')
#         c_str.write('Loadable = True\n')
#         c_str.write('Output Width = {}\n'.format(count_width))
#         c_str.write('############################\n')
#
#     return mod_str


def gen_one_hot(input_width, file_path=None):
    '''
        Function generates Verilog module of a one hot encoder -- simply
        explicitly implements the case statementfully pipelined mux.
        The inputs should be a single concatenated signal.
    '''
    output_width = 2 ** input_width

    file_name = 'one_hot_%d_%d.v' % (input_width, output_width)

    if file_path is None:
        file_path = os.getcwd()

    file_name = os.path.join(file_path, file_name)
    mod_name = ret_module_name(file_name)
    hex_chars = output_width // 4

    out_msb = output_width - 1

    with open(file_name, 'w') as fh:
        fh.write('/*******************************************************/\n')
        fh.write('//')
        fh.write('// File        : {}\n'.format(mod_name))
        fh.write('// Description : Implements a one_hot decoder\n')
        fh.write('// This module has a delay of 1 clock cycles')
        fh.write('//\n')
        fh.write('// -----------------------------------------------------\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/******************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module one_hot_{}_{}\n'.format(input_width, output_width))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input [{}:0] input_word,\n'.format(input_width - 1))
        fh.write('    output [{}:0] output_word\n'.format(out_msb))
        fh.write(');\n\n')
        fh.write('reg [{}:0] output_reg, next_output_reg;\n'.format(out_msb))
        fh.write('assign output_word = output_reg;\n')
        fh.write('\n')
        fh.write('always @(posedge clk) begin\n')
        fh.write('    output_reg <= next_output_reg;\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    case (input_word)\n')
        for ii in range(output_width):
            case_str = '{0:b}'.format(ii)
            case_str = str.zfill(case_str, input_width)
            case_str = '{}\'b{}'.format(input_width, case_str)
            # right_str = '{0:b}'.format(2**ii)
            # right_str = str.zfill(right_str, output_width)
            hex_val = hex(2**ii)[2:]
            if hex_val[-1] == 'L':
                hex_val = hex_val[:-1]
            hex_val = str.zfill(hex_val, hex_chars)
            right_str = '{}\'h{}'.format(output_width, hex_val)

            fh.write('        {} : next_output_reg = {};\n'.format(case_str, right_str))
        fh.write('    endcase\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return mod_name, file_name


def gen_pipe_mux(path, input_width, output_width, mux_bits=2, one_hot=False, one_hot_out=False):
    '''
        Function generates Verilog module of a fully pipelined mux.
        Input is a single concatenated signal.

        ==========
        Parameters
        ==========

            * input_width (int)
                input vector width
            * output_width (int)
                output vector width
            * file_path (str)
                Default current working directory.
            * mux_bits
                2**mux_bits input signals to each mux.  Input signal width
                equal to final output_width

        =======
        Returns
        =======

            Verilog file that implements a fully pipelined multiplexer.

    '''


    module_name = 'pipe_mux_{}_{}'.format(input_width, output_width)
    file_name = name_help(module_name, path)

    # if one-hot encoding, then embedd rom to convert to binary form.
    io_ratio = input_width / output_width

    assert (io_ratio.is_integer()), ("Input to Output ratio must be an integer value")

    one_hot_width = int(np.ceil(io_ratio))
    num_sels = np.ceil(np.log2(io_ratio)).astype(np.int)

    # if one_hot:
    #     table = np.arange(one_hot_width)
    #     num_bits = fp_utils.ret_num_bitsU(table[-1])
    #     table_fi = fp_utils.ufi(table, qvec=(num_bits, 0), signed=0)
    #     (rom_file, rom_name) = gen_rom(file_path, table_fi, rom_type='sp', rom_style='distributed')

    if mux_bits > num_sels:
        mux_bits = num_sels

    sels_msb = num_sels - 1

    mux_div_factor = 2**mux_bits
    num_mux_stages = np.ceil(num_sels / mux_bits).astype(np.int)

    sel_bits = num_sels
    sel_incr = mux_bits

    tot_latency = num_mux_stages + 1  # +1 for input delay.
    num_mux_per_stage = []
    mux_widths = []
    curr_width = input_width
    rhs_tuples = []
    sel_tuples = []
    sel_bits_rem = num_sels
    sel_rhs = 0
    for ii in range(num_mux_stages):
        io_ratio = np.ceil(io_ratio / mux_div_factor).astype(np.int)
        num_mux_per_stage.append(io_ratio)
        sel_lhs = sel_rhs + sel_incr - 1
        if sel_lhs > sel_bits - 1:
            sel_lhs = sel_bits - 1
        sel_tuples.append((sel_lhs, sel_rhs))
        sel_rhs += sel_incr
        temp_ratio = []
        for ii in range(io_ratio):
             lhs = (ii + 1) * curr_width // io_ratio - 1
             rhs = ii * curr_width // io_ratio
             temp_ratio.append((lhs, rhs))
        rhs_tuples.append(temp_ratio)
        curr_width = np.ceil(curr_width / mux_div_factor).astype(np.int)
        mux_widths.append(output_width)

    sel_strs = []
    mux_strs = []

    for (jj, num_muxes) in enumerate(num_mux_per_stage):
        temp = []
        temp_mux = []
        for ii in range(num_muxes):
            temp.append('sel_d{}_{}'.format(jj, ii))
            temp_mux.append('mux_d{}_{}'.format(jj, ii))
        sel_strs.append(temp)
        mux_strs.append(temp_mux)
    sel_strs.append(['sel_d{}'.format(len(num_mux_per_stage))])

    with open(file_name, 'w') as fh:

        fh.write('/*************************************************************************/\n')
        fh.write('//')
        fh.write('// File        : {}.v\n'.format(module_name))
        fh.write('// Description : Implements a pipelined multiplexer to be '
                 'used in high speed design\n')
        fh.write('// This module has a delay of {} clock cycles'.format(tot_latency))
        fh.write('//\n')
        fh.write('// -------------------------------------------------------------------\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/***************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('    input valid_i,\n')
        if one_hot:
            fh.write('    input [{}:0] sel,\n'.format(one_hot_width - 1))
        else:
            fh.write('    input [{}:0] sel,\n'.format(num_sels - 1))
        fh.write('    input [{}:0] input_word,\n'.format(input_width - 1))
        fh.write('    output valid_o,\n')
        if one_hot_out:
            fh.write('    output [{}:0] sel_o,\n'.format(one_hot_width - 1))
        else:
            fh.write('    output [{}:0] sel_o,\n'.format(num_sels - 1))
        if output_width == 1:
            fh.write('    output output_word\n')
        else:
            fh.write('    output [{}:0] output_word\n'.format(output_width - 1))

        fh.write(');\n')
        fh.write('\n')
        sels_used = 0
        for index in range(num_mux_stages):
            sels_msb = num_sels - 1
            for str_val in sel_strs[index]:
                fh.write('(* KEEP = "TRUE" *) reg [{}:0] {};\n'.format(sels_msb, str_val))
        fh.write('(* KEEP = "TRUE" *) reg [{}:0] {};\n'.format(sels_msb, sel_strs[-1][0]))
        for ii in range(num_mux_stages + 1 + one_hot):
            fh.write('reg valid_d{};\n'.format(ii))

        # for index in range(num_mux_stages)
        for index in range(num_mux_stages):
            mux_msb = mux_widths[index] - 1
            for mux_str in mux_strs[index]:
                fh.write('reg [{}:0] {}, next_{};\n'.format(mux_msb, mux_str, mux_str))

        fh.write('reg [{}:0] input_word_d;\n'.format(input_width - 1))

        if one_hot:
            fh.write('reg [{}:0] sel_lu;\n'.format(num_sels - 1))
            fh.write('reg [{}:0] input_word_d1;\n'.format(input_width - 1))
            if one_hot_out:
                for ii in range(num_mux_stages + 1):
                    fh.write('reg [{}:0] one_hot_d{};\n'.format(one_hot_width - 1, ii))
        fh.write('\n')
        fh.write('assign output_word = {};\n'.format(mux_strs[-1][0]))
        fh.write('assign valid_o = valid_d{};\n'.format(num_mux_stages))
        if one_hot_out:
            fh.write('assign sel_o = one_hot_d{};\n'.format(num_mux_stages))
        else:
            fh.write('assign sel_o = {};\n'.format(sel_strs[-1][0]))
        fh.write('\n')
        fh.write('always @(posedge clk) begin\n')
        fh.write('    if (sync_reset) begin\n')
        for ii in range(num_mux_stages + 1 + one_hot):
            fh.write('        valid_d{}  <= 0;\n'.format(ii))
        fh.write('    end else begin\n')
        fh.write('        valid_d0  <= valid_i;\n')
        for ii in range(num_mux_stages + one_hot):
            fh.write('        valid_d{}  <= valid_d{};\n'.format(ii + 1, ii))
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        if one_hot:
            fh.write('always @(posedge clk) begin\n')
            for ii in range(1, one_hot_width):
                dec_val = 2 ** (ii - 1)
                bin_val = fp_utils.dec_to_ubin(dec_val, one_hot_width)[0]
                if ii == 0:
                    fh.write('    if (sel == {}\'b{}) begin\n'.format(one_hot_width, bin_val))
                else:
                    fh.write('    end else if (sel == {}\'b{}) begin\n'.format(one_hot_width, bin_val))

                bin_val = fp_utils.dec_to_ubin(ii, num_sels)[0]

                fh.write('        sel_lu = {}\'b{};\n'.format(num_sels, bin_val))
            fh.write('    end else begin\n')
            bin_val = fp_utils.dec_to_ubin(0, num_sels)[0]
            fh.write('        sel_lu = {}\'b{};\n'.format(num_sels, bin_val))
            fh.write('    end\n')
        fh.write('\n')
        fh.write('always @(posedge clk) begin\n')
        fh.write('    input_word_d <= input_word;\n')
        if one_hot_out:
            for ii in range(num_mux_stages + 1):
                if ii == 0:
                    fh.write('    one_hot_d{} <= sel;\n'.format(ii))
                else:
                    fh.write('    one_hot_d{} <= one_hot_d{};\n'.format(ii, ii - 1))
        if one_hot:
            fh.write('    input_word_d1 <= input_word_d;\n')
        for str_vals in mux_strs:
            for mux_str in str_vals:
                fh.write('    {} <= next_{};\n'.format(mux_str, mux_str))

        # if one_hot:
        #     for str_val in reg_sel_strs[0]:
        #         fh.write('    {} <= next_sel;\n'.format(str_val))
        # else:
        for (ii, str_vals) in enumerate(sel_strs):
            if ii == 0:
                if one_hot:
                    rhs = 'sel_lu'
                else:
                    rhs = 'sel'
            else:
                rhs = sel_strs[ii-1][-1]
            for sel_str in str_vals:
                fh.write('    {} <= {};\n'.format(sel_str, rhs))
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        for (ii, depth) in enumerate(num_mux_per_stage):
            for mux_str in mux_strs[ii]:
                fh.write('    next_{} = {};\n'.format(mux_str, mux_str))
        fh.write('\n')

        incr = 2**mux_bits
        num_sels_rem = num_sels
        input_rhs = 'input_word_d'
        if one_hot:
            input_rhs = 'input_word_d1'
        for ii in range(num_mux_stages):
            max_idx = input_width - 1
            num_muxes = len(mux_strs[ii])
            sel_tuple = sel_tuples[ii]
            num_stmts = 2 ** (sel_tuple[0] - sel_tuple[1] + 1)
            mux_width = mux_widths[ii]
            # ipdb.set_trace()
            for jj, mux_str, sel_str in zip(count(), mux_strs[ii], sel_strs[ii]):
                rhs_tuple = rhs_tuples[ii][jj]
                for nn in range(num_stmts):
                    rhs = rhs_tuple[1] + nn
                    lhs = rhs + mux_width - 1
                    arg_str = '[{}:{}]'.format(lhs, rhs)
                    if ii > 0:
                        input_rhs = mux_strs[ii - 1][rhs]
                    if lhs - rhs == 0:
                        arg_str = '[{}]'.format(rhs)
                    if ii > 0:
                        arg_str = ''

                    if nn == 0:
                        fh.write('    if ({}[{}:{}] == {}) begin\n'.format(sel_str, sel_tuple[0], sel_tuple[1], nn))
                    elif (nn == num_stmts - 1):
                        fh.write('    end else begin\n')
                    else:
                        fh.write('    end else if ({}[{}:{}] == {}) begin\n'.format(sel_str, sel_tuple[0], sel_tuple[1], nn))
                    fh.write('        next_{} = {}{};\n'.format(mux_str, input_rhs, arg_str))
                fh.write('    end\n')
                fh.write('\n')

        fh.write('end\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return (file_name, tot_latency)


def gen_slicer(path, input_width=48, output_width=16, input_base=None, max_offset=31, rev_dir=False, prefix=''):
    '''
        Function generates Verilog module of for a configurable slicer.
        The output is a sliced version of the input.  The offset port defines
        the LSB offset from the bottom of the input bit stack.

        ==========
        Parameters
        ==========

            * input_width (int)
                input vector width
            * output_width (int)
                output vector width
            * file_path (str)
                Default current working directory.
            * max_offset
                Maximum user defined bit offset.
            * input_base
                Defines the true base of the input vector.  Allows the
                slicer to slice the actual occupied bits.
            * rev_dir
                Boolean to indicate whether slice offset begins counting
                from the LSB or offset from the MSB.
                Default : relative to LSB.


        =======
        Returns
        =======

            Verilog file that implements a slicer module.

    '''

    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)
    mod_name = '{}slicer_{}_{}'.format(prefix, input_width, output_width)
    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)

    in_str = str(input_width - 1)
    out_str = str(output_width - 1)

    ctrl_bits = ret_num_bitsU(max_offset)

    diff_bits = 0 if input_base is None else input_base - output_width
    ctrl_str = str(ctrl_bits - 1)

    with open(file_name, 'w') as fh:
        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : Python Generated\n')
        fh.write('// File        : ' + file_name + '\n')
        fh.write('// Description : Generates a variable slicer module.\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module {}(\n'.format(module_name))
        fh.write('  input sync_reset,\n')
        fh.write('  input clk,\n')
        fh.write('\n')
        fh.write('// Settings offet the slicer from the base value.\n')
        fh.write('  input [{}:0] slice_offset_i,\n'.format(ctrl_str))
        fh.write('\n')
        fh.write('  input valid_i,  // Data Valid Signal.\n')
        fh.write('  input [{}:0] signal_i, // Energy dectect signal.\n'.format(in_str))
        fh.write('\n')
        fh.write('  output valid_o,\n')
        fh.write('  output [{}:0] signal_o\n'.format(out_str))
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('reg valid_d;\n')
        fh.write('\n')
        fh.write('reg [{}:0] output_reg, next_output_reg;\n'.format(out_str))
        fh.write('\n')
        fh.write('assign signal_o = output_reg;\n')
        fh.write('assign valid_o = valid_d;\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset) begin\n')
        fh.write('        output_reg <= 0;\n')
        fh.write('        valid_d <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        output_reg <= next_output_reg;\n')
        fh.write('        valid_d <= valid_i;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    case (slice_offset_i)\n')
        for ii in range(2**ctrl_bits):
            bit_str = '{0:b}'.format(ii)
            bit_str = str.zfill(bit_str, ctrl_bits)
            if rev_dir is True:
                if ii <= max_offset:
                    lhs = input_width - 1 - ii - diff_bits
                    rhs = lhs - output_width + 1
                else:
                    lhs = input_width - 1 - max_offset
                    rhs = lhs - output_width + 1
            else:
                if ii <= max_offset:
                    lhs = ii + diff_bits + output_width - 1
                    rhs = ii + diff_bits
                else:
                    lhs = max_offset + diff_bits + output_width - 1
                    rhs = max_offset + diff_bits
            fh.write('        ' + str(ctrl_bits) + '\'b' + bit_str +
                     ' : next_output_reg = signal_i[' + str(lhs) + ':' + str(rhs) + '];\n')
        fh.write('\n')
        fh.write('    endcase\n')
        fh.write('\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return (file_name, module_name)


def gen_exp_conv(file_name, project_file, combined_table, corr_fac_fi, input_width=12, shift_bits=4, table_bits=16,
                 device='xc6slx45t', family='spartan6', package='csg324', speed_grade=3):

    assert(file_name is not None), 'User must specify File Name'
    module_name = ret_module_name(file_name)   # file_name[idx:idx + idx2]
    word_length = corr_fac_fi.word_length
    # check number of 1's in binary
    num_ones = 0
    for bit in corr_fac_fi.bin[2:]:
        num_ones += int(bit)

    shift = False
    block_latency = 12
    delay_to_mux = 8
    shift_value = int(np.ceil(np.abs(np.log2(corr_fac_fi.double))))
    if num_ones == 1:
        # constant multiplier reduces to a shift
        block_latency = 10
        shift = True
        word_length = shift_value
        corr_fac_fi = fp_utils.ufi(0, word_length, word_length)
        delay_to_mux = 6

    corr_mult_bits = word_length + (input_width // 2)

    frac_fi = fp_utils.ufi(0, input_width // 2, input_width // 2)
    b_port_fi = fp_utils.mult_fi(frac_fi, corr_fac_fi)
    table_fi = fp_utils.ufi(0, table_bits, table_bits - 1)

    c_port_fi = fp_utils.mult_fi(b_port_fi, table_fi)

    dsp_slice_msb = c_port_fi.fraction_length
    exp_name = ret_file_name(file_name[:-2])
    correction_name = exp_name + '_CorrDSP'
    corr_fac_name = exp_name + '_CorrMult'
    exp_rom_name = exp_name + '_ROM'
    exp_rom_name = exp_name + '_large_table'

    shift_msb = shift_bits - 1

    with open(file_name, 'w') as fh:
        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : Phil Vallance\n')
        fh.write('// File        : %s.v\n' % module_name)
        fh.write('// Description : Module converts an exponential value to '
                 'linear.\n')
        fh.write('//               The module uses a correction multiplier to '
                 'improve accuracy\n')
        fh.write('//\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('\n')
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module %s\n' % module_name)
        fh.write('#(parameter INPUT_WIDTH = %d,\n' % input_width)
        fh.write('  parameter TABLE_BITS=%d)\n' % table_bits)
        fh.write('(\n')
        fh.write('  input sync_reset,\n')
        fh.write('  input clk,\n')
        fh.write('\n')
        fh.write('  input valid_i,\n')
        fh.write('  input [INPUT_WIDTH-1:0] log_i,\n')
        fh.write('\n')
        fh.write('  output valid_o,\n')
        fh.write('  output [TABLE_BITS-1:0] lin_val_o,\n')
        fh.write('  output [%d:0] shift_val_o\n' % shift_msb)
        fh.write('\n')
        fh.write(');\n')
        fh.write('\n')
        sl_width = input_width // 2
        sl_msb = sl_width - 1

        fh.write('parameter UPPER_SL_WIDTH = INPUT_WIDTH/2;\n')
        fh.write('parameter LOWER_SL_WIDTH = INPUT_WIDTH/2;\n')
        fh.write('parameter SLICE_MSB = UPPER_SL_WIDTH + LOWER_SL_WIDTH - 1;\n')
        fh.write('parameter BLOCK_LATENCY = %d;\n' % block_latency)
        fh.write('parameter SHIFT_MSB = TABLE_BITS + %d;\n' % shift_msb)
        fh.write('\n')
        interp_bits = (table_bits + corr_mult_bits)
        fh.write('parameter INTERP_WIDTH = %d;\n' % interp_bits)
        fh.write('\n')
        str1 = (input_width // 2) * '1'
        str0 = (input_width // 2) * '0'
        fh.write('parameter ALL_ONES  = {}\'b{};\n'.format(input_width // 2, str1))
        fh.write('parameter ALL_ZEROS = {}\'b{};\n'.format(input_width // 2, str0))
        fh.write('\n')
        fh.write('wire [%d:0] upper_slice;\n' % sl_msb)
        fh.write('wire [%d:0] lower_slice;\n' % sl_msb)
        fh.write('\n')
        fh.write('reg [%d:0] lower_slice_d [2:0];\n' % sl_msb)
        fh.write('reg [%d:0] upper_slice_d [BLOCK_LATENCY-2:0];\n' % sl_msb)
        fh.write('\n')
        fh.write('reg [TABLE_BITS-1:0] lower_table_d [{}:0];\n'.format(delay_to_mux - 1))
        fh.write('reg [TABLE_BITS-1:0] upper_table_d, upper_table_d2;\n')
        fh.write('\n')
        fh.write('reg [{}:0] upper_shift_d [{}:0];\n'.format(shift_msb, delay_to_mux - 1))
        fh.write('reg [{}:0] lower_shift_d [{}:0];\n'.format(shift_msb, delay_to_mux - 1))

        fh.write('// small table is registered 5 times\n')
        fh.write('// max latency of distributed mem is 2.\n')
        fh.write('\n')
        fh.write('wire [INTERP_WIDTH-1:0] upper_table_pad;\n')
        fh.write('\n')
        fh.write('wire [INTERP_WIDTH:0] dsp_out;\n')
        fh.write('wire [TABLE_BITS-1:0] dsp_out_slice;\n')
        fh.write('\n')
        fh.write('wire [%d:0] corr_value;\n'.format(corr_mult_bits - 1))
        if shift is True:
            fh.write('reg [{}:0] corr_value_d1;\n'.format(corr_mult_bits - 1))
            fh.write('reg [{}:0] corr_value_d2;\n'.format(corr_mult_bits - 1))
        fh.write('\n')
        fh.write('reg [TABLE_BITS-1:0] mux_out, next_mux_out;\n')
        fh.write('reg [%d:0] shift_mux_out, next_shift_mux_out;\n' % shift_msb)
        fh.write('\n')
        fh.write('reg [BLOCK_LATENCY-1:0] valid_d;\n')
        fh.write('\n')
        fh.write('reg mux_sw, next_mux_sw;\n')
        fh.write('\n')
        fh.write('wire [TABLE_BITS+%d:0] upper_table, lower_table;\n' % shift_msb)
        fh.write('\n')
        fh.write('wire [TABLE_BITS-1:0] u_table, l_table;\n')
        fh.write('wire [%d:0] u_shift, l_shift;\n' % shift_msb)
        fh.write('\n')
        fh.write('wire [UPPER_SL_WIDTH:0] addra, addrb;\n')
        fh.write('\n')
        fh.write('assign u_table = upper_table[TABLE_BITS-1:0];\n')
        fh.write('assign l_table = lower_table[TABLE_BITS-1:0];\n')
        fh.write('\n')
        fh.write('assign u_shift = upper_table[SHIFT_MSB:TABLE_BITS];\n')
        fh.write('assign l_shift = lower_table[SHIFT_MSB:TABLE_BITS];\n')
        fh.write('\n')
        str0 = b_port_fi.word_length * '0'
        fh.write('assign upper_table_pad = '
                 '{upper_table_d2,%d\'b%s};\n' % (b_port_fi.word_length, str0))
        fh.write('\n')
        fh.write('assign dsp_out_slice = dsp_out[%d:%d];\n'
                 % (dsp_slice_msb, dsp_slice_msb - table_bits + 1))
        fh.write('\n')
        fh.write('assign valid_o = valid_d[BLOCK_LATENCY-1];\n')
        fh.write('assign lin_val_o = mux_out;\n')
        fh.write('assign shift_val_o = shift_mux_out;\n')
        fh.write('assign upper_slice = log_i[SLICE_MSB:LOWER_SL_WIDTH];\n')
        fh.write('assign lower_slice = log_i[LOWER_SL_WIDTH-1:0];\n')
        fh.write('assign addra = {1\'b1,upper_slice};\n')
        fh.write('assign addrb = {1\'b0,lower_slice};\n')
        str_val = str(shift_value) + '\'b' + shift_value * '0'
        if shift is True:
            fh.write('assign corr_value = {%s, lower_slice_d[2]};\n' % str_val)
        fh.write('\n')
        fh.write('integer ii;\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('\n')
        if (shift is True):
            fh.write('    corr_value_d1 <= corr_value;\n')
            fh.write('    corr_value_d2 <= corr_value_d1;\n')

        fh.write('    lower_table_d[0] <= l_table;\n')
        fh.write('    for (ii = 1; ii < %d; ii = ii + 1) begin\n' % delay_to_mux)
        fh.write('        lower_table_d[ii]  <= lower_table_d[ii-1];\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    lower_slice_d[0] <= lower_slice;\n')
        fh.write('    for (ii = 1; ii < 3; ii = ii + 1) begin\n')
        fh.write('        lower_slice_d[ii]  <= lower_slice_d[ii-1];\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    upper_slice_d[0] <= upper_slice;\n')
        fh.write('    for (ii = 1; ii < BLOCK_LATENCY-1; ii = ii + 1) begin\n')
        fh.write('        upper_slice_d[ii] <= upper_slice_d[ii-1];\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    upper_shift_d[0] <= u_shift;\n')
        fh.write('    for (ii = 1; ii < %d; ii = ii + 1) begin\n' % delay_to_mux)
        fh.write('        upper_shift_d[ii] <= upper_shift_d[ii-1];\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    upper_table_d <= u_table;\n')
        fh.write('    upper_table_d2 <= upper_table_d;\n')
        fh.write('\n')
        fh.write('    lower_shift_d[0] <= l_shift;\n')
        fh.write('    for (ii = 1; ii < %d; ii = ii + 1) begin\n' % delay_to_mux)
        fh.write('        lower_shift_d[ii] <= lower_shift_d[ii-1];\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        valid_d <= 0;\n')
        fh.write('        mux_out <= 0;\n')
        fh.write('        shift_mux_out <= 0;\n')
        fh.write('        mux_sw <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        valid_d <= {valid_d[BLOCK_LATENCY-2:0],valid_i};\n')
        fh.write('        mux_out <= next_mux_out;\n')
        fh.write('        shift_mux_out <= next_shift_mux_out;\n')
        fh.write('        mux_sw <= next_mux_sw;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('//mux Process Latency 1.\n')
        fh.write('always @*\n')
        delay_val = delay_to_mux - 1
        fh.write('begin\n')
        str_val = 'upper_slice_d[BLOCK_LATENCY-2] == ALL_ONES) || (upper_slice_d[BLOCK_LATENCY-2] == ALL_ZEROS'
        fh.write('    if (({})) begin\n'.format(str_val))
        fh.write('        next_mux_sw = 1\'b1;\n')
        fh.write('        next_mux_out = lower_table_d[{}];\n'.format(delay_val))
        fh.write('        next_shift_mux_out = lower_shift_d[%d];\n' % delay_val)
        fh.write('    end else begin\n')
        fh.write('        next_mux_sw = 1\'b0;\n')
        fh.write('        next_mux_out = dsp_out_slice;\n')
        fh.write('        next_shift_mux_out = upper_shift_d[%d];\n' % delay_val)
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// Latency = 3.\n')
        fh.write('%s Table (\n' % exp_rom_name)
        fh.write('  .clka(clk),\n')
        fh.write('  .addra(addra),\n')
        fh.write('  .douta(upper_table),\n')
        fh.write('  .clkb(clk),\n')
        fh.write('  .addrb(addrb),\n')
        fh.write('  .doutb(lower_table)\n')
        fh.write(');\n')
        fh.write('\n')
        if shift is False:
            fh.write('%s CorrMult (\n' % corr_fac_name)
            fh.write('  .clk(clk),\n')
            fh.write('  .a(lower_slice_d[2]),\n')
            fh.write('  .p(corr_value)\n')
            fh.write(');\n')
        fh.write('\n')
        fh.write('//Latency = 6. AGC Corr DSP\n')
        fh.write('%s CorrDSP (\n' % correction_name)
        fh.write('  .clk(clk),\n')
        fh.write('  .a(upper_table_d2),\n')
        if shift is False:
            fh.write('  .b(corr_value),\n')
        else:
            fh.write('  .b(corr_value_d2),\n')
        fh.write('  .c(upper_table_pad),\n')
        fh.write('  .p(dsp_out)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('endmodule\n')
        fh.close()


def gen_log_conv(path, combined_table, altera=False, tuser_width=0, tlast=False, prefix=''):
    # assert(file_name is not None), 'User must specify File Name'

    path = ret_valid_path(path)
    id_val = 0
    if tlast:
        id_val += 1
    if tuser_width:
        id_val += 2

    word_length = combined_table.qvec[0]
    table_width = combined_table.qvec[0] // 2

    input_width = fp_utils.nextpow2(combined_table.len // 2) * 2
    output_width = word_length // 2

    input_msb = input_width - 1
    output_msb = output_width - 1
    addr_bits = input_width // 2
    tuser_msb = tuser_width - 1

    table_msb = word_length - 1
    mult_width = table_width + addr_bits + 1
    interp_width = mult_width + 1

    file_name = '{}log_conv.v'.format(prefix)
    file_name = os.path.join(path, file_name)
    module_name = ret_module_name(file_name)

    rom_prefix = module_name + '_table_'
    sl_width = input_width // 2
    sl_msb = sl_width - 1

    # generate rom
    (rom_file, table_name) = gen_rom(path, combined_table, rom_type='tdp', rom_style='block', prefix=rom_prefix)
    print(rom_file)
    (fifo_file, fifo_name) = gen_axi_fifo(path, tuser_width=tuser_width, tlast=tlast,
                                          almost_full=True, ram_style='distributed', prefix='')
    print(fifo_file)
    if altera:
        dsp_name = altera_madd(path)
    else:
        (_, dsp_name) = gen_dsp48E1(path, name='log_mac', opcode='A*B+C', a_width=output_width, b_width=input_width // 2 + 1, areg=2,
                                    breg=2, mreg=1, preg=1, use_ce=False, use_pcout=False, c_width=interp_width + 1, 
                                    p_msb=interp_width - 1, p_lsb=0)

    with open(file_name, 'w') as fh:
        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : Phil Vallance\n')
        fh.write('// File        : {}.v\n'.format(module_name))
        fh.write('// Description : Module converts an input Magnitude to a log value.  Note that\n')
        fh.write('//               this is a Natural log conversion (better compression of the\n')
        fh.write('//               signal.  The module uses linear interpolation to reduce table\n')
        fh.write('//               size and improve accuracy.\n')
        fh.write('//\n')
        fh.write('\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        if tuser_width:
            fh.write('module {} #(\n'.format(module_name))
            fh.write('   parameter TUSER_WIDTH=8)\n')
        else:
            fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk, // clock\n')
        fh.write('    input sync_reset, // reset\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [{}:0] s_axis_tdata,\n'.format(input_msb))
        if tuser_width:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        # if (type_bits > 0):
        #     fh.write('    input [{}:0] id_i,\n'.format(type_msb))
        #     fh.write('\n')
        #     fh.write('    output [{}:0] id_o,\n'.format(type_msb))
        #     fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [{}:0] m_axis_tdata,\n'.format(output_msb))
        if tuser_width:
            fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        if tlast:
            fh.write('    output m_axis_tlast,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        one_str = addr_bits * '1'
        zero_str = addr_bits * '0'
        tot_latency = 8
        dsp_delay = 4
        if altera:
            tot_latency = 7
            dsp_delay = 3

        fh.write('parameter ALL_ONES  = {}\'b{};\n'.format(addr_bits, one_str))
        fh.write('parameter ALL_ZEROS = {}\'b{};\n'.format(addr_bits, zero_str))
        fh.write('\n')

        fh.write('wire [{}:0] upper_slice;\n'.format(sl_msb))
        fh.write('wire [{}:0] lower_slice;\n'.format(sl_msb))
        fh.write('wire almost_full;\n')
        fh.write('\n')
        fh.write('reg [{}:0] lower_slice_d [2:0];\n'.format(sl_msb))
        fh.write('reg [{}:0] upper_slice_d [{}:0];\n'.format(sl_msb, tot_latency - 2))
        fh.write('\n')
        if tuser_width:
            fh.write('reg [{}:0] tuser_d[0:{}];\n'.format('TUSER_WIDTH-1', tot_latency - 1))
            fh.write('wire [{}:0] fifo_tuser;\n'.format('TUSER_WIDTH-1'))
        if tlast:
            fh.write('reg [{}:0] tlast_d;\n'.format(tot_latency - 1))
            fh.write('wire fifo_tlast;\n')

        # if (type_bits > 0):
        #     str_val = 'id_s0'
        #     for ii in range(1, tot_latency):
        #         str_val += ', id_s{}'
        #     fh.write('reg [{}:0] {};\n'.format(type_msb, str_val))
        fh.write('reg [{}:0] small_table_out_d [{}:0];\n'.format(output_msb, dsp_delay - 1))
        fh.write('\n')
        fh.write('wire [{}:0] upper_table, lower_table;\n'.format(table_msb))
        fh.write('wire [{}:0] interp_out;\n'.format(interp_width - 1))
        fh.write('wire [{}:0] interp_out_slice;\n'.format(output_msb))
        fh.write('wire [{}:0] mag_table, diff_table, mag_small_table;\n'.format(output_msb))
        fh.write('wire [{}:0] large_table_pad;\n'.format(interp_width))
        fh.write('wire fifo_tvalid;\n')
        fh.write('wire [{}:0] fifo_tdata;\n'.format(output_msb))
        fh.write('\n')
        fh.write('reg [{}:0] mux_out, next_mux_out;\n'.format(output_msb))
        fh.write('\n')
        fh.write('reg [{}:0] valid_d;\n'.format(tot_latency - 1))
        fh.write('\n')
        fh.write('assign mag_table = upper_table[{}:{}];\n'.format(table_msb, output_width))
        fh.write('assign diff_table = upper_table[{}:0];\n'.format(output_msb))
        fh.write('assign mag_small_table = lower_table[{}:{}];\n'.format(table_msb, output_width))
        fh.write('assign upper_slice = s_axis_tdata[{}:{}];\n'.format(input_msb, addr_bits))
        fh.write('assign lower_slice = s_axis_tdata[{}:0];\n'.format(addr_bits - 1))
        fh.write('assign s_axis_tready = ~almost_full;\n')
        if tuser_width:
            fh.write('assign fifo_tuser = tuser_d[{}];\n'.format(tot_latency - 1))
        if tlast:
            fh.write('assign fifo_tlast = tlast_d[{}];\n'.format(tot_latency - 1))
        tuple_val = (output_msb, addr_bits)
        fh.write('assign large_table_pad = {{mag_table[{}],mag_table,{}\'d0}};\n'.format(*tuple_val))
        tuple_val = (output_msb + addr_bits, addr_bits)
        fh.write('assign interp_out_slice = interp_out[{}:{}];\n'.format(*tuple_val))

        fh.write('\n')
        fh.write('assign fifo_tvalid = valid_d[{}];\n'.format(tot_latency - 1))
        # if (type_bits > 0):
        #     fh.write('assign id_o = id_s{};\n'.format(tot_latency - 1))
        fh.write('assign fifo_tdata = mux_out;\n')
        fh.write('\n')
        fh.write('integer ii;\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('\n')
        fh.write('	lower_slice_d[0] <= lower_slice;\n')
        fh.write('	for (ii = 1; ii < 3; ii = ii + 1) begin\n')
        fh.write('		lower_slice_d[ii] <= lower_slice_d[ii-1];\n')
        fh.write('	end\n')
        fh.write('\n')
        fh.write('	upper_slice_d[0] <= upper_slice;\n')
        fh.write('	for (ii = 1; ii < {}; ii = ii + 1) begin\n'.format(tot_latency - 1))
        fh.write('		upper_slice_d[ii] <= upper_slice_d[ii-1];\n')
        fh.write('	end\n')
        fh.write('\n')
        fh.write('	small_table_out_d[0] <= mag_small_table;\n')
        fh.write('	for (ii = 1; ii < {}; ii = ii + 1) begin\n'.format(dsp_delay))
        fh.write('		small_table_out_d[ii] <= small_table_out_d[ii-1];\n')
        fh.write('	end\n')
        fh.write('	mux_out <= next_mux_out;\n')
        if tuser_width > 0:
            fh.write('    tuser_d[0] <= s_axis_tuser;\n')
            for jj in range(1, tot_latency):
                fh.write('    tuser_d[{}] <= tuser_d[{}];\n'.format(jj, jj - 1))
            fh.write('\n')
        if tlast:
            fh.write('    tlast_d[0] <= s_axis_tlast;\n')
            for jj in range(1, tot_latency):
                fh.write('    tlast_d[{}] <= tlast_d[{}];\n'.format(jj, jj - 1))
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('	if (sync_reset == 1\'b1) begin\n')
        fh.write('		valid_d  <= 0;\n')
        fh.write('	end else begin\n')
        fh.write('		valid_d <= {{valid_d[{}:0], s_axis_tvalid & ~almost_full}};\n'.format(tot_latency - 2))
        fh.write('	end\n')
        fh.write('end\n')
        fh.write('\n')
        # if (type_bits > 0):
        #     fh.write('always @(posedge clk)\n')
        #     fh.write('begin\n')
        #     fh.write('  id_s0 <= id_i;\n')
        #     for ii in range(tot_latency - 1):
        #         fh.write('  id_s{} <= id_s{};\n'.format(ii - 1, ii))
        #     fh.write('end\n')
        #     fh.write('\n')
        fh.write('//mux Process Latency 1.\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        t_val = (tot_latency - 2, tot_latency - 2)
        fh.write('	if ((upper_slice_d[{}] == ALL_ONES) || (upper_slice_d[{}] == ALL_ZEROS)) begin\n'.format(*t_val))
        fh.write('		next_mux_out = small_table_out_d[{}];\n'.format(dsp_delay - 1))
        fh.write('	end else begin\n')
        fh.write('		next_mux_out = interp_out_slice;\n')
        fh.write('	end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('// Latency = 3.\n')
        fh.write('{} log_table (\n'.format(table_name))
        fh.write('  .clk(clk), // input clka\n')
        fh.write('  .addra({1\'b1,upper_slice}), \n')
        fh.write('  .addrb({1\'b0,lower_slice}),\n')
        fh.write('  .doa(upper_table),\n')
        fh.write('  .dob(lower_table)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        if altera:
            d_str = '1' + zero_str
            fh.write('//Latency = 3.\n')
            fh.write('{} # (\n'.format(dsp_name))
            fh.write(' .A_WIDTH({}),\n'.format(table_width))
            fh.write(' .B_WIDTH({}),\n'.format(sl_width + 1))
            fh.write(' .MULT_WIDTH({}),\n'.format(mult_width))
            fh.write(' .OUT_WIDTH({}))\n'.format(interp_width))
            fh.write('interp_dsp\n')
            fh.write('(\n')
            fh.write('    .clock(clk),\n')
            fh.write('    .aclr(sync_reset),\n')
            fh.write('    .dataa(diff_table),\n')
            fh.write('    .datab({1\'b0,lower_slice_d[2]}),\n')
            fh.write('    .datac(mag_table),\n')
            fh.write('    .datad({}\'b{}),\n'.format(sl_width + 1, d_str))
            fh.write('    .result(interp_out)\n')
            fh.write(');\n')
        else:
            fh.write('//Latency = 4.\n')
            fh.write('{} interp_dsp (\n'.format(dsp_name))
            fh.write('  .clk(clk),\n')
            fh.write('  .a(diff_table),\n')
            fh.write('  .b({1\'b0,lower_slice_d[2]}),\n')
            fh.write('  .c(large_table_pad),\n')
            fh.write('  .p(interp_out)\n')
            fh.write(');\n')

        fh.write('\n')
        axi_fifo_inst(fh, fifo_name, inst_name='axi_fifo', data_width=output_width, af_thresh=8,
                      addr_width=4, tuser_width=tuser_width, tlast=tlast, s_tvalid_str='fifo_tvalid',
                      s_tdata_str='fifo_tdata', s_tuser_str='fifo_tuser', s_tlast_str='fifo_tlast',
                      s_tready_str='', almost_full_str='almost_full', m_tvalid_str='m_axis_tvalid', m_tdata_str='m_axis_tdata',
                      m_tuser_str='m_axis_tuser', m_tlast_str='m_axis_tlast', m_tready_str='m_axis_tready')

        fh.write('\n')
        fh.write('endmodule\n')


    return (file_name, rom_file, dsp_name)
        # if c_str is not None:
        #     c_str.write('##################################################\n')
        #     c_str.write('{} Cores\n'.format(module_name))
        #     c_str.write('##################################################\n')
        #     c_str.write('############################\n')
        #     c_str.write('Dual Port ROM \n')
        #     c_str.write('Latency = 3\n')
        #     c_str.write('Block Name = %s\n' % table_name)
        #     c_str.write('Addr Width = %d\n' % (sl_width + 1))
        #     c_str.write('Output Width = %d\n' % word_length)
        #     c_str.write('############################\n')
        #     c_str.write('DSP 48 - (A * B) + C \n')
        #     c_str.write('Block Name = %s\n' % dsp_name)
        #     c_str.write('Latency = 4\n')
        #     c_str.write('A Width = %d\n' % output_width)
        #     c_str.write('B Width = %d\n' % (sl_width + 1))
        #     c_str.write('C Width = %d\n' % (interp_width + 1))
        #     c_str.write('P Width = %d\n' % (interp_width + 2))
        #     c_str.write('############################\n')

        # create .coe file for large and small tables.
        # x_utils.coe_write(combined_table, radix=16, file_name=table_coe)
        # x_utils.coe_write(small_table, radix=16, file_name=small_table_coe)

# xilinx has built in FIFO logic -- using the core will result in better performance than inference.
def gen_axi_fifo(path, tuser_width=0, tlast=False, almost_full=False, almost_empty=False, count=False,
                 max_delay=0, ram_style='block', prefix=''):

    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)

    id_val = 0
    if tlast:
        id_val += 1
    if almost_full:
        id_val += 2
    if almost_empty:
        id_val += 4
    if count:
        id_val += 8
    if ram_style == 'distributed':
        id_val += 16
    if tuser_width:
        id_val += 32

    if max_delay:
        id_val += 64

    # width_msb = width - 1
    file_name = path + '{}axi_fifo_{}.v'.format(prefix, id_val)
    low_logic = almost_empty

    delay_msb = None
    delay_bits = None
    if max_delay > 0:
        delay_bits = ret_num_bitsU(max_delay)
        delay_msb = delay_bits - 1

    out_cnt = count or (almost_full) or (almost_empty)
    module_name = ret_module_name(file_name)
    with open(file_name, "w") as fh:
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : PJV\n')
        fh.write('// File        : {}\n'.format(module_name))
        fh.write('// Description : Generates FIFO with AXI interface. \n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//                Latency = 3.\n')
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('#( parameter DATA_WIDTH=32,\n')
        if almost_full:
            fh.write('   parameter ALMOST_FULL_THRESH=16,\n')
        if almost_empty:
            fh.write('   parameter ALMOST_EMPTY_THRESH=8,\n')
        if tuser_width:
            fh.write('   parameter TUSER_WIDTH=8,\n')
        fh.write('   parameter ADDR_WIDTH=8)\n')
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('    \n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [DATA_WIDTH-1:0] s_axis_tdata,\n')
        fh.write('    output s_axis_tready,\n')
        if tlast is True:
            fh.write('    input s_axis_tlast,\n')
        if tuser_width > 0:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')

        if max_delay > 0:
            fh.write('    input [{}:0] delay,\n'.format(delay_msb))
        fh.write('\n')
        if almost_full:
            fh.write('    output almost_full,\n')
        if almost_empty:
            fh.write('    output almost_empty,\n')
        if count:
            fh.write('    output [ADDR_WIDTH-1:0] data_cnt,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [DATA_WIDTH-1:0] m_axis_tdata,\n')

        if tlast is True:
            fh.write('    output m_axis_tlast,\n')
        if tuser_width > 0:
            fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('localparam ADDR_P1 = ADDR_WIDTH + 1;\n')
        if tuser_width > 0:
            if tlast is False:
                fh.write('localparam FIFO_WIDTH = DATA_WIDTH + TUSER_WIDTH;\n')
            else:
                fh.write('localparam FIFO_WIDTH = DATA_WIDTH + TUSER_WIDTH + 1;\n')
        else:
            if tlast:
                fh.write('localparam FIFO_WIDTH = DATA_WIDTH + 1;\n')
            else:
                fh.write('localparam FIFO_WIDTH = DATA_WIDTH;\n')

        fh.write('localparam FIFO_MSB = FIFO_WIDTH - 1;\n')
        fh.write('localparam ADDR_MSB = ADDR_WIDTH - 1;\n')
        fh.write('localparam DEPTH = 2 ** ADDR_WIDTH;\n')
        if almost_full:
            fh.write('localparam [ADDR_WIDTH:0] high_thresh = ALMOST_FULL_THRESH;\n')

        if low_logic:
            fh.write('localparam [ADDR_WIDTH:0] low_thresh = ALMOST_EMPTY_THRESH;\n')

        fh.write('\n')
        if out_cnt:
            fh.write('reg [ADDR_WIDTH:0] data_cnt_s = {{ADDR_P1{{1\'b0}}}};\n')

        if almost_full:
            fh.write('reg [ADDR_P1:0] high_compare;\n')

        if low_logic:
            fh.write('reg [ADDR_WIDTH+1:0] low_compare;\n')

        fh.write('reg [ADDR_WIDTH:0] wr_ptr = 0, next_wr_ptr;\n')
        fh.write('reg [ADDR_WIDTH:0] wr_addr = 0, next_wr_addr;\n')
        fh.write('reg [ADDR_WIDTH:0] rd_ptr = 0, next_rd_ptr;\n')
        fh.write('\n')
        # need attribute here.
        # (* ram_style = "distributed" *),
        fh.write('(* ram_style = "{}" *) reg [FIFO_MSB:0] buffer [DEPTH-1:0];\n'.format(ram_style))
        fh.write('wire [FIFO_MSB:0] wr_data;\n')
        fh.write('\n')
        if max_delay > 0:
            fh.write('reg [{}:0] delay_d1, next_delay_d1;\n'.format(delay_bits - 1))
            fh.write('wire add_delay;\n')
            fh.write('wire [ADDR_WIDTH:0] delay_s;\n')
        fh.write('// full when first MSB different but rest same\n')
        # tup_val = (addr_width, addr_width, addr_msb, addr_msb)
        fh.write('wire full;\n')
        fh.write('// empty when pointers match exactly\n')
        fh.write('wire empty;\n')
        fh.write('\n')
        fh.write('// control signals\n')
        fh.write('reg wr;\n')
        fh.write('reg rd;\n')
        fh.write('reg [1:0] occ_reg = 2\'b00, next_occ_reg;\n')
        fh.write('reg [FIFO_MSB:0] data_d0, data_d1, next_data_d0, next_data_d1;\n')
        fh.write('\n')
        fh.write('// control signals\n')
        if max_delay > 0:
            fh.write('assign full = ((wr_addr[ADDR_WIDTH] != rd_ptr[ADDR_WIDTH]) && (wr_addr[ADDR_MSB:0] == rd_ptr[ADDR_MSB:0]));\n')
        else:
            fh.write('assign full = ((wr_ptr[ADDR_WIDTH] != rd_ptr[ADDR_WIDTH]) && (wr_ptr[ADDR_MSB:0] == rd_ptr[ADDR_MSB:0]));\n')
        fh.write('assign s_axis_tready = ~full;\n')
        fh.write('assign m_axis_tvalid = occ_reg[1];\n')
        fh.write('assign empty = (wr_ptr == rd_ptr) ? 1\'b1 : 1\'b0;\n')
        fh.write('\n')

        if tuser_width == 0:
            if tlast is False:
                fh.write('assign wr_data = s_axis_tdata;\n')
                fh.write('assign m_axis_tdata = data_d1;\n')
            else:
                fh.write('assign wr_data = {s_axis_tlast, s_axis_tdata};\n')
                fh.write('assign m_axis_tdata = data_d1[DATA_WIDTH-1:0];\n')
                fh.write('assign m_axis_tlast = data_d1[FIFO_MSB];\n')
        else:
            if tlast is False:
                fh.write('assign wr_data = {s_axis_tuser, s_axis_tdata};\n')
                fh.write('assign m_axis_tdata = data_d1[DATA_WIDTH-1:0];\n')
                fh.write('assign m_axis_tuser = data_d1[FIFO_MSB:DATA_WIDTH];\n')
            else:
                fh.write('assign wr_data = {s_axis_tlast, s_axis_tuser, s_axis_tdata};\n')
                fh.write('assign m_axis_tdata = data_d1[DATA_WIDTH-1:0];\n')
                fh.write('assign m_axis_tuser = data_d1[FIFO_MSB-1:DATA_WIDTH];\n')
                fh.write('assign m_axis_tlast = data_d1[FIFO_MSB];\n')
        # fh.write('assign {m_axis_tlast, m_axis_tuser, m_axis_tdata} = output_data;\n')
        if almost_full:
            fh.write('assign almost_full = high_compare[ADDR_WIDTH];\n')
        if low_logic:
            fh.write('assign almost_empty = low_compare[ADDR_WIDTH];\n')

        if count:
            fh.write('assign data_cnt = data_cnt_s;\n')

        if max_delay > 0:
            fh.write('assign add_delay = (delay != delay_d1) ? 1\'b1 : 1\'b0;\n')
            fh.write('assign delay_s = {1\'b0, delay};\n')

        fh.write('\n')

        # initialize ram using initial statement and for loop.
        fh.write('integer i;\n')
        fh.write('initial begin\n')
        fh.write('    for (i = 0; i < DEPTH; i=i+1) begin\n')
        fh.write('        buffer[i] = 0;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// Write logic\n')
        fh.write('always @* begin\n')
        fh.write('    wr = 1\'b0;\n')
        fh.write('    next_wr_ptr = wr_ptr;\n')
        fh.write('    next_wr_addr = wr_addr;\n')
        if max_delay > 0:
            fh.write('    next_delay_d1 = delay_d1;\n')
        fh.write('\n')
        fh.write('    if (s_axis_tvalid) begin\n')
        fh.write('        // input data valid\n')
        fh.write('        if (~full) begin\n')
        fh.write('            // not full, perform write\n')
        fh.write('            wr = 1\'b1;\n')
        fh.write('            next_wr_ptr = wr_ptr + 1;\n')
        if max_delay == 0:
            fh.write('            next_wr_addr = wr_addr + 1;\n')
        else:
            fh.write('            if (add_delay == 1\'b1) begin\n')
            fh.write('                next_wr_addr = wr_ptr + delay_s + 1;\n'.format(delay_bits - 1))
            fh.write('                next_delay_d1 = delay;\n')
            fh.write('            end else begin\n')
            fh.write('                next_wr_addr = wr_addr + 1;\n')
            fh.write('            end\n')

        fh.write('        end\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')

        if out_cnt:
            fh.write('// Data Cnt Logic\n')
            fh.write('always @(posedge clk) begin\n')
            fh.write('    data_cnt_s <= next_wr_ptr - next_rd_ptr + occ_reg[0];\n')
            if almost_full:
                fh.write('    high_compare <= high_thresh - data_cnt_s;\n')
            if low_logic:
                fh.write('    low_compare <= data_cnt_s - low_thresh;\n')
            fh.write('end\n\n')

        fh.write('always @(posedge clk) begin\n')
        fh.write('    if (sync_reset) begin\n')
        fh.write('        wr_ptr <= 0;\n')
        if max_delay:
            fh.write('        wr_addr <= delay_s;\n')
        else:
            fh.write('        wr_addr <= 0;\n')
        fh.write('        occ_reg <= 0;\n')
        fh.write('        data_d0 <= 0;\n')
        fh.write('        data_d1 <= 0;\n')
        if max_delay > 0:
            fh.write('        delay_d1 <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        wr_ptr <= next_wr_ptr;\n')
        fh.write('        wr_addr <= next_wr_addr;\n')
        fh.write('        occ_reg <= next_occ_reg;\n')
        fh.write('        data_d0 <= next_data_d0;\n')
        fh.write('        data_d1 <= next_data_d1;\n')
        if max_delay > 0:
            fh.write('        delay_d1 <= next_delay_d1;\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    if (wr) begin\n')
        fh.write('        buffer[wr_addr[ADDR_MSB:0]] <= wr_data;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// Read logic\n')
        fh.write('always @* begin\n')
        fh.write('    rd = 1\'b0;\n')
        fh.write('    next_rd_ptr = rd_ptr;\n')
        fh.write('    next_occ_reg[0] = occ_reg[0];\n')
        fh.write('    next_occ_reg[1] = occ_reg[1];\n')
        fh.write('    next_data_d0 = data_d0;\n')
        fh.write('    next_data_d1 = data_d1;\n')
        fh.write('    if (occ_reg != 2\'b11 | m_axis_tready == 1\'b1) begin\n')
        fh.write('        // output data not valid OR currently being transferred\n')
        fh.write('        if (~empty) begin\n')
        fh.write('            // not empty, perform read\n')
        fh.write('            rd = 1\'b1;\n')
        fh.write('            next_rd_ptr = rd_ptr + 1;\n')
        fh.write('        end\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    if (rd) begin\n')
        fh.write('        next_occ_reg[0] = 1\'b1;\n')
        fh.write('    end else if (m_axis_tready == 1\'b1 || occ_reg[1] == 1\'b0) begin\n')
        fh.write('        next_occ_reg[0] = 1\'b0;\n')
        fh.write('    end\n')
        fh.write('    if (m_axis_tready == 1\'b1 || occ_reg[1] == 1\'b0) begin\n')
        fh.write('        next_occ_reg[1] = occ_reg[0];\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    if (rd) begin\n')
        fh.write('        next_data_d0 = buffer[rd_ptr[ADDR_MSB:0]];\n')
        fh.write('    end\n')
        fh.write('    if (m_axis_tready | ~occ_reg[1]) begin\n')
        fh.write('        next_data_d1 = data_d0;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk) begin\n')
        fh.write('    if (sync_reset) begin\n')
        fh.write('        rd_ptr <= 0;\n')
        fh.write('    end else begin\n')
        fh.write('        rd_ptr <= next_rd_ptr;\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return (file_name, module_name)

def gen_rom(path, fi_obj, rom_type='sp', rom_style='block', prefix='', write_access=False):
    """
        Generates single, dual, and true dual port rams.

    """
    path = ret_valid_path(path)
    depth = fi_obj.len
    width = fi_obj.qvec[0]
    bin_vec = fi_obj.bin
    addr_bits = int(np.ceil(np.log2(depth)))
    rom_depth = 2 ** addr_bits
    addr_msb = addr_bits - 1
    data_msb = width - 1

    def gen_port(fh, port='a'):
        if write_access is False:
            fh.write('// port {}\n'.format(port))
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            # old data is presented on the output port
            fh.write('    addr{}_d <= addr{};\n'.format(port, port))
            fh.write('    rom_pipe{} <= rom[addr{}_d];\n'.format(port, port))
            fh.write('    do{}_d <= rom_pipe{};\n'.format(port, port))
            fh.write('end\n')
        else:
            fh.write('// port {}\n'.format(port))
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            # old data is presented on the output port
            mem_interfaces(fh, rom_style, port)
        # New data is made available immediately on the output port.

    file_name = '{}{}_rom.v'.format(prefix, rom_type)
    # if write_access is False:
    # else:
    #     file_name = '{}{}_ram.v'.format(prefix, rom_type)

    file_name = os.path.join(path, file_name)
    module_name = ret_module_name(file_name)
    with open(file_name, 'w') as fh:
        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : Phil Vallance\n')
        fh.write('// File        : {}.v\n'.format(module_name))
        fh.write('// Description : Implements a single port RAM with block ram. The ram is a fully\n')
        fh.write('//               pipelined implementation -- 3 clock cycles from new read address\n')
        fh.write('//               to new data                                                     \n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        if rom_type == 'sp':
            fh.write('  input clk, \n')
            fh.write('\n')
            fh.write('  input [{}:0] addra,\n'.format(addr_msb))
            fh.write('  output [{}:0] doa\n'.format(data_msb))
            if write_access:
                fh.write('  input wea,\n')

        elif rom_type == 'dp':
            fh.write('  input clk, \n')
            if write_access:
                fh.write('  input wea,\n')
                fh.write('  input [{}:0] dia,\n'.format(data_msb))
                fh.write('  input [{}:0] addra,\n'.format(addr_msb))
            fh.write('  input [{}:0] addrb,\n'.format(addr_msb))
            fh.write('  output [{}:0] dob\n'.format(data_msb))
        elif rom_type == 'tdp':
            fh.write('  input clk, \n')
            fh.write('\n')
            if write_access:
                fh.write('  input wea,\n')
                fh.write('  input web,\n')
                fh.write('  input [{}:0] dia,\n'.format(data_msb))
                fh.write('  input [{}:0] dib,\n'.format(data_msb))
            fh.write('  input [{}:0] addra,\n'.format(addr_msb))
            fh.write('  input [{}:0] addrb,\n'.format(addr_msb))
            fh.write('  output [{}:0] doa,\n'.format(data_msb))
            fh.write('  output [{}:0] dob\n'.format(data_msb))
        fh.write(');\n')
        fh.write('\n')
        fh.write('(* rom_style = \"{}\" *) reg [{}:0] rom [{}:0];\n'.format(rom_style, data_msb, rom_depth - 1))
        if rom_type == 'sp':
            fh.write('reg [{}:0] addra_d;\n'.format(addr_msb))
            fh.write('reg [{}:0] doa_d;\n'.format(data_msb))
            fh.write('reg [{}:0] rom_pipea;\n'.format(data_msb))
            if write_access:
                fh.write('reg wea_d;\n')
                fh.write('reg [{}:0] dia_d;\n'.format(data_msb))

        if rom_type == 'dp':
            # fh.write('(* ram_style = \"{}\" *) reg [{}:0] ramb [{}:0];\n'.format(ram_style, data_msb, depth - 1))
            fh.write('reg [{}:0] addrb_d;\n'.format(addr_msb))
            fh.write('reg [{}:0] dob_d;\n'.format(data_msb))
            fh.write('reg [{}:0] rom_pipea;\n'.format(data_msb))
            if write_access:
                fh.write('reg [{}:0] addra_d;\n'.format(addr_msb))
                fh.write('reg [{}:0] dia_d;\n'.format(data_msb))
                fh.write('reg wea_d;\n')

        if rom_type == 'tdp':
            # fh.write('(* ram_style = \"{}\" *) reg [{}:0] ramb [{}:0];\n'.format(ram_style, data_msb, depth - 1))
            fh.write('reg [{}:0] addra_d;\n'.format(addr_msb))
            fh.write('reg [{}:0] addrb_d;\n'.format(addr_msb))
            fh.write('reg [{}:0] doa_d, dob_d;\n'.format(data_msb))
            fh.write('reg [{}:0] rom_pipea, rom_pipeb;\n'.format(data_msb))
            if write_access:
                fh.write('reg wea_d, web_d;\n')
                fh.write('reg [{}:0] dia_d, dib_d;\n'.format(data_msb))

        fh.write('\n')
        if rom_type == 'sp' or rom_type == 'tdp':
            fh.write('assign doa = doa_d;\n')

        if rom_type == 'dp' or rom_type == 'tdp':
            fh.write('assign dob = dob_d;\n')
            
        fh.write('\n')
        fh.write('initial\n')
        fh.write('begin\n')
        for i in range(rom_depth):
            if i < depth:
                fh.write('    rom[{}] = {}\'b{};\n'.format(i, width, bin_vec[i]))
            else:
                fh.write('    rom[{}] = {}\'b{};\n'.format(i, width, '0' * width))
                # fh.write('    $readmemb("{}", rom);\n'.format(rom_file))
        fh.write('end\n\n')

        if rom_type == 'sp':
            gen_port(fh, 'a')
            fh.write('\n')

        if rom_type == 'dp':
            fh.write('// port a\n')
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            if write_access:
                fh.write('    if (wea_d == 1\'b1) begin\n')
                fh.write('      rom[addra_d] <= dia_d;\n')
                fh.write('    end\n')
                fh.write('    wea_d <= wea;\n')
                fh.write('    dia_d <= dia;\n')
            fh.write('    addra_d <= addra;\n')
            fh.write('end\n\n')
            fh.write('// port b\n')
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            fh.write('    addrb_d <= addrb;\n')
            fh.write('    rom_pipea <= rom[addrb_d];\n')
            fh.write('    dob_d <= rom_pipea;\n')
            fh.write('end\n')
            fh.write('\n')

        if rom_type == 'tdp':
            gen_port(fh, 'a')
            gen_port(fh, 'b')
            fh.write('\n')

        fh.write('endmodule\n')

    return (file_name, module_name)


def mem_interfaces(fh, memory_type, port='a'):
    if memory_type == 'read_first':
        fh.write('    if (we{}_d == 1\'b1) begin\n'.format(port))
        fh.write('        ram[addr{}_d] <= di{}_d;\n'.format(port, port))
        fh.write('    end\n')
        fh.write('    di{}_d <= di{};\n'.format(port, port))
        fh.write('    addr{}_d <= addr{};\n'.format(port, port))
        fh.write('    we{}_d <= we{};\n'.format(port, port))
        fh.write('    ram_pipe{} <= ram[addr{}_d];\n'.format(port, port))
        fh.write('    do{}_d <= ram_pipe{};\n'.format(port, port))
        fh.write('end\n\n')

    # New data is made available immediately on the output port.
    if memory_type == 'write_first':
        fh.write('    if (we{}_d == 1\'b1) begin\n'.format(port))
        fh.write('        ram[addr{}_d] <= di{}_d;\n'.format(port, port))
        fh.write('        ram_pipe{} <= di{}_d;\n'.format(port, port))
        fh.write('    end else begin\n')
        fh.write('        ram_pipe{} <= ram[addr{}_d];\n'.format(port, port))
        fh.write('    end\n')
        fh.write('    di{}_d <= di{};\n'.format(port, port))
        fh.write('    addr{}_d <= addr{};\n'.format(port, port))
        fh.write('    we{}_d <= we{};\n'.format(port, port))
        fh.write('    do{}_d <= ram_pipe{};\n'.format(port, port))
        fh.write('end\n\n')

    # the output port is not changed during a write.
    if memory_type == 'no_change':
        fh.write('    if (we{}_d == 1\'b1) begin\n'.format(port))
        fh.write('        ram[addr{}_d] <= di{}_d;\n'.format(port, port))
        fh.write('    end else begin\n')
        fh.write('        ram_pipe{} <= ram[addr{}_d];\n'.format(port, port))
        fh.write('    end\n')
        fh.write('    di{}_d <= di{};\n'.format(port, port))
        fh.write('    addr{}_d <= addr{};\n'.format(port, port))
        fh.write('    we{}_d <= we{};\n'.format(port, port))
        fh.write('    do{}_d <= ram_pipe{};\n'.format(port, port))
        fh.write('end\n\n')


def gen_ram(path, ram_type='sp', memory_type='write_first', ram_style='block'):
    """
        Generates single, dual, and true dual port rams.
        Valid RAM styles : block, distributed, pipe_distributed.
    """
    # addr_bits = int(np.ceil(np.log2(depth)))
    # addr_msb = addr_bits - 1
    # data_msb = width - 1
    path = ret_valid_path(path)
    def gen_port(fh, port='a', memory_type='write_first'):
        fh.write('// port {}\n'.format(port))
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        # old data is presented on the output port
        mem_interfaces(fh, memory_type, port)

    file_name = '{}_{}_{}_ram.v'.format(ram_type, ram_style, memory_type)
    file_name = os.path.join(path, file_name)
    module_name = ret_module_name(file_name)
    with open(file_name, 'w') as fh:
        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : Phil Vallance\n')
        fh.write('// File        : {}.v\n'.format(module_name))
        fh.write('// Description : Implements a single port RAM with block ram. The ram is a fully\n')
        fh.write('//               pipelined implementation -- 3 clock cycles from new read address\n')
        fh.write('//               to new data                                                     \n')
        fh.write('//\n')
        print_header(fh)
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('#(parameter DATA_WIDTH=32,\n')
        fh.write('  parameter ADDR_WIDTH=8)\n')
        fh.write('(\n')
        if ram_type == 'sp':
            fh.write('  input clk, \n')
            fh.write('\n')
            fh.write('  input wea,\n')
            fh.write('  input [ADDR_WIDTH-1:0] addr,\n')
            fh.write('  input [DATA_WIDTH-1:0] di,\n')
            fh.write('  output [DATA_WIDTH-1:0] do\n')
        elif ram_type == 'dp':
            fh.write('  input clk, \n')
            fh.write('\n')
            fh.write('  input wea,\n')
            fh.write('  input [ADDR_WIDTH-1:0] addra,\n')
            fh.write('  input [ADDR_WIDTH-1:0] addrb,\n')
            fh.write('  input [DATA_WIDTH-1:0] dia,\n')
            fh.write('  output [DATA_WIDTH-1:0] dob\n')

        elif ram_type == 'tdp':
            fh.write('  input clk, \n')
            fh.write('\n')
            fh.write('  input wea,\n')
            fh.write('  input web,\n')
            fh.write('  input [ADDR_WIDTH-1:0] addra,\n')
            fh.write('  input [ADDR_WIDTH-1:0] addrb,\n')
            fh.write('  input [ADDR_WIDTH-1:0] dia,\n')
            fh.write('  input [DATA_WIDTH-1:0] dib,\n')
            fh.write('  output [DATA_WIDTH-1:0] doa,\n')
            fh.write('  output [DATA_WIDTH-1:0] dob\n')
        fh.write(');\n')
        fh.write('\n')

        fh.write('localparam ADDR_P1 = ADDR_WIDTH + 1;\n')
        fh.write('localparam DATA_MSB = DATA_WIDTH - 1;\n')
        fh.write('localparam ADDR_MSB = ADDR_WIDTH - 1;\n')
        fh.write('localparam DEPTH = 2 ** ADDR_WIDTH;\n\n')
        fh.write('(* ram_style = \"{}\" *) reg [DATA_MSB:0] ram [DEPTH-1:0];\n\n'.format(ram_style))

        if ram_type == 'sp':
            fh.write('reg [ADDR_MSB:0] addra_d;\n')
            fh.write('reg wea_d;\n')
            fh.write('reg [DATA_MSB:0] dia_d;\n')
            fh.write('reg [DATA_MSB:0] doa_d;\n')
            fh.write('reg [DATA_MSB:0] ram_pipea;\n')

        if ram_type == 'dp':
            fh.write('reg [ADDR_MSB:0] addra_d;\n')
            fh.write('reg [ADDR_MSB:0] addrb_d;\n')
            fh.write('reg wea_d;\n')
            fh.write('reg [DATA_MSB:0] dia_d;\n')
            fh.write('reg [DATA_MSB:0] dob_d;\n')
            fh.write('reg [DATA_MSB:0] ram_pipe;\n')

        if ram_type == 'tdp':
            # fh.write('(* ram_style = \"{}\" *) reg [DATA_MSB:0] ramb [DEPTH-1:0];\n'.format(ram_style))
            fh.write('reg wea_d;\n')
            fh.write('reg web_d;\n')
            fh.write('reg [ADDR_MSB:0] addra_d;\n')
            fh.write('reg [ADDR_MSB:0] addrb_d;\n')
            fh.write('reg [DATA_MSB:0] dia_d, dib_d;\n')
            fh.write('reg [DATA_MSB:0] doa_d, dob_d;\n')
            fh.write('reg [DATA_MSB:0] ram_pipea, ram_pipeb;\n')
            fh.write('reg wea_d, web_d;\n')

        if ram_type == 'sp':
            fh.write('assign do = doa_d;\n')

        if ram_type == 'dp':
            fh.write('assign dob = dob_d;\n')

        if ram_type == 'tdp':
            fh.write('assign doa = doa_d;\n')
            fh.write('assign dob = dob_d;\n')

        fh.write('\n')
        # initialize ram using initial statement and for loop.
        fh.write('integer i;\n')
        fh.write('initial begin\n')
        fh.write('    for (i = 0; i < DEPTH; i=i+1) begin\n')
        fh.write('        ram[i] = 0;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')

        if ram_type == 'sp':
            gen_port(fh, 'a', memory_type=memory_type)

        if ram_type == 'dp':
            fh.write('// port a\n')
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            fh.write('    if (wea_d == 1\'b1) begin\n')
            fh.write('      ram[addra_d] <= dia_d;\n')
            fh.write('    end\n')
            fh.write('    dia_d <= dia;\n')
            fh.write('    addra_d <= addra;\n')
            fh.write('    wea_d <= wea;\n')
            fh.write('end\n\n')
            fh.write('// port b\n')
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            fh.write('    addrb_d <= addrb;\n')
            fh.write('    ram_pipe <= ram[addrb_d];\n')
            fh.write('    dob_d <= ram_pipe;\n')
            fh.write('end\n')

        if ram_type == 'tdp':
            gen_port(fh, 'a', memory_type=memory_type)
            gen_port(fh, 'b', memory_type=memory_type)

        fh.write('endmodule\n')
        return module_name


def gen_axi_downsample(path, tlast=False, tuser_width=0):

    path = ret_valid_path(path)
    hash = 0
    if tlast:
        hash += 1
    if tuser_width > 0:
        hash += 2

    mod_name = 'axi_downsample_{}'.format(hash)
    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)

    tuser_msb = tuser_width - 1
    with open(file_name, 'w') as fh:

        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : Phil Vallance\n')
        fh.write('// File        : downsample.v\n')
        fh.write('// Description : Module used for variable decimation of a sample stream.\n')
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module downsample\n')
        fh.write('#(  parameter DATA_WIDTH = 16,\n')
        if tuser_width > 0:
            fh.write('    parameter TUSER_WIDTH = 1,\n')
        fh.write('    parameter CNT_BITS = 6)\n')
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('    input [CNT_BITS-1:0] rate,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        if tlast:
            fh.write('    input s_axis_tlast,\n')
        if tuser_width > 0:
            fh.write('    input [TUSER_WIDTH-1:0] s_axis_tuser,\n')
        fh.write('    input [DATA_WIDTH-1:0] s_axis_tdata,\n')
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        if tlast:
            fh.write('    output m_axis_tlast,\n')
        if tuser_width > 0:
            fh.write('    output [TUSER_WIDTH-1:0] m_axis_tuser,\n')
        fh.write('    output [DATA_WIDTH-1:0] m_axis_tdata,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('reg [CNT_BITS-1:0] cnt, next_cnt;\n')
        fh.write('reg [DATA_WIDTH-1:0] signal_out, next_signal_out;\n')
        fh.write('wire rdyfordata;\n')
        if tlast:
            fh.write('reg tlast_out, next_tlast_out;\n')
        if tuser_width > 0:
            fh.write('reg [TUSER_WIDTH-1:0] tuser_out, next_tuser_out;\n')
        fh.write('\n')
        fh.write('reg valid_s, next_valid_s;\n')
        fh.write('\n')
        fh.write('assign m_axis_tvalid = valid_s;\n')
        fh.write('assign m_axis_tdata = signal_out;\n')
        fh.write('assign s_axis_tready = rdyfordata;\n')
        if tlast:
            fh.write('assign m_axis_tlast = tlast_out;\n')
        if tuser_width > 0:
            fh.write('assign m_axis_tuser = tuser_out;\n')

        fh.write('assign rdyfordata = (m_axis_tready | ~valid_s) ? 1\'b1 : 1\'b0;\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        valid_s <= 1\'b0;\n')
        fh.write('        signal_out <= 0;\n')
        if tlast:
            fh.write('        tlast_out <= 1\'b0;\n')
        if tuser_width > 0:
            fh.write('        tuser_out <= 0;\n')

        fh.write('        cnt     <= 0;\n')
        fh.write('    end else begin\n')
        if tlast:
            fh.write('        tlast_out <= next_tlast_out;\n')
        if tuser_width > 0:
            fh.write('        tuser_out <= next_tuser_out;\n')
        fh.write('        valid_s <= next_valid_s;\n')
        fh.write('        signal_out <= next_signal_out;\n')
        fh.write('        cnt     <= next_cnt;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('//Edge Processes -- Sclk and SS\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_valid_s = 1\'b0;\n')
        fh.write('    next_signal_out = signal_out;\n')
        fh.write('    next_cnt = cnt;\n')
        if tlast:
            fh.write('    next_tlast_out = tlast_out;\n')
        if tuser_width > 0:
            fh.write('    next_tuser_out = tuser_out;\n')


        fh.write('    if (s_axis_tvalid == 1\'b1 && rdyfordata == 1\'b1) begin\n')
        fh.write('        if (cnt == 0) begin\n')
        fh.write('            next_valid_s = 1\'b1;\n')
        fh.write('            next_signal_out = s_axis_tdata;\n')
        if tlast:
            fh.write('            next_tlast_out = s_axis_tlast;\n')
        if tuser_width > 0:
            fh.write('            next_tuser_out = s_axis_tuser;\n')
        fh.write('        end\n')
        fh.write('        if (cnt == rate_i) begin\n')
        fh.write('            next_cnt = 0;\n')
        fh.write('        end else begin\n')
        fh.write('            next_cnt = cnt + 1;\n')
        fh.write('        end\n')
        fh.write('    end else if (m_axis_tready == 1\'b1) begin\n')
        fh.write('        next_valid_s = 1\'b0;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('endmodule\n')


def gen_shifter(path, input_width, shift_bits, gain_width, output_width=None, prefix=''):

    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)
    output_width = input_width if output_width is None else output_width

    mod_name = '{}shifter_{}iw_{}ow'.format(prefix, input_width, output_width)
    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)
    fh = open(file_name, 'w')

    slice_bits = input_width + gain_width - 1
    mult_width = gain_width + input_width

    (slicer_file, slicer_name) = gen_slicer(slice_bits, output_width, max_offset=2**shift_bits - 1, file_path=path, rev_dir=True)

    shift_msb = shift_bits - 1
    mult_msb = mult_width - 1
    output_msb = output_width - 1
    input_msb = input_width - 1
    gain_msb = gain_width - 1

    with open(file_name, 'w') as fh:
        fh.write('\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('//\n')
        fh.write('// Author      : Phil Vallance\n')
        fh.write('// File        : {}.v\n'.format(module_name))
        fh.write('// Description : Module performs scaling and bit slice as part of an gain block\n')
        fh.write('//\n')
        print_header(fh)
        fh.write('\n')
        fh.write('//\n')
        fh.write('/*****************************************************************************/\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('  input sync_reset,\n')
        fh.write('  input clk,\n')
        fh.write('\n')
        fh.write('  input valid_i,\n')
        fh.write('  input [{}:0] mult_factor_i,\n'.format(gain_msb))
        fh.write('  input [{}:0] shift_factor_i,\n'.format(shift_msb))
        fh.write('\n')
        fh.write('  input [{}:0] i_input,\n'.format(input_msb))
        fh.write('  input [{}:0] q_input,\n'.format(input_msb))
        fh.write('\n')
        fh.write('  output valid_o,\n')
        fh.write('  output [{}:0] i_output,\n'.format(output_msb))
        fh.write('  output [{}:0] q_output,\n'.format(output_msb))
        fh.write('  output overflow_o\n')
        fh.write('\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('parameter BLOCK_LATENCY = 6;\n')
        fh.write('\n')
        fh.write('wire [{}:0] i_gain, q_gain;\n'.format(mult_msb))
        fh.write('reg [{}:0] shift_val_d [3:0];\n'.format(shift_msb))
        fh.write('\n')
        fh.write('reg [4:0] i_sign, q_sign;\n')
        fh.write('\n')
        fh.write('reg [BLOCK_LATENCY-1:0] valid_d;\n')
        fh.write('\n')
        fh.write('wire [{}:0] i_shift, q_shift;\n'.format(output_msb))
        str_val = 'i_output, next_i_output, q_output, next_q_output'
        reg_str = 'reg [{}:0] '.format(output_msb)
        fh.write(reg_str + str_val + ';\n')
        fh.write('reg next_i_overflow, i_overflow, next_q_overflow, q_overflow;\n')
        fh.write('\n')
        fh.write('wire [{}:0] i_gain_slice, q_gain_slice;\n'.format(mult_msb - 1))
        fh.write('\n')
        fh.write('assign i_gain_slice = i_gain[{}:0];\n'.format(mult_msb - 1))
        fh.write('assign q_gain_slice = q_gain[{}:0];\n'.format(mult_msb - 1))
        fh.write('\n')
        fh.write('assign valid_o = valid_d[BLOCK_LATENCY-1];\n')
        fh.write('assign i_output = i_output;\n')
        fh.write('assign q_output = q_output;\n')
        fh.write('assign overflow_o = i_overflow | q_overflow;\n')
        fh.write('\n')
        fh.write('integer ii;\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('	if (sync_reset == 1\'b1) begin\n')
        fh.write('      valid_d  <= 0;\n')
        fh.write('      i_overflow <= 1\'b0;\n')
        fh.write('      q_overflow <= 1\'b0;\n')
        fh.write('	end else begin\n')
        fh.write('		valid_d <= {valid_d[BLOCK_LATENCY-2:0],valid_i};\n')
        fh.write('      i_overflow <= next_i_overflow;\n')
        fh.write('      q_overflow <= next_q_overflow;\n')
        fh.write('	end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('  i_sign[0] <= i_input[{}];\n'.format(input_msb))
        fh.write('  q_sign[0] <= q_input[{}];\n'.format(input_msb))
        fh.write('	shift_val_d[0] <= shift_factor_i;\n')
        fh.write('  for (ii=1; ii<5; ii=ii+1) begin\n')
        fh.write('    q_sign[ii] <= q_sign[ii-1];\n')
        fh.write('    i_sign[ii] <= i_sign[ii-1];\n')
        fh.write('  end\n')
        fh.write('	for (ii = 1; ii < 4; ii = ii + 1) begin\n')
        fh.write('		  shift_val_d[ii] <= shift_val_d[ii-1];\n')
        fh.write('	end\n')
        fh.write('  i_output <= next_i_output;\n')
        fh.write('  q_output <= next_q_output;\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('//mux Process Latency 1.\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('  next_i_overflow = 1\'b0;\n')
        fh.write('  next_q_overflow = 1\'b0;\n')
        fh.write('  if (i_sign[4] != i_shift[{}]) begin\n'.format(output_msb))
        fh.write('      next_i_overflow = 1\'b1;\n')
        fh.write('      if (i_sign[4] == 1\'b1) begin\n')
        str0 = '1' + (output_width - 1) * '0'
        fh.write('        next_i_output = {}\'b{};\n'.format(output_width, str0))
        fh.write('      end else begin\n')
        str1 = '0' + (output_width - 1) * '1'
        fh.write('        next_i_output = {}\'b{};\n'.format(output_width, str1))
        fh.write('      end\n')
        fh.write('  end else begin\n')
        fh.write('    next_i_output = i_shift;\n')
        fh.write('  end\n')
        fh.write('  if (q_sign[4] != q_shift[{}]) begin\n'.format(output_msb))
        fh.write('    next_q_overflow = 1\'b0;\n')
        fh.write('    if (q_sign[4] == 1\'b1) begin\n')
        fh.write('      next_q_output = {}\'b{};\n'.format(output_width, str0))
        fh.write('    end else begin\n')
        fh.write('      next_q_output = {}\'b{};\n'.format(output_width, str1))
        fh.write('    end\n')
        fh.write('  end else begin\n')
        fh.write('    next_q_output = q_shift;\n')
        fh.write('  end\n')
        fh.write('end\n')
        fh.write('\n')
        funcs = 'a*b'
        mod_name = prefix + '_gainmult'
        (gain_file, gain_name) = gen_dsp48E1(path, mod_name, opcode=funcs, areg=2, breg=2)
        fh.write('// Latency = 4.\n')
        fh.write('{} gain_i (\n'.format(gain_name))
        fh.write('  .clk(clk), \n')
        fh.write('  .a(i_input),\n')
        fh.write('  .b(mult_factor_i),\n')
        fh.write('  .p(i_gain)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// Latency = 4.\n')
        fh.write('{} gain_q (\n'.format(gain_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .a(q_input),\n')
        fh.write('  .b(mult_factor_i),\n')
        fh.write('  .p(q_gain)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('{} shift_i (\n'.format(slicer_name))
        fh.write('  .sync_reset(sync_reset), // reset\n')
        fh.write('  .clk(clk), // clock\n')
        fh.write('\n')
        fh.write('// Settings offet the slicer from the base value.\n')
        fh.write('  .slice_offset_i(shift_val_d[3]),\n')
        fh.write('\n')
        fh.write('  .valid_i(valid_d[3]),\n')
        fh.write('  .signal_i(i_gain_slice),\n')
        fh.write('\n')
        fh.write('  .valid_o(shift_valid),\n')
        fh.write('  .signal_o(i_shift)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('{} shift_q (\n'.format(slicer_name))
        fh.write('  .clk(clk),\n')
        fh.write('  .sync_reset(sync_reset),\n')
        fh.write('\n')
        fh.write('// Settings offet the slicer from the base value.\n')
        fh.write('  .slice_offset_i(shift_val_d[3]),\n')
        fh.write('\n')
        fh.write('  .valid_i(valid_d[3]),\n')
        fh.write('  .signal_i(q_gain_slice),\n')
        fh.write('\n')
        fh.write('  .valid_o(),\n')
        fh.write('  .signal_o(q_shift)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return (file_name, mod_name, slicer_file, slicer_name, gain_file, gain_name)


def test_run():
    num_corrs = 20
    gen_pipe_mux(20 * num_corrs, 20, './', one_hot=True)
    input_width = 42
    gen_pipe_logic(input_width)


# if __name__ == "__main__":
#     test_run()
