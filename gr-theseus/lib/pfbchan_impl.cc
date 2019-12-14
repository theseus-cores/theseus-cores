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

#include "pfbchan_impl.h"
#include <gnuradio/io_signature.h>
#include <gnuradio/block.h>
#include <gnuradio/block_detail.h>

namespace gr {
  namespace theseus {

    pfbchan::sptr
    pfbchan::make(
        const gr::ettus::device3::sptr &dev,
        const int block_select,
        const int device_select,
        const int num_channels,
        const std::vector<uint32_t> active_channels
    )
    {
        return gnuradio::get_initial_sptr(
            new pfbchan_impl(
                dev,
                block_select,
                device_select,
                num_channels,
                active_channels
            )
        );
    }

    /*
     * The private constructor
     */
    pfbchan_impl::pfbchan_impl(
        const gr::ettus::device3::sptr &dev,
        const int block_select,
        const int device_select,
        const int num_channels,
        const std::vector<uint32_t> active_channels
    )
      : gr::ettus::rfnoc_block("pfbchannelizer"),
        gr::ettus::rfnoc_block_impl(
            dev,
            gr::ettus::rfnoc_block_impl::make_block_id("pfbchannelizer",  block_select, device_select),
            ::uhd::stream_args_t("fc32", "sc16"),
            ::uhd::stream_args_t("fc32", "sc16"))
    {
      set_channels(num_channels, active_channels);
    }

    /*
     * Our virtual destructor.
     */
    pfbchan_impl::~pfbchan_impl()
    {
    }

    bool pfbchan_impl::start()
    {
      // Copy from rfnoc_block_impl
      // Need to override behavior so there's only one rx streamer for N outputs
      boost::recursive_mutex::scoped_lock lock(d_mutex);
      size_t ninputs  = detail()->ninputs();
      size_t noutputs = 1; // Hardcode noutputs to 1 (only 1 rx streamer)
      _rx.align = false; // Just call unaligned
      GR_LOG_DEBUG(d_debug_logger, str(boost::format("start(): ninputs == %d noutputs == %d") % ninputs % noutputs));

      if (ninputs == 0 && noutputs == 0) {
          return true;
      }

      // If the topology changed, we need to clear the old streamers
      if (_rx.streamers.size() != noutputs) {
        _rx.streamers.clear();
      }
      if (_tx.streamers.size() != ninputs) {
        _tx.streamers.clear();
      }

      //////////////////// TX ///////////////////////////////////////////////////////////////
      // Setup TX streamer.
      if (ninputs && _tx.streamers.empty()) {
        // Get a block control for the tx side:
        ::uhd::rfnoc::sink_block_ctrl_base::sptr tx_blk_ctrl =
            boost::dynamic_pointer_cast< ::uhd::rfnoc::sink_block_ctrl_base >(_blk_ctrl);
        if (!tx_blk_ctrl) {
          GR_LOG_FATAL(d_logger, str(boost::format("Not a sink_block_ctrl_base: %s") % _blk_ctrl->unique_id()));
          return false;
        }
        if (_tx.align) { // Aligned streamers:
          GR_LOG_DEBUG(d_debug_logger, str(boost::format("Creating one aligned tx streamer for %d inputs.") % ninputs));
          GR_LOG_DEBUG(d_debug_logger,
              str(boost::format("cpu: %s  otw: %s  args: %s channels.size: %d ") % _tx.stream_args.cpu_format % _tx.stream_args.otw_format % _tx.stream_args.args.to_string() % _tx.stream_args.channels.size()));
          assert(ninputs == _tx.stream_args.channels.size());
          ::uhd::tx_streamer::sptr tx_stream = _dev->get_tx_stream(_tx.stream_args);
          if (tx_stream) {
            _tx.streamers.push_back(tx_stream);
          } else {
            GR_LOG_FATAL(d_logger, str(boost::format("Can't create tx streamer(s) to: %s") % _blk_ctrl->get_block_id().get()));
            return false;
          }
        } else { // Unaligned streamers:
          for (size_t i = 0; i < size_t(ninputs); i++) {
            _tx.stream_args.channels = std::vector<size_t>(1, i);
            _tx.stream_args.args["block_port"] = str(boost::format("%d") % i);
            GR_LOG_DEBUG(d_debug_logger, str(boost::format("creating tx streamer with: %s") % _tx.stream_args.args.to_string()));
            ::uhd::tx_streamer::sptr tx_stream = _dev->get_tx_stream(_tx.stream_args);
            if (tx_stream) {
              _tx.streamers.push_back(tx_stream);
            }
          }
          if (_tx.streamers.size() != size_t(ninputs)) {
            GR_LOG_FATAL(d_logger, str(boost::format("Can't create tx streamer(s) to: %s") % _blk_ctrl->get_block_id().get()));
            return false;
          }
        }
      }

      _tx.metadata.start_of_burst = false;
      _tx.metadata.end_of_burst = false;
      _tx.metadata.has_time_spec = false;

      // Wait for all RFNoC streamers to have set up their tx streamers
      _tx_barrier.wait();

      //////////////////// RX ///////////////////////////////////////////////////////////////
      // Setup RX streamer
      if (noutputs && _rx.streamers.empty()) {
        // Get a block control for the rx side:
        ::uhd::rfnoc::source_block_ctrl_base::sptr rx_blk_ctrl =
            boost::dynamic_pointer_cast< ::uhd::rfnoc::source_block_ctrl_base >(_blk_ctrl);
        if (!rx_blk_ctrl) {
          GR_LOG_FATAL(d_logger, str(boost::format("Not a source_block_ctrl_base: %s") % _blk_ctrl->unique_id()));
          return false;
        }

        // Pay no attention to aligned/unaligned. Just make one streamer.
        _rx.stream_args.channels = std::vector<size_t>(1, 0) ;
        _rx.stream_args.args["block_port"] = str(boost::format("%d") % 0);
        GR_LOG_DEBUG(d_debug_logger, str(boost::format("creating rx streamer with: %s") % _rx.stream_args.args.to_string()));
        ::uhd::rx_streamer::sptr rx_stream = _dev->get_rx_stream(_rx.stream_args);
        if (rx_stream) {
          _rx.streamers.push_back(rx_stream);
        }
        if (_rx.streamers.size() != size_t(noutputs)) {
          GR_LOG_FATAL(d_logger, str(boost::format("Can't create rx streamer(s) to: %s") % _blk_ctrl->get_block_id().get()));
          return false;
        }
      }

      // Wait for all RFNoC streamers to have set up their rx streamers
      _rx_barrier.wait();

      // Start the streamers
      if (!_rx.streamers.empty()) {
        ::uhd::stream_cmd_t stream_cmd(::uhd::stream_cmd_t::STREAM_MODE_START_CONTINUOUS);
        if (_start_time_set) {
            stream_cmd.stream_now = false;
            stream_cmd.time_spec = _start_time;
            _start_time_set = false;
        } else {
            stream_cmd.stream_now = true;
        }
        for (size_t i = 0; i < _rx.streamers.size(); i++) {
          _rx.streamers[i]->issue_stream_cmd(stream_cmd);
        }
      }

      return true;
    }

    void pfbchan_impl::set_channels(
        uint32_t num_channels, std::vector<uint32_t> active_channels
    ) {
      assert(active_channels.empty() || num_channels == active_channels.size());

      // std::cout << "Setting channels. " << num_channels << " total, " << active_channels.size() << " active" << std::endl;

      d_num_channels = num_channels;
      d_active_channels = active_channels;

      // Calculate desired packet size
      // Aim for even multiple of num_outputs
      size_t max_packet_size = 256;
      size_t num_outputs = d_active_channels.size();
      d_target_pkt_size = int(max_packet_size / num_outputs) * num_outputs;
      if (d_target_pkt_size == 0) d_target_pkt_size = max_packet_size;

      // TODO: Inform gnuradio of packet sizes?

      // Save and set
      get_block_ctrl_throw< ::uhd::theseus::pfbchan_block_ctrl >()->set_arg("fft_size", d_num_channels);
      get_block_ctrl_throw< ::uhd::theseus::pfbchan_block_ctrl >()->set_arg("pkt_size", d_target_pkt_size);
      get_block_ctrl_throw< ::uhd::theseus::pfbchan_block_ctrl >()->set_active_channels(active_channels);
      d_idx = 0;
    }

    /*********************************************************************
     * Streaming
     *********************************************************************/
    void pfbchan_impl::work_rx_u(
        int noutput_items,
        gr_vector_void_star &output_items
    ) {
      // Temporarily channel copy from rfnoc_block_impl

      assert(_rx.streamers.size() == 1);
      assert(output_items.size() == d_active_channels.size());

      // nsamples = Maximum possible number of samples we could grab and write
      size_t nchannels = output_items.size();
      size_t nsamples = noutput_items*nchannels;

      gr_complex buff_samples[d_target_pkt_size];
      gr_vector_void_star buff_ptr(1);
      buff_ptr[0] = reinterpret_cast<void*> (&buff_samples[0]);

      size_t num_samps = _rx.streamers[0]->recv(
          buff_ptr,
          d_target_pkt_size,
          _rx.metadata, 0.1, true
      );

      switch(_rx.metadata.error_code) {
        case ::uhd::rx_metadata_t::ERROR_CODE_NONE:
          break;

        case ::uhd::rx_metadata_t::ERROR_CODE_TIMEOUT:
          //its ok to timeout, perhaps the user is doing finite streaming
          std::cout << "timeout on streamer " << 0 << std::endl;
          break;

        case ::uhd::rx_metadata_t::ERROR_CODE_OVERFLOW:
          // Not much we can do about overruns here
          std::cout << "overrun on streamer " << 0 << std::endl;
          break;

        default:
          std::cout << boost::format("RFNoC Streamer block received error %s (Code: 0x%x)")
            % _rx.metadata.strerror() % _rx.metadata.error_code << std::endl;
      }

      if (_rx.metadata.end_of_burst) {
        // NOTE: Dont worry about tags, for now...
        // for (size_t i = 0; i < output_items.size(); i++) {
        //   add_item_tag(
        //       i,
        //       nitems_written(i) + (num_samps / _rx.vlen) - 1,
        //       EOB_KEY, pmt::PMT_T
        //   );
        // }
      }

      if (num_samps != d_target_pkt_size) {
        std::cout << "WHOA! Couldnt get requested " << d_target_pkt_size << " samples. Only returned " << num_samps << std::endl;
      }


      size_t itemsize = output_signature()->sizeof_stream_item(0);
      const char *in = (const char *) buff_ptr[0];
      char **outv = (char **) &output_items[0];

      std::vector<int> produced(nchannels, 0);
      for (int ii = 0; ii < num_samps; ii++){
        // std::cout << "Deinterleaving: " << ii << " / Chan = " << d_idx << std::endl;
        memcpy(outv[d_idx], in, itemsize);
        produced[d_idx]++;
        outv[d_idx] += itemsize;
        in += itemsize;
        d_idx++;
        if (d_idx >= nchannels) d_idx = 0;
      }

      for (int ii = 0; ii < nchannels; ii++){
        // std::cout << "Producing Chan[" << ii << "]: "<< produced[ii] << std::endl;
        produce(ii, produced[ii]);
      }

    }

  } /* namespace theseus */
} /* namespace gr */
