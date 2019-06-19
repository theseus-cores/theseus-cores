# -*- coding: utf-8 -*-
"""
Created on Fri Jul 21 12:28:03 2016

@author: phil
"""

import scipy as sp
import scipy.signal as signal
import sys
import pdb
import matplotlib.pyplot as plt
import matplotlib.animation as manimation
import numpy as np
import copy
import time
# import ipdb
import pickle as pickle
from collections import OrderedDict
from matplotlib import rc
from argparse import ArgumentParser
import os
import gc
plt.ion()

gen_vhdl = False

try:
    from fil_utils import LPFilter
except ImportError:
    sys.path.append(os.path.abspath('../shared_tools/python/'))

finally:
    from fil_utils import LPFilter, CICDecFil
    import fp_utils as fp_utils
    from spec_an import plot_spec, plot_psd_helper, plot_spec_sig, gen_psd
    from gen_utils import upsample, add_noise_pwr, write_complex_samples, read_complex_samples, write_binary_file
    from gen_utils import gen_comp_tone, read_binary_file, ret_module_name


dirname = os.path.dirname(__file__)
if gen_vhdl:
    ip_path = os.path.join(dirname, '../vhdl/')
else:
    ip_path = os.path.join(dirname, '../verilog/')

sim_path = os.path.join(dirname, '../')
taps_per_phase = 32
gen_2X = True
six_db = 10 * np.log10(.25)
num_iters = 1000
freqz_pts = 5000
pfb_msb = 38
desired_msb = pfb_msb
qvec = (16, 15)
qvec_coef = (25, 24)
max_M = 2048

fil_transbw_factors = (10, 4.5)

rc('text', usetex=True)


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


def nextpow2(i):
    """
        Find 2**n that is equal to or greater than.
    """
    n = 0
    while (2**n) < i:
        n += 1
    return n


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
    def __init__(self, M=64, max_M=max_M, pbr=.1, sba=-80, taps_per_phase=32, gen_2X=True, qvec_coef=(25, 24),
                 qvec=(18, 17), desired_msb=None, K=None):

        self.taps_per_phase = taps_per_phase
        self.num_taps = M * taps_per_phase

        self.qvec_coef = qvec_coef
        self.qvec = qvec

        self.gen_2X = gen_2X
        self.max_M = max_M
        self.M = M
        self.sba = sba
        self.pbr = pbr
        self.desired_msb = desired_msb
        fc = 1. / M
        self.fc = fc

        self.gen_float_taps(gen_2X, K)

        # generating a 2X filter.
        self.paths = M

    def gen_float_taps(self, gen_2X, K=None):
        self.rate = 1
        if gen_2X:
            self.rate = 2
        if K is None:
            if gen_2X:
                # self.K = 10.519
                # self.K = 18.601
                self.K = 22.086093
            else:
                self.K = 30.794
        else:
            self.K = K

        taps = self.tap_equation(self.M)
        self.gen_fixed_filter(taps, desired_msb=self.desired_msb)

        return taps

    def plot_psd(self, fft_size=1024, taps=None, freq_vector=None, title=None, y_min=None, pwr_pts=None, freq_pts=None, savefig=False):

        h_log, omega = self.gen_psd(fft_size, taps, freq_vector)
        # zoom in on passband
        freq_high = (1. / self.M) * 5
        freq_low = (1. / self.M) * -5

        lidx = np.argmax(omega > freq_low)
        ridx = np.argmax(omega > freq_high)
        plot_spec(omega[lidx:ridx], h_log[lidx:ridx], title=title, y_min=y_min, plot_on=True, savefig=savefig, pwr_pts=pwr_pts, freq_pts=freq_pts, prec=6)

        return 0

    def gen_psd(self, fft_size=1024, taps=None, freq_vector=None):

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

        fig = plt.figure()
        plt.tight_layout()
        ax = fig.add_subplot(111)
        y_min = -200
        pwr_pts = six_db

        fft_size = 8192

        taps_1x = self.gen_taps(gen_2X=False)
        taps_2x = self.gen_taps(gen_2X=True)

        hlog_1x, omega = self.gen_psd(fft_size, taps_1x)
        hlog_2x, _ = self.gen_psd(fft_size, taps_2x)

        plot_psd_helper(ax, omega, hlog_1x, pwr_pts=None, label=r'\textsf{M Channelizer}', y_min=y_min,
                        label_size=18)
        plot_psd_helper(ax, omega, hlog_2x, pwr_pts=pwr_pts, label=r'\textsf{M/2 Channelizer}', y_min=y_min,
                        label_size=18)

        if savefig:
            fig.savefig('plot_compare2.png', figsize=(12, 10))
        else:
            fig.canvas.draw()

    def plot_psd_single(self, savefig=False, title=None):

        fig = plt.figure()
        ax = fig.add_subplot(111)
        y_min = -200
        pwr_pts = six_db

        fft_size = 8192

        taps_2x = self.gen_taps(gen_2X=True)

        hlog_2x, omega = self.gen_psd(fft_size, taps_2x)

        plot_psd_helper(ax, omega, hlog_2x, pwr_pts=pwr_pts, title=r'$M/2 \textsf{ Channelizer Filter PSD}$', y_min=y_min,
                        label_size=20)

        plt.tight_layout()
        if savefig:
            fig.savefig('plot_psd_single.png', figsize=(12, 10), dpi=600)
        else:
            fig.canvas.draw()


    def gen_poly_partition(self, taps):

        return np.reshape(taps, (self.M, -1), order='F')

    def gen_fixed_filter(self, taps, desired_msb=None):

        max_coeff_val = (2**(self.qvec_coef[0] - 1) - 1) * (2 ** -self.qvec_coef[1])

        taps_gain = max_coeff_val / np.max(np.abs(taps))
        taps *= taps_gain

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
        self.fil_msb = msb
        self.nfft = np.shape(self.poly_fil)[1]

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

    def tap_equation(self, fft_size, K=None):
        # using root raised erf function to generate filter prototype
        # less control but much faster option for very large filters.
        # Perfectly fine for standard low-pass filters. Link to code
        # effectively use twiddle algorithm to get the correct cut-off
        # frequency
        # http://www.mathworks.com/matlabcentral/fileexchange/15813-near-
        # perfect-reconstruction-polyphase-filterbank

        if K is None:
            K = self.K

        F = np.arange(self.num_taps)
        F = np.double(F) / len(F)

        x = K * (float(fft_size) * F - .5)
        A = np.sqrt(0.5 * self.erfc(x))

        N = len(A)
        idx = np.arange(N // 2)

        A[N - idx - 1] = np.conj(A[1 + idx])
        A[N // 2] = 0

        # this sets the appropriate -6.02 dB cut-off point requried for the channelizer
        db_diff = six_db - 10 * np.log10(.5)
        exponent = 10 ** (-db_diff / 10.)

        A = A ** exponent

        b = np.fft.ifft(A)
        b = (np.fft.fftshift(b)).real
        b /= np.sum(b)

        return b

    def gen_fil_params(self, start_size=8, end_size=4096, K_init=13.):

        end_bits = int(np.log2(end_size))
        start_bits = int(np.log2(start_size))

        M_vec = 1 << np.arange(start_bits, end_bits + 1)
        K_terms = OrderedDict()
        K_step = None
        msb_terms = OrderedDict()
        for M in M_vec:
            if self.rate == 1:
                trans_bw = 1 / (fil_transbw_factors[0] * M)
            else:
                trans_bw = 1 / (fil_transbw_factors[1] * M)
            num_taps = M * taps_per_phase
            fc = 1. / M
            filter_obj = LPFilter(M=M, P=M, pbr=self.pbr, sba=self.sba, num_taps=num_taps, fc=fc,
                                 freqz_pts=freqz_pts, num_iters=num_iters, fc_atten=six_db, qvec=self.qvec,
                                 qvec_coef=self.qvec_coef, quick_gen=True, trans_bw=trans_bw, K=K_init, K_step=K_step,
                                 num_iters_min=1000)

            K_terms[M] = filter_obj.K
            self.gen_float_taps(True, filter_obj.K)
            # use optimized paramater as the first guess on the next filter
            K_step = .01
            K_init = filter_obj.K
            msb_terms[M] = self.pfb_msb

        self.plot_psd()

        return K_terms, msb_terms

    def plot_filter(self, y_min=-100, w_time=True, fft_size=16384):
        """
            Helper function that plots the PSD of the filter.
        """
        six_db = 10 * np.log10(.25)
        plot_title = "Channelizer Filter Impulse Response"
        limit = 4 * self.fc
        step = self.fc / 50.
        freq_vector = np.arange(-limit, limit, step)
        self.plot_psd(title=plot_title, pwr_pts=six_db, fft_size=fft_size,
                      y_min=-100, freq_vector=freq_vector)

        plot_title = "Channelizer Filter Impulse Response Full"
        self.plot_psd(title=plot_title, pwr_pts=six_db, fft_size=fft_size,
                      y_min=-180)

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
            shift_out = in_vec

        return np.asarray(shift_out)

    def pf_run(self, sig_array, pf_bank, rate=1):
        """
            Runs the input array through the polyphase filter bank.
        """
        fil_out = []
        offset = self.paths / self.rate
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

    def gen_tap_vec(self):
        pfb_fil = copy.deepcopy(self.poly_fil_fi)
        pfb_fil = pfb_fil.T
        vec = np.array([])
        pad = np.array([0] * (self.max_M - self.M))
        for i, col in enumerate(pfb_fil):
            col_vec = np.concatenate((col, pad))
            vec = np.concatenate((vec, col_vec))

        return vec

    def output_tap_vec(self):
        with open('{}M_{}_taps.txt'.format(sim_path, self.M), 'w') as f:
            f.writelines(["%s\n" % int(item)  for item in self.gen_tap_vec()])

    def gen_tap_file(self, file_name=None):
        """
            Helper function that generates a single file used for programming the internal ram
        """
        vec = self.gen_tap_vec()
        print(len(vec))
        write_binary_file(vec, file_name, 'i', big_endian=True)

    def gen_mask_vec(self, percent_active=.5):
        np.random.seed(10)
        num_bins = int(self.M * percent_active)
        values = np.random.choice(a=self.M, size=num_bins, replace=False)
        values = np.sort(values)
        # map this vector to 32 bit words  -- there are 64 words in 2048 bit vector.
        bit_vector = [0] * 2048
        for value in values:
            bit_vector[value] = 1

        words = np.reshape(bit_vector, (-1, 32))
        words = np.fliplr(words)
        return fp_utils.list_to_uint(words)

    def gen_mask_file(self, file_name=None):
        """
            Helper function that generates a single file used for programming the internal ram
        """
        vec = np.array(self.gen_mask_vec())
        print(len(vec))
        write_binary_file(vec, file_name, 'I', big_endian=True)


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
        pf_bank = self.gen_pf_bank()

        sig_array = np.flipud(np.reshape(input_vec, (self.paths / self.rate, -1), order='F'))

        num_plots = 2
        if (plot_out):
            # for ii in range(num_plots):
            plt_sig = input_vec[:self.M * 10000]
            plt_array = np.reshape(plt_sig, (self.M / self.rate, -1), order='F')
            buff_array = []
            for j in range(10000):
                samp0 = plt_array[:, j]
                temp = np.concatenate((samp0, samp0))
                buff_array.extend(temp.tolist())

            plot_spec_sig(buff_array, fft_size=1024, title='Buffer Sig', y_min=None, w_time=True, markersize=None,
                          plot_on=True, savefig=True)

        fil_out = self.pf_run(sig_array, pf_bank, self.rate)

        if (plot_out):
            plt_array = np.reshape(fil_out[:, 50000:], (1, -1), order='F').flatten()
            plt_array = plt_array[:self.M * 10000]
            # for ii in range(num_plots):
            plot_spec_sig(plt_array, fft_size=1024, title='PFB Sig', y_min=None, w_time=True, markersize=None,
                          plot_on=True, savefig=True)

        # now perform circular shifting if this is a 2X filter bank.
        shift_out = self.circ_shift(fil_out.transpose())

        if (plot_out):
            # for ii in range(num_plots):
            shift_tp = shift_out.transpose()
            plt_array = np.reshape(shift_tp[:, 50000:], (1, -1), order='F').flatten()
            plt_array = plt_array[:self.M * 10000]
            plot_spec_sig(plt_array, fft_size=1024, title='Circ Shift Sig', y_min=None, w_time=True, markersize=None,
                          plot_on=True, savefig=True)

        chan_out = np.fft.fftshift(np.fft.ifft(shift_out * self.paths, axis=1))

        if (plot_out):
            for ii in range(num_plots):
                fig, (ax0, ax1) = plt.subplots(2)
                ax0.plot(np.real(chan_out[50 + ii, :]))
                ax1.plot(np.imag(chan_out[50 + ii, :]))
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
        ax = fig.add_subplot(111, projection='3d')

        exp_vec = np.exp(1j * 2 * np.pi * arg1)
        x_vec = np.imag(freq_abs * exp_vec)
        y_vec = np.arange(-1, 1., 2. / len(freq_abs))
        z_vec = np.real(freq_abs * exp_vec)
        ax.plot_wireframe(x_vec, y_vec, z_vec)  # , rstride=10, cstride=10)
        ax.set_xlabel(r'\textsf{Imag}')
        ax.set_ylabel(r'\textsf{Freq}')
        ax.set_zlabel(r'\textsf{Real}')
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

    def gen_animation(self, fps=10, dpi_val=400, mpeg_file='test.avi', sleep_time=.02):
        sel = 1
        ph_steps = 300
        inc = sel / float(ph_steps)
        num_frames = 10
        std_dev = np.sqrt(.02 / self.paths)
        mean = .5 / self.paths
        sig_bws = np.abs(std_dev * np.random.randn(self.paths) + mean)

        sig_bws = [value if value > .1 else .1 for value in sig_bws]
        cen_freqs = self.gen_cen_freqs()
        mod_obj = QPSK_Mod()
        for ii, (sig_bw, cen_freq) in enumerate(zip(sig_bws, cen_freqs)):  # cen_freqs:
            temp, _ = mod_obj.gen_frames(num_frames=num_frames, cen_freq=cen_freq, frame_space_mean=0, frame_space_var=0, sig_bw=sig_bw)
            idx = np.argmax(np.abs(temp))

            lidx = idx - 5000
            ridx = lidx + 20000

            if ii == 0:
                sig = temp[lidx:ridx]
            else:
                sig_temp = temp[lidx:ridx]
                sig[:len(sig_temp)] += sig_temp

        (sig, _) = add_noise_pwr(10, sig)
        plot_spec_sig(sig)
        FFMpegWriter = manimation.writers['ffmpeg']  # ['ffmpeg']  avconv
        metadata = dict(title='Movie Test', artist='Matplotlib', comment='Movie support!')
        writer = FFMpegWriter(fps=fps, metadata=metadata)

        pf_up = self.gen_usample_pf()
        fig = plt.figure()
        ax = fig.add_subplot(221, projection='3d')
        ax1 = fig.add_subplot(222, projection='3d')
        ax2 = fig.add_subplot(223, projection='polar')
        ax3 = fig.add_subplot(224)
        y_vec = np.arange(-1, 1., 2. / np.shape(pf_up)[1])

        (_, sig_psd) = gen_psd(sig, fft_size=len(y_vec))
        with writer.saving(fig, mpeg_file, dpi_val):
            for phase in np.arange(0, sel + 5 * inc, inc):
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
                        ax.set_xlabel(r'\textsf{Imag}')
                        ax.set_ylabel(r'\textsf{Freq}')
                        ax.set_zlabel(r'\textsf{Real}')
                        ax.view_init(30, 10)
                        ax.set_ylim(-1, 1.)
                        ax.set_xlim(-1, 1)
                        ax.set_zlim(-1, 1)
                        ax.set_title(r'\textsf{Phase Arms}')
                        ax.plot_wireframe([0, 0], [0, 0], [-1.2, 1.2], colors='k', linewidths=.5)
                        ax.plot_wireframe([0, 0], [-1.2, 1.2], [0, 0], colors='k', linewidths=.5)
                        ax.plot_wireframe([-1.2, 1.2], [0, 0], [0, 0], colors='k', linewidths=.5)

                    ax.plot_wireframe(x_vec, y_vec, z_vec)  # , rstride=10, cstride=10)

                x_sum = x_sum / self.paths
                z_sum = z_sum / self.paths

                ax1.set_xlabel(r'\textsf{Imag}')
                ax1.set_ylabel(r'\textsf{Freq}')
                ax1.set_zlabel(r'\textsf{Real}')
                ax1.view_init(30, 10)
                ax1.set_ylim(-1, 1.)
                ax1.set_xlim(-1, 1)
                ax1.set_zlim(-1, 1)
                ax1.set_title(r'\textsf{Phase Coherent Sum}')
                ax1.plot_wireframe([0, 0], [0, 0], [-1.2, 1.2], colors='k', linewidths=.5)
                ax1.plot_wireframe([0, 0], [-1.2, 1.2], [0, 0], colors='k', linewidths=.5)
                ax1.plot_wireframe([-1.2, 1.2], [0, 0], [0, 0], colors='k', linewidths=.5)
                ax1.plot_wireframe(x_sum, y_vec, z_sum)

                rot = [np.exp(1j * 2 * np.pi * (ii / float(self.paths)) * m) for ii in range(self.paths)]

                compass(np.real(rot), np.imag(rot), ax2)
                ax2.set_xlabel(r'\textsf{Phase rotator progression}')

                fil = z_sum + 1j * x_sum
                fil_log = 20 * np.log10(np.abs(fil))
                out_log = sig_psd + fil_log
                plot_psd_helper(ax3, y_vec, out_log, y_min=-85, title_size=12, label_size=10)

                fig.subplots_adjust(top=.5)   # tight_layout(h_pad=.5)
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
        title = r'\textsf{Polyphase Filter Phase Profiles}'

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

        title = r'\textsf{Reference Partition}'
        fig, ax = plt.subplots()
        ax.stem(bb1[0])
        ax.set_title(r'\textsf{Polyphase Filter -- Reference Partition}')
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

def test_8_chan():

    plt.close('all')
    gen_2X = True
    gen_test_sig(4, gen_2X)

    M = 8
    chan = Channelizer(M=M, gen_2X=gen_2X, qvec=qvec, qvec_coef=qvec_coef)

    # generate test signal.
    file_name = sim_path + 'sig_store_{}_float3.bin'.format(M)
    sig = read_complex_samples(file_name, q_first=False, format_str='h', offset=0, num_samps=None, big_endian=True)

    plot_spec_sig(sig, title='Input Signal', w_time=True, savefig=True)

    chan_out = chan.analysis_bank(sig, plot_out=True)
    chan.gen_tap_roms()
    ser_sig = np.reshape(chan_out, (1, -1), order='F').flatten()
    plot_spec_sig(ser_sig, title='PFB Signal', w_time=True, savefig=True)
    orig_sig = chan.synthesis_bank(ser_sig, plot_out=False)
    plot_spec_sig(orig_sig, title='Final Signal', w_time=True, savefig=True)

    for i, chan_sig in enumerate(chan_out):
        str_val = 'Channel - {}'.format(i)
        plot_spec_sig(chan_sig, title=str_val, w_time=True, savefig=True)

    chan.plot_filter()


def gen_samp_delay_coe(M):

    qvec = (36, 0)

    vec = np.array([0] * M)
    fi_obj = fp_utils.ret_dec_fi(vec, qvec)

    file_name = ip_path + '/sample_delay/sample_delay.coe'
    fp_utils.coe_write(fi_obj, radix=16, file_name=file_name, filter_type=False)

    file_name = ip_path + '/sample_ram/sample_ram.coe'

    ridx = 3 * M + 1
    vec = np.arange(1, ridx)  # np.array([0] * M * 3)
    fi_obj = fp_utils.ret_dec_fi(vec, qvec)
    fp_utils.coe_write(fi_obj, radix=16, file_name=file_name, filter_type=False)

    vec = np.array([0] * M)
    qvec = (36, 0)
    fi_obj = fp_utils.ret_dec_fi(vec, qvec)

    file_name = ip_path + '/circ_buff_ram/circ_buff_ram.coe'
    fp_utils.coe_write(fi_obj, radix=16, file_name=file_name, filter_type=False)

    file_name = ip_path + '/exp_averager_filter/exp_fil.coe'
    fil_vec = [1] * 64
    fi_obj = fp_utils.ret_dec_fi(fil_vec, (2, 0))
    fp_utils.coe_write(fi_obj, radix=16, file_name=file_name, filter_type=True)


def test_256_chan(gen_taps=False):

    plt.close('all')
    gen_2X = True

    M = 256
    chan = Channelizer(M=M, gen_2X=gen_2X, taps_per_phase=taps_per_phase, desired_msb=pfb_msb, qvec=qvec, qvec_coef=qvec_coef)
    # chan.gen_properties(plot_on=False)

    file_name = sim_path + '/sig_store_{}_taps.bin'.format(M)
    sig = read_complex_samples(file_name, False, 'f')

    print("Filter MSB = {}".format(chan.fil_msb))

    # generate test signal.
    chan_out = chan.analysis_bank(sig, plot_out=True)  #analysis:ignore
    chan.plot_filter()


def gen_taps(M, max_M=max_M, gen_2X=True, taps_per_phase=taps_per_phase, pfb_msb=40):

    chan = Channelizer(M=M, max_M=max_M, gen_2X=gen_2X, taps_per_phase=taps_per_phase, desired_msb=pfb_msb, qvec=qvec, qvec_coef=qvec_coef)
    print("Filter MSB = {}".format(chan.fil_msb))
    path = sim_path
    file_name = path + 'M_{}_taps.bin'.format(M)
    print(file_name)
    chan.gen_tap_file(file_name)


def gen_logic(M, gen_2X=True, taps_per_phase=taps_per_phase, sample_width=18):

    from cStringIO import StringIO
    import shutil

    plt.close('all')

    chan = Channelizer(M=M, gen_2X=gen_2X, taps_per_phase=taps_per_phase, desired_msb=pfb_msb, qvec=qvec, qvec_coef=qvec_coef)
    gen_taps(M, gen_2X, taps_per_phase)

    print("Filter MSB = {}".format(chan.filter.msb))

    c_str = StringIO()
    c_str.reset()
    # store c_str to file.
    with open('../verilog/file.xml', 'w') as fh:
        c_str.seek(0)
        shutil.copyfileobj(c_str, fh)

    # generate half-band filter
    fil_obj = LPFilter(num_taps=40, half_band=True)
    fil_obj.gen_fixed_filter(coe_file=ip_path + '/hb_fil/hb_fil.coe')

    print("HB Filter MSB = {}".format(fil_obj.msb))

    fil_obj.plot_psd()


def populate_fil_table(start_size=8, end_size=2048):

    chan = Channelizer(M=8, gen_2X=gen_2X, taps_per_phase=taps_per_phase, qvec=qvec, qvec_coef=qvec_coef)
    K_terms, msb_terms = chan.gen_fil_params(start_size, end_size)

    print(K_terms)
    print(msb_terms)

def gen_animation():
    chan_obj = Channelizer(M=4, taps_per_phase=taps_per_phase, gen_2X=False, qvec=qvec, qvec_coef=qvec_coef)
    chan_obj.gen_animation()

def find_best_terms():
    chan_obj = Channelizer(M=16, taps_per_phase=taps_per_phase, gen_2X=True, qvec=qvec, qvec_coef=qvec_coef)
    K_terms, msb_terms = chan_obj.gen_fil_params(8, 32)

    print(K_terms, msb_terms)

def gen_tones(freq_vec):
    num_samps = 8192 * 1024
    path = sim_path
    tones = [gen_comp_tone(num_samps, float(freq_value), 0) for freq_value in freq_vec]
    sig = np.sum(tones, 0)
    sig = sig / (2. * np.max(np.abs(sig)))

    sig_fi = fp_utils.ret_fi(sig, qvec=(16, 15), overflow='saturate')

    plot_spec_sig(sig_fi.vec[:2048], title='tone truth', y_min=-100, savefig=True, w_time=True, path=path)
    write_complex_samples(sig_fi.vec, path + 'sig_tones_input.bin', False, 'h', big_endian=True)

def gen_count(M=512):
    path = sim_path

    num_samps = 8192 * 256
    count = np.arange(0, num_samps)
    count = count % M
    count = count + 1j * 0

    sig_fi = fp_utils.ret_fi(count, qvec=(16, 0), overflow='saturate')
    write_complex_samples(sig_fi.vec, path + 'sig_count_{}.bin'.format(M), False, 'h', big_endian=True)


def process_chan_out(file_name, row_offset=100):

    samps = read_binary_file(file_name, format_str='Q', big_endian=True)
    print(len(samps))
    # samps = samps[42600:43500]
    samps = samps[1000:4000]
    if type(samps) is int:
        print('File does not exist')
        return -1

    if len(samps) == 0:
        print("Not enough samples in File")
        return -1

    mask_i = np.uint64(((1 << 16) - 1) << 16)
    mask_q = np.uint64((1 << 16) - 1)
    mask_tuser = np.uint64(((1 << 24) - 1) << 32)
    mask_eob = np.uint64(1 << 56)
    mask_bin_num = (1 << 11) - 1

    i_sig = [int(samp & mask_i) >> 16 for samp in samps]
    q_sig = [samp & mask_q for samp in samps]
    tuser_sig = [int(samp & mask_tuser) >> 32 for samp in samps]
    eob_sig = [int(samp & mask_eob) >> 56 for samp in samps]
    fft_bin_sig = [sig & mask_bin_num for sig in tuser_sig]

    offset = np.where(np.array(fft_bin_sig) == 0)[0][0]

    i_sig = fp_utils.uint_to_fp(i_sig[offset:], qvec=(16, 15), signed=1, overflow='wrap')
    q_sig = fp_utils.uint_to_fp(q_sig[offset:], qvec=(16, 15), signed=1, overflow='wrap')
    tuser_sig = tuser_sig[offset:]
    eob_sig = eob_sig[offset:]
    fft_bin_sig = fft_bin_sig[offset:]

    M = np.max(fft_bin_sig) + 1

    trunc = len(i_sig) % M
    if trunc:
        i_sig = i_sig.float[:-trunc]
        q_sig = q_sig.float[:-trunc]
        tuser_sig = tuser_sig[:-trunc]
        fft_bin_sig = fft_bin_sig[:-trunc]
    else:
        i_sig = i_sig.float
        q_sig = q_sig.float

    comp_sig = i_sig + 1j * q_sig
    comp_rsh = np.reshape(comp_sig, (M, -1), 'F')

    resps = []
    wvecs = []
    time_sigs = []
    row_size = np.shape(comp_rsh)[1] - row_offset
    if row_size < 64:
        print("Not enough samples in file for conclusive spectral plots")
        return -1

    if row_size > 2048:
        fft_size = 2048
    else:
        fft_size = row_size

    for ii, row in enumerate(comp_rsh):
        row = row[row_offset:]
        print(np.shape(row))
        if ii < 8:
            wvec, psd = gen_psd(row, fft_size=256, window='blackmanharris')
            resps.append(psd)
            wvecs.append(wvec)
            time_sigs.append(row)
            lg_idx = np.argmax(np.abs(row))
            real_value = np.real(row[lg_idx])
            imag_value = np.imag(row[lg_idx])
            res_value = np.max(psd)
            print("{} : Largest value = {}, i{} - resp = {} db".format(ii, real_value, imag_value, res_value))

    # title = 'Channelized Output'
    # fig, ax = plt.subplots(nrows=4, ncols=2)
    # fig.subplots_adjust(bottom=.10, left=.1, top=.95)
    # fig.subplots_adjust(hspace=.50, wspace=.2)
    # fig.set_size_inches(12., 12.)
    # fig.set_dpi(120)
    # plot_psd_helper(ax[0][0], wvecs[0], resps[0], title='Channel 0', y_min=-120, y_max=10)
    # plot_psd_helper(ax[0][1], wvecs[1], resps[1], title='Channel 1', y_min=-120, y_max=10)
    # plot_psd_helper(ax[1][0], wvecs[2], resps[2], title='Channel 2', y_min=-120, y_max=10)
    # plot_psd_helper(ax[1][1], wvecs[3], resps[3], title='Channel 3', y_min=-120, y_max=10)
    # plot_psd_helper(ax[2][0], wvecs[4], resps[4], title='Channel 4', y_min=-120, y_max=10)
    # plot_psd_helper(ax[2][1], wvecs[5], resps[5], title='Channel 5', y_min=-120, y_max=10)
    # plot_psd_helper(ax[3][0], wvecs[6], resps[6], title='Channel 6', y_min=-120, y_max=10)
    # plot_psd_helper(ax[3][1], wvecs[7], resps[7], title='Channel 7', y_min=-120, y_max=10)

    # file_name = copy.copy(title)
    # file_name = ''.join(e if e.isalnum() else '_' for e in file_name)
    # file_name += '.png'
    # file_name = file_name.replace("__", "_")
    # print(file_name)
    # fig.savefig(file_name)

    print(M)
    if len(resps) > 0:
        for j in range(M):
            plot_spec(wvecs[j], resps[j], title='PSD Overlay {}'.format(j), w_time=True, y_min=-200, y_max=20.,
                      time_sig=time_sigs[j], markersize=None, plot_on=False, savefig=True)

def process_synth_out(file_name, row_offset=600):

    samps = read_binary_file(file_name, format_str='I', big_endian=True)
    mod_name = ret_module_name(file_name)
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
    q_si1g = q_sig.float

    comp_sig = i_sig + 1j * q_sig
    if len(comp_sig) < 2000:
        print("Not enough Synthesis Data : Data is {} samples".format(len(comp_sig)))
        return 1
    comp_sig = comp_sig[1000:]

    plot_spec_sig(comp_sig, title='Synthesizer PSD Output', w_time=True, y_min=-100, y_max=None, plot_on=False, savefig=True)
    print("Synthesis Output Produced")

def gen_mask_files(M_list):
    path = sim_path
    for M in M_list:
        chan_obj = Channelizer(M=M, taps_per_phase=taps_per_phase, gen_2X=True, desired_msb=desired_msb, qvec=qvec, qvec_coef=qvec_coef)
        file_name = path + 'M_{}_mask.bin'.format(M)
        chan_obj.gen_mask_file(file_name)


def gen_tap_plots(M_list):

    for M in M_list:
        chan_obj = Channelizer(M=M, taps_per_phase=taps_per_phase, gen_2X=True, desired_msb=desired_msb, qvec=qvec, qvec_coef=qvec_coef)
        # chan_obj.plot_psd_single(savefig=True)
        gen_taps(M, max_M, gen_2X=True, taps_per_phase=taps_per_phase, pfb_msb=desired_msb)
        print(chan_obj.pfb_msb)
        tap_title = 'taps psd M {}'.format(M)
        # get adjacent bins and plot suppression value.
        freq_pts = [- 1.25 / M, 1.25 / M]
        fft_size=16384
        if M > 256:
            fft_size=16384 * 4
        chan_obj.plot_psd(fft_size, taps=None, freq_vector=None, title=tap_title, savefig=True, pwr_pts=six_db, freq_pts=freq_pts)
        gc.collect()

def gen_tap_vec(M_list):
    for M in M_list:
        chan_obj = Channelizer(M=M, taps_per_phase=taps_per_phase, gen_2X=True, desired_msb=desired_msb, qvec=qvec, qvec_coef=qvec_coef)
        chan_obj.output_tap_vec()

def get_args():

    M_list = [8, 16, 32, 64, 128, 256, 512, 1024, 2048]
    avg_len = 256
    chan_file = sim_path + 'chan_output.bin'
    # synth_file = sim_path + 'synth_out_8_file.bin'

    parser = ArgumentParser(description='Channelizer CLI -- Used to generate RTL code, input stimulus, and process output of RTL simulation.')
    parser.add_argument('-c', '--rtl_chan_outfile', type=str, help='Process RTL output file specified by input string -- can use \'default\' as input ')
    # parser.add_argument('-s', '--rtl_synth_outfile', type=str, help='Process RTL output file specified by input string -- can use \'default\' as input ')
    parser.add_argument('-i', '--rtl_sim_input', nargs='+', help='Generate tones based on list of tone frequencies (Normalized Discrete Freq range -1 -> 1) example list .25 .5 ', required=False)
    parser.add_argument('-t', '--generate_taps', action='store_true', help='Generates tap files for all valid FFT Sizes : [8, 16, 32, 64, 128, 256, 512, 1024, 2048]')
    parser.add_argument('-m', '--generate_masks', action='store_true', help='Generate Mask files for all valid FFT Sizes : [8, 16, 32, 64, 128, 256, 512, 1024, 2048]')
    parser.add_argument('-o', '--opt_taps', action='store_true', help='Returns optimized filter parameters all valid FFT Sizes : [8, 16, 32, 64, 128, 256, 512, 1024, 2048]')
    args = parser.parse_args()

    if args.rtl_chan_outfile is not None:
        if args.rtl_chan_outfile.lower() != 'default':
            chan_file = args.rtl_chan_outfile
        process_chan_out(chan_file)

    # if args.rtl_synth_outfile is not None:
    #     if args.rtl_synth_outfile.lower() != 'default':
    #         synth_file = args.rtl_synth_outfile
    #     process_synth_out(synth_file)

    if args.rtl_sim_input is not None:
        gen_tones(args.rtl_sim_input)

    if args.generate_taps:
        gen_tap_plots(M_list)
        gen_tap_vec(M_list)

    if args.generate_masks:
        gen_mask_files(M_list)

    if args.opt_taps:
        populate_fil_table()


    return args


if __name__ == "__main__":
    modem_args = get_args()
