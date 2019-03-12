//***************************************************************************--
//
// Author : PJV
// File : output_buffer
// Description : Output buffer to the M/2 Polyphase Channelizer Synthesis bank.
//      Buffer is hardcoded for a Maximum number of channels equal to 2048.
//      Can be any power of 2 less than that.
//
//***************************************************************************--
// no timescale needed
module output_buffer#(
    parameter [31:0] DATA_WIDTH = 32,
    parameter [31:0] FFT_SIZE_WIDTH=12)
(
    input clk,
    input sync_reset,

    input s_axis_tvalid,
    input [DATA_WIDTH - 1:0] s_axis_tdata,
    input s_axis_tlast,
    output s_axis_tready,

    input[FFT_SIZE_WIDTH - 2:0] phase_in,
    input[FFT_SIZE_WIDTH - 1:0] fft_size,
    output [FFT_SIZE_WIDTH - 2:0] phase_out,

    output m_axis_tvalid,
    output [DATA_WIDTH - 1:0] m_axis_tdata,
    output m_axis_final_cnt,
    input m_axis_tready
);

localparam ADDR_WIDTH = FFT_SIZE_WIDTH - 2;
localparam ADDR_MSB = ADDR_WIDTH - 1;
localparam SAMPLE_WIDTH = DATA_WIDTH >> 1;

localparam PAD_IN_BITS = 15 - ADDR_WIDTH;
localparam PAD_OUT_BITS = 17 - ADDR_WIDTH;

wire [PAD_IN_BITS-1:0] PAD_IN := {PAD_IN_BITS{1'b0}};
wire [PAD_OUT_BITS-1:0] PAD_OUT := {PAD_OUT_BITS{1'b0}}

wire [15:0] cnt_limit_out;  // write address roll over values.
reg [FFT_SIZE_WIDTH - 1:0] wr_roll_over_s;
wire [ADDR_WIDTH:0] wr_roll_over;
wire [ADDR_MSB:0] phase_wr;
reg [ADDR_WIDTH:0] half_cnt;  // Read address roll over values
reg [ADDR_WIDTH:0] roll_over_s;
wire [ADDR_MSB:0] roll_over, roll_over_m1;
reg tready;  // Ping Pong RAM signals.
wire [ADDR_MSB - 1:0] wr_addr0, wr_addr1;
wire [ADDR_MSB - 1:0] rd_addr0, rd_addr1;

reg [ADDR_WIDTH:0] wr_ptr0, next_wr_ptr0;
reg [ADDR_WIDTH:0] wr_ptr1, next_wr_ptr1;
reg [ADDR_WIDTH:0] rd_ptr0, next_rd_ptr0;
reg [ADDR_WIDTH:0] rd_ptr1, next_rd_ptr1;

reg [DATA_WIDTH - 1:0] wr_data, next_wr_data;
reg wr_side, next_wr_side;
reg rd_side, next_rd_side;

wire [DATA_WIDTH - 1:0] rd_data0_top, rd_data0_bottom, rd_data1_top, rd_data1_bottom;
reg rd_en, next_rd_en;
reg we0, next_we0;
reg we1, next_we1;
wire we0_top, we0_bottom;
wire we1_top, we1_bottom;

wire full0, full1;  // read state type

localparam S_IDLE=0, S_READ0=1, S_READ1=2;
reg [1:0] state, next_state;
reg start_sig, next_start_sig;  // start count
// delay signals to offset for 3 cycle latency through the RAMs.
reg [2:0] rd_en_d, rd_side_d, start_sig_d;  // signal rd_mux, next_rd_mux : std_logic;

reg [(DATA_WIDTH * 2) - 1:0] rd_tdata, next_rd_tdata;
wire [DATA_WIDTH - 1:0] out_tdata;
reg rd_tvalid, next_rd_tvalid;
reg bottom_active, next_bottom_active;
reg [3:0] rd_tvalid_d, rd_start_d;
reg rd_start, next_rd_start;
wire rd_tready, almost_full;
reg rd0_finish, next_rd0_finish, rd1_finish, next_rd1_finish;
wire [SAMPLE_WIDTH - 1:0] a_i, a_q, d_i, d_q;
wire [SAMPLE_WIDTH - 1:0] i_out, q_out;
wire [15:0] phase_s;
wire write0, write1;

assign rd_tready = ~almost_full;
assign phase_out = phase_s[FFT_SIZE_WIDTH - 2:0];
assign phase_wr = phase_in[ADDR_MSB:0];
assign roll_over = roll_over_s[ADDR_MSB:0];
assign roll_over_m1 = {roll_over_s[ADDR_MSB:1],1'b0};
assign wr_roll_over = wr_roll_over_s[ADDR_WIDTH:0];
assign cnt_limit_out = {PAD_OUT,roll_over};
assign s_axis_tready = tready;
assign full0 = (wr_ptr0[ADDR_WIDTH] != rd_ptr0[ADDR_WIDTH] && rd0_finish == 1'b0) ? 1'b1 : 1'b0;
assign full1 = (wr_ptr1[ADDR_WIDTH] != rd_ptr1[ADDR_WIDTH] && rd1_finish == 1'b0) ? 1'b1 : 1'b0;
assign wr_addr0 = wr_ptr0[ADDR_MSB - 1:0];
assign wr_addr1 = wr_ptr1[ADDR_MSB - 1:0];
assign a_i = rd_tdata[(4 * SAMPLE_WIDTH) - 1:3 * SAMPLE_WIDTH];
assign a_q = rd_tdata[(3 * SAMPLE_WIDTH) - 1:2 * SAMPLE_WIDTH];
assign d_i = rd_tdata[(2 * SAMPLE_WIDTH) - 1:SAMPLE_WIDTH];
assign d_q = rd_tdata[SAMPLE_WIDTH - 1:0];
assign out_tdata = {i_out,q_out};
assign rd_addr0 = rd_ptr0[ADDR_MSB - 1:0];
assign rd_addr1 = rd_ptr1[ADDR_MSB - 1:0];
assign write0 = (wr_side == 1'b0 && tready == 1'b1 && s_axis_tvalid == 1'b1) ? 1'b1 : 1'b0;
assign write1 = (wr_side == 1'b1 && tready == 1'b1 && s_axis_tvalid == 1'b1) ? 1'b1 : 1'b0;
assign we0_top = we0 &  ~bottom_active;
assign we0_bottom = we0 & bottom_active;
assign we1_top = we1 &  ~bottom_active;
assign we1_bottom = we1 & bottom_active;

// main clock process
always @(posedge clk, posedge sync_reset)
begin
    if (sync_reset == 1'b1) begin
        wr_ptr0 <= 0;
        wr_ptr1 <= 0;
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
        bottom_active <= 1'b0;
    end else begin
        wr_ptr0 <= next_wr_ptr0;
        wr_ptr1 <= next_wr_ptr1;
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
        bottom_active <= next_bottom_active;
    end
end

always @(posedge clk) begin
    we0 <= next_we0;
    we1 <= next_we1;
    wr_data <= next_wr_data;
    rd_en_d <= {rd_en_d[1:0],rd_en};
    rd_side_d <= {rd_side_d[1:0],rd_side};
    start_sig_d <= {start_sig_d[1:0],start_sig};
    wr_roll_over_s <= (fft_size) - 1;
    roll_over_s <= (fft_size[FFT_SIZE_WIDTH - 1:1]) - 1;
    half_cnt <= fft_size[FFT_SIZE_WIDTH - 1:1];
    rd_tvalid_d <= {rd_tvalid_d[2:0],rd_tvalid};
    rd_start_d <= {rd_start_d[2:0],rd_start};
end

always @*
begin
    tready = 1'b0;
    next_we0 = 1'b0;
    next_we1 = 1'b0;
    next_wr_data = 0;
    next_wr_ptr0 = wr_ptr0;
    next_wr_ptr1 = wr_ptr1;
    next_wr_side = wr_side;
    next_bottom_active = bottom_active;
    if (s_axis_tvalid == 1'b1) begin
        if (phase_in == 0) begin
            next_bottom_active = 1'b0;
        end else if (phase_in == half_cnt) begin
            next_bottom_active = 1'b1;
        end
        if (wr_side == 1'b0) begin
            if (full0 == 1'b0) begin
                next_we0 = 1'b1;
                tready = 1'b1;
                next_wr_data = s_axis_tdata;
                if (phase_in == wr_roll_over) begin
                    next_wr_ptr0 = {1'b1, phase_wr & roll_over};
                    next_wr_side = 1'b1;
                end else begin
                    next_wr_ptr0 = {1'b0, phase_wr & roll_over};
                end
            end
        end else begin
            if (full1 == 1'b0) begin
                next_we1 = 1'b1;
                tready = 1'b1;
                next_wr_data = s_axis_tdata;
                if((phase_in == wr_roll_over)) begin
                    next_wr_ptr1 = {1'b1, phase_wr & roll_over};
                    next_wr_side = 1'b0;
                end else begin
                    next_wr_ptr1 = {1'b0, phase_wr & roll_over};
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
                if (rd_ptr0 == roll_over_m1) begin
                    next_rd0_finish = 1'b1;
                    next_state = S_IDLE;
                end
            end
        end
        S_READ1 : begin
            if (write0 == 1'b1) begin
                next_rd0_finish = 1'b0;
            end
            if (rd_tready == 1'b1) begin
                next_rd_en = 1'b1;
                next_rd_ptr1 = rd_ptr1 + 1;
                if((rd_ptr1 == (roll_over_m1))) begin
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
            next_rd_tdata = {rd_data0_top,rd_data0_bottom};
        end else begin
            next_rd_tdata = {rd_data1_top,rd_data1_bottom};
        end
    end
end

  // latency = 3
  dp_block_read_first_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH - 1))
  u_ram_0_top(
    .clk(clk),
    .wea(we0_top),
    .addra(wr_addr0),
    .addrb(rd_addr0),
    .dia(wr_data),
    .dob(rd_data0_top));

  dp_block_read_first_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH - 1))
  u_ram_0_bottom(
    .clk(clk),
    .wea(we0_bottom),
    .addra(wr_addr0),
    .addrb(rd_addr0),
    .dia(wr_data),
    .dob(rd_data0_bottom));

  // latency = 3
  dp_block_read_first_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH - 1))
  u_ram_1_top(
    .clk(clk),
    .wea(we1_top),
    .addra(wr_addr1),
    .addrb(rd_addr1),
    .dia(wr_data),
    .dob(rd_data1_top));

  // latency = 3
  dp_block_read_first_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH - 1))
  u_ram_1_bottom(
    .clk(clk),
    .wea(we1_bottom),
    .addra(wr_addr1),
    .addrb(rd_addr1),
    .dia(wr_data),
    .dob(rd_data1_bottom));

  // latency = 4
  dsp48_output_add u_dadd_i(
    .clk(clk),
    .a(a_i),
    .d(d_i),
    .p(i_out));

  // latency = 4
  dsp48_output_add u_dadd_q(
    .clk(clk),
    .a(a_q),
    .d(d_q),
    .p(q_out));

  count_cycle_cw16_18 #(
    .DATA_WIDTH(32))
  u_out_count(
    .clk(clk),
    .sync_reset(sync_reset),
    .s_axis_tvalid(rd_tvalid_d[3]),
    .s_axis_tdata(out_tdata),
    .cnt_limit(cnt_limit_out),
    .start_sig(rd_start_d[3]),
    .s_axis_tready(),
    .af(almost_full),

    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata),
    .m_axis_final_cnt(m_axis_final_cnt),
    .count(phase_s),
    .m_axis_tready(m_axis_tready));


endmodule
