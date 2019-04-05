/* -*- c++ -*- */
/* Copyright 2015 Ettus Research
 * 
 * This is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3, or (at your option)
 * any later version.
 * 
 * gr-ettus is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with gr-ettus; see the file COPYING.  If not, write to
 * the Free Software Foundation, Inc., 51 Franklin Street,
 * Boston, MA 02110-1301, USA.
 */

#include <gnuradio/io_signature.h>
#include "theseus_generic_impl.h"
#include <boost/format.hpp>

namespace gr {
  namespace theseus {

    theseus_generic::sptr
      theseus_generic::make(
          const gr::ettus::device3::sptr &dev,
          const ::uhd::stream_args_t &tx_stream_args,
          const ::uhd::stream_args_t &rx_stream_args,
          const std::string &block_name,
          const int block_select,
          const int device_select
    ) {
      return gnuradio::get_initial_sptr(
          new theseus_generic_impl(dev, tx_stream_args, rx_stream_args, block_name, block_select, device_select)
      );
    }

    theseus_generic_impl::theseus_generic_impl(
        const gr::ettus::device3::sptr &dev,
        const ::uhd::stream_args_t &tx_stream_args,
        const ::uhd::stream_args_t &rx_stream_args,
        const std::string &block_name,
        const int block_select,
        const int device_select
    ) : gr::ettus::rfnoc_block(str(boost::format("uhd_rfnoc_%s") % block_name)),
        gr::ettus::rfnoc_block_impl(
            dev,
            gr::ettus::rfnoc_block_impl::make_block_id(block_name, block_select, device_select),
            tx_stream_args, rx_stream_args
        )
    {
      /* nop */
    }

    theseus_generic_impl::~theseus_generic_impl()
    {
      /* nop */
    }

  } /* namespace theseus */
} /* namespace gr */

