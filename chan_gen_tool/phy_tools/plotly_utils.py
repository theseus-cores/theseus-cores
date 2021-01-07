#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

Created on Sat Oct 24 7:54:28 2020

@author: phil
"""
import numpy as np
import scipy.signal as sig
import ipdb

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from phy_tools.qam_waveform import QAM_Mod
from phy_tools.plt_utils import parse_title, plot_macro, attach_legend, gen_psd, find_pwr
import pandas as pd

from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    __version__ = today.strftime("%Y.%m.%d")

PALETTE = px.colors.qualitative.D3
DF_STR = r'$\large{\sf{Discrete\ Frequency\ }\pi\,\frac{rads}{sample}}$'
SAMP_STR = r'$\large{\sf{Sample\ Number}}$'
TAMP_STR = r'$\large{\sf{Amplitude}}$'
PSD_STR = r'$\large{\sf{PSD}}$'
AMP_STR = r'$\large{\sf{Spectral\ Magnitude\ } \sf{\it{dB}}}$'
REAL_STR = r'$\large{\sf{Real}}$'
IMAG_STR = r'$\large{\sf{Imag}}$'
VSPACE = .10
DPI = 100

marker_offset = 0.004

def offset_signal(signal, marker_offset=0.04):
    if abs(signal) <= marker_offset:
        return 0
    return signal - marker_offset if signal > 0 else signal + marker_offset

def plotly_time_helper(df, mode=None, color=None, marker=None, selector=None, opacity=None, index_str='sig_idx', y_name='iq',
                       x_name=None, minx=None, maxx=None, miny=None, maxy=None, titlesize=12, labelsize=10, legendsize=10, title=None,
                       subplot_title=None, xlabel=None, ylabel=None, xprec=None, yprec = None, plt_size=(8., 6.), stem_plot=False,
                       pickle_fig=False):


    STANDOFF=10
    column_names=df.columns.to_list()
    sig_indices=np.unique(df[index_str])
    num_sigs=len(sig_indices)

    showlegend = True if num_sigs > 1 else False

    # sig_title = r'$\sf{{{}\}}$'.format(y_name)
    real_str = r'$\Large{{\sf{{{}\ Real}}}}$'.format(y_name) if subplot_title is None else subplot_title[0]
    #sig_title + ' ' + REAL_STR
    try:
        imag_str = r'$\Large{{\sf{{{}\ Imag}}}}$'.format(y_name) if subplot_title is None else subplot_title[1]
    except:
        imag_str = r'$\Large{{\sf{{{}\ Imag}}}}$'.format(y_name)

    xlabel=SAMP_STR if xlabel is None else xlabel
    ylabel=TAMP_STR if ylabel is None else ylabel

    marker=[dict(size= 12, line = None)] * num_sigs if marker is None else marker
        
    selector=[] * num_sigs if selector is None else selector
    opacity=[1.0] * num_sigs if opacity is None else opacity
    mode=['lines'] * num_sigs if mode is None else mode
    if stem_plot:
        mode = ['markers'] * num_sigs

    comp_sig = False
    ymins = []
    ymaxs = []
    for idx in sig_indices:
        signal=df[df[index_str] == idx][y_name].to_numpy()
        comp_sig = True if np.iscomplexobj(signal) else comp_sig
        if comp_sig:
            ymins.append(np.min(np.abs(signal)))
            ymaxs.append(np.max(np.abs(signal)))
        else:
            ymins.append(np.min(signal))
            ymaxs.append(np.max(signal))

    miny = np.min(ymins) - .1 * np.min(ymins) if miny is None else miny
    maxy = 1.1 * np.max(ymaxs) if maxy is None else maxy

    # if time dataframe was passed in.

    if comp_sig:
        fig=make_subplots(rows=1, cols=2, specs = [[{}, {}]],
                            subplot_titles = (real_str, imag_str), vertical_spacing = VSPACE, horizontal_spacing = .05,
                            shared_xaxes = 'rows')
    else:
        fig=make_subplots(rows = 1, cols = 1, subplot_titles = (real_str,), vertical_spacing = VSPACE, specs=[[{}]])

    shapes = []
    for ii, (idx, group) in enumerate(df.groupby(index_str)):
        r_idx = ii % len(PALETTE)
        c_idx = (ii + num_sigs) % len(PALETTE)
        x_series = group.index.to_series() if x_name is None else group[x_name].apply(np.real)
        fig.add_trace(go.Scattergl(x=x_series,
                                   y=group[y_name].apply(np.real),
                                   name='Real {}'.format(idx),
                                   marker_color=PALETTE[r_idx],
                                   marker=marker[ii],
                                   opacity=opacity[ii],
                                   mode=mode[ii],
                                   showlegend=showlegend), row = 1, col = 1, secondary_y = False)
                            
        if stem_plot:
            shapes.extend([dict(type='line', xref='x1', yref='y1', x0=i, y0=0, x1=i,
                                y1=offset_signal(np.real(group[y_name][i]), .001), opacity=opacity[ii],
                                line=dict(color=PALETTE[r_idx], width=2)) for i in range(len(group[y_name]))])


        # shapes = []
        if comp_sig:
            x_series = group.index.to_series() if x_name is None else group[x_name].apply(np.real)
            fig.add_trace(go.Scattergl(x=x_series,
                                       y=group[y_name].apply(np.imag),
                                       name='Imag {}'.format(idx),
                                       marker_color=PALETTE[c_idx],
                                       marker=marker[ii],
                                       opacity=opacity[ii],
                                       mode=mode[ii],
                                       showlegend=showlegend), row = 1, col = 2, secondary_y = False)

            if stem_plot:
                shapes.extend([dict(type='line', xref='x2', yref='y2', x0=i, y0=0, x1=i,
                                    y1=offset_signal(np.imag(group[y_name][i]), .001),
                                    line=dict(color=PALETTE[c_idx], width=2)) for i in range(len(group[y_name]))])


    fig.update_xaxes(
        tickangle = 45,
        title_text = xlabel,
        title_font = {"size": labelsize},
        title_standoff = STANDOFF,
        range=(minx, maxx),
        row=1, col=1)

    fig.update_yaxes(
        tickangle = 0,
        title_text = ylabel,
        title_font = {"size": labelsize},
        title_standoff = STANDOFF,
        range=(miny, maxy),
        row=1, col=1)

    if comp_sig:
        fig.update_xaxes(
            tickangle = 45,
            title_text = xlabel,
            title_font = {"size": labelsize},
            title_standoff = STANDOFF,
            range=(minx, maxx),
            row=1, col=2)

        fig.update_yaxes(
            tickangle = 0,
            title_text = ylabel,
            title_font = {"size": labelsize},
            title_standoff = STANDOFF,
            range=(miny, maxy),
            row=1, col=2)


    for ann in fig['layout']['annotations']:
        ann['font'] = dict(size=titlesize)  #,color='#ff0000')
        ann['y'] = ann['y'] + .03
        # ann['bargap'] = .95
    
    fig.update_layout(go.Layout(shapes=shapes, title=title))
    fig.layout.title.font.size = titlesize
    fig.layout.hovermode = 'x'
    return fig
    # fig.show()

def plotly_psd_helper(df, fft_size=1024, pwr_pts=None, freq_pts=None, plot_time=False, normalize=True, 
                      index_str='Sig_Idx', omega_name='omega', series_name='psd', tseries_name='iq', mode=None, color=None, 
                      marker=None, selector=None, opacity=None,
                      minx=None, maxx=None, miny=None, maxy=None, titlesize=12, labelsize=10, legendsize=10, title=None,
                      xlabel=None, ylabel=None, xprec=None, yprec=None,
                      window='blackmanharris', noverlap=None, nperseg=None, return_onesided=False, savefig=False,
                      dpi=DPI, time_df=None, pickle_fig=False):


    STANDOFF = 10
    column_names = df.columns.to_list()
    res = [curr_str for curr_str in df.columns.to_list() if series_name.lower() in curr_str.lower()]
    sig_indices = np.unique(df[index_str])
    num_sigs = len(sig_indices)

    xlabel = SAMP_STR if xlabel is None else xlabel
    ylabel = TAMP_STR if ylabel is None else ylabel

    marker = [dict(size=12, line=None)] * num_sigs if marker is None else marker
    selector = [] * num_sigs if selector is None else selector
    opacity = [1.0] * num_sigs if opacity is None else opacity
    mode = ['lines'] * num_sigs if mode is None else mode

    # then psd have already been computed.  Else extract signals and compute psd values.
    comp_sig = False
    ymins = []
    ymaxs = []
    print("hello")
    if len(res) == 0:
        new_df = pd.DataFrame({})
        for idx in sig_indices:
            signal = df[df[index_str] == idx][tseries_name].to_numpy()
            comp_sig = True if np.iscomplexobj(signal) else comp_sig
            omega, resp = gen_psd(signal, return_onesided, fft_size, noverlap, nperseg, normalize, False, window)
            ymins.append(np.min(resp))
            ymaxs.append(np.max(resp))
            pd_dict = {omega_name:omega, series_name: resp, index_str: idx}
            df_temp = pd.DataFrame(pd_dict)
            new_df = new_df.append(df_temp)
    else:
        new_df = df.copy()
        for idx in sig_indices:
            resp = df[df[index_str] == idx][series_name].to_numpy()
            ymins.append(np.min(resp))
            ymaxs.append(np.max(resp))

    miny = np.min(ymins) - 10 if miny is None else miny
    maxy = np.max(ymaxs) + 10 if maxy is None else maxy
    
    # if time dataframe was passed in.
    time_flag = time_df is not None
    time_df = df if time_flag is False else time_df

    num_plots = 1 + plot_time

    # if signal is a tuple or a list of tuples, then wvec and resp has been calculated.  Just plot.
    if plot_time:
        psd_tpl = (2, 1)
        if comp_sig:
            fig = make_subplots(rows=2, cols=2, specs=[[{}, {}], [{"colspan": 2}, None]], 
                                subplot_titles=(REAL_STR, IMAG_STR, PSD_STR), vertical_spacing=VSPACE, horizontal_spacing=.05,
                                shared_xaxes='rows')
            # subplot_titles = ("Plot 1", "Plot 2", "Plot 3", "Plot 4")
        else:
            fig = make_subplots(rows=2, cols=1, subplot_titles=(REAL_STR, PSD_STR), vertical_spacing=VSPACE, shared_xaxes='rows')

    else:
        psd_tpl = (1, 1)
        fig = make_subplots(rows=1, cols=1, subplot_titles=(PSD_STR), vertical_spacing=VSPACE, shared_xaxes='rows')


    if plot_time:
        for ii, (idx, group) in enumerate(time_df.groupby(index_str)):
            c_idx = ii % len(PALETTE)
            fig.add_trace(go.Scattergl(y=group[tseries_name].apply(np.real), 
                                       name='Real {}'.format(idx),
                                       marker_color=PALETTE[ii],
                                       marker=marker[ii],
                                       opacity=opacity[ii],
                                       mode=mode[ii],
                                       showlegend=False), row=1, col=1, secondary_y=False)

            if comp_sig:
                fig.add_trace(go.Scattergl(y=group[tseries_name].apply(np.imag), 
                              name='Imag {}'.format(idx),
                              marker_color=PALETTE[ii],
                              marker=marker[ii],
                              opacity=opacity[ii],
                              mode=mode[ii],
                              showlegend=False), row=1, col=2, secondary_y=False)

        fig.update_xaxes(
            tickangle = 45,
            title_text = xlabel,
            title_font = {"size": labelsize},
            title_standoff = STANDOFF,
            row=1, col=1)

        fig.update_yaxes(
            tickangle = 0,
            title_text = ylabel,
            title_font = {"size": labelsize},
            title_standoff = STANDOFF,
            row=1, col=1)

        if comp_sig:
            fig.update_xaxes(
                tickangle = 45,
                title_text = xlabel,
                title_font = {"size": labelsize},
                title_standoff = STANDOFF,
                row=1, col=2)

            fig.update_yaxes(
                tickangle = 0,
                title_text = ylabel,
                title_font = {"size": labelsize},
                title_standoff = STANDOFF,
                row=1, col=2)
    

    for ii, (idx, group) in enumerate(new_df.groupby("Sig_Idx")):
        c_idx = ii % len(PALETTE)
        fig.add_trace(go.Scattergl(x=group[omega_name], y=group[series_name], 
                      name=idx,
                      marker_color=PALETTE[ii],
                      marker=marker[ii],
                      mode=mode[ii],
                      opacity=opacity[ii]), row=psd_tpl[0], col=psd_tpl[1])
    

    if pwr_pts is not None:
        pwr_pts = np.atleast_1d(pwr_pts)
        resp = new_df[new_df[index_str] == 0][series_name].to_numpy()
        for pwr_pt in pwr_pts:
            lidx, ridx = find_pwr(resp, pwr_pt)
            fig.add_vline(x=new_df[omega_name].iloc[lidx], line_width=3, line_dash="dash",
                          line_color="green", row=psd_tpl[0], col=psd_tpl[1])
            fig.add_vline(x=new_df[omega_name].iloc[ridx], line_width=3, line_dash="dash",
                          line_color="green", row=psd_tpl[0], col=psd_tpl[1])

    fig.update_xaxes(
        tickangle = 45,
        title_text = DF_STR,
        title_font = {"size": labelsize},
        title_standoff = 15,
        range=(minx, maxx),
        row=psd_tpl[0], col=psd_tpl[1])

    fig.update_yaxes(
        tickangle = 0,
        title_text = AMP_STR,
        title_font = {"size": labelsize},
        title_standoff = 15,
        range=(miny, maxy),
        row=psd_tpl[0], col=psd_tpl[1])

    fig.update_layout(
        title_font = {"size":titlesize},)

    for ann in fig['layout']['annotations']:
        ann['font'] = dict(size=titlesize)  #,color='#ff0000')
        ann['y'] = ann['y'] + .03
    # fig.layout.annotations[0]["font"] = {'size': titlesize}
    return fig
    # fig.show()

def plotly_const_diag(df, title=None, label=None, format_str=None, linestyle=None, linewidth=None, x_vec=None,
                    min_n_ticks=4, color=None, marker=None, savefig=False, plot_on=False, markersize=None, miny=None,
                    maxy=None, minx=None, maxx=None, xlabel=None, ylabel=None, labelsize=14, titlesize=16, alpha=1.,
                    ax=None, pickle_fig=False, path='./'):
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
    if title is None:
        title = r'$\sf{Constellation\ Plot}$'
    columns = df.columns.to_list()
    fig = go.Figure(data=go.Scatter(
        x=df.iloc[:, 0],
        y=df.iloc[:, 1],
        # hovertext=' Scatter',
        hoverlabel=dict(namelength=0),
        hovertemplate='Scatter<br>%s: %%{x:.4f}<br>%s: %%{y:.4f}'% (columns[0], columns[1]),
        mode='markers',
        # marker_size=steamdf['ratio'],
        marker=dict(
            color='rgb(255, 178, 102)',
            size=10,
            line=dict(
                  color='DarkSlateGrey',
                  width=0
            )
        )
    ))
    fig.update_layout(
        title=title,
        xaxis_title=r'$\sf{{{}}}$'.format(df.columns[0]),
        yaxis_title=r'$\sf{{{}}}$'.format(df.columns[1]),
        font=dict(
            # family='Verdana',
            size=26,
            color='black'
        )
    )
    fig.show()


if __name__ == "__main__":

    import plotly.graph_objects as go

    SPB = 4
    SNR = 20

    x = np.random.normal(size=1000)
    y = np.random.normal(size=1000)

    data_dict = {'Real':x, 'Imag':y}

    df = pd.DataFrame(data_dict)
    
    # plotly_const_diag(df)

    sig_obj = QAM_Mod(frame_mod='qpsk', spb=SPB, snr=SNR)
    signal = sig_obj.gen_frames(5, frame_space_mean=100000, sig_bw=.5)[0]

    # omega, resp = gen_psd(signal)
    data_dict = {'iq': np.real(signal[:100]), 'Sig_Idx' : 0}

    df = pd.DataFrame(data_dict)

    signal = sig_obj.gen_frames(5, frame_space_mean=100000, sig_bw=.25, snr=40)[0]
    data_dict = {'iq': np.real(signal[:100]), 'Sig_Idx': 1}

    df2 = pd.DataFrame(data_dict)

    df = df.append(df2)

    fig = plotly_psd_helper(df, plot_time=True, opacity=[.8]*2, labelsize=18, titlesize=24, miny=-80, index_str='Sig_Idx', tseries_name='iq',
                            pwr_pts=-3.01)
    fig.show()
    # fig = plotly_time_helper(df, opacity=[.8]*2, labelsize=28, titlesize=136, index_str='Sig_Idx', 
                            #  y_name='iq', stem_plot=True, title=r'$\Large{\sf{Test\ Stem}}$')

    # fig.show()


    # fig = px.line(df, x="Omega", y="PSD", color="Sig_Idx")
    # fig.show()
    
