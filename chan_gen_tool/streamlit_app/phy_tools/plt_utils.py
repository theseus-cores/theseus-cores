#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author: phil
"""
import numpy as np
import scipy.signal as sig
import ipdb

import matplotlib.pyplot as plt
from matplotlib import rc
from matplotlib import rcParams
from matplotlib.ticker import MaxNLocator, FormatStrFormatter
import matplotlib.patches as patches
import copy
import sys
from collections.abc import Iterable
import dill as pickle
from pylatexenc.latex2text import LatexNodes2Text

from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    __version__ = today.strftime("%Y.%m.%d")

three_db = 10 * np.log10(.5)
six_db = 10 * np.log10(.25)

rc('text', usetex=False)

df_str = r'$\sf{Discrete\ Frequency\ }\pi\,\frac{rads}{sample}$'
amp_str = r'$\sf{Spectral\ Magnitude\ } \sf{\it{dB}}$'

samp_str = r'$\sf{Sample\ Number}$'
tamp_str = r'$\sf{Amplitude}$'
psd_str = r'$\sf{PSD}$'

plt.style.use('fivethirtyeight')

min_alpha = 70
dpi = 600
max_px = 1

plot_height = 360
plot_width = 750
win_list = ['triang', 'blackman', 'hamming', 'hann', 'bartlett', 'flattop', 'parzen', 'bohman', 'blackmanharris', 'nuttall', 'barthann']
num_list = [str(i) for i in range(1, 33)]

channel_dict = dict.fromkeys(['start_bin', 'end_bin', 'start_slice', 'end_slice'])

linestyle_dict = dict([
     ('solid', 'solid'),      # Same as (0, ()) or '-'
     ('dotted', 'dotted'),    # Same as (0, (1, 1)) or '.'
     ('dashed', 'dashed'),    # Same as '--'
     ('dashdot', 'dashdot'),
     ('loosely dotted',        (0, (1, 10))),
     ('dotted',                (0, (1, 1))),
     ('densely dotted',        (0, (1, 1))),

     ('loosely dashed',        (0, (5, 10))),
     ('dashed',                (0, (5, 5))),
     ('densely dashed',        (0, (5, 1))),

     ('loosely dashdotted',    (0, (3, 10, 1, 10))),
     ('dashdotted',            (0, (3, 5, 1, 5))),
     ('densely dashdotted',    (0, (3, 1, 1, 1))),

     ('dashdotdotted',         (0, (3, 5, 1, 5, 1, 5))),
     ('loosely dashdotdotted', (0, (3, 10, 1, 10, 1, 10))),
     ('densely dashdotdotted', (0, (3, 1, 1, 1, 1, 1)))])


def add_legend_item(ax, label):
    """
        Helper function adds patch to existing legend

        Args:

            legend : existing legend

            label : label that is to be appended to existing legend
    """

    # from matplotlib.patches import Patch
    # ipdb.set_trace()
    # ax = legend.axes

    # frame = ax.get_legend().get_frame()
    ipdb.set_trace()

    _, labels = ax.get_legend_handles_labels()
    # handles.append(lines_obj)
    labels.append(label)
    # leg = ax.get_legend()
    # leg.set_label(labels.append(label))

    ax.legend(labels)

    return ax

    # legend._legend_box = None
    # legend._init_legend_box(handles, labels)
    # legend._set_loc(legend._loc)
    # legend.set_title(legend.get_title().get_text())

def spec_label_helper(ax, title=None, xlabel=df_str, ylabel=amp_str, labelsize=14, titlesize=16):
    """
        Helper function for modifying and attaching x and y labels of spectral plots.
    """
    ax.set_xlabel(xlabel, fontsize=labelsize)
    ax.set_ylabel(ylabel, fontsize=labelsize)
    if title is not None:
        ax.set_title(title, fontsize=titlesize)
    else:
        ax.set_title(psd_str, fontsize=titlesize)


def label_helper(ax, title=None, xlabel=None, ylabel=None, labelsize=14, titlesize=16):
    """
        Helper function for modifying and attaching x and y labels.
    """
    if xlabel is None:
        xlabel = samp_str

    if ylabel is None:
        ylabel = tamp_str

    ax.set_xlabel(xlabel, fontsize=labelsize)
    ax.set_ylabel(ylabel, fontsize=labelsize)
    if title is not None:
        ax.set_title(title, fontsize=titlesize)
    else:
        ax.set_title(tamp_str, fontsize=titlesize)

def parse_title(title):
    """
        Uses pylatexenc package to convert any latex string to regular text with unicode values for symbols.
    """
    return LatexNodes2Text().latex_to_text(title)


def attach_legend(ax, fontsize=12):
    """
        Helper function for modifying and attaching legends to a plot.
    """
    legend = ax.legend(loc='upper right', fancybox=True, framealpha=0.75, fontsize=fontsize, frameon=True)
    frame = legend.get_frame()
    frame.set_facecolor('wheat')

def fig_wrap_up(fig, title=None, savefig=False, plot_on=False, pickle_fig=False, path=''):

    file_name = None
    if title is not None:
        # remove latex strings
        # search for open and close braces, {} and slice out string inside
        title = parse_title(title)
        #replace underscores with slash underscores
        title = title.replace('_', '\_')
        fig.canvas.set_window_title(title)

    if (savefig or pickle_fig) and title is not None:
        # convert spaces to underscores
        file_name = copy.copy(title)
        file_name = ''.join(e if e.isalnum() else '_' for e in file_name)
        # print("file_name = {}".format(file_name))
        file_name = path + file_name
        for _ in range(3):
            file_name = file_name.replace("__", "_")

    if savefig and title is not None:
        png_name = file_name + ".png"
        fig.savefig(png_name, dpi=dpi)

    if pickle_fig is True and title is not None:
        p_name = file_name + ".p"
        with open(p_name, 'wb') as fid:
            pickle.dump(fig, fid)

    if plot_on is True:
        fig.canvas.draw()

    return fig

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

def ret_omega(fft_size):
    """
        Helper function that generates the appropriate normalized discrete frequency $\pi rads / sec$
    """
    st = 2. / fft_size
    return np.arange(-1., 1, st), st

def gen_freq_vec(fft_size):
    """
        Helper function generates a frequency vector for plotting in normalized frequency units.
    """
    w, st = ret_omega(fft_size)

    test = np.where(w >= 0)
    cen_index = test[0][0]

    half_size = len(w) - cen_index
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
    overlap = 0
    if (win_str == 'blackmanharris'):
        win = sig.blackmanharris(win_size)
        overlap = .75
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
    elif (win_str == 'rect' or win_str == None):
        win = np.ones(win_size)
    else:
        print('Invalid Window Defined')
        return -1
    return win, overlap


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
        left_idx = (idx_max - 1) - temp[0]
    else:
        left_idx = None

    return left_idx, right_idx

def find_freq(wvec, freq_val):
    """
        Helper function returns the nearest index to the frequency point (freq_val)
    """
    return min(range(len(wvec)), key=lambda i: abs(wvec[i]-freq_val))

def plot_const_diag(const_sig, title=None, label=None, format_str=None, linestyle=None, linewidth=None,x_vec=None,
                    min_n_ticks=4, color=None, marker=None, savefig=False, plot_on=False, markersize=None, miny=None,
                    maxy=None, minx=None, maxx=None, xlabel=None, ylabel=None, labelsize=14, titlesize=16, alpha=1.,
                    ax=None, pickle_fig=False, path='./', dpi=200):

    """ 
        Function plots a constellation diagram.

    Args:

        const_sig (np.array):
            x, y signal representing the constellation symbols.  

        title (str):
            title string.

        label (list):
            list of legend strings to attach to plot.

        format_str (str):

    """
    fig = None
    if ax is None:
        fig = plt.figure()
        fig.set_size_inches(8., 6.)
        fig.set_dpi(dpi)
        gs = plt.GridSpec(1, 1, wspace=.25, hspace=.5)
        fig.subplots_adjust(bottom=.15, left=.1, hspace=.5, wspace=.4)
        fig.set_tight_layout(False)
        ax = fig.add_subplot(gs[0, 0])
        # ax = plt.subplot(111)

    if xlabel is None:
        xlabel = r'$\sf{Real}$'

    if ylabel is None:
        ylabel = r'$\sf{Imag}$'

    if title is None:
        title = r'$\sf{Constellation}$'

    if format_str is None:
        format_str = 'o'


    plot_time_sig(ax, np.imag(const_sig), label, x_vec=np.real(const_sig), miny=miny, maxy=maxy, minx=minx, maxx=maxx,
                  format_str=format_str, linestyle=linestyle, color=color, marker=marker, markersize=markersize,
                  linewidth=linewidth, min_n_ticks=min_n_ticks, xlabel=xlabel, ylabel=ylabel, labelsize=labelsize,
                  titlesize=titlesize, title=title, alpha=alpha)

    ax.set_ylim(-1.1 * np.abs(np.max(const_sig)), 1.1 * np.abs(np.max(const_sig)))
    ax.set_xlim(-1.1 * np.abs(np.max(const_sig)), 1.1 * np.abs(np.max(const_sig)))
    ax.set_aspect('equal')

    try:
        fig_wrap_up(fig, title, savefig, plot_on, pickle_fig, path)
    finally:
        return ax


def plot_psd_helper(signal, fft_size=1024, pwr_pts=None, freq_pts=None, label=None, plot_time=False, normalize=True,
                    format_str=None, color=None, marker=None, markersize=None, linewidth=None, linestyle=None, alpha=1.,
                    minx=None, maxx=None, miny=None, maxy=None, titlesize=12, labelsize=10, legendsize=10, title=None, min_n_ticks=4,
                    xlabel=None, ylabel=None, xprec=None, yprec=None, plt_size=(8., 6.), ax=None, ax1=None, ax2=None,
                    window='blackmanharris', noverlap=None, nperseg=None, return_onesided=False, savefig=False,
                    plot_on=False, path='./', dpi=dpi, time_sig=None, pickle_fig=False, ytime_max=None, ytime_min=None):

    tuple_flag = False
    fig = None
    if type(signal) is tuple:
        tuple_flag = True
        try:
            len(signal[0])
        except:
            signal = (np.array([signal[0]]), np.array([signal[1]]))
    else:
        try:
            len(signal[0])
        except:
            # if 1d array then just put in list
            signal = np.array([signal])

    time_flag = time_sig is not None
    if time_flag:
        try:
            len(time_sig[0])
        except:
            time_sig = np.array([time_sig])

    time_sig = signal if time_flag is False else time_sig

    # if signal is a tuple or a list of tuples, then wvec and resp has been calculated.  Just plot.
    if ax is None:
        fig = plt.figure()
        # fig.patch.set_alpha(fig_alpha)
        fig.set_size_inches(plt_size[0], plt_size[1])
        fig.set_dpi(dpi)
        num_plots = 1 + plot_time
        gs = plt.GridSpec(num_plots, 2, wspace=.25, hspace=.5)
        fig.subplots_adjust(left=.10, bottom=.15, top=.93, right=.96)
        fig.set_tight_layout(False)
        ax = fig.add_subplot(gs[0, :])
        # ax.set_facecolor('wheat')
        if plot_time:
            if np.iscomplexobj(time_sig):
                ax1 = fig.add_subplot(gs[1, 0])
                ax2 = fig.add_subplot(gs[1, 1], sharex=ax1)
            else:
                ax1 = fig.add_subplot(gs[1, :])

    wvec = []
    resp = []
    if tuple_flag:
        wvec = signal[0]
        resp = signal[1]
        # for omega, amp in zip(signal[0], signal[1]):
        #     wvec.append(omega)
        #     resp.append(amp)
    else:
        for sig in signal:
            # user has provided frequency vector and response vector
            omega, amp = gen_psd(sig, window=window, nperseg=nperseg, noverlap=noverlap, fft_size=fft_size,
                                 return_onesided=return_onesided, normalize=normalize)
            wvec.append(omega)
            resp.append(amp)

    plot_psd(ax, wvec, resp, format_str=format_str, title=title, label=label, min_n_ticks=min_n_ticks,
             alpha=alpha, miny=miny, maxy=maxy, minx=minx, maxx=maxx, color=color, legendsize=legendsize,
             markersize=markersize, marker=marker, linewidth=linewidth, linestyle=linestyle, pwr_pts=pwr_pts, ylabel=ylabel,
             freq_pts=freq_pts, xprec=xprec, yprec=yprec, labelsize=labelsize, titlesize=titlesize, xlabel=xlabel)

    if plot_time is True:
        real_sig = [np.real(sig) for sig in time_sig]
        plot_time_sig(ax1, real_sig, None, color=color, marker=marker, markersize=markersize,
                      linewidth=linewidth, linestyle=linestyle, format_str=format_str, labelsize=labelsize,
                      titlesize=titlesize, alpha=alpha, legendsize=legendsize, miny=ytime_min, maxy=ytime_max)
        if np.iscomplexobj(time_sig) is True:
            comp_sig = [np.imag(sig) for sig in time_sig]
            plot_time_sig(ax2, comp_sig, None, title=r'$\sf{Imag}$', color=color, marker=marker,
                          markersize=markersize, linewidth=linewidth, linestyle=linestyle, format_str=format_str,
                          labelsize=labelsize, titlesize=titlesize, alpha=alpha, legendsize=legendsize, miny=ytime_min,
                          maxy=ytime_max)

    try:
        fig = fig_wrap_up(fig, title, savefig, plot_on, pickle_fig, path)
    finally:
        if ax1 is not None and ax2 is None:
            return fig, ax, ax1
        elif ax1 is not None and ax2 is not None:
            return fig, ax, ax1, ax2
        else:
            return fig, ax


def gen_psd(in_vec, return_onesided=False, fft_size=1024, noverlap=None, nperseg=None, normalize=False,
            find_offset=False, window='blackmanharris'):

    """
        Function generates PSD based on Welch algorithm

    """

    if len(in_vec) < fft_size:
        # pad out input.
        pad = np.zeros((fft_size - len(in_vec),))
        in_vec = np.concatenate((in_vec, pad))
        # fft_size = len(in_vec)
    if noverlap is None:
        noverlap = int(.75 * fft_size)

    if nperseg is None:
        nperseg = fft_size

    omega, resp = sig.welch(in_vec, fs=2.0, window=window, nperseg=nperseg, noverlap=noverlap, nfft=fft_size,
                            return_onesided=return_onesided, scaling='density', detrend=False)

    if return_onesided:
        omega = omega[:-1]
        resp = resp[:-1]

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


def plot_time_helper(time_sig, title=None, label=None, format_str=None, linestyle=None, linewidth=None, x_vec=None, min_n_ticks=4,
                     color=None, marker=None, savefig=False, plot_on=False, markersize=None, miny=None, maxy=None, minx=None, maxx=None,
                     xlabel=None, ylabel=None, labelsize=14, legendsize=14, titlesize=16, alpha=None, ax1=None, ax2=None, xprec=None, yprec=None,
                     add_legend=True, dpi=dpi, plt_size=(8., 6.), path='./', pickle_fig=False):
    """
        Helper function for quickly plotting real or complex sample streams. Uses
        most commonly used defaults.

    Args:
        time_sig (nparray):
            1-D time domain signal.
        
        label (list / str):
            list of legend strings to attach to plot.

        format_str (list / str):
            list of format strings (
                'stem': produces stem plot
                None (for standard x, y plot), 
                else pass matplotlib format string to format markers and lines as desired.

        linestyle (list / str):
            standard matplotlib linestyle format modifier.
        
        linewidth (list / float):
            standard matplotlib linewidth modifier.

    """
    time_sig = np.atleast_2d(time_sig)
    fig = None
    if ax1 is None:
        fig = plt.figure()
        fig.set_size_inches(plt_size[0], plt_size[1])
        fig.set_dpi(dpi)
        fig.subplots_adjust(bottom=.15, left=.1)
        fig.subplots_adjust(hspace=.5, wspace=.4)
        fig.set_tight_layout(False)

        if np.iscomplexobj(time_sig):
            ax1 = plt.subplot(121)
            ax2 = plt.subplot(122, sharex=ax1)
            fig.add_axes(ax1)
            fig.add_axes(ax2)
        else:
            ax1 = plt.subplot(111)
            ax2 = None
            fig.add_axes(ax1)

        plt.rc('text', usetex=False)
        plt.rc('font', family='serif')

    if label is not None:
        label = [str(value).replace("_", "\_") for value in label]

    legend_temp = copy.copy(label)
    real_sig = []
    comp_sig = []
    for signal in time_sig:
        # check if boolean list
        if np.any(signal == False) or np.any(signal == True):
            real_sig.append(signal)
        else:
            # assume numeric list type.
            real_sig.append(np.real(signal))
            if np.iscomplexobj(time_sig) is True:
                comp_sig.append(np.imag(signal))

    plot_time_sig(ax1, real_sig, legend_temp, title=title, x_vec=x_vec, miny=miny, maxy=maxy, minx=minx, maxx=maxx,
                  format_str=format_str, linestyle=linestyle, color=color, marker=marker, markersize=markersize,
                  linewidth=linewidth, min_n_ticks=min_n_ticks, xlabel=xlabel, ylabel=ylabel, labelsize=labelsize,
                  titlesize=titlesize, alpha=alpha, xprec=xprec, yprec=yprec)
    if ax2 is not None:
        plot_time_sig(ax2, comp_sig, legend_temp, title=title, x_vec=x_vec, miny=miny, maxy=maxy, minx=minx,
                      maxx=maxx, format_str=format_str, linestyle=linestyle, color=color, marker=marker, markersize=markersize,
                      linewidth=linewidth, min_n_ticks=min_n_ticks, xlabel=xlabel, ylabel=ylabel, labelsize=labelsize,
                      titlesize=titlesize, alpha=alpha, xprec=xprec, yprec=yprec)

    if label is not None and add_legend is True:
        # generate legend string.
        attach_legend(ax1, fontsize=legendsize)

    try:
        fig_wrap_up(fig, title, savefig, plot_on, pickle_fig, path)
    finally:
        ret_tuple = (fig, ax1)
        if ax2 is not None:
            ret_tuple = ret_tuple + (ax2,)


    return ret_tuple


def plot_stem(ax, x, y, ms=None, label=None, lw=.3, title=None, xlabel=None, ylabel=None, labelsize=14, titlesize=16, legendsize=14,  color=None):
    # plot only nonzero values (stem can be slow.)
    # x = x_vec[np.where(signal != 0)[0]]
    stem = ax.stem(x, y, label=label, basefmt=' ', markerfmt='8', use_line_collection=True)

    label_helper(ax, title, xlabel, ylabel, labelsize, titlesize)
    stem.markerline.set_markerfacecolor(color)
    color = stem.markerline.get_color() if color is None else color
    stem.stemlines.set_color(color)
    if ms is not None:
        stem.markerline.set_markersize(ms)
    stem.stemlines.set_linewidth(lw)

    if label is not None:
        attach_legend(ax, fontsize=legendsize)

    return ax


def plot_macro(x_vec, signal, **kwargs):
    """
        Helper function that performs the preprocessing for ensuring mult-line plots are
        provided all the correct sized lists for all of the supported plot options.
    """
    try:
        len(signal[0])
    except:
        # if 1d array then just put in list
        signal = np.array([signal])

    if x_vec is not None:
        try:
            len(x_vec[0])
        except:
            x_vec = np.array([x_vec])

    label_list = [None] * len(signal) if kwargs['label'] is None else kwargs['label']
    format_list = [None] * len(signal) if kwargs['format_str'] is None else kwargs['format_str']
    color_list = [None] * len(signal) if kwargs['color'] is None else kwargs['color']
    marker_list = [None] * len(signal) if kwargs['marker'] is None else kwargs['marker']
    ms_list = [None] * len(signal) if kwargs['markersize'] is None else kwargs['markersize'] #np.atleast_1d(kwargs['markersize'])
    ls_list = [None] * len(signal) if kwargs['linestyle'] is None else kwargs['linestyle']  #np.atleast_1d(kwargs['linestyle'])
    lw_list = [1.] * len(signal) if kwargs['linewidth'] is None else kwargs['linewidth']  
    alpha_list = [1.] * len(signal) if kwargs['alpha'] is None else kwargs['alpha']

    xvec_list = [np.arange(len(signal[0])).tolist()] * len(signal) if x_vec is None else x_vec

    label_list = [label_list] if not isinstance(label_list, Iterable) else label_list
    format_list = [format_list] if not isinstance(format_list, Iterable) else format_list
    color_list = [color_list] if not isinstance(color_list, Iterable) else color_list
    marker_list = [marker_list] if not isinstance(marker_list, Iterable) else marker_list
    ms_list = [ms_list] if not isinstance(ms_list, Iterable) else ms_list
    ls_list = [ls_list] if not isinstance(ls_list, Iterable) else ls_list
    lw_list = [lw_list] if not isinstance(lw_list, Iterable) else lw_list
    alpha_list = [alpha_list] if not isinstance(alpha_list, Iterable) else alpha_list
    ret_value = zip(xvec_list, signal, label_list, format_list, color_list, marker_list, ms_list, ls_list, lw_list, alpha_list)

    return ret_value, x_vec, signal

def plt_ax(ax, zip_iter, xprec, yprec, min_n_ticks, minx, maxx, miny, maxy, ticksize=8):
    """
        Helper function to plot multiple datasets to plot axis.
    """
    lines = []
    for x_vec, signal, label, format_str, color, marker, ms, ls, lw, alpha in zip_iter:
        if format_str == 'stem':
            # plot only nonzero values (stem can be slow.)
            markerfmt = marker if marker is not None else '8'
            idx = (signal != 0).nonzero()
            y = signal[idx]
            x = np.array(x_vec)[idx]
            #np.where(signal != 0)[0]]
            stem = ax.stem(x, y, label=label, basefmt=' ', markerfmt=markerfmt, use_line_collection=True)
            color = stem.markerline.get_color() if color is None else color
            stem.stemlines.set_color(color)
            stem.markerline.set_color(color)
            if ms is not None:
                stem.markerline.set_markersize(ms)
            stem.stemlines.set_linewidth(lw)
            lines.append(stem)
        elif format_str is None:
            lines.append(ax.plot(x_vec, signal, ls=ls, color=color, marker=marker, ms=ms, lw=lw, label=label, alpha=alpha))
        else:
            lines.append(ax.plot(x_vec, signal, format_str, label=label, lw=lw, ms=ms, alpha=alpha))
        # ax.ticklabel_format(axis='x', style='plain')
    ax.locator_params(nbins=12, min_n_ticks=min_n_ticks)
    ax.tick_params(axis='x', labelsize=ticksize, labelrotation=45)
    if xprec is not None:
        ax.xaxis.set_major_formatter(FormatStrFormatter('%.{}f'.format(xprec)))
    else:
        ax.ticklabel_format(axis='x', style='sci', scilimits=(-3, 3))
    ax.tick_params(axis='y', labelsize=ticksize)
    if yprec is not None:
        ax.yaxis.set_major_formatter(FormatStrFormatter('%.{}f'.format(yprec)))
    else:
        ax.ticklabel_format(axis='y', style='sci', scilimits=(-3, 3))

    # ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(miny, maxy)
    ax.set_xlim(minx, maxx)
    ax.xaxis.get_offset_text().set_fontsize(10)
    ax.yaxis.get_offset_text().set_fontsize(10)

    return ax, lines

def plot_time_sig(ax, time_sig, label=None, title=r'$\sf{Real}$', x_vec=None, format_str=None, linestyle=None, color=None,
                  marker=None, markersize=None, linewidth=None, miny=None, maxy=None, minx=None, maxx=None, min_n_ticks=4,
                  xlabel=None, ylabel=None, labelsize=14, legendsize=14, ticksize=8, titlesize=16, alpha=None, xprec=None, yprec=None):


    tvalue = plot_macro(x_vec, time_sig, label=label, format_str=format_str, color=color, marker=marker,
                        markersize=markersize, linestyle=linestyle, linewidth=linewidth, alpha=alpha)

    zip_iter = tvalue[0]
    time_sig = tvalue[2][0]
    if miny is None:
        miny = np.min((-2 * np.abs(np.max(time_sig)), -2 * np.abs(np.min(time_sig))))

    if maxy is None:
        maxy = np.max((2 * np.abs(np.max(time_sig)), 2 * np.abs(np.min(time_sig))))

    maxy = 1 + miny if maxy == miny else maxy

    try:
        ax, lines = plt_ax(ax, zip_iter, xprec, yprec, min_n_ticks, minx, maxx, miny, maxy, ticksize)
    except:
        print("Unexpected error:", sys.exc_info()[0])

        print(ax, zip_iter, xprec, yprec, min_n_ticks, minx, maxx, miny, maxy, ticksize)
        return -1

    if label is not None:
        attach_legend(ax, fontsize=legendsize)
    label_helper(ax, title=title, labelsize=labelsize, xlabel=xlabel, ylabel=ylabel, titlesize=titlesize)

    return ax, lines


def waterfall_spec(in_vec, fft_size=1024, num_avgs=4, one_side=False, normalize=False, window='blackmanharris',
                   noverlap=None, rotate_spec=False):
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
    fft_size_orig = fft_size
    if (num_chunks < 1):
        num_chunks = 1

    ret_vec = np.reshape(new_vec, (-1, chunk_size), order='C')
    w_test, resp_water_test = gen_psd(ret_vec[0, :], fft_size=fft_size_orig, return_onesided=one_side, find_offset=False,
                                      normalize=normalize, noverlap=noverlap, window=window)

    w = np.zeros((num_chunks, len(w_test)))
    resp_water = np.zeros((num_chunks, len(w_test)))

    w[0, :] = w_test
    resp_water[0, :] = resp_water_test

    for ii in range(1, num_chunks):
        (w[ii, :], resp_water[ii, :]) = gen_psd(ret_vec[ii, :], fft_size=fft_size_orig, return_onesided=one_side,
                                                find_offset=False, normalize=normalize, noverlap=noverlap, window=window)

    if rotate_spec:
        resp_water = np.flipud(resp_water.T)

    return (w, resp_water)



def plot_waterfall(in_vec, plot_time=False, title=None, plot_psd=False, normalize=False, plt_size=(8., 6.),
                   fft_size=1024, num_avgs=4, rotate_spec=False, window='blackmanharris', channels=None, chan_colors=None,
                   savefig=False, plot_on=False, pickle_fig=False, path='./', psd_input=False, labelsize=14, one_side=False,
                   titlesize=18, ticksize=8, dpi=600, ytime_max=None, ytime_min=None, time_sig=None, psd_min=None, psd_max=None):
    """
        Helper function plots Waterfall spectral plot as a 2-D map.
    """

    from matplotlib import ticker

    min_size = fft_size * num_avgs * 2  # need minimum of 2 spectral slices.
    if min_size  > len(in_vec):
        # pad with zeros
        pad_len = min_size - len(in_vec)
        in_vec = np.concatenate((np.array(in_vec), np.array([1E-6 + 1j*1E-6]*pad_len)))

    if psd_input:
        num_blocks = len(in_vec) // fft_size
        resp_water = np.reshape(in_vec[:num_blocks * fft_size], (num_blocks, fft_size))
        w_vec = np.reshape(ret_omega(fft_size)[0].tolist() * num_blocks, (num_blocks, fft_size))
    else:
        w_vec, resp_water = waterfall_spec(in_vec, fft_size, num_avgs, window=window, one_side=one_side)

    if rotate_spec:
        resp_water = resp_water.T

    if time_sig is None:
        time_sig = in_vec
    plt.rc('text', usetex=False)
    plt.rc('font', family='serif')
    rcParams.update({'figure.autolayout': True})

    axI = None
    axQ = None
    ax_psd = None

    num_plots = int(plot_time) + int(plot_psd) + 1
    if plot_time and plot_psd:
        gs = plt.GridSpec(num_plots, 2, wspace=.25, hspace=.5)
    else:
        gs = plt.GridSpec(num_plots, 2, wspace=.25, hspace=.4)
    fig = plt.figure()
    fig.set_size_inches(plt_size[0], plt_size[1])
    fig.set_dpi(dpi)
    fig.subplots_adjust(left=.10, bottom=.12, top=.93, right=.96)
    fig.set_tight_layout(False)

    plot_cnt = 0
    if plot_time:
        if np.iscomplexobj(time_sig):
            axI = fig.add_subplot(gs[plot_cnt, 0])
            axQ = fig.add_subplot(gs[plot_cnt, 1], sharex=axI)
        else:
            axI = fig.add_subplot(gs[plot_cnt, :])
        plot_cnt += 1
    if plot_psd:
        ax_psd = fig.add_subplot(gs[plot_cnt, :])
        plot_cnt += 1

    ax_water = fig.add_subplot(gs[plot_cnt, :])
    if ytime_max is None:
        ytime_max = 2. * np.abs(np.max(in_vec))

    if ytime_min is None:
        ytime_min = -2. * np.abs(np.max(in_vec))

    if title is not None:
        window_title = parse_title(title)
        fig.canvas.set_window_title(window_title)
    if ytime_max - ytime_min == 0.:
        ytime_max += .001
        ytime_min -= .001
    if plot_time:
        axI.plot(np.real(time_sig), 'b', lw=.9)
        axI.ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
        axI.locator_params(nbins=10)
        axI.tick_params(axis='x', labelsize=ticksize, labelrotation=45)
        axI.tick_params(axis='y', labelsize=ticksize)
        axI.xaxis.get_offset_text().set_fontsize(8)
        axI.set_ylim(ytime_min, ytime_max)
        samp_str = r'$\sf{Sample\ Number}$'
        mag_str = r'$\sf{Linear\ Magnitude}$'
        lat_str_i = r'$\sf{I\ Signal}$'
        lat_str_q = r'$\sf{Q\ Signal}$'
        axI.set_title(lat_str_i, fontsize=titlesize)
        axI.set_xlabel(samp_str, fontsize=labelsize)
        axI.set_ylabel(mag_str, fontsize=labelsize)

        if np.iscomplexobj(time_sig):
            axQ.plot(np.imag(time_sig), 'r', lw=.9)
            axQ.locator_params(nbins=10)
            axQ.ticklabel_format(axis='x', style='sci', scilimits=(-2,2))
            axQ.tick_params(axis='x', labelsize=ticksize, labelrotation=45)
            axQ.tick_params(axis='y', labelsize=ticksize)
            axQ.xaxis.get_offset_text().set_fontsize(8)
            axQ.set_ylim(ytime_min, ytime_max)
            # xdata = np.add(range(hist_len*chunk_size),-hist_len*chunk_size)
            # ax0.set_xlim(xdata[0],xdata[-1])
            axQ.set_xlabel(samp_str, fontsize=labelsize)
            axQ.set_ylabel(mag_str, fontsize=labelsize)
            axQ.set_title(lat_str_q, fontsize=titlesize)

    if plot_psd:
        if psd_input:
            wvec = w_vec[0]
            # ipdb.set_trace()
            X2 = np.max(resp_water, 0)  #resp_water[0]
            if rotate_spec:
                X2 = np.max(resp_water, 1)
        else:
            (wvec, X2) = gen_psd(in_vec, find_offset=False, normalize=normalize)  # , scale_psd=False)
        if psd_min is None:
            psd_min = np.min(X2) - 10

        if psd_max is None:
            psd_max = np.max(X2) + 10
        ax_psd.plot(wvec, X2, lw=.9)
        ax_psd.locator_params(nbins=10)
        ax_psd.tick_params(axis='both', labelsize=ticksize)
        lat_str = r'$\sf{Discrete\ Frequency\ }$' + r'$\pi' + r'\frac{rads}{sample}$'
        ax_psd.set_xlabel(lat_str, fontsize=labelsize)
        lat_str = r'$\sf{Spectral\ Magnitude\ }$' + r'$\mathit{dB}$'
        ax_psd.set_ylabel(lat_str, fontsize=labelsize)
        ax_psd.set_title(psd_str, fontsize=titlesize)
        ax_psd.set_ylim(psd_min, psd_max)

    upper_val = np.shape(resp_water)[0] - 1
    low_freq = 0 if one_side else -1
    extent_val = [low_freq, 1, 0, upper_val]
    if rotate_spec:
        upper_val = np.shape(resp_water)[1] - 1
        extent_val = [0, upper_val, low_freq, 1]

    if upper_val == 0:
        upper_val = 1
    y_int = list(range(upper_val + 1))
    if len(y_int) > 15:
        dec_rate = len(y_int) // 15
        y_int = y_int[::dec_rate]
    im = ax_water.imshow(resp_water, origin='lower', interpolation='nearest', aspect='auto', extent=extent_val,
                         cmap=plt.get_cmap('viridis'))

    ax_water.locator_params(nbins=10)
    ax_water.tick_params(axis='x', labelsize=ticksize)
    ax_water.tick_params(axis='y', labelsize=ticksize)
    if title is None:
        title = r'$\sf{Waterfall\ Spectrum}$'
    ax_water.set_title(title, fontsize=titlesize)

    if rotate_spec:
        ax_water.xaxis.set_ticks(y_int)
        ax_water.ticklabel_format(axis='y', style='sci', scilimits=(-2,2))
        lat_str = r'$\sf{Discrete\ Frequency\ }$' + r'$\pi$' + r'$\frac{rads}{sample}$'
        ax_water.set_ylabel(lat_str, fontsize=labelsize)
        lat_str = r'$\sf{Spectral\ Slice\ Number}$'
        ax_water.set_xlabel(lat_str, fontsize=labelsize)
        ax_water.tick_params(axis='x', labelsize=ticksize, labelrotation=45)
    else:
        ax_water.yaxis.set_ticks(y_int)
        ax_water.ticklabel_format(axis='y', style='sci', scilimits=(-2,2))
        lat_str = r'$\sf{Discrete\ Frequency\ }$' + r'$\pi$' + r'$\frac{rads}{sample}$'
        ax_water.set_xlabel(lat_str, fontsize=labelsize)
        lat_str = r'$\sf{Spectral\ Slice\ Number}$'
        ax_water.set_ylabel(lat_str, fontsize=labelsize)
        ax_water.tick_params(axis='y', labelsize=ticksize, labelrotation=45)


    if channels is not None:
        bbox = ax_water.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
        ax_width, ax_height = bbox.width, bbox.height
        for i, chan in enumerate(channels):
            # this uses the dictionary structure given by channel_dict
            try:
                start_freq = w_vec[0][chan['start_bin']]
                end_freq = w_vec[0][chan['end_bin']]
                start_slice = chan['start_slice']
                end_slice = chan['end_slice']
                if rotate_spec:
                    bottom_left = (start_slice, start_freq)
                    width = (end_slice - start_slice)
                    height = (end_freq - start_freq)
                else:
                    bottom_left = (start_freq, start_slice)
                    height = (end_slice - start_slice)
                    width = (end_freq - start_freq)

                if chan_colors is None:
                    color = 'C{}'.format(i % 20)
                else:
                    color = 'C{}'.format(chan_colors[i])

                rect = patches.Rectangle(bottom_left, width, height,linewidth=2,edgecolor=color,facecolor=color, alpha=.5, fill=True)
                ax_water.add_patch(rect)
            except:
                continue

    ax_water.grid(False)
    # get postion of waterfall.
    box = ax_water.get_position()
    ax_water.set_position([box.x0, box.y0, box.width * .9, box.height])
    ax_color = plt.axes([box.x0 + box.width * .92, box.y0, 0.02, box.height])

    cb = plt.colorbar(im, cax=ax_color, orientation='vertical', aspect=100)
    tick_locator = ticker.MaxNLocator(nbins=5)
    cb.locator = tick_locator
    cb.update_ticks()
    cb.ax.tick_params(labelsize=ticksize)
    cb.set_label(r'$\sf{dB}$', fontsize=ticksize)

    # label_helper(ax, title=title, labelsize=labelsize, xlabel=xlabel, ylabel=ylabel, titlesize=titlesize)
    try:
        fig_wrap_up(fig, title, savefig, plot_on, pickle_fig, path)
    finally:
        ret_tuple = (fig,)
        if plot_time:
            ret_tuple = ret_tuple + (axI,)
            if np.iscomplexobj(time_sig):
                ret_tuple = ret_tuple + (axQ,)
        if plot_psd:
            ret_tuple = ret_tuple + (ax_psd,)

        ret_tuple = ret_tuple + (ax_water,)

    return ret_tuple


def plot_psd(ax, wvec, resp, format_str=None, title=None, label=None, min_n_ticks=4, alpha=1.,
             miny=None, maxy=None, minx=None, maxx=None, color=None, markersize=None, marker=None, linewidth=None, linestyle=None,
             pwr_pts=None, freq_pts=None, xprec=3, yprec=0, xlabel=df_str, ylabel=amp_str, labelsize=14, titlesize=16,
             legendsize=12, ticksize=8):
    """
        Helper method that generates a pretty Spectral plot.
    """
    tvalue = plot_macro(wvec, resp, label=label, format_str=format_str, color=color, marker=marker,
                        markersize=markersize, linestyle=linestyle, linewidth=linewidth, alpha=alpha)

    wvec = tvalue[1][0]
    resp = tvalue[2][0]
    zip_iter = tvalue[0]
    ylabel = amp_str if ylabel is None else ylabel
    # orig_marker_size = rcParams.get('lines.markersize')
    # if markersize is not None:
    #     rcParams.update({'lines.markersize': markersize})

    gen_box = False
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    if (pwr_pts is not None) or (freq_pts is not None):
        gen_box = True

    final_text = ''
    if pwr_pts is not None:
        pwr_pts = np.atleast_1d(pwr_pts)
        units = r'$\pi \frac{rads}{sample}$'
        if xlabel is not None:
            units = xlabel
        for pwr_pt in pwr_pts:
            lidx, ridx = find_pwr(resp, pwr_pt)
            wleft = None
            if lidx is not None:
                wleft = wvec[lidx]
            wright = wvec[ridx]
            ax.axvline(wright, color='g', linewidth=1)
            if lidx is not None:
                half = '{0:.{prec}f} dB points\n{1:.{prec}f} and {2:.{prec}f} '.format(pwr_pt, wleft, wright, prec=xprec)
                text_str = half + units
                ax.axvline(wleft, color='g', linewidth=1)
            else:
                text_str = '{0:.{prec}f} dB point\n{1:.{prec}f} '.format(pwr_pt, wright, prec=xprec)
                text_str = text_str + units

            final_text += text_str

    if freq_pts is not None:
        freq_pts = np.atleast_1d(freq_pts)
        for freq_pt in freq_pts:
            idx = find_freq(wvec, freq_pt)
            amp_val = resp[idx]
            freq_val = wvec[idx]
            ax.axvline(freq_val, color='r', linewidth=1)
            text_str = '\n{0:.{prec}f} dB @ {1:.{prec}f}'.format(amp_val, freq_val, prec=xprec)
            text_str = text_str + r'$\pi \frac{rads}{sample}$'
            final_text += text_str

    if gen_box:
        ax.text(0.05, 0.95, final_text, transform=ax.transAxes, fontsize=14, verticalalignment='top', bbox=props)

    maxy = 3. + resp.max() if maxy is None else maxy
    miny = resp.min() if miny is None else miny
    minx = np.min(wvec) if minx is None else minx
    maxx = np.max(wvec) if maxx is None else maxx

    xlabel = df_str if xlabel is None else xlabel

    ax, _ = plt_ax(ax, zip_iter, xprec, yprec, min_n_ticks, minx, maxx, miny, maxy, ticksize)
    ax.locator_params(nbins=10)
    # ax.ticklabel_format(axis='y', style='plain')
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    spec_label_helper(ax, title=title, titlesize=titlesize, labelsize=labelsize, xlabel=xlabel, ylabel=ylabel)

    # to use latex make sure machine has installed texlive-full packages.
    plt.rc('text', usetex=False)
    plt.rc('font', family='serif')
    if label is not None:
        attach_legend(ax, fontsize=legendsize)


def test_run():

    from phy_tools.qam_waveform import QAM_Mod
    plt.close('all')

    snr = 40
    spb = 8

    sig_obj = QAM_Mod(frame_mod='qpsk', spb=spb, snr=snr)
    signal = sig_obj.gen_frames(5, frame_space_mean=100000, sig_bw=.5)[0]
    #
    plot_psd_helper(signal, normalize=True, miny=-80, savefig=True, plot_on=False, title='test psd')
    plot_waterfall(signal, num_avgs=4)

    # out_name = 'test_sig.mp4'
    # water_obj.waterfall_scroll(signal, dpi_val=450, hist_len=20,
    #                            plot_time=True,
    #                            plot_psds=True, psd_max=40,
    #                            mpeg_file=out_name)


# if __name__ == "__main__":
#
#     test_run()
