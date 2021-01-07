#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 12:28:03 2016

@author: phil
"""

import scipy as sp
import scipy.signal as signal
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.animation as manimation
from matplotlib.animation import MovieWriter

from mpl_toolkits.mplot3d import axes3d, Axes3D
import numpy as np
import copy
import time
import ipdb
import dill as pickle
from collections import OrderedDict
from matplotlib import rc
from argparse import ArgumentParser

import phy_tools.fil_utils as fil_utils
import phy_tools.fp_utils as fp_utils

from phy_tools.plt_utils import plot_psd_helper, plot_psd, gen_psd, df_str, gen_freq_vec
import phy_tools.gen_utils as gen_utils
from phy_tools.gen_utils import upsample, add_noise_pwr, write_complex_samples, read_complex_samples, write_binary_file
from phy_tools.gen_utils import gen_comp_tone, read_binary_file, compass
from phy_tools.qam_waveform import QAM_Mod
from phy_tools.fp_utils import nextpow2
from phy_tools.gen_utils import ret_module_name, ret_valid_path
from phy_tools.fp_utils import ret_num_bitsU, dec_to_ubin

import phy_tools.verilog_gen as vgen
from phy_tools.verilog_gen import name_help
import phy_tools.verilog_filter as vfilter
import phy_tools.adv_pfb as adv_filter
import phy_tools.vgen_xilinx as vgenx

from shutil import copyfile

from IPython.core.debugger import set_trace

from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    __version__ = today.strftime("%Y.%m.%d")

plt.style.use('seaborn')
plt.ion()

dpi = 100

blockl = True

import os
dirname = os.path.dirname(__file__)
GEN_2X = True
# if gen_2X:
#     IP_PATH = os.path.join(dirname, '../hdl/src/verilog/')
# else:
#     IP_PATH = os.path.join(dirname, '../hdl/src/verilog-512_1x/')
IP_PATH = os.path.join(dirname, './chan_test/src/')

if not os.path.isdir(IP_PATH):
    os.makedirs(IP_PATH)

SIM_PATH = os.path.join(dirname, './chan_test/sim/')
if not os.path.isdir(SIM_PATH):
    os.makedirs(SIM_PATH)
# test if path exists
TAPS_PER_PHASE = 32
SIX_DB = 10 * np.log10(.25)
NUM_ITERS = 400
FREQZ_PTS = 20000
PFB_MSB = 43
DESIRED_MSB = PFB_MSB
QVEC = (16, 15)
QVEC_COEF = (25, 24)
M_MAX = 512
FC_SCALE = .85  # was .65
TBW_SCALE = .3
TAPS = None
rc('text', usetex=False)

K_default = OrderedDict([(4, 13.905715942382809), (8, 13.905715942382809), (16, 11.75405975341801), (32, 11.752742309570353), (64, 12.125381164550815), (128, 11.931529541015662), (256, 11.931502990722693), (512, 11.97845520019535), (1024, 11.954858093261757), (2048, 11.954857177734413)])
offset_default = OrderedDict([(4, .5), (8, .5), (16, .5), (32, .5), (64, .5), (128, .5), (256, .5), (512, .5), (1024, .5), (2048, .5)])
msb_default = OrderedDict([(8, 39), (16, 39), (32, 39), (64, 39), (128, 39), (256, 39), (512, 39), (1024, 39), (2048, 39)])

K_terms = OrderedDict([(8, 6.45), (16, 6.330000000000003), (32, 6.333000000000001), (64, 6.326999999999999), (128, 6.297), (256, 6.308999999999998), (512, 6.308999999999998), (1024, 6.308999999999998), (2048, 6.308999999999998)])
msb_terms = OrderedDict([(8, 40), (16, 40), (32, 40), (64, 40), (128, 40), (256, 40), (512, 40), (1024, 40), (2048, 40)])
offset_terms = OrderedDict([(8, 0.5149999999999997), (16, 0.49875), (32, 0.49875), (64, 0.49875), (128, 0.500625), (256, 0.499375), (512, 0.5), (1024, 0.5), (2048, 0.5)])

K_terms = OrderedDict([(8, 32.458509317419505), (16, 32.458509317419505), (32, 32.458509317419505), (64, 28.697231648754062), (
    128, 29.755193951058885), (256, 29.755193951058885), (512, 29.755193951058885), (1024, 29.755193951058885), (2048, 29.755193951058885)])
msb_terms = OrderedDict([(8, 39), (16, 39), (32, 39), (64, 39), (128, 39),
                         (256, 39), (512, 39), (1024, 39), (2048, 39)])
offset_terms = OrderedDict([(8, 0.5), (16, 0.505), (32, 0.505), (64, 0.51), (128, 0.51),
                            (256, 0.5), (512, 0.5), (1024, 0.5), (2048, 0.5)])

def ret_k_terms(taps_per_phase=24):
    # if TAPS_PER_PHASE == 32:
    #     K = 21.0497
    offset_terms = offset_default
    K_terms = K_default
    msb_terms = msb_default
    if taps_per_phase == 24:
        K_terms = OrderedDict([(8, 13.905715942382809), (16, 11.75405975341801), (32, 11.752742309570353), (64, 12.125381164550815), (128, 11.931529541015662), (256, 11.931502990722693), (512, 11.97845520019535), (1024, 11.954858093261757), (2048, 11.954857177734413)])
        msb_terms = OrderedDict([(8, 39), (16, 39), (32, 39), (64, 39), (128, 39), (256, 39), (512, 39), (1024, 39), (2048, 39)])
        offset_terms = offset_default
    elif taps_per_phase == 16:
        # K_terms = OrderedDict([(8, 5.909457397460962), (16, 6.285075988769546), (32, 6.283267211914079), (64, 6.282817687988298), (128, 6.230665893554707), (256, 6.256452941894549), (512, 6.243489379882831), (1024, 6.243487243652363), (2048, 6.2434869384765825)])
        # msb_terms = OrderedDict([(8, 40), (16, 41), (32, 41), (64, 43), (128, 43), (256, 43), (512, 43), (1024, 43), (2048, 43)])
        K_terms = OrderedDict([(8, 5.909457397460962), (16, 6.285075988769546), (32, 6.283267211914079), (64, 6.282817687988298), (128, 6.230665893554707), (256, 6.256452941894549), (512, 6.243489379882831), (1024, 6.243487243652363), (2048, 6.2434869384765825)])
        msb_terms = OrderedDict([(8, 40), (16, 41), (32, 42), (64, 43), (128, 44), (256, 45), (512, 46), (1024, 47), (2048, 48)])

    return K_terms, msb_terms

rc('text', usetex=False)

def gen_chan_name(chan_obj):
    """
        Helper function.  Generates channelizer module name based on channelizer parameters.

    """
    Mmax = chan_obj.Mmax
    taps_per_phase = chan_obj.taps_per_phase
    pfb_iw = chan_obj.qvec[0]
    pfb_ow = chan_obj.qvec[0]
    gen_2X = chan_obj.gen_2X

    if gen_2X:
        mod_name = 'chan_top_2x_{}M_{}iw_{}ow_{}tps'.format(Mmax, pfb_iw, pfb_ow, taps_per_phase)
    else:
        mod_name = 'chan_top_{}M_{}iw_{}ow_{}tps'.format(Mmax, pfb_iw, pfb_ow, taps_per_phase)

    return mod_name

def gen_chan_tb(path, chan_obj, mask_len):

    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)

    full_path = os.path.abspath(path)
    Mmax = chan_obj.Mmax

    fft_bits = ret_num_bitsU(Mmax)

    chan_name = gen_chan_name(chan_obj)
    mod_name = chan_name + '_tb'

    # set payload length to yield integer number of bin cycles that yields a packet of 4096 bytes

    bytes_per_vec = mask_len * 4
    num_cycles = 4096 // bytes_per_vec
    payload_len = num_cycles * mask_len
    print("mask_len = {}, num_cycles = {}, payload_len = {}".format(mask_len, num_cycles, payload_len))

    idx_bytes = int(np.ceil(ret_num_bitsU(Mmax - 1) / 8.))
    tuser_bits = idx_bytes * 8 + 8

    file_name = name_help(mod_name, path)
    with open(file_name, 'w') as fh:

        fh.write('// Top level testbench\n')
        fh.write('\n')
        fh.write('`timescale 1ns/1ps\n')
        fh.write('\n')
        fh.write('module {}();\n'.format(mod_name))
        fh.write('\n')
        fh.write('function integer clog2;\n')
        fh.write(' //\n')
        fh.write(' // ceiling( log2( x ) )\n')
        fh.write(' //\n')
        fh.write(' input integer x;\n')
        fh.write(' begin\n')
        fh.write('   if (x<=0) clog2 = -1;\n')
        fh.write('   else clog2 = 0;\n')
        fh.write('   x = x - 1;\n')
        fh.write('   while (x>0) begin\n')
        fh.write('     clog2 = clog2 + 1;\n')
        fh.write('     x = x >> 1;\n')
        fh.write('   end\n')
        fh.write('\n')
        fh.write(' end\n')
        fh.write('endfunction\n')
        fh.write('\n')
        fh.write("localparam stimulus = \"{}/sig_tones_{}.bin\";\n".format(full_path, Mmax))
        fh.write("localparam mask_file = \"{}/M_{}_mask.bin\";\n".format(full_path, Mmax))
        fh.write("localparam output_file = \"{}/chan_results.bin\";\n".format(full_path))
        fh.write('\n')
        fh.write('integer input_descr, mask_descr, output_descr;\n')
        fh.write('\n')
        fh.write('initial begin\n')
        fh.write('    input_descr = $fopen(stimulus, "rb");\n')
        fh.write('    mask_descr = $fopen(mask_file, "rb");\n')
        fh.write('    output_descr = $fopen(output_file, "wb");\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('reg clk = 1\'b0;\n')
        fh.write('reg sync_reset = 1\'b0;\n')
        fh.write('\n')
        fh.write('always #2.5 clk <= ~clk;\n')
        fh.write('\n')
        fh.write('wire s_axis_tvalid, s_axis_tready;\n')
        fh.write('wire m_axis_tvalid, m_axis_tready;\n')
        fh.write('wire [{}:0] m_axis_tuser;\n'.format(tuser_bits - 1))
        fh.write('wire [31:0] m_axis_tdata;\n')
        fh.write('wire m_axis_tlast;\n')
        fh.write('\n')
        fh.write('wire [63:0] word_cnt;\n')
        fh.write('wire [31:0] s_axis_tdata;\n')
        fh.write('wire eob_tag;\n')
        fh.write('reg data_enable = 1\'b0;\n')
        fh.write('\n')
        fh.write('// wire s_axis_reload_tvalid;\n')
        fh.write('// wire [31:0] s_axis_reload_tdata;\n')
        fh.write('// wire s_axis_reload_tlast;\n')
        fh.write('// wire s_axis_reload_tready;\n')
        fh.write('\n')
        fh.write('wire s_axis_select_tvalid;\n')
        fh.write('wire [31:0] s_axis_select_tdata;\n')
        fh.write('wire s_axis_select_tlast;\n')
        fh.write('wire s_axis_select_tready;\n')
        fh.write('\n')
        fh.write('reg flow_ctrl = 1\'b0;\n')
        fh.write('\n')
        fh.write('localparam FFT_SIZE_WIDTH = clog2(512) + 1;\n')
        fh.write('reg [FFT_SIZE_WIDTH-1:0] FFT_SIZE = 512;\n')
        fh.write('\n')
        fh.write('// reset signal process.\n')
        fh.write('initial begin\n')
        fh.write('  #10\n')
        fh.write('  sync_reset = 1\'b1;\n')
        fh.write('  #100  //repeat(10) @(posedge clk);\n')
        fh.write('  sync_reset = 1\'b0;\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('initial begin\n')
        fh.write('    #90000  // wait 90 us to start data flowing -- allows the taps to be written.\n')
        fh.write('    data_enable = 1\'b1;\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('// flow ctrl signal\n')
        fh.write('initial begin\n')
        fh.write('    forever begin\n')
        fh.write('        #50 flow_ctrl = 1\'b1;\n')
        fh.write('        #100 flow_ctrl = 1\'b0;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('grc_word_reader #(\n')
        fh.write('    .NUM_BYTES(4),\n')
        fh.write('    .FRAME_SIZE(1024)\n')
        fh.write(')\n')
        fh.write('u_data_reader\n')
        fh.write('(\n')
        fh.write('  .clk(clk),\n')
        fh.write('  .sync_reset(sync_reset),\n')
        fh.write('  .enable_i(data_enable),\n')
        fh.write('\n')
        fh.write('  .fd(input_descr),\n')
        fh.write('\n')
        fh.write('  .valid_o(s_axis_tvalid),\n')
        fh.write('  .word_o(s_axis_tdata),\n')
        fh.write('  .buffer_end_o(),\n')
        fh.write('  .len_o(),\n')
        fh.write('  .word_cnt(),\n')
        fh.write('\n')
        fh.write('  .ready_i(s_axis_tready)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('grc_word_reader #(\n')
        fh.write('    .NUM_BYTES(4),\n')
        fh.write('    .FRAME_SIZE(1024)\n')
        fh.write(')\n')
        fh.write('u_mask_reader\n')
        fh.write('(\n')
        fh.write('  .clk(clk),\n')
        fh.write('  .sync_reset(sync_reset),\n')
        fh.write('  .enable_i(1\'b1),\n')
        fh.write('\n')
        fh.write('  .fd(mask_descr),\n')
        fh.write('\n')
        fh.write('  .valid_o(s_axis_select_tvalid),\n')
        fh.write('  .word_o(s_axis_select_tdata),\n')
        fh.write('  .buffer_end_o(s_axis_select_tlast),\n')
        fh.write('  .len_o(),\n')
        fh.write('  .word_cnt(word_cnt),\n')
        fh.write('\n')
        fh.write('  .ready_i(s_axis_select_tready)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('{} u_dut\n'.format(chan_name))
        fh.write('(\n')
        fh.write('   .clk(clk),\n')
        fh.write('   .sync_reset(sync_reset),\n')
        fh.write('\n')
        fh.write('   .s_axis_tvalid(s_axis_tvalid),\n')
        fh.write('   .s_axis_tdata(s_axis_tdata),\n')
        fh.write('   .s_axis_tready(s_axis_tready),\n')
        fh.write('\n')
        fh.write('   .s_axis_reload_tvalid(1\'b0),\n')
        fh.write('   .s_axis_reload_tdata(32\'d0),\n')
        fh.write('   .s_axis_reload_tlast(1\'b0),\n')
        fh.write('   .s_axis_reload_tready(s_axis_reload_tready),\n')
        fh.write('\n')
        fh.write('   .s_axis_select_tvalid(s_axis_select_tvalid),\n')
        fh.write('   .s_axis_select_tdata(s_axis_select_tdata),\n')
        fh.write('   .s_axis_select_tlast(s_axis_select_tlast),\n')
        fh.write('   .s_axis_select_tready(s_axis_select_tready),\n')
        fh.write('\n')
        fh.write('   .fft_size({}\'d{}),\n'.format(fft_bits, Mmax))
        fh.write('   .avg_len(9\'b000001000),\n')
        fh.write('   .payload_length(16\'d{}),\n'.format(payload_len))
        fh.write('   .eob_tag(eob_tag),\n')
        fh.write('\n')
        fh.write('   .m_axis_tvalid(m_axis_tvalid),\n')
        fh.write('   .m_axis_tdata(m_axis_tdata),\n')
        fh.write('   .m_axis_tuser(m_axis_tuser),\n')
        fh.write('   .m_axis_tlast(m_axis_tlast),\n')
        fh.write('   .m_axis_tready(m_axis_tready)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('wire [63:0] store_vec;\n')
        fh.write('\n')
        t_bits = 32 + tuser_bits + 1
        pad_bits = 64 - t_bits
        fh.write('assign store_vec = {{{}\'d0, m_axis_tlast, m_axis_tuser, m_axis_tdata}};\n'.format(pad_bits))
        fh.write('\n')
        fh.write('grc_word_writer #(\n')
        fh.write('	.LISTEN_ONLY(0),\n')
        fh.write('	.ARRAY_LENGTH(1024),\n')
        fh.write('	.NUM_BYTES(8))\n')
        fh.write('u_writer\n')
        fh.write('(\n')
        fh.write('  .clk(clk),\n')
        fh.write('  .sync_reset(sync_reset),\n')
        fh.write('  .enable(1\'b1),\n')
        fh.write('\n')
        fh.write('  .fd(output_descr),\n')
        fh.write('\n')
        fh.write('  .valid(m_axis_tvalid),\n')
        fh.write('  .word(store_vec),\n')
        fh.write('\n')
        fh.write('  .wr_file(1\'b0),\n')
        fh.write('  .word_cnt(),\n')
        fh.write('\n')
        fh.write('  .rdy_i(flow_ctrl),\n')
        fh.write('  .rdy_o(m_axis_tready)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('endmodule //\n')


def calc_fft_tuser_width(Mmax):
    idx_bytes = int(np.ceil(ret_num_bitsU(Mmax - 1) / 8.))
    tuser_bits = idx_bytes * 8 + 8
    return tuser_bits


def gen_chan_top(path, chan_obj, shift_name, pfb_name, fft_name):  # gen_2X, Mmax, taps_per_phase, pfb_iw, pfb_ow):
    assert(path is not None), 'User must specify Path'
    path = ret_valid_path(path)

    shift_name = ret_module_name(shift_name)
    pfb_name = ret_module_name(pfb_name)

    Mmax = chan_obj.Mmax
    mod_name = gen_chan_name(chan_obj)
    pfb_iw = chan_obj.qvec[0]
    gen_2X = chan_obj.gen_2X

    file_name = name_help(mod_name, path)
    module_name = ret_module_name(file_name)

    data_width = pfb_iw * 2
    num_fft_sizes = int(np.log2(Mmax)) - 2
    fft_bits = ret_num_bitsU(Mmax)

    tuser_bits = calc_fft_tuser_width(Mmax)

    with open(file_name, 'w') as fh:

        fh.write('//***************************************************************************--\n')
        fh.write('//\n')
        fh.write('// Author : PJV\n')
        fh.write('// File : channelizer_top\n')
        fh.write('// Description : Top level wrapper for the M/2 Polyphase Channelizer bank.\n')
        fh.write('//\n')
        fh.write('//***************************************************************************--\n')
        fh.write('\n')
        fh.write('// no timescale needed\n')
        fh.write('`include "chan_sim.vh"\n')
        fh.write('\n')
        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        fh.write('    input clk,\n')
        fh.write('    input sync_reset,\n')
        fh.write('\n')
        fh.write('    input s_axis_tvalid,\n')
        fh.write('    input [{}:0] s_axis_tdata,\n'.format(data_width - 1))
        fh.write('    output s_axis_tready,\n')
        fh.write('\n')
        fh.write('    input s_axis_reload_tvalid,\n')
        fh.write('    input [31:0] s_axis_reload_tdata,\n')
        fh.write('    input s_axis_reload_tlast,\n')
        fh.write('    output s_axis_reload_tready,\n')
        fh.write('\n')
        fh.write('    // down selection FIFO interface\n')
        fh.write('    input s_axis_select_tvalid,\n')
        fh.write('    input [{}:0] s_axis_select_tdata,\n'.format(data_width - 1))
        fh.write('    input s_axis_select_tlast,\n')
        fh.write('    output s_axis_select_tready,\n')
        fh.write('\n')
        fh.write('    input [{}:0] fft_size,\n'.format(fft_bits - 1))
        fh.write('    input [8:0] avg_len,\n')
        fh.write('    input [15:0] payload_length,\n')
        fh.write('    output eob_tag,\n')
        fh.write('\n')
        fh.write('    output m_axis_tvalid,\n')
        fh.write('    output [{}:0] m_axis_tdata,\n'.format(data_width - 1))
        fh.write('    output [{}:0] m_axis_tuser,\n'.format(tuser_bits - 1))
        fh.write('    output m_axis_tlast,\n')
        fh.write('    input m_axis_tready\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('// currently only supporting up to 2048 bins.\n')
        fh.write('// Average Floating Point Exponent averaging length\n')
        fh.write('\n')
        for i in range(num_fft_sizes):
            fft_size = 2**(i + 3)
            fh.write('localparam FFT_{} = {};\n'.format(fft_size, fft_size))

        fh.write('localparam UPPER_IDX = {};\n'.format(data_width - 1))
        fh.write('localparam HALF_IDX = {};\n'.format(data_width // 2))
        fh.write('localparam LOWER_IDX = {};\n'.format(data_width // 2 - 1))
        fh.write('\n')
        fh.write('reg [4:0] nfft, next_nfft;\n')
        fh.write('reg [{}:0] fft_size_s;\n'.format(fft_bits - 1))
        fh.write('wire event_frame_started;\n')
        fh.write('wire event_tlast_unexpected;\n')
        fh.write('wire event_tlast_missing;\n')
        fh.write('wire event_status_channel_halt;\n')
        fh.write('wire event_data_in_channel_halt;\n')
        fh.write('wire event_data_out_channel_halt;\n')
        fh.write('\n')
        fh.write('reg async_reset, async_reset_d1;\n')
        fh.write('reg reset_int,  next_reset_int;\n')
        fh.write('reg [4:0] reset_cnt, next_reset_cnt;\n')
        fh.write('\n')
        fh.write('localparam [4:0] RESET_ZEROS = 5\'d0;\n')
        fh.write('localparam [4:0] RESET_HIGH_CNT = 5\'b01000;  // buffer signals\n')
        fh.write('\n')
        fh.write('// internal payload_length register\n')
        fh.write('reg [15:0] payload_length_s, payload_length_m1;\n')
        fh.write('\n')
        fh.write('wire buffer_tvalid;\n')
        fh.write('wire [{}:0] buffer_tdata;\n'.format(data_width - 1))
        fh.write('wire buffer_tlast;\n')
        fh.write('wire [{}:0] buffer_phase;\n'.format(fft_bits - 2))
        fh.write('wire buffer_tready;\n')
        fh.write('\n')
        fh.write('// pfb signals\n')
        fh.write('wire pfb_tvalid;\n')
        fh.write('wire [{}:0] pfb_tdata;\n'.format(data_width - 1))
        fh.write('wire pfb_tlast;\n')
        fh.write('wire [{}:0] pfb_phase;\n'.format(fft_bits - 2))
        fh.write('wire [{}:0] circ_phase;\n'.format(fft_bits - 2))
        fh.write('wire pfb_tready;\n')
        fh.write('\n')
        if gen_2X:
            fh.write('// circular buffer signals\n')
            fh.write('wire circ_tvalid;\n')
            fh.write('wire [{}:0] circ_tdata;\n'.format(data_width - 1))
            fh.write('wire [{}:0] circ_tdata_s;\n'.format(data_width - 1))
            fh.write('wire circ_tlast;\n')
            fh.write('wire circ_tready;\n')
        fh.write('\n')
        fh.write('// fft data signals\n')
        fh.write('wire fft_tvalid;\n')
        fh.write('wire [{}:0] fft_tdata;\n'.format(data_width - 1))
        fh.write('wire [{}:0] fft_tdata_s;\n'.format(data_width - 1))
        fh.write('wire [{}:0] fft_tuser;\n'.format(tuser_bits - 1))
        fh.write('wire fft_tlast;\n')
        fh.write('wire fft_tready;\n')
        fh.write('\n')
        fh.write('// fft config signals.\n')
        fh.write('reg fft_config_tvalid, next_fft_config_tvalid;\n')
        fh.write('wire fft_config_tready;\n')
        fh.write('wire [15:0] fft_config_tdata;  // fft status signals\n')
        fh.write('\n')
        fh.write('// exp shift signals\n')
        fh.write('wire shift_tvalid;\n')
        fh.write('wire [{}:0] shift_tdata;\n'.format(data_width - 1))
        fh.write('wire [{}:0] shift_tuser;\n'.format(tuser_bits - 1))
        fh.write('wire shift_tlast;\n')
        fh.write('wire shift_tready;\n')
        fh.write('wire shift_eob_tag;\n')
        fh.write('\n')
        fh.write('// down select signals\n')
        fh.write('wire down_sel_tvalid;\n')
        fh.write('wire [{}:0] down_sel_tdata;\n'.format(data_width - 1))
        fh.write('wire [{}:0] down_sel_tuser;\n'.format(tuser_bits - 1))
        fh.write('wire down_sel_tlast;\n')
        fh.write('wire down_sel_tready;\n')
        fh.write('\n')
        fh.write('// output signals\n')
        fh.write('wire m_axis_tvalid_s;\n')
        fh.write('wire [{}:0] m_axis_tdata_s;\n'.format(data_width - 1))
        fh.write('wire m_axis_tready_s;\n')
        fh.write('wire m_axis_tlast_s;\n')
        fh.write('wire [{}:0] m_axis_tuser_s;\n'.format(tuser_bits - 1))
        fh.write('\n')
        fh.write('wire [7:0] m_axis_status_tdata;\n')
        fh.write('wire m_axis_status_tvalid;\n')
        fh.write('wire m_axis_status_tready = 1\'b1;\n')
        fh.write('\n')
        fh.write('localparam S_CONFIG = 0, S_IDLE = 1;\n')
        fh.write('reg config_state, next_config_state;\n')
        fh.write('\n')
        fh.write('assign m_axis_tvalid = m_axis_tvalid_s;\n')
        fh.write('assign m_axis_tready_s = m_axis_tready;\n')
        fh.write('assign m_axis_tdata = m_axis_tdata_s;\n')
        fh.write('assign m_axis_tuser = m_axis_tuser_s;\n')
        fh.write('assign m_axis_tlast = m_axis_tlast_s;\n')
        fh.write('assign fft_config_tdata = {11\'d0,nfft};\n')
        fh.write('assign fft_tdata = {fft_tdata_s[LOWER_IDX:0],fft_tdata_s[UPPER_IDX:HALF_IDX]};\n')
        if gen_2X:
            fh.write('assign circ_tdata = {circ_tdata_s[LOWER_IDX:0],circ_tdata_s[UPPER_IDX:HALF_IDX]};\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_fft_config_tvalid = 1\'b0;\n')
        fh.write('    next_config_state = config_state;\n')
        fh.write('    next_nfft = nfft;\n')
        fh.write('    case(config_state)\n')
        fh.write('        S_CONFIG :\n')
        fh.write('        begin\n')
        fh.write('            if (fft_config_tready == 1\'b1) begin\n')
        fh.write('                next_fft_config_tvalid = 1\'b1;\n')
        fh.write('                next_config_state = S_IDLE;\n')
        fh.write('            end\n')

        fh.write('            if (fft_size == FFT_8) begin\n')

        fh.write('                next_nfft = 5\'b00011;\n')
        for i in range(1, num_fft_sizes):
            fft_size = 2 ** (i + 3)
            fh.write('            end else if (fft_size == FFT_{}) begin\n'.format(fft_size))
            bin_value = dec_to_ubin(int(np.log2(fft_size)), 5)
            fh.write('                next_nfft = 5\'b{};\n'.format(bin_value))
        fh.write('            end else begin\n')
        fh.write('                next_nfft = 5\'b00011;\n')
        fh.write('            end\n')
        fh.write('        end\n')
        fh.write('        S_IDLE :\n')
        fh.write('        begin\n')
        fh.write('            if (async_reset == 1\'b1 && async_reset_d1 == 1\'b0) begin\n')
        fh.write('                next_config_state = S_CONFIG;\n')
        fh.write('            end else begin\n')
        fh.write('                next_config_state = S_IDLE;\n')
        fh.write('            end\n')
        fh.write('        end\n')
        fh.write('        default :\n')
        fh.write('        begin\n')
        fh.write('        end\n')
        fh.write('    endcase\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk, posedge sync_reset)\n')
        fh.write('begin\n')
        fh.write('    if (sync_reset == 1\'b1) begin\n')
        fh.write('        config_state <= S_IDLE;\n')
        fh.write('        fft_config_tvalid <= 1\'b0;\n')
        fh.write('        nfft <= 5\'b00011;\n')
        fh.write('        fft_size_s <= {}\'d8;\n'.format(fft_bits))
        fh.write('        // default to 8\n')
        fh.write('        reset_cnt <= 5\'d31;\n')
        fh.write('        reset_int <= 1\'b1;\n')
        fh.write('    end else begin\n')
        fh.write('        config_state <= next_config_state;\n')
        fh.write('        fft_config_tvalid <= next_fft_config_tvalid;\n')
        fh.write('        nfft <= next_nfft;\n')
        fh.write('        if (fft_size != 0) begin\n')
        fh.write('            fft_size_s <= fft_size;\n')
        fh.write('        end\n')
        fh.write('        reset_cnt <= next_reset_cnt;\n')
        fh.write('        reset_int <= next_reset_int;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('always @(posedge clk)\n')
        fh.write('begin\n')
        fh.write('    async_reset <= !(sync_reset | reset_int);\n')
        fh.write('    async_reset_d1 <= async_reset;\n')
        fh.write('    payload_length_s <= payload_length;\n')
        fh.write('    payload_length_m1 <= payload_length_s - 1;\n')
        fh.write('end\n')
        fh.write('\n')
        fh.write('  // ensures that reset pulse is wide enough for all blocks.\n')
        fh.write('always @*\n')
        fh.write('begin\n')
        fh.write('    next_reset_cnt = reset_cnt;\n')
        fh.write('    if (fft_size_s != fft_size || payload_length_s != payload_length) begin\n')
        fh.write('        next_reset_cnt = RESET_HIGH_CNT;\n')
        fh.write('    end else if (reset_cnt != 0) begin\n')
        fh.write('        next_reset_cnt = reset_cnt - 1;\n')
        fh.write('    end\n')
        fh.write('    if (reset_cnt != RESET_ZEROS) begin\n')
        fh.write('        next_reset_int = 1\'b1;\n')
        fh.write('    end else begin\n')
        fh.write('        next_reset_int = 1\'b0;\n')
        fh.write('    end\n')
        fh.write('end\n')
        fh.write('\n')
        if gen_2X:
            fh.write('input_buffer #(\n')
        else:
            fh.write('input_buffer_1x #(\n')
        fh.write('    .DATA_WIDTH({}),\n'.format(data_width))
        fh.write('    .FFT_SIZE_WIDTH({}))\n'.format(fft_bits))
        fh.write('u_input_buffer(\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(reset_int),\n')
        fh.write('\n')
        fh.write('    .s_axis_tvalid(s_axis_tvalid),\n')
        fh.write('    .s_axis_tdata(s_axis_tdata),\n')
        fh.write('    .s_axis_tready(s_axis_tready),\n')
        fh.write('\n')
        fh.write('    .num_phases(fft_size_s),\n')
        fh.write('    .phase(buffer_phase),\n')
        fh.write('\n')
        fh.write('    .m_axis_tvalid(buffer_tvalid),\n')
        fh.write('    .m_axis_tdata(buffer_tdata),\n')
        fh.write('    .m_axis_final_cnt(buffer_tlast),\n')
        fh.write('    .m_axis_tready(buffer_tready)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('{} u_pfb(\n'.format(pfb_name))
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(reset_int),\n')
        fh.write('\n')
        fh.write('    .s_axis_tvalid(buffer_tvalid),\n')
        fh.write('    .s_axis_tdata(buffer_tdata),\n')
        fh.write('    .s_axis_tlast(buffer_tlast),\n')
        fh.write('    .s_axis_tready(buffer_tready),\n')
        fh.write('\n')
        fh.write('    .num_phases(fft_size_s),\n')
        fh.write('    .phase(buffer_phase),\n')
        fh.write('    .phase_out(pfb_phase),\n')
        fh.write('\n')
        fh.write('    .s_axis_reload_tvalid(s_axis_reload_tvalid),\n')
        fh.write('    .s_axis_reload_tdata(s_axis_reload_tdata),\n')
        fh.write('    .s_axis_reload_tlast(s_axis_reload_tlast),\n')
        fh.write('    .s_axis_reload_tready(s_axis_reload_tready),\n')
        fh.write('\n')
        fh.write('    .m_axis_tvalid(pfb_tvalid),\n')
        fh.write('    .m_axis_tdata(pfb_tdata),\n')
        fh.write('    .m_axis_tlast(pfb_tlast),\n')
        fh.write('    .m_axis_tready(pfb_tready)\n')
        fh.write(');\n')
        fh.write('\n')
        if gen_2X:
            fh.write('circ_buffer #(\n')
            fh.write('    .DATA_WIDTH({}),\n'.format(data_width))
            fh.write('    .FFT_SIZE_WIDTH({}))\n'.format(fft_bits))
            fh.write('u_circ_buffer(\n')
            fh.write('    .clk(clk),\n')
            fh.write('    .sync_reset(reset_int),\n')
            fh.write('\n')
            fh.write('    .s_axis_tvalid(pfb_tvalid),\n')
            fh.write('    .s_axis_tdata(pfb_tdata),\n')
            fh.write('    .s_axis_tlast(pfb_tlast),\n')
            fh.write('    .s_axis_tready(pfb_tready),\n')
            fh.write('\n')
            fh.write('    .fft_size(fft_size_s),\n')
            fh.write('    .phase(pfb_phase),\n')
            fh.write('    .phase_out(circ_phase),\n')
            fh.write('\n')
            fh.write('    .m_axis_tvalid(circ_tvalid),\n')
            fh.write('    .m_axis_tdata(circ_tdata_s),\n')
            fh.write('    .m_axis_tlast(circ_tlast),\n')
            fh.write('    .m_axis_tready(circ_tready)\n')
            fh.write(');\n')
        fh.write('\n')
        fh.write('{} u_fft(\n'.format(fft_name))
        fh.write('    .aclk(clk),\n')
        fh.write('    .aresetn(async_reset),\n')
        fh.write('    .s_axis_config_tvalid(fft_config_tvalid),\n')
        fh.write('    .s_axis_config_tdata(fft_config_tdata),\n')
        fh.write('    .s_axis_config_tready(fft_config_tready),\n')
        if gen_2X:
            fh.write('    .s_axis_data_tvalid(circ_tvalid),\n')
            fh.write('    .s_axis_data_tdata(circ_tdata),\n')
            fh.write('    .s_axis_data_tlast(circ_tlast),\n')
            fh.write('    .s_axis_data_tready(circ_tready),\n')
        else:
            fh.write('    .s_axis_data_tvalid(pfb_tvalid),\n')
            fh.write('    .s_axis_data_tdata(pfb_tdata),\n')
            fh.write('    .s_axis_data_tlast(pfb_tlast),\n')
            fh.write('    .s_axis_data_tready(pfb_tready),\n')

        fh.write('    .m_axis_data_tvalid(fft_tvalid),\n')
        fh.write('    .m_axis_data_tdata(fft_tdata_s),\n')
        fh.write('    .m_axis_data_tuser(fft_tuser),\n')
        fh.write('    .m_axis_data_tlast(fft_tlast),\n')
        fh.write('    .m_axis_data_tready(fft_tready),\n')
        fh.write('    .m_axis_status_tvalid(m_axis_status_tvalid),\n')
        fh.write('    .m_axis_status_tdata(m_axis_status_tdata),\n')
        fh.write('    .m_axis_status_tready(m_axis_status_tready),\n')
        fh.write('    .event_frame_started(event_frame_started),\n')
        fh.write('    .event_tlast_unexpected(event_tlast_unexpected),\n')
        fh.write('    .event_tlast_missing(event_tlast_missing),\n')
        fh.write('    .event_status_channel_halt(event_status_channel_halt),\n')
        fh.write('    .event_data_in_channel_halt(event_data_in_channel_halt),\n')
        fh.write('    .event_data_out_channel_halt(event_data_out_channel_halt)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('{} #(\n'.format(shift_name))
        fh.write(' .HEAD_ROOM(7\'d2))\n')
        fh.write('u_shifter(\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(reset_int),\n')
        fh.write('\n')
        fh.write('    .s_axis_tvalid(fft_tvalid),\n')
        fh.write('    .s_axis_tdata(fft_tdata),\n')
        fh.write('    .s_axis_tuser(fft_tuser),\n')
        fh.write('    .s_axis_tlast(fft_tlast),\n')
        fh.write('    .s_axis_tready(fft_tready),\n')
        fh.write('\n')
        fh.write('    .fft_size(fft_size_s),\n')
        fh.write('    .avg_len(avg_len),\n')
        fh.write('\n')
        fh.write('    .m_axis_tvalid(shift_tvalid),\n')
        fh.write('    .m_axis_tdata(shift_tdata),\n')
        fh.write('    .m_axis_tuser(shift_tuser),\n')
        fh.write('    .m_axis_tlast(shift_tlast),\n')
        fh.write('\n')
        fh.write('    .eob_tag(shift_eob_tag),\n')
        fh.write('    .m_axis_tready(shift_tready)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('downselect #(\n')
        fh.write('    .DATA_WIDTH({}))\n'.format(data_width))
        fh.write('u_downselect(\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(reset_int),\n')
        fh.write('\n')
        fh.write('    .s_axis_tvalid(shift_tvalid),\n')
        fh.write('    .s_axis_tdata(shift_tdata),\n')
        fh.write('    .s_axis_tuser(shift_tuser),\n')
        fh.write('    .s_axis_tlast(shift_tlast),\n')
        fh.write('    .s_axis_tready(shift_tready),\n')
        fh.write('\n')
        fh.write('    .eob_tag(shift_eob_tag),\n')
        fh.write('\n')
        fh.write('    // down selection FIFO interface\n')
        fh.write('    .s_axis_select_tvalid(s_axis_select_tvalid),\n')
        fh.write('    .s_axis_select_tdata(s_axis_select_tdata),\n')
        fh.write('    .s_axis_select_tlast(s_axis_select_tlast),\n')
        fh.write('    .s_axis_select_tready(s_axis_select_tready),\n')
        fh.write('\n')
        fh.write('    .m_axis_tvalid(down_sel_tvalid),\n')
        fh.write('    .m_axis_tdata(down_sel_tdata),\n')
        fh.write('    .m_axis_tuser(down_sel_tuser),\n')
        fh.write('    .m_axis_tlast(down_sel_tlast),\n')
        fh.write('    .m_axis_tready(down_sel_tready),\n')
        fh.write('\n')
        fh.write('    .eob_downselect(eob_tag)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('count_cycle_cw16_65 #(\n')
        fh.write('    .DATA_WIDTH({}),\n'.format(data_width))
        fh.write('    .TUSER_WIDTH({}))\n'.format(tuser_bits))
        fh.write('u_final_cnt\n')
        fh.write('(\n')
        fh.write('    .clk(clk),\n')
        fh.write('    .sync_reset(reset_int),\n')
        fh.write('\n')
        fh.write('    .s_axis_tvalid(down_sel_tvalid),\n')
        fh.write('    .s_axis_tdata(down_sel_tdata),\n')
        fh.write('    .cnt_limit(payload_length_m1),\n')
        fh.write('    .s_axis_tuser(down_sel_tuser),\n')
        fh.write('    .s_axis_tlast(down_sel_tlast),\n')
        fh.write('    .s_axis_tready(down_sel_tready),\n')
        fh.write('\n')
        fh.write('    .m_axis_tvalid(m_axis_tvalid_s),\n')
        fh.write('    .m_axis_tdata(m_axis_tdata_s),\n')
        fh.write('    .m_axis_final_cnt(m_axis_tlast_s),\n')
        fh.write('    .m_axis_tuser(m_axis_tuser_s),\n')
        fh.write('    .count(),\n')
        fh.write('    .m_axis_tlast(),\n')
        fh.write('    .m_axis_tready(m_axis_tready_s)\n')
        fh.write(');\n')
        fh.write('\n')
        fh.write('`ifdef SIM_BIN_WRITE\n')
        fh.write('\n')
        fh.write('    localparam buffer_out = "buffer_output.bin";\n')
        fh.write('    localparam pfb_out = "pfb_output.bin";\n')
        fh.write('    localparam circ_out = "circ_output.bin";\n')
        fh.write('    localparam fft_out = "fft_output.bin";\n')
        fh.write('    localparam exp_out = "exp_output.bin";\n')
        fh.write('    localparam down_select_out = "down_select_output.bin";\n')
        fh.write('    localparam final_out = "final_output.bin";\n')
        fh.write('\n')
        fh.write('    integer buffer_descr, pfb_descr, circ_descr, fft_descr, exp_descr, down_descr, final_descr;\n')
        fh.write('\n')
        fh.write('    initial begin\n')
        fh.write('        buffer_descr = $fopen(buffer_out, "wb");\n')
        fh.write('        pfb_descr = $fopen(pfb_out, "wb");\n')
        fh.write('        circ_descr = $fopen(circ_out, "wb");\n')
        fh.write('        fft_descr = $fopen(fft_out, "wb");\n')
        fh.write('        exp_descr = $fopen(exp_out, "wb");\n')
        fh.write('        down_descr = $fopen(down_select_out, "wb");\n')
        fh.write('        final_descr = $fopen(final_out, "wb");\n')
        fh.write('    end\n')
        fh.write('\n')
        fh.write('    wire buffer_take, pfb_take, circ_take, fft_take, exp_take, down_take, final_take;\n')
        fh.write('\n')
        fh.write('    wire [63:0] buffer_st_tdata;\n')
        fh.write('    wire [63:0] pfb_st_tdata;\n')
        fh.write('    wire [63:0] fft_st_tdata;\n')
        fh.write('    wire [63:0] exp_st_tdata;\n')
        fh.write('    wire [63:0] count_st_tdata;\n')
        fh.write('    wire [31:0] circ_st_tdata;\n')
        fh.write('    wire [63:0] exp_st_tdata;\n')
        fh.write('    wire [63:0] down_st_tdata;\n')
        fh.write('    wire [63:0] final_st_tdata;\n')
        fh.write('\n')
        buffer_pad = 64 - data_width - (fft_bits - 1)
        fft_pad = 64 - data_width - 24
        fh.write('    assign buffer_st_tdata = {{{}\'d0, buffer_phase, buffer_tdata}};\n'.format(buffer_pad))
        fh.write('    assign pfb_st_tdata = {{{}\'d0, pfb_phase, pfb_tdata}};\n'.format(buffer_pad))
        fh.write('    assign fft_st_tdata = {{{}\'d0, fft_tuser, fft_tdata}};\n'.format(fft_pad))
        fh.write('    assign exp_st_tdata = {{{}\'d0, shift_tuser, shift_tdata}};\n'.format(fft_pad))
        fh.write('    assign down_st_tdata = {{{}\'d0, down_sel_tuser, down_sel_tdata}};\n'.format(fft_pad))
        fh.write('    assign final_st_tdata = {{{}\'d0, m_axis_tuser_s, m_axis_tdata_s}};\n'.format(fft_pad))
        fh.write('\n')
        fh.write('    assign circ_st_tdata = circ_tdata_s;\n')
        fh.write('\n')
        fh.write('    assign buffer_take = buffer_tvalid & buffer_tready;\n')
        fh.write('    assign pfb_take = pfb_tvalid & pfb_tready;\n')
        fh.write('\n')
        fh.write('    assign circ_take = circ_tvalid & circ_tready;\n')
        fh.write('    assign fft_take = fft_tvalid & fft_tready;\n')
        fh.write('    assign exp_take = shift_tvalid & shift_tready;\n')
        fh.write('    assign down_take = down_sel_tvalid & down_sel_tready;\n')
        fh.write('    assign final_take = m_axis_tvalid_s & m_axis_tready_s;\n')
        fh.write('\n')
        fh.write('    grc_word_writer #(\n')
        fh.write('        .LISTEN_ONLY(1),\n')
        fh.write('        .ARRAY_LENGTH(1024),\n')
        fh.write('        .NUM_BYTES(8)\n')
        fh.write('    )\n')
        fh.write('    u_buffer_wr\n')
        fh.write('    (\n')
        fh.write('        .clk(clk),\n')
        fh.write('        .sync_reset(reset_int),\n')
        fh.write('        .enable(1\'b1),\n')
        fh.write('\n')
        fh.write('        .fd(buffer_descr),\n')
        fh.write('\n')
        fh.write('        .valid(buffer_take),\n')
        fh.write('        .word(buffer_st_tdata),\n')
        fh.write('\n')
        fh.write('        .wr_file(1\'b0),\n')
        fh.write('\n')
        fh.write('        .rdy_i(1\'b1),\n')
        fh.write('        .rdy_o()\n')
        fh.write('        );\n')
        fh.write('\n')
        fh.write('    grc_word_writer #(\n')
        fh.write('        .LISTEN_ONLY(1),\n')
        fh.write('        .ARRAY_LENGTH(1024),\n')
        fh.write('        .NUM_BYTES(8)\n')
        fh.write('    )\n')
        fh.write('    u_pfb_wr\n')
        fh.write('    (\n')
        fh.write('        .clk(clk),\n')
        fh.write('        .sync_reset(reset_int),\n')
        fh.write('        .enable(1\'b1),\n')
        fh.write('\n')
        fh.write('        .fd(pfb_descr),\n')
        fh.write('\n')
        fh.write('        .valid(pfb_take),\n')
        fh.write('        .word(pfb_st_tdata),\n')
        fh.write('\n')
        fh.write('        .wr_file(1\'b0),\n')
        fh.write('\n')
        fh.write('        .rdy_i(1\'b1),\n')
        fh.write('        .rdy_o()\n')
        fh.write('    );\n')
        fh.write('\n')
        fh.write('    grc_word_writer #(\n')
        fh.write('        .LISTEN_ONLY(1),\n')
        fh.write('        .ARRAY_LENGTH(1024),\n')
        fh.write('        .NUM_BYTES(4)\n')
        fh.write('    )\n')
        fh.write('    u_circ_wr\n')
        fh.write('    (\n')
        fh.write('        .clk(clk),\n')
        fh.write('        .sync_reset(reset_int),\n')
        fh.write('        .enable(1\'b1),\n')
        fh.write('\n')
        fh.write('        .fd(circ_descr),\n')
        fh.write('\n')
        fh.write('        .valid(circ_take),\n')
        fh.write('        .word(circ_st_tdata),\n')
        fh.write('\n')
        fh.write('        .wr_file(1\'b0),\n')
        fh.write('\n')
        fh.write('        .rdy_i(1\'b1),\n')
        fh.write('        .rdy_o()\n')
        fh.write('    );\n')
        fh.write('\n')
        fh.write('    grc_word_writer #(\n')
        fh.write('        .LISTEN_ONLY(1),\n')
        fh.write('        .ARRAY_LENGTH(1024),\n')
        fh.write('        .NUM_BYTES(8)\n')
        fh.write('        )\n')
        fh.write('    u_fft_wr\n')
        fh.write('    (\n')
        fh.write('        .clk(clk),\n')
        fh.write('        .sync_reset(reset_int),\n')
        fh.write('        .enable(1\'b1),\n')
        fh.write('\n')
        fh.write('        .fd(fft_descr),\n')
        fh.write('\n')
        fh.write('        .valid(fft_take),\n')
        fh.write('        .word(fft_st_tdata),\n')
        fh.write('\n')
        fh.write('        .wr_file(1\'b0),\n')
        fh.write('\n')
        fh.write('        .rdy_i(1\'b1),\n')
        fh.write('        .rdy_o()\n')
        fh.write('        );\n')
        fh.write('\n')
        fh.write('    grc_word_writer #(\n')
        fh.write('        .LISTEN_ONLY(1),\n')
        fh.write('        .ARRAY_LENGTH(1024),\n')
        fh.write('        .NUM_BYTES(8)\n')
        fh.write('        )\n')
        fh.write('    u_exp_wr\n')
        fh.write('    (\n')
        fh.write('        .clk(clk),\n')
        fh.write('        .sync_reset(reset_int),\n')
        fh.write('        .enable(1\'b1),\n')
        fh.write('\n')
        fh.write('        .fd(exp_descr),\n')
        fh.write('\n')
        fh.write('        .valid(exp_take),\n')
        fh.write('        .word(exp_st_tdata),\n')
        fh.write('\n')
        fh.write('        .wr_file(1\'b0),\n')
        fh.write('\n')
        fh.write('        .rdy_i(1\'b1),\n')
        fh.write('        .rdy_o()\n')
        fh.write('        );\n')
        fh.write('\n')
        fh.write('    grc_word_writer #(\n')
        fh.write('        .LISTEN_ONLY(1),\n')
        fh.write('        .ARRAY_LENGTH(1024),\n')
        fh.write('        .NUM_BYTES(8)\n')
        fh.write('        )\n')
        fh.write('    u_downselect_wr\n')
        fh.write('    (\n')
        fh.write('        .clk(clk),\n')
        fh.write('        .sync_reset(reset_int),\n')
        fh.write('        .enable(1\'b1),\n')
        fh.write('\n')
        fh.write('        .fd(down_descr),\n')
        fh.write('\n')
        fh.write('        .valid(down_take),\n')
        fh.write('        .word(down_st_tdata),\n')
        fh.write('\n')
        fh.write('        .wr_file(1\'b0),\n')
        fh.write('\n')
        fh.write('        .rdy_i(1\'b1),\n')
        fh.write('        .rdy_o()\n')
        fh.write('        );\n')
        fh.write('\n')
        fh.write('    grc_word_writer #(\n')
        fh.write('        .LISTEN_ONLY(1),\n')
        fh.write('        .ARRAY_LENGTH(1024),\n')
        fh.write('        .NUM_BYTES(8)\n')
        fh.write('        )\n')
        fh.write('    u_final_wr\n')
        fh.write('    (\n')
        fh.write('        .clk(clk),\n')
        fh.write('        .sync_reset(reset_int),\n')
        fh.write('        .enable(1\'b1),\n')
        fh.write('\n')
        fh.write('        .fd(final_descr),\n')
        fh.write('\n')
        fh.write('        .valid(final_take),\n')
        fh.write('        .word(final_st_tdata),\n')
        fh.write('\n')
        fh.write('        .wr_file(1\'b0),\n')
        fh.write('\n')
        fh.write('        .rdy_i(1\'b1),\n')
        fh.write('        .rdy_o()\n')
        fh.write('        );\n')
        fh.write('\n')
        fh.write('`endif\n')
        fh.write('\n')
        fh.write('\n')
        fh.write('endmodule\n')

    return file_name

class Channelizer(object):
    """
        Implements channelizer class.  It is used to fully design the LPF of the channelizer,
        generate diagnostic plots, and processing of signal streams.

        * It includes both critically sampled and 2X sampled channelizers.

        * M : int  : Number of channels.
        * pbr : float : passband ripple in dB.
        * sba : float : stopband attenuation in dB.
        *
    """
    def __init__(self, M=64, Mmax=None, pbr=.1, sba=-80, taps_per_phase=32, gen_2X=True, qvec_coef=(25, 24),
                 qvec=(18, 17), desired_msb=None, K_terms=K_default, offset_terms=offset_default, fc_scale=1., 
                 tbw_scale=.5, taps=None):

        self.taps_per_phase = taps_per_phase
        self.qvec_coef = qvec_coef
        self.qvec = qvec

        self.gen_2X = gen_2X
        self.M = M
        self.Mmax = Mmax
        self.Mmax = M if Mmax is None else Mmax

        self.sba = sba
        self.pbr = pbr
        self.desired_msb = desired_msb
        fc = 1. / M
        self.fc = fc * fc_scale
        self.fc_scale = fc_scale
        self.rate = 2 if self.gen_2X else 1
        self.tbw_scale = tbw_scale

        if taps is None:
            self.num_taps = M * taps_per_phase
            taps = self.gen_float_taps(gen_2X, K_terms, offset_terms, M)
        else:
            self.num_taps = len(taps)

        self.gen_fixed_filter(taps, self.desired_msb)

        # generating a 2X filter.
        self.paths = M

    def gen_float_taps(self, gen_2X, K_terms, offset_terms, M):
        self.rate = 1
        if gen_2X:
            self.rate = 2

        self.K = K_terms[M]
        self.offset = offset_terms[M]
        taps = self.tap_equation(M)

        return taps

    def plot_psd(self, fft_size=1024, taps=None, freq_vector=None, title=None, miny=None, pwr_pts=None,
                 freq_pts=None, savefig=False, omega_scale=1, xlabel=df_str):

        """
            Helper function that plot the frequency response of baseband filter.
        """
        h_log, omega = self.gen_psd(fft_size, taps, freq_vector)
        # zoom in on passband
        plot_psd_helper((omega*omega_scale, h_log), title=title, miny=miny, plot_on=True, savefig=savefig, pwr_pts=pwr_pts,
                        freq_pts=freq_pts, xprec=4, xlabel=xlabel, dpi=dpi)

        return 0

    def gen_psd(self, fft_size=1024, taps=None, freq_vector=None):
        """
            Helper generates the PSD of the baseband filter
        """
        if taps is None:
            taps = self.taps

        step = 2. / fft_size
        if freq_vector is None:
            # this vector is normalized frequency.
            freq_vector = np.arange(-1., 1., step)

        omega, h = sp.signal.freqz(taps, worN=freq_vector * np.pi)

        # whole = True
        h_log = 20. * np.log10(np.abs(h))
        h_log -= np.max(h_log)

        omega /= np.pi

        return h_log, omega

    def plot_comparison(self, savefig=False, title=None):
        """
            Method plots the comparison of M/2 and M channelizer filter designs.
        """
        fig = plt.figure()
        plt.tight_layout()
        ax = fig.add_subplot(111)
        miny = -200
        pwr_pts = SIX_DB

        fft_size = 8192

        taps_1x = self.gen_taps(gen_2X=False)
        taps_2x = self.gen_taps(gen_2X=True)

        hlog_1x, omega = self.gen_psd(fft_size, taps_1x)
        hlog_2x, _ = self.gen_psd(fft_size, taps_2x)

        plot_psd(ax, omega, hlog_1x, pwr_pts=None, label=r'$\sf{M Channelizer}$', miny=miny, labelsize=18)
        plot_psd(ax, omega, hlog_2x, pwr_pts=pwr_pts, label=r'$\sf{M/2\ Channelizer}$', miny=miny, labelsize=18)

        if savefig:
            fig.savefig('plot_compare2.png', figsize=(12, 10))
        else:
            fig.canvas.draw()

    def plot_psd_single(self, savefig=False, title=None):

        fig = plt.figure()
        ax = fig.add_subplot(111)
        miny = -200
        pwr_pts = SIX_DB

        fft_size = 8192
        taps_2x = self.gen_taps(gen_2X=True)
        hlog_2x, omega = self.gen_psd(fft_size, taps_2x)
        plot_psd(ax, omega, hlog_2x, pwr_pts=pwr_pts, title=r'$M/2 \sf{\ Channelizer Filter PSD}$', miny=miny, labelsize=20)

        plt.tight_layout()
        if savefig:
            fig.savefig('plot_psd_single.png', figsize=(12, 10), dpi=dpi)
        else:
            fig.canvas.draw()


    def gen_poly_partition(self, taps):
        """
            Returns the polyphase partition of the PFB filter
        """
        return np.reshape(taps, (self.M, -1), order='F')

    def gen_fixed_filter(self, taps, desired_msb=None):
        """
            Generates the fixed-point representation of the PFB filter coefficients
        """
        max_coeff_val = (2**(self.qvec_coef[0] - 1) - 1) * (2 ** -self.qvec_coef[1])

        taps_gain = max_coeff_val / np.max(np.abs(taps))
        taps *= taps_gain
        # M = self.M  #len(taps) // self.taps_per_phase

        taps_fi = (taps * (2 ** self.qvec_coef[1])).astype(np.int)
        poly_fil = np.reshape(taps_fi, (self.M, -1), order='F')
        max_input = 2**(self.qvec[0] - 1) - 1

        # compute noise and signal gain.
        n_gain = np.max(np.sqrt(np.sum(np.abs(poly_fil)**2, axis=1)))
        s_gain = np.max(np.abs(np.sum(poly_fil, axis=1)))

        snr_gain = 20. * np.log10(s_gain / n_gain)
        path_gain = s_gain #np.max(np.abs(np.sum(poly_fil, axis=1)))
        bit_gain = nextpow2(np.max(s_gain))

        gain_msb = nextpow2(s_gain)
        max_coef_val = 2.**gain_msb - 1
        in_use = s_gain / max_coef_val

        max_value = np.max(s_gain) * np.max(max_input)
        num_bits = fp_utils.ret_num_bitsS(max_value)
        msb = num_bits - 1

        if in_use > .9:
            new_b = poly_fil
            delta_gain = 1
        else:
            # note we are scaling down here hence the - 1
            msb = msb - 1
            delta_gain = .5 * (max_coef_val / s_gain)
            new_b = np.floor(poly_fil * delta_gain).astype(int)
            s_gain = np.abs(np.max(np.sum(new_b, axis=1)))
            path_gain = np.max(np.abs(np.sum(new_b, axis=1)))
            bit_gain = nextpow2(path_gain)

        poly_fil = new_b
        if desired_msb is not None:
            if msb > desired_msb:
                diff = msb - desired_msb
                poly_fil = poly_fil >> diff
                msb = desired_msb

        taps_fi = np.reshape(poly_fil, (1, -1), order='F')
        self.taps_fi = taps_fi
        self.poly_fil_fi = poly_fil
        self.poly_fil = poly_fil * (2 ** -self.qvec_coef[1])
        self.taps = taps
        self.taps_per_phase = np.shape(self.poly_fil)[1]
        self.fil_msb = msb
        self.nfft = np.shape(self.poly_fil)[0]
        return (s_gain, n_gain, snr_gain, path_gain, bit_gain)

    @property
    def pfb_msb(self):
        return self.fil_msb

    def erfc(self, x):
        # save the sign of x
        sign = [1 if val >= 0 else -1 for val in x]
        x = np.abs(x)

        # constants
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        # A&S formula 7.1.26
        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * np.exp(-x * x)
        ret_val = 1 - sign * y
        return ret_val

    def tap_equation(self, fft_size, K=None, offset=None):
        # using root raised erf function to generate filter prototype
        # less control but much faster option for very large filters.
        # Perfectly fine for standard low-pass filters. Link to code
        # effectively use twiddle algorithm to get the correct cut-off
        # frequency
        # http://www.mathworks.com/matlabcentral/fileexchange/15813-near-
        # perfect-reconstruction-polyphase-filterbank

        if K is None:
            K = self.K

        if offset is None:
            offset = self.offset

        F = np.arange(self.num_taps)
        F = np.double(F) / len(F)

        MTerm = np.round((self.fc_scale * (1. / fft_size))**-1)

        x = K * (MTerm * F - offset)
        A = np.sqrt(0.5 * self.erfc(x))

        N = len(A)
        idx = np.arange(N // 2)

        A[N - idx - 1] = np.conj(A[1 + idx])
        A[N // 2] = 0

        # this sets the appropriate -6.02 dB cut-off point required for the channelizer
        db_diff = SIX_DB - 10 * np.log10(.5)
        exponent = 10 ** (-db_diff / 10.)

        A = A ** exponent

        b = np.fft.ifft(A)
        b = (np.fft.fftshift(b)).real
        b /= np.sum(b)

        return b

    def gen_fil_params(self, start_size=8, end_size=4096, K_init=13., fc_scale=FC_SCALE, tbw_scale=TBW_SCALE):
        """
            Determines optimum K values and required MSB values for varying FFT sizes, given filter
            corner frequency and transition bandwidth.
        """

        end_bits = int(np.log2(end_size))
        start_bits = int(np.log2(start_size))

        M_vec = 1 << np.arange(start_bits, end_bits + 1)
        K_terms = OrderedDict()
        offset_terms = OrderedDict()
        K_step = None
        msb_terms = OrderedDict()
        for M in M_vec:
            fc = (1. / M) * fc_scale
            trans_bw = (1./ M) * tbw_scale
            # if fc_scale == 1.:
            #     if self.rate == 1:
            #         trans_bw = 1 / (10. * M)
            #     else:
            #         trans_bw = 1 / (3.5 * M)
            # else:
            #     trans_bw = (1. / M) - fc
            self.num_taps = M * self.taps_per_phase
            self.M = M
            filter_obj = fil_utils.LPFilter(M=M, P=M, pbr=self.pbr, sba=self.sba, num_taps=self.num_taps, fc=fc,
                                            freqz_pts=FREQZ_PTS, num_iters=NUM_ITERS, fc_atten=SIX_DB, qvec=self.qvec,
                                            qvec_coef=self.qvec_coef, quick_gen=True, trans_bw=trans_bw, K=K_init, K_step=K_step,
                                            num_iters_min=100)

            K_terms[M] = filter_obj.K
            offset_terms[M] = filter_obj.offset
            taps = self.gen_float_taps(self.gen_2X, K_terms, offset_terms, M)
            msb_terms[M] = self.pfb_msb
            # use optimized paramater as the first guess on the next filter
            K_step = .01
            K_init = filter_obj.K
            self.gen_fixed_filter(taps)

        return K_terms, msb_terms, offset_terms

    def plot_filter(self, miny=-100, w_time=True, fft_size=16384):
        """
            Helper function that plots the PSD of the filter.
        """
        plot_title = "Channelizer Filter Impulse Response"
        limit = 4 * self.fc
        step = self.fc / 50.
        freq_vector = np.arange(-limit, limit, step)
        self.plot_psd(title=plot_title, pwr_pts=SIX_DB, fft_size=fft_size,
                      miny=-100, freq_vector=freq_vector)

        plot_title = "Channelizer Filter Impulse Response Full"
        self.plot_psd(title=plot_title, pwr_pts=SIX_DB, fft_size=fft_size, miny=-180)

    def gen_cen_freqs(self):

        half_step = 1. / self.paths
        full_step = half_step * 2
        num_steps = self.paths // 2 - 1

        init_list = [0]
        left_side = [-full_step - val * full_step for val in reversed(range(num_steps))]
        right_side = [full_step + val * full_step for val in range(num_steps + 1)]
        init_list = left_side + init_list + right_side

        return init_list

    def circ_shift(self, in_vec):
        """
            Implements the circular shift routine of the Channelizer algorithm
        """
        shift_out = []
        if self.gen_2X:
            for i, fil_arm in enumerate(in_vec):
                if i % 2:
                    shift_out.append(np.roll(fil_arm, self.paths // 2))
                else:
                    shift_out.append(fil_arm)

        else:
            shift_out = copy.copy(in_vec)

        return np.asarray(shift_out)

    def pf_run(self, sig_array, pf_bank, rate=1):
        """
            Runs the input array through the polyphase filter bank.
        """
        fil_out = []
        offset = self.paths // self.rate
        for j in range(rate):
            for i, input_vec in enumerate(sig_array):
                # remember in channelizer samples are fed to last path first -- it is a decimating filter.
                index = i + j * offset
                fil_out.append(signal.upfirdn(pf_bank[index, :], sig_array[i, :]))


        return np.asarray(fil_out)

    def trunc_vec(self, input_vec):
        mod_term = self.paths
        if self.gen_2X:
            mod_term = self.paths // 2
        trunc = len(input_vec) % mod_term
        if trunc > 0:
            input_vec = input_vec[:-trunc]

        return input_vec

    def ret_taps_fi(self):
        taps = self.gen_float_taps(self.gen_2X, self.K, self.M)
        ipdb.set_trace()

    def gen_tap_roms(self, path=None, file_prefix=None, roll_start=0, roll_offset=0, qvec_coef=(25, 24), qvec=(18, 17)):
        """
            Helper function that generates the coe files to be used with the PFB logic.
        """
        pfb_fil = copy.deepcopy(self.poly_fil_fi)
        # convert each column into ROM
        pfb_fil = pfb_fil.T
        qvec = (self.qvec_coef[0], 0)
        for idx, col in enumerate(pfb_fil):
            fi_obj = fp_utils.ret_dec_fi(col, qvec)
            if file_prefix is None:
                file_name = 'pfb_col_{}.coe'.format(idx)
            else:
                file_name = '{}_pfb_col_{}.coe'.format(file_prefix, idx)
            if path is not None:
                file_name = path + 'pfb_taps_{}/'.format(idx) + file_name

            fp_utils.coe_write(fi_obj, radix=16, file_name=file_name, filter_type=False)

    def gen_tap_file(self, file_name=None):
        """
            Helper function that generates a single file used for programming the internal ram
        """
        pfb_fil = copy.deepcopy(self.poly_fil_fi)
        pfb_fil = pfb_fil.T
        vec = np.array([])
        pad = np.array([0] * (self.Mmax - self.M))
        for i, col in enumerate(pfb_fil):
            col_vec = np.concatenate((col, pad))
            vec = np.concatenate((vec, col_vec))

        print(len(vec))
        write_binary_file(vec, file_name, 'i', big_endian=True)

    def gen_mask_vec(self, percent_active=None, bin_values=[42, 43, 56]):

        if percent_active is not None:
            np.random.seed(10)
            num_bins = int(self.M * percent_active)
            bin_values = np.random.choice(a=self.M, size=num_bins, replace=False)
            bin_values = np.sort(bin_values)
        # map this vector to 32 bit words  -- there are 64 words in 2048 bit vector for example.
        bit_vector = [0] * 65536
        num_words = int(np.ceil(self.M / 32))
        for value in bin_values:
            bit_vector[value] = 1

        words = np.reshape(bit_vector, (-1, 32))
        words = np.fliplr(words)
        words = words[:num_words, :]

        ret_val = np.atleast_1d(fp_utils.list_to_uint(words))
        return ret_val, bin_values

    def gen_mask_file(self, file_name=None, percent_active=None, bin_values=[42, 43, 56]):
        """
            Helper function that generates a single file used for programming the internal ram
        """
        vec, bin_values = self.gen_mask_vec(percent_active, bin_values)
        write_binary_file(np.array(vec), file_name, 'I', big_endian=True)
        return bin_values

    def gen_pf_bank(self):
        """
            Generates appropriate form of the polyphase filter bank to be used in the
            channelizer.
        """
        pf_bank = copy.copy(self.poly_fil)
        # modify pf_bank if gen_2X
        if self.rate == 2:
            pf_ret = []
            for i, pf_row in enumerate(pf_bank):
                if i < (self.paths // 2):
                    pf_ret.append(upsample(pf_row, 2, 0))
                else:
                    pf_ret.append(upsample(pf_row, 2, 1))

            return np.asarray(pf_ret)
        else:
            return np.asarray(pf_bank)

    def analysis_bank(self, input_vec, plot_out=False):
        """
            Function generates the analysis bank form of the channelizer.
        """
        # reshape input_vec

        input_vec = self.trunc_vec(input_vec)
        if plot_out:
            plot_psd_helper(input_vec, fft_size=1024, title='Buffer Sig', miny=None, w_time=True, markersize=None,
                            plot_on=True, savefig=True)


        sig_array = np.flipud(np.reshape(input_vec, (self.paths // self.rate, -1), order='F'))

        pf_bank = self.gen_pf_bank()
        num_plots = self.M
        if (plot_out):
            plt_sig = input_vec[:self.M * 10000]
            plt_array = np.reshape(plt_sig, (self.M // self.rate, -1), order='F')
            buff_array = []
            for j in range(10000):
                samp0 = plt_array[:, j]
                temp = np.concatenate((samp0, samp0))
                buff_array.extend(temp.tolist())


        fil_out = self.pf_run(sig_array, pf_bank, self.rate)

        if (plot_out):
            plt_array = np.reshape(fil_out[:,:], (1, -1), order='F').flatten()
            plt_array = plt_array[:self.M * 100000]
            # for ii in range(num_plots):
            plot_psd_helper(plt_array, title='PFB Sig', miny=None, w_time=True, markersize=None,
                            plot_on=True, savefig=True)

        # now perform circular shifting if this is a 2X filter bank.
        shift_out = self.circ_shift(fil_out.transpose())
        if (plot_out):
            shift_tp = shift_out.transpose()
            plt_array = np.reshape(shift_tp, (1, -1), order='F').flatten()
            plt_array = plt_array[:self.M * 100000]
            plot_psd_helper(plt_array, fft_size=1024, title='Circ Shift Sig', miny=None, w_time=True, markersize=None,
                            plot_on=True, savefig=True)

        chan_out = np.fft.fftshift(np.fft.ifft(shift_out, axis=1), axes=1)

        if (plot_out):
            for ii in range(num_plots):
                fig, (ax0, ax1) = plt.subplots(2)
                ax0.plot(np.real(chan_out[:, ii]))
                ax1.plot(np.imag(chan_out[:, ii]))
                title = 'IFFT Output #{}'.format(ii)
                fig.canvas.set_window_title(title)
                fig.savefig(title + '.png', figsize=(12, 10))

        return chan_out.transpose()

    def synthesis_bank(self, input_vec, plot_out=False):
        """
            Function generates the synthesis bank of the channelizer.
        """
        input_vec = self.trunc_vec(input_vec)
        sig_array = np.reshape(input_vec, (self.paths, -1), order='F')
        pf_bank = self.gen_pf_bank()

        fft_out = np.fft.ifft(self.paths * sig_array, axis=0)

        shift_out = self.circ_shift(fft_out.transpose())
        fil_out = self.rate * self.pf_run(shift_out.transpose(), pf_bank, 1)

        if self.rate == 2:
            offset = self.paths // 2
            for i in range(self.paths // 2):
                fil_out[i, :] = (fil_out[i, :] + fil_out[i + offset, :])

            fil_out = fil_out[:offset, :]

        return np.reshape(fil_out, (1, -1), order='F').flatten()

    def plot_phase_csum(self, pf_up=None):

        if pf_up is None:
            pf_up = self.gen_usample_pf()

        (freq_path, phase_path, ref_phase) = self.gen_freq_phase_profiles(pf_up)

        nfft = np.shape(pf_up)[1]
        freq1 = np.fft.fftshift(np.fft.fft(pf_up, nfft, 1))

        freq_sum = np.sum(freq1, 1)
        freq_abs = np.abs(freq_sum)
        phase_sum = np.unwrap(np.angle(freq_sum)) / (2 * np.pi)
        arg1 = phase_sum - ref_phase

        fig = plt.figure()
        ax = Axes3D(fig)
        # ax = fig.add_subplot(111, projection='3d')

        exp_vec = np.exp(1j * 2 * np.pi * arg1)
        x_vec = np.imag(freq_abs * exp_vec)
        y_vec = np.arange(-1, 1., 2. / len(freq_abs))
        z_vec = np.real(freq_abs * exp_vec)
        ax.plot(x_vec, y_vec, z_vec)  # , rstride=10, cstride=10)
        ax.set_xlabel(r'$\sf{Imag}')
        ax.set_ylabel(r'$\sf{Freq}')
        ax.set_zlabel(r'$\sf{Real}')
        ax.view_init(30, 10)
        ax.set_ylim(-1, 1.)
        ax.set_xlim(-1, 1)
        ax.set_zlim(-1, 1)
        title = 'Phase Rotators'
        fig.savefig(title+'.png', fig_size=(12, 10))

    def gen_usample_pf(self):

        coef_array = []
        # coef_array = self.filter.poly_fil
        # Upsample Filter Coefficients based on M.
        pf_up = []
        if self.gen_2X:
            b_temp = self.taps
            x_vec = np.arange(0, len(b_temp))
            x_vec2 = np.arange(0, len(b_temp), .5)
            b_temp = sp.interp(x_vec2, x_vec, b_temp) / 2.
            coef_array = self.gen_poly_partition(b_temp)
        else:
            coef_array = self.poly_fil

        for i, path_taps in enumerate(coef_array):
            # upsample path taps so that the paths show the prospective "paddle wheels"
            temp = upsample(path_taps, self.paths)
            # samples.
            pf_up.append(np.roll(temp, i))

        max_gain = np.max(np.sum(pf_up, 1))
        pf_up = [max_gain / np.sum(value) * value for value in pf_up]

        return pf_up

    def gen_freq_phase_profiles(self, pf_up=None):

        if pf_up is None:
            pf_up = self.gen_usample_pf()

        freq_path = []
        phase_path = []
        for i, taps_bb in enumerate(pf_up):
            temp = np.fft.fftshift(np.fft.fft(taps_bb))
            freq_path.append(np.abs(temp))
            phase_path.append(np.unwrap(np.angle(temp)) / (2 * np.pi))

        ref_phase = phase_path[0]

        return (freq_path, phase_path, ref_phase)

    def gen_animation(self, fps=15, dpi_val=300, mpeg_file='test.mp4', sleep_time=.02):
        sel = 1
        ph_steps = 300
        inc = sel / float(ph_steps)
        num_frames = 10
        std_dev = np.sqrt(.02 / self.paths)
        mean = .5 / self.paths
        sig_bws = np.abs(std_dev * np.random.randn(self.paths) + mean)

        sig_bws = [value if value > .1 else .1 for value in sig_bws]
        cen_freqs = self.gen_cen_freqs()
        mod_obj = QAM_Mod()
        sig = None
        for ii, (sig_bw, cen_freq) in enumerate(zip(sig_bws, cen_freqs)):  # cen_freqs:
            temp, _ = mod_obj.gen_frames(num_frames=num_frames, cen_freq=cen_freq, frame_space_mean=0, frame_space_std=0, sig_bw=sig_bw)
            idx = np.argmax(np.abs(temp))

            lidx = idx - 5000
            ridx = lidx + 20000

            if ii == 0:
                sig = temp[lidx:ridx]
            else:
                sig_temp = temp[lidx:ridx]
                sig[:len(sig_temp)] += sig_temp

        (sig, _) = gen_utils.add_noise_pwr(30, sig)
        
        plot_psd_helper(sig)
        FFMpegWriter = manimation.writers['ffmpeg']  # ['ffmpeg']  avconv
        # metadata = dict(title='Movie Test', artist='Matplotlib', comment='Movie support!')
        metadata = dict(artist='Matplotlib')

        writer = FFMpegWriter(fps=fps, codec="libx264", bitrate=-1,metadata=None)

        pf_up = self.gen_usample_pf()
        fig = plt.figure()
        fig.set_tight_layout(False)

        # writer = MovieWriter(fig, frame_format= , fps=fps)
        ax = fig.add_subplot(221, projection='3d')
        ax.xaxis.labelpad = 10
        ax.yaxis.labelpad = 10
        ax1 = fig.add_subplot(222, projection='3d')
        ax1.xaxis.labelpad = 10
        ax1.yaxis.labelpad = 10
        ax2 = fig.add_subplot(223, projection='polar')
        ax3 = fig.add_subplot(224)
        fig.subplots_adjust(left=.08, bottom=.13, top=.95, right=.96, hspace=.4, wspace=.2)
        y_vec = np.arange(-1, 1., 2. / np.shape(pf_up)[1])

        phase_vec = np.arange(0, sel + 5 * inc, inc)
        # pad the end with the last phase for 30 frames
        phase_vec = np.concatenate((phase_vec, np.array([phase_vec[-1]]*30)))

        (_, sig_psd) = gen_psd(sig, fft_size=len(y_vec))
        with writer.saving(fig, mpeg_file, dpi_val):
            for phase in phase_vec:
                if phase > 1:
                    m = 1
                else:
                    m = phase
                indices = np.arange(0, self.M)
                rot = np.exp(1j * 2 * np.pi * (indices / float(self.M)) * m)
                pf_up3 = [rot_value * row for (rot_value, row) in zip(rot, pf_up)]
                (freq_path, phase_path, ref_phase) = self.gen_freq_phase_profiles(pf_up3)
                x_sum = 0
                z_sum = 0
                for i, (f_path, p_path) in enumerate(zip(freq_path, phase_path)):
                    arg1 = p_path - ref_phase

                    # x term is the imaginary component frequency Response of path ii
                    # rotated by the phase response of path ii
                    exp_vec = np.exp(1j * 2 * np.pi * arg1)
                    x_vec = f_path * np.imag(exp_vec)
                    z_vec = f_path * np.real(exp_vec)
                    x_sum += x_vec
                    z_sum += z_vec
                    if i == 0:
                        ax.set_xlabel(r'$\sf{Imag}$')
                        ax.set_ylabel(r'$\sf{Freq}$')
                        ax.set_zlabel(r'$\sf{Real}$')
                        ax.view_init(30, 10)
                        ax.set_ylim(-1, 1.)
                        ax.set_xlim(-1, 1)
                        ax.set_zlim(-1, 1)
                        ax.set_title(r'$\sf{Phase\ Arms}$')
                        ax.plot(np.array([0, 0]), np.array([0, 0]), np.array([-1.2, 1.2]), color='k', linewidth=.5)
                        ax.plot(np.array([0, 0]), np.array([-1.2, 1.2]), np.array([0, 0]), color='k', linewidth=.5)
                        ax.plot(np.array([-1.2, 1.2]), np.array([0, 0]), np.array([0, 0]), color='k', linewidth=.5)

                    # ax.plot_wireframe(x_vec, y_vec, z_vec)  # , rstride=10, cstride=10)
                    ax.plot(x_vec, y_vec, z_vec, linewidth=.9)  # , rstride=10, cstride=10)

                x_sum = x_sum / self.paths
                z_sum = z_sum / self.paths

                ax1.set_xlabel(r'$\sf{Imag}$')
                ax1.set_ylabel(r'$\sf{Freq}$')
                ax1.set_zlabel(r'$\sf{Real}$')
                ax1.view_init(30, 10)
                ax1.set_ylim(-1, 1.)
                ax1.set_xlim(-1, 1)
                ax1.set_zlim(-1, 1)
                ax1.set_title(r'$\sf{Phase Coherent Sum}$')
                ax1.plot([0, 0], [0, 0], [-1.2, 1.2], color='k', linewidth=.5)
                ax1.plot([0, 0], [-1.2, 1.2], [0, 0], color='k', linewidth=.5)
                ax1.plot([-1.2, 1.2], [0, 0], [0, 0], color='k', linewidth=.5)
                ax1.plot(x_sum, y_vec, z_sum, linewidth=.9)

                rot = [np.exp(1j * 2 * np.pi * (ii / float(self.paths)) * m) for ii in range(self.paths)]

                compass(np.real(rot), np.imag(rot), ax2)
                ax2.set_xlabel(r'$\sf{Phase\ rotator\ progression}')

                fil = z_sum + 1j * x_sum
                fil_log = 20 * np.log10(np.abs(fil))
                out_log = sig_psd + fil_log
                plot_psd(ax3, y_vec, out_log, miny=-85, maxy=15, titlesize=12, labelsize=10, xlabel=df_str)

                # fig.subplots_adjust(top=.95)   # tight_layout(h_pad=.5)
                writer.grab_frame()
                time.sleep(sleep_time)
                ax.clear()
                ax1.clear()
                ax2.clear()
                ax3.clear()

        plt.close(fig)

    def gen_properties(self, plot_on=True):
        """
            Generates plots related to the analysis bank of the designed filter.
        """
        self.paths = self.M
        # Upsample Filter Coefficients based on M.
        pf_up = self.gen_usample_pf()

        # now insert the extra delay if this is a 2X implementation.
        b_nc = np.fft.fftshift(self.taps)
        bb1 = np.reshape(b_nc, (self.paths, -1), order='F')
        nfft = len(self.taps)

        fig, ax = plt.subplots()
        title = r'$\sf{Polyphase\ Filter\ Phase\ Profiles}$'

        x_vec = np.arange(-1, 1., (2. / nfft)) * self.paths
        phs_sv = []
        for i in range(self.paths):
            fft_out = np.fft.fftshift(np.fft.fft(pf_up[i], nfft))
            phs = np.unwrap(np.angle(fft_out))
            temp = phs[nfft // 2]
            phs_sv.append(temp)
            ax.plot(x_vec, phs - temp)

        ax.set_xlabel('Nyquist Zones')
        ax.set_ylabel('Phase (radians)')
        ax.set_title(title)
        fig.canvas.set_window_title(title)
        fig.savefig(title, figsize=(12, 10))

        title = r'$\sf{Reference\ Partition}$'
        fig, ax = plt.subplots()
        ax.stem(bb1[0])
        ax.set_title(r'$\sf{Polyphase Filter\ --\ Reference\ Partition}$')
        fig.canvas.set_window_title(title)
        fig.savefig(title, figsize=(12, 10))

        if plot_on:
            (freq_path, phase_path, ref_phase) = self.gen_freq_phase_profiles(pf_up)

            ax = []
            fig = plt.figure()
            for i, (f_path, p_path) in enumerate(zip(freq_path, phase_path)):
                arg1 = p_path - ref_phase
                # x term is the imaginary component frequency Response of path ii
                # rotated by the phase response of path ii
                exp_vec = np.exp(1j * 2 * np.pi * arg1)
                x_vec = np.imag(f_path * exp_vec)
                y_vec = np.arange(-1, 1., 2. / len(f_path))
                z_vec = np.real(f_path * exp_vec)
                ax.append(fig.add_subplot(2, self.paths / 2, i + 1, projection='3d'))
                ax[i].plot_wireframe(x_vec, y_vec, z_vec)  # , rstride=10, cstride=10)
                ax[i].set_xlabel('Imag')
                ax[i].set_ylabel('Freq')
                ax[i].set_zlabel('Real')
                ax[i].view_init(30, 10)
                ax[i].set_ylim(-1, 1.)
                ax[i].set_xlim(-1, 1)
                ax[i].set_zlim(-1, 1)

            fig.savefig('Properties.png', figsize=(12, 10))

def gen_test_sig(file_name=None, bursty=False):

    cen_freqs = [-.20, -.5, .25, .75]
    sig_bws = [.1, .10, .05, .125]
    amps = [.2, .5, .7, .3]
    roll = [1000, 3000, 4000, 5000]

    # bursty
    if bursty:
        num_frames = 10
        packet_size = 100
        frame_space_mean = 20000
        roll = [1000, 3000, 4000, 5000]
    else:
        num_frames = 1
        packet_size = 10000
        frame_space_mean = 0
        roll = [0, 0, 0, 0]

    sig_list = []
    if file_name is None:
        file_name = SIM_PATH + 'sig_store_test8.bin'
    mod_obj = QAM_Mod(frame_mod='qam16', xcode_shift=2, ycode_shift=2, packet_size=packet_size)
    for ii, (cen_freq, sig_bw, amp, shift) in enumerate(zip(cen_freqs, sig_bws, amps, roll)):
        temp, _ = mod_obj.gen_frames(num_frames=num_frames, cen_freq=cen_freq, frame_space_mean=frame_space_mean,
                                     frame_space_std=0, sig_bw=sig_bw, snr=200)

        if not bursty:
            idx = np.where(np.abs(temp) > .5)[0][0]
            temp = np.asarray(temp[idx:idx + 1000000])
        temp *= (amp * .1)
        temp = np.roll(temp, shift)
        sig_list.append(temp)

    min_length = min([len(temp) for temp in sig_list])
    sig = 0
    for temp in sig_list:
        sig += temp[:min_length]
    sig, _ = add_noise_pwr(80, sig)
    sig_fi = fp_utils.ret_fi(sig, qvec=(16, 15), overflow='saturate')

    plot_psd_helper(sig_fi.vec, title='Input Spectrum', savefig=True, w_time=True)
    write_complex_samples(sig_fi.vec, file_name, False, 'h', big_endian=True)
    plt.show()


def test_8_chan():

    plt.close('all')
    gen_test_sig(4, GEN_2X)

    M = 8
    chan = Channelizer(M=M, gen_2X=GEN_2X, qvec=QVEC, qvec_coef=QVEC_COEF, fc_scale=FC_SCALE, taps=TAPS)

    # generate test signal.
    file_name = SIM_PATH + 'sig_store_{}_float3.bin'.format(M)
    sig = read_complex_samples(file_name, q_first=False, format_str='h', offset=0, num_samps=None, big_endian=True)

    plot_psd_helper(sig, title='Input Signal', w_time=True, savefig=True)

    chan_out = chan.analysis_bank(sig, plot_out=True)
    chan.gen_tap_roms()
    ser_sig = np.reshape(chan_out, (1, -1), order='F').flatten()
    plot_psd_helper(ser_sig, title='PFB Signal', w_time=True, savefig=True)
    orig_sig = chan.synthesis_bank(ser_sig, plot_out=False)
    plot_psd_helper(orig_sig, title='Final Signal', w_time=True, savefig=True)

    for i, chan_sig in enumerate(chan_out):
        str_val = 'Channel - {}'.format(i)
        plot_psd_helper(chan_sig, title=str_val, w_time=True, savefig=True)

    chan.plot_filter()


def gen_corr_table(num_bits=6):

    qvec = (num_bits, num_bits)
    vec = fp_utils.comp_range_vec(qvec)
    new_vec = 2 ** -vec
    path = IP_PATH
    new_vec_fi = fp_utils.ret_dec_fi(new_vec, qvec=(16, 15), signed=0)
    print(vgen.gen_rom(path, new_vec_fi, rom_type='sp', rom_style='distributed', prefix='exp_shift_'))

    return new_vec_fi


def gen_samp_delay_coe(M):

    qvec = (36, 0)

    vec = np.array([0] * M)
    fi_obj = fp_utils.ret_dec_fi(vec, qvec)

    file_name = IP_PATH + '/sample_delay/sample_delay.coe'
    fp_utils.coe_write(fi_obj, radix=16, file_name=file_name, filter_type=False)

    file_name = IP_PATH + '/sample_ram/sample_ram.coe'

    ridx = 3 * M + 1
    vec = np.arange(1, ridx)  # np.array([0] * M * 3)
    fi_obj = fp_utils.ret_dec_fi(vec, qvec)
    fp_utils.coe_write(fi_obj, radix=16, file_name=file_name, filter_type=False)

    vec = np.array([0] * M)
    qvec = (36, 0)
    fi_obj = fp_utils.ret_dec_fi(vec, qvec)

    file_name = IP_PATH + '/circ_buff_ram/circ_buff_ram.coe'
    fp_utils.coe_write(fi_obj, radix=16, file_name=file_name, filter_type=False)

    file_name = IP_PATH + '/exp_averager_filter/exp_fil.coe'
    fil_vec = [1] * 64
    fi_obj = fp_utils.ret_dec_fi(fil_vec, (2, 0))
    fp_utils.coe_write(fi_obj, radix=16, file_name=file_name, filter_type=True)


def test_256_chan(gen_taps=False):

    plt.close('all')

    M = 256
    chan = Channelizer(M=M, gen_2X=GEN_2X, taps_per_phase=TAPS_PER_PHASE, desired_msb=PFB_MSB,
                       qvec=QVEC, qvec_coef=QVEC_COEF, fc_scale=FC_SCALE, taps=TAPS)
    # chan.gen_properties(plot_on=False)

    file_name = SIM_PATH + '/sig_store_{}_taps.bin'.format(M)
    sig = read_complex_samples(file_name, False, 'f')

    print("Filter MSB = {}".format(chan.fil_msb))

    # generate test signal.
    chan_out = chan.analysis_bank(sig, plot_out=True)  #analysis:ignore
    chan.plot_filter()


def gen_taps(M, Mmax=512, gen_2X=True, taps_per_phase=TAPS_PER_PHASE, pfb_msb=40):

    chan = Channelizer(M=M, Mmax=Mmax, gen_2X=GEN_2X, taps_per_phase=taps_per_phase,
                       desired_msb=PFB_MSB, qvec=QVEC, qvec_coef=QVEC_COEF, fc_scale=FC_SCALE, taps=TAPS)
    print("Filter MSB = {}".format(chan.fil_msb))
    path = SIM_PATH
    file_name = path + 'M_{}_taps.bin'.format(M)
    print(file_name)
    chan.gen_tap_file(file_name)


# def gen_logic(M, gen_2X=True, taps_per_phase=TAPS_PER_PHASE, sample_width=18):

#     # from cStringIO import StringIO
#     import shutil
#     import phy_tools.fil_utils as fil_utils

#     plt.close('all')

#     chan = Channelizer(M=M, gen_2X=GEN_2X, taps_per_phase=TAPS_PER_PHASE, desired_msb=pfb_msb,
#                        qvec=qvec, qvec_coef=QVEC_COEF, fc_scale=FC_SCALE)
#     gen_taps(M, gen_2X, taps_per_phase)

#     print("Filter MSB = {}".format(chan.filter.msb))

#     # c_str = StringIO()
#     # c_str.reset()
#     # # store c_str to file.
#     # with open('../verilog/file.xml', 'w') as fh:
#     #     c_str.seek(0)
#     #     shutil.copyfileobj(c_str, fh)

#     # generate half-band filter
#     fil_obj = fil_utils.LPFilter(num_taps=40, half_band=True)
#     fil_obj.gen_fixed_filter(coe_file=IP_PATH + '/hb_fil/hb_fil.coe')

#     print("HB Filter MSB = {}".format(fil_obj.msb))

#     fil_obj.plot_psd()


def populate_fil_table(start_size=8, end_size=2048, taps_per_phase=TAPS_PER_PHASE, fc_scale=FC_SCALE, 
                       gen_2X=GEN_2X, tbw_scale=TBW_SCALE):

    # K_init = 20. if gen_2X else 40.
    K_init = 40.

    chan = Channelizer(M=8, gen_2X=gen_2X, taps_per_phase=taps_per_phase, qvec=QVEC,
                       qvec_coef=QVEC_COEF, fc_scale=fc_scale, tbw_scale=tbw_scale, taps=TAPS)

    K_terms, msb_terms, offset_terms = chan.gen_fil_params(start_size, end_size, fc_scale=fc_scale, K_init=K_init, 
                                                           tbw_scale=tbw_scale)

    print("K_terms = {}".format(K_terms))
    print("msb_terms = {}".format(msb_terms))
    print("offset_terms = {}".format(offset_terms))

    return K_terms, msb_terms, offset_terms

def gen_animation():
    chan_obj = Channelizer(M=4, taps_per_phase=TAPS_PER_PHASE, gen_2X=False, qvec=QVEC,
                           qvec_coef=QVEC_COEF, fc_scale=FC_SCALE, taps=TAPS)
    chan_obj.gen_animation()

def find_best_terms(gen_2X=True, qvec=QVEC):
    # M = [4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384]
    # M = 2 ** np.arange(2, 7)
    M = 64
    chan_obj = Channelizer(M=M, taps_per_phase=TAPS_PER_PHASE, gen_2X=GEN_2X, qvec=QVEC,
                           qvec_coef=QVEC_COEF, fc_scale=FC_SCALE, tbw_scale=TBW_SCALE, K_terms=K_default, taps=TAPS)

    K_terms, msb_terms, offset_terms = chan_obj.gen_fil_params(8, 2048)

    print("K_terms = {}".format(K_terms))
    print("msb_terms = {}".format(msb_terms))
    print("offset_terms = {}".format(offset_terms))

def gen_input_buffer(Mmax=512, path=IP_PATH):

    cnt_width = 16  #  input buffers are fixed code -- always use 16 bit counters
    print("==========================")
    print(" input buffer")
    print("")
    ram_out = vgen.gen_ram(path, ram_type='dp', memory_type='read_first', ram_style='block')
    print(ram_out)
    cnt_in = vgen.gen_aligned_cnt(path, cnt_width=cnt_width, tuser_width=0, tlast=False, start_sig=False, dwn_cnt=True)
    print(cnt_in)
    cnt_out = vgen.gen_aligned_cnt(path, cnt_width=cnt_width, tuser_width=0, tlast=False, start_sig=True, use_af=True,
                                   almost_full_thresh=16, fifo_addr_width=5)
    print(cnt_out)
    print("==========================")
    print("")

def gen_output_buffer(Mmax=512, path=IP_PATH):

    print("==========================")
    print(" output buffer")
    print("")
    cnt_width = int(np.ceil(np.log2(Mmax - 1)))
    ram_out = vgen.gen_ram(path, ram_type='dp', memory_type='read_first', ram_style='block')
    print(ram_out)
    # cnt_in = vgen.gen_aligned_cnt(path, cnt_width=cnt_width, tuser_width=0, tlast=True, start_sig=False, dwn_cnt=False)
    # vgen.gen_aligned_cnt(path, cnt_width=16, tuser_width=0, tlast=False, incr=1, tot_latency=None, start_sig=False, cycle=False, upper_cnt=False, prefix='', dwn_cnt=False, load=False, dport=True, startup=True, almost_full_thresh=None)
    # print(cnt_in)
    cnt_out = vgen.gen_aligned_cnt(path, cnt_width=cnt_width, tuser_width=0, tlast=False, start_sig=True, use_af=True,
                                   almost_full_thresh=16, fifo_addr_width=5)
    print(cnt_out)
    _, dsp_name = vgenx.gen_dsp48E1(path, 'output_add', opcode='A+D', a_width=QVEC[0], d_width=QVEC[0], dreg=1, areg=1, creg=2, mreg=1, breg=0, preg=1, rnd=True, p_msb=QVEC[0], p_lsb=1)
    print(dsp_name)
    print("==========================")
    print("")


def gen_one_hot(Mmax=512, path=IP_PATH):
    print("==========================")
    print(" one hot encoder")
    print("")
    input_width = int(np.ceil(np.log2(Mmax-1)))
    one_hot_out = vgen.gen_one_hot(input_width, file_path=path)
    print(one_hot_out)
    print("==========================")
    print("")

def gen_downselect(Mmax=512, path=IP_PATH):
    print("==========================")
    print(" one hot encoder")
    print("")
    tuser_bits = calc_fft_tuser_width(Mmax)
    print("tuser_bits = {}".format(tuser_bits))
    downselect = adv_filter.gen_down_select(path, name='downselect', num_channels=Mmax, tuser_width=tuser_bits)
    print(downselect)
    print("==========================")
    print("")

def gen_mux(Mmax=512, path=IP_PATH):
    print("==========================")
    print(" pipelined mux")
    print("")
    input_width = Mmax
    mux_out = vgen.gen_pipe_mux(path, input_width, 1, mux_bits=3, one_hot=False, one_hot_out=False)
    print(mux_out)
    print("==========================")
    print("")

def gen_pfb(chan_obj, path=IP_PATH, fs=6.4E6):  # Mmax=512, pfb_msb=40, M=512, taps=None, gen_2X=GEN_2X):
    """
        Generates the logic for the Polyphase Filter bank
    """

    # path = IP_PATH
    print("==========================")
    print(" pfb filter")
    print("")

    print("K terms = {}".format(chan_obj.K))
    print("fc_scale = {}".format(FC_SCALE))
    pfb_fil = chan_obj.poly_fil_fi
    pfb_reshape = np.reshape(pfb_fil, (1, -1), order='F').flatten()
    qvec_int = (QVEC_COEF[0], 0)
    taps_fi = fp_utils.ret_dec_fi(pfb_reshape, qvec_int)

    mid_pt = len(taps_fi.vec) // 2
    print("Taps binary")
    [print(value) for value in taps_fi.bin[mid_pt-10:mid_pt+10]]

    fft_size=8192
    step = 1 / (32768 * 8)
    freq_vector = np.arange(-10. / chan_obj.M, 10. / chan_obj.M, step)
    omega_scale = (fs / 2) / chan_obj.M
    xlabel = r'$\sf{kHz}$'
    chan_obj.plot_psd(fft_size=fft_size, taps=None, freq_vector=freq_vector, title=r'$\sf{Filter\ Prototype}$', savefig=True,
                      pwr_pts=SIX_DB, miny=-120, omega_scale=omega_scale, xlabel=xlabel)

    pfb_out = adv_filter.gen_pfb(path, chan_obj.Mmax, taps_fi, input_width=chan_obj.qvec[0], output_width=chan_obj.qvec[0],
                                 taps_per_phase=chan_obj.taps_per_phase, pfb_msb=chan_obj.pfb_msb, 
                                 tlast=True, tuser_width=0,
                                 ram_style='block', prefix='', gen_2X=chan_obj.gen_2X)

    print(pfb_out)
    print("==========================")
    return pfb_out[0]

def gen_circ_buffer(Mmax=512, path=IP_PATH):
    print("======================")
    print("circular buffer")
    print("")
    ram_out = vgen.gen_ram(path, ram_type='dp', memory_type='read_first', ram_style='block')
    print(ram_out)
    fifo_out = vgen.gen_axi_fifo(path, tuser_width=0, tlast=True, almost_full=True, ram_style='distributed')
    print(fifo_out)
    print("======================")
    print("")

def gen_final_cnt(path=IP_PATH):
    print("======================")
    print("Final Count")
    print("")
    final_cnt = vgen.gen_aligned_cnt(path, cnt_width=16, tuser_width=24, tlast=True)
    print(final_cnt)
    print("======================")
    print("")


def gen_exp_shifter(chan_obj, avg_len=16, sample_fi=None, path=IP_PATH):
    print("=================================")
    print("exp shifter")
    print("")
    # generate correction ROM
    table_bits = fp_utils.ret_bits_comb(avg_len)
    frac_bits = int(np.ceil(np.log2(avg_len)))
    fft_shift_bits = 5
    qvec_in = (fft_shift_bits, 0)
    qvec_out = (fft_shift_bits + frac_bits, frac_bits)
    cic_obj = fil_utils.CICDecFil(M=avg_len, N=1, qvec_in=qvec_in, qvec_out=qvec_out)
    fil_out = vfilter.gen_cic_top(path, cic_obj, count_val=0, prefix='', tuser_width=0)
    fil_msb = fft_shift_bits + table_bits - 1

    fi_obj = fp_utils.ret_dec_fi([1.] * avg_len, qvec=(25, 0), overflow='wrap', signed=1)

    # generate fifo
    fifo_out = vgen.gen_axi_fifo(path, tuser_width=24, tlast=True, almost_full=True, ram_style='distributed')    
    print(fifo_out)
    print("================================")
    print("")

    exp_out = adv_filter.gen_exp_shift_rtl(path, chan_obj, cic_obj)
    print(exp_out)
    print("================================")
    print("")
    return exp_out

def gen_tones(M=512, lidx=30, ridx=31, offset=0, path=SIM_PATH):

    scale = np.max(np.abs((lidx, ridx)))
    tone_vec = np.arange(lidx, ridx, 1) / float(M / 2) + offset
    phase_vec = np.arange(lidx, ridx, 1) / (scale * np.pi)
    num_samps = 8192 * 64
    tones = [gen_comp_tone(num_samps, tone_value, phase_value) for (tone_value, phase_value) in zip(tone_vec, phase_vec)]
    sig = np.sum(tones, 0)
    sig = sig / (2. * np.max(np.abs(sig)))
    sig *= .5

    sig_fi = fp_utils.ret_fi(sig, qvec=(16, 15), overflow='saturate')

    plot_psd_helper(sig_fi.vec[:900], title='tone truth', miny=-100, savefig=True, plot_time=True, path=path)
    write_complex_samples(sig_fi.vec, path + 'sig_tones_{}.bin'.format(M), False, 'h', big_endian=True)

def gen_tones_vec(tone_vec, M=512, offset=0, path=SIM_PATH):

    omega = np.roll(gen_freq_vec(M)['w'], -M // 2)
    tones = np.array([omega[tone_idx] for tone_idx in tone_vec]) + offset

    scale = np.max(tone_vec)
    phase_vec = np.array(tone_vec) / (scale * np.pi)
    num_samps = 8192 * 256
    tones = [gen_comp_tone(num_samps, tone_value, phase_value) for (tone_value, phase_value) in zip(tones, phase_vec)]
    sig = np.sum(tones, 0)
    sig = sig / (2. * np.max(np.abs(sig)))
    sig *= .5

    sig_fi = fp_utils.ret_fi(sig, qvec=(16, 15), overflow='saturate')

    # plot_psd_helper(sig_fi.vec[:900], title='tone truth', miny=-100, savefig=True, plot_time=True, path=path)
    write_complex_samples(sig_fi.vec, path + 'sig_tones_{}.bin'.format(M), False, 'h', big_endian=True)

def gen_count(M=512):
    path = SIM_PATH

    num_samps = 8192 * 256
    count = np.arange(0, num_samps)
    count = count % M
    count = count + 1j * 0

    sig_fi = fp_utils.ret_fi(count, qvec=(16, 0), overflow='saturate')
    write_complex_samples(sig_fi.vec, path + 'sig_count_{}.bin'.format(M), False, 'h', big_endian=True)

def process_pfb_out(file_name, row_offset=128):
    """
        Helper function that ingests data from RTL simulation and plots the output of the PFB of the channelizer.
    """
    samps = read_binary_file(file_name, format_str='Q', big_endian=True)
    print(len(samps))
    if type(samps) is int:
        print('File does not exist')
        return -1

    if len(samps) == 0:
        print("Not enough samples in File")
        return -1

    mask_i = np.uint64(((1 << 16) - 1) << 16)
    mask_q = np.uint64((1 << 16) - 1)
    mask_bin_num = np.uint64(((1 << 24) - 1) << 32)

    i_sig = [int(samp & mask_i) >> 16 for samp in samps]
    q_sig = [samp & mask_q for samp in samps]
    fft_bin_sig = [int(samp & mask_bin_num) >> 32 for samp in samps]

    offset = np.where(np.array(fft_bin_sig) == 0)[0][0]

    store_sig = np.array(i_sig[offset:] )+ 1j * np.array(q_sig[offset:])

    write_complex_samples(store_sig, './raw_pfb_out.bin', q_first=False)

    i_sig = fp_utils.uint_to_fp(i_sig[offset:], qvec=(16, 15), signed=1, overflow='wrap')
    q_sig = fp_utils.uint_to_fp(q_sig[offset:], qvec=(16, 15), signed=1, overflow='wrap')
    fft_bin_sig = fft_bin_sig[offset:]

    M = np.max(fft_bin_sig) + 1
    print("M = {}".format(M))

    trunc = len(i_sig) % M
    if trunc:
        i_sig = i_sig.float[:-trunc]
        q_sig = q_sig.float[:-trunc]
        fft_bin_sig = fft_bin_sig[:-trunc]
    else:
        i_sig = i_sig.float
        q_sig = q_sig.float


    comp_sig = i_sig + 1j * q_sig
    plot_psd_helper(comp_sig, w_time=True, savefig=True, title='Interlace PFB', miny=-80)
    comp_rsh = np.reshape(comp_sig, (M, -1), 'F')
    comp_rsh = np.fft.ifft(comp_rsh, axis=0)

    resps = []
    wvecs = []
    time_sigs = []
    print(np.shape(comp_rsh))
    for ii, row in enumerate(comp_rsh):
        if row_offset < len(row):
            row = row[row_offset:]
        print(np.max(np.abs(row)))

        wvec, psd = gen_psd(row, fft_size=256, window='blackmanharris')
        resps.append(psd)
        wvecs.append(wvec)
        time_sigs.append(row)
        lg_idx = np.argmax(np.abs(row))
        real_value = np.real(row[lg_idx])
        imag_value = np.imag(row[lg_idx])
        res_value = np.max(psd)
        print("{} : Largest value = {}, i{} - resp = {} db".format(ii, real_value, imag_value, res_value))

def process_inbuff(file_name):
    """
        Helper function that ingests data from RTL simulation and plots the output of the input buffer of the channelizer.
    """
    samps = read_binary_file(file_name, format_str='Q', big_endian=True)
    print(len(samps))
    if type(samps) is int:
        print('File does not exist')
        return -1

    if len(samps) == 0:
        print("Not enough samples in File")
        return -1

    mask_i = np.uint64(((1 << 16) - 1) << 16)
    mask_q = np.uint64((1 << 16) - 1)
    mask_bin_num = np.uint64(((1 << 24) - 1) << 32)

    i_sig = [int(samp & mask_i) >> 16 for samp in samps]
    q_sig = [samp & mask_q for samp in samps]
    fft_bin_sig = [int(samp & mask_bin_num) >> 32 for samp in samps]

    offset = np.where(np.array(fft_bin_sig) == 0)[0][0]
    print(offset)

    store_sig = np.array(i_sig[offset:] )+ 1j * np.array(q_sig[offset:])
    write_complex_samples(store_sig, './raw_inputbuffer.bin', q_first=False)

    i_sig = fp_utils.uint_to_fp(i_sig[offset:], qvec=(16, 15), signed=1, overflow='wrap')
    q_sig = fp_utils.uint_to_fp(q_sig[offset:], qvec=(16, 15), signed=1, overflow='wrap')
    fft_bin_sig = fft_bin_sig[offset:]

    M = np.max(fft_bin_sig) + 1
    print("M = {}".format(M))

    trunc = len(i_sig) % M
    if trunc:
        i_sig = i_sig.float[:-trunc]
        q_sig = q_sig.float[:-trunc]
        fft_bin_sig = fft_bin_sig[:-trunc]
    else:
        i_sig = i_sig.float
        q_sig = q_sig.float


    comp_sig = i_sig + 1j * q_sig
    plot_psd_helper(comp_sig, w_time=True, savefig=True, title='Input Buffer', miny=-80)

def process_chan_out(file_name, iq_offset=10*TAPS_PER_PHASE, Mmax=64):
    """
        Helper function that ingests and plots the output of the channelizer from an RTL simulation.
    """
    samps = read_binary_file(file_name, format_str='Q', big_endian=True)
    tuser_bits = calc_fft_tuser_width(Mmax)
    print(len(samps))
    if type(samps) is int:
        print('File does not exist')
        return -1

    if len(samps) == 0:
        print("Not enough samples in File")
        return -1

    mask_i = np.uint64(((1 << 16) - 1) << 16)
    mask_q = np.uint64((1 << 16) - 1)
    mask_tuser = np.uint64(((1 << tuser_bits) - 1) << 32)
    mask_fft_bin = int(((1 << int(np.log2(Mmax))) -1))
    mask_tlast = np.uint64(1 << 32 + tuser_bits)

    # ipdb.set_trace()

    i_sig = [(int(samp & mask_i) >> 16) for samp in samps]
    q_sig = [(samp & mask_q)  for samp in samps]
    tuser_sig = [int(samp & mask_tuser) >> 32 for samp in samps]
    fft_bin_sig = [int(samp & mask_fft_bin) for samp in tuser_sig]
    tlast_sig = [int(samp & mask_tlast) >> (32 + tuser_bits) for samp in samps]

    bin_list = np.unique(fft_bin_sig)
    offset = np.where(np.array(fft_bin_sig) == np.min(bin_list))[0][0]

    M = np.max(bin_list) + 1
    print("M = {}".format(M))

    # write_complex_samples(iq_sig, './raw_out.bin', q_first=False)

    # ipdb.set_trace()
    i_sig = fp_utils.uint_to_fp(i_sig[offset:], qvec=(16, 15), signed=1, overflow='wrap')
    q_sig = fp_utils.uint_to_fp(q_sig[offset:], qvec=(16, 15), signed=1, overflow='wrap')
    tuser_sig = tuser_sig[offset:]
    tlast_sig = tlast_sig[offset:]
    fft_bin_sig = fft_bin_sig[offset:]

    iq_sig = np.array(i_sig.float[offset:] )+ 1j * np.array(q_sig.float[offset:])
    # partition streams into separate lists based on fft_bin_sig
    samp_lists = []
    for value in bin_list:
        indices = np.where(np.array(fft_bin_sig) == value)[0]
        iq_temp = [iq_sig[index] for index in indices]
        # print(len(iq_temp))
        samp_lists.append(iq_temp)

    # comp_sig = i_sig.vec + 1j * q_sig.vec
    # ipdb.set_trace()
    # comp_rsh = np.reshape(comp_sig, (M, -1), 'F')
    # pickle.dump(comp_rsh, open('rtl_output.p', 'wb'))
    # print(np.shape(comp_rsh))

    resps = []
    wvecs = []
    time_sigs = []
    for iq_vec, bin_num in zip(samp_lists, bin_list):
        if iq_offset < len(iq_vec):
            iq_vec = iq_vec[iq_offset:]
        # print(np.max(np.abs(iq_vec)))
        wvec, psd = gen_psd(iq_vec, fft_size=1024, window='blackmanharris')
        resps.append(psd)
        wvecs.append(wvec)
        time_sigs.append(iq_vec)
        lg_idx = np.argmax(np.abs(iq_vec))
        real_value = np.real(iq_vec[lg_idx])
        imag_value = np.imag(iq_vec[lg_idx])
        res_value = np.max(psd)
        print("Bin {} \t: Largest value = {:.4f}, i{:.4f} - resp = {:.4f} db".format(bin_num, real_value, imag_value, res_value))

    # title = 'Channelized Output'
    # fig, ax = plt.subplots(nrows=3, ncols=2)
    # fig.subplots_adjust(bottom=.10, left=.1, top=.95)
    # fig.subplots_adjust(hspace=.50, wspace=.2)
    # fig.set_size_inches(12., 12.)
    # fig.set_dpi(120)
    # print("wvecs  shape = {}".format(np.shape(wvecs)))
    # plot_psd(ax[0][0], wvecs[40], resps[40], title='Channel 0', miny=-120, maxy=10)
    # plot_psd(ax[0][1], wvecs[42], resps[42], title='Channel 1', miny=-120, maxy=10)
    # plot_psd(ax[1][0], wvecs[43], resps[41], title='Channel 2', miny=-120, maxy=10)
    # plot_psd(ax[1][1], wvecs[44], resps[44], title='Channel 3', miny=-120, maxy=10)
    # plot_psd(ax[2][0], wvecs[45], resps[45], title='Channel 4', miny=-120, maxy=10)
    # plot_psd(ax[2][1], wvecs[46], resps[46], title='Channel 5', miny=-120, maxy=10)

    # file_name = copy.copy(title)
    # file_name = ''.join(e if e.isalnum() else '_' for e in file_name)
    # file_name += '.png'
    # file_name = file_name.replace("__", "_")
    # print(file_name)
    # fig.savefig(file_name)

    mpl.use('Agg')
    # sig_list = np.arange(0, M).tolist()
    # sig_list = np.arange(35, 51).tolist()  #[41, 42, 43, 44, 45, 46]
    for j, bin_num in enumerate(bin_list):
        plot_psd_helper((wvecs[j], resps[j]), title=r'$\sf{{PSD\ Overlay\ {}}}$'.format(bin_num), plot_time=True, miny=-150, maxy=20.,
                        time_sig=time_sigs[j][:500], markersize=None, plot_on=False, savefig=True, ytime_min=-1., ytime_max=1.)
        plt.close('all')


def process_synth_out(file_name, row_offset=600):

    samps = read_binary_file(file_name, format_str='I', big_endian=True)
    mod_name = gen_utils.ret_module_name(file_name)
    mod_name = mod_name.replace("_", " ")

    if type(samps) is int:
        print('File does not exist')
        return -1

    if len(samps) == 0:
        print("Not enough samples in File")
        return -1

    mask_i = np.uint32(((2 ** 16) - 1) << 16)
    mask_q = np.uint32((2 ** 16) - 1)

    i_sig = [int((samp & mask_i) / (1 << 16)) for samp in samps]
    i_sig = fp_utils.uint_to_fp(i_sig, qvec=(16, 15), signed=1, overflow='wrap')
    q_sig = [samp & mask_q for samp in samps]
    q_sig = fp_utils.uint_to_fp(q_sig, qvec=(16, 15), signed=1, overflow='wrap')

    i_sig = i_sig.float
    q_sig = q_sig.float

    comp_sig = i_sig + 1j * q_sig
    if len(comp_sig) < 2000:
        print("Not enough Synthesis Data : Data is {} samples".format(len(comp_sig)))
        return 1
    comp_sig = comp_sig[1000:]

    # plot_psd_helper(comp_sig, title='Synthesizer PSD Output - {}'.format(mod_name), w_time=True, miny=-100, maxy=None, plot_on=False, savefig=True)
    plot_psd_helper(comp_sig, title='Synthesizer PSD Output', w_time=True, miny=-100, maxy=None, plot_on=False, savefig=True)
    print("Synthesis Output Produced")


def gen_mask_files(M_list, percent_active=None, values=[42, 43, 44, 45, 46], path=SIM_PATH):
    bin_list = []
    for M in M_list:
        chan_obj = Channelizer(M=M, taps_per_phase=TAPS_PER_PHASE, gen_2X=GEN_2X, taps=TAPS,
                               desired_msb=DESIRED_MSB, qvec=QVEC, qvec_coef=QVEC_COEF, fc_scale=FC_SCALE)
        file_name = path + 'M_{}_mask.bin'.format(M)
        bin_values = chan_obj.gen_mask_file(file_name, percent_active, values)
        bin_list.append(bin_values)

    return bin_list

def gen_tap_plots(M_list):

    for M in M_list:
        chan_obj = Channelizer(M=M, taps_per_phase=TAPS_PER_PHASE, gen_2X=GEN_2X, K=K_default, taps=TAPS, 
                               desired_msb=DESIRED_MSB, qvec=QVEC, qvec_coef=QVEC_COEF, fc_scale=FC_SCALE)
        # chan_obj.plot_psd_single(savefig=True)
        gen_taps(M, M_MAX, gen_2X=GEN_2X, taps_per_phase=TAPS_PER_PHASE, pfb_msb=DESIRED_MSB)
        print(chan_obj.pfb_msb)
        tap_title = 'taps psd M {}'.format(M)
        # get adjacent bins and plot suppression value.
        freq_pts = [- 1.25 / M, 1.25 / M, -1. / M, 1. / M]
        fft_size=16384
        if M > 256:
            fft_size = 16384
        chan_obj.plot_psd(fft_size=fft_size, taps=None, freq_vector=None, title=tap_title, savefig=True, pwr_pts=SIX_DB, freq_pts=freq_pts, miny=-120)

def plot_input_file(file_name):
    samps = read_binary_file(file_name, format_str='I', big_endian=True, num_samps=50000)
    # write_binary_file(samps, file_name, format_str='h', append=False, big_endian=True)
    mod_name = gen_utils.ret_module_name(file_name)
    mod_name = mod_name.replace("_", " ")
    if type(samps) is int:
        print('File does not exist')
        return -1

    if len(samps) == 0:
        print("Not enough samples in File")
        return -1

    mask_i = np.uint32(((2 ** 16) - 1) << 16)
    mask_q = np.uint32((2 ** 16) - 1)

    q_sig = [int((samp & mask_i) / (1 << 16)) for samp in samps]
    q_sig = fp_utils.uint_to_fp(q_sig, qvec=(16, 15), signed=1, overflow='wrap')
    i_sig = [samp & mask_q for samp in samps]
    i_sig = fp_utils.uint_to_fp(i_sig, qvec=(16, 15), signed=1, overflow='wrap')

    i_sig = i_sig.float
    q_sig = q_sig.float

    comp_sig = i_sig + 1j * q_sig

    plot_psd_helper(comp_sig, title='Stimulus PSD', w_time=True, miny=-100, maxy=None, plot_on=False, savefig=True, fft_size=2048)
    print("Input stimulus plotted")

def gen_logic(chan_obj, path=IP_PATH, avg_len=256, fs=6.4E6):
    """
        Helper function that generate RTL logic 
    """
    sample_fi = fp_utils.ret_dec_fi(0, qvec=chan_obj.qvec, overflow='wrap', signed=1)
    sample_fi.gen_full_data()
    gen_output_buffer(chan_obj.Mmax, path)
    gen_exp_shifter(chan_obj, avg_len, sample_fi=sample_fi, path=path)
    gen_input_buffer(chan_obj.Mmax, path)
    gen_circ_buffer(chan_obj.Mmax, path)
    gen_pfb(chan_obj, path, fs=fs)
    gen_downselect(chan_obj.Mmax, path)
    gen_final_cnt(path)
    print(chan_obj.Mmax)

def get_args():

    M_list = [8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    avg_len = 256
    chan_file = SIM_PATH + 'chan_out_8_file.bin'
    synth_file = SIM_PATH + 'synth_out_8_file.bin'
    input_file = SIM_PATH + 'sig_store_test8.bin'
    pfb_file = SIM_PATH + 'pfb_out_8_file.bin'
    gen_2X = False
    taps_per_phase = 16
    Mmax = 512

    parser = ArgumentParser(description='Channelizer CLI -- Used to generate RTL code, input stimulus, and process output of RTL simulation.')
    parser.add_argument('-l', '--generate_logic', action='store_true', help='Generates RTL Logic for modules, FIFOs, DSP48, CIC filters, etc, to be used in exp_shifter.vhd, input_buffer.vhd, circ_buffer.vhd, and the PFB module')
    parser.add_argument('-c', '--rtl-chan-outfile', type=str, help='Process RTL output file specified by input string -- can use \'default\' as input ')
    parser.add_argument('-s', '--rtl-synth-outfile', type=str, help='Process RTL output file specified by input string -- can use \'default\' as input ')
    parser.add_argument('--check-stim', type=str, help='Plot PSD of input file')
    parser.add_argument('--gen-tones', action='store_true', help='Generate Input Tones')
    parser.add_argument('--process-pfb', type=str, help='Process PFB by running through FFT -- can use \'default\' as input')
    parser.add_argument('--process-inbuff', type=str, help='Plot PSD of input buffer')
    parser.add_argument('--process-input', type=str, help='Generate Channelizer Ouput with Python code')
    parser.add_argument('-i', '--rtl-sim-infile', type=str, help='Generate RTL input and store to filename specified by string -- can use \'default\' as input')
    parser.add_argument('-t', '--generate-taps', action='store_true', help='Generates tap files for all valid FFT Sizes : [8, 16, 32, 64, 128, 256, 512, 1024, 2048]')
    parser.add_argument('-m', '--generate-masks', action='store_true', help='Generate Mask files for all valid FFT Sizes : [8, 16, 32, 64, 128, 256, 512, 1024, 2048]')
    parser.add_argument('-o', '--opt-taps', action='store_true', help='Returns optimized filter parameters all valid FFT Sizes : [8, 16, 32, 64, 128, 256, 512, 1024, 2048]')
    parser.add_argument('--generate-animation', action='store_true', help='Generates polyphase filter animation')
    parser.add_argument('--find-opt-filters', action='store_true', help='Designs optimized Exponential filters')
    parser.add_argument('--gen-2X', action='store_true', help='Flag indicates that a M/2 Channelizer is desired')
    parser.add_argument('--Mmax', type=str, help='Maximum decimation of desired channelizer')
    parser.add_argument('--tps', type=str, help='Specify Taps Per PFB Phase (tps)')

    args = parser.parse_args()
    if args.gen_2X:
        gen_2X = True

    if args.Mmax is not None:
        Mmax = int(args.Mmax)

    if args.tps is not None:
        taps_per_phase = int(args.tps)

    if args.gen_tones:
        gen_tones(M=512, lidx=30, ridx=31, offset=0.00050)

    if args.generate_logic:
        chan_obj = Channelizer(M=Mmax, taps_per_phase=taps_per_phase, gen_2X=gen_2X, desired_msb=DESIRED_MSB, qvec=QVEC, 
                               qvec_coef=QVEC_COEF, fc_scale=FC_SCALE, taps=TAPS)

        sample_fi = fp_utils.ret_dec_fi(0, qvec=QVEC, overflow='wrap', signed=1)
        sample_fi.gen_full_data()
        gen_output_buffer(Mmax)
        shift_name = gen_exp_shifter(chan_obj, avg_len, sample_fi=sample_fi)
        gen_input_buffer(Mmax)
        gen_circ_buffer(Mmax)
        pfb_name = gen_pfb(chan_obj)
        gen_downselect(Mmax)
        gen_final_cnt()
        adv_filter.gen_chan_top(IP_PATH, chan_obj, shift_name, pfb_name)
        if chan_obj.gen_2X:
            copyfile('./verilog/circ_buffer.v', IP_PATH + '/circ_buffer.v')
            copyfile('./verilog/input_buffer.v', IP_PATH + '/input_buffer.v')
        else:
            copyfile('./verilog/input_buffer_1x.v', IP_PATH + '/input_buffer_1x.v')
        print(Mmax)

    if args.rtl_chan_outfile is not None:
        if args.rtl_chan_outfile.lower() != 'default':
            chan_file = args.rtl_chan_outfile
        process_chan_out(chan_file, Mmax=Mmax, iq_offset=10*taps_per_phase)

    if args.rtl_synth_outfile is not None:
        if args.rtl_synth_outfile.lower() != 'default':
            synth_file = args.rtl_synth_outfile
        process_synth_out(synth_file)

    if args.rtl_sim_infile is not None:
        if args.rtl_sim_infile.lower() != 'default':
            input_file = args.rtl_sim_infile
        gen_test_sig(input_file)

    if args.check_stim is not None:
        if args.check_stim.lower() != 'default':
            input_file = args.check_stim
        plot_input_file(input_file)

    if args.process_pfb is not None:
        if args.process_pfb.lower() != 'default':
            pfb_file = args.process_pfb
        process_pfb_out(pfb_file)

    if args.process_inbuff is not None:
        inbuff_file = args.process_inbuff
        process_inbuff(inbuff_file)

    if args.process_input is not None:
        M = Mmax
        print(K_default)
        chan = Channelizer(M=M, gen_2X=gen_2X, qvec=QVEC, qvec_coef=QVEC_COEF, fc_scale=FC_SCALE, taps=TAPS)
        vec = read_complex_samples(args.process_input, q_first=False) * (2 ** -15)
        chan_out = chan.analysis_bank(vec[:1500000], plot_out=False)
        pickle.dump(chan_out, open('float_output.p', 'wb'))
        row_offset = 200
        row_end = 1000
        resps = []
        wvecs = []
        time_sigs = []
        for ii, row in enumerate(chan_out):
            row = row[row_offset:row_end]
            print(np.max(np.abs(row)))
            wvec, psd = gen_psd(row, fft_size=256, window='blackmanharris')
            resps.append(psd)
            wvecs.append(wvec)
            time_sigs.append(row)
            lg_idx = np.argmax(np.abs(row))
            real_value = np.real(row[lg_idx])
            imag_value = np.imag(row[lg_idx])
            res_value = np.max(psd)
            print("{} : Largest value = {}, i{} - resp = {} db".format(ii, real_value, imag_value, res_value))

    if args.generate_taps:
        gen_tap_plots(M_list)

    if args.generate_masks:
        gen_mask_files(M_list)

    if args.opt_taps:
        populate_fil_table()

    if args.generate_animation:
        chan_obj = Channelizer(M=4, gen_2X=False)
        chan_obj.gen_animation()

    if args.find_opt_filters:
        find_best_terms()

    return 


if __name__ == "__main__":
    modem_args = get_args()

    plt.show(block=blockl)
