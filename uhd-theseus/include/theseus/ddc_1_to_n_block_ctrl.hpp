//
// Copyright 2016 Ettus Research
// Copyright 2018 Ettus Research, a National Instruments Company
//
// SPDX-License-Identifier: GPL-3.0-or-later
//

#ifndef INCLUDED_LIBUHD_RFNOC_DDC_1_TO_N_BLOCK_CTRL_HPP
#define INCLUDED_LIBUHD_RFNOC_DDC_1_TO_N_BLOCK_CTRL_HPP

#include <uhd/rfnoc/source_block_ctrl_base.hpp>
#include <uhd/rfnoc/sink_block_ctrl_base.hpp>
#include <uhd/rfnoc/rate_node_ctrl.hpp>
#include <uhd/rfnoc/scalar_node_ctrl.hpp>

namespace theseus {

/*! \brief DDC 1-to-N block controller
 *
 * This block provides DSP for Rx operations.
 * Its main component is a DDC chain, which can decimate over a wide range
 * of decimation rates (using a CIC and halfband filters).
 *
 * It also includes a CORDIC component to shift signals in frequency.
 */
class UHD_RFNOC_API ddc_1_to_n_block_ctrl :
    public uhd::rfnoc::source_block_ctrl_base,
    public uhd::rfnoc::sink_block_ctrl_base,
    public uhd::rfnoc::rate_node_ctrl,
    public uhd::rfnoc::scalar_node_ctrl
{
public:
    UHD_RFNOC_BLOCK_OBJECT(ddc_1_to_n_block_ctrl)

}; /* class ddc_1_to_n_block_ctrl*/

} /* namespace theseus */

#endif /* INCLUDED_LIBUHD_RFNOC_DDC_1_TO_N_BLOCK_CTRL_HPP */
