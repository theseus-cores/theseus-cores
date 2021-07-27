/* -*- c++ -*- */
/*
 * Copyright 2017 <+YOU OR YOUR COMPANY+>.
 *
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 *
 * This software is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this software; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#include <stdio.h>
#include <math.h>
#include <vector>
#include <uhd/convert.hpp>

#include <gnuradio/types.h>
#include <gnuradio/fft/fft.h>
#include <gnuradio/fft/fft.h>
#include <gnuradio/sys_paths.h>
#include <gnuradio/gr_complex.h>

#include <theseus/pfbchan_block_ctrl.hpp>

using namespace uhd::rfnoc;
using namespace uhd::theseus;

static const float a1 = 0.254829592;
static const float a2 = -0.284496736;
static const float a3 = 1.421413741;
static const float a4 = -1.453152027;
static const float a5 = 1.061405429;
static const float p = 0.3275911;
static const float K = 22.086093;

static const int default_taps_per_phase = 32;
static const int qvec_coef[2] = {25, 24};
static const int default_max_fft_size = 2048;
static const int qvec[2] = {16, 15};

class pfbchan_block_ctrl_impl : public pfbchan_block_ctrl
{
public:

    UHD_RFNOC_BLOCK_CONSTRUCTOR(pfbchan_block_ctrl)
    {
        _n_taps = uint32_t(user_reg_read64("RB_NUM_TAPS"));
        UHD_ASSERT_THROW(_n_taps);
        UHD_LOG_DEBUG(unique_id(), "Found PFB M/2 Channelizer max " << _n_taps << " taps");

        auto max_fft_size = user_reg_read64("RB_MAX_FFT_SIZE");
        _max_fft_size = _max_fft_size == 0x0BADC0DE0BADC0DE ? default_max_fft_size : max_fft_size;
        UHD_LOG_DEBUG(unique_id(), "Found PFB M/2 Channelizer fft size: " << _max_fft_size << "");

        auto taps_per_phase = user_reg_read64("RB_TAPS_PER_PHASE");
        _taps_per_phase = _taps_per_phase == 0x0BADC0DE0BADC0DE ? default_taps_per_phase : taps_per_phase;
        UHD_LOG_DEBUG(unique_id(), "Found PFB M/2 Channelizer taps per phase: " << _taps_per_phase << "");

        // Save the addresses so we dont need to re-query
        SR_RELOAD = uint32_t(_tree->access<size_t>(_root_path / "registers" / "sr" / "SR_RELOAD").get());
        SR_RELOAD_LAST = uint32_t(_tree->access<size_t>(_root_path / "registers" / "sr" / "SR_RELOAD_LAST").get());
        SR_CHANNELMASK = uint32_t(_tree->access<size_t>(_root_path / "registers" / "sr" / "SR_CHANNELMASK").get());
        SR_CHANNELMASK_LAST = uint32_t(_tree->access<size_t>(_root_path / "registers" / "sr" / "SR_CHANNELMASK_LAST").get());

        // Initialize the channel mask
        _n_mask = ceil(((float) _max_fft_size)/32.0);
        _channel_mask.clear();
        for (int ii = 0; ii < _n_mask; ii++) {
            _channel_mask.push_back(0xFFFFFFFF);
        }

        // Initialize subscriber for fft_size
        // Set default to 64
        _tree->access<int>(get_arg_path("fft_size/value", 0))
            .add_coerced_subscriber([this](const int value){
                this->set_taps(value);
            })
            .set(64)
        ;

        set_active_channels();
    }

    void set_active_channels(const std::vector<uint32_t> channels = std::vector<uint32_t>())
    {
        // If channels vector is empty (default), enable all channels and return
        if (channels.empty()) {
            _channel_mask.clear();
            for (int ii = 0; ii < _n_mask; ii++) {
                _channel_mask.push_back(0xFFFFFFFF);
            }
            write_channel_mask();
            return;
        }

        // First set all channels to 0
        _channel_mask.clear();
        for (int ii = 0; ii < _n_mask; ii++) {
            _channel_mask.push_back(0);
        }

        // OR the channels we want
        int chan, idx, shift;
        for (int ii = 0; ii < channels.size(); ii++){
            chan = channels[ii];
            if (chan > _n_taps) {
                UHD_LOGGER_WARNING(unique_id()) << boost::format(
                    "Cannot enable channel %d. Only %d max channels"
                ) % chan % _n_taps;
            }
            idx = floor(((float) chan)/32.0);
            shift = chan - (idx*32);
            _channel_mask[idx] |= (1 << shift);
            UHD_LOG_TRACE(unique_id(), boost::format("Enabling channel %d: (Idx %d / Shift %d)") % chan % idx % shift);
        }

        // Write channels
        write_channel_mask();
    }

private:
    size_t _n_taps;
    size_t _fft_size;
    size_t _max_fft_size;
    size_t _taps_per_phase;
    uint32_t SR_RELOAD;
    uint32_t SR_RELOAD_LAST;
    uint32_t SR_CHANNELMASK;
    uint32_t SR_CHANNELMASK_LAST;
    size_t _n_mask;
    std::vector<uint32_t> _channel_mask;

    void write_channel_mask(){
        for (int ii = 0; ii < _n_mask-1; ii++){
            UHD_LOG_DEBUG(unique_id(), boost::format("Writing Channel Mask [%d]: %08X") % ii % _channel_mask[ii]);
            sr_write(SR_CHANNELMASK, _channel_mask[ii]);
        }
        UHD_LOG_DEBUG(unique_id(), boost::format("Writing Channel Mask [%d]: %08X") % _channel_mask.size() % _channel_mask.back());
        sr_write(SR_CHANNELMASK_LAST, _channel_mask.back());
    }

    void set_taps(const int fft_size)
    {
        UHD_LOG_INFO(unique_id(), "Writing PFB Channelizer taps for " << fft_size << " channels (may take some time)...");
        gr_vector_float taps;
        tap_equation(fft_size, taps);
        int desired_msb = 40;  //TODO: replace internal constant
        gr_vector_int taps_fi;
        gen_fixed_filter(taps, fft_size, desired_msb, taps_fi);

        if (taps_fi.size() > _n_taps) {
            throw uhd::value_error(str(
                boost::format("Too many filter coefficients! Provided %d, "
                              "FIR allows %d.\n")
                % taps_fi.size() % _n_taps));
        }

        for (size_t i = 0; i < taps_fi.size(); i++) {
            if (taps_fi[i] > 16777215) {
                UHD_LOG_DEBUG(unique_id(),
                    boost::format("Coercing coeff %d: Value %d => %d") % i % taps_fi[i] % 16777215);
                taps_fi[i] = 16777215;
            }
            if (taps_fi[i] < -16777216) {
                UHD_LOG_DEBUG(unique_id(),
                    boost::format("Coercing coeff %d: Value %d => %d") % i % taps_fi[i] % -16777216);
                taps_fi[i] = -16777216;
            }
            if (taps_fi[i] > 16777215  || taps_fi[i] < -16777216) {
                throw uhd::value_error(str(
                    boost::format(
                        "Channelizer: Coefficient %d out of range! "
                        "Value %d, Allowed range [-16777216,16777215].\n")
                    % i % taps_fi[i]));
            }
        }

        if (taps_fi.size() < _n_taps) {
            taps_fi.resize(_n_taps, 0);
        }

        uint32_t num_taps_read;
        num_taps_read = user_reg_read32("RB_NUM_TAPS");

        UHD_LOG_TRACE(unique_id(), boost::format("num_taps = %d") % (int) num_taps_read);
        for (size_t i = 0; i < taps_fi.size() - 1; i++) {
            sr_write(SR_RELOAD, boost::uint32_t(taps_fi[i]));
            // UHD_LOG_TRACE(unique_id(), "tap[%d] = %d\n", (int) i, (int) boost::uint32_t(taps_fi[i]));
        }
        sr_write(SR_RELOAD_LAST, boost::uint32_t(taps_fi.back()));
        // UHD_LOG_TRACE(unique_id(), "final tap = %d\n", (int) boost::uint32_t(taps_fi.back()));
        // UHD_LOG_TRACE(unique_id(), "set_taps() done\n");

        // // Write the channel mask
        // write_channel_mask();
    }

    void
    erfc(const gr_vector_float& value, gr_vector_float& ret_val)
    {
        // save the sign of x
        gr_vector_int sign;
        int temp;
        gr_vector_float x_val;
        for (size_t i=0; i < value.size(); i++) {
            temp = ((value[i] >= 0) ? 1 : -1);
            sign.push_back(temp);
            x_val.push_back(std::abs(value[i]));
        }
        // sign = [1 if val >= 0 else -1 for val in x]
        // A&S formula 7.1.26
        for (size_t i=0; i < x_val.size(); i++) {
            float x = x_val[i];
            float t = 1.0/(1.0 + p*x);
            float y = 1.0 - (((((a5*t + a4)*t) + a3)*t + a2)*t + a1)*t*std::exp(-x*x);
            ret_val.push_back(1 - sign[i]*y);
        }
    }


    int
    nextpow2(const int value)
    {
        int n = 0;
        while ((1 << n) < value)
        {
            n++;
        }
        return n;
    }

    int
    ret_num_bitsU(const int value)
    {

        float val_new = (float) value;
        if (value == 0)
        {
            return 1;
        }

        float temp = std::ceil(std::log(std::abs(val_new + .5)) / std::log(2.));
        int ret_value = (int) temp;
        return ret_value;
    }

    int
    ret_num_bitsS(const int value)
    {
        int temp;
        if (value < 0)
        {
            temp = ret_num_bitsU(std::abs(value) - 1);
        }
        else
        {
            temp = ret_num_bitsU(value) + 1;
        }
        return temp;
    }

    void
    tap_equation(const int fft_size, gr_vector_float& ret_val)
    {
        int vec_len = _taps_per_phase * fft_size;
        gr_vector_float x_vec;
        float F_val;
        float temp;
        for (int i=0; i < vec_len; i++)
        {
            F_val = (float) i / (float) vec_len;
            temp = K * ((float) fft_size * F_val - .5);
            x_vec.push_back(temp);
        }

        gr_vector_float erfc_vals;
        erfc(x_vec, erfc_vals);

        gr_vector_float A_vals;
        for (size_t i=0; i < erfc_vals.size(); i++)
        {
            A_vals.push_back(std::sqrt(.5 * erfc_vals[i]));
        }

        int N = A_vals.size();
        // idx = np.arange(N / 2)

        for (int i=0; i < N / 2; i++)
        {
            A_vals[N - i - 1] = A_vals[1 + i];
        }
        A_vals[N / 2] = 0;

        float six_db = 10 * std::log10(.25);
        float db_diff = six_db - 10. * std::log10(.5);
        float exponent = std::pow(10., -db_diff / 10.);
        for (size_t i=0; i < A_vals.size(); i++)
        {
            A_vals[i] = std::pow(A_vals[i], exponent);
        }
        // cast A as complex.
        // gr_complex *A_complex = new gr_complex;
        // volk_32f_x2_interleave_32fc(A_complex, &A_vals[0], q_a, A_vals.size());

        int fil_size = (int) A_vals.size();
        gr::fft::fft_complex *d_fwdfft = new gr::fft::fft_complex(fil_size, false, 1);

        // copy real vector into complex vector
        // gr_vector_compex
        std::vector<gr_complex> A_comp;

        gr_complex temp_grc;
        for (int j=0; j<fil_size; j++)
        {
            temp_grc = (gr_complex) A_vals[j];
            A_comp.push_back(temp_grc);
            // printf("A_comp[%d] = %f + j%f;\n", j, temp_grc.real(), temp_grc.imag());
        }

        // copy A values into fft input buffer
        memcpy(d_fwdfft->get_inbuf(), &A_comp[0], fil_size * sizeof(gr_complex));

        d_fwdfft->execute(); // compute fwd xform

        gr_complex *b = d_fwdfft->get_outbuf();
        gr_complex *b_copy;

        // memcpy(b_copy, b, fft_size);
        // perform shift
        int shift_pt = fil_size >> 1;
        float sum_b = 0.;

        for (int i=0; i < fil_size; i++)
        {
            temp = b[(i + shift_pt) % fil_size].real();
            sum_b += temp;
            ret_val.push_back(temp);
        }

        // normalize b.
        for (int i=0; i < fil_size; i++)
        {
            ret_val[i] = ret_val[i] / sum_b;
        }
        delete d_fwdfft;
    }

    void
    gen_fixed_filter(const gr_vector_float& taps, const int fft_size, const int desired_msb, gr_vector_int& output_vector)
    {
        // float max_coeff_val = (2. **(qvec_coef[0] - 1) - 1) * (2. ** -self.qvec_coef[1])
        float max_coeff_val = (std::pow(2., (float) qvec_coef[0] - 1.) - 1.) * std::pow(2., (float)-qvec_coef[1]);
        int max_input = (int) std::pow(2., (float) qvec[0] - 1.) - 1;

        float max_value = 0;
        float temp;
        for (size_t i = 0; i < taps.size(); i++)
        {
            temp = std::fabs(taps[i]);
            if (temp > max_value)
            {
                max_value = temp;
            }
        }

        gr_vector_int taps_fi;
        float taps_gain = max_coeff_val / max_value;
        float temp_tap;
        int fixed_tap;
        for (size_t i=0; i<taps.size(); i++)
        {
            temp_tap = taps[i] * taps_gain;
            // convert to fixed point
            fixed_tap = (int) (temp_tap * std::pow(2., qvec_coef[1]));
            taps_fi.push_back(fixed_tap);
        }
        std::vector< gr_vector_int > poly_fi;
        gr_vector_int path_gain;
        // create polyphase implementation of taps.
        for (int i=0; i < fft_size; i++)
        {
            int tap_offset = 0;
            gr_vector_int temp_row;
            int temp_gain = 0;
            for (int j=0; j < _taps_per_phase; j++)
            {
                int index = i + tap_offset;
                temp_gain += taps_fi[index];
                temp_row.push_back(taps_fi[index]);
                tap_offset += fft_size;
            }
            poly_fi.push_back(temp_row);
            path_gain.push_back(std::abs(temp_gain));
        }

        //
        std::vector<int>::const_iterator s_gain;
        s_gain = std::max_element(path_gain.begin(), path_gain.end());
        // // compute noise and signal gain.
        int gain_msb = nextpow2(*s_gain);
        //
        // gain_msb = self.nextpow2(s_gain)
        int max_coef_val = (int) std::pow(2.,  (float) gain_msb - 1.);
        float in_use = (float) *s_gain / (float) max_coef_val;
        // // print(np.max(s_gain), np.max(max_input))
        int int_max_value = *s_gain * max_input;
        int num_bits = ret_num_bitsS(int_max_value);
        // // print(num_bits)
        int msb = num_bits - 1;
        if (in_use <= .9)
        {
            // note we are scaling down here hence the - 1
            msb = msb - 1;
            float delta_gain = .5 * ((float) max_coef_val / (float) *s_gain);
            // scale polyphase filter.
            for (int i=0; i < fft_size; i++)
            {
                for (int j=0; j < _taps_per_phase; j++)
                {
                    poly_fi[i][j] = (int) ((float) poly_fi[i][j] * delta_gain);
                }
            }
        }
        //
        if (desired_msb < msb)
        {
            int diff = msb - desired_msb;
            for (int i=0; i < fft_size; i++)
            {
                for (int j=0; j < _taps_per_phase; j++)
                {
                    poly_fi[i][j] = poly_fi[i][j] >> diff;
                }
            }
        }

        // reshape poly_fi into single vector with padding.
        int pad = _max_fft_size - fft_size;
        // // print("msb = {}".format(msb))
        // // taps_fi = np.reshape(poly_fil, (1, -1), order='F')
        // poly_fil = poly_fil.astype(np.int32)
        //
        for (int j=0; j < _taps_per_phase; j++)
        {
            for (int i=0; i < fft_size; i++)
            {
                output_vector.push_back(poly_fi[i][j]);
            }
            for (int m=0; m < pad; m++)
            {
                output_vector.push_back(0);
            }
        }
    }

};

UHD_RFNOC_BLOCK_REGISTER(pfbchan_block_ctrl, "pfbchannelizer");
