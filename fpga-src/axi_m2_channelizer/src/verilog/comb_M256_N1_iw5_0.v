
/*****************************************************************************/
//
// Author : PJV
// File : comb_M256_N1_iw5_0.v
// Description : Comb Filter.
// The module implements a comb filter using a RAM block and 
// a single DSP48A core. 
//

//
/*****************************************************************************/


module comb_M256_N1_iw5_0
(
  input clk,
  input sync_reset,

  input  [8:0] msetting,

  input s_axis_tvalid,
  input [47:0] s_axis_tdata,

  output m_axis_tvalid,
  output [47:0] m_axis_tdata
);

localparam TOTAL_DELAY = 10;
wire [47:0] diff_delay;
wire [47:0] comb_out;
wire [8:0] msetting_s;

reg [47:0] c_d0, c_d1, c_d2;

reg [3:0] tvalid_d;
wire tvalid_s;

assign m_axis_tdata = comb_out;
assign m_axis_tvalid = tvalid_d[3];
assign msetting_s = msetting;


always @(posedge clk)
begin
    c_d0 <= s_axis_tdata;
    c_d1 <= c_d0;
    c_d2 <= c_d1;
end

//Latency 1
always @(posedge clk)
begin
    if (sync_reset == 1'b1) begin
        tvalid_d <= 0;
    end else begin
        tvalid_d <= {tvalid_d[2:0], tvalid_s};
	end
end


// Differential Delay. Latency = 3.
axi_fifo_64 #(
    .DATA_WIDTH(48),
    .ADDR_WIDTH(9))
u_diff_delay
(
    .clk(clk),
    .sync_reset(sync_reset),

    .s_axis_tvalid(s_axis_tvalid),
    .s_axis_tdata(s_axis_tdata),
    .s_axis_tready(),

    .delay(msetting_s),

    .m_axis_tvalid(tvalid_s),
    .m_axis_tdata(diff_delay),
    .m_axis_tready(1'b1)
);

// Latency = 4.
// EQ : C - CONCAT
dsp48_comb_M256_N1_iw5_0 u_dsp (
  .clk(clk),
  .c(c_d2), 
  .concat(diff_delay), 
  .p(comb_out) 
);

endmodule
