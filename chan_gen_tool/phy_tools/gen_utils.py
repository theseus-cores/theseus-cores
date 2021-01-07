# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 17:01:28 2016

@author: phil
"""
import copy
from phy_tools import fp_utils
from phy_tools.fp_utils import xor_list
import ipdb
import numpy as np
import time
import re
import scipy.signal as signal
import struct
from itertools import count
from scipy.special import erfc, comb
import os
from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    __version__ = today.strftime("%Y.%m.%d")

mod_dict_default = {'shape_filt': 'rrcosine', 'mod_type': 'qpsk', 'beta': .2, }
mod_dict = {'bpsk': 1, 'qpsk': 2, 'qam16': 4, 'qam64': 6}


class RingArray(np.ndarray):

    def __getslice__(self, lidx, ridx):
        """
            Overloaded getslice method.
        """
        lidxTemp = lidx % len(self)
        ridxTemp = ridx % len(self)
        if (ridxTemp < lidxTemp):
            temp1 = np.ndarray.__getslice__(self, lidxTemp, len(self))
            temp2 = np.ndarray.__getslice__(self, 0, ridxTemp)
            return np.concatenate((temp1, temp2))
        elif (ridx == len(self)):
            return np.ndarray.__getslice__(self, lidxTemp, ridx)
        else:
            return np.ndarray.__getslice__(self, lidxTemp, ridxTemp)

class RingList(list):

    def __getslice__(self, lidx, ridx):
        """
            Overloaded getslice method.
        """
        lidxTemp = lidx % len(self)
        ridxTemp = ridx % len(self)
        if (ridxTemp < lidxTemp):
            temp1 = list.__getslice__(self, lidxTemp, len(self))
            temp2 = list.__getslice__(self, 0, ridxTemp)
            return temp1 + temp2
        elif (ridx == len(self)):
            return list.__getslice__(self, lidxTemp, ridx)
        else:
            return list.__getslice__(self, lidxTemp, ridxTemp)

class RingBuffer(object):
    def __init__(self, size, padding=None, dtype=np.float):
        self.size = size
        self.padding = size if padding is None else padding
        self.buffer = np.zeros(self.size + self.padding, dtype=dtype)
        self.counter = 0

    def append(self, data):
        """this is an O(n) operation"""
        # data = data[-self.padding:]
        data = np.atleast_1d(data)
        n = len(data)
        if self.remaining < n:
            self.compact()

        self.buffer[self.counter + self.size:][:n] = data
        self.counter += n

    @property
    def remaining(self):
        return self.padding - self.counter

    @property
    def view(self):
        """this is always an O(1) operation"""
        return self.buffer[self.counter:][:self.size]

    def compact(self):
        """
            note: only when this function is called, is an O(size) performance hit
            incurred, and this cost is amortized over the whole padding space
        """
        # print 'compacting'
        self.buffer[:self.size] = self.view
        self.counter = 0

def print_libraries(fh):
    fh.write('library ieee;\n')
    fh.write('use ieee.std_logic_1164.all;\n')
    fh.write('use ieee.numeric_std.all;\n') #analysis:ignore

def print_intro(fh, module_name):
    fh.write('package {}_cmp is\n'.format(module_name))
    fh.write('    component {}\n'.format(module_name))

def print_exit(fh, module_name):
    fh.write('    end component;\n')
    fh.write('end package {}_cmp;\n'.format(module_name))

def print_entity_intro(fh, module_name):
    fh.write('entity {} is\n'.format(module_name))
    fh.write('    port\n')
    fh.write('    (\n')

def calc_errors(vec0, vec1, name, block=0):

    error_vec = xor_list(vec0, vec1)
    num_errors = np.sum(error_vec)
    print("number of {} errors in block {} = {}".format(name, block, num_errors))

    # print error locations
    if num_errors > 0:
        indices = np.nonzero(error_vec)[0].tolist()
        print("{} Error indices in block {} = {}".format(name, block, indices))

def squared_error(vec, ref):
    """
        Helper function computes squared error between vec and reference, ref.
    """
    return [np.abs(value - ref_v) ** 2. for (value, ref_v) in zip(vec, ref)]

def str_find_all(str_input, match_val):
    """
        Function returns indexes of all occurrences of matchVal inside of str_input
    """
    return [m.start() for m in re.finditer(match_val, str_input)]

def calc_pad(ref_len, non_pad_len):
    remainder = non_pad_len % ref_len
    pad = ref_len - remainder if remainder else 0

    return pad

def cart2pol(x, y):
    """
        Convert from Cartesian to polar coordinates.

        Example
        -------
        >>> theta, radius = pol2cart(x, y)
    """
    radius = np.hypot(x, y)
    theta = np.arctan2(y, x)
    return theta, radius


def compass(u, v, ax, arrowprops=None):
    """
        Compass draws a graph that displays the vectors with
        components `u` and `v` as arrows from the origin.

        Examples
        --------
        >>> import numpy as np
        >>> u = [+0, +0.5, -0.50, -0.90]
        >>> v = [+1, +0.5, -0.45, +0.85]
        >>> compass(u, v)
    """
    angles, radii = cart2pol(u, v)
    kw = dict(arrowstyle="->", color='k')
    if arrowprops:
        kw.update(arrowprops)

    [ax.annotate("", xy=(angle, radius), xytext=(0, 0), arrowprops=kw) for angle, radius in zip(angles, radii)]
    ax.set_ylim(0, np.max(radii))

    return ax

def conv_to_sym(data, sym_index):
    """
        Performs symbol mapping.

        ==========
        Parameters
        ==========

        data          : int
            Binary string of 1's and 0's.

        * sym_index   : symbol mapping order as though input is an index.

        =======
        Returns
        =======

        * syms     : IQ symbols of mapped data
    """
    data_int = data.copy()
    data_int = fp_utils.bin_array_to_uint(data_int.T)

    return sym_index[data_int]

def gen_syms(sym_index, bits_per_sym, data=None):
    """
        Main generator method for creating symbol map and mapping data onto
        said map.
    """
    if data is None:
        np.random.seed(42)
        data = np.round(np.random.rand(1000,)).astype(int)

    # truncate extra data
    ridx = len(data) - np.remainder(len(data), bits_per_sym)
    data = data[:ridx]

    data_reshape = np.reshape(data, (bits_per_sym, -1), order='F')

    return conv_to_sym(data_reshape, sym_index)

def ret_sym_index(bit_map, sym_map):
    """
        Helper function remaps sym_map into a single dimension list used
        for mapping of bits to symbols.
    """
    bit_map_dec = np.zeros(np.shape(bit_map))
    for ii, val in np.ndenumerate(bit_map):
        # binary strign
        bit_map_dec[ii] = int(val, 2)

    # reshape sym_map into sequential row vector
    # used as bits to symbol mapper.
    sym_map_rsh = np.ravel(sym_map)
    bit_map_rsh = np.ravel(bit_map_dec)
    idx = np.argsort(bit_map_rsh)

    return sym_map_rsh[idx]

def sweep_func(in_vec, sweep_freqs=None, dwell_time=0, start_freq=None, stop_freq=None, num_sweeps=1):
    """
        Function performs frequency sweeping of input signal.
    """
    output = np.zeros(np.shape(in_vec))
    vec_len = np.size(in_vec)
    if (sweep_freqs is None):
        curr_step = 0
        if (start_freq is not None):
            curr_step = start_freq * np.pi

        end_freq = 2 * np.pi
        start_freq = curr_step
        if (stop_freq is not None):
            if (stop_freq < 0):
                stop_freq = stop_freq + 1  # using normalized frequency units.
            end_freq = np.pi * stop_freq
            assert (start_freq < end_freq), ('Must specify start and stop frequencies in increasing order')
        step_size = num_sweeps * (end_freq - start_freq) / vec_len
        max_step = end_freq
        min_step = start_freq
        sweep_dir = 1
        fl = output.flat
        for ii in range(vec_len):
            sub_idx = fl.coords
            output[sub_idx] = np.exp(1j * curr_step * ii) * in_vec[sub_idx]
            curr_step = curr_step + sweep_dir * step_size
            if (curr_step >= max_step or curr_step <= min_step):
                sweep_dir = -1 * sweep_dir
            fl.next()
    else:
        if (stop_freq < 0):
            stop_freq = stop_freq + 1
        freq_steps = (stop_freq - start_freq + 1) / sweep_freqs
        est_dwell_time = np.floor((vec_len) / (freq_steps * num_sweeps))
        if (dwell_time is not None):
            est_dwell_time = dwell_time
        dwell_count = 0
        start_freq = np.pi * start_freq
        stop_freq = np.pi * stop_freq
        min_step = start_freq
        max_step = stop_freq
        sweep_dir = 1
        curr_step = start_freq
        fl = output.flat
        for ii in range(vec_len):
            sub_idx = fl.coords
            output[sub_idx] = np.exp(1j * curr_step * ii) * in_vec[sub_idx]
            if (dwell_count >= est_dwell_time):
                dwell_count = 0
                curr_step = curr_step + sweep_dir * freq_steps
            if (curr_step >= max_step or curr_step <= min_step):
                sweep_dir = -1 * sweep_dir
            dwell_count += 1
            fl.next()

    return (output, dwell_time, start_freq, stop_freq, sweep_freqs, num_sweeps)


def schmidl_cox_est(input_sig, block_size=256, corr_size=256, num_blocks=2, min_pwr=None):
    """
    ==========
    Parameters
    ==========

        * input_sig : (ndarray) complex
            Input signal
        * corr_size : (int)
            number of samples that repeat in the preamble.
        * block_size: (int)
            number of samples between self-correlations.
        * num_blocks : (int)
            total number of correlated blocks in preamble per correlation.
        * min_pwr : (float)
            minimum power of auto_correlation values to be used for
            normalization.
        * numCorrs : int
            Total number of self correlations.

    =======
    Returns
    =======

        out : dict -- (timing_est,timing_est_norm,phase_angle,auto_corr,retSig)

            * timing_est     : gross timing estimate based on self correlation.
            * timing_est_norm : normalized timing estimate
                -- normalized by auto_correlation or power estimate.
            * phase_angle    : frequency offset estimate.
            * auto_corr      : auto_correlation estimate.
            * ret_sig       : returned signal.

    """
    sig_offsets = []
    # create offset signal vector for cross correlation
    for ii in range(num_blocks):
        offset = ii * block_size
        temp = np.roll(input_sig, -offset)
        sig_offsets.append(temp)

    # perform complex cross correlation (complex conjugate second term)
    auto_corr = 0
    p_d = 0
    r_d = 0
    # comp_conj = 0
    for ii in range(num_blocks - 1):
        p_d += np.conj(sig_offsets[ii]) * sig_offsets[ii + 1]
        r_d += np.abs(sig_offsets[ii + 1]) ** 2.

    # shift r_d by block_size
    r_d = np.roll(r_d, block_size)
    # now sum over block lengths.
    fil_b = np.ones((corr_size,)) / corr_size
    p_d = signal.upfirdn(fil_b, p_d)
    r_d = signal.upfirdn(fil_b, r_d)
    phase_angle = np.angle(p_d)
    # replace 0's in auto_corr with mean -- avoids infinities.
    idx = (r_d == 0.)
    r_d[idx] = np.mean(r_d)
    if min_pwr is not None:
        min_pwr = min_pwr
        idx = (r_d < min_pwr)
        r_d[idx] = min_pwr
        p_d[idx] = 0.

    p_d2 = np.abs(p_d) ** 2
    r_d2 = r_d ** 2

    if num_blocks <= 1:
        max_shift = 0
    else:
        max_shift = (num_blocks - 2) * block_size
    # phase_angle = np.angle(signal.upfirdn(fil_b, p_d))
    # need to roll phase_angle by maximum shift
    phase_angle = np.roll(phase_angle, max_shift)
    timing_est_norm = p_d2 / r_d2
    trunc = corr_size - 1

    return (timing_est_norm[:-trunc], phase_angle[:-trunc], p_d2[:-trunc], r_d2[:-trunc])

def gen_map(xcode_shift=0, ycode_shift=0, mod_type='psk', psk_offset=0, Es_avg=None, psk_order=None):
    """
        Converts binary data to a graycoded symbol map of either PSK or QAM
        constellation.  Computes the constellation mapping and converts input
        data to constellation symbols.

        ==========
        Parameters
        ==========

        * xcode_shift  : int (0)
            Circular shift of a QAM constellation's x-axis bit mapping
        * ycode_shift  : int (0)
            Circular shift of a QAM constellation's y-axis bit mapping
        * psk_type     : bool (False)
            Indicates that constellation is of a PSK type.
        * psk_offset   : float (0)
            phase offset of PSK constellation in radians.

        =======
        Returns
        =======

        * data     : uncoded original data
        * map      : constellation symbol mapping (graycoded integers)
        * syms     : IQ symbols of mapped data
        * bit_map   : binary constellation mapping.

    """
    k = int(np.log2(psk_order)) if (str.lower(mod_type) == 'psk') else mod_dict[str.lower(mod_type)]
    # k = bits_per_sym #np.min(np.shape(data)) #bits per symbol.
    # firstCorner -- specifies which constellation
    # data = bin2Uint(data) #uintConv(data,size(data,2))
    num_const = 2**k
    if (mod_type.lower() == 'psk'):
        sym_index = range(0, 2**k)
        # Phase alphabet
        phase_alpha = np.arange(psk_offset, 2 * np.pi + psk_offset, (2 * np.pi / num_const))
        phase_alpha = phase_alpha[0:num_const]

        bit_map_dec = gray_code(sym_index)['map']
        temp = bit_map_dec[sym_index]

        # [None]*num_const # intialize list.
        bit_map = fp_utils.dec_to_ubin(temp)
        bit_map = [val[2:] for val in bit_map]
        # now take gray coded data and map them to the PSK alphabet
        sym_map = np.cos(phase_alpha) + 1j * np.sin(phase_alpha)

    else:
        # binMap   = range(orderInt)  # Binary mapping to be map to specified code
        dim = 2**(k // 2)
        # mapping the first k/2 bits to the I-channel
        # if bpsk then only map to I channel only else mapping the bottom bits to the Q-channel.
        # gray coding bits.
        # Check for BPSK
        if (dim == 1):
            bit_map = np.roll(np.array(['0', '1']), xcode_shift)
            # bit_map_dec = [int(value, 2) for value in bit_map]
            sym_map = np.array([-1, 1])
        else:
            # map graycoded bits to QAM constellation.
            sym_map = np.zeros((dim, dim), dtype=np.complex)
            # bit_map_dec = np.zeros((dim, dim))
            bit_map = fp_utils.init_str_array(dim, (dim, dim))
            g_code = gray_code(dim // 2)['map']
            # gray code and map.
            x_code = np.roll(g_code, xcode_shift)
            y_code = np.roll(g_code, ycode_shift)
            for ii in range(dim):
                for jj in range(dim):
                    # Q symbols are mapped from most positive y
                    quad = (dim - 1) - 2 * (jj)
                    # I symbols are mapped from most negative x
                    in_phase = -(dim - 1) + 2 * (ii)
                    sym_map[jj, ii] = np.complex(in_phase, quad)
                    # re-combine -- I gets top bits -- Q bottom bits.
                    num_bits_1 = fp_utils.ret_num_bitsU(dim - 1)
                    term1 = fp_utils.dec_to_ubin(x_code[ii], num_bits=num_bits_1)
                    term2 = fp_utils.dec_to_ubin(y_code[dim - 1 - jj], num_bits=num_bits_1)
                    bit_map[jj, ii] = term1 + term2
                    # bit_map_dec[jj, ii] = int(term1 + term2, 2)

    # compute average symbol energy
    Es_avg_comp = np.sqrt(np.sum(np.abs(sym_map)**2) / np.size(sym_map))
    # if user does not supply Es_avg -- then compute scale factor to yield
    # an average symbol energy of 1.
    scale_factor = 1. / Es_avg_comp if Es_avg is None else Es_avg / Es_avg_comp

    # scale_factor = 1
    sym_index = scale_factor * ret_sym_index(bit_map, sym_map)
    sym_map = scale_factor * sym_map

    # With square code -- one can map as a serpentine pattern starting with
    # the lower left and mapping up to upperleft -- then start one column
    # to the right and mapping down.  Continue this pattern until the
    # symbols have been mapped.
    ret_dict = {}
    ret_dict['bits_per_sym'] = k
    ret_dict['sym_map'] = sym_map
    ret_dict['sym_index'] = sym_index
    ret_dict['bit_map'] = bit_map
    ret_dict['Es_avg_comp'] = Es_avg_comp
    #(k, sym_map, sym_index, bit_map, Es_avg_comp)

    return ret_dict  


def conv_to_sym(data, sym_index):
    """
        Performs symbol mapping.

        ==========
        Parameters
        ==========

        data          : int
            Binary string of 1's and 0's.

        * sym_index   : symbol mapping order as though input is an index.

        =======
        Returns
        =======

        * syms     : IQ symbols of mapped data

    """
    data_int = data.copy()
    data_int = fp_utils.bin_array_to_uint(data_int.T)

    return sym_index[data_int]

def map_bits2syms(bits, map_dict, normalize=False):
    """
        Helper function takes a map_dect (return dictionary from gen_map function above) and a bit stream and
        returns a symbol stream.
    """
    bits_per_sym = map_dict['bits_per_sym']
    sym_index = map_dict['sym_index']
    norm_fac = map_dict['Es_avg_comp']
    data_reshape = np.reshape(bits, (bits_per_sym, -1), order='F')
    syms = conv_to_sym(data_reshape, sym_index)
    if normalize:
        syms = [sym * norm_fac for sym in syms]

    return syms

def comp_ber_curve(const_map, ebno_db=None):
    """
        Method computes BER curve for given constellation.
    """
    num = np.sum(np.abs(const_map)**2)
    den = np.size(const_map)

    num_const_pts = np.size(const_map)

    es_avg = np.sqrt(num / den)
    bits_per_sym = np.log2(np.size(const_map))

    const_map = np.atleast_2d(const_map)
    # Compute BER Curve for given constellation
    # uses Union Bound as an approximation.
    num_rows = np.shape(const_map)[0]
    num_cols = np.shape(const_map)[1]
    # determine distance to assign to Es
    ebno_db = np.arange(-1.6, 25, .4) if ebno_db is None else ebno_db  # ebno in dB.

    ebno = 10**(ebno_db / 10)  # ebno in Log.
    eb_avg = es_avg / bits_per_sym
    No = eb_avg / ebno
    noise_var = No
    snr = 10 * np.log10(es_avg / noise_var)

    q_matrix = np.zeros((np.size(const_map), np.size(snr)))

    # Compute Union bound for BER determination.
    # for kk in range(np.size(self.sym_map)):
    kk = 0
    for sub_idx, map_val in np.ndenumerate(const_map):
        i = sub_idx[0]
        j = sub_idx[1]
        # find neighbors
        row_start = i - 1 if i > 0 else 0
        row_end = i + 1 if i < (num_rows - 1) else num_rows - 1
        col_start = j - 1 if j > 0 else 0
        col_end = j + 1 if j < (num_cols - 1) else num_cols - 1
        # create indices --
        temp = np.zeros((1, np.size(snr)))
        for mm in np.arange(row_start, row_end + 1):
            for nn in np.arange(col_start, col_end + 1):
                index = (mm, nn)
                if index != (i, j):
                    # compute distance
                    dist = abs(const_map[i, j] - const_map[mm, nn])
                    # compute distance as a ratio of Eb.
                    q_value = dist / np.sqrt(2 * No)
                    q_func_out = q_func(q_value)
                    temp = temp + q_func_out

        q_matrix[kk, :] = temp
        kk += 1

    q_matrix = q_matrix / num_const_pts

    # this is probability for symbol error.
    psym_error = np.sum(q_matrix, 0)
    ber_curve = psym_error / bits_per_sym

    return (ebno_db, snr, ber_curve)

def comp_per_curve(self, const_map, pkt_length, ebno_db=None, fec_bits=0):
    """
        Helper function generates a PER curve for a given constellation.
        PER=1-(1-BER)^N where N is the number of bits. This is where there
        is no error correction.

        For error correction - able to correct up to m number of bits then.
        You want to add the binomial coefficient since you are finding
        the probability that > m bits were found in error.
        Effectively using Bernoulli Trials theory to calculate PER.

    """
    # pkt_length is in bits.
    (ebno_db, snr, ber_curve) = self.comp_ber_curve(const_map, ebno_db)
    per_curve = np.zeros(np.shape(ber_curve))

    k = pkt_length - fec_bits
    n = pkt_length

    first_term = comb(n, k, exact=1)
    # first term represents the number of combinations that k correct bits
    # can be drawn.
    for ii in range(len(per_curve)):
        # second term represents the probability that
        # n - m  (k) bits are correct for a given packet.
        # based on uniform distribution of errors and errors are independent.
        sec_term = (1 - ber_curve[ii])**k
        # third term represents the probability that 1 of m bits is in error.
        third_term = ber_curve[ii]**(n - k)
        per_curve[ii] = 1 - first_term * sec_term * third_term

    return (ebno_db, snr, per_curve)

def ret_es_avg(sym_map):
    """
        returns the average symbol energy.
    """
    return np.sqrt(np.sum(np.abs(sym_map)**2) / np.size(sym_map))

def gen_const_pts_list(bit_map, sym_map, EbNo_table=None, sig_gain=1):
    """
        Creates a list that hold constellation points related to 1's and
        another list that hold the points related to 0's
    """

    if EbNo_table is None:
        EbNo_table = np.arange(-5, 20, .2)

    Es_avg = ret_es_avg(sym_map)
    bits_per_sym = len(bit_map[0])
    EbNo_sel = 10**(EbNo_table / 10.)
    noise_var = (bits_per_sym * EbNo_sel)**-1
    # retrieve normalization factor.
    Nf = Es_avg
    # Pilot gain
    gain_lin = 10 ** (sig_gain / 10.)
    noise_const = np.sqrt(gain_lin) * (np.sqrt(Nf))**-1
    exp_noise_const = 2 * noise_var

    bit_depend = []
    const_pts_list0 = []
    const_pts_list1 = []

    # generate log-likelihood tables -- only supports square
    # constellations.
    for ii in range(bits_per_sym):
        one_list = np.zeros(sym_map.shape, dtype=np.int)
        zero_list = np.zeros(sym_map.shape, dtype=np.int)
        for (sub_idx, sym) in np.ndenumerate(bit_map):
            if (sym[ii] == '1'):
                one_list[sub_idx] = 1
            else:
                zero_list[sub_idx] = 1

        one_list = np.atleast_2d(one_list)
        zero_list = np.atleast_2d(zero_list)
        sym_map_int = np.atleast_2d(sym_map)

        temp = np.argwhere(one_list == 1.)

        row = temp[0, 0]
        col = temp[0, 1] if len(temp) > 1 else 0
        if np.all(one_list[:, col] == 1) or np.all(one_list[:, col] == 0 ):
            bit_depend.append('col')
            const_pts = sym_map_int[row, :].real
            const_pts0 = const_pts[zero_list[row, :] == 1]
            const_pts1 = const_pts[one_list[row, :] == 1]

        else:
            bit_depend.append('row')
            const_pts = sym_map_int[:, col].imag
            const_pts0 = const_pts[zero_list[:, col] == 1]
            const_pts1 = const_pts[one_list[:, col] == 1]

        const_pts_list0.append(list(const_pts0))
        const_pts_list1.append(list(const_pts1))

    return (bit_depend, const_pts_list0, const_pts_list1)

def ret_bit_sym(bit_map):
    """
        Returns the number of bits per symbol.
    """
    idx = bit_map[0].find('b')
    return len(bit_map[0][idx:])

def ret_EbNo(bit_map, sym_map, snr):
    """
        Computes EbNo value for a given SNR and symbol map.
    """
    Es_avg = ret_es_avg(sym_map)
    bits_per_sym = ret_bit_sym(bit_map)

    noise_var = Es_avg / (10.**(snr / 10.))

    Eb_avg = Es_avg / bits_per_sym
    EbNo = Eb_avg / noise_var
    EbNo_dB = 10 * np.log10(EbNo)

    return EbNo_dB

def comp_llr_values(syms_w_noise, bit_map, sym_map, EbNo_db = 3, sig_gain=1, polarity=1):
    """
        Compute Log-Likelihood values for generated symbols.

        ==========
        Parameters
        ==========

            * symWNoise (complex)
                I/Q symbol including noise

        =======
        Returns
        =======

            * LLRValues (float)
                Returns LLR values for each bit.
    """
    bits_per_sym = ret_bit_sym(bit_map)
    (bit_depend, const_pts_list0, const_pts_list1) = gen_const_pts_list(bit_map, sym_map)
    llr_list = []
    EbNo = 10 ** (EbNo_db / 10.)

    # EbNo_sel = 10**(EbNo_table / 10.)
    noise_var = (bits_per_sym * EbNo)**-1
    Es_avg = ret_es_avg(sym_map)
    # retrieve normalization factor.
    Nf = Es_avg
    # Pilot gain
    gain_lin = 10 ** (sig_gain / 10.)
    noise_const = np.sqrt(gain_lin) * (np.sqrt(Nf))**-1
    exp_noise_const = 2 * noise_var

    t1 = time.time()
    for sym in syms_w_noise:
        for (ii, depend_val) in enumerate(bit_depend):
            pos = sym.real if depend_val == 'col' else sym.imag

            P_1 = np.sum(-(const_pts_list1[ii] - pos)**2 / exp_noise_const)
            P_0 = np.sum(-(const_pts_list0[ii] - pos)**2 / exp_noise_const)

            P_0 = np.finfo(np.float).tiny if P_0 == 0 else P_0
            P_1 = np.finfo(np.float).tiny if P_1 == 0 else P_1
            llr_value = P_1 - P_0 if polarity == 1 else P_0 - P_1
            llr_list.append(llr_value)

    print("llr time = {}".format(time.time() - t1))
    return np.array(llr_list)


def comp_llr_table(qvec, bit_map, sym_map, EbNo_sel = 3):
    """
        Compute Log-Likelihood values for generated symbols.

        ==========
        Parameters
        ==========

            * symWNoise (complex)
                I/Q symbol including noise

        =======
        Returns
        =======

            * LLRValues (float)
                Returns LLR values for each bit.
    """
    bits_per_sym = ret_bit_sym(bit_map)
    (bit_depend, const_pts_list0, const_pts_list1) = gen_const_pts_list(bit_map, sym_map)
    llr_list = []

    # EbNo_sel = 10**(EbNo_table / 10.)
    noise_var = (bits_per_sym * EbNo_sel)**-1
    Es_avg = ret_es_avg(sym_map)
    # retrieve normalization factor.
    Nf = Es_avg
    # Pilot gain
    gain_lin = 10 ** (1. / 10.)
    noise_const = np.sqrt(gain_lin) * (np.sqrt(Nf))**-1
    exp_noise_const = 2 * noise_var

    pos = fp_utils.comp_range_vec(qvec, signed=1)

    pos_fi = fp_utils.Fi(pos, qvec=qvec)
    # for sym in syms_w_noise:
    
    for (ii, depend_val) in enumerate(bit_depend):
        P_1 = 0
        P_0 = 0
        for const_pt in const_pts_list1[ii]:
            # compute square distance in Log domain.
            P_1 += -((const_pt - pos)**2) / exp_noise_const
        for const_pt in const_pts_list0[ii]:
            # compute square distance
            P_0 += -((const_pt - pos)**2) / exp_noise_const

        idx = (P_0 == 0)
        P_0[idx] = np.finfo(np.float).tiny
        idx = (P_1 == 0)

        llr_list.append(P_1 - P_0)

    return (pos_fi, np.array(llr_list))

# generates simple sinc filter with roll-off factor beta.
def make_sinc_filter(beta, tap_cnt, sps, offset=0):
    """
        return the taps of a sinc filter
    """
    assert tap_cnt & 1, "tap_cnt must be odd"
    t_index = np.arange(-(tap_cnt - 1) // 2, (tap_cnt - 1) // 2 + 1) / np.double(sps)

    taps = np.sinc(beta * t_index + offset)
    taps /= np.sum(taps)

    return taps


def gain_calc_kpki(loop_eta, loop_bw_ratio):
    """
        Function compute the kp and ki values for the loop filter of the
        synchronization system.
    """

    # PLL parameters
    K_pd = 1  # abs(errGain); %error detector gain
    Kv = 1  # sqrt(EsAvg); %2*pi/4;
    Fn_Fs = loop_bw_ratio  # sampsBaud;
    theta = Fn_Fs  # *pi; %(Fn/Fs)*pi;
    eta = loop_eta
    ki_s = (4. * theta**2.) / (1 + 2. * eta * theta + theta**2.)
    kp_s = (4. * eta * theta) / (1 + 2 * eta * theta + theta**2.)
    kp = kp_s / (Kv * K_pd)
    ki = ki_s / (Kv * K_pd)

    return (kp, ki)


def pad_data_head(in_vec, num_samps, extend=False, fil_val=None):
    """
        Pads head data with zeros to align it with the ouput of another
        processing element
        ==========
        Parameters
        ==========

        in_vec : nparray
            Input vector.

        num_samps : int
            number of samples to pad the beginning of the vector

        extend : bool (False)
            Optional parameter.  If true then the tail of the vector is
            pad with the current last value.

        fil_val : same types as in_vec[0]
            Optional parameter.  User specifies a fill value to use for
            padding.


        =======
        Returns
        =======

        out : ndarray
            Output vector.

    """
    mult_val = fil_val if fil_val is not None else 0.
    mult_val = in_vec[0] if extend is True else mult_val
    if np.iscomplexobj(in_vec):
        pad = mult_val * np.ones((num_samps,), dtype=np.complex)
    else:
        pad = mult_val * np.ones((num_samps,))

    return np.concatenate((pad, in_vec))


def pad_data(in_vec, num_samps, extend=False, fil_val=None):
    """
        Pads tail data with zeros to align it with the ouput of another
        processing element.

        ==========
        Parameters
        ==========

        in_vec : ndarray
            Input vector.

        num_samps : int
            number of samples to pad the beginning of the vector

        extend : bool (False)
            Optional parameter.  If true then the tail of the vector is
            pad with the current last value.

        =======
        Returns
        =======

        out : ndarray
            Output vector.
    """
    mult_val = fil_val if fil_val is not None else 0.
    mult_val = in_vec[-1] if extend is True else mult_val
    if np.iscomplexobj(in_vec):
        pad = mult_val * np.ones((num_samps,), dtype=np.complex)
    else:
        pad = mult_val * np.ones((num_samps,))

    return np.concatenate((in_vec, pad))


def hyst_trigger(on_thresh, off_thresh, input_sig, offset=0):
    """
        Function generates a boolean output signal based on two thresholds.
        Once a signal crosses the on_thresh value the output is '1'.
        The output remains a '1' until the input signal falls below the
        off_thresh value.

    """
    # grab first index
    hi = input_sig >= on_thresh
    hi_indices = np.where(hi == True)[0] + offset
    lo_indices = np.where(input_sig < off_thresh)[0] + offset
    ret_val = [False] * len(input_sig)
    burst_indices = []
    if any(hi):
        while(1):
            # hi_indices = hi_indices[curr_idx:]
            burst_start = hi_indices[0]
            if burst_start > 0:
                burst_start -= 1
            # find first False that is greater than burst_start, then find next True (that is turn-off)
            testa = lo_indices > burst_start
            if any(testa):
                idx = np.where(testa)[0][0]
                # truncate lo_indices
                print(idx, lo_indices)
                burst_end = lo_indices[idx] - 1
                lo_indices = lo_indices[idx:]
            else:
                burst_end = len(input_sig) - 1
                lo_indices = None

            slice_len = burst_end - burst_start + 1
            ret_val[burst_start:burst_end + 1] = [True] * slice_len
            burst_indices.append((burst_start, burst_end + 1))
            if lo_indices is None:
                return ret_val, burst_indices

            # find first hi index that is > current burst_end
            try:
                offset = np.where(hi_indices > burst_end)[0][0]
                hi_indices = hi_indices[offset:]
            except:
                # returned empty array
                return ret_val, burst_indices

    else:
        # never crossed "turn_on" threshold
        return [False] * len(input_sig), burst_indices



def squelch_short_pulse(bin_sig, min_width):
    """
        Function squelchs the boolean input signal based on the minimum pulse width
        of the input signal.
    """
    last_idx = 0
    on_state = False
    count = 0
    out_sig = copy.copy(bin_sig)
    for i, value in enumerate(bin_sig):
        if on_state is False:
            if value is True:
                on_state = True
                last_idx = i
                count = 1
        else:
            if value is False:
                on_state = False
                if count < min_width:
                    out_sig[last_idx:i] = [False] * count
            else:
                count += 1

    return out_sig

def win_max(win_trig, win_vals):
    """
        Function generates a pulse that reflects the maximum (+ offset) of an
        enable pulse.  A window is determined by the rising and
        falling edge of the win_trig.  If a maximum window length is not given
        and the falling edge is not detected, the center pulse is placed at the
        center value from the rising edge until the end of the input vector.

        ==========
        Parameters
        ==========

        * win_trig : nparray (bool)
            Rising edge is the beginning of the window when a peak should be
            search for.  Falling edge indicates the end of the window.
        * offset : int -- Default = 0
            Offset from the center of the pulse.

        =======
        Returns
        =======

        out   : nparray (bool)
            Output bool vector '1' indicating a maximum value.
    """
    ret_bool = np.zeros(np.shape(win_trig), dtype=np.bool)

    start_index = 0
    trig_val_old = False
    last_index = np.size(win_trig) - 1
    for (idx, trig_val) in zip(count(), win_trig):
        r_edge = trig_val and not trig_val_old
        f_edge = not trig_val and trig_val_old
        if r_edge:
            start_index = idx
        if (f_edge or idx == last_index) and start_index is not None:
            end_index = idx
            max_index = np.argmax(win_vals[start_index:end_index])
            cen_index = start_index + max_index

            ret_bool[cen_index] = 1
            # reset start_index
            start_index = None

        trig_val_old = trig_val

    return ret_bool


def gray_code(x):
    # function gray codes a vector x
    # pdb.set_trace()
    num_bits = int(np.ceil(np.log2(np.max(x) + 1)))  # unsigned number of bits

    # create map
    prime = np.int_(np.arange(0, 2**num_bits))
    diff = np.int_(prime >> 1)

    temp_map = np.zeros((len(prime,)), dtype=int)

    for jj in range(0, len(prime)):
        temp_map[jj] = prime[jj] ^ diff[jj]  # temp_map
    # map inputs to outputs
    out = {}
    out['data'] = temp_map[x]
    out['map'] = temp_map
    out['bin_map'] = [fp_utils.dec_to_ubin(value, num_bits) for value in temp_map]

    return out

def q_func(value):
    """
        implements the Q-function or the tail probability of the normal
        distribution
    """
    return .5 * erfc(value / np.sqrt(2))

def fer_calc(ber, frame_size, num_errors=1):
    """
        Helper function that computes the frame error rate.
    """
    fer = 0
    for m in range(num_errors, frame_size):
        nchoosek = comb(frame_size, m)
        if (nchoosek == np.inf):
            nchoosek = np.finfo(np.float).max
        term1 = ber**float(m)
        term2 = (1 - ber)**(frame_size - m)
        fer += nchoosek * term1 * term2

    return fer

print_head = False
def print_header(fh):
    if print_head:
        import datetime
        now = datetime.datetime.now()
        fh.write('// This software is property of Vallance Engineering, LLC and may\n')
        fh.write('// not be used, reviewed, or distributed without prior written consent.\n')
        fh.write('//                                                      (c) {}\n'.format(now.year))

def print_header_vhd(fh):
    if print_head:
        import datetime
        now = datetime.datetime.now()
        fh.write('-- This software is property of Vallance Engineering, LLC and may\n')
        fh.write('-- not be used, reviewed, or distributed without prior written consent.\n')
        fh.write('--                                                      (c) {}\n'.format(now.year))

def attach_legend(ax):
    """
        Attaches a nice looking legend to plot.
    """
    legend = ax.legend(loc='upper right', fancybox=True, framealpha=0.75)
    frame = legend.get_frame()
    frame.set_facecolor('wheat')


def upsample(s, n, phase=0):
    """Increase sampling rate by integer factor n  with included offset phase.
    """
    return np.roll(np.kron(s, np.r_[1, np.zeros(n - 1)]), phase)

def ret_valid_path(path):
    if path[-1] != '/':
        path += '/'

    if path[-2:] == '//':
        path = path[:-1]

    if not os.path.isdir(path):
        os.makedirs(path)
    return path

def ret_name_idx(file_name):

    idx = str(file_name[::-1]).find('/')
    if (idx == -1):
        idx = 0
    else:
        idx = len(file_name) - idx
    idx2 = str(file_name[idx:]).find('.')
    if (idx2 == -1):
        idx2 = len(file_name)

    return idx, idx2


def ret_module_name(file_name):

    idx, idx2 = ret_name_idx(file_name)

    return file_name[idx:idx + idx2]


def ret_file_name(file_name):
    # find last forward slash
    idx = str(file_name[::-1]).find('/')
    if (idx == -1):
        idx = 0
    else:
        idx = len(file_name) - idx

    file_name = file_name[idx:]

    return file_name


def convert_to_script(in_file_name, out_file_name):
    """
        Helper function takes an input file and converts it to a file
        formatted to be converted to a python function.  Allows quick
        and parametric generation of the original file.
    """
    fh = open(in_file_name, 'r')
    lines = fh.readlines()
    # print(lines)
    fh.close()
    with open(out_file_name, "w") as fh:
        fh.write('#!/usr/bin/env python\n')
        fh.write('# -*- coding: utf-8 -*-\n')
        fh.write('\n\n')
        fh.write('def generic_function(file_name):\n')
        fh.write('    assert(file_name is not None), \'User must specify File Name\'\n')

        # find last forward slash
        fh.write('    module_name = ret_module_name(file_name)\n')
        fh.write('    with open(\"{}\", \'w\') as fh:\n'.format(out_file_name))
        fh.write('\n')
        for line in lines:
            # check line for '
            line = line.rstrip('\n')
            line = line.replace("'", "\\'")
            line = line.replace("{", "{{")
            line = line.replace("}", "}}")
            new_line = '        fh.write(\'' + line + '\\n\')\n'
            fh.write(new_line)

def complex_rot(in_vec, rot_factor=0., phase=0):
    """
        Implements the function of a DDS

        ==========
        Parameters
        ==========

            * in_vec     : nparray (real or complex)
                Input vector
            * rot_factor : nparray (0.)
                Normalized discrete frequency offset +/- 1.  If it is not a
                singular value then it must be the same shape as in_vec.
            * mod_type   : str (None)
                Used if performing 'cosine' or 'sine' frequency translation.

        =======
        Returns
        =======

            out : nparray
                Frequency translated complex output array.
    """

    # functions performs frequency translation through the use of a
    # complex rotation

    # input : sampled data stream to be complex rotated.
    # rot_factor : rotation factor -- 1 = pi
    # print(type(in_vec))
    # sys.exit()
    num_inputs = len(in_vec)
    try:
        # test is rot_factor is a list or an array
        num_samps = len(rot_factor)
        # rot_factor array must be same len as in_vec
        if num_samps < num_inputs:
            rot_factor = pad_data(rot_factor, num_inputs, fil_val=0.)
        rot_factor = np.cumsum(rot_factor)
        return in_vec * np.exp(1j * (np.pi * rot_factor[:num_inputs] + phase))
    except:
        ii = np.arange(np.size(np.array(in_vec)))
        return in_vec * np.exp(1j * (np.pi * rot_factor * ii + phase))

    # if modulation type is not given then simply assume a complex rotator

def gen_comp_tone(num_samps, dfreq, phase=0):
    dc_term = [1.] * num_samps
    return complex_rot(dc_term, dfreq, phase)

# method generates coefficients for Gaussian Filter
# bt is the the Bandwidth*Symbol constant
# pulled from Appendix B: All-Digital Frequency Synthesizer in
# Deep-Submicron CMOS
def make_gauss_filter(bt, tap_count, sps):
    """
        return the taps of a Gaussian Filter
    """
    osr = sps / 2  # oversampling ratio
    b_const = bt / osr
    term1 = np.sqrt(2.) * np.pi / np.sqrt(np.log(2))
    t_index = np.arange(-tap_count // 2, tap_count // 2 + 1) / np.double(osr)
    taps = np.exp(-(term1 * bt * t_index)**2)
    taps /= sum(taps)

    return (taps, b_const)


def make_rc_filter(beta, tap_count, sps):
    """
        return the taps of a raised cosine filter
    """
    assert tap_count & 1, "tap_count must be odd"
    t_index = np.arange(-(tap_count - 1) // 2, (tap_count - 1) // 2 + 1) / np.double(sps)
    num = np.cos(np.pi * beta * t_index)
    den = 1 - 4 * beta**2 * t_index**2
    zero_idx = (den == 0)
    den[zero_idx] = 1.
    taps = np.sinc(t_index) * num / den

    return taps

def make_rrc_filter(beta, tap_cnt, sps):
    """
        return the taps of an Root Raised Cosine filter
    """
    assert tap_cnt & 1, "tap_cnt must be odd"
    t_index = np.arange(-(tap_cnt - 1) // 2, (tap_cnt - 1) // 2 + 1) / np.double(sps)
    num = (4. * beta * t_index * np.cos((1. + beta) * np.pi * t_index) + np.sin((1. - beta) * np.pi * t_index))

    den = 4. * beta * t_index * (1. - (4. * beta * t_index)**2)

    # check for infinities -- will be replaced below.
    zero_idx = (den == 0)
    idx = (tap_cnt - 1) // 2
    den[zero_idx] = 1
    zero_idx[idx] = False

    taps = num / den
    taps[idx] = 1 if beta == 0 else (4. * beta + (1. - beta) * np.pi) / (4. * beta)

    # linear interpolate zero indices
    x_term = np.pi / (4 * beta)
    temp = x_term * (beta / np.sqrt(2)) * ((1 + 2. / np.pi) * np.sin(x_term) + (1 - 2. / np.pi) * np.cos(x_term))
    taps[zero_idx] = temp

    return taps


def est_no(snr, in_vec):
    """
        Utility that estimates No for both I and Q channels based on required SNR and the input vector.
    """
    snr = 10.**(snr / 10.)  # converted into linear units

    sig_pwr_i = np.mean(np.abs(in_vec.real)**2)
    sig_pwr_q = np.mean(np.abs(in_vec.imag)**2)

    # Determine the energy per bit normalized to Nyquist rate
    no_i = sig_pwr_i / snr
    # this is the noise power or the variance of the noise
    no_q = sig_pwr_q / snr

    return no_i, no_q

def gen_noise(vec_len, no_i, no_q, seed_i=20, seed_q=30, isreal=False):
    """
        Generates noise of length "vec_len" based on No parameters
    """
    if isreal:
        # include scaling for full power.
        # factor of 2 is since BW is measured between -1 and 1.
        # so for full bandwidth -- the digital BW = 2.
        # make noise draws predictable.
        np.random.seed(seed_i)
        complex_noise = np.sqrt(no_i) * np.random.standard_normal(vec_len)
    else:
        # create complex Gaussian noise with variance = No/2
        # make noise draws consistent with seeds.
        np.random.seed(seed_i)
        noise_i = np.sqrt(no_i) * np.random.standard_normal(vec_len)
        np.random.seed(seed_q)
        noise_q = np.sqrt(no_q) * np.random.standard_normal(vec_len)

        # Scale for full noise power
        complex_noise = noise_i + 1j * noise_q

    return complex_noise

def add_noise_pwr(snr, in_vec, seed_i=None, seed_q=None):
    """
        Add Noise to signal
        # Specify snr and add AWGN
        # snr -- Ratio of signal Power / noise power

        =======
        Returns
        =======

        (sig_wnoise, complex_noise)
    """
    if seed_i is None:
        seed_i = 10
    if seed_q is None:
        seed_q = 20

    no_i, no_q = est_no(snr, in_vec)
    vec_shape = np.shape(in_vec)
    # If there is no imag component then dealing with real Single sided
    # variance of Gaussian noise = No/2.
    complex_noise = gen_noise(len(in_vec), no_i, no_q, seed_i, seed_q)
    # Add noise into complex signal
    sig_wnoise = in_vec + complex_noise

    return (sig_wnoise, complex_noise)


def gen_rand_data(seed=42, num_bits=1000, dtype=np.int):
    """
        Generates a random stream of 1's and 0's

        ==========
        Parameters
        ==========

        seed : int
            Seed for random number generator

        num_bits : int
            Number of random bits to generate

        =======
        Returns
        =======

        out : ndarray
            Returns an array of 1's and 0's
    """
    np.random.seed(seed)
    ret_val = np.round(np.random.rand(num_bits,))
    if dtype == np.int:
        return ret_val.astype(np.int)
    else:
        return ret_val


def crc_comp(data_frame, spec=None, polynomial=None, init_value=0, num_bits=None,
             out_rev=False, byte_swap=False, out_inv=False, lsb_first=False, rev_bytes=False):
    """
        Function performs traditional CRC check.

        ==========
        Parameters
        ==========

            * data_frame : array_type
                vector of bits representing the data + appended CRC code.
            * polynomial : string
                hex string of the CRC polynomial.

        =======
        Returns
        =======

            * ret_tuple : tuple
                (pass/fail,crc_val) : pass/fail bit (0 pass, -1 for fail)
                the computed CRC value.

    """
    if spec == 'crc16':
        byte_swap = False
        out_rev = True
        out_inv = False
        rev_bytes = True
        init_value = 0
        polynomial = '8005'
        num_bits = 16
    elif spec == 'crc32':
        byte_swap = False
        rev_bytes = True
        out_rev = True
        out_inv = True
        init_value = 1
        polynomial = '4c11db7'
        num_bits = 32
    elif spec == 'crc_ccitt_xmodem':
        init_value = 0
        byte_swap = False
        out_rev = False
        out_inv = False
        polynomial = '1021'  # CRC-CCITT
        num_bits = 16

    if rev_bytes:
        num_bytes = len(data_frame) // 8
        new_vec = []
        for ii in range(num_bytes):
            lidx = ii * 8
            ridx = lidx + 8
            temp = data_frame[lidx:ridx]
            new_vec.extend(temp[::-1])

        data_frame = new_vec

    if type(polynomial) is not list:
        g_x = fp_utils.hex_to_list_vec(polynomial)
    else:
        g_x = polynomial

    if lsb_first:
        g_x = g_x[::-1]
    if num_bits is not None:
        num_zeros = num_bits - len(g_x)
        g_x = np.array([1] + [0] * num_zeros + g_x)

    g_x = g_x[:-1]
    len_gx = len(g_x)
    crc_len = len_gx  # - 1
    init_state = [init_value] * crc_len
    mask_val = init_state
    # now loop and compute xOR
    for bit in data_frame:
        out_bit = bit ^ mask_val[0]
        if out_bit == 1:
            xor_val = fp_utils.xor_list(mask_val, g_x)
        else:
            xor_val = list(mask_val)
        mask_val = xor_val[1:] + [out_bit]

    # do not invert
    crc_val = mask_val
    if out_rev:
        crc_val = crc_val[::-1]

    ret_val = copy.copy(crc_val)

    if byte_swap:
        num_words = int(np.ceil(len(crc_val) / 16.))
        for ii in range(num_words):
            lidx = ii * 8
            ridx = lidx + 8
            lidx2 = ridx
            ridx2 = lidx2 + 8
            ret_val[lidx2:ridx2] = crc_val[lidx:ridx]
            ret_val[lidx:ridx] = crc_val[lidx2:ridx2]
        ret_val
    else:
        ret_val

    if out_inv:
        ret_val = [1 if val == 0 else 0 for val in ret_val]

    return ret_val

def ret_a_val(vec, format_str):

    vec = np.array(vec)
    a_val = vec.astype(int)
    if format_str == 'f':
        a_val = vec.astype(np.float32)
    if format_str == 'h':
        a_val = vec.astype(np.int16)
    if format_str == 'H':
        a_val = vec.astype(np.uint16)
    if format_str == 'd':
        a_val = vec.astype(np.float64)
    if format_str == 'Q':
        a_val = vec.astype(np.uint64)
    if format_str == 'q':
        a_val = vec.astype(np.int64)
    if format_str == 'c':
        a_val = vec.astype()

    return a_val

def write_pkts(vec, file_name, format_str='h', append=False, big_endian=True):
    """Write a numpy array of complex samples to a binary file.  The samples
    are treated as 16 bit signed integers -- little endian.

    Arguments
    =========
    vec - the numpy array to be written
    file_name - the name of the file to be written to
              structure val[0]val[1]val[2]val[3]...

        .. _making-a-table:
        ====== ============== =================== ============= ============
        Format	C Type         Python type         Standard size Notes
        ====== ============== =================== ============= ============
        x      pad byte	       no value
        c      char            string of length 1   1           \
        b      signed char     integer	            1           (3)
        B	   unsigned char   integer              1           (3)
        ?	   _Bool           bool                 1           (1)
        h      short           integer              2           (3)
        H      unsigned short  integer              2           (3)
        i      int             integer              4           (3)
        I      unsigned int    integer              4           (3)
        l 	   long	           integer	            4	        (3)
        L	   unsigned long   integer	            4	        (3)
        q	   long long	   integer	            8	        (2), (3)
        Q      u long long	   integer	            8	        (2), (3)
        f	   float	       float                4           (4)
        d      double          float                8	        (4)
        s      char[]          string               \           \
        p      char[]          string               \           \
        P      void *          integer              \           (5), (3)
        ====== ============== =================== ============= ============


    Returns
    =======
    None
    """
    a_val = ret_a_val(vec, format_str)
    # format_str = '<%d' + format_str
    write_opt = "wb"
    if append:
        write_opt = "ab"

    f_str = '<'
    new_a_val = []
    try:
        if big_endian:
            f_str = '>'
        # insert meta date in front of each word in a_val
        for ii, value in enumerate(a_val):
            meta_data = 0
            if ii == 0:
                meta_data = 1
            if ii == len(a_val) - 1:
                meta_data = 2
            new_a_val.append(meta_data)
            new_a_val.append(value)

            f_str += 'B'
            f_str += format_str

        with open(file_name, write_opt) as f:
            # need to prepend meta data byte to each word.
            # str_val = struct.pack('<' + format_str, value)
            ret_val = struct.pack(f_str, *new_a_val)
            f.write(ret_val)
        return 0
    except:
        ret_val = struct.pack(f_str, *new_a_val)
        print("did not write packet to {}, {}".format(file_name, ret_val))
        return -1


def write_binary_file(vec, file_name, format_str='h', append=False, big_endian=True):
    """Write a numpy array of complex samples to a binary file.  The samples
    are treated as 16 bit signed integers -- little endian.

    Arguments
    =========
    vec - the numpy array to be written
    file_name - the name of the file to be written to
              structure val[0]val[1]val[2]val[3]...

        .. _making-a-table:
        ====== ============== =================== ============= ============
        Format	C Type         Python type         Standard size Notes
        ====== ============== =================== ============= ============
        x      pad byte	       no value
        c      char            string of length 1   1          \
        b      signed char     integer	            1          (3)
        B	   unsigned char   integer              1          (3)
        ?	   _Bool           bool                 1          (1)
        h      short           integer              2          (3)
        H      unsigned short  integer              2          (3)
        i      int             integer              4          (3)
        I      unsigned int    integer              4          (3)
        l 	   long	           integer	            4	       (3)
        L	   unsigned long   integer	            4	       (3)
        q	   long long	   integer	            8	       (2), (3)
        Q      u long long	   integer	            8	       (2), (3)
        f	   float	       float                4          (4)
        d      double          float                8	       (4)
        s      char[]          string               \          \
        p      char[]          string               \          \
        P      void *          integer              \          (5), (3)
        ====== ============== =================== ============= ============


    Returns
    =======
    None
    """
    a_val = ret_a_val(vec, format_str)

    format_new = '<%d' + format_str
    if big_endian:
        format_new = '>%d' + format_str

    write_opt = "wb"
    if append:
        write_opt = "ab"

    try:
        with open(file_name, write_opt) as f:
            ret_val = f.write(struct.pack(format_new % len(a_val), *a_val))
            print('file {} successfully written'.format(file_name))
        return 0
    except:
        print('file {} not successfully written'.format(file_name))
        return -1



def write_complex_samples(vec, file_name, q_first=True, format_str='h', big_endian=True, append=False):
    """
        Write a numpy array of complex samples to a binary file.

        Arguments
        =========
        vec - the complex integer numpy array to be written
        file_name - the name of the file to be written to
        q_first - when True  file has structure Q[0]I[0]Q[1]I[1]Q[2]I[2]Q[3]I[3]...
                  when False file has structure I[0]Q[0]I[1]Q[1]I[2]Q[2]I[3]Q[3]...


        .. _making-a-table:
        ====== ============== =================== ============= ============
        Format	C Type         Python type         Standard size Notes
        ====== ============== =================== ============= ============
        x      pad byte	       no value
        c      char            string of length     1            1
        b      signed char     integer	            1           (3)
        B	   unsigned char   integer              1           (3)
        ?	   _Bool           bool                 1           (1)
        h      short           integer              2           (3)
        H      unsigned short  integer              2           (3)
        i      int             integer              4           (3)
        I      unsigned int    integer              4           (3)
        l 	   long	           integer	            4	        (3)
        L	   unsigned long   integer	            4	        (3)
        q	   long long	   integer	            8	        (2), (3)
        Q      u long long	   integer	            8	        (2), (3)
        f	   float	       float                4           (4)
        d      double          float                8	        (4)
        s      char[]          string               \           \
        p      char[]          string               \           \
        P      void *          integer              \           (5), (3)
        ====== ============== =================== ============= ============

        Returns
        =======
        0 - File written successfully.
        -1 - Failure to write file
    """
    if q_first:
        vec = np.array([np.imag(vec), np.real(vec)]).ravel('F')
    else:
        vec = np.array([np.real(vec), np.imag(vec)]).ravel('F')

    a_val = ret_a_val(vec, format_str)

    write_opt = "wb"
    if append:
        write_opt = "ab"

    format_new = '<%d' + format_str
    if big_endian:
        format_new = '>%d' + format_str

    try:
        with open(file_name, write_opt) as f:
            f.write(struct.pack(format_new % len(a_val), *a_val))
            print('file {} successfully written'.format(file_name))
        return 0
    except:
        print('file {} not successfully written'.format(file_name))
        return -1


def ret_divisor(format_str):
    divisor = 2
    dtype = 'u2'
    if format_str == 'H':
        divisor = 2
        dtype = 'u2'
    elif format_str == 'h':
        divisor = 2
        dtype = 'i2'
    elif format_str == 'i':
        divisor = 4
        dtype = 'i4'
    elif format_str == 'I':
        divisor = 4
        dtype = 'u4'
    elif format_str == 'b':
        divisor = 1
        dtype = 'i1'
    elif format_str == 'B':
        divisor = 1
        dtype = 'u1'
    elif format_str == 'f':
        divisor = 4
        dtype = 'f4'
    elif format_str == 'd':
        divisor = 8
        dtype = 'f8'
    elif format_str == 'q':
        divisor = 8
        dtype = 'i8'
    elif format_str == 'Q':
        divisor = 8
        dtype = 'u8'
    elif format_str == 'c':
        divisor = 1
        dtype = 'c'
    elif format_str == 'l':
        divisor = 4
        dtype = 'i4'
    elif format_str == 'L':
        divisor = 4
        dtype = 'u4'

    return (divisor, dtype)


def read_complex_samples(file_name, q_first=False, format_str='h', offset=0, num_samps=None, big_endian=True):
    """
    Read a binary file into a numpy array  -- format string specifies the
    word size.

    Format String :

        .. _making-a-table:
        ====== ============== =================== ============= ============
        Format	C Type         Python type         Standard size Notes
        ====== ============== =================== ============= ============
        x      pad byte	       no value
        c      char            string of length      1            \
        b      signed char     integer	             1           (3)
        B	   unsigned char   integer               1           (3)
        ?	   _Bool           bool                  1           (1)
        h      short           integer               2           (3)
        H      unsigned short  integer               2           (3)
        i      int             integer               4           (3)
        I      unsigned int    integer               4           (3)
        l 	   long	           integer	             4	         (3)
        L	   unsigned long   integer	             4	         (3)
        q	   long long	   integer	             8	         (2), (3)
        Q      u long long	   integer	             8	         (2), (3)
        f	   float	       float                 4           (4)
        d      double          float                 8	         (4)
        s      char[]          string                \           \
        p      char[]          string                \           \
        P      void *          integer               \           (5), (3)
        ====== ============== =================== ============= ============

    =========
    Arguments
    =========

        * file_name - the name of the file to be written to
        * q_first - when True  file has structure Q[0]I[0]Q[1]I[1]Q[2]I[2]...
              when False file has structure I[0]Q[0]I[1]Q[1]I[2]Q[2]I[3]Q[3]...

        * offset int (0)
            Number of words offset into file.

        * num_samps int (None)
            Number of words to read from file.


    =======
    Returns
    =======
    the numpy array read from the file
    """

    (divisor, dtype) = ret_divisor(format_str)
    iq_word_len = divisor * 2

    format_new = '<' + dtype
    if big_endian:
        format_new = '>' + dtype
    if num_samps is None:
        num_samps = -1
    else:
        num_samps = int(num_samps * 2)

    try:
        with open(file_name, 'rb') as f:
            # f.seek(offset * iq_word_len, 0)
            d_vec = np.fromfile(f, dtype=format_new, count=num_samps, offset=offset*iq_word_len)
            # ensure that even number of samples.
            trunc = len(d_vec) % 2
            if trunc:
                d_vec = d_vec[:-1]

        if q_first:
            return d_vec[1::2] + 1.j * d_vec[::2]
        else:
            return d_vec[::2] + 1.j * d_vec[1::2]

    except:
        print("ERROR : Invalid File name")
        return -1


def find_nearest(array, value):
    """
        Helper function finds closes value in a numpy array.
    """
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return array[idx]

def read_str_file(file_name):
    """
        Reads in a file with floating point value strings, 1 per line.
    """
    x = []
    try:
        with open(file_name, 'r') as f:
            lines = f.read().splitlines()
            for y in lines:
                try:
                    x.append(float(y))
                except ValueError:
                    continue
        return x
    except:
        print('file {} not successfully read'.format(file_name))
        return -1


def read_binary_file(file_name, format_str='h', offset=0, num_samps=None, big_endian=True):
    """
        Read a binary file into a numpy array.

        Arguments
        =========
        file_name - the name of the file to be written to
        bitWidth - specifies the datawidth of the underlying data.

        .. _making-a-table:
        ====== ============== =================== ============= ============
        Format	C Type         Python type         Standard size Notes
        ====== ============== =================== ============= ============
        x      pad byte	     no value
        c      char            string of length 1   1           \
        b      signed char     integer	          1           (3)
        B	    unsigned char   integer              1          (3)
        ?	    _Bool           bool                 1          (1)
        h      short           integer              2           (3)
        H      unsigned short  integer              2           (3)
        i      int             integer              4           (3)
        I      unsigned int    integer              4           (3)
        l 	    long	         integer	              4	     (3)
        L	    unsigned long integer	              4	     (3)
        q	    long long	    integer	         8	     (2), (3)
        Q       u long long	    integer	         8	          (2), (3)
        f	      float	    float                4           (4)
        d      double          float                8	           (4)
        s      char[]          string               \           \
        p      char[]          string               \           \
        P      void *          integer              \           (5), (3)
        ====== ============== =================== ============= ============

        Returns
        =======
        the numpy array read from the file
    """

    (divisor, dtype) = ret_divisor(format_str)
    if big_endian:
        dtype = '>{}'.format(dtype)
    else:
        dtype = '<{}'.format(dtype)

    try:
        with open(file_name, 'r') as f:
            f.seek(offset * divisor)
            if (num_samps is None):
                num_samps = -1

            d_vec = np.fromfile(f, dtype=dtype, count=num_samps)
        return d_vec
    except:
        print('file {} not successfully read'.format(file_name))
        return -1


def gen_split_tables(addr_vec, table_fi, slice_bits=None):
    """
        Function generates a split table with linear interpolation lower table and lower table when input
        value is small. The tables are populated so that input value are
        directly mapped to addresses.

        ==========
        Parameters
        ==========

            * table_fi  : fixed integer objects
            * slice_bits : int (8)
                number of address bits to slice from top of input vector. Determines size of all three LUTs.

        =======
        Returns
        =======

            (u_table,diff_table,s_table) : sfi objects

    """
    qvec = table_fi.qvec
    table_width = table_fi.qvec[0]
    input_width = int(np.log2(table_fi.len))
    if slice_bits is None:
        slice_bits = np.ceil(input_width / 2).astype(np.int)

    l_bits = qvec[0] - slice_bits
    l_qvec = (l_bits, qvec[1])
    # generate upper indices.
    upper_bits = input_width - slice_bits
    addrs = addr_vec.udec

    addr_old = None
    upper_values = []
    upper_addrs = []
    for addr, value in zip(addrs, table_fi.float):
        temp = addr >> slice_bits
        if temp != addr_old:
            upper_values.append(value)
            addr_old = temp
            upper_addrs.append(temp)

    # upper_indices = np.arange(0, 2**upper_bits) << slice_bits
    # upper_values = table_fi.float[upper_indices]
    diff_values = np.diff(upper_values)
    # np.concatenate((log_vals_diff,log_vals_diff[-1]))
    diff_values = np.append(diff_values, diff_values[-1])
    # order values in terms of their addresses.

    sort_addrs = np.argsort(upper_addrs)
    upper_values = [upper_values[address] for address in sort_addrs]
    diff_values = [diff_values[address] for address in sort_addrs]

    u_table_fi = fp_utils.Fi(upper_values, qvec, signed=1, overflow='saturate')
    diff_table_fi = fp_utils.Fi(diff_values, qvec, signed=1, overflow='saturate')

    upper_table_fi = fp_utils.concat_fi(u_table_fi, diff_table_fi)

    # now create lower table.
    lower_values = []
    lower_addrs = []
    mask = ((2 ** upper_bits) - 1) << slice_bits
    lmask = (2 ** slice_bits - 1)
    for addr, value in zip(addrs, table_fi.float):
        temp = addr & mask
        if temp == 0:
            lower_values.append(value)
            lower_addrs.append(addr & lmask)

    lsort_addrs = np.argsort(lower_addrs)
    # order values in terms of addresses
    lower_values = [lower_values[address] for address in lsort_addrs]
    zero_values = [0] * len(lsort_addrs)

    s_table_fi = fp_utils.Fi(lower_values, qvec, overflow='saturate', signed=1)
    e_table_fi = fp_utils.Fi(zero_values, qvec, overflow='saturate', signed=1)

    lower_table_fi = fp_utils.concat_fi(s_table_fi, e_table_fi)
    # now format small table identically to the large table.
    # now concatenate tables to form combined table.
    combined_table = fp_utils.stack_fi(lower_table_fi, upper_table_fi)

    return combined_table


def gen_fib_LFSR(polynomial, length, poly_flip=False, init_state=None):
    """
        Generates Fibonacci LFSR Sequence of length, length.
        If the initial state is not given, then it is assumed to be the all
        1's case.

        ==========
        Parameters
        ==========

            * polynomial : hex or list
                Specifies the polynomial in x^n-1 + x^n-2 .... + 1 form.
            * length  : integer
                Number of bits to generate.
            * poly_flip : bool
                Reverses the polynomial.
            * init_state : integer or list
                In same for as polynomial -- specifies the initial state
                of the internal register of the Fibonacci LFSR.

        =======
        Returns
        =======

            * pn_seq : list (int)
                List of 1's and 0's that represent the LFSR sequence.
            * state : list (int)
                List of integer values representing the internal state of the
                LFSR engine.
    """

    if (type(polynomial) == list):
        if (poly_flip is True):
            polynomial = polynomial[::-1]
    else:
        # hex value.
        polynomial = fp_utils.hex_to_list_vec(polynomial)
        if (poly_flip is True):
            polynomial = polynomial[::-1]

    b_vec = fp_utils.list_to_uint(polynomial)
    b_vec = b_vec >> 1
    num_regs = len(polynomial) - 1

    state = 2**(num_regs) - 1
    if init_state is not None:
        if type(init_state) == list:
            state = fp_utils.list_to_uint(init_state)
        else:
            state = init_state

    upper_mask = 2**(num_regs - 1)
    lower_mask = upper_mask - 1

    pn_seq = []
    state_seq = []
    for ii in range(length):
        state_seq.append(state)
        new_output = fp_utils.xor_vec(b_vec, state)
        state = ((lower_mask & state) << 1) + new_output
        pn_seq.append(new_output)

    return (pn_seq, state_seq)

def galois_LFSR_gen(polynomial, length, poly_flip=False, init_state=None):
    """
        Generates Galois LFSR Sequence of length, length.
        If the initial state is not given, then it is assumed to be the all
        1's case.

        ==========
        Parameters
        ==========

            * polynomial : integer or list
                Specifies the polynomial in x^n-1 + x^n-2 .... + 1 form.
            * length  : integer
                Number of bits to generate.

            * init_state : integer or list
                In same for as polynomial -- specifies the initial state
                of the internal register of the Galois LFSR.

        =======
        Returns
        =======

            * pn_seq : list (int)
                List of 1's and 0's that represent the LFSR sequence.
            * state : list (int)
                List of integer values representing the internal state of the
                LFSR engine.
    """

    if (type(polynomial) == list):
        if (poly_flip is True):
            polynomial = polynomial[::-1]
    else:
        # hex value.
        polynomial = fp_utils.hex_to_list_vec(polynomial)
        if (poly_flip is True):
            polynomial = polynomial[::-1]

    b_vec = fp_utils.list_to_uint(polynomial)

    b_vec = b_vec >> 1
    num_regs = len(polynomial) - 1
    # mask off top bit
    b_vec = b_vec & (2**(num_regs - 2) - 1)

    state = 2**(num_regs) - 1
    if init_state is not None:
        if type(init_state) == list:
            state = fp_utils.list_to_uint(init_state)
        else:
            state = init_state

    pn_seq = []
    state_seq = []
    for ii in range(length):
        state_seq.append(state)
        new_output = state & 1
        # perform shift.
        stateNew = 0
        if new_output == 1:
            for ii in range(num_regs - 1):
                # need to start at top of state register and work down.
                # this is due to consecutive 1's for the XOR operations.
                # top register bit is never XOR so can skip.
                index = (ii + 1) % num_regs
                val = (b_vec >> ii) & 1
                stateVal = (state >> index) & 1
                if val == 1:
                    stateNew += (stateVal ^ new_output) << ii
                else:
                    stateNew += stateVal << ii
            state = stateNew + (new_output << (num_regs - 1))
        else:
            state = (state >> 1)

        pn_seq.append(new_output)

    return (pn_seq, state_seq)

def make_log_tables(qvec=(16, 13), table_bits=20):
    """
        Function generates natural log look-up tables.  Takes upper bits and
        generates large value Look-up Table (LUT).  The lower bits for used
        for linear interpolation of large table and for LUT when input
        value is small. The tables are populated so that input value are
        directly mapped to addresses.

        ==========
        Parameters
        ==========

            * qvec  : tuple (16,13)
                Input quantization vector.
            * table_bits : int (20)
                natural log LUT number of bits.  Width of the actual table

        =======
        Returns
        =======

            (u_table,diff_table,s_table) : sfi objects

    """

    # slice bits always taken as half of qvec -- able to have 1 combined table for upper, diff, and small tables.
    slice_bits = np.ceil(qvec[0] / 2).astype(np.int)

    eps_val = np.finfo(np.double).eps
    diff_val = qvec[0] - slice_bits
    upper_val_qvec = (slice_bits, qvec[1] - diff_val)

    l_bits = qvec[0] - slice_bits

    # u_fi_obj = fp_utils.ufi(0, upper_val_qvec[0], upper_val_qvec[1])
    vals = fp_utils.comp_range_vec(upper_val_qvec, signed=0)
    slope = fp_utils.comp_slope_value(upper_val_qvec)
    vals_obj = fp_utils.ufi(vals, qvec=upper_val_qvec)

    addr_vec = vals_obj.udec

    log_vals = np.log(vals + eps_val)
    idx0 = (vals == 0.)
    idx1 = (vals == slope)

    log_vals[idx0] = log_vals[idx1]
    # added smallest float value to remove warnings for log(0)

    # compute diff values
    log_vals_diff = np.diff(log_vals)
    # pad out log_vals_diff
    log_vals_diff = np.append(log_vals_diff, log_vals_diff[-1])

    log_valsR = log_vals[addr_vec]
    log_vals_diffR = log_vals_diff[addr_vec]

    frac_bits = fp_utils.comp_frac_width(log_valsR, table_bits, signed=1)
    # reduce fraction length by 1 -- this give head room to negative
    u_table_qvec = (table_bits, frac_bits - 1)
    # this is just the large log table -- can be used for qvec values for all table elements.
    u_table = fp_utils.Fi(log_valsR, u_table_qvec, overflow='saturate', signed=1)

    # log values that will show up in the small table.
    diff_table = fp_utils.Fi(log_vals_diffR, u_table_qvec, overflow='saturate', signed=1)

    # now combine upper and differential tables into large table.
    diff_vals = diff_table.vec
    u_vals = u_table.udec

    # new values is large table concatenated with difference or delta values
    new_vals = (u_vals << table_bits) + diff_vals

    l_qvec = (l_bits, qvec[1])
    l_vals = fp_utils.comp_range_vec(l_qvec, signed=0)
    # quantizing large table / diff values table.
    lvals_fi = fp_utils.ufi(l_vals, l_qvec, overflow='wrap')
    laddr_vec = lvals_fi.udec

    # generate small log values table.
    small_log_vals = np.log(l_vals + eps_val)
    small_log_vals[0] = small_log_vals[1]
    small_log_valsR = small_log_vals[laddr_vec]

    s_table = fp_utils.sfi(small_log_valsR, u_table_qvec, overflow='saturate')

    # now format small table identically to the large table.
    svals = (s_table.udec << table_bits)

    # now concatenate tables to form combined table.
    comb_vals = np.concatenate((svals, new_vals))
    combined_table = fp_utils.ufi(comb_vals, (2 * table_bits, 0))

    return combined_table, u_table_qvec


def make_exp_tables(qvec_in=(16, 13), table_bits=16, max_shift=None):
    """
        Function generates exp look-up tables.  Takes upper bits and
        generates large value Look-up Table (LUT).  The lower bits for used for
        LUT for linear interpolation of large table and for LUT when input
        value is small.
        The tables are populated so that input value are directly mapped to
        addresses.

        ==========
        Parameters
        ==========

            * qvec_in  : tuple (16,13)
                Input quantization vector.
            * table_bits : int (20)
                natural log LUT number of bits.

        =======
        Returns
        =======

            (exp_combined_fi, exp_qvec) : sfi objects

    """
    # slice bits always taken as half of qvec -- able to have 1 combined table for upper, diff, and small tables.
    slice_bits = np.ceil(qvec_in[0] / 2).astype(np.int)

    upper_val_qvec = (qvec_in[0] - slice_bits, qvec_in[1] - slice_bits)
    l_bits = qvec_in[0] - slice_bits

    u_fi_obj = fp_utils.sfi(0, qvec=upper_val_qvec)
    vals = u_fi_obj.comp_range_vec()

    vals_obj = fp_utils.sfi(vals, qvec=u_fi_obj.qvec)

    addr_vec = vals_obj.udec
    exp_vals = np.exp(vals)

    # compute ratio of exp_vals
    exp_vals_ratio = exp_vals[1::] / exp_vals[0:-1]
    exp_vals_ratio = pad_data(exp_vals_ratio, 1, extend=True)
    # take mean here -- should be close to a constant ratio not necessary
    # to make table out of it.
    ratio_value = np.mean(exp_vals_ratio)
    shift_table = (np.ceil(np.log2(exp_vals))).astype(np.int)

    # force minimum shift to be 0
    idx = (shift_table < 0)
    shift_table[idx] = 0

    if max_shift is not None:
        idx = (shift_table > max_shift)
        shift_table[idx] = max_shift

    exp_vals = exp_vals * 2.**(-shift_table)
    idx = (exp_vals > 1.)
    exp_vals[idx] = 1.0

    exp_valsR = exp_vals[addr_vec]
    shift_tableR = shift_table[addr_vec]

    frac_bits = fp_utils.comp_frac_width(exp_valsR, table_bits, signed=0)
    # reduce fraction length by 1 -- this give head room to negative
    u_table_qvec = (table_bits, frac_bits)

    u_table = fp_utils.ufi(exp_valsR, u_table_qvec)
    shift_len = int(np.ceil(np.log2(np.max(shift_tableR))))
    shift_qvec = (shift_len, 0)
    ls_table = fp_utils.ufi(shift_tableR, qvec=(shift_len, 0))

    l_qvec = (l_bits, qvec_in[1])
    l_vals_obj = fp_utils.sfi(0, l_qvec)
    l_vals = l_vals_obj.comp_range_vec()
    vals_obj = fp_utils.sfi(l_vals, qvec=l_qvec, overflow=l_vals_obj.overflow)
    addr_vec = vals_obj.udec

    small_exp_vals = np.exp(l_vals)
    small_shift = (np.ceil(np.log2(small_exp_vals))).astype(np.int)
    idx = (small_shift < 0)
    small_shift[idx] = 0

    small_exp_vals = small_exp_vals * 2.**(-small_shift)
    small_exp_valsR = small_exp_vals[addr_vec]
    small_shiftR = small_shift[addr_vec]

    s_table = fp_utils.ufi(small_exp_valsR, qvec=u_table.qvec, overflow=u_table.overflow)
    ss_table = fp_utils.ufi(small_shiftR, qvec=ls_table.qvec, overflow=ls_table.overflow)

    # now create 1 Exp table
    exp_comb_0 = fp_utils.concat_fi(ls_table, u_table)
    exp_comb_1 = fp_utils.concat_fi(ss_table, s_table)

    exp_combined_fi = fp_utils.stack_fi(exp_comb_1, exp_comb_0)

    return (exp_combined_fi, u_table_qvec, shift_qvec, ratio_value)

def use_log_tables(in_val, combined_table, log_qvec, qvec):
    """
        Function performs look-up and linear interpolation if necessary.  Input is assumed to be properly quantized
    """

    u_bits = qvec[0] // 2
    l_bits = qvec[0] // 2
    all_ones = (1 << u_bits) - 1
    lower_mask = (1 << log_qvec[0]) - 1
    upper_mask = lower_mask << log_qvec[0]

    int_val = int(in_val * 2**qvec[1])
    bin_val = fp_utils.dec_to_bin(int_val, num_bits=qvec[0])

    # slice binary value -- this represents an address for look-up
    # paramsMag.qvec(1) - logMagTable.table_bits
    bot_addr = int(fp_utils.bin_to_udec(bin_val[-l_bits:]))
    top_addr = int(fp_utils.bin_to_udec(bin_val[-(u_bits + l_bits):-l_bits]))
    u_addr = top_addr + (1 << l_bits)

    use_bot = False
    if (top_addr == 0):  # or top_addr == all_ones):
        use_bot = True

    if (use_bot):
        small_value = (combined_table.udec[bot_addr] & upper_mask) >> log_qvec[0]
        ssmall_value = fp_utils.udec_to_sdec(small_value, log_qvec[0])
        # convert to signed.
        return ssmall_value * 2.**(-log_qvec[1])
    else:
        # use u_table and perform linear interpolation.
        large_val = (combined_table.udec[u_addr] & upper_mask) >> log_qvec[0]
        slarge_val = fp_utils.udec_to_sdec(large_val, log_qvec[0])
        diff_val = (combined_table.udec[u_addr] & lower_mask)
        sdiff_val = fp_utils.udec_to_sdec(diff_val, log_qvec[0])

        frac = bot_addr / (2.**l_bits)
        return (slarge_val + frac * sdiff_val)  * 2.**(-log_qvec[1])


def use_exp_tables(in_val, combined_table, log_qvec, exp_qvec, ratio_value):
    """
        Function performs exponential table lookup and correction.

        ==========
        Parameters
        ==========

            * in_val : input value in log.
            * combined_table : combined exponential table.
            * ratio_value: correction factor that combines lower and upper tables.

    """

    u_bits = log_qvec[0] // 2
    l_bits = log_qvec[0] // 2
    all_ones = (1 << u_bits) - 1
    lower_mask = (1 << exp_qvec[0]) - 1
    upper_mask = lower_mask << exp_qvec[0]

    int_val = int(in_val * 2**log_qvec[1])
    bin_val = fp_utils.dec_to_bin(int_val, num_bits=log_qvec[0])

    # slice binary value -- this represents an address for look-up
    bot_addr = fp_utils.bin_to_udec(bin_val[-l_bits:])
    top_addr = fp_utils.bin_to_udec(bin_val[-(u_bits + l_bits):-l_bits])
    u_addr = top_addr + (1 << l_bits)

    use_bot = False
    if (top_addr == 0):  # or top_addr == all_ones):
        use_bot = True

    if (use_bot):
        small_value = (combined_table.udec[bot_addr] & lower_mask) * 2.**(-exp_qvec[1])
        shift_int = (combined_table.udec[bot_addr] & upper_mask) >> exp_qvec[0]
        # convert to signed.
        return small_value * 2.**shift_int
    else:
        frac = bot_addr / float(2**l_bits)
        upper_val = (combined_table.udec[u_addr] & lower_mask) * 2.**(-exp_qvec[1])
        shift_int = (combined_table.udec[u_addr] & upper_mask) >> exp_qvec[0]
        temp = upper_val * (1 + (ratio_value - 1.) * frac)
        return temp * 2.**shift_int

def exp_avg(time_series, alpha=.1):

    ret_list = []
    prev_s = 0
    for i, val in enumerate(time_series):
        curr_s = alpha * val + (1 - alpha)*prev_s
        prev_s = curr_s
        ret_list.append(curr_s)

    return ret_list

# if __name__ == "__main__":
#     # convert_to_script('/home/phil/git_clones/chan_fpga/fpgadev-rfnoc/usrp3/lib/rfnoc/noc_block_channelizer/pfb_2x.v',
#                     #   '/home/phil/git_clones/whitetip/shared_tools/python/pfb_2x.py')
#
