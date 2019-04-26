/* -*- c++ -*- */
/*
 * Copyright 2018 Ettus Research
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

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <gnuradio/io_signature.h>
#include "pfbchan_impl.h"
#include <gnuradio/block.h>

namespace gr {
  namespace theseus {

    pfbchan::sptr
    pfbchan::make(
        const gr::ettus::device3::sptr &dev,
        const int block_select,
        const int device_select
    )
    {
        return gnuradio::get_initial_sptr(
            new pfbchan_impl(
                dev,
                block_select,
                device_select
            )
        );
    }

    /*
     * The private constructor
     */
    pfbchan_impl::pfbchan_impl(
        const gr::ettus::device3::sptr &dev,
        const int block_select,
        const int device_select
    )
      : gr::ettus::rfnoc_block("pfbchannelizer"),
        gr::ettus::rfnoc_block_impl(
            dev,
            gr::ettus::rfnoc_block_impl::make_block_id("pfbchannelizer",  block_select, device_select),
            ::uhd::stream_args_t("fc32", "sc16"),
            ::uhd::stream_args_t("fc32", "sc16"))
    {
        gr::block::set_min_noutput_items(256);
    }

    /*
     * Our virtual destructor.
     */
    pfbchan_impl::~pfbchan_impl()
    {
    }

  } /* namespace theseus */
} /* namespace gr */
