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


#ifndef INCLUDED_THESEUS_RFNOC_PFBCHAN_BLOCK_CTRL_HPP
#define INCLUDED_THESEUS_RFNOC_PFBCHAN_BLOCK_CTRL_HPP

#include <uhd/rfnoc/source_block_ctrl_base.hpp>
#include <uhd/rfnoc/sink_block_ctrl_base.hpp>

namespace uhd {
    namespace theseus {

/*! \brief Block controller for the PFB M/2 Channelizer RFNoC block.
 *
 */
class UHD_RFNOC_API pfbchan_block_ctrl :
    public uhd::rfnoc::source_block_ctrl_base,
    public uhd::rfnoc::sink_block_ctrl_base
{
public:
    UHD_RFNOC_BLOCK_OBJECT(pfbchan_block_ctrl)

    virtual void set_active_channels(const std::vector<uint32_t> channels = std::vector<uint32_t>()) = 0;

}; /* class pfbchan_block_ctrl*/

}} /* namespace uhd::rfnoc */

#endif /* INCLUDED_THESEUS_RFNOC_PFBCHAN_BLOCK_CTRL_HPP */
