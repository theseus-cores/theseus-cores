
//
// Copyright 2015 Ettus Research
//
//

module noc_block_channelizer #(
  parameter NOC_ID = 64'hF2A3373CFBFB4BFA,
  parameter STR_SINK_FIFOSIZE = 11)
(
  input bus_clk, input bus_rst,
  input ce_clk, input ce_rst,
  input  [63:0] i_tdata,
  input  i_tlast,
  input  i_tvalid,
  output i_tready,
  output [63:0] o_tdata,
  output o_tlast,
  output o_tvalid,
  input  o_tready,
  output [63:0] debug
);

  ////////////////////////////////////////////////////////////
  //
  // RFNoC Shell
  //
  ////////////////////////////////////////////////////////////
  wire [31:0] set_data;
  wire [7:0]  set_addr;
  wire        set_stb;
  reg  [63:0] rb_data;
  wire [7:0]  rb_addr;

  wire [63:0] cmdout_tdata, ackin_tdata;
  wire        cmdout_tlast, cmdout_tvalid, cmdout_tready, ackin_tlast, ackin_tvalid, ackin_tready;

  wire [63:0] str_sink_tdata, str_src_tdata;
  wire        str_sink_tlast, str_sink_tvalid, str_sink_tready, str_src_tlast, str_src_tvalid, str_src_tready;

  wire [15:0] src_sid;
  wire [15:0] next_dst_sid, resp_out_dst_sid;
  wire [15:0] resp_in_dst_sid;
  wire eob_tag;

  wire        clear_tx_seqnum;



  noc_shell #(
    .NOC_ID(NOC_ID),
    .STR_SINK_FIFOSIZE(STR_SINK_FIFOSIZE))
  noc_shell (
    .bus_clk(bus_clk), .bus_rst(bus_rst),
    .i_tdata(i_tdata), .i_tlast(i_tlast), .i_tvalid(i_tvalid), .i_tready(i_tready),
    .o_tdata(o_tdata), .o_tlast(o_tlast), .o_tvalid(o_tvalid), .o_tready(o_tready),
    // Computer Engine Clock Domain
    .clk(ce_clk), .reset(ce_rst),
    // Control Sink
    .set_data(set_data), .set_addr(set_addr), .set_stb(set_stb),
    .rb_stb(1'b1), .rb_data(rb_data), .rb_addr(rb_addr),
    // Control Source
    .cmdout_tdata(cmdout_tdata), .cmdout_tlast(cmdout_tlast), .cmdout_tvalid(cmdout_tvalid), .cmdout_tready(cmdout_tready),
    .ackin_tdata(ackin_tdata), .ackin_tlast(ackin_tlast), .ackin_tvalid(ackin_tvalid), .ackin_tready(ackin_tready),
    // Stream Sink
    .str_sink_tdata(str_sink_tdata), .str_sink_tlast(str_sink_tlast), .str_sink_tvalid(str_sink_tvalid), .str_sink_tready(str_sink_tready),
    // Stream Source
    .str_src_tdata(str_src_tdata), .str_src_tlast(str_src_tlast), .str_src_tvalid(str_src_tvalid), .str_src_tready(str_src_tready),
    // Stream IDs set by host
    .src_sid(src_sid),                   // SID of this block
    .next_dst_sid(next_dst_sid),         // Next destination SID
    .resp_in_dst_sid(resp_in_dst_sid),   // Response destination SID for input stream responses / errors
    .resp_out_dst_sid(resp_out_dst_sid), // Response destination SID for output stream responses / errors
    // Misc
    .vita_time('d0), .clear_tx_seqnum(clear_tx_seqnum),
    .debug(debug));

  ////////////////////////////////////////////////////////////
  //
  // AXI Wrapper
  // Convert RFNoC Shell interface into AXI stream interface
  //
  ////////////////////////////////////////////////////////////
  wire [31:0] m_axis_data_tdata;
  wire        m_axis_data_tlast;
  wire        m_axis_data_tvalid;
  wire        m_axis_data_tready;
  wire [127:0] m_axis_data_tuser;

  wire [31:0] s_axis_data_tdata;
  wire        s_axis_data_tlast;
  wire        s_axis_data_tvalid;
  wire        s_axis_data_tready;
  wire [127:0] s_axis_data_tuser;


  // assign s_axis_data_tuser = {3'b000, eob_tag & s_axis_data_tlast, 12'd0, 16'd0, m_axis_data_tuser[79:64], next_dst_sid, 64'd0};
  axi_wrapper #(
    .SIMPLE_MODE(0),
    .RESIZE_OUTPUT_PACKET(0))
  axi_wrapper (
    .bus_clk(bus_clk), .bus_rst(bus_rst),
    .clk(ce_clk), .reset(ce_rst),
    .clear_tx_seqnum(clear_tx_seqnum),
    .next_dst(next_dst_sid),
    .set_stb(set_stb), .set_addr(set_addr), .set_data(set_data),
    .i_tdata(str_sink_tdata), .i_tlast(str_sink_tlast), .i_tvalid(str_sink_tvalid), .i_tready(str_sink_tready),
    .o_tdata(str_src_tdata), .o_tlast(str_src_tlast), .o_tvalid(str_src_tvalid), .o_tready(str_src_tready),
    .m_axis_data_tdata(m_axis_data_tdata),
    .m_axis_data_tlast(m_axis_data_tlast),
    .m_axis_data_tvalid(m_axis_data_tvalid),
    .m_axis_data_tready(m_axis_data_tready),
    .m_axis_data_tuser(m_axis_data_tuser),
    .s_axis_data_tdata(s_axis_data_tdata),
    .s_axis_data_tlast(s_axis_data_tlast),
    .s_axis_data_tvalid(s_axis_data_tvalid),
    .s_axis_data_tready(s_axis_data_tready),
    .s_axis_data_tuser(s_axis_data_tuser),
    .m_axis_config_tdata(),
    .m_axis_config_tlast(),
    .m_axis_config_tvalid(),
    .m_axis_config_tready(),
    .m_axis_pkt_len_tdata(),
    .m_axis_pkt_len_tvalid(),
    .m_axis_pkt_len_tready());

  ////////////////////////////////////////////////////////////
  //
  // User code
  //
  ////////////////////////////////////////////////////////////
  // NoC Shell registers 0 - 127,
  // User register address space starts at 128
  localparam SR_USER_REG_BASE = 128;
  localparam RB_NUM_TAPS = 128;
  localparam SR_FFT_SIZE = 129;
  localparam RB_FFT_SIZE = 129;
  localparam SR_AVG_LEN = 130;
  localparam RB_AVG_LEN = 130;
  localparam SR_RELOAD = 131;
  localparam SR_RELOAD_LAST = 132;
  localparam SR_MASK_RELOAD = 133;
  localparam SR_MASK_RELOAD_LAST = 134;
  localparam SR_PKT_SIZE = 135;
  localparam RB_PKT_SIZE = 135;
  localparam RB_MAX_FFT_SIZE = 136;
  localparam RB_TAPS_PER_PHASE = 137;
  localparam NUM_TAPS = 65536;
  localparam MAX_FFT_SIZE = 2048;
  localparam TAPS_PER_PHASE = 32;

  // Control Source Unused
  assign cmdout_tdata  = 64'd0;
  assign cmdout_tlast  = 1'b0;
  assign cmdout_tvalid = 1'b0;
  assign ackin_tready  = 1'b1;

  wire [31:0] m_axis_reload_tdata;
  wire        m_axis_reload_tvalid;
  wire  m_axis_reload_tready;
    //(* keep = “true”, dont_touch = “true”, mark_debug = “true” *)
  wire m_axis_reload_tlast;
  
  wire [31:0] m_axis_select_tdata;
  wire        m_axis_select_tvalid;
  wire  m_axis_select_tready;
    //(* keep = "true", dont_touch = "true", mark_debug = "true" *)
  wire m_axis_select_tlast;

  wire [15:0] payload_length;
  cvita_hdr_encoder cvita_hdr_encoder (
   .pkt_type(2'd0), .eob(1'b0), .has_time(1'b0),
   .seqnum(12'd0), .payload_length(payload_length), .dst_sid(next_dst_sid), .src_sid(src_sid),
   .vita_time(64'd0),
   .header(s_axis_data_tuser));

   setting_reg #(.my_addr(SR_PKT_SIZE), .awidth(8), .width(16), .at_reset(767))
   set_payload_length_inst (
   .clk(ce_clk), .rst(ce_rst),
   .strobe(set_stb), .addr(set_addr), .in(set_data), .out(payload_length), .changed());

  // Settings registers
  //
  // - The settings register bus is a simple strobed interface.
  // - Transactions include both a write and a readback.
  // - The write occurs when set_stb is asserted.
  //   The settings register with the address matching set_addr will
  //   be loaded with the data on set_data.
  // - Readback occurs when rb_stb is asserted. The read back strobe
  //   must assert at least one clock cycle after set_stb asserts /
  //   rb_stb is ignored if asserted on the same clock cycle of set_stb.
  //   Example valid and invalid timing:
  //              __    __    __    __
  //   clk     __|  |__|  |__|  |__|  |__
  //               _____
  //   set_stb ___|     |________________
  //                     _____
  //   rb_stb  _________|     |__________     (Valid)
  //                           _____
  //   rb_stb  _______________|     |____     (Valid)
  //           __________________________
  //   rb_stb                                 (Valid if readback data is a constant)
  //               _____
  //   rb_stb  ___|     |________________     (Invalid / ignored, same cycle as set_stb)
  //
  // Readback registers
  // rb_stb set to 1'b1 on NoC Shell
  wire [11:0] fft_size;
  wire [8:0] avg_len;
  always @(posedge ce_clk) begin
    case(rb_addr)
      RB_NUM_TAPS : rb_data <= {NUM_TAPS};
      RB_FFT_SIZE : rb_data <= {20'd0, fft_size};
      RB_AVG_LEN : rb_data <= {23'd0, avg_len};
      RB_PKT_SIZE : rb_data <= {16'd0, payload_length};
      RB_MAX_FFT_SIZE : rb_data <= {MAX_FFT_SIZE};
      RB_TAPS_PER_PHASE : rb_data <= {TAPS_PER_PHASE};
      default : rb_data <= 64'h0BADC0DE0BADC0DE;
    endcase
  end


  /* Channelizer top level instantiation */

// FFT Size Register
//
axi_setting_reg #(
    .ADDR(SR_FFT_SIZE),
    .WIDTH(12))
set_fft_size (
    .clk(ce_clk),
    .reset(ce_rst),
    .set_stb(set_stb),
    .set_addr(set_addr),
    .set_data(set_data),
    .error_stb(),
    .o_tdata(fft_size),
    .o_tlast(),
    .o_tvalid(),
    .o_tready(1'b1)
);

// Average Length register
axi_setting_reg #(
    .ADDR(SR_AVG_LEN),
    .WIDTH(9))
set_avg_len (
    .clk(ce_clk),
    .reset(ce_rst),
    .set_stb(set_stb),
    .set_addr(set_addr),
    .set_data(set_data),
    .error_stb(),
    .o_tdata(avg_len),
    .o_tlast(),
    .o_tvalid(),
    .o_tready(1'b1)
);

// FIR filter coefficient reload bus
// (see Xilinx FIR Filter Compiler documentation)
axi_setting_reg #(
  .ADDR(SR_RELOAD),
  .USE_ADDR_LAST(1),
  .ADDR_LAST(SR_RELOAD_LAST),
  .WIDTH(32),
  .USE_FIFO(1),
  .FIFO_SIZE(7))
set_coeff (
  .clk(ce_clk),
  .reset(ce_rst),
  .set_stb(set_stb),
  .set_addr(set_addr),
  .set_data(set_data),
  .o_tdata(m_axis_reload_tdata),
  .o_tlast(m_axis_reload_tlast),
  .o_tvalid(m_axis_reload_tvalid),
  .o_tready(m_axis_reload_tready));

// Mask reload bus
// (see Xilinx FIR Filter Compiler documentation)
axi_setting_reg #(
  .ADDR(SR_MASK_RELOAD),
  .USE_ADDR_LAST(1),
  .ADDR_LAST(SR_MASK_RELOAD_LAST),
  .WIDTH(32),
  .USE_FIFO(1),
  .FIFO_SIZE(7))
set_mask (
  .clk(ce_clk),
  .reset(ce_rst),
  .set_stb(set_stb),
  .set_addr(set_addr),
  .set_data(set_data),
  .o_tdata(m_axis_select_tdata),
  .o_tlast(m_axis_select_tlast),
  .o_tvalid(m_axis_select_tvalid),
  .o_tready(m_axis_select_tready));

chan_top_2x_2048M_16iw_16ow_32tps channelizer_top
(
    .clk(ce_clk),
    .sync_reset(ce_rst),

    .fft_size(fft_size),
    .avg_len(avg_len),
    .eob_tag(eob_tag),
    .payload_length(payload_length),

    .s_axis_tdata(m_axis_data_tdata),
    .s_axis_tvalid(m_axis_data_tvalid),
    .s_axis_tready(m_axis_data_tready),

    .s_axis_reload_tdata(m_axis_reload_tdata),
    .s_axis_reload_tlast(m_axis_reload_tlast),
    .s_axis_reload_tvalid(m_axis_reload_tvalid),
    .s_axis_reload_tready(m_axis_reload_tready),

    // down selection FIFO interface
    .s_axis_select_tvalid(m_axis_select_tvalid),
    .s_axis_select_tdata(m_axis_select_tdata),
    .s_axis_select_tlast(m_axis_select_tlast),
    .s_axis_select_tready(m_axis_select_tready),

    .m_axis_tdata(s_axis_data_tdata),
    .m_axis_tuser(),
    .m_axis_tvalid(s_axis_data_tvalid),
    .m_axis_tlast(s_axis_data_tlast),
    .m_axis_tready(s_axis_data_tready)
);

endmodule
