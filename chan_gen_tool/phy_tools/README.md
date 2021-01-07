# ```phy_tools``` Highlights

## LPFilter Class

Low-Pass filter ```LPFilter``` class that provides utilities for computing filter coefficients based on Pass-band ripple (generating configurable low-pass-band ripple ```pbr```, stop-band attenuation ```sba```, and transition bandwidth ```trans_bw```.  Filter generation is constrained by the number of taps ```num_taps```, upsampling rate ```P```, downsampling rate ```M```.  The upsampling rate and downsampling rate may pad the coefficients with zeroes in order to obtain integer number of taps in the polyphase filter arms.

LPFilter class uses two filter coefficient algorithms.  For relatively small filters (less than 1000 coefficients), the Remez algorithm from ```scipy``` is used with the standard calling interface: ```scipy.signal.remez(numtaps, bands, desired, weight=None, Hz=None, type='bandpass', maxiter=25, grid_density=16, fs=None)```.

For large filters, the ```quick_gen``` option can be used to generate filter coefficients using root raised erf function to generate filter prototype less control but much faster option for very large filters.  Perfectly fine for standard low-pass filters. The code iteratively adjusts the ```K``` value until the specified cut-off frequency is obtained.  This is a link to the algorithm : http://www.mathworks.com/matlabcentral/fileexchange/15813-near-perfect-reconstruction-polyphase-filterbank.

The class can also generate Hilbert transforms and Half-band filter based on the ```hilbert``` and ```half-band``` Boolean values given during object construction.

The class also provided fixed point utilities using methods from the ```fp_utils``` module.  Coefficient and sample fixed-point representations are given by quantization coefficient tuppls ```qvec_coef``` and ```qvec``` respectively.  Quantization vector is of the formed fixed(N, F).  Where the first value indicates the total number of bits and the second number indicates the location of the fractional point.  These are the built-in fixed point utilities:


```python
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
```

```python
def gen_fixed_filter(self, desired_msb=None, coe_file=None):
    """
        Method quantizes the filter coefficients based on qvec_coef tuple.  Also using desired_msb (Desired Most Significant bit)
        to optimize the scaling of the coefficients to not induce significant DC gain of the input.  The user
        can optionally generate a .coe file to be used with Xilinx cores.
    """
    # quantize filters.
    fp_repr = self.fp_fil_repr(self.b)
    self.b_q = fp_repr.vec
    poly_fil_fi = self.fp_fil_repr(self.poly_fil)

    poly_fil_float = poly_fil_fi.vec * (2 ** -self.qvec_coef[1])

    # maximize filter output for best dynamic range
    (new_fi, msb, max_tuple) = max_filter_output(poly_fil_float, self.qvec_coef, P=self.P, input_width=self.qvec[0],
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
```

## CICDecFil

This class facilitates the design and fixed-point implementation of CIC Filters.  The transfer function of the CIC filter is given by:

```math
H(z) = H_{I}^{N}(z)H_{C}^{N}(z) = \frac{\left(1 - z^{-RM} \right)^N}{\left(1-z^{-1}\right)^N}=\left[\sum_{k=0}^{RM-1} z^{-k} \right]^N
```

where $H_{I}=\frac{1}{1-z^{-1}}$ is the interpolator transfer function and $H_C(z)=1-z^{-RM}$ is the comb filter transfer function.

The class performs all the optimal word truncations based on *Hogenauer's An Economical Class of Digital Filters for Decimation and Interpolation* paper.  There are several important methods included :

1.  ```gen_tables``` method calculates the gain parameters to maintain constant DC gain that is affected by decimation/interpolation rate.
2.  ```gen_cic_comp``` method can be used to generate a CIC compensation filter to correct the *droop* in the pass-band.
3.  ```gen_fixed_cic_comp``` converts the CIC compensation filter into a fixed-point implementation.

There are also various PSD generation and plotting utilities, including:

1.  ```plot_psd``` plots the PSD of the CIC filter.
2.  ```ret_psd``` returns the PSD of the designed CIC filter as a numpy array.
3.  ```plot_comp_psd``` plots the PSD of the corresponding CIC compensation filter.
