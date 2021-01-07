//***************************************************************************--
//
// Author : PJV
// File : downselect.v
// Description : Module performs downselection of channel based on a selection
// mask set from a FIFO interface
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

// downselection registers.
reg [7:0] select_reg = 8'd0;
reg [7:0] next_select_reg = 8'd0;
reg [-3:0] select_addr, next_select_addr;
reg select_take_d1;
reg [31:0] select_dina, next_select_dina;
wire select_take;
reg select_tready;

reg load_done, next_load_done, load_done_d1;

reg [1:0] take_d;
reg [2:0] tlast_d;
reg [2:0] eob_tag_d;
reg [DATA_WIDTH-1:0] tdata_d[0:2];
reg [23:0] tuser_d[0:2];
wire [24:0] tuser_s, m_axis_tuser_s;
reg push, next_push;

wire mask_value;

// bit count registers.
reg new_mask, next_new_mask;

wire [2:0] curr_channel, chan_out;
wire almost_full;
wire take_data;

// down selection signals.
assign select_take = s_axis_select_tvalid & select_tready;
assign take_data = s_axis_tvalid & ~almost_full & load_done_d1;
assign s_axis_tready = ~almost_full & load_done_d1;
assign curr_channel = s_axis_tuser[2:0];
assign s_axis_select_tready = 1'b1;
assign tuser_s = {eob_tag_d[2], tuser_d[2]};
assign eob_downselect = m_axis_tuser_s[24];
assign m_axis_tuser = m_axis_tuser_s[23:0];

always @(posedge clk, posedge sync_reset)
begin
    if (sync_reset == 1'b1) begin
        select_tready <= 1'b0;
        select_addr <= -2'd0;
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

    take_d <= {take_d[0:0], take_data};
    tlast_d <= {tlast_d[1:0], s_axis_tlast};
    eob_tag_d <= {eob_tag_d[1:0], eob_tag};

    tdata_d[0] <= s_axis_tdata;
    tuser_d[0] <= s_axis_tuser;
    for (n=1;n<3; n=n+1) begin
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
            -2'd0: next_select_reg[31:0] = select_dina;
            default: next_select_reg[31:0] = select_dina;
        endcase
    end
end

// selection logic.
always @*
begin
    next_push = 1'b0;
    if (take_d[3] == 1'b1 && mask_value == 1'b1) begin  // output fifo is not full and not loading new select_reg.
        next_push = 1'b1;
    end
end


// 4 tick delay
pipe_mux_8_1 u_pipe_mux
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
    .s_axis_tdata(tdata_d[2]),
    .s_axis_tlast(tlast_d[2]),
    .s_axis_tuser(tuser_s),
    .s_axis_tready(),
    .almost_full(almost_full),
    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata),
    .m_axis_tlast(m_axis_tlast),
    .m_axis_tuser(m_axis_tuser_s),
    .m_axis_tready(m_axis_tready));

endmodule
