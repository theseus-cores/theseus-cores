/* -*- c++ -*- */
/*
 * Copyright 2019 Theseus Cores
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

#ifndef INCLUDED_LIBUHD_RFNOC_DDC_1_TO_N_BLOCK_CTRL_HPP
#define INCLUDED_LIBUHD_RFNOC_DDC_1_TO_N_BLOCK_CTRL_HPP

#include <uhd/rfnoc/source_block_ctrl_base.hpp>
#include <uhd/rfnoc/sink_block_ctrl_base.hpp>
#include <uhd/rfnoc/rate_node_ctrl.hpp>
#include <uhd/rfnoc/scalar_node_ctrl.hpp>

namespace uhd {
    namespace theseus {

/*! \brief DDC 1-to-N block controller
 *
 * This block provides DSP for Rx operations.
 * The first channel's input is split to N output channels.
 * Output channels are independently tuneable
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

}} /* namespace uhd::theseus */

#endif /* INCLUDED_LIBUHD_RFNOC_DDC_1_TO_N_BLOCK_CTRL_HPP */
