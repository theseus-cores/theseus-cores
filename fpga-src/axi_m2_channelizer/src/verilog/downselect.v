//***************************************************************************--
//
// Author : PJV
// File : downselect.v
// Description : Module performs downselection of channel based on a selection
// mask set from a RFNOC FIFO interface
//
//***************************************************************************--

// no timescale needed
//
module downselect
#(parameter DATA_WIDTH = 32)
(
    input clk,
    input sync_reset,

    input s_axis_tvalid,
    input [DATA_WIDTH-1:0] s_axis_tdata,
    input [23:0] s_axis_tuser,
    input s_axis_tlast,
    output s_axis_tready,

    input eob_tag,

    // down selection FIFO interface
    input s_axis_select_tvalid,
    input [31:0] s_axis_select_tdata,
    input s_axis_select_tlast,
    output s_axis_select_tready,

    output m_axis_tvalid,
    output [DATA_WIDTH-1:0] m_axis_tdata,
    output [23:0] m_axis_tuser,
    output m_axis_tlast,
    output eob_downselect,
    input m_axis_tready

);

localparam [2047:0] ZEROS = 2048'd0;

// downselection registers.
reg [2047:0] select_reg = 2048'd0;
reg [2047:0] next_select_reg = 2048'd0;
reg [5:0] select_addr, next_select_addr;
reg select_take_d1;
reg [31:0] select_dina, next_select_dina;
wire select_take;
reg select_tready;

reg load_done, next_load_done, load_done_d1;

reg [4:0] take_d;
reg [5:0] tlast_d;
reg [5:0] eob_tag_d;
reg [DATA_WIDTH-1:0] tdata_d[0:5];
reg [23:0] tuser_d[0:5];
wire [24:0] tuser_s, m_axis_tuser_s;
reg push, next_push;

wire mask_value;

// bit count registers.
reg new_mask, next_new_mask;

wire [10:0] curr_channel, chan_out;
wire almost_full;
wire take_data;

// down selection signals.
assign select_take = s_axis_select_tvalid & select_tready;
assign take_data = s_axis_tvalid & ~almost_full & load_done_d1;
assign s_axis_tready = ~almost_full & load_done_d1;
assign curr_channel = s_axis_tuser[10:0];
assign s_axis_select_tready = 1'b1;
assign tuser_s = {eob_tag_d[5], tuser_d[5]};
assign eob_downselect = m_axis_tuser_s[24];
assign m_axis_tuser = m_axis_tuser_s[23:0];

always @(posedge clk, posedge sync_reset)
begin
    if (sync_reset == 1'b1) begin
        select_tready <= 1'b0;
        select_addr <= 6'd0;
        select_dina <= 32'd0;
        new_mask <= 1'b1;
        load_done <= 1'b0;
        push <= 1'b0;
    end else begin
        select_tready <= 1'b1;
        select_addr <= next_select_addr;
        select_dina <= next_select_dina;
        new_mask <= next_new_mask;
        load_done <= next_load_done;
        push <= next_push;
    end
end

integer n;
always @(posedge clk)
begin
    select_reg <= next_select_reg;
    select_take_d1 <= select_take;
    load_done_d1 <= load_done;

    take_d <= {take_d[3:0], take_data};
    tlast_d <= {tlast_d[4:0], s_axis_tlast};
    eob_tag_d <= {eob_tag_d[4:0], eob_tag};

    tdata_d[0] <= s_axis_tdata;
    tuser_d[0] <= s_axis_tuser;
    for (n=1;n<6; n=n+1) begin
        tdata_d[n] <= tdata_d[n-1];
        tuser_d[n] <= tuser_d[n-1];
    end
end


// down selection register writes
always @*
begin
    next_select_addr = select_addr;
    next_select_dina = select_dina;
    next_new_mask = new_mask;
    next_load_done = load_done;
    if (select_take == 1'b1) begin
        next_select_dina = s_axis_select_tdata;
        if (new_mask == 1'b1) begin
            next_select_addr = 0;
            next_new_mask = 1'b0;
            next_load_done = 1'b0;
        end else begin
            next_select_addr = select_addr + 1;
            if (s_axis_select_tlast == 1'b1) begin
                next_new_mask = 1'b1;
                next_load_done = 1'b1;
            end
        end
    end
    // implements the write address pointer for tap updates.
    next_select_reg = select_reg;
    if (select_take_d1 == 1'b1) begin
        case (select_addr)
            6'd0: next_select_reg[31:0] = select_dina;
            6'd1: next_select_reg[63:32] = select_dina;
            6'd2: next_select_reg[95:64] = select_dina;
            6'd3: next_select_reg[127:96] = select_dina;
            6'd4: next_select_reg[159:128] = select_dina;
            6'd5: next_select_reg[191:160] = select_dina;
            6'd6: next_select_reg[223:192] = select_dina;
            6'd7: next_select_reg[255:224] = select_dina;
            6'd8: next_select_reg[287:256] = select_dina;
            6'd9: next_select_reg[319:288] = select_dina;
            6'd10: next_select_reg[351:320] = select_dina;
            6'd11: next_select_reg[383:352] = select_dina;
            6'd12: next_select_reg[415:384] = select_dina;
            6'd13: next_select_reg[447:416] = select_dina;
            6'd14: next_select_reg[479:448] = select_dina;
            6'd15: next_select_reg[511:480] = select_dina;
            6'd16: next_select_reg[543:512] = select_dina;
            6'd17: next_select_reg[575:544] = select_dina;
            6'd18: next_select_reg[607:576] = select_dina;
            6'd19: next_select_reg[639:608] = select_dina;
            6'd20: next_select_reg[671:640] = select_dina;
            6'd21: next_select_reg[703:672] = select_dina;
            6'd22: next_select_reg[735:704] = select_dina;
            6'd23: next_select_reg[767:736] = select_dina;
            6'd24: next_select_reg[799:768] = select_dina;
            6'd25: next_select_reg[831:800] = select_dina;
            6'd26: next_select_reg[863:832] = select_dina;
            6'd27: next_select_reg[895:864] = select_dina;
            6'd28: next_select_reg[927:896] = select_dina;
            6'd29: next_select_reg[959:928] = select_dina;
            6'd30: next_select_reg[991:960] = select_dina;
            6'd31: next_select_reg[1023:992] = select_dina;
            6'd32: next_select_reg[1055:1024] = select_dina;
            6'd33: next_select_reg[1087:1056] = select_dina;
            6'd34: next_select_reg[1119:1088] = select_dina;
            6'd35: next_select_reg[1151:1120] = select_dina;
            6'd36: next_select_reg[1183:1152] = select_dina;
            6'd37: next_select_reg[1215:1184] = select_dina;
            6'd38: next_select_reg[1247:1216] = select_dina;
            6'd39: next_select_reg[1279:1248] = select_dina;
            6'd40: next_select_reg[1311:1280] = select_dina;
            6'd41: next_select_reg[1343:1312] = select_dina;
            6'd42: next_select_reg[1375:1344] = select_dina;
            6'd43: next_select_reg[1407:1376] = select_dina;
            6'd44: next_select_reg[1439:1408] = select_dina;
            6'd45: next_select_reg[1471:1440] = select_dina;
            6'd46: next_select_reg[1503:1472] = select_dina;
            6'd47: next_select_reg[1535:1504] = select_dina;
            6'd48: next_select_reg[1567:1536] = select_dina;
            6'd49: next_select_reg[1599:1568] = select_dina;
            6'd50: next_select_reg[1631:1600] = select_dina;
            6'd51: next_select_reg[1663:1632] = select_dina;
            6'd52: next_select_reg[1695:1664] = select_dina;
            6'd53: next_select_reg[1727:1696] = select_dina;
            6'd54: next_select_reg[1759:1728] = select_dina;
            6'd55: next_select_reg[1791:1760] = select_dina;
            6'd56: next_select_reg[1823:1792] = select_dina;
            6'd57: next_select_reg[1855:1824] = select_dina;
            6'd58: next_select_reg[1887:1856] = select_dina;
            6'd59: next_select_reg[1919:1888] = select_dina;
            6'd60: next_select_reg[1951:1920] = select_dina;
            6'd61: next_select_reg[1983:1952] = select_dina;
            6'd62: next_select_reg[2015:1984] = select_dina;
            6'd63: next_select_reg[2047:2016] = select_dina;

            default: next_select_reg[31:0] = select_dina;
        endcase
    end
end

// selection logic.
always @*
begin
    next_push = 1'b0;
    if (take_d[4] == 1'b1 && mask_value == 1'b1) begin  // output fifo is not full and not loading new select_reg.
        next_push = 1'b1;
    end
end


// 5 tick delay
pipe_mux_2048_1 u_pipe_mux
(
    .clk(clk),
    .sync_reset(sync_reset),
    .valid_i(1'b1),
    .sel(curr_channel),
    .input_word(select_reg),
    .valid_o(),
    .sel_o(chan_out),
    .output_word(mask_value)
);


// Output fifo
axi_fifo_51 #(
    .DATA_WIDTH(32),
    .ALMOST_FULL_THRESH(20),
    .TUSER_WIDTH(25),
    .ADDR_WIDTH(5))
u_fifo(
    .clk(clk),
    .sync_reset(sync_reset),
    .s_axis_tvalid(push),
    .s_axis_tdata(tdata_d[5]),
    .s_axis_tlast(tlast_d[5]),
    .s_axis_tuser(tuser_s),
    .s_axis_tready(),
    .almost_full(almost_full),
    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata),
    .m_axis_tlast(m_axis_tlast),
    .m_axis_tuser(m_axis_tuser_s),
    .m_axis_tready(m_axis_tready));

endmodule
