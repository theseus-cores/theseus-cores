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


#ifndef INCLUDED_THESEUS_RFNOC_DUCDDC_BLOCK_CTRL_HPP
#define INCLUDED_THESEUS_RFNOC_DUCDDC_BLOCK_CTRL_HPP

#include <uhd/rfnoc/source_block_ctrl_base.hpp>
#include <uhd/rfnoc/sink_block_ctrl_base.hpp>
#include <uhd/rfnoc/rate_node_ctrl.hpp>

namespace uhd {
	namespace theseus {

/*! \brief DUCDDC block controller
 *
 * This block provides basic M:N rate-changing operations.
 * It includes a DDC subcomponent, followed by a DUC. Both components
 * are wrapped with an axi_rate_change to handle corresponding rate changes.
 *
 * While frequency-shift logic exists in the DUC, this block is not
 * intended to perform frequency shifts (just rate changes)
 */
class UHD_RFNOC_API ducddc_block_ctrl :
    virtual public uhd::rfnoc::source_block_ctrl_base,
    virtual public uhd::rfnoc::sink_block_ctrl_base,
    virtual public uhd::rfnoc::rate_node_ctrl
{
public:
    UHD_RFNOC_BLOCK_OBJECT(ducddc_block_ctrl)

}; /* class ducddc_block_ctrl*/

} } /* namespace theseus */

#endif /* INCLUDED_THESEUS_RFNOC_DUCDDC_BLOCK_CTRL_HPP */

