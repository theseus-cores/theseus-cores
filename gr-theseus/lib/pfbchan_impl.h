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

#ifndef INCLUDED_THESEUS_PFBCHAN_IMPL_H
#define INCLUDED_THESEUS_PFBCHAN_IMPL_H

#include <theseus/pfbchan.h>
#include <theseus/pfbchan_block_ctrl.hpp>
#include <ettus/rfnoc_block_impl.h>

namespace gr {
  namespace theseus {

    class pfbchan_impl : public pfbchan, public gr::ettus::rfnoc_block_impl
    {
     private:
         size_t d_fft_size;

     public:
      pfbchan_impl(const gr::ettus::device3::sptr &dev, const int block_select, const int device_select);
      ~pfbchan_impl();

      // virtual int general_work(
      //     int noutput_items,
      //     gr_vector_int &ninput_items,
      //     gr_vector_const_void_star &input_items,
      //     gr_vector_void_star &output_items
      //  );
      virtual bool start();

      virtual void work_rx_u(
          int noutput_items,
          gr_vector_void_star &output_items
      );
    };

  } // namespace theseus
} // namespace gr

#endif /* INCLUDED_THESEUS_PFBCHAN_IMPL_H */
