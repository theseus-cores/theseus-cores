//***************************************************************************--
//
// Author : PJV
// File : mem_ctrl_pfb_8Mmax_16iw_16ow_10tps.v
// Description : Memory controller used to load default coefficients into PFB.
// It also provides interface for loading new coefficients.
//
//***************************************************************************--
module mem_ctrl_pfb_8Mmax_16iw_16ow_10tps
(
    input clk,
    input sync_reset,

    input s_axis_reload_tvalid,
    input [31:0] s_axis_reload_tdata,
    input s_axis_reload_tlast,
    output s_axis_reload_tready,

    output [2:0] taps_addr,
    output [9:0] taps_we,
    output [24:0] taps_douta

);

reg [6:0] wr_addr, next_wr_addr;
reg [24:0] wr_data, next_wr_data;

reg [6:0] taps_addr_d1, taps_addr_d2, taps_addr_d3;
reg [6:0] taps_addr_int, next_taps_addr;
reg [9:0] taps_we_s, next_taps_we;

reg sync_reset_d1;

reg reload_tready = 1'b0;
reg next_reload_tready;
reg next_config, config_s;
reg config_d1, config_d2, config_d3;

reg new_coeffs, next_new_coeffs;
wire tap_take;
reg we;

assign taps_addr = taps_addr_d3;
assign taps_we = taps_we_s;
assign tap_take = reload_tready & s_axis_reload_tvalid;
assign s_axis_reload_tready = reload_tready;
// assign taps_dina = taps_dina_s;

localparam S_CONFIG = 0, S_IDLE = 1;
reg state = S_CONFIG;
reg next_state;
reg state_d1 = S_IDLE;

// clock and reset process
always @(posedge clk, posedge sync_reset)
begin
	if (sync_reset == 1'b1) begin
          new_coeffs <= 1'b1;
          wr_addr <= 0;
          wr_data <= 0;
          taps_we_s <= 0;
          taps_addr_int <= 0;
          reload_tready <= 1'b0;
          state <= S_CONFIG;
          state_d1 <= S_IDLE;
          config_s <= 1'b0;
	end else begin
          new_coeffs <= next_new_coeffs;
          wr_addr <= next_wr_addr;
          wr_data <= next_wr_data;
          taps_we_s <= next_taps_we;
          taps_addr_int <= next_taps_addr;
          reload_tready <= next_reload_tready;
          state <= next_state;
          state_d1 <= state;
          config_s <= next_config;
	end
end

// delay process.
always @(posedge clk)
begin
    taps_addr_d1 <= taps_addr_int;
    taps_addr_d2 <= taps_addr_d1;
    taps_addr_d3 <= taps_addr_d2;
    config_d1 <= config_s;
    config_d2 <= config_d1;
    config_d3 <= config_d2;
    we <= tap_take;
    sync_reset_d1 <= sync_reset;
end

// state machine.
always @*
begin
    next_state = state;
    next_taps_addr = taps_addr_int;
    next_reload_tready = reload_tready;
    next_config = 1'b0;
    case(state)
        S_CONFIG :
        begin
            if (taps_addr_int == 7'd78) begin
                next_state = S_IDLE;
            end
            if (state_d1 == S_IDLE) begin
                next_taps_addr = 0;
            end else begin
                next_taps_addr = taps_addr_int + 1;
            end
            next_config = 1'b1;
        end
        S_IDLE :
        begin
            if (sync_reset == 1'b1 && sync_reset_d1 == 1'b0) begin
                next_state = S_CONFIG;
                next_reload_tready = 1'b0;
            end else if (tap_take == 1'b1 && s_axis_reload_tlast == 1'b1) begin
                next_state = S_CONFIG;
                next_reload_tready = 1'b0;
            end else begin
                next_state = S_IDLE;
                next_reload_tready = 1'b1;
            end
        end
        default :
        begin
        end
    endcase
end

// write enable muxing .
always @*
begin
    next_wr_addr = wr_addr;
    next_wr_data = wr_data;

    next_new_coeffs = new_coeffs;
    if (tap_take == 1'b1) begin
        next_wr_data = s_axis_reload_tdata[24:0];
        if (new_coeffs == 1'b1) begin
            next_wr_addr = 0;
            next_new_coeffs = 1'b0;
        end else begin
            next_wr_addr = wr_addr + 1;
            if (s_axis_reload_tlast == 1'b1) begin
                next_new_coeffs = 1'b1;
            end
        end
    end
    // implements the write address pointer for tap updates.
    if (config_d2 == 1'b1) begin
        case (taps_addr_d2[6:3])
            4'd0: next_taps_we = 10'd1;
            4'd1: next_taps_we = 10'd2;
            4'd2: next_taps_we = 10'd4;
            4'd3: next_taps_we = 10'd8;
            4'd4: next_taps_we = 10'd16;
            4'd5: next_taps_we = 10'd32;
            4'd6: next_taps_we = 10'd64;
            4'd7: next_taps_we = 10'd128;
            4'd8: next_taps_we = 10'd256;
            4'd9: next_taps_we = 10'd512;
            default: next_taps_we = 10'd0;
        endcase
    end else begin
        next_taps_we = 10'd0;
    end
end

// 3 cycle latency.
pfb_8Mmax_16iw_16ow_10tps_dp_rom coeff_mem (
  .clk(clk),
  .wea(we),
  .addra(wr_addr),
  .dia(wr_data),
  .addrb(taps_addr_int),
  .dob(taps_douta)
);


endmodule
