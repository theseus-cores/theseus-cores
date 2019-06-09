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
module downselect#(
    parameter DATA_WIDTH = 32,
(
    input clk,
    input sync_reset,

    input s_axis_tvalid,
    input [DATA_WIDTH-1:0] s_axis_tdata,
    input [23:0] s_axis_tuser,
    input s_axis_tlast,
    output s_axis_tready,

    input [15:0] packet_length,
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

localparam S_DUMP = 0, S_START_PKT = 1, S_PASS = 2;
reg [1:0] flow_state, next_flow_state;

localparam S_WAIT_TLAST = 0, S_DELAY = 1, S_REG_MASK= 2, S_COUNT = 3;
reg [1:0] count_state, next_count_state;

// downselection registers.
reg [2047:0] select_reg, next_select_reg;
reg [2047:0] mask_reg, 0 next_mask_reg;
reg [5:0] select_addr, next_select_addr;
reg select_take_d1;
reg [31:0] select_dina, next_select_dina;
wire select_take;
reg select_tready;

// bit count registers.
reg [15:0] bit_count, next_bit_count;
reg [10:0] mask_idx, next_mask_idx;
reg new_mask, next_new_mask;
reg count_done, next_count_done;
reg [15:0] space_avail, next_space_avail;

wire [10:0] curr_channel;
wire [2047:0] chan_one_hot;
wire s_axis_tready_s;
wire almost_full;
wire [10:0] curr_channel;

// down selection signals.
assign select_take = s_axis_select_tvalid & select_tready;
assign take_data = s_axis_tvalid & s_axis_tready_s;
assign s_axis_tread = s_axis_tready_s;
assign curr_channel = s_axis_tuser[10:0];

always @(posedge clk, posedge sync_reset)
begin
    if (sync_reset == 1'b1) begin
        count_state <= S_WAIT_TLAST;
        flow_state <= S_DUMP;
        select_tready <= 1'b0;
        select_addr <= 6'd0;
        select_dina <= 32'd0;
        new_mask <= 1'b1;
        bit_count <= 16'd0;
        mask_idx <= 11'd0;
        count_done <= 1'b0;
        space_avail <= 16'd0;
    end else begin
        count_state <= next_count_state;
        flow_state <= next_flow_state;
        select_tready <= 1'b1;
        select_addr <= next_select_addr;
        select_dina <= next_select_dina;
        new_mask <= next_new_mask;
        bit_count <= next_bit_count;
        mask_idx <= next_mask_idx;
        count_done <= next_count_done;
        space_avail <= next_space_avail;
    end
end

always @(posedge clk)
begin
    mask_reg <= next_mask_reg;
    select_reg <= next_select_reg;
end


// flow control state machine
always @*
begin
    next_flow_state = flow_state;
    next_space_avail = space_avail;
    s_axis_tready_s = 1'b0;
    case(flow_state)
        S_DUMP :
        begin
            if (count_done == 1'b1 && s_axis_tvalid == 1'b1 && s_axis_tuser == ) begin
                next_flow_state = S_START_PKT;
                next_space_avail = payload_length - bit_count;
            end else begin
                s_axis_tready_s = 1'b1;
            end
        end
        S_START_PKT :
        begin
            next_count_state = S_REG_MASK;
        end
        default :
        begin
        end
    endcase
end

// bit counter state machine
always @*
begin
    next_count_state = count_state;
    next_mask_reg = mask_reg;
    next_mask_idx = mask_idx;
    next_bit_count = bit_count;
    next_count_done = count_done;
    case(count_state)
        S_WAIT_TLAST :
        begin
            if (s_axis_select_tlast == 1'b1 && select_take == 1'b1) begin
                next_count_state = S_DELAY;
                next_count_done = 1'b0;
            end
        end
        S_DELAY :
        begin
            next_count_state = S_REG_MASK;
        end
        S_REG_MASK :
        begin
            next_mask_reg = select_reg;
            next_count_state = S_COUNT;
            next_mask_idx = 11'd0;
            next_bit_count = 12'd0;
        end
        S_COUNT :
        begin
            next_mask_idx = mask_idx + 1;
            if (mask_reg[mask_idx] == 1'b1) begin
                next_bit_count = bit_count + 1;
            end
            if (mask_idx == 11'd2047) begin
                next_count_state = S_WAIT_TLAST;
                next_count_done = 1'b1;
            end
        end
        default :
        begin
        end
    endcase
end


// down selection register writes
integer n;
always @*
begin
    next_select_addr = select_addr;
    next_select_dina = select_dina;
    next_new_mask = new_mask;
    if (select_take == 1'b1) begin
        next_select_dina = s_axis_select_tdata;
        if (new_mask == 1'b1) begin
            next_select_addr = 0;
            next_new_mask = 1'b0;
        end else begin
            next_select_addr = select_addr + 1;
            if (s_axis_select_tlast == 1'b1) begin
                next_new_mask = 1'b1;
            end
        end
    end
    // implements the write address pointer for tap updates.
    next_select_reg = select_reg;
    if (select_take_d1 == 1'b1) begin
        case (select_addr)
            6'd0: next_select_reg(31 downto 0) = select_dina;
            6'd1: next_select_reg(63 downto 32) = select_dina;
            6'd2: next_select_reg(95 downto 64) = select_dina;
            6'd3: next_select_reg(127 downto 96) = select_dina;
            6'd4: next_select_reg(159 downto 128) = select_dina;
            6'd5: next_select_reg(191 downto 160) = select_dina;
            6'd6: next_select_reg(223 downto 192) = select_dina;
            6'd7: next_select_reg(255 downto 224) = select_dina;
            6'd8: next_select_reg(287 downto 256) = select_dina;
            6'd9: next_select_reg(319 downto 288) = select_dina;
            6'd10: next_select_reg(351 downto 320) = select_dina;
            6'd11: next_select_reg(383 downto 352) = select_dina;
            6'd12: next_select_reg(415 downto 384) = select_dina;
            6'd13: next_select_reg(447 downto 416) = select_dina;
            6'd14: next_select_reg(479 downto 448) = select_dina;
            6'd15: next_select_reg(511 downto 480) = select_dina;
            6'd16: next_select_reg(543 downto 512) = select_dina;
            6'd17: next_select_reg(575 downto 544) = select_dina;
            6'd18: next_select_reg(607 downto 576) = select_dina;
            6'd19: next_select_reg(639 downto 608) = select_dina;
            6'd20: next_select_reg(671 downto 640) = select_dina;
            6'd21: next_select_reg(703 downto 672) = select_dina;
            6'd22: next_select_reg(735 downto 704) = select_dina;
            6'd23: next_select_reg(767 downto 736) = select_dina;
            6'd24: next_select_reg(799 downto 768) = select_dina;
            6'd25: next_select_reg(831 downto 800) = select_dina;
            6'd26: next_select_reg(863 downto 832) = select_dina;
            6'd27: next_select_reg(895 downto 864) = select_dina;
            6'd28: next_select_reg(927 downto 896) = select_dina;
            6'd29: next_select_reg(959 downto 928) = select_dina;
            6'd30: next_select_reg(991 downto 960) = select_dina;
            6'd31: next_select_reg(1023 downto 992) = select_dina;
            6'd32: next_select_reg(1055 downto 1024) = select_dina;
            6'd33: next_select_reg(1087 downto 1056) = select_dina;
            6'd34: next_select_reg(1119 downto 1088) = select_dina;
            6'd35: next_select_reg(1151 downto 1120) = select_dina;
            6'd36: next_select_reg(1183 downto 1152) = select_dina;
            6'd37: next_select_reg(1215 downto 1184) = select_dina;
            6'd38: next_select_reg(1247 downto 1216) = select_dina;
            6'd39: next_select_reg(1279 downto 1248) = select_dina;
            6'd40: next_select_reg(1311 downto 1280) = select_dina;
            6'd41: next_select_reg(1343 downto 1312) = select_dina;
            6'd42: next_select_reg(1375 downto 1344) = select_dina;
            6'd43: next_select_reg(1407 downto 1376) = select_dina;
            6'd44: next_select_reg(1439 downto 1408) = select_dina;
            6'd45: next_select_reg(1471 downto 1440) = select_dina;
            6'd46: next_select_reg(1503 downto 1472) = select_dina;
            6'd47: next_select_reg(1535 downto 1504) = select_dina;
            6'd48: next_select_reg(1567 downto 1536) = select_dina;
            6'd49: next_select_reg(1599 downto 1568) = select_dina;
            6'd50: next_select_reg(1631 downto 1600) = select_dina;
            6'd51: next_select_reg(1663 downto 1632) = select_dina;
            6'd52: next_select_reg(1695 downto 1664) = select_dina;
            6'd53: next_select_reg(1727 downto 1696) = select_dina;
            6'd54: next_select_reg(1759 downto 1728) = select_dina;
            6'd55: next_select_reg(1791 downto 1760) = select_dina;
            6'd56: next_select_reg(1823 downto 1792) = select_dina;
            6'd57: next_select_reg(1855 downto 1824) = select_dina;
            6'd58: next_select_reg(1887 downto 1856) = select_dina;
            6'd59: next_select_reg(1919 downto 1888) = select_dina;
            6'd60: next_select_reg(1951 downto 1920) = select_dina;
            6'd61: next_select_reg(1983 downto 1952) = select_dina;
            6'd62: next_select_reg(2015 downto 1984) = select_dina;
            6'd63: next_select_reg(2047 downto 2016) = select_dina;

            default: next_select_reg(31 downto 0) = select_dina;
        endcase
    end
end


one_hot_11_2048 u_one_hot
(
    .clk(clk),
    .input_word(curr_channel),
    .output_word(chan_one_hot)
);


// Output fifo
axi_fifo_51 #(
    .DATA_WIDTH(32),
    .ALMOST_FULL_THRESH(16),
    .TUSER_WIDTH(24),
    .ADDR_WIDTH(6))
u_fifo(
    .clk(clk),
    .sync_reset(sync_reset),
    .s_axis_tvalid(take_d[23]),
    .s_axis_tdata(fifo_tdata),
    .s_axis_tlast(tlast_d[23]),
    .s_axis_tuser(tuser_d[23]),
    .s_axis_tready(),
    .almost_full(almost_full),
    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata),
    .m_axis_tlast(m_axis_tlast),
    .m_axis_tuser(m_axis_tuser_s),
    .m_axis_tready(m_axis_tready));

endmodule
