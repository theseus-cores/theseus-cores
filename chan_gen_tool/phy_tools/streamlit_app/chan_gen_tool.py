import streamlit as st
import pandas as pd
import numpy as np
from phy_tools.channelizer import Channelizer, gen_exp_shifter, gen_input_buffer, gen_circ_buffer, gen_pfb, gen_downselect
from phy_tools.channelizer import gen_final_cnt, gen_output_buffer, populate_fil_table, gen_mux, gen_mask_files, gen_tones_vec
from phy_tools.channelizer import gen_chan_top, gen_chan_tb
import phy_tools.fp_utils as fp_utils
from gen_buffers import gen_inbuff_logic, gen_inbuff1x_logic, gen_circbuff_logic, gen_reader, gen_writer
import phy_tools.adv_pfb as adv_filter
from phy_tools.plotly_utils import plotly_time_helper
from phy_tools.gen_xfft import gen_xfft_xci
from phy_tools.plt_utils import find_pwr
import SessionState

import pandas as pd
from collections import OrderedDict

from shutil import copyfile, make_archive
import base64

import os

def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, _, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


def get_zip_download_link(path, file_name):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    # b64 = base64.b64encode(csv.encode()).decode()  # some strings <-> bytes conversions necessary here
    # href = f'<a href="data:file/zip;base64,{b64}">Download zip file</a>'
    with open(file_name, 'rb') as fin:
        bytes_var = fin.read()
        b64 = base64.b64encode(bytes_var).decode()
    return f'<a href="data:file/zip;base64,{b64}" download="{file_name}">Download zip file</a>'

QVEC = (16, 15)
QVEC_COEF = (25, 24)
DESIRED_MSB = 40
IP_PATH = './tmp/'
AVG_LEN = 256

st.title('Channelizer Verilog Generation Tool')

fft_list = tuple(2 ** np.arange(3, 17))
db_list = tuple(np.arange(-60, -300, -20))
gen_2X = False

# fc_scale = st.
max_fft = st.sidebar.selectbox("Maximum Number of Channels", fft_list, index=3)
taps_per_phase = st.sidebar.number_input("Taps Per Arm of PFB", value=16, min_value=12, max_value=64)
# st.sidebar.slider("Taps Per Arm of the PFB", 12, 64, 16, 1)
chan_type = st.sidebar.radio("Channelizer Type", ('M', 'M/2'))
# opt_taps = st.checkbox("Optimize Filter Taps")
min_db = st.sidebar.selectbox("Plot Min DB", db_list, index=3)
fc_scale = st.sidebar.number_input("Cut off Frequency (Proportional to Bin Width)", value=.8, min_value=0.5, max_value=1.0)
tbw_scale = st.sidebar.number_input("Transition Bandwidth (Proportional to Bin Width) - M/2 Designs should relax specs", value=.5, min_value=0.20, max_value=1.0)

K_terms = OrderedDict([(8, 8.363989999999983), (16, 8.363989999999983), (32, 8.363989999999983),
                       (64, 8.363989999999983), (128, 8.363989999999983), (256, 8.363989999999983), (512, 8.363989999999983),
                       (1024, 8.363989999999983), (2048, 8.363989999999983)])
msb_terms = OrderedDict([(8, 39), (16, 39), (32, 39), (64, 39), (128, 39), (256, 39), (512, 39), (1024, 39), (2048, 39)])
offset_terms = OrderedDict([(8, .5), (16, .5), (32, .5), (64, .5), (128, .5), (256, .5), (512, 0.5), (1024, 0.5), (2048, 0.5)])

session_state = SessionState.get(K_terms=K_terms, msb_terms=msb_terms, offset_terms=offset_terms)

def update_chan_obj(K_terms, offset_terms, msb_terms, taps_per_phase, gen_2X, max_fft):
    return Channelizer(M=max_fft, taps_per_phase=taps_per_phase, gen_2X=gen_2X, qvec=QVEC,
                       qvec_coef=QVEC_COEF, fc_scale=fc_scale, tbw_scale=tbw_scale, taps=None, 
                       K_terms=K_terms, offset_terms=offset_terms,
                       desired_msb=msb_terms[max_fft])

    # remove all .v and .xci files from IP_PATH
def remove_files(path):
    ip_files = os.listdir(path)
    for item in ip_files:
        if item.endswith(".v") or item.endswith(".xci") or item.endswith(".sv"):
            os.remove(os.path.join(path, item))

if chan_type == 'M/2':
    gen_2X = True
    chan_str = 'M_2'
else:
    gen_2X = False
    chan_str = 'M'

st.sidebar.markdown("""
<style>
.small-font {
    font-size:100px !important;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown('<p class="big-font">Click Optimize Filter after updating filter settings</p>', unsafe_allow_html=True)

opt_button = st.sidebar.button('Optimize Filter')
gen_button = st.sidebar.button('Generate Verilog')

def opt_params(max_fft, taps_per_phase, gen_2X, fc_scale, tbw_scale):
    # st.write("Optimizing Taps = {}".format(opt_button))
    return populate_fil_table(start_size=max_fft, end_size=max_fft, fc_scale=fc_scale, taps_per_phase=taps_per_phase, gen_2X=gen_2X, tbw_scale=tbw_scale)

if opt_button:
    K_terms, msb_terms, offset_terms = opt_params(max_fft, taps_per_phase, gen_2X, fc_scale, tbw_scale)
    session_state.K_terms = K_terms
    session_state.msb_terms = msb_terms
    session_state.offset_terms = offset_terms


# @st.cache
def update_psd(K_terms, offset_terms, msb_terms, taps_per_phase, gen_2X, max_fft):
    chan_obj = update_chan_obj(K_terms, offset_terms, msb_terms, taps_per_phase, gen_2X, max_fft)
    resp, omega = chan_obj.gen_psd(fft_size=32768*2)
    data_dict = {'Omega': omega, 'PSD':resp, 'sig_idx': 0}
    return pd.DataFrame(data_dict)

# @st.cache
def update_stem(K_terms, offset_terms, msb_terms, taps_per_phase, gen_2X, max_fft):
    chan_obj = update_chan_obj(K_terms, offset_terms, msb_terms, taps_per_phase, gen_2X, max_fft)
    taps = chan_obj.taps
    data_dict = {'Taps': taps, 'sig_idx': 0}
    return pd.DataFrame(data_dict)

if gen_button:
    # check if IP_PATH exists -- create it if it doesn't
    if not os.path.exists(IP_PATH):
        os.makedirs(IP_PATH)
    remove_files(IP_PATH)           
    chan_obj = update_chan_obj(K_terms, offset_terms, msb_terms, taps_per_phase, gen_2X, max_fft)
    print("===========================================================")
    print("Generate K {}, Mmax {}".format(chan_obj.K, chan_obj.Mmax))
    print("===========================================================")
    sample_fi = fp_utils.ret_dec_fi(0, qvec=QVEC, overflow='wrap', signed=1)
    sample_fi.gen_full_data()
    gen_output_buffer(max_fft, IP_PATH)
    shift_name = gen_exp_shifter(chan_obj, AVG_LEN, sample_fi=sample_fi, path=IP_PATH)
    gen_input_buffer(max_fft, IP_PATH)
    gen_circ_buffer(max_fft, IP_PATH)
    pfb_name = gen_pfb(chan_obj, path=IP_PATH)
    gen_mux(max_fft, IP_PATH)
    gen_downselect(max_fft, IP_PATH)
    gen_final_cnt(IP_PATH)
    fft_name = gen_xfft_xci(IP_PATH, max_fft)
    tones = gen_mask_files([max_fft], percent_active=.25, path=IP_PATH)
    gen_tones_vec(tones[0], M=max_fft, offset=.1 / max_fft, path=IP_PATH)

    gen_chan_top(IP_PATH, chan_obj, shift_name, pfb_name, fft_name)
    gen_chan_tb(IP_PATH, chan_obj, len(tones[0]))
    adv_filter.gen_sim_vh(IP_PATH)
    if chan_obj.gen_2X:
        gen_inbuff_logic(IP_PATH)
        gen_circbuff_logic(IP_PATH)
        # copyfile('./circ_buffer.v', IP_PATH + '/circ_buffer.v')
        # copyfile('./input_buffer.v', IP_PATH + '/input_buffer.v')
    else:
        gen_inbuff1x_logic(IP_PATH)
        # copyfile('./input_buffer_1x.v', IP_PATH + '/input_buffer_1x.v')

    gen_reader(IP_PATH)
    gen_writer(IP_PATH)
    # copyfile('./grc_word_reader.sv', IP_PATH + '/grc_word_reader.sv')
    # copyfile('./grc_word_writer.sv', IP_PATH + '/grc_word_writer.sv')

    file_name = 'verilog_{}_{}_{}'.format(max_fft, taps_per_phase, chan_str)
    full_name = IP_PATH + '/' + file_name
    make_archive(file_name, 'zip', IP_PATH)
    st.sidebar.markdown(get_zip_download_link('./', file_name + '.zip'), unsafe_allow_html=True)
else:
    pass
    # st.write('New Channelizer')


psd_df = update_psd(session_state.K_terms, session_state.offset_terms, session_state.msb_terms, taps_per_phase, gen_2X, max_fft)
try:

    minx = -4. / max_fft
    maxx = 4. / max_fft
    pwr_pt = -3.01

    binl = -1. / max_fft
    binr = 1. / max_fft
    bin_width = binr - binl
    # xlabel = st.latex(r'''\pi\ rads/sec''')
    # 'Discrete Freq.'
    fig = plotly_time_helper(psd_df, opacity=[.8] * 2, miny=min_db, maxy=10, index_str='sig_idx', x_name='Omega', y_name='PSD',
                             labelsize=20, titlesize=30, xlabel='\u03A0 rads/sec', ylabel='dB', 
                             subplot_title=('Fil PSD',), minx=minx, maxx=maxx) #, pwr_pts=-3.01)


    resp = psd_df['PSD'].to_numpy()
    
    lidx, ridx = find_pwr(resp, pwr_pt)
    resp_offset_lidx = int(ridx + (ridx - lidx) * (tbw_scale / fc_scale))
    resp_offset_ridx = int(lidx - (ridx - lidx) * (tbw_scale / fc_scale))

    stop_atten = np.max(resp[resp_offset_lidx:])
    # print(resp[resp_offset:])
    x_left = psd_df['Omega'].iloc[lidx]
    x_right = psd_df['Omega'].iloc[ridx]
    # ann_x = .20 * (maxx - minx) + minx
    fig.add_shape(type="line", x0=x_left, y0=-1000, x1=x_left, y1=1000,
                  line=dict(color="forestgreen", width=2, dash='dash'))
    fig.add_shape(type="line", x0=x_right, y0=-1000, x1=x_right, y1=1000,
                  line=dict(color="forestgreen", width=2, dash='dash'))
    tbw_left = psd_df['Omega'].iloc[resp_offset_lidx]
    tbw_right = psd_df['Omega'].iloc[resp_offset_ridx]
    trans_bw = tbw_right - x_right 
    fig.add_shape(type="line", x0=tbw_left, y0=-1000, x1=tbw_left, y1=1000,
                  line=dict(color="magenta", width=2, dash='dash'))
    fig.add_shape(type="line", x0=tbw_right, y0=-1000, x1=tbw_right,
                  y1=1000, line=dict(color="magenta", width=2, dash='dash'))
    fig.add_shape(type="line", x0=binl, y0=-1000, x1=binl,
                  y1=1000, line=dict(color="darkgreen", width=2, dash='dash'))
    fig.add_shape(type="line", x0=binr, y0=-1000, x1=binr,
                  y1=1000, line=dict(color="darkgreen", width=2, dash='dash'))
    fig.add_shape(type="line", x0=2*binl, y0=-1000, x1=2*binl,
                  y1=1000, line=dict(color="crimson", width=2, dash='dash'))
    fig.add_shape(type="line", x0=2*binr, y0=-1000, x1=2*binr,
                  y1=1000, line=dict(color="crimson", width=2, dash='dash'))
    fig.add_shape(type="line", x0=-100, y0=stop_atten, x1=100, y1=stop_atten, line=dict(color="crimson",width=2, dash='dash'))

    offset = int((10 - min_db) * .02)
    fig.add_annotation(
        x=0,
        y=stop_atten + 40 + offset,
        xref="x",
        yref="y",
        text="1 Bin Width",
        font=dict(
            family='sans serif',
            size=13,
            color="darkgreen"
        ),
        align='center',
        showarrow=False,
    )
    fig.add_annotation(
        x=binl,
        y=stop_atten + 40,
        xref="x",
        yref="y",
        text="",
        ax = 0,
        ay = stop_atten + 40,
        axref = "x", 
        ayref = "y",
        arrowhead = 3,
        arrowwidth = 1.5,
        arrowcolor="darkgreen",
        opacity=1.0,
    )
    fig.add_annotation(
        x=binr,
        y=stop_atten + 40,
        xref="x",
        yref="y",
        ax = .03 * binl,
        ay = stop_atten + 40,
        text = "",
        axref = "x", 
        ayref = "y",
        arrowhead = 3,
        arrowwidth = 1.5,
        arrowcolor="darkgreen",
        opacity=1.0,
    )

    fig.add_annotation(
        x=0,
        y=stop_atten + 30 + offset,
        xref="x",
        yref="y",
        text="2X Bin Width",
        font=dict(
            family='sans serif',
            size=13,
            color="crimson"
        ),
        align='center',
        showarrow=False,
    )
    fig.add_annotation(
        x=2*binl,
        y=stop_atten + 30,
        xref="x",
        yref="y",
        text="",

        ax = 0,
        ay = stop_atten + 30,
        axref = "x", 
        ayref = "y",
        arrowhead = 3,
        arrowwidth = 1.5,
        arrowcolor="crimson",
        opacity=1.,
    )
    fig.add_annotation(
        x=2*binr,
        y=stop_atten + 30,
        xref="x",
        yref="y",
        text="",
        ax = .02 * binl * 2,
        ay = stop_atten + 30,
        axref = "x", 
        ayref = "y",
        arrowhead = 3,
        arrowwidth = 1.5,
        arrowcolor="crimson",
        opacity=1.,
    )

    fig.add_annotation(
        x=.02, #x_left,
        y=.98,
        xref="paper",
        yref="paper",
        # text="3 dB Freqs = {:.5f}, {:.5f} \u03A0 rads/sec <br> Trans BW = {:.5f} \u03A0 rads/sec <br> Stopband Atten = {:.0f} dB <br> Bin Width = {:.5f} \u03A0 rads/sec <br> 2X Bin Width = {:.5f} \u03A0 rads/sec".format(
        #     x_left, x_right, trans_bw, stop_atten, bin_width, 2*bin_width),
        text="3 dB Freqs = {:.5f}, {:.5f} \u03A0 rads/sec <br> Trans BW = {:.5f} \u03A0 rads/sec <br> Stopband Atten = {:.0f} dB".format(
            x_left, x_right, trans_bw, stop_atten),
        showarrow=False,
        font=dict(
            family='sans serif', 
            size=13,
            color="#ffffff"
        ),
        align="center",
        # arrowhead=2,
        # arrowsize=1,
        # arrowwidth=2,
        # arrowcolor="#636363",
        # ax=20,
        # ay=-30,
        bordercolor="#c7c7c7",
        borderwidth=2,
        borderpad=4,
        bgcolor="#ff7f0e",
        opacity=0.7
    )
    fig.update_shapes(dict(xref='x', yref='y'))
    # fig.add_vline(x=psd_df['Omega'].iloc[lidx], line_width=3, line_dash="dash",
    #               line_color="green", row=0, col=0)
    # fig.add_vline(x=psd_df['Omega'].iloc[ridx], line_width=3, line_dash="dash",
    #               line_color="green", row=0, col=0)
# pwr_pts = -3.01,
    # find 3 dB cutoff .
    # print(psd_df.columns)
    # print(psd_df.PSD)
    
    
    fig.update_layout(autosize=False, width=900, height=550, margin=dict(l=20, r=40, b=40, t=70))
    st.plotly_chart(fig)
except:
    pass

stem_df = update_stem(session_state.K_terms, session_state.offset_terms,
                      session_state.msb_terms, taps_per_phase, gen_2X, max_fft)
try:
    fig = plotly_time_helper(stem_df, opacity=[.8] * 2, index_str='sig_idx', y_name='Taps', stem_plot=True, miny=-.5,
                                labelsize=20, titlesize=30, xlabel='Tap Index', ylabel='Amplitude', subplot_title=('Taps',))

    fig.update_layout(autosize=False, width=900, height=350, margin=dict(l=20, r=40, b=40, t=70))
    st.plotly_chart(fig)
except:
    pass


