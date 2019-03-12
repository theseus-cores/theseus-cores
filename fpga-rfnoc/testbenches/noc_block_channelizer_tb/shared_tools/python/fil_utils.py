# -*- coding: utf-8 -*-F
"""
Created on Mon Jun 13 23:30:30 2016

@author: phil
"""
import numpy as np
import fp_utils as fp_utils
import scipy as sp
import scipy.signal as signal
from spec_an import plot_spec, gen_freq_vec, plot_psd_helper, plot_spec_sig, gen_psd
from gen_utils import upsample
import copy
# import ipdb  #analysis:ignore
from fractions import Fraction
from scipy import interpolate
import matplotlib.pyplot as plt
import pickle as pickle

__version__ = "1.0"


max_uprate = 5000
taps_per_phase = 48


def gen_fixed_poly_filter(poly_fil, qvec_coef=(25, 24), qvec=(16, 15),
                          qvec_out=None, P=1):
    """
       Computes coefficients that maximize dynamic range for a polyphase filter
       implementation.
    """
    # quantize filters.
    if qvec_out is None:
        qvec_out = qvec

    poly_fil_fi = fp_fil_repr(poly_fil, qvec_coef)

    poly_fil_float = poly_fil_fi.vec * (2 ** -qvec_coef[1])

    # maximize filter output for best dynamic range
    (new_fi, msb, max_tuple) = max_filter_output(poly_fil_float, qvec_coef, P=P,
                                                 input_width=qvec[0],
                                                 output_width=qvec_out[0])

    (s_gain, delta_gain, path_gain, bit_gain, corr_gain, corr_msb, snr_gain) = max_tuple

    return new_fi


def ret_group_delay(taps):
    """
        Helper function computes group delay of FIR filter.
    """
    grp_delay = (len(taps)-1)//2

    return grp_delay

def mov_avg(input_vec, num_taps):
    """
        Simple Boxcar filter
    """
    avg_mask = np.ones((num_taps,)) / float(num_taps)
    return np.convolve(input_vec, avg_mask, 'same')


def smooth_fil(num_iters, input_vec, num_taps=3):
    """
        Smooths a signal by repetitively applying a mov_avg filter of length,
        num_taps.  Maintains original length and calculates initial filter
        coefficients to avoid steps in the output.
    """

    smooth_out = input_vec.copy()

    orig_max = np.max(np.abs(smooth_out))
    orig_min = np.min(np.abs(smooth_out))
    for ii in range(num_iters):
        (smooth_out, _) = mov_avg(smooth_out, num_taps, init_output=smooth_out[0], pad=True)

    offset = (num_iters * (num_taps - 1)) // 2
    smooth_out = smooth_out[offset:]
    pad = smooth_out[-1] * np.ones((offset,))
    smooth_out = np.concatenate((smooth_out, pad))

    orig_diff = orig_max - orig_min
    new_min = np.min(smooth_out)
    new_diff = np.max(smooth_out) - new_min
    slope = orig_diff / new_diff

    for (ii, val) in enumerate(smooth_out):
        smooth_out[ii] = slope * (val - new_min) + orig_min

    return smooth_out


def pb_comp(comp_resp, num_taps, freq_vector, trans_bw=.25, comp_freq=.25, weights=None):
    """
        Function generates a compensation filter using
        firwin2 function from the scipy.signal library.

        ==========
        Parameters
        ==========

            * num_taps : (int)
                Filter order of the compensation filter.
            * comp_resp : (ndarray)
                Frequency response to be compensated
                passed in as Log.
            * freq_vector : (ndarray)
                Frequency vector corresponding to comp_resp.  Begins at 0.
            * trans_bw : (float)
                Transition BW of compensation filter.
            * comp_freq : (float)
                Desired frequency that the user would like
                to compensate for.  Given in normalized
                discrete frequency units.
            * weights : (list)
                weight vector.  Equals the ratios of
                number of points to use for each region.

        =======
        Returns
        =======

            b_comp : (ndarray)
                Filter coefficients.

    """
    # minimum number of frequency points.
    min_points = 5
    if weights is None:
        weights = [50, 50, 50]

    idx = np.argmax(comp_resp)

    idx2 = np.argwhere(freq_vector >= comp_freq)[0]
    if (idx2 > idx):
        idx = idx2

    a_end = -comp_resp[idx]
    a_end = 10.**(a_end / 20.)
    # amplitude pass band.
    amp_pass = -comp_resp[0:idx + 1]
    amp_pass = 10.**(amp_pass / 20.)
    # pass band frequency vector.
    f_pass = freq_vector[0:idx + 1]

    pass_points = weights[0] * min_points
    if (idx - 1 < pass_points):
        pass_frac = np.ceil(pass_points / len(amp_pass))
        interp_f = sp.interpolate.interp1d(f_pass, amp_pass, kind='linear')
        step = np.diff(f_pass)[0]
        f_pass = np.arange(f_pass[0], f_pass[-1], step / pass_frac)
        amp_pass = interp_f(f_pass)

    f_pass[0] = 0.

    f1 = f_pass[-1] + np.diff(f_pass)[0]
    f2 = comp_freq + trans_bw

    trans_points = weights[1] * min_points

    step = (f2 - f1) / trans_points
    # create transition band frequency points.
    f_trans = np.arange(f1, f2, step)
    # creating a straight line for the transition band.
    slope = -a_end / (f2 - f1)
    amp_trans = a_end + slope * (f_trans - f1)

    # create stopband points.
    stop_points = weights[2] * min_points
    f_stop_1 = f_trans[-1] + np.diff(f_trans)[0]
    step = (1 - f_stop_1) / stop_points
    f_stop = np.arange(f_stop_1, 1., step)
    amp_stop = np.zeros(np.shape(f_stop))

    f_stop[-1] = 1.

    f = np.concatenate((f_pass, f_trans, f_stop))
    amp_vec = np.concatenate((amp_pass, amp_trans, amp_stop))

    # run amp vector through smoother.
    amp_vec = smooth_fil(10, amp_vec)
    amp_vec[-1] = 0.
    b_comp = sp.signal.firwin2(num_taps, f, amp_vec)

    return b_comp


def gen_resamp_fil(path='./'):

    # frac_obj = Fraction.from_float(1. / (resamp_rat)).limit_denominator(max_uprate)
    up_rate = max_uprate

    fc = .55 / up_rate
    taps_phase = taps_per_phase

    resamp_fil = LPFilter(P=up_rate, num_taps=taps_phase * up_rate, num_iters=200, quick_gen=1, sba=-120, pbr=.1,
                          trans_bw=.65 * fc, fc=fc, K=12.2, freqz_pts=10000)

    fig, (ax, ax1) = plt.subplots(2)
    plot_psd_helper(ax, w_vec=resamp_fil.omega, amp=resamp_fil.h_log, pwr_pts=resamp_fil.fc_atten,
                    label=r'\textsf{Proto Filter}', y_min=-200, prec=9)

    start_freq = -10 * fc
    stop_freq = 10 * fc
    freq_step = (stop_freq - start_freq) / 8192
    freq_vector = np.pi * np.arange(-10 * fc, 10 * fc, freq_step)
    (w_vec, h_log) = ret_fil_freq_resp(resamp_fil.b, freq_vector)

    plot_psd_helper(ax1, w_vec=w_vec, amp=h_log, label=r'\textsf{Proto Filter Full}', y_min=-300, y_max=20, prec=9)

    path = path + '/resamp_fil.p'
    pickle.dump(resamp_fil.b, open(path, 'wb'))


def resampler(input_vec, resamp_rat, max_uprate=5000, taps_per_phase=48, fc=None):
    """
        Implements a Resampler based on a nearest neighbor Polyphase
        interpolator. Generates the filter internally and applies the nearest
        neighbor interpolation. It also applies any follow on downsampler that
        is required.

        ==========
        Parameters
        ==========

        input_vec  : ndarray Input vector that the interpolator processes.
        resamp_rat : double Ratio : (output_rate / input_rate)

        =======
        Returns
        =======

        * output   : ndarray resampled values.
    """
    if fc is None:
        fc = .25
    taps_phase = 141

    # this filter ensures that the input vector is resampled the 4 samples per baud.
    # the high K value generates a sharp transition
    init_fil = LPFilter(P=4, num_taps=taps_phase * 4, num_iters=1, quick_gen=1, sba=-120, pbr=.1,
                        trans_bw=.01, fc=fc, K=120.0)

    fil_gain = np.sum(init_fil.b) / 4.

    init_fil.b /= fil_gain

    input_vec = signal.upfirdn(init_fil.b, input_vec, 4, 1)   # , all_samples=False)

    # always going up by a factor of 4.  Relaxes filter constraints considerably.
    frac_obj = Fraction.from_float(1. / (resamp_rat)).limit_denominator(max_uprate)

    up_rate = frac_obj.denominator
    step = frac_obj.numerator

    # Resampling
    fc = .55 / up_rate
    taps_phase = taps_per_phase

    resamp_fil = LPFilter(P=up_rate, num_taps=taps_phase * up_rate, num_iters=1, quick_gen=1, sba=-120, pbr=.1,
                          trans_bw=.45 * fc, fc=fc, K=12.0)

    # Resampling
    # Use resampler to do the job.
    # upsample symbols (minimum required to ensure 0 ISI) and pass through
    # filter conducts upsampling and filtering.
    # can control symbol rate by using arbitrary resampler.

    # Using a step of 1 will effectively return a symbol rate of
    # 1/up_rate*(1+alpha) and a sample per symbol rate of upsample.
    # Use the arbitrary resampler to configure any signal bandwidth desired.

    output = signal.upfirdn(resamp_fil.b, input_vec, up_rate, step)
    output = output[::4]

    return output


def ret_fil_freq_resp(taps, freq_vector=None, whole=True, freq_pts=5000, rot_freq=False):
    """
        Helper function generates the frequency response of a filter.

        ==========
        Parameters
        ==========

            * taps - ndarray (float)
                taps of filter.
            * freq_vector - ndarray (float)
                 vector of frequency points to be calculated (optional),
                 overides whole and worN parameters
            * whole - boolean
                Flag indicates whether to compute the frequency response
                between -pi and pi.
            * freq_pts - int
                Number of points to break up the frequency response.

        =======
        Returns
        =======

            * tuples (omega,h_log)
                Returns a tuple containing the frequency vector and
                the amplitude response in dB.

    """
    if freq_vector is not None:
        (omega, h) = sp.signal.freqz(taps, 1, worN=freq_vector, whole=whole)
    else:
        (omega, h) = sp.signal.freqz(taps, 1, worN=freq_pts, whole=whole)

    omega = omega / np.pi
    idx0 = (h == 0.)
    h[idx0] = np.finfo(np.float).tiny

    h_log = 20. * np.log10(np.abs(h))

    if rot_freq is True:
        omega = gen_freq_vec(len(omega))['w']
        omega = omega[:len(h_log)]
        h_log = np.fft.fftshift(h_log)

    return (omega, h_log)


def fp_fil_repr(b, qvec_coef):
    """
        Returns a fixed point; representation of the filter based on
        the QVecCoeff parameter supplied.

        ==========
        Parameters
        ==========
        **values** : given ndarray representing the floating point
                        impulse response.

        =======
        Returns
        =======

        out : ndarray
            Array of fixed point values representing the given input
            ndarray.  Uses the object supplied qvec_coef for calculations.
    """
    b_new = copy.copy(b)
    fp_taps = fp_utils.ret_dec_fi(0, qvec=qvec_coef)
    taps_gain = fp_utils.comp_max_value(fp_taps.qvec, 1) / np.max(np.abs(b_new))

    b_new *= taps_gain
    fp_taps = fp_utils.ret_dec_fi(b_new, qvec=qvec_coef)
    # return quantized taps
    return fp_taps


def comp_fil_gains(taps, P=1):
    """
        Computes the signal gain, noise gain, snr_gain, path_gain
        (polyphase implementations), and bit growth of a filter.

        ==========
        Parameters
        ==========

        taps : ndarray
            filter taps

        P : int
            upsampling rate of filter.  Default is 1.

        =======
        Returns
        =======

        Tuple with following return values.

        * s_gain    : Signal Gain
        * n_gain    : Noise Gain
        * snr_gain  : SNR Gain
        * path_gain : Path Gain
        * bit_gain  : Filter bit growth
    """
    taps = np.atleast_2d(taps)
    # need the abs for complex filter taps.
    if P > 1:
        n_gain = np.max(np.sqrt(np.sum(np.abs(taps)**2, axis=1)))
        s_gain = np.abs(np.max(np.sum(taps, axis=1)))
    else:
        n_gain = np.max(np.sqrt(np.sum(np.sum(np.abs(taps)**2, axis=1))))
        s_gain = np.abs(np.max(np.sum(np.sum(taps, axis=1))))

    # taps = taps.flatten()

    snr_gain = 20. * np.log10(s_gain / n_gain)
    path_gain = np.max(np.abs(np.sum(taps, axis=1)))
    bit_gain = fp_utils.nextpow2(np.max(s_gain))

    return (s_gain, n_gain, snr_gain, path_gain, bit_gain)


def comp_proc_gain(taps):
    """
        Computes the processing gain of a filter

        ==========
        Parameters
        ==========

        taps  : ndarray
            impulse response of filter

        =======
        Returns
        =======

        out : float
            Computed processing gain of filter.
    """
    return (np.sum(taps)**2.) / np.sum(taps**2.)


def comp_num_bits(taps_fi, input_width=16, output_width=None, max_input=None, P=1):
    """
        Computes bit usage, signal gain, msb, and final slice width of a fixed
        point filter.

        ==========
        Parameters
        ==========

        * taps : fi object.

        * max_input    : Maximum possible input value
        * output_width : Total number of bits desired on the output.
        * input_width  : Total number of bits on the input.
        * P           : upsampling rate of filter.

        =======
        Returns
        =======

        Tuple :

        * percent_max   : percentage of the 'bits used' on the output
        * slice_width   : number of bits on output.
                            Full width computed if output_width=None
        * msb           : computed value of msb
        * s_gain        : signal gain due to filter.

    """
    taps = taps_fi.vec

    (s_gain, n_gain, snr_gain, path_gain, bit_gain) = comp_fil_gains(taps, P)

    if max_input is not None:
        max_value = np.max(s_gain) * np.max(max_input)
    else:
        max_input = 2**(input_width - 1) - 1

    max_value = np.max(s_gain) * np.max(max_input)
    num_bits = fp_utils.ret_num_bitsS(max_value)
    msb = num_bits - 1
    max_value = np.max(s_gain) * np.max(max_input)
    bit_shift = 0
    if output_width is not None:
        bit_shift = num_bits - output_width
    max_output = np.floor(max_value * 2. ** -bit_shift)

    output_width = fp_utils.ret_num_bitsS(max_output)

    bit_gain_frac = np.log2(np.abs(np.max(np.sum(s_gain))))
    percent_max = bit_gain_frac % 1.

    percent_max = 100 if (percent_max == 0) else 100 * percent_max

    slice_width = output_width

    return (percent_max, slice_width, msb, s_gain, n_gain, snr_gain, path_gain, bit_gain)


def max_filter_output(taps, qvec_coef, P=1, input_width=16, output_width=16, correlator=False):
    """
        This function will scale the coefficients to maximize the usage of the
        output bits.  We do this by scaling down the coefficients so that the
        gain is as close as possible, but not greater than the
        nearest power of 2

          params  - the input structure to the filter routine
          num_out  - the output of the comp_num_bits function
          b_fi     - fi object
    """
    single_dim = False
    if (len(np.shape(taps)) == 1):
        single_dim = True
    tap_width = qvec_coef[0]
    tap_fraction_len = qvec_coef[1]
    taps_fi = fp_utils.ret_dec_fi(taps.real, qvec_coef)
    if np.iscomplexobj(taps):
        temp = fp_utils.ret_dec_fi(taps.imag, qvec_coef)
        taps = taps_fi.vec + 1j * temp.vec
        taps_fi = fp_utils.Fi(taps, qvec_coef)

    (percent_max, slice_width,
     msb, s_gain, n_gain, snr_gain,
     path_gain, msb_gain) = comp_num_bits(taps_fi, P=P, input_width=input_width, output_width=output_width)

    taps = taps_fi.vec

    taps = np.atleast_2d(taps)
    # First figure out how much of the bit we are using
    max_coef_val = 2.**msb_gain - 1
    in_use = s_gain / max_coef_val
    if np.isnan(in_use):
        in_use = 0

    taps = np.atleast_2d(taps)
    corr_gain = np.max(np.sum(np.abs(taps), axis=1))
    # taps = taps.flatten()
    # max correlated value -- this assumes a
    # corr_gain = fp_utils.nextpow2(temp)
    if correlator:
        s_gain = corr_gain
        msb_gain = fp_utils.nextpow2(s_gain)
        max_coef_val = 2.**msb_gain - 1
        in_use = s_gain / max_coef_val
    # only change the coefficients if less than 90# of the range is in use.
    if in_use > .9:
        new_b = taps
        delta_gain = 1
    else:
        # note we are scaling down here hence the - 1
        msb = msb - 1
        delta_gain = .5 * (max_coef_val / s_gain)
        if np.iscomplexobj(taps):
            real_temp = np.floor(np.real(taps) * delta_gain).astype(int)
            imag_temp = np.floor(np.imag(taps) * delta_gain).astype(int)
            new_b = real_temp + 1j * imag_temp
        else:
            new_b = np.floor(taps * delta_gain).astype(int)

        s_gain = np.abs(np.max(np.sum(new_b, axis=1)))
        path_gain = np.max(np.abs(np.sum(new_b, axis=1)))
        msb_gain = fp_utils.nextpow2(path_gain)
        temp = np.max(np.sum(np.abs(new_b), axis=1))
        corr_gain = fp_utils.nextpow2(temp)

    corr_msb = corr_gain + input_width - 1
    new_b = new_b * 2**-tap_fraction_len
    if single_dim:
        new_b = new_b.flatten()
    # modify object's parameters.
    qvec = (tap_width, tap_fraction_len)
    new_fi = fp_utils.ret_dec_fi(new_b.real, qvec)
    if np.any(np.iscomplexobj(new_b)):
        temp = fp_utils.ret_dec_fi(new_b.imag, qvec)
        new_vec = new_fi.vec + 1j * temp.vec
        new_fi = fp_utils.Fi(new_vec, qvec)

    return (new_fi, msb, (s_gain, delta_gain, path_gain, msb_gain, corr_gain, corr_msb, snr_gain))


class CICDecFil(object):
    """
        Routine determines the ideal bit widths for each stage
        of a CIC Decimator

        ==========
        Parameters
        ==========

        - Input defaults given inside ()

            * M - int (1)
                Differential delay of CIC comb sections.
            * N - int (1)
                Order of CIC filter, i.e. number of integrator
                and comb sections.
            * r_min - int (1)
                Minimum decimation rate of CIC Filter
            * r_max - int (1)
                Maximum decimation rate of CIC Filter
            * q_vec_in - tuple (16, 15)
                q vector on the input of the CIC Filter.
            * max_input - int (None)
                Optional input parameter -- maximum input value

            * qvec_coef - tuple
                Q vector of coefficients used for compensation filter.

    """

    def __init__(self, M=1, N=1, r_min=1, r_max=1, m_min=1, m_max=1, R=1, qvec_in=(16, 15), qvec_out=(16, 15),
                 qvec_coef=(18, 17), fft_size=1024, max_input=None):

        self.qvec_in = qvec_in
        self.qvec_out = qvec_out
        if r_max < R:
            r_max = R

        if r_min > r_max:
            r_min = r_max

        self.M = M
        self.N = N
        self.r_min = r_min
        self.r_max = r_max
        self.m_min = m_min
        self.m_max = m_max
        self.input_width = qvec_in[0]
        self.output_width = qvec_out[0]
        self.max_input = max_input
        self.qvec_in = qvec_in
        self.qvec_out = qvec_out
        self.qvec_coef = qvec_coef
        self.fft_size = fft_size
        self.b_comp = None

        if self.m_max < self.M:
            self.m_max = self.M

    def ret_bmax(self, R=None, M=None):
        if R is None:
            R = self.r_max
        if M is None:
            M = self.m_max

        return (np.ceil(self.N * np.log2(R * M) + self.input_width - 1).astype(np.int))

    def ret_btrunc(self, b_max):
        return (b_max + 1) - self.output_width

    def ret_m_gain(self, R=None, M=None):
        if R is None:
            R = self.r_max
        if M is None:
            M = self.m_max

        temp = np.float(R) * M
        gain = temp**self.N
        return np.max(gain)

    def cic_dec_trunc(self):
        """
            Routine determines the ideal bit widths for each stage
            of a CIC Decimator.  Taken from Hogenauer's Paper.

            ==========
            Parameters
            ==========

            - kwargs input defaults given inside ()

                * M - int (1)
                    Differential delay of CIC comb sections.
                * N - int (1)
                    Order of CIC filter, i.e. number of integrator
                    and comb sections.
                * r_min - int (1)
                    Minimum decimation rate of CIC Filter
                * r_max - int (1)
                    Maximum decimation rate of CIC Filter
                * m_min - int (1)
                    Minimum differential delay of CIC Filter
                * m_max - int (1)
                    Maximum differential delay of CIC Filter
                * input_width - int (16)
                    Input width of CIC Filter.
                * output_width - int (16)
                    Final stage output width of CIC Filter.
                * max_input - int (None)
                    Optional input parameter -- maximum input value

            =======
            Returns
            =======

                * out - nparray
                    Vector of stage widths listed with integrator stages first
                    and then with comb stages -- no change in bit width through
                    decimator.
        """
        temp = np.arange(self.r_min, self.r_max + 1).astype(np.float) * self.M
        gain = temp**self.N
        self.m_gain = np.max(gain)

        bit_gain = np.ceil(np.log2(np.max(gain)))

        if self.max_input is not None:
            num_max = self.m_gain * np.max(self.max_input)
            num_bits = fp_utils.ret_num_bitsS(num_max)
            # slice off top CIC Bits
            bit_shift = num_bits - self.output_width
            self.max_output = np.floor(num_max * 2.**-bit_shift)
            msb = num_bits - 1
        else:
            msb = self.input_width + bit_gain - 1
            num_bits = msb + 1
            max_value = 2.**msb - 1
            bit_shift = num_bits - self.output_width
            self.max_output = np.floor(max_value * 2.**-bit_shift)

        lim1 = 2. * self.N
        lim2 = (self.r_max * self.m_max - 1) * self.N + self.N
        limits = (lim1, lim2)
        limits = sorted(limits, reverse=True)

        self.max_width = np.int(num_bits)

        self.h_vec = np.zeros((2 * self.N, limits[0]))
        # Register growth equation -- Reference Hogenauer's Paper under
        # register growth equations 9a and 9b - Use Max Decimation.
        # pdb.set_trace()
        for j in np.arange(1, self.N + 1):
            kmax = (self.r_max * self.m_max - 1) * self.N + j - 1
            for k in range(kmax + 1):
                temp_len = np.int(np.floor(k / (self.r_max * self.m_max)) + 1)
                # pdb.set_trace()
                temp = np.zeros((temp_len,))
                for l in range(tempLen):
                    term1 = (-1)**l * sp.misc.comb(self.N, l)
                    term2 = sp.misc.comb((self.N - j + k - self.r_max * self.m_max * l), (k - self.r_max * self.m_max * l))
                    temp[l] = term1 * term2
                self.h_vec[j - 1, k] = np.sum(temp)

        for j in np.arange(self.N + 1, 2 * self.N + 1):
            # term in loop comes from 9b where j = N+1:2N

            for k in range(2 * self.N + 2 - j):
                self.h_vec[j - 1, k] = (-1)**k * \
                    sp.misc.comb(2 * self.N + 1 - j, k)

        nTerms = np.shape(self.h_vec)[0]
        Fsq = np.zeros((nTerms,))

        for ii in range(nTerms):
            Fsq[ii] = np.sum(self.h_vec[ii, :]**2.)

        self.F = np.sqrt(Fsq)

        self.b_max = self.ret_bmax()

        self.Btrunc = self.ret_btrunc(self.b_max)
        sigma_sq_2n_1 = (12.**-1) * 2.**(2 * self.Btrunc)

        # reference Hogenauer Equation Set 9 -- page 3 of
        # An Economical Class of Digital Filters for Decimation and
        # Interpolation"
        Bk = np.zeros((len(self.F),))
        for (ii, val) in enumerate(self.F):
            # this computes the number of bits to truncate off the bottom at
            # each stage.
            Bk[ii] = (.5 * np.log2(6. / self.N) + np.log2(np.sqrt(sigma_sq_2n_1)) - np.log2(val))

        idx = (Bk < 0.0)
        Bk[idx] = 0

        # From Hogenauer, b_max is the msb (counting from 0) of the filter
        # before truncation.
        # self.b_max = np.ceil(self.N*np.log2(self.r_max*self.m_max) +
        #                         self.input_width-1).astype(np.int)
        self.Bk = Bk
        self.bk_floor = np.floor(Bk)
        self.bit_widths = (num_bits - self.bk_floor).astype(np.int)
        self.msb = msb

        return 0

    def gen_slicer_vars(self):
        """
            Function returns the Offset parameters by varying the decimation
            rate, R and the (if it is given) the differential delay vector
            var_m
        """
        # bit_width_list = []
        trunc_list = []
        bmax_list = []
        idx_list = []
        gain_list = []
        for jj in np.arange(self.m_min, self.m_max + 1):
            for ii in np.arange(1, self.r_max + 1):
                bmax_val = self.ret_bmax(ii, jj)
                trunc_val = self.ret_btrunc(bmax_val)
                bmax_list.append(bmax_val)
                trunc_list.append(trunc_val)
                gain_list.append(self.ret_m_gain(ii, jj))
                idx_list.append(ii + (jj - self.m_min) * (self.r_max + 1))

        gain_list = np.array(gain_list)
        # remove negative values in truncation list.
        idx = np.argwhere(np.array(trunc_list) < 0).flatten()
        for ii in idx:
            trunc_list[ii] = 0

        slice_gain = 2.**np.array(trunc_list)
        corr_list = 1. / gain_list
        for (ii, val) in enumerate(trunc_list):
            if val != 0:
                corr_list[ii] = slice_gain[ii] / gain_list[ii]
        # inserting correction value for beginning of table.
        for ii in range(np.min(idx_list)):
            corr_list = np.insert(corr_list, 0, corr_list[0])
            gain_list = np.insert(gain_list, 0, gain_list[0])
            trunc_list = np.insert(trunc_list, 0, 0)
            idx_val = np.min(idx_list) - 1 - ii
            idx_list = np.insert(idx_list, 0, idx_val)
            bmax_list = np.insert(bmax_list, 0, bmax_list[0])
            # bit_width_list = np.insert(bit_width_list, 0, bit_width_list[0])

        return (bmax_list, trunc_list, gain_list, idx_list, corr_list)

    def gen_tables(self, qvec_correction=None):

        (bmax_list, trunc_list, gain_list, idx_list, _) = self.gen_slicer_vars()
        if qvec_correction is None:
            qvec_correction = self.qvec_out

        int_bits_in = self.qvec_in[0] - self.qvec_in[1]
        int_bits_out = self.qvec_out[0] - self.qvec_out[1]
        gain_factor = 2.**(int_bits_out - int_bits_out)
        gain_list = np.array(gain_list)
        gain_list /= gain_factor

        # remove negative values in truncation list
        idx = np.argwhere(np.array(trunc_list) < 0).flatten()
        if (len(idx) != 0):
            trunc_list[idx] = 0
        slice_gain = 2.**np.array(trunc_list)
        corr_list = slice_gain / gain_list
        offset_bits = fp_utils.ret_num_bitsU(np.max(trunc_list))
        # factor of 2 to account for the slice
        # adjustment after the correction multiplier.
        # now create offset and gain tables.
        corr_gain_fi = fp_utils.ret_dec_fi(corr_list, qvec_correction, overflow='wrap', signed=0)
        qvec_offset = (offset_bits, 0)
        offset_fi = fp_utils.ret_dec_fi(trunc_list, qvec_offset, signed=0)

        return corr_gain_fi, offset_fi

    def gen_cic_comp(self, fc, num_taps, trans_bw=.25, weights=None):
        """
            Function returns the PSD of the designed CIC filter.

            =======
            Returns
            =======

                * out (tuple)
                    Returns a tuple containing a frequency and PSD vector.

        """

        freq_vector, resp = self.ret_psd()

        idx = np.squeeze(np.argwhere(freq_vector >= 0.))

        freq_vector = freq_vector[idx]
        resp = resp[idx]

        self.b_comp = pb_comp(resp, num_taps, freq_vector, comp_freq=fc,
                              trans_bw=trans_bw, weights=weights)

        # remove DC gain
        self.b_comp = self.b_comp / np.sum(self.b_comp)

        return self.b_comp

    def ret_comp_psd(self, freq_vector=None):
        """
            Generates frequency response of designed compensation filter.
        """
        if self.b_comp is None:
            str_val = "Need to generate CIC compensation filter"
            assert (self.b_comp is not None), str_val
        else:
            return ret_fil_freq_resp(self.b_comp, freq_vector, rot_freq=True)

    def plot_comp_psd(self, freq_vector=None, title=None, y_min=None,
                      savefig=False, half_pwr_pts=False,
                      plot_on=True):
        """
            Helper function plots frequency response.
        """
        (wvec, resp) = self.ret_comp_psd(freq_vector=freq_vector)
        plot_spec(wvec, resp, y_min=y_min, title=title, savefig=savefig, half_pwr_pts=half_pwr_pts, plot_on=plot_on)

    def gen_fixed_cic_comp(self, fc, num_taps, trans_bw=.24, weights=None):
        b_comp = self.gen_cic_comp(fc, num_taps, trans_bw, weights)
        # convert to fixed point

        in_width = self.qvec_in[0]
        out_width = self.qvec_out[0]

        (b_comp_fi, fil_params) = max_filter_output(b_comp,
                                                    self.qvec_coef,
                                                    input_width=in_width,
                                                    output_width=out_width)

        return (b_comp_fi, fil_params)

    def ret_psd(self, freq_vector=None, M=None, N=None):
        """
            Function returns the PSD of the designed CIC filter.

            ==========
            Parameters
            ==========
                * freq_vector : optional frequency vector.  Normalized
                            Discrete frequency units assumed.


            =======
            Returns
            =======

                * out (tuple)
                    Returns a tuple containing a frequency and PSD vector.

        """
        if M is None:
            M = self.m_max

        if N is None:
            N = self.N

        # small signal approximation of peak.
        # peak = (self.M * self.r_max)**2.
        step = 2. / self.fft_size
        if freq_vector is None:
            # this vector is normalized frequency.
            f = np.arange(-1., 1., step)
        else:
            f = freq_vector

        num = sp.sin(.5 * np.pi * M * f)
        den = sp.sin(.5 * np.pi * f / self.r_max)
        idx0 = (np.abs(den) < np.finfo(np.float).tiny)
        # np.argmin(np.abs(den))
        den[idx0] = np.finfo(np.float).tiny
        resp = (num / den)**(2. * N)
        resp[idx0] = np.max(resp)

        resp /= np.max(resp)  # normalize output.
        # This is the power response so only multiply by factor of 10.
        resp = 10. * np.log10(resp)
        return (f, resp)

    def plot_psd(self, title=None, y_min=None, freq_vector=None,
                 M=None, N=None, savefig=False,
                 plot_on=True, half_pwr_pts=False):
        """
            Helper function, plot PSD of CIC filter
        """
        f, resp = self.ret_psd(freq_vector, M=M, N=N)
        plot_spec(f, resp, title=title, y_min=y_min, savefig=True, plot_on=plot_on, half_pwr_pts=half_pwr_pts)


def remez_ord(pbr, sba, trans_bw):
    """
        Returns the estimated number of taps required for the Remez
        algorithm generate filter given user specifications

        ==========
        Parameters
        ==========

        pbr : float
            Passband ripple of the desired filter given in dB

        sba : float
            Stopband ripple of the desired filter given in dB

        trans_bw : float
            Transition BW given normalized discrete
            frequency i.e. :math:`\pi` rad/sec

        =======
        Returns
        =======

        out : int
            Returns the approximate order the desired filter.

    """
    #    c1 = (.0729*np.log(pbr))**2 + .07114*np.log(pbr) - .4761
    #    c2 = (.0518*np.log(pbr))**2 + .59410*np.log(pbr) - .4278
    #    c3 = 11.01217 + .541244*(np.log(pbr) - np.log(sba))
    #
    #    K  = c1*np.log(sba) + c2 + c3*trans_bw**2

#    c1 = (.0729 * pbr)**2 + .07114 * pbr - .4761
#    c2 = (.0518 * pbr)**2 + .59410 * pbr - .4278
#    c3 = 11.01217 + .541244 * (pbr - sba)
#
#    K = c1 * sba + c2 + c3 * trans_bw**2
#
#    N = np.int(np.ceil(trans_bw**-1 * K))

    N = int(np.ceil(np.abs(sba) / (22. * trans_bw)))

    return N


class LPFilter(object):
    """
        Class used to generate Single Band FIR filter using either the Remez
        algorithm or exponential filters.

        Calculate the filter-coefficients for the finite impulse response
        (FIR) filter whose transfer function minimizes the maximum error
        between the desired gain and the realized gain in the specified
        frequency bands using the Remez exchange algorithm.

        ==========
        Parameters
        ==========

        (Default values are given in parentheses)

        fc  : float (.25)
            Cutoff frequency in normalized discrete frequency (pi rad/sample)
        num_taps : int (default is determined by remez_ord method)
                    The desired number of taps in the filter. The number of taps is
                    the number of terms in the filter, or the filter order plus one.
        P : int (1)
            Upsampling rate of polyphase implementation.
        M : int (1)
            Downsampling rate of polyphase implementation
        hilbert : bool (False)
            Transforms LPF into a hilbert transformer
        half_band : bool (False)
            Indicator that tells the class to generate a Half-Band filter.
        trans_bw : float (.1)
            Transition bandwidth of generated filter.
        quick_gen : bool (True)
            If true then exponential filters are used instead of Remez.
        fc_atten : float (-3.0)
            Cutoff frequency attenuation given in dB.
        K : float (9.396)
            K parameter for exponential filter design. Higher K results on
            smaller transition bandwidth but at the expense of less stopband
            attenuation.
        pbr : float (.1)
            passband ripple given in dB
        sba : float (-70.)
            Stopband ribble given in dB
        qvec_coef : tuple (25,24)
            Quantization vector for fixed-point coefficients.
                25 total bits, 24 fractional bits
        qvec : tuple (16,15)
            Quantization vector for fixed-point representation of input.
        qvec_out : tuple ()
            Desired Quantization vector for the output of the filter.

        stop_freq : None (float : (0, 1) )
            Desired stop frequency of low-pass filter. 0 < step_freq < 1.

        =======
        Returns
        =======
        out : object2 lpfilter object

    """
    def __init__(self, M=1, P=1, fc=.25, trans_bw=.1, pbr=.1, num_taps=None, sba=-70., freqz_pts=5000, hilbert=False,
                 half_band=False, quick_gen=False, even_filter=False, num_iters=32, num_iters_min=1, hp_point=None,
                 stop_freq=None, K=4., K_step=.1, fc_atten=None, weights=None,
                 qvec_coef=(25, 24), qvec=(16, 15), qvec_out=None, flip_hilbert=False):

        three_db = 10 * np.log10(.5)
        self.trans_bw = trans_bw
        self.M = M
        self.P = P
        self.freqz_pts = freqz_pts if freqz_pts < int(50E6) else int(50E6)
        self.hilbert = hilbert
        self.half_band = half_band
        self.quick_gen = quick_gen
        self.even_filter = even_filter
        self.num_iters = num_iters
        self.num_iters_min = num_iters_min

        self.paths = int(self.P if (self.P > self.M) else np.floor(self.M))
        self.fc = fc
        self.corner1 = self.fc
        self.stop_freq = stop_freq

        self.hp_point = hp_point if hp_point is not None else self.fc
        if self.stop_freq is not None:
            self.corner2 = self.stop_freq
            self.corner1 = self.fc - (self.corner2 - self.fc) / 4.
            self.hp_point = self.fc
        else:
            # user half voltage point.
            # This generally gives you a point with 1/2 voltage or -6 dB power.
            self.corner1 = self.hp_point - self.trans_bw / 4.
            self.corner2 = self.hp_point + self.trans_bw * 3. / 4.
        if self.quick_gen:
            self.corner1 = self.hp_point

        self.corner_step = .05 * self.hp_point
        self.fc_atten = fc_atten if fc_atten is not None else three_db
        # root-raised error function K and MTerm parameters
        self.K = K
        if K_step is None:
            K_step = .1
        self.K_step = K_step
        self.offset = .5
        self.MTerm = np.round(1. / self.hp_point)

        assert (self.corner2 < np.pi), ('Invalid passband to stopband edge transition must occur below pi rads/sample')

        self.pbr = pbr
        self.sba = sba
        self.num_taps = num_taps if num_taps is not None else remez_ord(self.pbr, self.sba, self.trans_bw)
        self.pbr = 10.**(self.pbr / 20.) - 1.
        self.sba = 10.**(self.sba / 20.)

        # quantization vector of filter itself.
        self.qvec_coef = qvec_coef
        # quantization vector of input to filter
        self.qvec = qvec
        # half power point.
        self.qvec_out = self.qvec if qvec_out is None else qvec_out

        self.flip_hilbert = flip_hilbert

        self.h_log = None
        # for polyphase implementations -- pad n so that if gives the correct
        # number of taps for the number of phases.
        self.fc = self.corner1
        if (self.hilbert is True or self.half_band is True) and self.P == 1 and self.M == 1:
            # n must be even
            self.num_taps = self.num_taps + (self.num_taps % 2)
            self.fc = 1. - self.trans_bw
            self.corner1 = self.fc
            self.corner2 = 1.

        self.num_taps += (self.num_taps % self.paths)

        if weights is not None:
            self.weights = weights
        else:
            weights = (1. / self.pbr, 1. / self.sba)
            weights = weights / np.min(weights)
            self.weights = weights

        self.gen_filter()

    def ret_fil(self, fil_type='std'):
        """
            Returns the filter impulse response associated with fil_type
            given in the following forms:

            ==========
            Parameters
            ==========
            **fil_type** : 4 filter types:

            * STD       : 1-d floating point filter
            * STD_FP    : 1-d fixed point filter (integers)
            * POLY      : n-d floating point polyphase implementation
            * POLY_FP   : n-d fixed point polyphase implementation (integers)

            =======
            Returns
            =======

            out : ndarray
                Array of values representing the correct filter impulse
                response.

        """
        ret_type = {'std': self.b, 'std_fp': self.b_q,
                    'poly': self.poly_fil, 'poly_fp': self.poly_fil_q}
        return ret_type[str.lower(fil_type)]
        # generates High pass filter equivalent

    def ret_hp_fil(self, fil_type='std'):
        """
            Generates High pass equivalent filter and returns the filter
            impulse response associated with fil_type given in the following
            forms:

            ==========
            Parameters
            ==========
            **fil_type** : 4 filter types:

            * STD       : 1-d floating point filter
            * STD_FP    : 1-d fixed point filter (integers)
            * POLY      : n-d floating point polyphase implementation
            * POLY_FP   : n-d fixed point polyphase implementation (integers)

            =======
            Returns
            =======

            out : ndarray
                Array of values representing the correct filter impulse
                response.
        """
        if (str.lower(fil_type) == 'std'):
            temp = self.b
            temp[1::2] = -temp[1::2]
            return temp
        elif (str.lower(fil_type) == 'std_fp'):
            temp = self.b_q
            temp[1::2] = -temp[1::2]
            return temp
        elif (str.lower(fil_type) == 'poly'):
            temp = self.b
            temp[1::2] = -temp[1::2]
            return self.poly_partition(temp)
        elif (str.lower(fil_type) == 'poly_fp'):
            temp = self.b_q
            temp[1::2] = -temp[1::2]
            return self.poly_partition(temp)
        else:
            print('Undefined filter type')
            return None

    def ret_hil_fil(self):
        """
            Returns hilbert transform of low-pass filter
        """
        vec = range(len(self.b))
        vec = np.exp(1j * np.pi / 2. * vec)
        self.b = self.b * vec

    def plot_impulse(self, title=None):

        (fig, ax) = plt.subplots()
        ax.stem(self.b, '-.')
        if title is None:
            ax.set_title(r'\textsf{Impulse Response}')
        else:
            ax.set_title(title)

        ax.set_xlabel(r'\textsf{Tap Number}')
        ax.set_ylabel(r'\textsf{Magnitude}')
        # setp(tup_val.markerline, 'markerfacecolor', 'b')
        # setp(tup_val.baseline, 'color','r', 'linewidth', 2)
        fig.canvas.draw()

    def plot_poly_impulse(self, title=None):

        poly_phase = self.poly_partition(self.b)
        (fig, ax) = plt.subplots(len(poly_phase))
        for ii, phase in enumerate(poly_phase):
            ax[ii].stem(phase, '-.')
            if title is None:
                ax[ii].set_title(r'\textsf{Impulse Response}')
            else:
                ax[ii].set_title(title)

            ax[ii].set_xlabel(r'\textsf{Tap Number}')
            ax[ii].set_ylabel(r'\textsf{Magnitude}')
        # setp(tup_val.markerline, 'markerfacecolor', 'b')
        # setp(tup_val.baseline, 'color','r', 'linewidth', 2)
        fig.canvas.draw()

    def poly_partition(self, taps):
        """
            Returns a polyphase partition of the filter object
        """
        return np.reshape(taps, (self.paths, -1), order='F')

    def hilbert_filter(self, input_vec):
        """
            Apply hilbert filter to input vector.  This is assumed to be an odd
            non-polyphased filter implementation.
        """
        test_vec = np.array(input_vec).copy()
        if ((len(test_vec) % 2) != 0):
            test_vec = np.append(test_vec, 0.)

        test_vec_rsh = np.reshape(test_vec, (2, -1), order='F')

        H1z = self.b[0::2]

        pad = np.zeros((((self.num_taps - 1) / 2),))
        real_out = np.concatenate((pad, test_vec_rsh[0, :]))
        imag_out = signal.upfirdn(H1z, test_vec_rsh[1, :])
        short_len = np.min((len(real_out), len(imag_out)))

        return real_out[:short_len] + 1j * imag_out[:short_len]

    def fp_fil_repr(self, values):
        """
            Returns a fixed point representation of the filter based on
            the qvec_coef parameter supplied.

            =======
            Returns
            =======

            out : ndarray
                Array of fixed point values representing the given input
                ndarray.  Uses the object supplied qvec_coef for calculations.
        """
        return fp_fil_repr(values, self.qvec_coef)

    def plot_psd(self, title=None, y_min=None, freq_vector=None, fft_size=1024,
                 plot_on=True, savefig=False, pwr_pts=None):

        step = 2. / fft_size
        if freq_vector is None:
            # this vector is normalized frequency.
            freq_vector = np.arange(-1., 1., step)

        omega, h_log = self.ret_psd(self.b, freq_vector=freq_vector)
        plot_spec(omega, h_log, title=title, y_min=y_min, plot_on=plot_on, savefig=savefig, pwr_pts=pwr_pts)

        return 0
        # method returns freqz output of the filter

    def ret_psd(self, b=None, freq_vector=None, nbins=None):
        """
            Generate and return the frequency response of the filter.
            The user can supply a frequency vector.  See scipy.signal.freqz for
            the correct representation of the frequency vector.

            ==========
            Parameters
            ==========

            **freq_vector** : User supplied frequency vector for
                            sp.signal.freqz
                            to compute against (units are rad/sample).

            See Also
            --------

            scipy.signal.freqz

        """
        worN = 8192  # by default compute at 8192 frequencies
        taps = self.b
        if b is not None:
            taps = b
        if nbins is not None:
            worN = nbins

        if freq_vector is not None:
            whole = False
        else:
            whole = True

        if self.hilbert is True:
            idx = np.argmax(taps)
            taps = taps * 1j
            taps[idx] = 1.

        if freq_vector is not None:
            omega, h = sp.signal.freqz(taps, worN=freq_vector * np.pi)
        else:
            omega, h = sp.signal.freqz(taps, worN=worN, whole=whole)

        omega /= np.pi
        # omega /= np.pi  # put back into normalized units.
        h_log = 20. * np.log10(np.abs(h))
        h_log -= np.max(h_log)

        return (omega, h_log)

    def ret_b_fi(self, desired_msb=None):
        self.gen_fixed_filter(desired_msb)
        return self.b_q

    def gen_fixed_filter(self, desired_msb=None, coe_file=None):

        # quantize filters.
        fp_repr = self.fp_fil_repr(self.b)
        self.b_q = fp_repr.vec
        poly_fil_fi = self.fp_fil_repr(self.poly_fil)

        poly_fil_float = poly_fil_fi.vec * (2 ** -self.qvec_coef[1])

        # maximize filter output for best dynamic range
        (new_fi, msb, max_tuple) = max_filter_output(poly_fil_float, self.qvec_coef, P=self.P,
                                                     input_width=self.qvec[0],
                                                     output_width=self.qvec_out[0])

        (s_gain, delta_gain, path_gain, bit_gain, corr_gain, corr_msb, snr_gain) = max_tuple

        self.poly_fi = new_fi
        self.poly_q = self.poly_fi.vec
        if desired_msb is not None:
            if msb > desired_msb:
                diff = msb - desired_msb
                self.b_q = self.b_q >> diff
                msb = desired_msb
        self.trunc_bits = msb + 1 - self.qvec_out[0]

        # store away msb of filter.
        self.msb = msb
        self.bit_gain = msb - self.qvec[0] + 1

        # calculate absolute maximum bit width
        b_abs = np.abs(self.b_q)
        self.msb_max = int(np.ceil(np.log2(np.sum(b_abs)))) + self.qvec[0]

        if coe_file is not None:
            # write the contents to a coe file.
            fp_reprc = copy.deepcopy(fp_repr)
            fp_reprc.qvec = (fp_repr.qvec[0], 0)
            fp_reprc.vec = self.b_q
            if self.hilbert:
                idx_max = np.argmax(fp_reprc.vec)
                fp_reprc.vec[idx_max] = 0.
            # if hilbert transform -- replace center tap with 0.
            fp_utils.coe_write(fp_reprc, file_name=coe_file, filter_type=True)

        return self.b_q

    def comp_proc_gain(self):
        """
            Helper function.  Computes processing gain of filter.
        """

        self.PG = (np.sum(self.b)**2.) / np.sum(self.b**2.)
        return self.PG

    def comp_dc_gain(self, taps=None):
        """
            Computes DC gain of filter.
        """
        if (taps is None):
            taps = self.b
        return np.sum(taps)

    def comp_max_gain(self, taps=None):
        """
            Computes maximum possible gain of filter
        """
        if (taps is None):
            taps = self.b
        return np.sum(np.abs(taps))

    def gen_omega(self, start_freq, stop_freq):
        if stop_freq > 1.:
            stop_freq = 1.
        stop_freq = stop_freq * np.pi
        start_freq = start_freq * np.pi
        freq_step = ((stop_freq - start_freq) / self.freqz_pts)
        freq_vector = np.arange(start_freq, stop_freq, freq_step)
        (omega, h_val) = sp.signal.freqz(self.b, worN=freq_vector)

        return (omega, h_val, freq_step)

    def gen_filter(self):
        """
            Generates the filter specified by the user supplied parameters.

            Uses an iterative filter design algorithm.  Can either use remez or
            exponential filters.  Generally based on the twiddle algorithm.nnn
        """
        iterations = 1
        direction = None
        K_step = self.K_step
        offset_step = .1
        freq_diff_old = None
        fstep = self.fc / 2.

        start_freq = (self.fc - fstep)
        stop_freq = (self.fc + 2 * self.trans_bw)
        freq_step = (stop_freq - start_freq) / self.freqz_pts
        bw_diff_old = None

        bw_cnt = 0
        bw_opt = True

        # sba_log = 20 * np.log10(self.sba)
        while 1:
            # vector of frequency band edges
            self.a = (1., 0.)
            self.f = (0, self.corner1, self.corner2, 1.)
            self.dev = (self.pbr, self.sba)
            if self.even_filter and (self.num_taps % 2 == 1):
                self.num_taps += 1

            if self.num_taps % self.paths:
                self.num_taps + self.paths - (self.num_taps % self.paths)

            # using remez
            if not self.quick_gen:
                self.b = signal.remez(self.num_taps, self.f, self.a, weight=self.weights, Hz=2)
                # check for convergence

                (h_val, omega, _) = self.gen_omega(start_freq, stop_freq)
                check = np.sum(np.isnan(self.b))
                assert (check == 0), ('remez did not converge -- may want to try quick option')
                break
            # using root raised erf function to generate filter prototype
            # less control but much faster option for very large filters.
            # Perfectly fine for standard low-pass filters. Link to code
            # effectively use twiddle algorithm to get the correct cut-off frequency
            # http://www.mathworks.com/matlabcentral/fileexchange/15813-near-perfect-reconstruction-polyphase-filterbank

            else:
                # quick option generates exponential filters.

                # MTerm = self.M // 2
                F = np.arange(self.num_taps)
                F = np.double(F) / len(F)

                x = self.K * (self.MTerm * F - self.offset)
                A = np.sqrt(0.5 * sp.special.erfc(x))

                N = len(A)

                idx = np.arange(N // 2)
                A[N - idx - 1] = np.conj(A[1 + idx])
                A[N // 2] = 0

                # scale using
                db_diff = self.fc_atten - 10 * np.log10(.5)
                exponent = 10 ** (-db_diff / 10.)

                A = A ** exponent

                self.b = np.fft.ifft(A)
                # the imaginary components should be tiny -- the error caused is negligible .
                self.b = (np.fft.fftshift(self.b)).real

                self.b /= np.sum(self.b)

            self.num_taps = len(self.b)
            # check frequency response for proper cut-off point.
            # check atten point
            temp = []
            loop_cnt = 0
            fstep = self.fc / 2.
            while len(temp) == 0:
                start_freq = (self.fc - fstep)
                stop_freq = self.fc + 2 * self.trans_bw  # (self.fc + 10 * fstep) * np.pi
                (omega, h_val, freq_step) = self.gen_omega(start_freq, stop_freq)
                f = interpolate.interp1d(omega, h_val)

                omega_new = np.arange(start_freq * np.pi, omega[-1], freq_step / 100.)
                h_val = f(omega_new)
                h_log = 20. * np.log10(np.abs(h_val))
                temp = np.where(h_log <= self.fc_atten)[0]
                if len(temp) == 0:
                    fstep += self.fc / 50.
                loop_cnt += 1

                if loop_cnt == 1000:
                    print("Poor Filter Design")
                    raise
                    break

            omega = omega_new / np.pi
            idx = temp[0]
            freq_val = omega[idx]
            freq_diff = self.hp_point - freq_val
            # plot_psd_helper(ax, omega, h_log, pwr_pts=self.fc_atten, label=r'\textsf{Proto Filter}', y_min=-200)
            # estimate transition bandwidth
            temp = np.where(h_log <= -80.)[0]
            if len(temp) == 0:
                trans_bw = omega[-1] - freq_val
            else:
                idx_bw = temp[0]
                trans_bw = omega[idx_bw] - freq_val
            bw_diff = self.trans_bw - trans_bw
            tup_val = (iterations, np.abs(freq_diff))

            # optimize for transition bandwidth first.  Then go back and correct corner frequency
            value = (tup_val[0], freq_val, tup_val[1], self.hp_point, trans_bw, bw_diff)
            debug_string = 'Filter has been iterated {} times, freq_val = {}, error = {}, hp_point = {}, trans_bw = {}, bw error = {}'.format(*value) #analysis:ignore
            # print(freq_diff, K_step, self.K)
            if iterations >= self.num_iters:
                if (self.num_iters > 1):
                    print(debug_string)
                break

            print_tup = (freq_diff, freq_val, self.K, self.offset, loop_cnt, bw_diff, trans_bw, bw_cnt)
            print("freq_diff = {}, fc = {}, K = {}, offset = {}, loop_cnt = {}, bw_diff = {}, trans_bw = {}, bw_cnt = {}".format(*print_tup))  #analysis:ignore

            if bw_opt and self.quick_gen:
                if trans_bw > self.trans_bw:
                    direction = 1
                else:
                    direction = -1
                if bw_diff_old is not None:
                    if np.sign(bw_diff) != np.sign(bw_diff_old):
                        self.corner_step *= .5
                        K_step *= .5
                        bw_cnt += 1

                self.K += K_step * direction
                self.K_step = K_step
                bw_diff_old = bw_diff

                if bw_cnt == 10:
                    bw_opt = False

                iterations += 1

            else:
                if np.abs(freq_diff) < .0001 * self.fc:
                    # self.freqz_pts**-1 and iterations >= self.num_iters_min:
                    print("filter has converged")
                    print(debug_string)
                    break

                if direction is None:
                    direction_old = 1  # np.sign(freq_diff)
                    direction = 1  # np.sign(freq_diff)

                print(freq_diff, freq_diff_old, freq_val, self.hp_point, self.K, self.offset, loop_cnt,
                      bw_diff, bw_diff_old, trans_bw, self.trans_bw)

                if iterations > 1:
                    freq_ch = np.abs(np.abs(freq_diff) - np.abs(freq_diff_old))
                    if (freq_ch < (freq_step / (1000 * np.pi))) and (iterations >= self.num_iters_min):
                        # (.000003 * self.fc):   # freq_incr):
                        print("frequency conversion has stalled")
                        print(debug_string)
                        break

                    if (freq_diff > 0. and freq_diff > freq_diff_old) or (freq_diff < 0 and freq_diff < freq_diff_old):
                        # :np.sign(freq_diff_old) != np.sign(freq_diff)):
                        direction = -1 * direction_old
                        self.corner_step *= .5
                        offset_step *= .5

                self.corner1 += direction * self.corner_step
                self.corner2 += direction * self.corner_step
                self.offset += offset_step * direction

                direction_old = direction
                freq_diff_old = freq_diff
                iterations += 1

        self.omega = omega
        self.h = np.abs(h_val)
        self.h_log = 20 * np.log10(np.abs(h_val))
        if self.hilbert or self.half_band:
            # upsample and alternate taps except for center tap.
            new_b = self.b
            vec = np.arange(1, len(new_b) + 1, dtype=np.float)
            if self.hilbert:
                vec = np.exp(1j * np.pi * vec)
            else:
                vec = np.ones((len(new_b),))
            if self.flip_hilbert:
                vec = -1. * vec
            mid_pt = len(vec) // 2
            vec = np.real(np.insert(vec, mid_pt, 1.))
            new_b = np.insert(new_b, mid_pt, 1.)
            b_hilbert = new_b * vec
            first_half = upsample(b_hilbert[:mid_pt], 2)
            sec_half = upsample(b_hilbert[mid_pt + 1:], 2)
            pad = np.atleast_1d(1.)  # np.array(1.).atleast_1d
            # mr.upsample(self.b,2)
            b_hilbert = np.concatenate((first_half[:-1], pad, sec_half[:-1]))

            self.b = b_hilbert

        # scale filter so that maximum values the maximum positive fixed point
        # value
        # reshape for polyphase implementation
        self.poly_fil = self.poly_partition(self.b)

        (s_gain, n_gain, snr_gain, path_gain, bit_gain) = comp_fil_gains(self.poly_fil, self.P)

        self.snr_gain = snr_gain

        return self.b
