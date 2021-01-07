/*************************************************************************/
//// File        : pipe_mux_8_1.v
// Description : Implements a pipelined multiplexer to be used in high speed design
// This module has a delay of 2 clock cycles//
// -------------------------------------------------------------------
//
/***************************************************************************/


module pipe_mux_8_1
(
    input clk,
    input sync_reset,
    input valid_i,
    input [2:0] sel,
    input [7:0] input_word,
    output valid_o,
    output [2:0] sel_o,
    output output_word
);

(* KEEP = "TRUE" *) reg [2:0] sel_d0_0;
(* KEEP = "TRUE" *) reg [2:0] sel_d1;
reg valid_d0;
reg valid_d1;
reg [0:0] mux_d0_0, next_mux_d0_0;
reg [7:0] input_word_d;

assign output_word = mux_d0_0;
assign valid_o = valid_d1;
assign sel_o = sel_d1;

always @(posedge clk) begin
    if (sync_reset) begin
        valid_d0  <= 0;
        valid_d1  <= 0;
    end else begin
        valid_d0  <= valid_i;
        valid_d1  <= valid_d0;
    end
end


always @(posedge clk) begin
    input_word_d <= input_word;
    mux_d0_0 <= next_mux_d0_0;
    sel_d0_0 <= sel;
    sel_d1 <= sel_d0_0;
end


always @*
begin
    next_mux_d0_0 = mux_d0_0;

    if (sel_d0_0[2:0] == 0) begin
        next_mux_d0_0 = input_word_d[0];
    end else if (sel_d0_0[2:0] == 1) begin
        next_mux_d0_0 = input_word_d[1];
    end else if (sel_d0_0[2:0] == 2) begin
        next_mux_d0_0 = input_word_d[2];
    end else if (sel_d0_0[2:0] == 3) begin
        next_mux_d0_0 = input_word_d[3];
    end else if (sel_d0_0[2:0] == 4) begin
        next_mux_d0_0 = input_word_d[4];
    end else if (sel_d0_0[2:0] == 5) begin
        next_mux_d0_0 = input_word_d[5];
    end else if (sel_d0_0[2:0] == 6) begin
        next_mux_d0_0 = input_word_d[6];
    end else begin
        next_mux_d0_0 = input_word_d[7];
    end

end

endmodule
