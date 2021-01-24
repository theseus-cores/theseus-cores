// Top level testbench

`timescale 1ns/1ps

module chan_top_2x_2048M_16iw_16ow_32tps_tb();

function integer clog2;
 //
 // ceiling( log2( x ) )
 //
 input integer x;
 begin
   if (x<=0) clog2 = -1;
   else clog2 = 0;
   x = x - 1;
   while (x>0) begin
     clog2 = clog2 + 1;
     x = x >> 1;
   end

 end
endfunction

localparam stimulus = "/home/phil/lts_gitclones/wavephy/wavephy/streamlit_app/tmp/sig_tones_2048.bin";
localparam mask_file = "/home/phil/lts_gitclones/wavephy/wavephy/streamlit_app/tmp/M_2048_mask.bin";
localparam output_file = "/home/phil/lts_gitclones/wavephy/wavephy/streamlit_app/tmp/chan_results.bin";

integer input_descr, mask_descr, output_descr;

initial begin
    input_descr = $fopen(stimulus, "rb");
    mask_descr = $fopen(mask_file, "rb");
    output_descr = $fopen(output_file, "wb");
end

reg clk = 1'b0;
reg sync_reset = 1'b0;

always #2.5 clk <= ~clk;

wire s_axis_tvalid, s_axis_tready;
wire m_axis_tvalid, m_axis_tready;
wire [23:0] m_axis_tuser;
wire [31:0] m_axis_tdata;
wire m_axis_tlast;

wire [63:0] word_cnt;
wire [31:0] s_axis_tdata;
wire eob_tag;
reg data_enable = 1'b0;

// wire s_axis_reload_tvalid;
// wire [31:0] s_axis_reload_tdata;
// wire s_axis_reload_tlast;
// wire s_axis_reload_tready;

wire s_axis_select_tvalid;
wire [31:0] s_axis_select_tdata;
wire s_axis_select_tlast;
wire s_axis_select_tready;

reg flow_ctrl = 1'b0;

localparam FFT_SIZE_WIDTH = clog2(512) + 1;
reg [FFT_SIZE_WIDTH-1:0] FFT_SIZE = 512;

// reset signal process.
initial begin
  #10
  sync_reset = 1'b1;
  #100  //repeat(10) @(posedge clk);
  sync_reset = 1'b0;
end

initial begin
    #90000  // wait 90 us to start data flowing -- allows the taps to be written.
    data_enable = 1'b1;
end

// flow ctrl signal
initial begin
    forever begin
        #50 flow_ctrl = 1'b1;
        #100 flow_ctrl = 1'b0;
    end
end


grc_word_reader #(
    .NUM_BYTES(4),
    .FRAME_SIZE(1024)
)
u_data_reader
(
  .clk(clk),
  .sync_reset(sync_reset),
  .enable_i(data_enable),

  .fd(input_descr),

  .valid_o(s_axis_tvalid),
  .word_o(s_axis_tdata),
  .buffer_end_o(),
  .len_o(),
  .word_cnt(),

  .ready_i(s_axis_tready)
);

grc_word_reader #(
    .NUM_BYTES(4),
    .FRAME_SIZE(1024)
)
u_mask_reader
(
  .clk(clk),
  .sync_reset(sync_reset),
  .enable_i(1'b1),

  .fd(mask_descr),

  .valid_o(s_axis_select_tvalid),
  .word_o(s_axis_select_tdata),
  .buffer_end_o(s_axis_select_tlast),
  .len_o(),
  .word_cnt(word_cnt),

  .ready_i(s_axis_select_tready)
);

chan_top_2x_2048M_16iw_16ow_32tps u_dut
(
   .clk(clk),
   .sync_reset(sync_reset),

   .s_axis_tvalid(s_axis_tvalid),
   .s_axis_tdata(s_axis_tdata),
   .s_axis_tready(s_axis_tready),

   .s_axis_reload_tvalid(1'b0),
   .s_axis_reload_tdata(32'd0),
   .s_axis_reload_tlast(1'b0),
   .s_axis_reload_tready(s_axis_reload_tready),

   .s_axis_select_tvalid(s_axis_select_tvalid),
   .s_axis_select_tdata(s_axis_select_tdata),
   .s_axis_select_tlast(s_axis_select_tlast),
   .s_axis_select_tready(s_axis_select_tready),

   .fft_size(12'd2048),
   .avg_len(9'd128),
   .payload_length(16'd1000),
   .eob_tag(eob_tag),

   .m_axis_tvalid(m_axis_tvalid),
   .m_axis_tdata(m_axis_tdata),
   .m_axis_tuser(m_axis_tuser),
   .m_axis_tlast(m_axis_tlast),
   .m_axis_tready(m_axis_tready)
);

wire [63:0] store_vec;

assign store_vec = {7'd0, m_axis_tlast, m_axis_tuser, m_axis_tdata};

grc_word_writer #(
	.LISTEN_ONLY(0),
	.ARRAY_LENGTH(1024),
	.NUM_BYTES(8))
u_writer
(
  .clk(clk),
  .sync_reset(sync_reset),
  .enable(1'b1),

  .fd(output_descr),

  .valid(m_axis_tvalid),
  .word(store_vec),

  .wr_file(1'b0),
  .word_cnt(),

  .rdy_i(flow_ctrl),
  .rdy_o(m_axis_tready)
);


endmodule //
