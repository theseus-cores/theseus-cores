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


#ifndef INCLUDED_THESEUS_PFBCHAN_H
#define INCLUDED_THESEUS_PFBCHAN_H

#include <theseus/api.h>
#include <ettus/device3.h>
#include <ettus/rfnoc_block.h>

namespace gr {
  namespace theseus {

    /*!
     * \brief <+description of block+>
     * \ingroup pfb_channelizer
     *
     */
    class THESEUS_API pfbchan : virtual public gr::ettus::rfnoc_block
    {
     public:
      typedef boost::shared_ptr<pfbchan> sptr;

      /*!
       * \brief Return a shared_ptr to a new instance of pfb_channelizer::pfbchan.
       *
       * To avoid accidental use of raw pointers, pfb_channelizer::pfbchan's
       * constructor is in a private implementation
       * class. pfb_channelizer::pfbchan::make is the public interface for
       * creating new instances.
       */
      static sptr make(
        const gr::ettus::device3::sptr &dev,
        const int block_select=-1,
        const int device_select=-1,
        const int num_channels=8,
        const std::vector<uint32_t> active_channels=std::vector<uint32_t>()
        );

      virtual void set_channels(uint32_t num_channels=8, std::vector<uint32_t> active_channels=std::vector<uint32_t>()) = 0;
    };
  } // namespace pfb_channelizer
} // namespace gr

#endif /* INCLUDED_THESEUS_PFBCHAN_H */
