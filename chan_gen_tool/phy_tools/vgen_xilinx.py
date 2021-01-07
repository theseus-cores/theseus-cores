# -*- coding: utf-8 -*-
"""
Created on Tue October 10 17:01:28 2017

@author: phil
"""
import os
from phy_tools.gen_utils import ret_module_name
import numpy as np
from phy_tools.dsp_opts import opcode_opts
import copy
import ipdb
import re

from IPython.core.debugger import set_trace

from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    __version__ = today.strftime("%Y.%m.%d")


use_dict = {'use_mult': False, 'use_2pports': False, 'use_concat': False, 'use_aport': False, 'use_bport': False,
            'use_cport': False, 'use_acin': False, 'use_bcin': False, 'use_pcin': False, 'use_dport': False,
            'use_carryin': False, 'use_carrycascin': False, 'use_preadd': False}

def comp_opmodes(opcode, areg, breg, rnd=False):

    opmode = 0
    inmode = 0

    port_dict = ret_opcode_params(opcode, rnd)

    use_mult = port_dict['use_mult']
    use_concat = port_dict['use_concat']
    use_2pport = port_dict['use_2pports']
    use_cport = port_dict['use_cport']
    use_pcin_port = port_dict['use_pcin']
    use_preadd = port_dict['use_preadd']

    num_pterms = len(re.findall(r'\bp\b', opcode, re.IGNORECASE))
    num_cterms = len(re.findall(r'\bc\b', opcode, re.IGNORECASE))
    # ipdb.set_trace()
    # X MUX Settings.
    if use_mult:
        opmode += 1
    elif use_concat:
        opmode += 3
    elif use_2pport or (num_pterms == 2):
        opmode += 2

    # Y MUX Settings.
    if use_mult:
        opmode += 4
    elif (use_cport and (use_pcin_port or num_pterms > 0) or num_cterms == 2):
        opmode += 12

    z_val = ''
    # Z MUX settings.
    if re.search(r'\bpcin\s>>\s17\b', opcode, re.IGNORECASE) is not None:
        opmode += 5 << 4
        z_val = 'pcin>>17'
    elif re.search(r'\bp\s>>\s17\b', opcode, re.IGNORECASE) is not None:
        opmode += 6 << 4
        z_val = 'p>>17'
    elif re.search(r'\bpcin\b', opcode, re.IGNORECASE) is not None:
        opmode += 16
        z_val = 'pcin'
    elif re.search(r'\bp\b', opcode, re.IGNORECASE) is not None:
        opmode += 2 << 4
        z_val = 'p'
    elif use_cport:
        opmode += 3 << 4
        z_val = 'c'

    inmode = 0
    if areg > 0:
        if re.search(r'\bd\s*\+\s*a\b|\bd\s*\+\s*acin\b|\bacin\s*\+\s*d\b|\ba\s*\+\s*d\b', opcode, re.IGNORECASE) is not None:
            inmode = 4
        elif re.search(r'd\s*-\s*a|d\s*-\s*acin', opcode, re.IGNORECASE) is not None:
            inmode = 12
        elif re.search(r'-a|-acin', opcode, re.IGNORECASE) is not None:
            inmode += 8
            inmode = inmode & 13
        elif re.search(r'\bd\b', opcode, re.IGNORECASE) is not None:
            inmode = 6
        elif re.search(r'\ba\b|\bacin\b', opcode, re.IGNORECASE) is not None:
            inmode = inmode & 13
        else:
            inmode = 2
        if areg == 1:
            inmode += 1

    if breg == 1:
        inmode += 16

    carryin_sel = 0
    if re.search(r'\bcarrycascin\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 2
    elif re.search(r'\bcarrycascout\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 4
    elif re.search(r'\brndsimple(\spcin\s)\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 1
    elif re.search(r'\brndsimple(\sp\s)\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 5
    elif re.search(r'\brndsym(\spcin\s)\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 3
    elif re.search(r'\brndsym(\sp\s)\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 7
    elif re.search(r'\brndsym\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 6
    elif re.search(r'\brndsimple\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 6

    alumode, inmode_diff = opcode_opts(opcode)
    if inmode_diff is not None:
        inmode &= inmode_diff

    return opmode, inmode, alumode, carryin_sel

def comp_opmodes_e2(opcode, areg, breg, rnd=False):
    """
        Helper function for computing inmode register for DSP48E2 module.
    """
    opmode = 0
    inmode = 0

    port_dict = ret_opcode_params_e2(opcode, rnd)

    use_mult = port_dict['use_mult']
    use_concat = port_dict['use_concat']
    use_2pport = port_dict['use_2pports']
    use_cport = port_dict['use_cport']
    use_pcin_port = port_dict['use_pcin']
    use_preadd = port_dict['use_preadd']
    use_dport = port_dict['use_dport']

    num_pterms = len(re.findall(r'\bp\b', opcode, re.IGNORECASE))
    num_cterms = len(re.findall(r'\bc\b', opcode, re.IGNORECASE))
    # X MUX Settings.
    if use_mult:
        opmode += 1
    elif use_concat:
        opmode += 3
    elif use_2pport or (num_pterms == 2):
        opmode += 2

    # Y MUX Settings.
    if use_mult:
        opmode += 4
    elif (use_cport and (use_pcin_port or num_pterms > 0) or num_cterms == 2):
        opmode += 12

    # W Mux Settings
    if rnd:
        opmode += 1 << 8
    elif len(re.findall(r'c', opcode, re.IGNORECASE)) > 1:
        # multiple occurences of C
        opmode += 3 << 7
    elif len(re.findall(r'p', opcode, re.IGNORECASE)) > 1:
        # multiple occurences of P
        opmode += 1 << 7

    z_val = ''
    # Z MUX settings.
    if re.search(r'\bpcin\s>>\s17\b', opcode, re.IGNORECASE) is not None:
        opmode += 5 << 4
        z_val = 'pcin>>17'
    elif re.search(r'\bp\s>>\s17\b', opcode, re.IGNORECASE) is not None:
        opmode += 6 << 4
        z_val = 'p>>17'
    elif re.search(r'\bpcin\b', opcode, re.IGNORECASE) is not None:
        opmode += 16
        z_val = 'pcin'
    elif re.search(r'\bp\b', opcode, re.IGNORECASE) is not None:
        opmode += 2 << 4
        z_val = 'p'
    elif use_cport:
        opmode += 3 << 4
        z_val = 'c'

    bmultsel = 'B'
    if re.search(r'\bb\s*\*\b', opcode, re.IGNORECASE) is not None:
        bmultsel = 'B'
    # if B^2
    if re.search(r'\bb\s*\*\s*b\b', opcode, re.IGNORECASE) is not None:
        bmultsel = 'AD'

    if re.search(r'\ba\s*\*zero\b', opcode, re.IGNORECASE) is not None:
        bmultsel = 'B'


    preaddsel = 'A'
    if re.search(r'\bd\s*\+b\b|\bb\s*\+d\b', opcode, re.IGNORECASE) is not None:
        preaddsel = 'B'

    if re.search(r'\bd\s*\+a\b|\ba\s*\+d\b', opcode, re.IGNORECASE) is not None:
        preaddsel = 'A'

    if re.search(r'\bb\s*\*\s*b\b', opcode, re.IGNORECASE) is not None:
        preaddsel = 'B'

    if re.search(r'\ba\s*\*\s*a\b', opcode, re.IGNORECASE) is not None:
        preaddsel = 'A'

    if re.search(r'\ba\s*\*zero\b', opcode, re.IGNORECASE) is not None:
        preaddsel = 'B'

    if re.search(r'\bb\s*\*zero\b', opcode, re.IGNORECASE) is not None:
        preaddsel = 'A'

    amultsel = 'AD' if use_dport else 'A'
    inmode = 0

    bpres = re.search(r'\bb\b|\bbcin\b', opcode, re.IGNORECASE) is not None
    apres = re.search(r'\ba\b|\bacin\b', opcode, re.IGNORECASE) is not None
    axorb = apres ^ bpres
    # Capturing both A and B ports with new DSP48E2 functionality  Table 2-2 DSP48E2 Functionality
    # D + A | D + ACIN | ACIN + D | A + D
    if re.search(r'\bd\s*\+\s*a\b|\bd\s*\+\s*acin\b|\bacin\s*\+\s*d\b|\ba\s*\+\s*d\b', opcode, re.IGNORECASE) is not None:
        inmode = 4
    #D + B | D + BCIN | BCIN + D | B + D
    elif re.search(r'\bd\s*\+\s*b\b|\bd\s*\+\s*bcin\b|\bbcin\s*\+\s*d\b|\bb\s*\+\s*d\b', opcode, re.IGNORECASE) is not None:
        inmode = 4
    # D - A | D - ACIN
    elif re.search(r'd\s*-\s*a|d\s*-\s*acin', opcode, re.IGNORECASE) is not None:
        inmode = 12
    #D - B | D - BCIN
    elif re.search(r'd\s*-\s*b|d\s*-\s*bcin', opcode, re.IGNORECASE) is not None:
        inmode = 12

    # -A | -ACIN
    elif re.search(r'-a|-acin', opcode, re.IGNORECASE) is not None:
        inmode += 8
        inmode = inmode & 13
    # D
    elif re.search(r'\bd\b', opcode, re.IGNORECASE) is not None:
        inmode = 6
    # A | ACIN
    elif re.search(r'\ba\b|\bacin\b', opcode, re.IGNORECASE) is not None:
        inmode = inmode & 13

    # if A XOR B | (NOT A AND NOT B)
    if axorb or (not apres and not bpres):
        inmode += 2

    if areg == 1:
        # INMODE[0] selects between A1 (INMODE[0] = 1) and the A2 mux controlled by AREG (INMODE[0] = 0).
        # Note that using A2 is used for both 0 and 2 A registers -- see Figure 2-5
        inmode += 1

    if breg == 1:
        # INMODE[4] selects between B1 (INMODE[4] = 1) and the B2 mux controlled by BREG (INMODE[4] = 0)
        # Note that using B2 is used for both 0 and 2 B registers -- see Figure 2-6
        inmode += 16

    carryin_sel = 0
    if re.search(r'\bcarrycascin\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 2
    elif re.search(r'\bcarrycascout\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 4
    elif re.search(r'\brndsimple(\spcin\s)\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 1
    elif re.search(r'\brndsimple(\sp\s)\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 5
    elif re.search(r'\brndsym(\spcin\s)\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 3
    elif re.search(r'\brndsym(\sp\s)\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 7
    elif re.search(r'\brndsym\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 6
    elif re.search(r'\brndsimple\b', opcode, re.IGNORECASE) is not None:
        carryin_sel = 6

    alumode, inmode_diff = opcode_opts(opcode)
    if inmode_diff is not None:
        inmode &= inmode_diff

    return opmode, inmode, alumode, carryin_sel, amultsel, bmultsel, preaddsel

def gen_regs(fh, prefix='a_d', cnt=1, sp='', msb=24, str_val=None):
    for jj in range(cnt):
        if str_val is not None and jj == 0:
            fh.write('{}reg [{}:0] {};\n'.format(sp, msb, str_val))
        else:
            fh.write('{}reg [{}:0] {}{};\n'.format(sp, msb, prefix, jj))

def logic_rst(fh, prefix='a_d', cnt=1, sp=''):
    for jj in range(cnt):
        fh.write('{}{}{} <= 0;\n'.format(sp, prefix, jj))

def logic_gate(fh, prefix='a_d', str_val='a', cnt=1, sp=''):
    for jj in range(cnt):
        rside = str_val if (jj == 0) else '{}{}'.format(prefix, jj - 1)
        fh.write('{}{}{} <= {};\n'.format(sp, prefix, jj, rside))

def ret_opcode_params(opcode, rnd=False):
    int_dict = use_dict.copy()

    # \b is for whole word search
    if re.search('\*', opcode) is not None:
        int_dict['use_mult'] = True
    if re.search('-A', opcode, re.IGNORECASE) is not None:
        int_dict['use_preadd'] = True
        int_dict['use_dport'] = True
        
    if re.search('-ACIN', opcode, re.IGNORECASE) is not None:
        int_dict['use_preadd'] = True
        int_dict['use_dport'] = True

    test1 = re.search(r'\bp\b&\bpcin\b', opcode, re.IGNORECASE)
    test2 = re.search(r'>>', opcode, re.IGNORECASE)
    if test1 is not None and test2 is None:
        int_dict['use_2pports'] = True

    if re.search(r'\ba\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_aport'] = True

    if re.search(r'\bb\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_bport'] = True

    if re.search(r'\bc\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_cport'] = True

    if re.search(r'\bd\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_dport'] = True
        int_dict['use_preadd'] = True
        int_dict['use_mult'] = True

    if re.search(r'\bacin\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_acin'] = True
    if re.search(r'\bbcin\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_bcin'] = True
    if re.search(r'\bpcin\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_pcin'] = True

    if re.search(r'\bcarrin\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_carryin'] = True

    if re.search(r'\bconcat\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_concat'] = True
        int_dict['use_aport'] = False
        int_dict['use_bport'] = False

    # if rounding then must use cport and carryin.
    if rnd:
        int_dict['use_cport'] = True
        int_dict['use_carryin'] = True

    return int_dict

def ret_opcode_params_e2(opcode, rnd=False):
    int_dict = use_dict.copy()

    # \b is for whole word search
    if re.search('\*', opcode) is not None:
        int_dict['use_mult'] = True

    # got a parentheses must have a pre-add
    # print(opcode)
    if re.search('\(', opcode, re.IGNORECASE) is not None:
        int_dict['use_preadd'] = True

    if re.search('-A', opcode, re.IGNORECASE) is not None:
        int_dict['use_dport'] = True
    if re.search('-ACIN', opcode, re.IGNORECASE) is not None:
        int_dict['use_dport'] = True

    test1 = re.search(r'\bp\b&\bpcin\b', opcode, re.IGNORECASE)
    test2 = re.search(r'>>', opcode, re.IGNORECASE)
    if test1 is not None and test2 is None:
        int_dict['use_2pports'] = True

    if re.search(r'\ba\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_aport'] = True

    if re.search(r'\bb\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_bport'] = True

    if re.search(r'\bc\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_cport'] = True

    if re.search(r'\bd\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_dport'] = True
        int_dict['use_preadd'] = True
        int_dict['use_mult'] = True

    # if re.search(r'\bb\b', opcode, re.IGNORECASE) is not None:
    if re.search(r'\bb\*b\b|\ba\*a\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_dport'] = True

    if re.search(r'\bacin\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_acin'] = True
    if re.search(r'\bbcin\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_bcin'] = True
    if re.search(r'\bpcin\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_pcin'] = True

    if re.search(r'\bcarrin\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_carryin'] = True

    if re.search(r'\bconcat\b', opcode, re.IGNORECASE) is not None:
        int_dict['use_concat'] = True
        int_dict['use_aport'] = False
        int_dict['use_bport'] = False

    # if rounding then must use cport and carryin.
    if rnd:
        # int_dict['use_cport'] = True
        int_dict['use_carryin'] = True

    return int_dict


def gen_dsp48E1(path, name, opcode='A*B', a_width=25, b_width=18, c_width=48, d_width=25,
                areg=1, breg=1, creg=1, dreg=1, mreg=1, preg=1, concatreg=1, carryreg=1,
                use_acout=False, use_bcout=False, use_pcout=False, use_ce=False, use_reset=False, rnd=False,
                p_msb=None, p_lsb=None, a_signed=True, b_signed=True):

    def input_port(fh):
        # op_strs = re.findall(r"[\w']+", opcode)
        # for str_val in op_strs
        if use_aport:
            fh.write('    input [{}:0] a,\n'.format(a_msb))
        if use_acin_port:
            fh.write('    input [29:0] acin,\n')
        if use_bport:
            fh.write('    input [{}:0] b,\n'.format(b_msb))
        if use_bcin_port:
            fh.write('    input [29:0] bcin,\n')
        if use_concat:
            fh.write('    input [47:0] concat,\n')
        if use_pcin_port:
            fh.write('    input [47:0] pcin,\n')
        if use_carryin:
            fh.write('    input carryin,\n')
        if use_carrycascin:
            fh.write('    input carrycascin,\n')
        if use_dport:
            fh.write('    input [{}:0] d,\n'.format(d_msb))
        if use_cport:
            fh.write('    input [{}:0] c,\n'.format(c_msb))
        if multi_opcode:
            fh.write('    input [{}:0] opcode,\n'.format(opcode_bits - 1))

    def output_port(fh):
        if use_acout:
            fh.write('    output [29:0] acout,\n')
        if use_bcout:
            fh.write('    output [29:0] bcout,\n')
        if use_pcout:
            fh.write('    output [47:0] pcout,\n')
    assert(path is not None), 'User must specify directory'
    file_name = 'dsp48_{}.v'.format(name)
    file_name = os.path.join(path, file_name)
    module_name = ret_module_name(file_name)
    # parse opcode
    if type(opcode) is list:
        opcodes = copy.copy(opcode)
    else:
        opcodes = [opcode]

    concat_list = []
    two_pports_list = []
    mult_list = []
    aport_list = []
    bport_list = []
    cport_list = []
    dport_list = []
    acin_list = []
    bcin_list = []
    pcin_list = []
    carryin_list = []
    carrycascin_list = []

    for opcode in opcodes:
        temp_dict = ret_opcode_params(opcode)
        concat_list.append(temp_dict['use_concat'])
        two_pports_list.append(temp_dict['use_2pports'])
        mult_list.append(temp_dict['use_mult'])
        aport_list.append(temp_dict['use_aport'])
        bport_list.append(temp_dict['use_bport'])
        cport_list.append(temp_dict['use_cport'])
        dport_list.append(temp_dict['use_dport'])
        acin_list.append(temp_dict['use_acin'])
        bcin_list.append(temp_dict['use_bcin'])
        pcin_list.append(temp_dict['use_pcin'])
        carryin_list.append(temp_dict['use_carryin'])
        carrycascin_list.append(temp_dict['use_carrycascin'])

    use_mult = np.any(mult_list)
    use_2pports = np.any(two_pports_list)
    use_concat = np.any(concat_list)
    use_aport = np.any(aport_list)
    use_bport = np.any(bport_list)
    use_cport = np.any(cport_list)
    use_dport = np.any(dport_list)
    use_acin_port = np.any(acin_list)
    use_bcin_port = np.any(bcin_list)
    use_pcin_port = np.any(pcin_list)
    use_carryin = np.any(carryin_list)
    use_carrycascin = np.any(carrycascin_list)
    use_preadd = use_aport and use_dport

    pcin = 'pcin' if use_pcin_port else '48\'d0'
    a_val = 'a_s' if (use_aport or use_concat) else '30\'d0'
    b_val = 'b_s' if (use_bport or use_concat) else '18\'d1'
    c_val = 'c_s' if use_cport else '48\'d0'
    d_val = 'd_s' if use_dport else '25\'d0'
    acin = 'acin' if use_acin_port else '30\'d0'
    bcin = 'bcin' if use_bcin_port else '18\'d0'
    carryin = 'carryin' if use_carryin else '1\'b0'
    carrycascin = 'carrycascin' if use_carrycascin else '1\'b0'

    multi_opcode = (len(opcodes) > 1)
    opcode_bits = int(np.ceil(np.log2(len(opcodes))))
    op_strs = []
    for opcode in opcodes:
        opcode = opcode.lower()
        op_strs.append(re.findall(r"[\w']+", opcode))
    # op_strs = op_code.split(" ") gives a list of strings:
    a_source = 'DIRECT'
    b_source = 'DIRECT'
    areg_logic = 0
    breg_logic = 0
    creg_logic = 0
    dreg_logic = 0
    concatreg_logic = 0
    carryreg_logic = 0

    opmode_reg = 0
    inmode_reg = 0
    alumode_reg = 0
    carryin_sel_reg = 0

    mult_delay = np.max((areg, breg)) + mreg
    opmode_logic = 0
    opmode_delay = 0
    alumode_delay = 0
    inmode_delay = areg
    if use_concat:
        inmode_delay = np.max((inmode_delay, concatreg))
    if use_cport:
        inmode_delay = np.max((inmode_delay, creg - mreg))

    inmode_logic = 0
    alumode_logic = 0
    carryin_sel_delay = 0
    carryin_sel_logic = 0
    if multi_opcode:
        opmode_delay = np.max((mult_delay, creg))
        # there is an implied 1 tick delay due to the multi_opcode mux.
        opmode_logic = np.max((opmode_delay - 1, 1))
        opmode_reg = np.max((opmode_delay - opmode_logic, 0))
        inmode_reg = np.min((inmode_delay, 1))
        inmode_logic = inmode_delay - inmode_reg
        alumode_delay = opmode_delay
        alumode_reg = opmode_reg
        alumode_logic = opmode_logic
        carryin_sel_delay = opmode_delay
        carryin_sel_reg = opmode_reg
        carryin_sel_logic = opmode_logic

    infer_logic = False
    input_regs = np.max([(areg - 2)*use_aport, (breg - 2)*use_bport, (creg - 1)*use_cport, (dreg - 1)*use_dport, concatreg - 2])
    if input_regs + alumode_logic + inmode_logic + opmode_logic > 0:
        infer_logic = True

    if use_concat:
        if concatreg > 2:
            breg_logic = concatreg - 2
            areg_logic = concatreg - 2
            areg = 2
            breg = 2
        else:
            areg = concatreg
            breg = concatreg
    else:
        areg_logic = np.max((areg - 2, 0))
        breg_logic = np.max((breg - 2, 0))

    if areg_logic > 0 and (use_aport or use_concat):
        a_val = 'a_d{}'.format(areg_logic - 1)
        areg = 2
    if breg_logic > 0 and (use_bport or use_concat):
        b_val = 'b_d{}'.format(breg_logic - 1)
        breg = 2
    if not use_cport:
        creg = 0
    else:
        if creg > 1 and use_cport:
            creg_logic = creg - 1
            creg = 1
            c_val = 'c_d{}'.format(creg_logic - 1)

    if not use_dport:
        dreg = 0
    else:
        if dreg > 1:
            dreg_logic = dreg - 1
            dreg = 1
            d_val = 'd_d{}'.format(dreg_logic - 1)
    if carryreg > 1:
        carryreg_logic = carryreg - 1
        carryreg = 1

    if use_concat:
        if concatreg > 2:
            breg_logic = concatreg - 2
            areg_logic = concatreg - 2
            areg = 2
            breg = 2
        else:
            areg = concatreg
            breg = concatreg

    adreg = 1 if (use_preadd and areg == 2) else 0

    a_msb = a_width - 1
    b_msb = b_width - 1
    c_msb = c_width - 1
    d_msb = d_width - 1

    ce = 'ce' if use_ce else '1\'b1'
    cea1 = ce if areg >= 1 else '1\'b0'        
    cea2 = ce if areg == 2 else '1\'b0'

    ceb1 = ce if breg >= 1 else '1\'b0'
    ceb2 = ce if breg == 2 else '1\'b0'
        
    sync_reset = 'sync_reset' if use_reset else '1\'b0'
        
    a = '{}\'d0'.format(a_width)
    b = '{}\'d0'.format(b_width)
    c = '{}\'d0'.format(c_width)
    d = '25\'d0'
    dport_str = 'FALSE'
    if use_dport:
        dport_str = 'TRUE'

    p_slice = True if (p_msb is not None and p_lsb is not None) else False
    if rnd or p_slice:
        p_width = p_msb - p_lsb + 1
    else:
        p_width = 48

    if rnd:
        assert(use_cport is not True), 'User cannot use c-port when rounding'
        c_constant = 2**(p_lsb - 1) - 1
        if use_aport:
            carryin = 'a[0]'
        elif use_bport:
            carryin = 'b[0]'
        else:
            # make this a registered value.
            carryin = 'p_d'

    for str_val in op_strs:
        if str_val == 'acin':
            a_source = 'CASCADE'
        if str_val == 'bcin':
            b_source = 'CASCADE'

    opmodes = []
    inmodes = []
    alumodes = []
    carryin_sels = []
    for opcode in opcodes:
        temp0, temp1, temp2, temp3 = comp_opmodes(opcode, areg, breg, rnd)
        # print(opcode, temp0, temp1, temp2, temp3)
        opmodes.append(temp0)
        inmodes.append(temp1)
        alumodes.append(temp2)
        carryin_sels.append(temp3)

    if opmode_logic:
        opmode_str = 'opmode_d{}'.format(opmode_logic - 1)
    else:
        if multi_opcode:
            opmode_str = 'opmode'
        else:
            opmode_str = '7\'d{}'.format(opmodes[0])

    if inmode_logic:
        inmode_str = 'inmode_d{}'.format(inmode_delay - 2)
    else:
        if multi_opcode:
            inmode_str = 'inmode'
        else:
            inmode_str = '5\'d{}'.format(inmodes[0])


    if alumode_logic:
        alumode_str = 'alumode_d{}'.format(alumode_delay - 2)
    else:
        if multi_opcode:
            alumode_str = 'alumode'
        else:
            alumode_str = '4\'d{}'.format(alumodes[0])

    if carryin_sel_logic:
        carryin_sel_str = 'carryin_sel_d{}'.format(carryin_sel_logic - 1)
    else:
        if multi_opcode:
            carryin_sel_str = 'carryin_sel'
        else:
            carryin_sel_str = '3\'d{}'.format(carryin_sels[0])


    if not use_mult:
        mreg = 0

    with open(file_name, "w") as fh:

        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        if use_reset:
            fh.write('    input sync_reset,\n')
        fh.write('    input clk,\n')
        if use_ce:
            fh.write('    input ce,\n')
        fh.write('\n')

        input_port(fh)
        output_port(fh)
        # fh.write('\n')
        fh.write('    output [{}:0] p\n'.format(p_width - 1))
        fh.write(');\n\n')
        if use_aport or use_concat:
            fh.write('wire [29:0] a_s;\n')
        if use_bport or use_concat:
            fh.write('wire [17:0] b_s;\n')
        if use_cport:
            fh.write('wire [47:0] c_s;\n')
        if use_dport:
            fh.write('wire [24:0] d_s;\n')
        if rnd or p_slice:
            fh.write('wire [47:0] p_s;\n')
            fh.write('reg p_d = 1\'b0;\n')
        fh.write('\n')
        if infer_logic:
            gen_regs(fh, prefix='a_d', cnt=areg_logic, sp='', msb=29)
            gen_regs(fh, prefix='b_d', cnt=breg_logic, sp='', msb=17)
            gen_regs(fh, prefix='c_d', cnt=creg_logic, sp='', msb=47)
            gen_regs(fh, prefix='d_d', cnt=dreg_logic, sp='', msb=24)
            gen_regs(fh, prefix='carryreg_d', cnt=carryreg_logic, sp='', msb=0)
            # print("opmode_logic = {}".format(opmode_logic))
            gen_regs(fh, prefix='opmode_d', cnt=opmode_logic, sp='', msb=6)
            gen_regs(fh, prefix='inmode_d', cnt=inmode_logic, sp='', msb=4)
            gen_regs(fh, prefix='alumode_d', cnt=alumode_logic, sp='', msb=3)
            gen_regs(fh, prefix='carryin_sel_d', cnt=carryin_sel_logic, sp='', msb=2)
            if multi_opcode is True:
                gen_regs(fh, prefix='next_alumode', cnt=1, sp='', msb=3, str_val='next_alumode')
                gen_regs(fh, prefix='next_carryin_sel', cnt=1, sp='', msb=2, str_val='next_carryin_sel')
                gen_regs(fh, prefix='next_inmode', cnt=1, sp='', msb=4, str_val='next_inmode')
                gen_regs(fh, prefix='next_opmode', cnt=1, sp='', msb=6, str_val='next_opmode')

        fh.write('\n')
        if rnd or p_slice:
            fh.write('assign p = p_s[{}:{}];\n'.format(p_msb, p_lsb))
        if use_aport or use_concat:
            if use_concat:
                fh.write('assign a_s = concat[47:18];\n')  # {{{{{}{{a[{}]}}}}, a}};\n'.format(30 - a_width, a_width - 1))
            else:
                fh.write('assign a_s = {{{{{}{{a[{}]}}}}, a}};\n'.format(30 - a_width, a_width - 1))

        if use_bport or use_concat:
            if use_concat:
                fh.write('assign b_s = concat[17:0];\n')
            else:
                if b_width < 18:
                    fh.write('assign b_s = {{{{{}{{b[{}]}}}}, b}};\n'.format(18 - b_width, b_width - 1))
                else:
                    fh.write('assign b_s = b;\n')

        if use_dport:
            if d_width < 25:
                fh.write('assign d_s = {{{{{}{{d[{}]}}}}, d}};\n'.format(25 - d_width, d_width - 1))
            else:
                fh.write('assign d_s = d;\n')

        if use_cport:
            if c_width < 48:
                fh.write('assign c_s = {{{{{}{{c[{}]}}}}, c}};\n'.format(48 - c_width, c_width - 1))
            else:
                fh.write('assign c_s = c;\n')

        fh.write('\n')
        extra_tab = ''
        if infer_logic or rnd:
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            if use_reset:
                fh.write('	if (sync_reset == 1\'b1) begin\n')
                logic_rst(fh, prefix='a_d', cnt=areg_logic, sp='\t\t')
                logic_rst(fh, prefix='b_d', cnt=breg_logic, sp='\t\t')
                logic_rst(fh, prefix='c_d', cnt=creg_logic, sp='\t\t')
                logic_rst(fh, prefix='d_d', cnt=dreg_logic, sp='\t\t')
                logic_rst(fh, prefix='carryreg_d', cnt=carryreg_logic, sp='\t\t')
                logic_rst(fh, prefix='opmode_d', cnt=opmode_logic, sp='\t\t')
                logic_rst(fh, prefix='inmode_d', cnt=inmode_logic, sp='\t\t')
                logic_rst(fh, prefix='alumode_d', cnt=alumode_logic, sp='\t\t')
                logic_rst(fh, prefix='carryin_sel_d', cnt=carryin_sel_logic, sp='\t\t')
                if rnd:
                    fh.write('	          p_d <= 1\'b0;\n')
                fh.write('	end else begin\n')
                extra_tab = ''
                if use_ce:
                    extra_tab = 't'
                    fh.write('    if (ce == 1\'b1) begin\n')
                logic_gate(fh, prefix='a_d', str_val='a_s', cnt=areg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='b_d', str_val='b_s', cnt=breg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='c_d', str_val='c_s', cnt=creg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='d_d', str_val='d_s', cnt=dreg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='carryreg_d', str_val='carryreg', cnt=carryreg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='opmode_d', str_val='next_opmode', cnt=opmode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='inmode_d', str_val='next_inmode', cnt=inmode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='alumode_d', str_val='next_alumode', cnt=alumode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='carryin_sel_d', str_val='next_carryin_sel', cnt=carryin_sel_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                if rnd:
                    fh.write('\t{}p_d <= p_s[0];\n'.format(extra_tab))
                #
                if use_ce:
                    fh.write('    end\n')
                fh.write('  end\n')
            else:
                extra_tab = ''
                if use_ce:
                    extra_tab = '\t'
                    fh.write('    if (ce == 1\'b1) begin\n')
                logic_gate(fh, prefix='a_d', str_val='a_s', cnt=areg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='b_d', str_val='b_s', cnt=breg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='c_d', str_val='c_s', cnt=creg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='d_d', str_val='d_s', cnt=dreg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='carryreg_d', str_val='carryreg', cnt=carryreg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='opmode_d', str_val='next_opmode', cnt=opmode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='alumode_d', str_val='next_alumode', cnt=alumode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='inmode_d', str_val='next_inmode', cnt=inmode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='carryin_sel_d', str_val='next_carryin_sel', cnt=carryin_sel_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                if rnd:
                    fh.write('\t{}p_d <= p_s[0];\n'.format(extra_tab))
                if use_ce:
                    fh.write('    end\n')
            fh.write('end\n\n')

        if multi_opcode:
            extra_tab = ''
            fh.write('always @*\n')
            fh.write('begin\n')
            fh.write('    next_opmode = opmode_d0;\n')
            fh.write('    next_inmode = inmode_d0;\n')
            fh.write('    next_alumode = alumode_d0;\n')
            if carryreg_logic:
                fh.write('    next_carryin_sel = carryin_sel_d0;\n')
            if use_ce:
                fh.write('    if (ce == 1\'b1) begin\n')
                extra_tab = '\t'
            for ii in range(len(opcodes)):
                if ii == 0:
                    fh.write('{}    if (opcode == {}\'d{}) begin\n'.format(extra_tab, opcode_bits, ii))
                else:
                    fh.write('{}    end else if (opcode == {}\'d{}) begin\n'.format(extra_tab, opcode_bits, ii))
                fh.write('{}        next_opmode = 7\'d{};\n'.format(extra_tab, opmodes[ii]))
                fh.write('{}        next_alumode = 4\'d{};\n'.format(extra_tab, alumodes[ii]))
                fh.write('{}        next_inmode = 5\'d{};\n'.format(extra_tab, inmodes[ii]))
                fh.write('{}        next_carryin_sel = 3\'d{};\n'.format(extra_tab, carryin_sels[ii]))
            fh.write('{}    end else begin\n'.format(extra_tab))
            fh.write('{}        next_opmode = 7\'d{};\n'.format(extra_tab, opmodes[0]))
            fh.write('{}        next_alumode = 4\'d{};\n'.format(extra_tab,alumodes[0]))  #analysis:ignore
            fh.write('{}        next_inmode = 5\'d{};\n'.format(extra_tab, inmodes[0]))
            fh.write('{}        next_carryin_sel = 3\'d{};\n'.format(extra_tab, carryin_sels[0]))
            fh.write('{}    end\n'.format(extra_tab))
            if use_ce:
                fh.write('    end\n')
            fh.write('end\n\n')
        fh.write('DSP48E1 #(\n')
        fh.write('    // Feature Control Attributes: Data Path Selection\n')
        fh.write('    .A_INPUT(\"{}\"), // Selects A input source, "DIRECT" (A port) or "CASCADE" (ACIN port)\n'.format(a_source))  #analysis:ignore
        fh.write('    .B_INPUT(\"{}\"), // Selects B input source, "DIRECT" (B port) or "CASCADE" (BCIN port)\n'.format(b_source))  #analysis:ignore
        fh.write('    .USE_DPORT(\"{}\"), // Select D port usage (TRUE or FALSE)\n'.format(dport_str))
        if use_concat and use_mult:
            fh.write('    .USE_MULT("DYNAMIC"), // Select multiplier usage ("MULTIPLY", "DYNAMIC", or "NONE")\n')
        elif use_concat:
            fh.write('    .USE_MULT("NONE"), // Select multiplier usage ("MULTIPLY", "DYNAMIC", or "NONE")\n')
        else:
            fh.write('    .USE_MULT("MULTIPLY"), // Select multiplier usage ("MULTIPLY", "DYNAMIC", or "NONE")\n')

        fh.write('    // Pattern Detector Attributes: Pattern Detection Configuration\n')
        fh.write('    .AUTORESET_PATDET("NO_RESET"), // "NO_RESET", "RESET_MATCH", "RESET_NOT_MATCH"\n')
        fh.write('    .MASK(48\'h3fffffffffff), // 48-bit mask value for pattern detect (1=ignore)\n')
        fh.write('    .PATTERN(48\'h000000000000), // 48-bit pattern match for pattern detect\n')
        fh.write('    .SEL_MASK("MASK"), // "C", "MASK", "ROUNDING_MODE1", "ROUNDING_MODE2"\n')
        fh.write('    .SEL_PATTERN("PATTERN"), // Select pattern value ("PATTERN" or "C")\n')
        fh.write('    .USE_PATTERN_DETECT("NO_PATDET"), // Enable pattern detect ("PATDET" or "NO_PATDET")\n')
        fh.write('    // Register Control Attributes: Pipeline Register Configuration\n')
        fh.write('    .ACASCREG({}), // Number of pipeline stages between A/ACIN and ACOUT (0, 1 or 2)\n'.format(areg))
        fh.write('    .ADREG({}), // Number of pipeline stages for pre-adder (0 or 1)\n'.format(adreg))
        fh.write('    .ALUMODEREG({}), // Number of pipeline stages for ALUMODE (0 or 1)\n'.format(alumode_reg))
        fh.write('    .AREG({}), // Number of pipeline stages for A (0, 1 or 2)\n'.format(areg))
        fh.write('    .BCASCREG({}), // Number of pipeline stages between B/BCIN and BCOUT (0, 1 or 2)\n'.format(breg))
        fh.write('    .BREG({}), // Number of pipeline stages for B (0, 1 or 2)\n'.format(breg))
        fh.write('    .CARRYINREG({}), // Number of pipeline stages for CARRYIN (0 or 1)\n'.format(carryreg))
        fh.write('    .CARRYINSELREG(1), // Number of pipeline stages for CARRYINSEL (0 or 1)\n')
        fh.write('    .CREG({}), // Number of pipeline stages for C (0 or 1)\n'.format(creg))
        fh.write('    .DREG({}), // Number of pipeline stages for D (0 or 1)\n'.format(dreg))
        fh.write('    .INMODEREG({}), // Number of pipeline stages for INMODE (0 or 1)\n'.format(inmode_reg))
        fh.write('    .MREG({}), // Number of multiplier pipeline stages (0 or 1)\n'.format(mreg))
        fh.write('    .OPMODEREG({}), // Number of pipeline stages for OPMODE (0 or 1)\n'.format(opmode_reg))
        fh.write('    .PREG({}), // Number of pipeline stages for P (0 or 1)\n'.format(preg))
        fh.write('    .USE_SIMD("ONE48") // SIMD selection ("ONE48", "TWO24", "FOUR12")\n')
        fh.write(')\n')
        fh.write('dsp_48_inst (\n')
        fh.write('    // Cascade: 30-bit (each) output: Cascade Ports\n')
        if use_acout:
            fh.write('    .ACOUT(acout), // 30-bit output: A port cascade output\n')
        else:
            fh.write('    .ACOUT(), // 30-bit output: A port cascade output\n')

        if use_bcout:
            fh.write('    .BCOUT(bcout), // 18-bit output: B port cascade output\n')
        else:
            fh.write('    .BCOUT(), // 18-bit output: B port cascade output\n')
        fh.write('    .CARRYCASCOUT(), // 1-bit output: Cascade carry output\n')
        fh.write('    .MULTSIGNOUT(), // 1-bit output: Multiplier sign cascade output\n')
        if use_pcout:
            fh.write('    .PCOUT(pcout), // 48-bit output: Cascade output\n')
        else:
            fh.write('    .PCOUT(), // 48-bit output: Cascade output\n')
        fh.write('    // Control: 1-bit (each) output: Control Inputs/Status Bits\n')
        fh.write('    .OVERFLOW(), // 1-bit output: Overflow in add/acc output\n')
        fh.write('    .PATTERNBDETECT(), // 1-bit output: Pattern bar detect output\n')
        fh.write('    .PATTERNDETECT(), // 1-bit output: Pattern detect output\n')
        fh.write('    .UNDERFLOW(), // 1-bit output: Underflow in add/acc output\n')
        fh.write('    // Data: 4-bit (each) output: Data Ports\n')
        fh.write('    .CARRYOUT(), // 4-bit output: Carry output\n')
        if rnd or p_slice:
            fh.write('    .P(p_s), //-- 48-bit output: Primary data output\n')
        else:
            fh.write('    .P(p), // 48-bit output: Primary data output\n')
        fh.write('    // Cascade: 30-bit (each) input: Cascade Ports\n')
        fh.write('    .ACIN({}), // 30-bit input: A cascade data input\n'.format(acin))
        fh.write('    .BCIN({}), // 18-bit input: B cascade input\n'.format(bcin))
        fh.write('    .CARRYCASCIN({}), // 1-bit input: Cascade carry input\n'.format(carrycascin))
        fh.write('    .MULTSIGNIN(1\'b0), // 1-bit input: Multiplier sign input\n')
        fh.write('    .PCIN({}), // 48-bit input: P cascade input\n'.format(pcin))
        fh.write('    // Control: 4-bit (each) input: Control Inputs/Status Bits\n')
        fh.write('    .ALUMODE({}), // 4-bit input: ALU control input\n'.format(alumode_str))
        fh.write('    .CARRYINSEL({}), // 3-bit input: Carry select input\n'.format(carryin_sel_str))
        if multi_opcode:
            fh.write('    .CEINMODE({}), // 1-bit input: Clock enable input for INMODEREG\n'.format(ce))
        else:
            fh.write('    .CEINMODE(1\'b1), // 1-bit input: Clock enable input for INMODEREG\n')
        fh.write('    .CLK(clk), // 1-bit input: Clock input\n')
        fh.write('    .INMODE({}), // 5-bit input: INMODE control input\n'.format(inmode_str))
        fh.write('    .OPMODE({}), // 7-bit input: Operation mode input\n'.format(opmode_str))
        fh.write('    .RSTINMODE({}), // 1-bit input: Reset input for INMODEREG\n'.format(sync_reset))
        fh.write('    // Data: 30-bit (each) input: Data Ports\n')
        fh.write('    .A({}), // 30-bit input: A data input\n'.format(a_val))
        fh.write('    .B({}), // 18-bit input: B data input\n'.format(b_val))
        if rnd:
            fh.write('    .C(48\'d{}), // 48-bit input: C data input\n'.format(c_constant))
        else:
            fh.write('    .C({}), // 48-bit input: C data input\n'.format(c_val))
        fh.write('    .CARRYIN({}), // 1-bit input: Carry input signal\n'.format(carryin))
        fh.write('    .D({}), // 25-bit input: D data input\n'.format(d_val))
        fh.write('    // Reset/Clock Enable: 1-bit (each) input: Reset/Clock Enable Inputs\n')
        fh.write('    .CEA1({}), // 1-bit input: Clock enable input for 1st stage AREG\n'.format(cea1))
        fh.write('    .CEA2({}), // 1-bit input: Clock enable input for 2nd stage AREG\n'.format(cea2))
        fh.write('    .CEAD({}), // 1-bit input: Clock enable input for ADREG\n'.format(ce))
        if multi_opcode:
            fh.write('    .CEALUMODE({}), // 1-bit input: Clock enable input for ALUMODERE\n'.format(ce))
        else:
            fh.write('    .CEALUMODE(1\'b1), // 1-bit input: Clock enable input for ALUMODERE\n')

        fh.write('    .CEB1({}), // 1-bit input: Clock enable input for 1st stage BREG\n'.format(ceb1))
        fh.write('    .CEB2({}), // 1-bit input: Clock enable input for 2nd stage BREG\n'.format(ceb2))
        fh.write('    .CEC({}), // 1-bit input: Clock enable input for CREG\n'.format(ce))
        fh.write('    .CECARRYIN({}), // 1-bit input: Clock enable input for CARRYINREG\n'.format(ce))
        if multi_opcode:
            fh.write('    .CECTRL({}), // 1-bit input: Clock enable input for OPMODEREG and CARRYINSELREG\n'.format(ce))
        else:
            fh.write('    .CECTRL(1\'b1), // 1-bit input: Clock enable input for OPMODEREG and CARRYINSELREG\n')

        fh.write('    .CED({}), // 1-bit input: Clock enable input for DREG\n'.format(ce))
        fh.write('    .CEM({}), // 1-bit input: Clock enable input for MREG\n'.format(ce))
        fh.write('    .CEP({}), // 1-bit input: Clock enable input for PREG\n'.format(ce))
        fh.write('    .RSTA({}), // 1-bit input: Reset input for AREG\n'.format(sync_reset))
        fh.write('    .RSTALLCARRYIN({}), // 1-bit input: Reset input for CARRYINREG\n'.format(sync_reset))
        fh.write('    .RSTALUMODE({}), // 1-bit input: Reset input for ALUMODEREG\n'.format(sync_reset))
        fh.write('    .RSTB({}), // 1-bit input: Reset input for BREG\n'.format(sync_reset))
        fh.write('    .RSTC({}), // 1-bit input: Reset input for CREG\n'.format(sync_reset))
        fh.write('    .RSTCTRL({}), // 1-bit input: Reset input for OPMODEREG and CARRYINSELREG\n'.format(sync_reset))
        fh.write('    .RSTD({}), // 1-bit input: Reset input for DREG and ADREG\n'.format(sync_reset))
        fh.write('    .RSTM({}), // 1-bit input: Reset input for MREG\n'.format(sync_reset))
        fh.write('    .RSTP({}) // 1-bit input: Reset input for PREG\n'.format(sync_reset))
        fh.write(');\n\n')
        fh.write('endmodule\n')

    return file_name, module_name


def gen_dsp48E2(path, name, opcode='A*B', a_width=27, b_width=18, c_width=48, d_width=27,
                areg=1, breg=1, creg=1, dreg=1, mreg=1, preg=1, concatreg=1, carryreg=1,
                use_acout=False, use_bcout=False, use_pcout=False, use_ce=False, use_reset=False, rnd=False,
                p_msb=None, p_lsb=None, a_signed=True, b_signed=True, dither=False, sat_accum=False, 
                mask="48\'h3fffffffffff", pattern="48\'h000000000000"):

    """
        Helper function for instantiating DSP48E2.  Changes from E1 to E2:
        1. Pre-adder can now source A or B ports: (D + B) * A, (D + B)^2, etc
        2. W Port for rounding.  All functions cannot support RND in same operation.  There is a RND attribute, do not
           have to use C port for static Rounding value.  Still would need to use C port for dynamically changed value.

            RND : 48 bit field : This 48-bit value is used as the Rounding Constant into the WMUX

        3. Wide XOR port (not currently implemented in template)
        4. USE_DPORT attribute has been replaced by PREADDINSEL, AMULTSEL, BMULTSEL

            PREADDINSEL : Selects the input to be added with D in the preadder : A, B (A)
            AMULTSEL : Selects the input to the 27-bit A input of the multiplier. In the 7 series primitive DSP48E1
                       the attribute is called USE_DPORT, but has been renamed due to new pre-adder flexibility
                       enhancements (default AMULTSEL = A is equivalent to USE_DPORT=FALSE).

            BMULTSEL : Selects the input to the 18-bit B input of the multiplier
        5.
    """
    def input_port(fh):
        # op_strs = re.findall(r"[\w']+", opcode)
        # for str_val in op_strs
        if use_aport:
            fh.write('    input [{}:0] a,\n'.format(a_msb))
        if use_acin_port:
            fh.write('    input [29:0] acin,\n')
        if use_bport:
            fh.write('    input [{}:0] b,\n'.format(b_msb))
        if use_bcin_port:
            fh.write('    input [29:0] bcin,\n')
        if use_concat:
            fh.write('    input [47:0] concat,\n')
        if use_pcin_port:
            fh.write('    input [47:0] pcin,\n')
        if use_carryin:
            fh.write('    input carryin,\n')
        if use_carrycascin:
            fh.write('    input carrycascin,\n')
        if use_dport:
            fh.write('    input [{}:0] d,\n'.format(d_msb))
        if use_cport:
            fh.write('    input [{}:0] c,\n'.format(c_msb))
        if multi_opcode:
            fh.write('    input [{}:0] opcode,\n'.format(opcode_bits - 1))

    def output_port(fh):
        if use_acout:
            fh.write('    output [29:0] acout,\n')
        if use_bcout:
            fh.write('    output [29:0] bcout,\n')
        if use_pcout:
            fh.write('    output [47:0] pcout,\n')

    assert(path is not None), 'User must specify directory'
    file_name = 'dsp48_{}.v'.format(name)
    file_name = os.path.join(path, file_name)
    module_name = ret_module_name(file_name)
    # parse opcode
    if type(opcode) is list:
        opcodes = copy.copy(opcode)
    else:
        opcodes = [opcode]

    concat_list = []
    two_pports_list = []
    mult_list = []
    aport_list = []
    bport_list = []
    cport_list = []
    dport_list = []
    acin_list = []
    bcin_list = []
    pcin_list = []
    carryin_list = []
    carrycascin_list = []

    for opcode in opcodes:
        temp_dict = ret_opcode_params_e2(opcode)
        concat_list.append(temp_dict['use_concat'])
        two_pports_list.append(temp_dict['use_2pports'])
        mult_list.append(temp_dict['use_mult'])
        aport_list.append(temp_dict['use_aport'])
        bport_list.append(temp_dict['use_bport'])
        cport_list.append(temp_dict['use_cport'])
        dport_list.append(temp_dict['use_dport'])
        acin_list.append(temp_dict['use_acin'])
        bcin_list.append(temp_dict['use_bcin'])
        pcin_list.append(temp_dict['use_pcin'])
        carryin_list.append(temp_dict['use_carryin'])
        carrycascin_list.append(temp_dict['use_carrycascin'])

    use_mult = np.any(mult_list)
    use_2pports = np.any(two_pports_list)
    use_concat = np.any(concat_list)
    use_aport = np.any(aport_list)
    use_bport = np.any(bport_list)
    use_cport = np.any(cport_list)
    use_dport = np.any(dport_list)
    use_acin_port = np.any(acin_list)
    use_bcin_port = np.any(bcin_list)
    use_pcin_port = np.any(pcin_list)
    use_carryin = np.any(carryin_list)
    use_carrycascin = np.any(carrycascin_list)
    use_preadd = use_aport and use_dport
    
    mreg = 0 if not use_mult else mreg

    pcin = 'pcin' if use_pcin_port else '48\'d0'
    a_val = 'a_s' if (use_aport or use_concat) else '30\'d0'
    b_val = 'b_s' if (use_bport or use_concat) else '18\'d1'
    c_val = 'c_s' if use_cport else '48\'d0'
    d_val = 'd_s' if use_dport else '27\'d0'
    acin = 'acin' if use_acin_port else '30\'d0'
    bcin = 'bcin' if use_bcin_port else '18\'d0'
    carryin = 'carryin' if use_carryin else '1\'b0'
    carrycascin = 'carrycascin' if use_carrycascin else '1\'b0'

    multi_opcode = (len(opcodes) > 1)
    opcode_bits = int(np.ceil(np.log2(len(opcodes))))
    opcode_msb = opcode_bits - 1
    op_strs = []
    for opcode in opcodes:
        opcode = opcode.lower()
        op_strs.append(re.findall(r"[\w']+", opcode))
    # op_strs = op_code.split(" ") gives a list of strings:
    a_source = 'DIRECT'
    b_source = 'DIRECT'
    areg_logic = 0
    breg_logic = 0
    creg_logic = 0
    dreg_logic = 0
    concatreg_logic = 0
    carryreg_logic = 0

    opmode_reg = 0
    inmode_reg = 0
    alumode_reg = 0
    carryin_sel_reg = 0

    mult_delay = np.max((areg, breg)) + mreg
    opmode_logic = 0
    opmode_delay = 0
    alumode_delay = 0
    inmode_delay = areg
    if use_concat:
        inmode_delay = np.max((inmode_delay, concatreg))
    if use_cport:
        inmode_delay = np.max((inmode_delay, creg - mreg))

    inmode_logic = 0
    alumode_logic = 0
    carryin_sel_delay = 0
    carryin_sel_logic = 0
    if multi_opcode:
        opmode_delay = np.max((mult_delay, creg))
        # there is an implied 1 tick delay due to the multi_opcode mux.
        opmode_logic = np.max((opmode_delay - 1, 1))
        opmode_reg = np.max((opmode_delay - opmode_logic, 0))
        inmode_reg = np.min((inmode_delay, 1))
        inmode_logic = inmode_delay - inmode_reg
        alumode_delay = opmode_delay
        alumode_reg = opmode_reg
        alumode_logic = opmode_logic
        carryin_sel_delay = opmode_delay
        carryin_sel_reg = opmode_reg
        carryin_sel_logic = opmode_logic

    input_regs = np.max([(areg - 2)*use_aport, (breg - 2)*use_bport, (creg - 1)*use_cport, (dreg - 1)*use_dport, concatreg - 2])
    infer_logic = True if (input_regs + alumode_logic + inmode_logic + opmode_logic) > 0 else False
    infer_logic = True if multi_opcode else infer_logic
    patdet = "PATDET" if sat_accum else "NO_PATDET"

    if use_concat:
        if concatreg > 2:
            breg_logic = concatreg - 2
            areg_logic = concatreg - 2
            areg = 2
            breg = 2
        else:
            areg = concatreg
            breg = concatreg
    else:
        areg_logic = np.max((areg - 2, 0))
        breg_logic = np.max((breg - 2, 0))

    if areg_logic > 0 and (use_aport or use_concat):
        a_val = 'a_d{}'.format(areg_logic - 1)
        areg = 2
    if breg_logic > 0 and (use_bport or use_concat):
        b_val = 'b_d{}'.format(breg_logic - 1)
        breg = 2
    if not use_cport:
        creg = 0
    else:
        if creg > 1 and use_cport:
            creg_logic = creg - 1
            creg = 1
            c_val = 'c_d{}'.format(creg_logic - 1)
    if not use_dport:
        dreg = 0
    else:
        if dreg > 1:
            dreg_logic = dreg - 1
            dreg = 1
            d_val = 'd_d{}'.format(dreg_logic - 1)
    if carryreg > 1:
        carryreg_logic = carryreg - 1
        carryreg = 1

    if use_concat:
        if concatreg > 2:
            breg_logic = concatreg - 2
            areg_logic = concatreg - 2
            areg = 2
            breg = 2
        else:
            areg = concatreg
            breg = concatreg

    adreg = 1 if (use_preadd and areg == 2) else 0
    a_msb = a_width - 1
    b_msb = b_width - 1
    c_msb = c_width - 1
    d_msb = d_width - 1

    ce = 'ce' if use_ce else '1\'b1'
    cea1 = ce if areg >= 1 else '1\'b0'        
    cea2 = ce if areg == 2 else '1\'b0'
    ceb1 = ce if breg >= 1 else '1\'b0'
    ceb2 = ce if breg == 2 else '1\'b0'

    sync_reset = 'sync_reset' if use_reset else '1\'b0'

    a = '{}\'d0'.format(a_width)
    b = '{}\'d0'.format(b_width)
    c = '{}\'d0'.format(c_width)
    d = '27\'d0'
    dport_str = 'FALSE'
    if use_dport:
        dport_str = 'TRUE'

    p_slice = True if (p_msb is not None and p_lsb is not None) else False
    if rnd or p_slice:
        p_width = p_msb - p_lsb + 1
    else:
        p_width = 48

    if rnd:
        assert(use_cport is not True), 'User cannot use c-port when rounding'
        c_constant = int(2**(p_lsb - 1) - 1)
        if use_aport:
            carryin = 'a[0]'
        elif use_bport:
            carryin = 'b[0]'
        else:
            # make this a registered value.
            carryin = 'p_d'

    if dither:
        carryin = 'p_d'

    for str_val in op_strs:
        if str_val == 'acin':
            a_source = 'CASCADE'
        if str_val == 'bcin':
            b_source = 'CASCADE'

    opmodes = []
    inmodes = []
    alumodes = []
    amultsels = []
    bmultsels = []
    preaddsels = []

    carryin_sels = []
    for opcode in opcodes:
        temp0, temp1, temp2, temp3, temp4, temp5, temp6 = comp_opmodes_e2(opcode, areg, breg, rnd)
        opmodes.append(temp0)
        inmodes.append(temp1)
        alumodes.append(temp2)
        carryin_sels.append(temp3)
        amultsels.append(temp4)
        bmultsels.append(temp5)
        preaddsels.append(temp6)

    if opmode_logic:
        opmode_str = 'opmode_d{}'.format(opmode_logic - 1)
    else:
        if multi_opcode:
            opmode_str = 'opmode'
        else:
            opmode_str = '9\'d{}'.format(opmodes[0])

    if inmode_logic:
        inmode_str = 'inmode_d{}'.format(inmode_delay - 2)
    else:
        if multi_opcode:
            inmode_str = 'inmode'
        else:
            inmode_str = '5\'d{}'.format(inmodes[0])


    if alumode_logic:
        alumode_str = 'alumode_d{}'.format(alumode_delay - 2)
    else:
        if multi_opcode:
            alumode_str = 'alumode'
        else:
            alumode_str = '4\'d{}'.format(alumodes[0])

    if carryin_sel_logic:
        carryin_sel_str = 'carryin_sel_d{}'.format(carryin_sel_logic - 1)
    else:
        if multi_opcode:
            carryin_sel_str = 'carryin_sel'
        else:
            carryin_sel_str = '3\'d{}'.format(carryin_sels[0])


    with open(file_name, "w") as fh:

        fh.write('module {}\n'.format(module_name))
        fh.write('(\n')
        if use_reset:
            fh.write('    input sync_reset,\n')
        fh.write('    input clk,\n')
        if use_ce:
            fh.write('    input ce,\n')
        fh.write('\n')

        input_port(fh)
        output_port(fh)
        # fh.write('\n')
        fh.write('    output [{}:0] p\n'.format(p_width - 1))
        fh.write(');\n\n')
        if use_aport or use_concat:
            fh.write('wire [29:0] a_s;\n')
        if use_bport or use_concat:
            fh.write('wire [17:0] b_s;\n')
        if use_cport:
            fh.write('wire [47:0] c_s;\n')
        if use_dport:
            fh.write('wire [24:0] d_s;\n')
        if rnd or p_slice:
            fh.write('wire [47:0] p_s;\n')
            fh.write('reg p_d = 1\'b0;\n')
        fh.write('\n')
        fh.write('wire overflow, underflow;\n')
        if multi_opcode:
            fh.write('wire [{}:0] opcode_s;'.format(opcode_msb))
        if infer_logic:
            gen_regs(fh, prefix='a_d', cnt=areg_logic, sp='', msb=29)
            gen_regs(fh, prefix='b_d', cnt=breg_logic, sp='', msb=17)
            gen_regs(fh, prefix='c_d', cnt=creg_logic, sp='', msb=47)
            gen_regs(fh, prefix='d_d', cnt=dreg_logic, sp='', msb=24)
            gen_regs(fh, prefix='carryreg_d', cnt=carryreg_logic, sp='', msb=0)
            # print("opmode_logic = {}".format(opmode_logic))
            gen_regs(fh, prefix='opmode_d', cnt=opmode_logic, sp='', msb=8)
            gen_regs(fh, prefix='inmode_d', cnt=inmode_logic, sp='', msb=4)
            gen_regs(fh, prefix='alumode_d', cnt=alumode_logic, sp='', msb=3)
            gen_regs(fh, prefix='carryin_sel_d', cnt=carryin_sel_logic, sp='', msb=2)
            if multi_opcode is True:
                gen_regs(fh, prefix='next_alumode', cnt=1, sp='', msb=3, str_val='next_alumode')
                gen_regs(fh, prefix='next_carryin_sel', cnt=1, sp='', msb=2, str_val='next_carryin_sel')
                gen_regs(fh, prefix='next_inmode', cnt=1, sp='', msb=4, str_val='next_inmode')
                gen_regs(fh, prefix='next_opmode', cnt=1, sp='', msb=6, str_val='next_opmode')

        fh.write('\n')
        if multi_opcode:
            if sat_accum:
                zero_pad = '{}\'b{}'.format(opcode_bits-2, '0' * (opcode_bits - 2))
                fh.write('assign opcode_s = {{underflow, overflow, {}}}  | opcode;\n'.format(zero_pad))
            else:
                fh.write('assign opcode_s = opcode;\n')
        
        if rnd or p_slice:
            fh.write('assign p = p_s[{}:{}];\n'.format(p_msb, p_lsb))
        if use_aport or use_concat:
            if use_concat:
                fh.write('assign a_s = concat[47:18];\n')  # {{{{{}{{a[{}]}}}}, a}};\n'.format(30 - a_width, a_width - 1))
            else:
                fh.write('assign a_s = {{{{{}{{a[{}]}}}}, a}};\n'.format(30 - a_width, a_width - 1))

        if use_bport or use_concat:
            if use_concat:
                fh.write('assign b_s = concat[17:0];\n')
            else:
                if b_width < 18:
                    fh.write('assign b_s = {{{{{}{{b[{}]}}}}, b}};\n'.format(18 - b_width, b_width - 1))
                else:
                    fh.write('assign b_s = b;\n')

        if use_dport:
            if d_width < 27:
                fh.write('assign d_s = {{{{{}{{d[{}]}}}}, d}};\n'.format(27 - d_width, d_width - 1))
            else:
                fh.write('assign d_s = d;\n')

        if use_cport:
            if c_width < 48:
                fh.write('assign c_s = {{{{{}{{c[{}]}}}}, c}};\n'.format(48 - c_width, c_width - 1))
            else:
                fh.write('assign c_s = c;\n')

        fh.write('\n')
        extra_tab = ''
        if infer_logic or rnd:
            fh.write('always @(posedge clk)\n')
            fh.write('begin\n')
            if use_reset:
                fh.write('	if (sync_reset == 1\'b1) begin\n')
                logic_rst(fh, prefix='a_d', cnt=areg_logic, sp='\t\t')
                logic_rst(fh, prefix='b_d', cnt=breg_logic, sp='\t\t')
                logic_rst(fh, prefix='c_d', cnt=creg_logic, sp='\t\t')
                logic_rst(fh, prefix='d_d', cnt=dreg_logic, sp='\t\t')
                logic_rst(fh, prefix='carryreg_d', cnt=carryreg_logic, sp='\t\t')
                logic_rst(fh, prefix='opmode_d', cnt=opmode_logic, sp='\t\t')
                logic_rst(fh, prefix='inmode_d', cnt=inmode_logic, sp='\t\t')
                logic_rst(fh, prefix='alumode_d', cnt=alumode_logic, sp='\t\t')
                logic_rst(fh, prefix='carryin_sel_d', cnt=carryin_sel_logic, sp='\t\t')
                if rnd or dither:
                    fh.write('	          p_d <= 1\'b0;\n')
                fh.write('	end else begin\n')
                extra_tab = ''
                if use_ce:
                    extra_tab = 't'
                    fh.write('    if (ce == 1\'b1) begin\n')
                logic_gate(fh, prefix='a_d', str_val='a_s', cnt=areg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='b_d', str_val='b_s', cnt=breg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='c_d', str_val='c_s', cnt=creg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='d_d', str_val='d_s', cnt=dreg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='carryreg_d', str_val='carryreg', cnt=carryreg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='opmode_d', str_val='next_opmode', cnt=opmode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='inmode_d', str_val='next_inmode', cnt=inmode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='alumode_d', str_val='next_alumode', cnt=alumode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='carryin_sel_d', str_val='next_carryin_sel', cnt=carryin_sel_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                if rnd or dither:
                    fh.write('\t{}p_d <= p_s[0];\n'.format(extra_tab))
                #
                if use_ce:
                    fh.write('    end\n')
                fh.write('  end\n')
            else:
                extra_tab = ''
                if use_ce:
                    extra_tab = '\t'
                    fh.write('    if (ce == 1\'b1) begin\n')
                logic_gate(fh, prefix='a_d', str_val='a_s', cnt=areg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='b_d', str_val='b_s', cnt=breg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='c_d', str_val='c_s', cnt=creg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='d_d', str_val='d_s', cnt=dreg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='carryreg_d', str_val='carryreg', cnt=carryreg_logic, sp='\t{}'.format(extra_tab))
                logic_gate(fh, prefix='opmode_d', str_val='next_opmode', cnt=opmode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='alumode_d', str_val='next_alumode', cnt=alumode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='inmode_d', str_val='next_inmode', cnt=inmode_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                logic_gate(fh, prefix='carryin_sel_d', str_val='next_carryin_sel', cnt=carryin_sel_logic, sp='\t{}'.format(extra_tab))  #analysis:ignore
                if rnd:
                    fh.write('\t{}p_d <= p_s[0];\n'.format(extra_tab))
                if use_ce:
                    fh.write('    end\n')
            fh.write('end\n\n')

        if multi_opcode:
            extra_tab = ''
            fh.write('always @*\n')
            fh.write('begin\n')
            fh.write('    next_opmode = opmode_d0;\n')
            fh.write('    next_inmode = inmode_d0;\n')
            fh.write('    next_alumode = alumode_d0;\n')
            if carryreg_logic:
                fh.write('    next_carryin_sel = carryin_sel_d0;\n')
            if use_ce:
                fh.write('    if (ce == 1\'b1) begin\n')
                extra_tab = '\t'
            for ii in range(len(opcodes)):
                if ii == 0:
                    fh.write('{}    if (opcode_s == {}\'d{}) begin\n'.format(extra_tab, opcode_bits, ii))
                else:
                    fh.write('{}    end else if (opcode_s == {}\'d{}) begin\n'.format(extra_tab, opcode_bits, ii))
                fh.write('{}        next_opmode = 9\'d{};\n'.format(extra_tab, opmodes[ii]))
                fh.write('{}        next_alumode = 4\'d{};\n'.format(extra_tab, alumodes[ii]))
                fh.write('{}        next_inmode = 5\'d{};\n'.format(extra_tab, inmodes[ii]))
                fh.write('{}        next_carryin_sel = 3\'d{};\n'.format(extra_tab, carryin_sels[ii]))
            fh.write('{}    end else begin\n'.format(extra_tab))
            fh.write('{}        next_opmode = 9\'d{};\n'.format(extra_tab, opmodes[0]))
            fh.write('{}        next_alumode = 4\'d{};\n'.format(extra_tab,alumodes[0]))  #analysis:ignore
            fh.write('{}        next_inmode = 5\'d{};\n'.format(extra_tab, inmodes[0]))
            fh.write('{}        next_carryin_sel = 3\'d{};\n'.format(extra_tab, carryin_sels[0]))
            fh.write('{}    end\n'.format(extra_tab))
            if use_ce:
                fh.write('    end\n')
            fh.write('end\n\n')
        fh.write('DSP48E2 #(\n')
        fh.write('    // Feature Control Attributes: Data Path Selection\n')
        fh.write('    .A_INPUT(\"{}\"), // Selects A input source, "DIRECT" (A port) or "CASCADE" (ACIN port)\n'.format(a_source))  #analysis:ignore
        fh.write('    .B_INPUT(\"{}\"), // Selects B input source, "DIRECT" (B port) or "CASCADE" (BCIN port)\n'.format(b_source))  #analysis:ignore
        # fh.write('    .USE_DPORT(\"{}\"), // Select D port usage (TRUE or FALSE)\n'.format(dport_str))
        if use_concat and use_mult:
            fh.write('    .USE_MULT("DYNAMIC"), // Select multiplier usage ("MULTIPLY", "DYNAMIC", or "NONE")\n')
        elif use_concat:
            fh.write('    .USE_MULT("NONE"), // Select multiplier usage ("MULTIPLY", "DYNAMIC", or "NONE")\n')
        else:
            fh.write('    .USE_MULT("MULTIPLY"), // Select multiplier usage ("MULTIPLY", "DYNAMIC", or "NONE")\n')

        fh.write('    // Pattern Detector Attributes: Pattern Detection Configuration\n')
        fh.write('    .AUTORESET_PATDET("NO_RESET"), // "NO_RESET", "RESET_MATCH", "RESET_NOT_MATCH"\n')
        rnd_word = '48\'d{}'.format(c_constant) if rnd else "48\'d0"
        fh.write('    .RND({}), // 48-bit input: RND parameter generic\n'.format(rnd_word))
        fh.write('    .MASK({}), // 48-bit mask value for pattern detect (1=ignore)\n'.format(mask))
        fh.write('    .PATTERN({}), // 48-bit pattern match for pattern detect\n'.format(pattern))
        fh.write('    .SEL_MASK("MASK"), // "C", "MASK", "ROUNDING_MODE1", "ROUNDING_MODE2"\n')
        fh.write('    .SEL_PATTERN("PATTERN"), // Select pattern value ("PATTERN" or "C")\n')
        fh.write('    .USE_PATTERN_DETECT("{}"), // Enable pattern detect ("PATDET" or "NO_PATDET")\n'.format(patdet))
        fh.write('    // Register Control Attributes: Pipeline Register Configuration\n')
        fh.write('    .ACASCREG({}), // Number of pipeline stages between A/ACIN and ACOUT (0, 1 or 2)\n'.format(areg))
        fh.write('    .ADREG({}), // Number of pipeline stages for pre-adder (0 or 1)\n'.format(adreg))
        fh.write('    .ALUMODEREG({}), // Number of pipeline stages for ALUMODE (0 or 1)\n'.format(alumode_reg))
        fh.write('    .AREG({}), // Number of pipeline stages for A (0, 1 or 2)\n'.format(areg))
        fh.write('    .BCASCREG({}), // Number of pipeline stages between B/BCIN and BCOUT (0, 1 or 2)\n'.format(breg))
        fh.write('    .BREG({}), // Number of pipeline stages for B (0, 1 or 2)\n'.format(breg))
        fh.write('    .CARRYINREG({}), // Number of pipeline stages for CARRYIN (0 or 1)\n'.format(carryreg))
        fh.write('    .CARRYINSELREG(1), // Number of pipeline stages for CARRYINSEL (0 or 1)\n')
        fh.write('    .CREG({}), // Number of pipeline stages for C (0 or 1)\n'.format(creg))
        fh.write('    .DREG({}), // Number of pipeline stages for D (0 or 1)\n'.format(dreg))
        fh.write('    .INMODEREG({}), // Number of pipeline stages for INMODE (0 or 1)\n'.format(inmode_reg))
        fh.write('    .MREG({}), // Number of multiplier pipeline stages (0 or 1)\n'.format(mreg))
        fh.write('    .OPMODEREG({}), // Number of pipeline stages for OPMODE (0 or 1)\n'.format(opmode_reg))
        fh.write('    .PREG({}), // Number of pipeline stages for P (0 or 1)\n'.format(preg))
        fh.write('    .PREADDINSEL("{}"), // Selects the input to be added with D in the preadder\n'.format(preaddsels[0]))
        fh.write('    .AMULTSEL("{}"), // Selects the input to the 27-bit A input of the multiplier. In the 7 series primitive DSP48E1 the attribute is called USE_DPORT\n'.format(str(amultsels[0]).upper()))
        fh.write('    .BMULTSEL("{}"), // Selects the input to the 18-bit B input of the multiplier.\n'.format(bmultsels[0]))
        fh.write('    .USE_SIMD("ONE48"), // SIMD selection ("ONE48", "TWO24", "FOUR12")\n')
        fh.write('    .USE_WIDEXOR("FALSE"),\n')
        fh.write('    .XORSIMD("XOR12") // Selects the mode of operation for the Wide XOR. \n')
        fh.write(')\n')
        fh.write('dsp_48_inst (\n')
        fh.write('    // Cascade: 30-bit (each) output: Cascade Ports\n')
        acout_word = 'acout' if use_acout else ''
        fh.write('    .ACOUT({}), // 30-bit output: A port cascade output\n'.format(acout_word))
        bcout_word = 'bcout' if use_bcout else ''
        fh.write('    .BCOUT({}), // 18-bit output: B port cascade output\n'.format(bcout_word))
        fh.write('    .CARRYCASCOUT(), // 1-bit output: Cascade carry output\n')
        fh.write('    .MULTSIGNOUT(), // 1-bit output: Multiplier sign cascade output\n')
        pcout_word = 'pcout' if use_pcout else ''
        fh.write('    .PCOUT({}), // 48-bit output: Cascade output\n'.format(pcout_word))
        fh.write('    .XOROUT(),\n')  # XOROUT is not currently supported.
        fh.write('    // Control: 1-bit (each) output: Control Inputs/Status Bits\n')
        fh.write('    .OVERFLOW(overflow), // 1-bit output: Overflow in add/acc output\n')
        fh.write('    .PATTERNBDETECT(), // 1-bit output: Pattern bar detect output\n')
        fh.write('    .PATTERNDETECT(), // 1-bit output: Pattern detect output\n')
        fh.write('    .UNDERFLOW(underflow), // 1-bit output: Underflow in add/acc output\n')
        fh.write('    // Data: 4-bit (each) output: Data Ports\n')
        fh.write('    .CARRYOUT(), // 4-bit output: Carry output\n')
        p_word = 'p_s' if rnd else 'p'
        fh.write('    .P({}), //-- 48-bit output: Primary data output\n'.format(p_word))
        fh.write('    // Cascade: 30-bit (each) input: Cascade Ports\n')
        fh.write('    .ACIN({}), // 30-bit input: A cascade data input\n'.format(acin))
        fh.write('    .BCIN({}), // 18-bit input: B cascade input\n'.format(bcin))
        fh.write('    .CARRYCASCIN({}), // 1-bit input: Cascade carry input\n'.format(carrycascin))
        fh.write('    .MULTSIGNIN(1\'b0), // 1-bit input: Multiplier sign input\n')
        fh.write('    .PCIN({}), // 48-bit input: P cascade input\n'.format(pcin))
        fh.write('    // Control: 4-bit (each) input: Control Inputs/Status Bits\n')
        fh.write('    .ALUMODE({}), // 4-bit input: ALU control input\n'.format(alumode_str))
        fh.write('    .CARRYINSEL({}), // 3-bit input: Carry select input\n'.format(carryin_sel_str))
        ceinmode_word = ce if multi_opcode else '1\'b1'
        fh.write('    .CEINMODE({}), // 1-bit input: Clock enable input for INMODEREG\n'.format(ceinmode_word))
        fh.write('    .CLK(clk), // 1-bit input: Clock input\n')
        fh.write('    .INMODE({}), // 5-bit input: INMODE control input\n'.format(inmode_str))
        fh.write('    .OPMODE({}), // 7-bit input: Operation mode input\n'.format(opmode_str))
        fh.write('    .RSTINMODE({}), // 1-bit input: Reset input for INMODEREG\n'.format(sync_reset))
        fh.write('    // Data: 30-bit (each) input: Data Ports\n')
        fh.write('    .A({}), // 30-bit input: A data input\n'.format(a_val))
        fh.write('    .B({}), // 18-bit input: B data input\n'.format(b_val))
        c_word = rnd_word = '48\'d{}'.format(c_constant) if rnd else c_val
        fh.write('    .C({}), // 48-bit input: C data input\n'.format(c_word))
        fh.write('    .CARRYIN({}), // 1-bit input: Carry input signal\n'.format(carryin))
        fh.write('    .D({}), // 27-bit input: D data input\n'.format(d_val))
        fh.write('    // Reset/Clock Enable: 1-bit (each) input: Reset/Clock Enable Inputs\n')
        fh.write('    .CEA1({}), // 1-bit input: Clock enable input for 1st stage AREG\n'.format(cea1))
        fh.write('    .CEA2({}), // 1-bit input: Clock enable input for 2nd stage AREG\n'.format(cea2))
        fh.write('    .CEAD({}), // 1-bit input: Clock enable input for ADREG\n'.format(ce))
        cealumode_word = ce if multi_opcode else '1\'b1'
        fh.write('    .CEALUMODE({}), // 1-bit input: Clock enable input for ALUMODERE\n'.format(cealumode_word))
        fh.write('    .CEB1({}), // 1-bit input: Clock enable input for 1st stage BREG\n'.format(ceb1))
        fh.write('    .CEB2({}), // 1-bit input: Clock enable input for 2nd stage BREG\n'.format(ceb2))
        fh.write('    .CEC({}), // 1-bit input: Clock enable input for CREG\n'.format(ce))
        fh.write('    .CECARRYIN({}), // 1-bit input: Clock enable input for CARRYINREG\n'.format(ce))
        cectrl_word = ce if multi_opcode else '1\'b1'
        fh.write('    .CECTRL({}), // 1-bit input: Clock enable input for OPMODEREG and CARRYINSELREG\n'.format(cectrl_word))
        fh.write('    .CED({}), // 1-bit input: Clock enable input for DREG\n'.format(ce))
        fh.write('    .CEM({}), // 1-bit input: Clock enable input for MREG\n'.format(ce))
        fh.write('    .CEP({}), // 1-bit input: Clock enable input for PREG\n'.format(ce))
        fh.write('    .RSTA({}), // 1-bit input: Reset input for AREG\n'.format(sync_reset))
        fh.write('    .RSTALLCARRYIN({}), // 1-bit input: Reset input for CARRYINREG\n'.format(sync_reset))
        fh.write('    .RSTALUMODE({}), // 1-bit input: Reset input for ALUMODEREG\n'.format(sync_reset))
        fh.write('    .RSTB({}), // 1-bit input: Reset input for BREG\n'.format(sync_reset))
        fh.write('    .RSTC({}), // 1-bit input: Reset input for CREG\n'.format(sync_reset))
        fh.write('    .RSTCTRL({}), // 1-bit input: Reset input for OPMODEREG and CARRYINSELREG\n'.format(sync_reset))
        fh.write('    .RSTD({}), // 1-bit input: Reset input for DREG and ADREG\n'.format(sync_reset))
        fh.write('    .RSTM({}), // 1-bit input: Reset input for MREG\n'.format(sync_reset))
        fh.write('    .RSTP({}) // 1-bit input: Reset input for PREG\n'.format(sync_reset))
        fh.write(');\n\n')
        fh.write('endmodule\n')

    return file_name, module_name
