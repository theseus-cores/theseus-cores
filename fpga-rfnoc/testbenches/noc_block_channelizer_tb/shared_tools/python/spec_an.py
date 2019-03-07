#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author: phil
"""
import numpy as np
import scipy.signal as sig

import time  #analysis:ignor
import matplotlib.pyplot as plt
import matplotlib as mpl  #analysis:ignore
from matplotlib import rc
from matplotlib.ticker import FormatStrFormatter
import pandas as pd

from matplotlib import rcParams
from cycler import cycler

from itertools import count

import copy

three_db = 10 * np.log10(.5)

rc('text', usetex=True)

df_str = r'\textsf{Discrete Frequency }' + r'$\pi\frac{rads}{sample}$'
amp_str = r'\textsf{Spectral Magnitude } \textsf{\textit{dB}}'

samp_str = r'\textsf{Sample Number}'
tamp_str = r'\textsf{Amplitude}'
psd_str = r'\textsf{PSD}'

plt.style.use('fivethirtyeight')

min_alpha = 120
dpi = 100

plot_height = 325
plot_width = 650

def ret_extents(xrange, yrange):
    """
        Extents helper function to be used with Holoviews/Datashader API
    """
    if xrange is None and yrange is None:
        extents = (None, None, None, None)
    elif yrange is None:
        extents = (xrange[0], None, xrange[1], None)
    elif xrange is None:
        extents = (None, yrange[0], None, yrange[1])
    else:
        extents = (xrange[0], yrange[0], xrange[1], yrange[1])

    return extents

def spec_label_helper(ax, title=None, xlabel=df_str, ylabel=amp_str, label_size=14, title_size=16):

    ax.set_xlabel(xlabel, fontsize=label_size)
    ax.set_ylabel(ylabel, fontsize=label_size)
    if title is not None:
        ax.set_title(title, fontsize=title_size)


def label_helper(ax, title=None, xlabel=samp_str, ylabel=tamp_str, label_size=14, title_size=16):

    ax.set_xlabel(xlabel, fontsize=label_size)
    ax.set_ylabel(ylabel, fontsize=label_size)
    if title is not None:
        ax.set_title(title, fontsize=title_size)


class NotAMovie(object):
    class Context(object):
        def __enter__(self):
            pass

        def __exit__(self, type, value, traceback):
            pass

    def saving(self, *args):
        return NotAMovie.Context()

    def grab_frame(self):
        pass


def gen_freq_vec(fft_size):
    st = 1. / fft_size * 2.
    w = np.arange(-1., 1, st)

    st = 2. / fft_size

    test = np.where(w > 0)
    cen_index = w[test[0][0]]

    half_size = len(w) - cen_index + 1
    ret_dict = {'cen_index': cen_index, 'w': w, 'half_size': half_size, 'step': st}

    return ret_dict


def conv_unit_circle(freqs):
    """
        Helper function takes normalized +/- discrete frequency
        and maps it to 0 -> 2*pi radians sample
    """
    freqs_copy = copy.copy(freqs)
    idx = (freqs_copy >= 0.)
    freqs_copy[idx] = freqs_copy[idx] * np.pi
    idx = (freqs_copy < 0.)
    freqs_copy[idx] = freqs_copy[idx] * np.pi + 2 * np.pi

    return freqs_copy


def win_sel(win_str, win_size):
    """
        Function returns a window vector based on window name.
        Note class can only use windows found in scipy.signal library.
    """
    if (win_str == 'blackmanharris'):
        win = sig.blackmanharris(win_size)
    elif (win_str == 'blackman'):
        win = sig.blackman(win_size)
    elif (win_str == 'bartlett'):
        win = sig.bartlett(win_size)
    elif (win_str == 'hamming'):
        win = sig.hamming(win_size)
    elif (win_str == 'hanning'):
        win = sig.hanning(win_size)
    elif (win_str == 'hann'):
        win = sig.hann(win_size)
    elif (win_str == 'barthann'):
        win = sig.barthann(win_size)
    elif (win_str == 'triang'):
        win = sig.triang(win_size)
    elif (win_str == 'rect'):
        win = np.ones(win_size)
    else:
        print('Invalid Window Defined')
        return -1
    return win


def find_pwr(resp, pwr_val=three_db):
    """
        Helper function returns the indices containing the half-pwr or -3 dB
        indices. The expected psd is the shape of a  typical lower pass filter,
        so the search will start with the peak and search outwards in both
        directions.
    """
    idx_max = np.argmax(resp)
    # find index moving right from idx_max
    trunc_right = resp[idx_max:]
    trunc_left = resp[:idx_max][::-1]

    right_idx = idx_max + (trunc_right <= pwr_val).nonzero()[0][0]
    temp = (trunc_left <= pwr_val).nonzero()[0]
    if len(temp) > 0:
        left_idx = idx_max - temp[0]
    else:
        left_idx = None

    return left_idx, right_idx

def find_freq(wvec, freq_val):
    """
        Helper function returns the nearest index to the frequency point (freq_val)
    """
    return min(range(len(wvec)), key=lambda i: abs(wvec[i]-freq_val))

def plot_psd_helper(ax, w_vec, amp, pwr_pts=None, freq_pts=None, label=None, y_min=None, y_max=None, x_offset=None,
                    title_size=16, label_size=14, title=None, prec=3):

    ax.plot(w_vec, amp, label=label, lw=.9)
    if x_offset is not None:
        ax.set_xlim(-x_offset, x_offset)
    else:
        ax.set_xlim(np.min(w_vec), np.max(w_vec))

    gen_box = False
    if (pwr_pts is not None) or (freq_pts is not None):
        gen_box = True
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

    final_text = ''
    if pwr_pts is not None:
        pwr_pts = np.atleast_1d(pwr_pts)
        for pwr_pt in pwr_pts:
            lidx, ridx = find_pwr(amp, pwr_pt)
            if lidx is not None:
                wleft = w_vec[lidx]
            wright = w_vec[ridx]
            ax.axvline(wright, color='g', linewidth=1)
            if lidx is not None:
                half = '{0:.{prec}f} dB points\n{1:.{prec}f} and {2:.{prec}f} '.format(pwr_pt, wleft, wright, prec=prec)
                text_str = half + r'$\pi \frac{rads}{sample}$'
                ax.axvline(wleft, color='g', linewidth=1)
            else:
                text_str = '{0:.{prec}f} dB point\n{1:.{prec}f} '.format(pwr_pt, wright, prec=prec)
                text_str = text_str + r'$\pi \frac{rads}{sample}$'

        final_text += text_str

    if freq_pts is not None:
        freq_pts = np.atleast_1d(freq_pts)
        for freq_pt in freq_pts:
            idx = find_freq(w_vec, freq_pt)
            amp_val = amp[idx]
            freq_val = w_vec[idx]
            ax.axvline(freq_val, color='r', linewidth=1)
            text_str = '\n{0:.{prec}f} dB @ {1:.{prec}f}'.format(amp_val, freq_val, prec=prec)
            text_str = text_str + r'$\pi \frac{rads}{sample}$'
            final_text += text_str

    if gen_box:
        ax.text(0.05, 0.95, final_text, transform=ax.transAxes, fontsize=14, verticalalignment='top', bbox=props)

    if y_max is None:
        y_max = 3. + amp.max()

    if y_min is None:
        y_min = amp.min()

    ax.set_ylim(y_min, y_max)
    ax.locator_params(nbins=10)
    spec_label_helper(ax, title=title, title_size=title_size, label_size=label_size)


def gen_psd(in_vec, return_onesided=False, fft_size=1024, noverlap=None, nperseg=None, normalize=False,
            find_offset=False, window='blackmanharris'):

    if len(in_vec) < fft_size:
        fft_size = len(in_vec)
    if noverlap is None:
        noverlap = int(.75 * fft_size)

    if nperseg is None:
        nperseg = fft_size

    omega, resp = sig.welch(in_vec, fs=2.0, window=window, nperseg=nperseg, noverlap=noverlap, nfft=fft_size,
                            return_onesided=return_onesided, scaling='density', detrend=False)

    resp = 10. * np.log10(resp + 1E-24)

    if return_onesided is False:
        omega = np.fft.fftshift(omega)
        resp = np.fft.fftshift(resp)

    if normalize:
        max_val = np.max(resp)
        resp -= max_val

    if find_offset is True:
        if np.size(in_vec) > fft_size:
            # pdb.set_trace()
            i_val = np.real(in_vec)
            q_val = np.imag(in_vec)
            first_i = np.argwhere(i_val != 0)
            first_q = np.argwhere(q_val != 0)
            if (not np.size(first_i)) & (not np.size(first_q)):
                offset = 0
            elif not np.size(first_i):
                offset = np.min(first_q)
            elif not np.size(first_q):
                offset = np.min(first_i)
            else:
                offset = np.min((np.min(first_i), np.min(first_q)))

            in_vec = in_vec[offset:]

    return omega, resp


def plot_spec_sig(signal, fft_size=1024, title=None, y_min=None, y_max=None, w_time=False, markersize=None, plot_on=True,
                  savefig=False, pwr_pts=None, legend_str=None, normalize=True, return_onesided=False, window='blackmanharris',
                  path='./'):

    """
        Helper function for quickly plotting spectrum from signal.  Uses
        most commonly used defaults.
    """
    signals = np.atleast_2d(signal)

    if len(signal) < fft_size:
        fft_size = len(signal)
    noverlap = int(.75 * fft_size)
    nperseg = fft_size

    wvec = []
    resp = []
    for signal in signals:
        fft_size_s = fft_size
        if fft_size > len(signal):
            fft_size_s = len(signal)
        temp_w, temp_resp = sig.welch(signal, fs=2.0, window=window, nperseg=nperseg, noverlap=noverlap,
                                      nfft=fft_size_s, return_onesided=return_onesided, scaling='density', detrend=False)

        temp_resp = 10. * np.log10(temp_resp + 1E-24)

        temp_w = np.fft.fftshift(temp_w)
        temp_resp = np.fft.fftshift(temp_resp)
        if normalize:
            max_val = np.max(temp_resp)
            temp_resp -= max_val
        wvec.append(temp_w)
        resp.append(temp_resp)

    plot_spec(wvec, resp, title=title, y_min=y_min, y_max=y_max, markersize=markersize, plot_on=plot_on, savefig=savefig,
              pwr_pts=pwr_pts, legend_str=legend_str, w_time=w_time, time_sig=signals, path=path)


def attach_legend(ax):
    legend = ax.legend(loc='upper right', fancybox=True, framealpha=0.75, fontsize=16)
    frame = legend.get_frame()
    frame.set_facecolor('wheat')


def plot_time_helper(time_sig, title=None, legend_str=None, savefig=False, plot_on=False, markersize=None):
    """
        Helper function for quickly plotting real or complex sample streams. Uses
        most commonly used defaults.
    """
    fig = plt.figure()
    fig.set_size_inches(8., 6.)
    fig.set_dpi(dpi)
    fig.subplots_adjust(bottom=.15, left=.1)
    fig.subplots_adjust(hspace=.5, wspace=.4)
    fig.set_tight_layout(False)

    orig_marker_size = rcParams.get('lines.markersize')
    if markersize is not None:
        rcParams.update({'lines.markersize': markersize})
    ax = plt.subplot(111)
    if np.iscomplexobj(time_sig):
        ax1 = plt.subplot(121)
        ax2 = plt.subplot(122, sharex=ax1)
        fig.add_axes(ax1)
        fig.add_axes(ax2)
    else:
        ax1 = plt.subplot(111)
        fig.add_axes(ax1)

    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')

    real_sig = [np.real(signal) for signal in time_sig]
    legend_temp = copy.copy(legend_str)
    plot_time_sig(ax1, real_sig, legend_temp)
    if np.iscomplexobj(time_sig) is True:
        comp_sig = [np.imag(signal) for signal in time_sig]
        plot_time_sig(ax2, comp_sig, legend_temp, r'\textsf{Imag}')

    if legend_str is not None:
        # generate legend string.
        attach_legend(ax1)

    if title is not None:
        fig.canvas.set_window_title(title)
        title_new = r'\textsf{{{}}}'.format(title)
        ax.set_title(title_new, fontsize=17)

    if savefig is True and title is not None:
        # convert spaces to underscores
        file_name = copy.copy(title)
        file_name = ''.join(e if e.isalnum() else '_' for e in file_name)
        file_name += ".png"
        for ii in range(3):
            file_name = file_name.replace("__", "_")
        fig.savefig(file_name)

    if plot_on is True:
        fig.canvas.draw()
        plt.show()

    rcParams.update({'lines.markersize': orig_marker_size})

def plot_time_sig(ax, time_sig, legend, title=r'\textsf{Real}', miny=None, maxy=None):

    time_sig = np.atleast_2d(time_sig)
    if legend is None:
        legend_list = [None] * len(time_sig)
    else:
        legend_list = copy.copy(legend)

    if miny is None:
        miny = -2 * np.abs(np.max(time_sig))

    if maxy is None:
        maxy = 2 * np.abs(np.max(time_sig))

    lines = []
    for signal, label in zip(time_sig, legend_list):
        lines.append(ax.plot(signal, label=label, lw=.9))
        ax.ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
        ax.ticklabel_format(axis='y', style='sci', scilimits=(-3,3))
        ax.set_ylim(miny, maxy)
        ax.locator_params(nbins=10)

    if legend is not None:
        attach_legend(ax)
    label_helper(ax, title=title)

    return ax, lines


def waterfall_spec(in_vec, fft_size=1024, num_avgs=4, one_side=False, normalize=False, window='blackmanharris', noverlap=None):
        """
            Generates a 2-D PSD estimate.  Used to populate a waterfall plot.
            Computes complete waterfall for input vector.
        """
        input_size = len(in_vec)
        chunk_size = fft_size * num_avgs
        while chunk_size > input_size:
            num_avgs -= 1
            chunk_size = fft_size * num_avgs

        new_len = input_size - np.remainder(input_size, chunk_size)
        new_vec = in_vec[0:new_len]
        num_chunks = np.floor(len(new_vec) / chunk_size).astype(np.int)
        if (num_chunks < 1):
            num_chunks = 1
        if one_side:
            temp = gen_freq_vec(fft_size)
            fft_size = temp['half_size']

        resp_water = np.zeros((num_chunks, fft_size))
        w = np.zeros((num_chunks, fft_size))
        ret_vec = np.reshape(new_vec, (-1, chunk_size), order='C')

        for ii in range(num_chunks):
            (w[ii, :], resp_water[ii, :]) = gen_psd(ret_vec[ii, :], fft_size=fft_size, return_onesided=one_side,
                                                    find_offset=False, normalize=normalize, noverlap=noverlap, window=window)

        return (w, resp_water)


def plot_waterfall(in_vec, plot_time=False, title=None, plot_psd=False, plot_png=True,
                   fft_size=1024, num_avgs=4):
        """
            Helper function plots Waterfall spectral plot as a 2-D map.
        """
        # sns.set_palette('bright')
        w_vec, resp_water = waterfall_spec(in_vec, fft_size, num_avgs)

        plt.rc('text', usetex=True)
        plt.rc('font', family='serif')
        rcParams.update({'figure.autolayout': True})

        num_plots = int(plot_time) + int(plot_psd) + 1
        gs = plt.GridSpec(num_plots, 2, wspace=.4, hspace=.4)
        fig1 = plt.figure()   # figsize=(12, 10))
        fig1.set_size_inches(8., 6.)
        fig1.set_dpi(dpi)
        fig1.subplots_adjust(left=.12, bottom=.1)
        fig1.set_tight_layout(False)

        plot_cnt = 0
        if plot_time:
            axI = fig1.add_subplot(gs[plot_cnt, 0])
            axQ = fig1.add_subplot(gs[plot_cnt, 1], sharex=axI)
            plot_cnt += 1
        if plot_psd:
            ax_psd = fig1.add_subplot(gs[plot_cnt, :])
            plot_cnt += 1

        ax_water = fig1.add_subplot(gs[plot_cnt, :])

        label_font = 14
        title_font = 16

        if title is not None:
            fig1.canvas.set_window_title(title)

        if plot_time:
            axI.plot(np.real(in_vec), 'b')
            axQ.plot(np.imag(in_vec), 'r')
            axI.ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
            axQ.ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
            axI.set_ylim(-2. * np.abs(np.max(in_vec)), 2. * np.abs(np.max(in_vec)))
            axQ.set_ylim(-2. * np.abs(np.max(in_vec)), 2. * np.abs(np.max(in_vec)))
            # xdata = np.add(range(hist_len*chunk_size),-hist_len*chunk_size)
            # ax0.set_xlim(xdata[0],xdata[-1])
            axI.locator_params(nbins=10)
            axQ.locator_params(nbins=10)
            lat_str = r'\textsf{Sample Number}'
            axI.set_xlabel(lat_str, fontsize=14)
            axQ.set_xlabel(lat_str, fontsize=14)
            lat_str = r'\textsf{Linear Magnitude}'
            axI.set_ylabel(lat_str, fontsize=14)
            axQ.set_ylabel(lat_str, fontsize=14)
            lat_str = r'\textsf{Time Domain Signal}'
            axI.set_title(lat_str, fontsize=16)
            axQ.set_title(lat_str, fontsize=16)

        if plot_psd:
            (wvec, X2) = gen_psd(in_vec, find_offset=False)  # , scale_psd=False)
            psd_min = np.min(X2) - 10
            psd_max = np.max(X2) + 10
            ax_psd.plot(wvec, X2)
            ax_psd.locator_params(nbins=10)
            lat_str = r'\textsf{Discrete Frequency }' + r'$\pi' + r'\frac{rads}{sample}$'
            ax_psd.set_xlabel(lat_str, fontsize=label_font)
            lat_str = r'\textsf{Spectral Magnitude }' + r'$\textit{dB}$'
            ax_psd.set_ylabel(lat_str, fontsize=label_font)
            ax_psd.set_title(psd_str, fontsize=title_font)
            ax_psd.set_ylim(psd_min, psd_max)

        upper_val = len(resp_water) - 1
        if upper_val == 0:
            upper_val = 1
        extent_val = [-1, 1, 0, upper_val]
        y_int = range(upper_val + 1)
        if len(y_int) > 15:
            dec_rate = len(y_int) // 15
            y_int = y_int[::dec_rate]
        im = ax_water.imshow(resp_water, origin='lower', interpolation='nearest', aspect='auto',
                             extent=extent_val, cmap=plt.get_cmap('plasma'))
        ax_water.locator_params(nbins=10)
        ax_water.yaxis.set_ticks(y_int)
        ax_water.ticklabel_format(axis='y', style='sci', scilimits=(-2,2))
        lat_str = r'\textsf{Discrete Frequency }' + r'$\pi' + r'\frac{rads}{sample}$'
        ax_water.set_xlabel(lat_str, fontsize=14)
        lat_str = r'\textsf{Spectral Slice Number}'
        ax_water.set_ylabel(lat_str, fontsize=14)
        lat_str = r'\textsf{Waterfall Spectrum}'
        ax_water.set_title(lat_str, fontsize=16)
        ax_water.tick_params(axis='y', labelsize=9)
        # ax_water.tick.label.set_fontsize(9)
        # get postion of waterfall.
        box = ax_water.get_position()

        ax_water.set_position([box.x0, box.y0, box.width * .9, box.height])
        ax_color = plt.axes([box.x0 + box.width * .92, box.y0, 0.01, box.height])

        cb = plt.colorbar(im, cax=ax_color, orientation='vertical')
        cb.set_label(r'\textsf{dB}', fontsize=14)

        if plot_png:
            if title is None:
                fig1.savefig('waterfall.png', figsize=(12, 10))
            else:
                fig1.savefig(title + '.png', figsize=(12, 10))
        else:
            fig1.canvas.draw()
            plt.show()

        # sns.set_palette('dark')


def plot_spec(wvec, resp, title=None, y_min=None, y_max=None, w_time=False, time_sig=None, markersize=None,
              plot_on=True, savefig=False, pwr_pts=None, freq_pts=None, legend_str=None, path='./', prec=3):
    """
        Helper method that generates a pretty Spectral plot.
    """
    wvec = np.atleast_2d(wvec)
    resp = np.atleast_2d(resp)
    time_sig = np.atleast_2d(time_sig)
    legend_temp = copy.copy(legend_str)

    fig = plt.figure()
    fig.set_size_inches(8., 6.)
    fig.set_dpi(dpi)
    fig.subplots_adjust(bottom=.15, left=.1)
    fig.subplots_adjust(hspace=.5, wspace=.4)
    fig.set_tight_layout(False)
    # gs = plt.GridSpec(num_plots, 2, wspace=.4, hspace=.4)
    orig_marker_size = rcParams.get('lines.markersize')
    if markersize is not None:
        rcParams.update({'lines.markersize': markersize})

    rcParams.update({'figure.autolayout': True})
    # set figure size
    if w_time is False:
        ax = plt.subplot(111)
        fig.add_axes(ax)
    else:
        ax = plt.subplot(211)
        if np.iscomplexobj(time_sig):
            ax1 = plt.subplot(223)
            ax2 = plt.subplot(224, sharex=ax1)
            fig.add_axes(ax1)
            fig.add_axes(ax2)
        else:
            ax1 = plt.subplot(212)
            fig.add_axes(ax1)

    # to use latex make sure machine has installed texlive-full packages.
    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')

    if legend_temp is None:
        legend_temp = [None] * len(wvec)
    for ii, w, amp, label in zip(count(), wvec, resp, legend_temp):
        plot_psd_helper(ax, w, amp, pwr_pts=pwr_pts, freq_pts=freq_pts, label=label, y_min=y_min, y_max=y_max, prec=prec)

    total_plts = ii + 1
    legend_temp = legend_temp[total_plts:]

    if legend_str is not None:
        attach_legend(ax)

    if title is not None:
        #TODO: this causes the over-specification warnings!!
        # ax.set_title(r'{{{}}}'.format(title), fontsize=18)
        title_new = r'\textsf{{{}}}'.format(title)
        ax.set_title(title_new, fontsize=17)
    else:
        ax.set_title(psd_str, fontsize=17)

    total_plts = 0
    legend_temp = copy.copy(legend_str)
    if w_time is True:
        real_sig = [np.real(signal) for signal in time_sig]
        plot_time_sig(ax1, real_sig, legend_temp)
        if np.iscomplexobj(time_sig) is True:
            comp_sig = [np.imag(signal) for signal in time_sig]
            plot_time_sig(ax2, comp_sig, legend_temp, r'\textsf{Imag}')

        if legend_str is not None:
            # generate legend string.
            attach_legend(ax1)

    if title is not None:
        fig.canvas.set_window_title(title)

    if savefig is True and title is not None:
        # convert spaces to underscores
        file_name = copy.copy(title)
        file_name = ''.join(e if e.isalnum() else '_' for e in file_name)
        file_name += ".png"
        for ii in range(3):
            file_name = file_name.replace("__", "_")

        fig.savefig(path + file_name)
    if plot_on is True:
        fig.canvas.draw()
        plt.show()

    rcParams.update({'lines.markersize': orig_marker_size})

def test_run():

    from qpsk_waveform import QAM_Mod
    plt.close('all')

    snr = 40
    spb = 8

    sig_obj = QAM_Mod(frame_mod='qpsk', spb=spb, snr=snr)
    signal = sig_obj.gen_frames(5, frame_space_mean=100000, sig_bw=.5)[0]
    #
    plot_spec_sig(signal, normalize=True, y_min=-80, savefig=True, plot_on=False, title='test psd')
    plot_waterfall(signal, num_avgs=4)


if __name__ == "__main__":

    test_run()
