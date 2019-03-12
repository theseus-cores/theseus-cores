#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

@author: phil
"""

import numpy as np
import binascii

# from cStringIO import StringIO
from io import StringIO
import copy
from mpmath import mp


"""
    Quantization vector is of the formed fixed(N, F).  Where the first value indicates the
    total number of bits and the second number indicates the location of the fractional point.
"""

__version__ = "1.1"

def bit_count(val):
    """
        Fast way to count 1's in a 64 bit integer.  Based on Hamming weight
    """
    val = val - ((val >> 1) & 0x5555555555555555)
    val = (val & 0x3333333333333333) + ((val >> 2) & 0x3333333333333333)
    return (((val + (val >> 4)) & 0xF0F0F0F0F0F0F0F) * 0x101010101010101) >> 56

def r_shift(bin_str, new_val):
    """
        Function performs a right shift of a binary string.  Placing the new
        value into the MSB position.
    """
    offset = bin_str.find('b') + 1
    new_val = str(new_val) + bin_str[offset:-1]
    if (offset != -1):
        new_val = '0b' + new_val

    return new_val


def l_shift(bin_str, new_val):
    """
        Function performs a left shift of a binary string.  Placing the new
        value into the LSB position.
    """
    offset = bin_str.find('b') + 1
    new_val = bin_str[offset + 1:] + str(new_val)
    if (offset != -1):
        new_val = '0b' + new_val

    return new_val

def lappend(bin_str, str_append):
    """
        Function left appends a binary string with string specified by
        string append.
    """
    offset_a = bin_str.find('b') + 1
    offset_b = str_append.find('b') + 1

    new_val = str_append[offset_b:] + bin_str[offset_a:]
    if ((offset_a != -1) | (offset_b != -1)):
        new_val = '0b' + new_val

    return new_val

def lappend_udec(int_val, bit_val, num_bits):
    """
        Function left appends int_val with bit_val.  bit_val is assumed
        to be one bit.  num_bits is the number of bits to represent
        unsigned integer int_val
    """
    temp = np.floor(int_val / 2) + ((1 << (num_bits - 1)) * bit_val)
    return temp.astype(np.int)


def collapse_byte(values):
    """
        Function collapses a bit stream into unsigned integer representing bytes.
    """
    temp = 0
    byte_val = []
    for i, val in enumerate(values):
        idx = 7 - (i % 8)
        temp += val << idx
        if idx == 0:
            byte_val.append(temp)
            temp = 0

    return byte_val

def uint_to_fp(vec, qvec=(16, 15), signed=0, overflow='wrap'):

    max_int = int(comp_max_value(qvec, signed) * 2 ** qvec[1])
    min_int = max_int + 1

    vec_fp = []
    for value in vec:
        # value = float(value)
        if value > max_int and signed == 1:
            # negative value
            value = -1 * (min_int - (value % min_int))
        vec_fp.append(value * (2 ** -qvec[1]))

    return ret_fi(vec_fp, qvec=qvec, overflow=overflow, signed=signed)


class range_fi(object):
    def __init__(self, min_int, max_int, step):
        self.max = max_int
        self.min = min_int
        self.step = step


class Fi(object):

    def __init__(self, vec, qvec=(16, 15), overflow='wrap', signed=1):
        """
            Simple fixed integer object to hold parameters related to a \
            fixed point object.
        """
        self.vec = vec
        self.qvec = qvec
        self.overflow = overflow
        self.signed = signed
        self.comp = False
        if np.iscomplexobj(vec):
            self.comp = True

    @property
    def bin(self):
        """
            Converts vector to 2's complement binary values.
        """
        num_chars = self.qvec[0]
        if self.comp:
            real_vals = [dec_to_bin(np.real(value).astype(np.int), num_chars) for value in self.vec]
            imag_vals = [dec_to_bin(np.imag(value).astype(np.int), num_chars) for value in self.vec]
            return [real_val + (",j" + imag_val) for (real_val, imag_val) in zip(real_vals, imag_vals)]
        else:
            return [dec_to_bin(value, num_chars) for value in self.vec]

    @property
    def udec(self):
        """
            Returns unsigned decimal integer of the vector
        """

        values = copy.deepcopy(self.vec)
        # min_int = int(comp_min_value(self.qvec, 0) * 2 ** self.qvec[1])
        max_int = int(comp_max_value(self.qvec, 0) * 2 ** self.qvec[1])
        num_chars = self.qvec[0]
        if self.comp:
            real_vals = np.real(values)
            neg_idx = (real_vals < 0)
            real_vals[neg_idx] += (max_int + 1)
            imag_vals = np.imag(values)
            neg_idx = (imag_vals < 0)
            imag_vals[neg_idx] += (max_int + 1)

            return (real_vals + 1j * imag_vals)
        else:
            real_vals = np.real(values)
            neg_idx = (real_vals < 0)
            real_vals[neg_idx] += (max_int + 1)
            return real_vals

    @property
    def hex(self):
        """
            Converts vector to 2's complement hexadecimal values.
        """
        num_chars = int(np.ceil(self.qvec[0] / 4.))
        if self.comp:
            real_vals = dec_to_hex(np.real(self.vec).astype(np.int), num_chars)
            imag_vals = dec_to_hex(np.imag(self.vec).astype(np.int), num_chars)
            return [real_val + (",j" + imag_val) for (real_val, imag_val) in zip(real_vals, imag_vals)]
        else:
            return dec_to_hex(self.vec, num_chars)

    @property
    def len(self):
        return (len(self.vec))

    # overriding built in len term.
    def __len__(self):
        return (len(self.vec))

    # def __getslice__(self, lidx, ridx):
    #     """
    #         Overloaded getslice method.
    #     """
    #     self.vec = self.vec[lidx, ridx]
    #     # return self
    #     #
    # def __getitem__(self, index)


    @property
    def float(self):
        return (self.vec * 2. ** (-self.qvec[1]))

    @property
    def max_float(self):
        return np.max(self.float)

    @property
    def max_udec(self):
        return np.max(self.udec)

    @property
    def min_udec(self):
        return np.min(self.udec)

    @property
    def min_float(self):
        return np.min(self.float)

    @property
    def max(self):
        return np.max(self.vec)

    @property
    def min(self):
        return np.min(self.vec)

    @property
    def range(self):
        min_int = comp_min_value(self.qvec, self.signed)
        max_int = comp_max_value(self.qvec, self.signed)
        step = comp_slope_value(self.qvec)

        return range_fi(min_int, max_int, step)


    def __getslice__(self, i, j):
        return self.vec[i:j]

    def gen_full_data(self):
        range_obj = self.range

        vec =  np.arange(range_obj.min, range_obj.max, range_obj.step)

        self.vec = (vec * (2 ** self.qvec[1])).astype(np.int)

    def __repr__(self):
        c_str = StringIO()
        c_str.write('    qvec : {}\n'.format(self.qvec))
        c_str.write('overflow : {}\n'.format(self.overflow))
        c_str.write('  signed : {}\n'.format(self.signed))
        # , self.__class__.__name__, self.block_name
        c_str.seek(0)

        return c_str.getvalue()


def coe_write(fi_obj, radix=16, file_name=None, filter_type=False):
    """
        Function takes a fixed point vector as input and generates a Xilinx
        compatibily .coe file for ROM/RAM initialization.

        ==========
        Parameters
        ==========

            * fi_obj : fixed integer object
                Fixed Point object generated by fixed point toolbox.
            * radix : int (16)
                Radix used for formatting .coe file.
            * file_name : str
                File name used for outputting file to correct location
                and name.
        =======
        Returns
        =======

            Correctly formatted .coe file for use by Xilinx coregenerator
            modules.
    """
    fi_vec = fi_obj.vec
    signed = fi_obj.signed
    word_length = fi_obj.qvec[0]
    fraction_length = fi_obj.qvec[1]

    assert(file_name is not None), 'User must specify File Name'
    # find last forward slash
    idx = str(file_name[::-1]).find('/')
    if (idx == -1):
        idx = 0
    else:
        idx = len(file_name) - 1 - idx

    if (str(file_name).find('.', idx) == -1):
        file_name = file_name + '.coe'

    str_val = 'Radix must of the following: 2, 8, 10, 16'
    assert(radix == 16 or radix == 10 or radix == 8 or radix == 2), str_val

    with open(file_name, 'w') as f:
        f.write('; Initialization File  : \n')
        if signed:
            f.write('; Signed Fixed Point\n')
        else:
            f.write('; Unsigned Fixed Point\n')

        # skip = 2
        f.write('; Word Length : %d\n' % word_length)
        f.write('; Fraction Length : %d\n' % fraction_length)
        f.write('; Number of Entries : %d\n\n' % len(fi_vec))
        if (filter_type is False):
            f.write('memory_initialization_radix = ' + str(radix) + ';\n')
            f.write('memory_initialization_vector = ' + '\n')
        else:
            f.write('Radix = ' + str(radix) + ';\n')
            f.write('Coefficient_Width = %d;\n' % word_length)
            f.write('CoefData = \n')

        mod_fac = (1 << word_length)

        if radix == 16:
            num_chars = int(np.ceil(word_length / 4.))
            format_str = '0{}X'.format(num_chars)
        elif radix == 8:
            num_chars = int(np.ceil(word_length / 3.))
            format_str = '0{}o'.format(num_chars)
        elif radix == 2:
            format_str = '0{}b'.format(word_length)
        for (ii, val) in enumerate(fi_vec):
            if radix == 16:
                temp = (val + mod_fac) % mod_fac
                temp = format(temp, format_str)
            elif radix == 8:
                temp = (val + mod_fac) % mod_fac
                temp = format(temp, format_str)
            elif radix == 10:
                temp = str(val)
            elif radix == 2:
                temp = (val + mod_fac) % mod_fac
                temp = format(temp, format_str)

            f.write(temp)
            if ii == (len(fi_vec) - 1):
                f.write(';')
            else:
                f.write(',\n')


def comp_frac_width(value, word_width, signed=0):
    """
        Function computes the optimal fractional width given the vector and the word_width
    """
    shift_val = -1
    temp_val = value
    bit_shift = ret_num_bitsU(np.max(np.abs(temp_val)))
    while bit_shift < 0:
        temp_val = temp_val * 2
        shift_val += 1
        bit_shift = ret_num_bitsU(np.max(np.abs(temp_val)))
    if (bit_shift >= shift_val):
        shift_val = -bit_shift
    frac_width = word_width - signed + shift_val
    return frac_width

def comp_min_value(qvec, signed=0):
    """
        Computes the mimimum real value given the fixed point representation
    """
    word_width = qvec[0]
    frac_width = qvec[1]
    min_val = -1 * 2.**(word_width - signed) / (2.**frac_width)
    if signed == 0:
        min_val = 0

    return min_val


def comp_max_value(qvec, signed=0):
    """
        Computes maximum real value given the fixed point representation, qvec.
    """
    word_width = qvec[0]
    frac_width = qvec[1]
    max_val = 2.**(word_width - signed) / (2.**frac_width)
    max_val -= 2.**(-frac_width)

    return max_val


def comp_slope_value(qvec):
    """
        Returns the fixed point increment per unit increase in binary number.
    """
    frac_width = qvec[1]
    return 2.**(-frac_width)


def comp_range_vec(qvec, signed=0):
    """
        Computes range of real values for a given fixed point representation.
    """
    min_val = comp_min_value(qvec, signed)
    max_val = comp_max_value(qvec, signed)
    slope = comp_slope_value(qvec)
    return np.arange(min_val, max_val + slope, slope)


def hex_to_ascii(hex_val):
    """
        Converts hex value to ascii string.
    """
    offset = hex_val.find('x') + 1
    return binascii.unhexlify(hex_val[offset:])  # .decode('hex')


def str_to_dec(str_val, base=2, signed_val=True):
    """
        Method converts numerical string to unsigned decimal representation
        Can take single value or vector; complex or real.  Base 2 : binary
        base 8 : octal, base 16 : hexadecimal
    """
    if (not isinstance(str_val, np.ndarray)):
        val_int = np.atleast_1d(str_val)
    else:
        val_int = str_val.copy()

    fl = val_int.flat
    sub_idx = fl.coords

    complex_vals = (val_int[sub_idx][-1] == 'j')

    if complex_vals:
        ret_vals = np.zeros(val_int.shape, dtype=np.complex)
    else:
        ret_vals = np.zeros(val_int.shape, dtype=int)

    num_chars = len(val_int[sub_idx])
    if complex_vals:
        num_chars = (len(str_val[sub_idx]) - 4) / 2
        imag_lidx = num_chars + 3
        imag_ridx = len(str_val[sub_idx]) - 1

    if signed_val is False:
        if complex_vals:
            for [sub_idx, value] in np.ndenumerate(val_int):
                ret_vals[sub_idx] = np.int(value[0:num_chars], base)
                if complex_vals:
                    ret_vals[sub_idx] += 1j * np.int(value[imag_lidx:imag_ridx], base)
        else:
            for [sub_idx, value] in np.ndenumerate(val_int):
                ret_vals[sub_idx] = np.int(value, base)
    else:
        offset = str.find(val_int[sub_idx], 'b') + 1
        corr_fac = 2 ** (num_chars - offset)
        if complex_vals:
            offsetI = imag_lidx + 2
        for (sub_idx, value) in np.ndenumerate(val_int):
            ret_vals[sub_idx] = np.int(value[0:num_chars], base)
            if (value[offset] == '1'):
                ret_vals[sub_idx] -= corr_fac
            if complex_vals:
                temp = np.int(value[imag_lidx:imag_ridx], base)
                if (value[offsetI] == '1'):
                    temp -= corr_fac
                ret_vals[sub_idx] += 1j * temp

    return ret_vals[0] if (ret_vals.size == 1) else ret_vals


def dec_to_list(dec_val, num_bits):
    """
        Converts decimal value to list of 1's and 0's.
    """
    bin_str = '{0:b}'.format(dec_val)
    bin_str = str.zfill(bin_str, num_bits)
    ret_list = []
    for bin_val in bin_str:
        ret_list.append(int(bin_val))

    return ret_list


def bin_array_to_uint(data_vec):
    """
        Converts 1 / 0 array to unsigned integer array representing
        constellation indices.

        Each binary vector that is to be converted to an unsigned number
        lies on each row of the vector.
    """
    data_int = np.atleast_2d(data_vec)
    num_bits = np.size(data_int, 1)
    mp.prec = num_bits

    ret_val = []
    for vec in data_int:
        sum_value = 0
        for idx, bin_bit in enumerate(reversed(vec)):
            if bin_bit == 1:
                sum_value += int(mp.power(2, idx))
        ret_val.append(sum_value)

    if len(ret_val) == 1:
        ret_val = ret_val[0]

    return ret_val


def bin_to_udec(bin_vec):

    func = lambda x: int(x, 2)
    vfunc = np.vectorize(func)
    return vfunc(bin_vec)


def nextpow2(i):
    """
        Find 2^n that is equal to or greater than.
    """
    n = 0
    while (2**n) < i:
        n += 1
    return n

def ret_bits_comb(value):
    """
        Helper function returns number of bits to represent number of combinations, value.
    """
    return int(np.ceil(np.log2(value)))

def ret_num_bitsU(value):
    """
        Function returns required number of bits for unsigned binary
        representation.
    """
    val_new = np.floor(value)

    if value == 0:
        return 1

    temp = np.ceil(np.log2(np.abs(val_new + .5)))
    return temp.astype(np.int)


def ret_num_bitsS(value):
    """
        Function returns required number of bits for 2's
        complement representation.
    """
    if value < 0:
        temp = ret_num_bitsU(np.abs(value) - 1)
    else:
        temp = ret_num_bitsU(value) + 1
    return temp


def bin_to_bool(string):
    """
        Helper function converts a binary string into a boolean array
    """
    # return map(lambda x: x**2, range(10)
    bool_array = np.zeros((len(string),), dtype=np.bool)
    for (ii, val) in enumerate(string):
        bool_array[ii] = True if (val == '1') else False

    return bool_array


def init_str_array(num_chars, array_shape, compType=False):
    """
        Initializes a string array.
    """
    init_str = ' ' * num_chars
    if len(array_shape) == 1:
        ret_str = [init_str] * array_shape[0]
    else:
        ret_str = [[init_str] * array_shape[1] for x in range(array_shape[0])]
    return np.array(ret_str)


def flip_bin_vec(bin_str):
    """
        Function flip bit order of binary string.  Assumed to
    """
    offset = bin_str.find('b') + 1
    num_bits = len(bin_str) - offset

    ret_val = bin_str[:offset]
    for ii in range(num_bits):
        ret_val += bin_str[offset + num_bits - ii - 1]

    return ret_val


def xor_vec(in_val, mask_vec):
    """
        Returns the XOR of bits from the result of masking bin_vec with the
        mask vector mask_vec.
    """
    and_val = in_val & mask_vec
    return (bin(and_val).count('1') % 2)


def xor_list(prim_list, sec_list):
    """
        Returns the XOR of bits from the primary and secondary lists.

    """
    ret_list = []
    for (x_val, y_val) in zip(prim_list, sec_list):
        ret_list.append(x_val ^ y_val)

    return ret_list


def parity_list(list_val, init_value=0):
    """
        Helper function computes parity on list of 1's and 0's
    """
    curr_value = init_value
    for value in list_val:
        curr_value = curr_value ^ value

    return curr_value

def list_to_bin(list_val):
    """
        Converts a 1,0 list and or ndarray to a binary string.
    """
    vec = np.atleast_2d(np.array(list_val))
    str_vec = '0b'

    str_list = []
    for val in vec:
        str_vec = '0b'
        for str_val in val:
            str_vec += bin(str_val)[2]
        str_list.append(str_vec)

    return str_list


def list_to_oct(list_val, num_chars=None):
    """
        Converts list of 1's and 0's to unsigned hex string.
    """

    num_base_chars = int(np.ceil(len(list_val) / 3.))

    num_bits = 3 * num_base_chars
    if num_chars is not None:
        num_bits = num_chars * 3

    remain = len(list_val) % num_bits
    pad = np.sign(remain) * num_bits - remain

    list_val = [0] * pad + list_val
    list_sh = np.reshape(list_val, (-1, 3))

    ret_str = ''
    for vec in list_sh:
        dec_val = list_to_uint(vec)
        oct_val = oct(dec_val)[1:]
        # ipdb.set_trace()
        ret_str += oct_val

    ret_str = ret_str[-num_base_chars:]
    return ret_str


def list_to_hex(list_val, num_chars=None):
    """
        Converts list of 1's and 0's to unsigned hex string.
    """

    num_base_chars = int(np.ceil(len(list_val) / 4.))

    num_bits = 4 * num_base_chars
    if num_chars is not None:
        num_bits = num_chars * 4

    remain = len(list_val) % num_bits
    pad = np.sign(remain) * num_bits - remain

    list_val = [0] * pad + list_val
    list_sh = np.reshape(list_val, (-1, 4))

    ret_str = ''
    for vec in list_sh:
        dec_val = list_to_uint(vec)
        hex_val = hex(dec_val)[2:]
        ret_str += hex_val

    ret_str = ret_str[-num_base_chars:]
    return '0x' + ret_str



def list_to_uint(list_val):
    """
        Converts list of 1's and 0's to unsigned integer.
    """

    list_val = np.atleast_2d(np.array(list_val))
    bin_vec = list_to_bin(list_val)
    ret_list = [int(vec, 2) for vec in bin_vec]

    if len(ret_list) > 1:
        return ret_list
    else:
        return ret_list[0]


def hex_to_list_vec(hex_str, num_bits=None):
    """
        Converts hex string to list of 1's and 0's.
    """
    def hex_conv(hex_str):
        offset = hex_str.find('x') + 1
        hex_str = hex_str[offset:]
        ret_list = []
        for hex_val in hex_str:
            # pdb.set_trace()
            temp = bin(int(hex_val, 16))[2:].zfill(4)
            temp_bits = [int(bin_val) for bin_val in temp]
            ret_list.extend(temp_bits)
        if num_bits is not None:
            pad = num_bits - len(ret_list)
            return [0] * pad + ret_list
        else:
            return ret_list

    # if single hex string
    if isinstance(hex_str, str):
        return hex_conv(hex_str)
    else:
        # if list of hex strings
        ret_list = [hex_conv(hex_string) for hex_string in hex_str]
        return ret_list


def uint_to_list(dec_val, num_bits=8):
    """
        Converts hex string to list of 1's and 0's.
    """

    format_str = '0{}b'.format(num_bits)
    ret_val = format(dec_val, format_str)
    temp = [int(bit) for bit in ret_val]  # str_val in ret_val for bit in str_val]
    return temp


def dec_to_ubin(dec_val, num_bits):

    format_str = '0{}b'.format(num_bits)
    return format(dec_val, format_str)


def dec_to_bin(dec_val, num_bits):
    """
        Helper function convert decimal value to signed 2's complement binary value.
    """
    mod_fac = (1 << num_bits)
    format_str = '0{}b'.format(num_bits)
    return format((dec_val + mod_fac) % mod_fac, format_str) # for value in dec_vals]


def dec_to_hex(dec_vals, num_chars):

    if type(dec_vals) is not list and type(dec_vals) is not np.ndarray:
        dec_vals = [dec_vals]

    mod_fac = (1 << num_chars * 4)

    format_str = '0{}X'.format(num_chars)
    ret_val = [format((value + mod_fac) % mod_fac, format_str) for value in dec_vals]

    return ret_val

def oct_to_udec(oct_str):
    """
        Function returns decimal equivalent to octal value.
    """
    return int(oct_str, 8)


def hex_to_ubin(hex_str, num_bits):
    """
        Method converts hex string (ndarray) to binary string.
    """
    format_str = '0{}b'.format(num_bits)

    return format(int(hex_str, 16), format_str)

def oct_to_ubin(oct_str, num_bits):
    """
        Method converts hex string (ndarray) to binary string.
    """

    format_str = '0{}b'.format(num_bits)
    return format(int(oct_str, 8), format_str)


def oct_to_list(oct_str, num_bits):
    udec_val = oct_to_udec(oct_str)
    return uint_to_list(udec_val, num_bits)


def hex_to_udec(hex_str):
    """
        Function returns decimal equivalent to hexadecimal value
    """

    return int(hex_str, 16)


def hex_to_dec(hex_str):
    """
        Function returns decimal equivalent to hexadecimal value
    """
    return str_to_dec(hex_str, 16, signed_val=True)






# def comp_frac_width(value, word_width, signed=0):
#
#     shift_val = -1
#     temp_val = value
#     bit_shift = ret_num_bitsU(np.max(np.abs(temp_val)))
#     while bit_shift < 0:
#         temp_val = temp_val * 2
#         shift_val += 1
#         bit_shift = ret_num_bitsU(np.max(np.abs(temp_val)))
#     if (bit_shift >= shift_val):
#         shift_val = -bit_shift
#     frac_width = word_width - signed + shift_val
#     return frac_width


def ret_fi(vec, qvec=(16, 15), overflow='wrap', signed=1):
    """
        Helper function returns a fixed integer vector to the user.
        If input is complex it will automatically convert real and
        imaginary components separately.
    """
    if np.iscomplexobj(vec):
        real_temp = ret_dec_fi(vec.real, qvec, overflow, signed)
        comp_temp = ret_dec_fi(vec.imag, qvec, overflow, signed)

        vec = real_temp.vec + 1j * comp_temp.vec
        fi_obj = Fi(vec, qvec, overflow, signed)
        return fi_obj
    else:
        return ret_dec_fi(vec, qvec, overflow, signed)

def ret_flat_fi(vec, qvec=(16, 15), overflow='wrap', signed=1):

    new_qvec = (qvec[0] * 2, 0)
    if np.iscomplexobj(vec):
        real_temp = ret_dec_fi(vec.real, qvec, overflow, signed)
        comp_temp = ret_dec_fi(vec.imag, qvec, overflow, signed)

        new_vec = (real_temp.udec << qvec[0]) + comp_temp.udec
        return Fi(new_vec, new_qvec, overflow, signed=0)
    else:
        return ret_dec_fi(vec, qvec, overflow, signed)

def ret_dec_fi(vec, qvec=(16, 15), overflow='wrap', signed=1):
    """
        Helper function returns a fixed integer vector to the user.
        Assumes signed input.
    """
    # word_width = qvec[0]
    fraction_width = qvec[1]
    temp = np.around(np.array(vec) * 2.**fraction_width, decimals=0)
    temp = np.atleast_1d(temp)

    min_int = comp_min_value(qvec, signed)
    min_int *= 2. ** fraction_width
    max_int = comp_max_value(qvec, signed)
    max_int *= 2. ** fraction_width

    if signed == 0 and str.lower(overflow) == 'wrap':
        # this is so negative values and wrap appropriately on the
        # asymmetric positive number line.
        min_int = max_int + 1

    if str.lower(overflow) == 'saturate':
        idx = (temp >= max_int)
        if np.any(idx):
            # check for wrapping here.
            temp[idx] = max_int
        idx = (temp <= min_int)
        if (np.any(idx)):
            temp[idx] = min_int

    if str.lower(overflow) == 'wrap':
        idx = (temp > max_int)
        if np.any(idx):
            # check for wrapping here.
            temp[idx] = temp[idx] % max_int
        idx = (temp < min_int)
        if np.any(idx):
            temp[idx] = temp[idx] % min_int

    temp = temp.flatten()
    # create fi_obj and return it to the user
    fi_obj = Fi(temp.astype(np.int), qvec, overflow, signed)

    return fi_obj


def concat_fi(first_fi, second_fi):
    """
        Function does a bitwise concatenation of 2 fi objects.
        Treats both of the them as unsigned -- returns unsigned object that
        is of the quantization type [total_ bits 0].  Only
        format that makes sense.  Uses fi_math of first_fi object.
    """
    nbits0 = first_fi.qvec[0]
    nbits1 = second_fi.qvec[0]
    total_bits = nbits0 + nbits1

    new_dec = (first_fi.udec << nbits0) + second_fi.udec

    return ret_dec_fi(new_dec, (total_bits, 0), signed=0)


def stack_fi(first_fi, second_fi):
    """
        Function does a stacking of 2 fi objects..
        Treats both of the them as unsigned -- returns unsigned object that
        Both fi object must have the same word lengths.
        Only format that makes sense.  Uses fi_math of first_fi object.
    """
    nbits0 = first_fi.qvec[0]
    nbits1 = second_fi.qvec[0]
    assert (nbits0 == nbits1), 'Both fi objects must have the same word length'

    vals0 = first_fi.udec
    vals1 = second_fi.udec
    new_dec = np.concatenate((vals0, vals1))

    return ret_dec_fi(new_dec, (nbits0, 0), signed=0)


# def add_fi(first_term, sec_term):
#     """
#         Method is used to perform a trial addition of two fi objects.
#         Simply uses the fi_math and numeric_types to generate a new fi object
#         with 0 as its data.
#
#         Commonly used to determine Integer and Fractional bit widths at the
#         output of a fixed point multiplier.
#
#         ==========
#         Parameters
#         ==========
#
#             * first_term : (fi Object):
#                 First fi object used in the multiplication check.
#             * sec_term : (fi Object)
#                 Second fi object used in the multiplication check
#
#         =======
#         Returns
#         =======
#
#             * out : (fi Object):
#                 Returns new fi object -- output of multiplying first and
#                 second input terms.
#     """
#     if (not isinstance(sec_term, Fi)):
#         sec_term = ret_dec_fi(sec_term)
#     if (not isinstance(first_term, Fi)):
#         first_term = ret_dec_fi(first_term)
#
#     num_type_first = first_term.numeric_type
#     num_type_sec = sec_term.numeric_type
#
#     first_term = fi(0, numeric_type=num_type_first, sign_val=0)
#     sec_term = fi(0, numeric_type=num_type_sec, sign_val=0)
#
#     new_obj = first_term + sec_term
#     return new_obj
#
#
def mult_fi(first_term, sec_term, use_data=False):
    """
        Method is used to perform a trial multiplication of two fi objects.
        Simply uses the fi_math and numeric_types to generate a new fi object
        with 0 as its data.

        Commonly used to determine Integer and Fractional bit widths at the
        output of a fixed point multiplier.

        ==========
        Parameters
        ==========

            * first_term : (fi Object):
                First fi object used in the multiplication check.
            * sec_term : (fi Object)
                Second fi object used in the multiplication check

        =======
        Returns
        =======

            * out : (fi Object):
                Returns new fi object -- output of multiplying first and
                second input terms.
    """
    if (not isinstance(sec_term, Fi)):
        sec_term = ret_dec_fi(sec_term)
    if (not isinstance(first_term, Fi)):
        first_term = ret_dec_fi(first_term)

    frac_length = first_term.qvec[1] + sec_term.qvec[1]
    signed = first_term.signed or sec_term.signed
    vec = 0.
    if first_term.comp or sec_term.comp:
        vec = 0. + 0.*1j
    if use_data:
        fp_step = first_term.range.step * sec_term.range.step
        mat = (first_term.max_float * sec_term.max_float, first_term.min_float * sec_term.max_float,
               first_term.max_float * sec_term.min_float, first_term.min_float * sec_term.min_float)

        if first_term.comp or sec_term.comp:
            mat = (np.max(np.abs(mat)), -np.max(np.abs(mat)))

        max_data = np.max(mat)
        min_data = np.min(mat)
        if signed:
            whole_bits = np.max((ret_num_bitsS(max_data), ret_num_bitsS(min_data)))
        else:
            whole_bits = np.max((ret_num_bitsU(max_data), ret_num_bitsU(min_data)))

        word_length = whole_bits + frac_length

    else:
        word_length = first_term.qvec[0] + sec_term.qvec[0]

        if first_term.comp and sec_term.comp:
            word_length += 1

    qvec_new = (word_length, frac_length)
    return ret_fi(vec, qvec=qvec_new, overflow='wrap', signed=signed)


if __name__ == "__main__":

    list_val = [1, 1, 1, 1]
    print(list_to_uint(list_val))
