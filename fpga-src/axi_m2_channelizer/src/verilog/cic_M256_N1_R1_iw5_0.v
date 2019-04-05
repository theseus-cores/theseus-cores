
/*****************************************************************************/
//
// Author      : PJV
// File        : cic_M256_N1_R1_iw5_0
// Description : CIC Filter module with gain correction and output slicer.
//

//
/*****************************************************************************/


module cic_M256_N1_R1_iw5_0
(
  input sync_reset, // reset
  input clk,

  input [8:0] msetting,

  input s_axis_tvalid,
  input [4:0] s_axis_tdata, 

  output s_axis_tready,
  output m_axis_tvalid,
  output [12:0] m_axis_tdata,
  input m_axis_tready
);


wire [12:0] corr_factor;
wire [12:0] slice_out_s;
wire [0:0] slice_offset;

wire [47:0] input_signal;
wire [12:0] signal_d;
wire [0:0] reset;
wire almost_full;

reg [47:0] int_signal_0;
wire [47:0] int_out_signal_0;
reg int_valid_d0;
reg int_valid_d1;
reg int_valid_d2;
reg int_valid_d3;
reg int_valid_d4;
wire [47:0] comb_signal_0;
wire [47:0] comb_signal_1;

wire comb_valid_0;
wire comb_valid_1;
wire slice_valid;
reg slice_valid_d0;
reg slice_valid_d1;
reg slice_valid_d2;
reg slice_valid_d3;
reg slice_valid_d4;

reg [0:0] count, next_count;

wire [47:0] signal_out_s;

assign reset[0] = sync_reset;
assign s_axis_tready = ~almost_full;
assign signal_d = signal_out_s[12:0];
assign input_signal = {{43{s_axis_tdata[4]}},s_axis_tdata};
assign comb_valid_0 = int_valid_d4;
assign comb_signal_0 = int_out_signal_0;


always @(posedge clk)
begin
   // Logic ensures that the integrators do not integrate stale values
    if (s_axis_tvalid == 1'b1 && almost_full == 1'b0) begin
		int_signal_0 <= input_signal;
    end else begin
        int_signal_0 <= 0;
    end

end

always @*
begin
  if (slice_valid_d3 == 1'b1 && count != 0) begin
    next_count = count - 1;
  end else begin
    next_count = count;
  end
end

always @(posedge clk)
begin
  int_valid_d0 <= s_axis_tvalid & ~almost_full;
  int_valid_d1 <= int_valid_d0;
  int_valid_d2 <= int_valid_d1;
  int_valid_d3 <= int_valid_d2;
  int_valid_d4 <= int_valid_d3;
end
always @(posedge clk)
begin
    slice_valid_d0 <= comb_valid_1;
    slice_valid_d1 <= slice_valid_d0;
    slice_valid_d2 <= slice_valid_d1;
    slice_valid_d3 <= slice_valid_d2;
end


//Latency 1
always @(posedge clk)
begin
  if (sync_reset == 1'b1) begin
      slice_valid_d4 <= 0;
      count <= 0;
  end else begin
      if (slice_valid_d3 == 1'b1) begin
          if (count == 0) begin
              slice_valid_d4 <= 1'b1;
          end else begin
              count <= count - 1;
          end
      end else begin
          slice_valid_d4 <= 1'b0;
      end
	end
end

//latency = 4.
dsp48_cic_M256_N1_R1_iw5_0 integrator_section_0 (
  .clk(clk), // input clk
  .opcode(reset),
  .concat(int_signal_0),
  .p(int_out_signal_0)
);


//latency = 10.
comb_M256_N1_iw5_0 comb_section_0
(
  .clk(clk), 
  .sync_reset(sync_reset),
  .msetting(msetting),
  .s_axis_tvalid(comb_valid_0),
  .s_axis_tdata(comb_signal_0),
  .m_axis_tvalid(comb_valid_1),
  .m_axis_tdata(comb_signal_1)
);



cic_M256_N1_R1_iw5_0_offset_sp_rom offset_rom (
  .clk(clk),
  .addra(msetting),
  .doa(slice_offset)
);

// Latency 1
slicer_48_13 slicer (
  .clk(clk), // clock
  .sync_reset(sync_reset), // reset

  .slice_offset_i(slice_offset),
  // offset is relative to the base value

  .valid_i(comb_valid_1),
  .signal_i(comb_signal_1),

  .valid_o(slice_valid),
  .signal_o(slice_out_s)
);

cic_M256_N1_R1_iw5_0_correction_sp_rom corr_factor_rom (
  .clk(clk), 
  .addra(msetting),
  .doa(corr_factor)
);

//Latency = 4
dsp48_cic_M256_N1_R1_iw5_0_corr correction_multiplier (
  .clk(clk),
  .a(slice_out_s),
  .b(corr_factor),
  .p(signal_out_s)
);

axi_fifo_2 #(
    .DATA_WIDTH(13),
    .ALMOST_FULL_THRESH(42),
    .ADDR_WIDTH(6))
u_fifo
(
    .clk(clk),
    .sync_reset(sync_reset),

    .s_axis_tvalid(slice_valid_d4),
    .s_axis_tdata(signal_d),
    .s_axis_tready(),

    .almost_full(almost_full),

    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata),
    .m_axis_tready(m_axis_tready)
);

endmodule
