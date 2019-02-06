/*****************************************************************************/
//// Author      : Python Generated
// File        : add_16_16_l2
// Description : Implements a fully pipelined adder.
//
//
//
// LICENSE     : SEE LICENSE FILE AGREEMENT,
//
//
//
/*****************************************************************************/
module add_16_16_l2
(
    input clk,
    input valid_i,
    input [15:0] a,
    input [15:0] b,
    output valid_o,
    output [16:0] c
);

reg [8:0] padd_0;
reg [9:0] padd_1;
reg [7:0] padd_delay0_0;
reg [15:0] adelay_0;
reg [15:0] bdelay_0;
reg [1:0] valid_d;
assign valid_o = valid_d[1];
assign c = {padd_1[9:1], padd_delay0_0[7:0]};

always @(posedge clk)
begin
    valid_d[0] <= valid_i;
    valid_d[1] <= valid_d[0];
    padd_0 <= {1'b0, a[7:0]} + {1'b0, b[7:0]};
    padd_1 <= {{1'b0}, adelay_0[15:8], padd_0[8]} + {{1'b0}, bdelay_0[15:8], padd_0[8]};
    adelay_0 <= a;
    bdelay_0 <= b;
    padd_delay0_0 <= padd_0[7:0];
end

endmodule
