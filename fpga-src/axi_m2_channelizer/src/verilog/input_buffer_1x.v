//***************************************************************************--
//
// Author : PJV
// File : input_buffer
// Description : Input buffer to the M Polyphase Channelizer bank.
//      Can be any power of 2 less than that.
//
//***************************************************************************--
module input_buffer_1x#(
    parameter DATA_WIDTH = 32,
    parameter FFT_SIZE_WIDTH = 12)
(
    input clk,
    input sync_reset,
    input s_axis_tvalid,
    input [DATA_WIDTH - 1:0] s_axis_tdata,
    output s_axis_tready,
    input [FFT_SIZE_WIDTH - 1:0] fft_size,
    output m_axis_tvalid,
    output [DATA_WIDTH - 1:0] m_axis_tdata,
    output m_axis_final_cnt,
    output [FFT_SIZE_WIDTH - 2:0] phase,
    input m_axis_tready
);

localparam ADDR_WIDTH = FFT_SIZE_WIDTH - 1;
localparam ADDR_MSB = ADDR_WIDTH - 1;
localparam PAD_BITS = 16 - ADDR_WIDTH;

wire [PAD_BITS-1:0] PAD = {PAD_BITS{1'b0}};

// input count signals.
wire [15:0] cnt_limit_in;
wire [15:0] cnt_limit_out;
wire count_tvalid;
wire [DATA_WIDTH - 1:0] count_tdata;
wire final_cnt;
wire [15:0] count;
reg count_tready;
wire [ADDR_MSB:0] roll_over;
wire [ADDR_MSB:0] roll_over_m1;
reg [ADDR_WIDTH:0] roll_over_s;  // Ping Pong RAM signals.
reg [FFT_SIZE_WIDTH-1:0] fft_size_m1;


wire [ADDR_WIDTH - 1:0] wr_addr0, wr_addr1;
wire [ADDR_WIDTH - 1:0] rd_addr0, rd_addr1;

reg [ADDR_WIDTH:0] wr_ptr0, next_wr_ptr0;
reg [ADDR_WIDTH:0] wr_ptr0_inv, next_wr_ptr0_inv;
reg [ADDR_WIDTH:0] wr_ptr1_inv, next_wr_ptr1_inv;
reg [ADDR_WIDTH:0] wr_ptr1, next_wr_ptr1;
reg [ADDR_WIDTH:0] rd_ptr0, next_rd_ptr0;
reg [ADDR_WIDTH:0] rd_ptr1, next_rd_ptr1;

reg [DATA_WIDTH - 1:0] wr_data, next_wr_data;
reg wr_side, next_wr_side;
reg rd_side, next_rd_side;
wire [DATA_WIDTH - 1:0] rd_data0, rd_data1;
reg rd_en, next_rd_en;
reg we0, next_we0;
reg we1, next_we1;
wire full0, full1;  // read state type

localparam S_IDLE=0, S_READ0=1, S_READ1=2;
reg [1:0] state, next_state;

reg start_sig, next_start_sig;  // start count
// delay signals to offset for 3 cycle latency through the RAMs.
reg [2:0] rd_en_d, rd_side_d, start_sig_d;  // signal rd_mux, next_rd_mux : std_logic;
reg [DATA_WIDTH - 1:0] rd_tdata, next_rd_tdata;
reg rd_tvalid, next_rd_tvalid;
reg rd_start, next_rd_start;
wire rd_tready;
wire almost_full;
reg rd0_finish, next_rd0_finish, rd1_finish, next_rd1_finish;

wire [15:0] phase_s;
wire write0, write1;

assign rd_tready = ~almost_full;
assign roll_over = roll_over_s[ADDR_MSB:0];
assign roll_over_m1 = {roll_over_s[ADDR_MSB:1],1'b0};
assign cnt_limit_in = {PAD,roll_over};
assign cnt_limit_out = {PAD,roll_over};
assign full0 = (wr_ptr0_inv[ADDR_WIDTH] != rd_ptr0[ADDR_WIDTH] && rd0_finish == 1'b0) ? 1'b1 : 1'b0;
assign full1 = (wr_ptr1_inv[ADDR_WIDTH] != rd_ptr1[ADDR_WIDTH] && rd1_finish == 1'b0) ? 1'b1 : 1'b0;
assign phase = phase_s[ADDR_WIDTH:0];
assign wr_addr0 = wr_ptr0[ADDR_MSB:0];
assign wr_addr1 = wr_ptr1[ADDR_MSB:0];
assign rd_addr0 = rd_ptr0[ADDR_MSB:0];
assign rd_addr1 = rd_ptr1[ADDR_MSB:0];
assign write0 = (wr_side == 1'b0 && count_tready == 1'b1 && count_tvalid == 1'b1) ? 1'b1 : 1'b0;
assign write1 = (wr_side == 1'b1 && count_tready == 1'b1 && count_tvalid == 1'b1) ? 1'b1 : 1'b0;

// main clock process
always @(posedge clk, posedge sync_reset) begin
    if (sync_reset == 1'b1) begin
        wr_ptr0 <= 0;
        wr_ptr1 <= 0;
        wr_ptr0_inv <= 0;
        wr_ptr1_inv <= 0;
        wr_side <= 1'b0;
        rd_ptr0 <= 0;
        rd_ptr1 <= 0;
        state <= S_IDLE;
        start_sig <= 1'b0;
        rd_tdata <= 0;
        rd_en <= 1'b0;
        rd_side <= 1'b1;
        rd_tvalid <= 1'b0;
        rd_start <= 1'b0;
        rd0_finish <= 1'b0;
        rd1_finish <= 1'b0;
    end else begin
        wr_ptr0 <= next_wr_ptr0;
        wr_ptr1 <= next_wr_ptr1;
        wr_ptr0_inv <= next_wr_ptr0_inv;
        wr_ptr1_inv <= next_wr_ptr1_inv;
        wr_side <= next_wr_side;
        rd_ptr0 <= next_rd_ptr0;
        rd_ptr1 <= next_rd_ptr1;
        state <= next_state;
        start_sig <= next_start_sig;
        rd_en <= next_rd_en;
        rd_side <= next_rd_side;
        rd_tdata <= next_rd_tdata;
        rd_tvalid <= next_rd_tvalid;
        rd_start <= next_rd_start;
        rd0_finish <= next_rd0_finish;
        rd1_finish <= next_rd1_finish;
    end
end

always @(posedge clk) begin
    we0 <= next_we0;
    we1 <= next_we1;
    wr_data <= next_wr_data;
    rd_en_d <= {rd_en_d[1:0], rd_en};
    rd_side_d <= {rd_side_d[1:0], rd_side};
    start_sig_d <= {start_sig_d[1:0], start_sig};
    roll_over_s <= fft_size - 1;
end

always @*
begin
    count_tready = 1'b0;
    next_we0 = 1'b0;
    next_we1 = 1'b0;
    next_wr_data = {(((DATA_WIDTH - 1))-((0))+1){1'b0}};
    next_wr_ptr0 = wr_ptr0;
    next_wr_ptr1 = wr_ptr1;
    next_wr_ptr0_inv = wr_ptr0_inv;
    next_wr_ptr1_inv = wr_ptr1_inv;
    next_wr_side = wr_side;
    if (count_tvalid == 1'b1) begin
        if (wr_side == 1'b0) begin
            if (full0 == 1'b0) begin
                next_we0 = 1'b1;
                count_tready = 1'b1;
                next_wr_data = count_tdata;
                if (final_cnt == 1'b1) begin
                    next_wr_ptr0 = {1'b1,count[ADDR_MSB:0]};
                    next_wr_ptr0_inv = {1'b1,roll_over & ( ~count[ADDR_MSB:0])};
                    next_wr_side = 1'b1;
                end else begin
                    next_wr_ptr0 = {1'b0,count[ADDR_MSB:0]};
                    next_wr_ptr0_inv = {1'b0,roll_over & ( ~count[ADDR_MSB:0])};
                end
            end
        end else begin
            if (full1 == 1'b0) begin
                next_we1 = 1'b1;
                count_tready = 1'b1;
                next_wr_data = count_tdata;
                if (final_cnt == 1'b1) begin
                    next_wr_ptr1 = {1'b1,count[ADDR_MSB:0]};
                    next_wr_ptr1_inv = {1'b1,roll_over & ( ~count[ADDR_MSB:0])};
                    next_wr_side = 1'b0;
                end else begin
                    next_wr_ptr1 = {1'b0, count[ADDR_MSB:0]};
                    next_wr_ptr1_inv = {1'b0, roll_over & ( ~count[ADDR_MSB:0])};
                end
            end
        end
    end
end

always @*
begin
    next_rd_ptr0 = rd_ptr0;
    next_rd_ptr1 = rd_ptr1;
    next_rd_side = rd_side;
    next_rd0_finish = rd0_finish;
    next_rd1_finish = rd1_finish;
    next_state = state;
    next_rd_en = 1'b0;
    next_start_sig = 1'b0;
    case(state)
        S_IDLE :
        begin
            if (rd_side == 1'b1 && full0 == 1'b1 && rd_tready == 1'b1) begin
                next_rd_side = 1'b0;
                next_rd_en = 1'b1;
                next_rd_ptr0 = 0;
                next_rd_ptr1 = 0;
                next_state = S_READ0;
                next_start_sig = 1'b1;
            end else if (rd_side == 1'b0 && full1 == 1'b1 && rd_tready == 1'b1) begin
                next_rd_side = 1'b1;
                next_rd_en = 1'b1;
                next_rd_ptr1 = 0;
                next_rd_ptr0 = 0;
                next_state = S_READ1;
                next_start_sig = 1'b1;
            end
            if (write0 == 1'b1) begin
                next_rd0_finish = 1'b0;
            end
            if (write1 == 1'b1) begin
                next_rd1_finish = 1'b0;
            end
        end
        S_READ0 :
        begin
            if (write1 == 1'b1) begin
                next_rd1_finish = 1'b0;
            end
            if (rd_tready == 1'b1) begin
                next_rd_en = 1'b1;
                next_rd_ptr0 = rd_ptr0 + 1;
                // if (rd_ptr0 == (roll_over_s)) begin
                //     next_rd_ptr0 = 0;
                // end else begin
                // end
                if (rd_ptr0 == (roll_over_m1)) begin
                    next_state = S_IDLE;
                    next_rd0_finish = 1'b1;
                end
            end
        end
        S_READ1 :
        begin
            if (write0 == 1'b1) begin
                next_rd0_finish <= 1'b0;
            end
            if (rd_tready == 1'b1) begin
                next_rd_en = 1'b1;
                next_rd_ptr1 = rd_ptr1 + 1;
                // if (rd_ptr1 == (roll_over_s)) begin
                //     next_rd_ptr1 = 0;
                // end else begin
                // end
                if (rd_ptr1 == (roll_over_m1)) begin
                  next_state = S_IDLE;
                  next_rd1_finish = 1'b1;
                end
            end
        end
        default :
        begin
        end
    endcase
end

always @*
begin
    next_rd_tvalid = 1'b0;
    next_rd_start = 1'b0;
    next_rd_tdata = rd_tdata;
    if (rd_en_d[2] == 1'b1) begin
        next_rd_start = start_sig_d[2];
        next_rd_tvalid = 1'b1;
        if (rd_side_d[2] == 1'b0) begin
            next_rd_tdata = rd_data0;
        end else begin
            next_rd_tdata = rd_data1;
        end
    end
end

count_cycle_cw16_8 #(
    .DATA_WIDTH(DATA_WIDTH))
u_in_count(
    .clk(clk),
    .sync_reset(sync_reset),
    .s_axis_tvalid(s_axis_tvalid),
    .s_axis_tdata(s_axis_tdata),
    .cnt_limit(cnt_limit_in),
    .s_axis_tready(s_axis_tready),
    .m_axis_tvalid(count_tvalid),
    .m_axis_tdata(count_tdata),
    .m_axis_final_cnt(final_cnt),
    .count(count),
    .m_axis_tready(count_tready)
);

// latency = 3
dp_block_read_first_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH))
u_ram_0(
    .clk(clk),
    .wea(we0),
    .addra(wr_addr0),
    .addrb(rd_addr0),
    .dia(wr_data),
    .dob(rd_data0)
);

  // latency = 3
dp_block_read_first_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH))
u_ram_1(
    .clk(clk),
    .wea(we1),
    .addra(wr_addr1),
    .addrb(rd_addr1),
    .dia(wr_data),
    .dob(rd_data1)
);

count_cycle_cw16_18 #(
    .DATA_WIDTH(32))
u_out_count(
    .clk(clk),
    .sync_reset(sync_reset),
    .s_axis_tvalid(rd_tvalid),
    .s_axis_tdata(rd_tdata),
    .cnt_limit(cnt_limit_out),
    .start_sig(rd_start),
    .s_axis_tready(open),
    .af(almost_full),
    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata),
    .m_axis_final_cnt(m_axis_final_cnt),
    .count(phase_s),
    .m_axis_tready(m_axis_tready)
);


endmodule
