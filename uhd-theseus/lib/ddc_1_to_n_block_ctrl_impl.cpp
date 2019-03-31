//
// Copyright 2016-2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#include <theseus/ddc_1_to_n_block_ctrl.hpp>
#include <uhd/utils/log.hpp>
#include <uhd/convert.hpp>
#include <uhd/types/ranges.hpp>
#include <boost/math/special_functions/round.hpp>
#include <boost/math/special_functions/sign.hpp>
#include <cmath>

static const int32_t MAX_FREQ_WORD = boost::numeric::bounds<int32_t>::highest();
static const int32_t MIN_FREQ_WORD = boost::numeric::bounds<int32_t>::lowest();

using namespace uhd::rfnoc;
using namespace theseus;

class ddc_1_to_n_block_ctrl_impl : public ddc_1_to_n_block_ctrl
{
public:
    UHD_RFNOC_BLOCK_CONSTRUCTOR(ddc_1_to_n_block_ctrl)
        , _fpga_compat(user_reg_read64(RB_REG_COMPAT_NUM))
        , _num_halfbands(narrow_cast<size_t>(
                    user_reg_read64(RB_REG_NUM_HALFBANDS)))
        , _cic_max_decim(narrow_cast<size_t>(
                    user_reg_read64(RB_REG_CIC_MAX_DECIM)))
    {
        UHD_LOG_DEBUG(unique_id(),
            "Loading DDC 1-to-N with " << get_num_halfbands() << " halfbands and "
            "max CIC decimation " << get_cic_max_decim()
        );

        // TODO: assert_fpga_compat is currently hidden behind uhdlib
        //       --> Replace this function or expose to uhd API?
        // uhd::assert_fpga_compat(
        //     MAJOR_COMP, MINOR_COMP,
        //     _fpga_compat,
        //     "DDC", "DDC",
        //     false /* Let it slide if minors mismatch */
        // );

        _tree->access<double>(get_arg_path("input_rate/value", 0))
            .add_coerced_subscriber([this](const double rate){
                this->set_input_rate(rate, 0);
            })
        ;

        // Argument/prop tree hooks
        for (size_t chan = 0; chan < get_output_ports().size(); chan++) {
            const double default_freq = get_arg<double>("freq", chan);
            _tree->access<double>(get_arg_path("freq/value", chan))
                .set_coercer([this, chan](const double value){
                    return this->set_freq(value, chan);
                })
                .set(default_freq);
            ;
            const double default_output_rate =
                get_arg<double>("output_rate", chan);
            _tree->access<double>(get_arg_path("output_rate/value", chan))
                .set_coercer([this, chan](const double value){
                    return this->set_output_rate(value, chan);
                })
                .set(default_output_rate)
            ;
            _tree->access<uhd::time_spec_t>("time/cmd")
                .add_coerced_subscriber([this, chan](const uhd::time_spec_t time_spec){
                    this->set_command_time(time_spec, chan);
                })
            ;
            if (_tree->exists("tick_rate")) {
                const double tick_rate =
                    _tree->access<double>("tick_rate").get();
                set_command_tick_rate(tick_rate, chan);
                _tree->access<double>("tick_rate")
                    .add_coerced_subscriber([this, chan](const double rate){
                        this->set_command_tick_rate(rate, chan);
                    })
                ;
            }

            // Rate 1:1 by default
            sr_write("N", 1, chan);
            sr_write("M", 1, chan);
            sr_write("CONFIG", 1, chan); // Enable clear EOB
        }
    } // end ctor

    virtual ~ddc_1_to_n_block_ctrl_impl() {}

    double get_output_scale_factor(size_t port=ANY_PORT)
    {
        port = port == ANY_PORT ? 0 : port;
        if (not (_rx_streamer_active.count(port) and _rx_streamer_active.at(port))) {
            return SCALE_UNDEFINED;
        }
        return get_arg<double>("scalar_correction", port);
    }

    double get_input_samp_rate(size_t port=ANY_PORT)
    {
        port = port == ANY_PORT ? 0 : port;
        if (not (_tx_streamer_active.count(port) and _tx_streamer_active.at(port))) {
            return RATE_UNDEFINED;
        }
        return get_arg<double>("input_rate", port);
    }

    double get_output_samp_rate(size_t port=ANY_PORT)
    {
        if (port == ANY_PORT) {
            port = 0;
            for (size_t i = 0; i < get_input_ports().size(); i++) {
                if (_rx_streamer_active.count(i) and _rx_streamer_active.at(i)) {
                    port = i;
                    break;
                }
            }
        }

        // Wait, what? If this seems out of place to you, you're right. However,
        // we need a function call that is called when the graph is complete,
        // but streaming is not yet set up.
        if (_tree->exists("tick_rate")) {
            const double tick_rate = _tree->access<double>("tick_rate").get();
            set_command_tick_rate(tick_rate, port);
        }

        if (not (_rx_streamer_active.count(port) and _rx_streamer_active.at(port))) {
            return RATE_UNDEFINED;
        }
        return get_arg<double>("output_rate", port);
    }

    void issue_stream_cmd(
            const uhd::stream_cmd_t &stream_cmd_,
            const size_t chan
    ) {
        UHD_RFNOC_BLOCK_TRACE() << "ddc_1_to_n_block_ctrl_base::issue_stream_cmd()" ;

        size_t upstream_chan = 0;

        if (list_upstream_nodes().count(upstream_chan) == 0) {
            UHD_LOGGER_INFO("RFNOC") << "No upstream blocks." ;
            return;
        }

        uhd::stream_cmd_t stream_cmd = stream_cmd_;
        if (stream_cmd.stream_mode == uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_DONE or
            stream_cmd.stream_mode == uhd::stream_cmd_t::STREAM_MODE_NUM_SAMPS_AND_MORE) {
            size_t decimation = get_arg<double>("input_rate", upstream_chan) / get_arg<double>("output_rate", chan);
            stream_cmd.num_samps *= decimation;
        }

        // Disable or enable output channel based on stream mode
        if (stream_cmd.stream_mode == uhd::stream_cmd_t::STREAM_MODE_STOP_CONTINUOUS) {
            set_arg<int>("enable", 0, chan);
        } else {
            set_arg<int>("enable", 1, chan);
        }

        source_node_ctrl::sptr this_upstream_block_ctrl =
                boost::dynamic_pointer_cast<source_node_ctrl>(list_upstream_nodes().at(upstream_chan).lock());
        if (this_upstream_block_ctrl) {
            this_upstream_block_ctrl->issue_stream_cmd(
                    stream_cmd,
                    get_upstream_port(upstream_chan)
            );
        }
    }

private:
    static constexpr size_t MAJOR_COMP = 2;
    static constexpr size_t MINOR_COMP = 0;
    static constexpr size_t RB_REG_COMPAT_NUM = 0;
    static constexpr size_t RB_REG_NUM_HALFBANDS = 1;
    static constexpr size_t RB_REG_CIC_MAX_DECIM = 2;

    const uint64_t _fpga_compat;
    const size_t _num_halfbands;
    const size_t _cic_max_decim;

    void get_freq_and_freq_word(
            const double requested_freq,
            const double tick_rate,
            double &actual_freq,
            int32_t &freq_word
    ) {
        // Pulled in from uhdlib/usrp/cores/dsp_core_utils.hpp => Not exposed :(

        //correct for outside of rate (wrap around)
        double freq = std::fmod(requested_freq, tick_rate);
        if (std::abs(freq) > tick_rate/2.0)
            freq -= boost::math::sign(freq) * tick_rate;

        //confirm that the target frequency is within range of the CORDIC
        UHD_ASSERT_THROW(std::abs(freq) <= tick_rate/2.0);

        /* Now calculate the frequency word. It is possible for this calculation
         * to cause an overflow. As the requested DSP frequency approaches the
         * master clock rate, that ratio multiplied by the scaling factor (2^32)
         * will generally overflow within the last few kHz of tunable range.
         * Thus, we check to see if the operation will overflow before doing it,
         * and if it will, we set it to the integer min or max of this system.
         */
        freq_word = 0;

        static const double scale_factor = std::pow(2.0, 32);
        if ((freq / tick_rate) >= (MAX_FREQ_WORD / scale_factor)) {
            /* Operation would have caused a positive overflow of int32. */
            freq_word = MAX_FREQ_WORD;

        } else if ((freq / tick_rate) <= (MIN_FREQ_WORD / scale_factor)) {
            /* Operation would have caused a negative overflow of int32. */
            freq_word = MIN_FREQ_WORD;

        } else {
            /* The operation is safe. Perform normally. */
            freq_word = int32_t(boost::math::round((freq / tick_rate) * scale_factor));
        }

        actual_freq = (double(freq_word) / scale_factor) * tick_rate;
    }

    template <class T>
    T ceil_log2(T num){
        // Pulled in from uhdlib/utils/math.hpp
        return std::ceil(std::log(num)/std::log(T(2)));
    }

    template <class T, class U>
    inline constexpr T narrow_cast(U&& u) noexcept
    {
        return static_cast<T>(std::forward<U>(u));
    }

    //! Set the DDS frequency shift the signal to \p requested_freq
    double set_freq(const double requested_freq, const size_t chan)
    {
        const double input_rate = get_arg<double>("input_rate", 0);
        double actual_freq;
        int32_t freq_word;
        get_freq_and_freq_word(requested_freq, input_rate, actual_freq, freq_word);
        sr_write("DDS_FREQ", uint32_t(freq_word), chan);
        return actual_freq;
    }

    //! Return a range of valid frequencies the DDS can tune to
    uhd::meta_range_t get_freq_range(void)
    {
        const double input_rate = get_arg<double>("input_rate", 0);
        return uhd::meta_range_t(
                -input_rate/2,
                +input_rate/2,
                input_rate/std::pow(2.0, 32)
        );
    }

    uhd::meta_range_t get_output_rates(void)
    {
        uhd::meta_range_t range;
        const double input_rate = get_arg<double>("input_rate", 0);
        for (int hb = _num_halfbands; hb >= 0; hb--) {
            const size_t decim_offset = _cic_max_decim<<(hb-1);
            for(size_t decim = _cic_max_decim; decim > 0; decim--) {
                const size_t hb_cic_decim =  decim*(1<<hb);
                if(hb == 0 || hb_cic_decim > decim_offset) {
                    range.push_back(uhd::range_t(input_rate/hb_cic_decim));
                }
            }
        }
        return range;
    }

    double set_output_rate(const int requested_rate, const size_t chan)
    {
        const double input_rate = get_arg<double>("input_rate", 0);
        const size_t decim_rate =
            boost::math::iround(input_rate/this->get_output_rates().clip(requested_rate, true));
        size_t decim = decim_rate;
        // The FPGA knows which halfbands to enable for any given value of hb_enable.
        uint32_t hb_enable = 0;
        while ((decim % 2 == 0) and hb_enable < _num_halfbands) {
            hb_enable++;
            decim /= 2;
        }
        UHD_ASSERT_THROW(hb_enable <= _num_halfbands);
        UHD_ASSERT_THROW(decim > 0 and decim <= _cic_max_decim);
        // What we can't cover with halfbands, we do with the CIC
        sr_write("DECIM_WORD", (hb_enable << 8) | (decim & 0xff), chan);

        // Rate change = M/N
        sr_write("N", std::pow(2.0, double(hb_enable)) * (decim & 0xff), chan);
        const auto noc_id = _tree->access<uint64_t>(_root_path / "noc_id").get();
        // FIXME this should be a rb reg in the FPGA, not based on a hard-coded
        // Noc-ID
        if (noc_id == 0xDDC5E15CA7000000) {
            UHD_LOG_DEBUG("DDC1TON", "EISCAT DDC! Assuming real inputs.");
            sr_write("M", 2, chan);
        } else {
            sr_write("M", 1, chan);
        }

        if (decim > 1 and hb_enable == 0) {
            UHD_LOGGER_WARNING("RFNOC") << boost::format(
                "The requested decimation is odd; the user should expect passband CIC rolloff.\n"
                "Select an even decimation to ensure that a halfband filter is enabled.\n"
                "Decimations factorable by 4 will enable 2 halfbands, those factorable by 8 will enable 3 halfbands.\n"
                "decimation = dsp_rate/samp_rate -> %d = (%f MHz)/(%f MHz)"
            ) % decim_rate % (input_rate/1e6) % (requested_rate/1e6);
        }

        // Calculate algorithmic gain of CIC for a given decimation.
        // For Ettus CIC R=decim, M=1, N=4. Gain = (R * M) ^ N
        const double rate_pow = std::pow(double(decim & 0xff), 4);
        // Calculate compensation gain values for algorithmic gain of DDS and CIC taking into account
        // gain compensation blocks already hardcoded in place in DDC (that provide simple 1/2^n gain compensation).
        static const double DDS_GAIN = 2.0;
        //
        // The polar rotation of [I,Q] = [1,1] by Pi/8 also yields max magnitude of SQRT(2) (~1.4142) however
        // input to the DDS thats outside the unit circle can only be sourced from a saturated RF frontend.
        // To provide additional dynamic range head room accordingly using scale factor applied at egress from DDC would
        // cost us small signal performance, thus we do no provide compensation gain for a saturated front end and allow
        // the signal to clip in the H/W as needed. If we wished to avoid the signal clipping in these circumstances then adjust code to read:
        const double scaling_adjustment =
            std::pow(2, ceil_log2(rate_pow))/(DDS_GAIN*rate_pow);
        update_scalar(scaling_adjustment, chan);
        return input_rate/decim_rate;
    }

    //! Set frequency and decimation again
    void set_input_rate(const double /* rate */, const size_t chan)
    {
        if (chan != 0){
            return;
        }

        for (size_t ochan = 0; ochan < get_output_ports().size(); ochan++) {
            const double desired_freq = _tree->access<double>(get_arg_path("freq", ochan) / "value").get_desired();
            set_arg<double>("freq", desired_freq, ochan);
            const double desired_output_rate = _tree->access<double>(get_arg_path("output_rate", ochan) / "value").get_desired();
            set_arg<double>("output_rate", desired_output_rate, ochan);
        }
    }

    // Calculate compensation gain values for algorithmic gain of DDS and CIC taking into account
    // gain compensation blocks already hardcoded in place in DDC (that provide simple 1/2^n gain compensation).
    // Further more factor in OTW format which adds further gain factor to weight output samples correctly.
    void update_scalar(const double scalar, const size_t chan)
    {
        const double target_scalar = (1 << 15) * scalar;
        const int32_t actual_scalar = boost::math::iround(target_scalar);
        // Calculate the error introduced by using integer representation for the scalar, can be corrected in host later.
        const double scalar_correction =
            target_scalar / actual_scalar / double(1 << 15) // Rounding error, normalized to 1.0
            * get_arg<double>("fullscale"); // Scaling requested by host
        set_arg<double>("scalar_correction", scalar_correction, chan);
        // Write DDC with scaling correction for CIC and DDS that maximizes dynamic range in 32/16/12/8bits.
        sr_write("SCALE_IQ", actual_scalar, chan);
    }

    //! Get cached value of FPGA compat number
    uint64_t get_fpga_compat() const
    {
        return _fpga_compat;
    }

    //! Get cached value of _num_halfbands
    size_t get_num_halfbands() const
    {
        return _num_halfbands;
    }

    //! Get cached value of _cic_max_decim readback
    size_t get_cic_max_decim() const
    {
        return _cic_max_decim;
    }
};

UHD_RFNOC_BLOCK_REGISTER(ddc_1_to_n_block_ctrl, "DDC1TON");
