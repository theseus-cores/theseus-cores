# -*- coding: utf-8 -*-
"""
Created on Tue Jun 14 17:01:28 2016

@author: phil
"""
import copy
import fp_utils as fp_utils
import numpy as np
import re
import scipy as sp
import scipy.signal as signal
import struct
from itertools import cycle, count
from scipy.special import erfc

mod_dict_default = {'shape_filt': 'rrcosine', 'mod_type': 'qpsk', 'beta': .2, }
mod_dict = {'bpsk': 1, 'qpsk': 2, 'qam16': 4, 'qam64': 6}


class RingArray(np.ndarray):

    def __getslice__(self, lidx, ridx):
        '''
            Overloaded getslice method.
        '''
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
        '''
            Overloaded getslice method.
        '''
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

def str_find_all(str_input, match_val):
    """
        Function returns indexes of all occurrences of matchVal inside of str_input
    """
    return [m.start() for m in re.finditer(match_val, str_input)]

def calc_pad(ref_len, non_pad_len):
    remainder = non_pad_len % ref_len
    pad = 0
    if remainder:
        pad = ref_len - remainder

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
    # fig, ax = plt.subplots(subplot_kw=dict(polar=True))
    kw = dict(arrowstyle="->", color='k')

    if arrowprops:
        kw.update(arrowprops)

    [ax.annotate("", xy=(angle, radius), xytext=(0, 0), arrowprops=kw) for angle, radius in zip(angles, radii)]

    ax.set_ylim(0, np.max(radii))

    return ax


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
    mult_val = 0.
    if fil_val is not None:
        mult_val = fil_val
    if extend is True:
        mult_val = in_vec[0]

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

    mult_val = 0.
    if fil_val is not None:
        mult_val = fil_val
    if extend is True:
        mult_val = in_vec[-1]

    if np.iscomplexobj(in_vec):
        pad = mult_val * np.ones((num_samps,), dtype=np.complex)
    else:
        pad = mult_val * np.ones((num_samps,))

    return np.concatenate((in_vec, pad))


def hyst_trigger(on_thresh, off_thresh, input_sig, initial=False):
    """
        Function generates a boolean output signal based on two thresholds.
        Once a signal crosses the on_thresh value the output is '1'.
        The output remains a '1' until the input signal falls below the
        off_thresh value.

    """
    zip_val = zip(input_sig, cycle(on_thresh))

    hi = [True if (val >= thresh) else False for (val, thresh) in zip_val]
    zip_val2 = zip(input_sig, hi, cycle(off_thresh))
    lo_or_hi = [True if (val <= thresh or hi_val) else False for (val, hi_val, thresh) in zip_val2]

    ind = np.nonzero(lo_or_hi)[0]
    cnt = np.cumsum(lo_or_hi)

    ret_val = [hi[ind[val - 1]] for val in cnt]

    return ret_val


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
    ii = np.arange(np.size(np.array(in_vec)))

    # if modulation type is not given then simply assume a complex rotator
    output = in_vec * np.exp(1j * (np.pi * rot_factor * ii + phase))

    return output

def gen_comp_tone(num_samps, dfreq, phase=0):
    dc_term = [1.] * num_samps
    return complex_rot(dc_term, dfreq, phase)


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

    snr = 10.**(snr / 10.)  # converted into linear units

    sig_pwr_i = np.mean(np.abs(in_vec.real)**2)
    sig_pwr_q = np.mean(np.abs(in_vec.imag)**2)

    # Determine the energy per bit normalized to Nyquist rate
    no_i = sig_pwr_i / snr
    # this is the noise power or the variance of the noise
    no_q = sig_pwr_q / snr

    # ipdb.set_trace()
    vec_shape = np.shape(in_vec)
    # If there is no imag component then dealing with real Single sided
    # variance of Gaussian noise = No/2.
    if np.isrealobj(in_vec):
        # include scaling for full power.
        # factor of 2 is since BW is measured between -1 and 1.
        # so for full bandwidth -- the digital BW = 2.
        # rng(10) # make noise draws predictable.
        np.random.seed(seed_i)
        Noise = np.sqrt(no_i) * np.random.standard_normal(vec_shape)
        # Noise = No.*randn(1,length(in_vec))
        sig_wnoise = in_vec + Noise
        complex_noise = Noise

    else:
        # create complex Gaussian noise with variance = No/2
        # rng(10) # make noise draws predictable.
        np.random.seed(seed_i)
        noise_i = np.sqrt(no_i) * np.random.standard_normal(vec_shape)
        np.random.seed(seed_q)
        noise_q = np.sqrt(no_q) * np.random.standard_normal(vec_shape)

        # Scale for full noise power
        complex_noise = noise_i + 1j * noise_q

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

    try:
        new_a_val = []
        f_str = '<'
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
            f.seek(offset * iq_word_len, 0)
            d_vec = np.fromfile(f, dtype=format_new, count=num_samps)
            # ensure that even number of samples.
            trunc = len(d_vec) % 2
            if trunc == 1:
                d_vec = d_vec[:-1]

        if q_first:
            return d_vec[1::2] + 1.j * d_vec[0::2]
        else:
            return d_vec[::2] + 1.j * d_vec[1::2]

    except:
        print("ERROR : Invalid File name")
        return -1


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
