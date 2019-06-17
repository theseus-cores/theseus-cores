/*****************************************************************************/
//
// Author : PJV
// File : count_cycle_cw16_65
// Description : Implement simple count / data alignment logic while optimizing pipelining.
//                Useful for aligning data with addition of metadata
//
//
/*****************************************************************************/

module count_cycle_cw16_65 #( 
    parameter DATA_WIDTH=32,
    parameter TUSER_WIDTH=32)
(
    input clk,
    input sync_reset,

    input s_axis_tvalid,
    input [DATA_WIDTH-1:0] s_axis_tdata,
    input [15:0] cnt_limit,
    input [TUSER_WIDTH-1:0] s_axis_tuser,
    input s_axis_tlast,
    output s_axis_tready,

    output m_axis_tvalid,
    output [DATA_WIDTH-1:0] m_axis_tdata,
    output m_axis_final_cnt,
    output [TUSER_WIDTH-1:0] m_axis_tuser,
    output [15:0] count,
    output m_axis_tlast,
    input m_axis_tready
);


localparam DATA_MSB = DATA_WIDTH - 1;
localparam TUSER_MSB = TUSER_WIDTH - 1;
reg [DATA_MSB:0] data_d0;
reg [DATA_MSB:0] data_d1;
reg [TUSER_MSB:0] tuser_d[0:1];
reg [1:0] tlast_d;

reg startup, next_startup;
wire almost_full;

wire m_fifo_tvalid;
wire [DATA_WIDTH + 16:0] m_fifo_tdata;
wire m_fifo_tready;
wire [23:0] m_fifo_tuser;
wire m_fifo_tlast;
reg [8:0] cnt_nib0, next_cnt_nib0;
reg [8:0] cnt_nib1, next_cnt_nib1;

reg [7:0] cnt_nib0_d0;

wire [15:0] count_s;
reg reset_cnt, next_reset_cnt;

wire [7:0] mask0;
wire [7:0] mask1;

wire take_data, tready_s;
wire final_cnt, cnt_reset;
wire fifo_tready;
wire [DATA_WIDTH + 16:0] fifo_tdata;
wire cnt_reset_0;
reg take_d0;
reg take_d1;

assign fifo_tdata = {final_cnt, count_s, data_d1};
assign m_axis_tvalid = m_fifo_tvalid;
assign m_axis_tdata = m_fifo_tdata[DATA_MSB:0];
assign m_fifo_tready = m_axis_tready;
assign m_axis_final_cnt = m_fifo_tdata[DATA_WIDTH + 16];
assign m_axis_tlast = m_fifo_tlast;
assign m_axis_tuser = m_fifo_tuser;
assign tready_s = ~almost_full;
assign take_data = s_axis_tvalid & tready_s & !sync_reset;
assign s_axis_tready = tready_s;
assign final_cnt = (count_s == cnt_limit) ? 1'b1 : 1'b0;
assign cnt_reset_0 = (cnt_nib0_d0 == mask0 && cnt_nib1[7:0] == mask1) ? 1'b1 : 1'b0;
assign cnt_reset = (cnt_nib0[7:0] == mask0 && next_cnt_nib1[7:0] == mask1) ? 1'b1 : 1'b0;

assign count_s = {cnt_nib1[7:0], cnt_nib0_d0};
assign count = m_fifo_tdata[DATA_WIDTH + 15:DATA_WIDTH];

assign mask0 = cnt_limit[7:0];
assign mask1 = cnt_limit[15:8];

always @(posedge clk)
begin
	if (sync_reset) begin
        reset_cnt <= 1'b0;
        cnt_nib0 <= 0;
        cnt_nib1 <= 0;
        startup <= 1'b1;
	end else begin
        reset_cnt <= next_reset_cnt;
        cnt_nib0 <= next_cnt_nib0;
        cnt_nib1 <= next_cnt_nib1;
        startup <= next_startup;
	end
end


// delay process
always @(posedge clk)
begin
    cnt_nib0_d0 <= cnt_nib0[7:0];

    data_d0 <= s_axis_tdata;
    data_d1 <= data_d0;
    tuser_d[0] <= s_axis_tuser;
    tuser_d[1] <= tuser_d[0];
    tlast_d[0] <= s_axis_tlast;
    tlast_d[1] <= tlast_d[0];
    take_d0 <= take_data;
    take_d1 <= take_d0;
end


// input and count process;
always @*
begin
    next_cnt_nib0 = cnt_nib0;
    next_cnt_nib1 = cnt_nib1;
    next_reset_cnt = reset_cnt;
    next_startup = startup;
    if (take_data) begin
        next_reset_cnt = cnt_reset;
        if (cnt_reset | startup) begin
            next_cnt_nib0 = 0;
        end else begin
            next_cnt_nib0 = cnt_nib0[7:0] + 1;
        end
        next_startup = 1'b0;
    end

    if (reset_cnt | cnt_reset_0) begin
        next_cnt_nib1 = 0;
    end else if (take_d0) begin
        next_cnt_nib1 = cnt_nib1[7:0] + cnt_nib0[8];
    end

end


axi_fifo_51 #(
    .DATA_WIDTH(DATA_WIDTH + 17),
    .ALMOST_FULL_THRESH(5),
    .TUSER_WIDTH(TUSER_WIDTH),
    .ADDR_WIDTH(3))
u_fifo
(
    .clk(clk),
    .sync_reset(sync_reset),

    .s_axis_tvalid(take_d1),
    .s_axis_tdata(fifo_tdata),
    .s_axis_tuser(tuser_d[1]),
    .s_axis_tlast(tlast_d[1]),
    .s_axis_tready(fifo_tready),

    .almost_full(almost_full),

    .m_axis_tvalid(m_fifo_tvalid),
    .m_axis_tdata(m_fifo_tdata),
    .m_axis_tuser(m_fifo_tuser),
    .m_axis_tlast(m_fifo_tlast),
    .m_axis_tready(m_fifo_tready)
);

endmodule
