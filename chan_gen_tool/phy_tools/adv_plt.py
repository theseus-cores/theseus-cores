#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author: phil
"""

import pandas as pd
import numpy as np
import holoviews as hv
import ipdb
import datashader as ds
from holoviews.operation.datashader import datashade, aggregate, dynspread
from holoviews.operation import decimate
from bokeh.palettes import Viridis256
from bokeh.models import HoverTool
from holoviews import opts
import panel as pp
import param
from phy_tools.plt_utils import waterfall_spec, gen_psd, win_list, num_list

from subprocess import check_output, CalledProcessError, DEVNULL
try:
    __version__ = check_output('git log -1 --pretty=format:%cd --date=format:%Y.%m.%d'.split(), stderr=DEVNULL).decode()
except CalledProcessError:
    from datetime import date
    today = date.today()
    __version__ = today.strftime("%Y.%m.%d")

hv.extension('bokeh','matplotlib')
renderer = hv.renderer('bokeh')

ds_limit = 20000

# plot_width = 800
# plot_height = 600
max_px = 20
min_alpha = 120
font_dict = dict(xlabel=15, ylabel=15, title=15, xticks=10, yticks=10)

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

class SpecOptions0(param.Parameterized):
    FFT_Size_list = ['32', '64', '128', '256', '512', '1024', '2048', '4096', '8192', '16384']
    FFT_Size = param.ObjectSelector(default='256', objects=FFT_Size_list)
    Window = param.ObjectSelector(default='blackmanharris', objects=win_list)


class SpecOptions1(param.Parameterized):
    Percent_Overlap_list = ['0', '25', '50', '75']
    Percent_Overlap = param.ObjectSelector(default='75', objects=Percent_Overlap_list)
    Num_Avgs = param.ObjectSelector(default='1', objects=num_list)

class TimePlotter(object):
    def __init__(self, plot_width=600, plot_height=600):
        self.xrange = None
        self.yrange0 = None
        self.yrange1 = None
        self.plot_height = plot_height
        self.plot_width = plot_width
        self.hover_count_real = 1
        self.view_count_real = 1
        self.hover_count_imag = 1
        self.view_count_imag = 1
        self.update_count = 0
        self.time_df = None
        self.max_samples = ds_limit
        self.min_alpha = 70

    def load_data(self, sig):
        self.sig = np.array(sig)
        self.plot_time()

    def plot_time(self):
        x_vals = np.arange(0, len(self.sig), dtype=np.int)
        data_dict = {'Sample':x_vals, 'Real':np.real(self.sig), 'Imag':np.imag(self.sig)}
        self.time_df = pd.DataFrame(data_dict, columns = ['Sample', 'Real', 'Imag'])

        self.xrange = (0, len(self.sig) - 1)
        if self.time_df.Real.min() > 0:
            self.yrange0 = (.75*self.time_df.Real.min(), 1.25*self.time_df.Real.max())
        else:
            self.yrange0 = (1.25*self.time_df.Real.min(), 1.25*self.time_df.Real.max())

        if self.time_df.Imag.min() > 0:
            self.yrange1 = (.75*self.time_df.Imag.min(), 1.25*self.time_df.Imag.max())
        else:
            self.yrange1 = (1.25*self.time_df.Imag.min(), 1.25*self.time_df.Imag.max())


        if np.iscomplexobj(self.sig)is False:
            self.yrange1 = (-1, 1)

        self.real_curve = hv.Curve(self.time_df, 'Sample', vdims='Real', group='Time Domain')
        self.imag_curve = hv.Curve(self.time_df, 'Sample', vdims='Imag', group='Time Domain')

        self.update_count += 1

        return 0

    def time_hover_gen(self, data, vdims, x_range):

        lidx = 0
        ridx = len(self.time_df)
        if x_range is not None:
            lidx = int(x_range[0])
            ridx = int(x_range[1])

        num_pts = ridx - lidx + 1
        size = 1
        if num_pts > 500:
            size = .5
        if num_pts > 1000:
            size = .25
        if num_pts > 2000:
            size = .125

        hover = HoverTool(tooltips=[('Sample', '@{Sample}'), (vdims, '@{}'.format(vdims))], mode='vline')
        scatt = hv.Scatter(self.time_df[lidx:ridx], kdims='Sample', vdims=vdims, group='Time Domain').opts(size=size, tools=[hover])
        return scatt

    def gen_real_view(self, resetting, x_range, y_range):

        if x_range is None:
            x_range = self.xrange
        if y_range is None:
            y_range = self.yrange0
        # ipdb.set_trace()
        if resetting:
            return dynspread(datashade(self.real_curve, cmap='blue', normalization='linear', x_range=self.xrange, y_range=self.yrange0, min_alpha=self.min_alpha, dynamic=False), max_px=max_px)
        else:
            return dynspread(datashade(self.real_curve, cmap='blue', normalization='linear', x_range=x_range, y_range=y_range, min_alpha=self.min_alpha, dynamic=False), max_px=max_px)

    def gen_real_hover(self, resetting, x_range, y_range):
        if resetting:
            x_range = self.xrange
            y_range = self.yrange1

        opts_hover_time = dict(alpha=0, hover_alpha=0.2, fill_alpha=0, framewise=True, color='r')
        hover = self.time_hover_gen(self.time_df, vdims='Real', x_range=x_range)
        return decimate(hover, max_samples=self.max_samples, dynamic=False).opts(**opts_hover_time)

    def gen_imag_view(self, resetting, x_range, y_range):

        if x_range is None:
            x_range = self.xrange
        if y_range is None:
            y_range = self.yrange1
        if resetting:
            return dynspread(datashade(self.imag_curve, cmap='red', normalization='linear', x_range=self.xrange, y_range=self.yrange1, min_alpha=self.min_alpha, dynamic=False), max_px=max_px)
        else:
            return dynspread(datashade(self.imag_curve, cmap='red', normalization='linear', x_range=x_range, y_range=y_range, min_alpha=self.min_alpha, dynamic=False), max_px=max_px)

    def gen_imag_hover(self, resetting, x_range, y_range):
        # print("gen_imag_hover {}".format(resetting))
        if resetting:
            x_range = self.xrange
            y_range = self.yrange1
        opts_hover_time = dict(alpha=0, hover_alpha=0.2, fill_alpha=0, framewise=True, color='r')
        hover = self.time_hover_gen(self.time_df, vdims='Imag', x_range=x_range)
        return decimate(hover, max_samples=self.max_samples, dynamic=False).opts(**opts_hover_time)  #, dynamic=True)


class SpecPlotter(object):
    def __init__(self, plot_width=600, plot_height=600):  # , *args, **kwargs):
        # super(Spectrum_Class, self).__init__(*args, **kwargs)
        self.xrange = None
        self.yrange = None
        self.zrange = None
        self.step_size = None
        self.plot_height = plot_height
        self.plot_width = plot_width
        self.hover_count = 1
        self.view_count = 1
        self.update_count = 0
        self.water_x_range = None
        self.water_y_range = None

    def water_view(self, x_range, FFT_Size='256', Percent_Overlap='50', Num_Avgs='1', Window='blackmanharris'):
        # print(FFT_Size)
        if self.view_count > self.update_count:
            self.gen_spec_points(x_range, FFT_Size, Percent_Overlap, Num_Avgs, Window)
        self.view_count += 1

        return self.gen_water_spec()

    def psd_view(self, x_range, FFT_Size='256', Percent_Overlap='50', Num_Avgs='1', Window='blackmanharris'):
        # print("updating psd_view {}, {}".format(self.view_count, self.update_count))
        if self.view_count > self.update_count:
            self.gen_spec_points(x_range, FFT_Size, Percent_Overlap, Num_Avgs, Window)
        self.view_count += 1
        return self.psd

    def set_plot_height(self, plot_height):
        self.plot_height = plot_height

    def set_plot_width(self, plot_width):
        self.plot_width = plot_width

    def load_data(self, sig):
        self.sig = np.array(sig)
        # generate initial points

    def add_stream(self, stream_value):
        self.streams.append(stream_value)

    def update_xy(self, xrange, yrange):
        self.water_x_range = xrange
        self.water_y_range = yrange

    def gen_spec_points(self, rangex, FFT_Size, Percent_Overlap, Num_Avgs, Window):
        sig_int = np.array(self.sig)
        if rangex is not None:
            lidx = int(rangex[0])
            if lidx < 0:
                lidx = 0
            ridx = int(rangex[1])
            if ridx > len(sig_int):
                ridx = len(sig_int)
            sig_int = sig_int[lidx:ridx]

        # remove nans
        sig_int = sig_int[~np.isnan(sig_int)]
        # put in check here and pad with zeros.
        fft_size = int(FFT_Size)
        num_avgs = int(Num_Avgs)
        noverlap = int(.01 * int(Percent_Overlap) * fft_size)
        sig_len = len(sig_int)
        min_len = 4 * fft_size * num_avgs
        if sig_len < min_len:
            pad = [0] * (min_len - sig_len)
            sig_int = np.concatenate((sig_int, np.array(pad)))
        (omega_init, resp_init) = waterfall_spec(sig_int, fft_size=fft_size, window=Window, noverlap=noverlap, num_avgs=num_avgs)
        (omega_psd, resp_psd) = gen_psd(sig_int, fft_size=fft_size, window=Window, noverlap=noverlap)
        data_dict = {'Discrete Freq': omega_psd, 'dB':resp_psd}

        psd_df = pd.DataFrame(data_dict)
        self.step_size = 2. / fft_size
        discrete_freq = omega_init[0, :]
        spectral_slice = np.arange(0, np.shape(omega_init)[0], dtype=np.int)
        df = pd.DataFrame(resp_init, index=spectral_slice, columns=discrete_freq)

        df.columns.name = 'Discrete Freq'
        df.index.name = 'Spectral Slice'
        self.xrange = (discrete_freq[0], discrete_freq[-1])
        self.yrange = (spectral_slice[0], spectral_slice[-1])
        self.zrange = (np.min(np.min(resp_init)), np.max(np.max(resp_init)))
        self.source = pd.DataFrame(df.stack(), columns=['PowerdB']).reset_index()
        opts_curve = dict(tools=['wheel_zoom','box_zoom','save', 'reset'])
        self.points = hv.Points(self.source, kdims=['Discrete Freq', 'Spectral Slice'], vdims=['PowerdB'], group='Spectrum')
        hover = HoverTool(tooltips=[('Freq', '@{Discrete Freq}'), ('Power (dB)', '@{dB}')], mode='vline')
        opts = dict(tools=[hover])
        self.psd = hv.Curve(psd_df, 'Discrete Freq', vdims='dB', group='PSD').opts(**opts)

        self.update_count += 1

    def gen_water_spec(self):
        opts_spec = dict(width=self.plot_width, height=self.plot_height, xticks=10, yticks=10, xrotation=10, fontsize=font_dict)  # colorbar=False,
        heat_ds = datashade(self.points, aggregator=ds.min('PowerdB'), dynamic=False, cmap=Viridis256, clims=self.zrange, min_alpha=min_alpha,
                            normalization='linear', x_sampling=self.step_size, y_sampling=1).options(**opts_spec)
        return heat_ds

    def water_hover_gen(self, x_range, FFT_Size='256', Percent_Overlap='50', Num_Avgs='1', Window='blackmanharris'):
        width = 128
        height = 128
        fft_size = int(FFT_Size)
        if fft_size < 128:
            width = fft_size
            height = fft_size

        if self.hover_count > self.update_count:
            self.gen_spec_points(x_range, FFT_Size, Percent_Overlap, Num_Avgs, Window)
        self.hover_count += 1

        opts_hover = dict(tools=['hover'], alpha=0, hover_alpha=0.2, fill_alpha=0)
        agg = aggregate(self.points, width=width, height=height, dynamic=False, aggregator=ds.max('PowerdB'), x_sampling=self.step_size, y_sampling=1)
        return hv.QuadMesh(agg).options(**opts_hover)


def plot_bokeh_spectrum(sig, plot_width=600, plot_height=600):

    opts_spec = dict(width=plot_width, height=plot_height, xticks=10, yticks=10, xrotation=10, colorbar=False, fontsize=font_dict)
    time_obj = TimePlotter(plot_width=plot_width, plot_height=plot_height)
    time_obj.load_data(sig)
    # (real_curve, imag_curve, yrange0, yrange1, time_df) = plot_time(sig)
    resetp = hv.streams.PlotReset()
    rangexy = hv.streams.RangeXY()
    time_tools=['pan','wheel_zoom','box_zoom','save', 'reset']
    opts = dict(width=plot_width, height=plot_height, xticks=6, xrotation=10, fontsize=font_dict, framewise=True)
    opts_hover_time0 = dict(default_tools=time_tools, alpha=0, hover_alpha=0.2, fill_alpha=0, framewise=True, color='r')
    opts_hover_time1 = dict(default_tools=time_tools, alpha=0, hover_alpha=0.2, fill_alpha=0, framewise=True, color='b')

    dm0 = hv.DynamicMap(lambda **kw : time_obj.gen_real_view(**kw),  streams=[resetp, rangexy])
    dm0_hover = hv.DynamicMap(lambda **kw : time_obj.gen_real_hover(**kw), streams=[resetp, rangexy])
    dm0_final = (dm0 * dm0_hover).opts(**opts)
    #
    dm1 = hv.DynamicMap(lambda **kw : time_obj.gen_imag_view(**kw), streams=[resetp, rangexy])  # streams=[resetp]
    dm1_hover = hv.DynamicMap(lambda **kw : time_obj.gen_imag_hover(**kw), streams=[resetp, rangexy]) #, streams=[resetp])
    dm1_final = (dm1 * dm1_hover).opts(**opts)
    #
    row0 = pp.Row(dm0_final + dm1_final)

    # rangex = hv.streams.RangeX(source=rangexy)  #time_obj.real_curve)
    rangex = hv.streams.RangeX(source=dm0)
    spec_obj = SpecPlotter(plot_width=plot_width, plot_height=plot_height) #name="Waterfall Spectrum", streams=rangex)
    spec_obj.load_data(sig)

    options0 = SpecOptions0(name="Spectral Plot Params")
    options1 = SpecOptions1(name="------------------->")
    # generate waterfall
    spec_tools=['wheel_zoom','box_zoom','save', 'reset']
    spec_opts = dict(default_tools=spec_tools, framewise=True, fontsize=font_dict)
    dm0 = hv.DynamicMap(lambda **kw : spec_obj.water_view(**kw), streams=[rangex, options0, options1]).opts(**spec_opts)
    dm1 = hv.DynamicMap(lambda **kw : spec_obj.water_hover_gen(**kw), streams=[rangex, options0, options1]).opts(**spec_opts)
    water_overlay = dm0 * dm1

    # generate psd
    psd_opts = dict(default_tools=spec_tools, framewise=True, xrotation=10, width=plot_width, height=plot_height, fontsize=font_dict)
    psd_overlay = hv.DynamicMap(lambda **kw : spec_obj.psd_view(**kw), streams=[rangex, options0, options1]).opts(**psd_opts)
    bottom_row = water_overlay + psd_overlay
    row1 = pp.Row(bottom_row)
    row2 = pp.Row(options0, options1)
    layout = pp.Column(row0, row1, row2)
    layout.servable()

    return layout
