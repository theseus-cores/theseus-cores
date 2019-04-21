//
// Copyright 2019 Theseus Cores
//

module multi_split_stream #(
  parameter WIDTH=16,
  parameter USER_WIDTH=2,
  parameter OUTPUTS=4
)(
  input clk, input reset, input clear,  // These are not used in plain split_stream
  input [WIDTH-1:0] i_tdata,
  input i_tlast,
  input i_tvalid,
  output i_tready,
  input [USER_WIDTH-1:0] i_tuser,
  output [WIDTH*OUTPUTS-1:0] o_tdata,
  output [OUTPUTS-1:0] o_tlast,
  output [OUTPUTS-1:0] o_tvalid,
  input [OUTPUTS-1:0] o_tready,
  output [OUTPUTS*USER_WIDTH-1:0] o_tuser
);

  // NOTE -- this violates the AXI spec because tvalids are dependent on treadys.
  //   It will be ok most of the time, but muxes and demuxes will need a fifo in
  //   the middle to avoid deadlock

  assign i_tready = &o_tready;

  genvar ii;
  generate for (ii = 0; ii < OUTPUTS; ii = ii + 1) begin : gen_split
    assign o_tdata[WIDTH*ii +: WIDTH] = i_tdata;
    assign o_tuser[USER_WIDTH*ii +: USER_WIDTH] = i_tuser;
    assign o_tlast[ii] = i_tlast;
    assign o_tvalid[ii] = i_tready & i_tvalid;
  end endgenerate

endmodule // multi_split_stream
