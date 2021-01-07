//***************************************************************************--
//
// Author : PJV
// File : input_buffer
// Description : The circular buffer implements the circular shifting functionality as
// specified in "A Versatile Multichannel Filter Bank with Multiple Channel Bandwidths" paper.
// It is implemented using multiple sample memores that allow the block to ping-pong between different memories.
// This mitigates the requirement to throttle the input data stream.Input buffer to the M/2 Polyphase Channelizer bank.
//      Buffer is hardcoded for a Maximum number of channels equal to 2048.
//      Can be any power of 2 less than that.
//
//***************************************************************************
module circ_buffer#(
    parameter DATA_WIDTH = 32,
    parameter FFT_SIZE_WIDTH = 12)
(
    input clk,
    input sync_reset,
    input s_axis_tvalid,
    input [DATA_WIDTH - 1:0] s_axis_tdata,
    input s_axis_tlast,
    output s_axis_tready,

    input [FFT_SIZE_WIDTH - 1:0] fft_size,
    input [FFT_SIZE_WIDTH - 2:0] phase,
    output [FFT_SIZE_WIDTH - 2:0] phase_out,

    output m_axis_tvalid,
    output [DATA_WIDTH - 1:0] m_axis_tdata,
    output m_axis_tlast,
    input m_axis_tready
);


localparam ADDR_WIDTH = FFT_SIZE_WIDTH - 1;
localparam ADDR_MSB = ADDR_WIDTH - 1;

reg we0, next_we0;
reg we1, next_we1;

reg full0, next_full0;
reg full1, next_full1;

reg [ADDR_MSB:0] wr_half;
reg [ADDR_WIDTH:0] wr_full;

reg [ADDR_MSB:0] wr_full_slice, wr_full_m1;
reg [ADDR_MSB:0] wr_ptr0, next_wr_ptr0;
reg [ADDR_MSB:0] wr_ptr1, next_wr_ptr1;
reg [ADDR_MSB:0] rd_ptr0, next_rd_ptr0;
reg [ADDR_MSB:0] rd_ptr1, next_rd_ptr1;

reg [ADDR_MSB:0] rd_ptr0_d0, rd_ptr0_d1, rd_ptr0_d2;
reg [ADDR_MSB:0] rd_ptr1_d0, rd_ptr1_d1, rd_ptr1_d2;

wire [ADDR_MSB:0] rd_addr0, rd_addr1;
wire [ADDR_MSB:0] wr_addr0, wr_addr1;

reg rd_side, next_rd_side;
reg wr_side, next_wr_side;

reg rd_en, next_rd_en;
wire [DATA_WIDTH - 1:0] rd_data0, rd_data1;
reg [DATA_WIDTH - 1:0] wr_data, next_wr_data;

wire [ADDR_MSB:0] phase_s;

reg [2:0] rd_side_d;
reg [2:0] rd_en_d;
reg [2:0] rd_tlast_d;
reg rd_tlast, next_rd_tlast;

reg tvalid_fifo, next_tvalid_fifo;
reg [DATA_WIDTH + ADDR_MSB:0] tdata_fifo, next_tdata_fifo;
wire [DATA_WIDTH + ADDR_MSB:0] m_axis_tdata_s;
wire [DATA_WIDTH + ADDR_MSB:0] tdata0, tdata1;
reg tlast_fifo, next_tlast_fifo;

wire almost_full;
wire take_data;

localparam S_IDLE = 0, S_READ0 = 1, S_READ1 = 2;
reg [1:0] state, next_state;

assign wr_addr0 = wr_ptr0;
assign wr_addr1 = wr_ptr1;

assign rd_addr0 = rd_ptr0;
assign rd_addr1 = rd_ptr1;
assign phase_s = phase;

assign take_data = (s_axis_tvalid == 1'b1 && almost_full == 1'b0) ? 1'b1 : 1'b0;

assign tdata0 = {rd_ptr0_d2,rd_data0};
assign tdata1 = {rd_ptr1_d2,rd_data1};

assign m_axis_tdata = m_axis_tdata_s[DATA_WIDTH - 1:0];
assign phase_out = m_axis_tdata_s[(DATA_WIDTH + ADDR_MSB):DATA_WIDTH];

assign s_axis_tready = ~almost_full;

// main clock process
always @(posedge clk, posedge sync_reset)
begin
    if (sync_reset == 1'b1) begin
        rd_side <= 1'b1;
        wr_ptr0 <= 0;
        wr_ptr1 <= 0;
        wr_side <= 1'b0;
        rd_ptr0 <= 0;
        rd_ptr1 <= 0;
        full0 <= 1'b0;
        full1 <= 1'b0;
        state <= S_IDLE;
    end else begin
        rd_side <= next_rd_side;
        wr_ptr0 <= next_wr_ptr0;
        wr_ptr1 <= next_wr_ptr1;
        wr_side <= next_wr_side;
        rd_ptr0 <= next_rd_ptr0;
        rd_ptr1 <= next_rd_ptr1;
        full0 <= next_full0;
        full1 <= next_full1;
        state <= next_state;
    end
end

//delay process
always @(posedge clk)
begin
    we0 <= next_we0;
    we1 <= next_we1;
    wr_half <= fft_size[FFT_SIZE_WIDTH-1:1];
    wr_full <= fft_size - 1;
    wr_full_slice <= wr_full[ADDR_MSB:0];
    wr_full_m1 <= wr_full_slice - 1;
    wr_data <= next_wr_data;
    rd_tlast <= next_rd_tlast;
    rd_en <= next_rd_en;
    tvalid_fifo <= next_tvalid_fifo;
    tdata_fifo <= next_tdata_fifo;
    tlast_fifo <= next_tlast_fifo;
    rd_en <= next_rd_en;
    rd_en_d <= {rd_en_d[1:0],rd_en};
    rd_side_d <= {rd_side_d[1:0],rd_side};
    rd_tlast_d <= {rd_tlast_d[1:0],rd_tlast};

    rd_ptr0_d0 <= rd_ptr0;
    rd_ptr0_d1 <= rd_ptr0_d0;
    rd_ptr0_d2 <= rd_ptr0_d1;

    rd_ptr1_d0 <= rd_ptr1;
    rd_ptr1_d1 <= rd_ptr1_d0;
    rd_ptr1_d2 <= rd_ptr1_d1;
end

// full signal process
always @*
begin
    next_full0 = full0;
    next_full1 = full1;
    if (full0 == 1'b0) begin
        if (take_data == 1'b1 && wr_side == 1'b0 && (phase_s == wr_full_slice || s_axis_tlast == 1'b1)) begin
            next_full0 = 1'b1;
        end
    end else begin
        if (state == S_READ0 && almost_full == 1'b0 && rd_ptr0 == wr_full_m1) begin
            next_full0 = 1'b0;
        end
    end
    if (full1 == 1'b0) begin
        if (take_data == 1'b1 && wr_side == 1'b1 && (phase_s == wr_full_slice || s_axis_tlast == 1'b1)) begin
            next_full1 = 1'b1;
        end
    end else begin
        if (state == S_READ1 && almost_full == 1'b0 && rd_ptr1 == wr_full_m1) begin
            next_full1 = 1'b0;
        end
    end
end

// write process
always @*
begin
    next_we0 = 1'b0;
    next_we1 = 1'b0;
    next_wr_data = 0;
    next_wr_ptr0 = wr_ptr0;
    next_wr_ptr1 = wr_ptr1;
    next_wr_side = wr_side;
    if (s_axis_tvalid == 1'b1 && almost_full == 1'b0) begin
        next_wr_data = s_axis_tdata;
        if (wr_side == 1'b0) begin
            if (full0 == 1'b0) begin
                next_we0 = 1'b1;
                next_wr_ptr0 <= phase_s;
                if (phase_s == wr_full_slice) begin
                    next_wr_side = 1'b1;
                end
            end
        end else begin
            if (full1 == 1'b0) begin
                next_we1 = 1'b1;
                next_wr_ptr1 = (phase_s + wr_half) & wr_full_slice;
                if (phase_s == wr_full_slice) begin
                    next_wr_side = 1'b0;
                end
            end
        end
    end
end


// read state machine
always @*
begin
    next_rd_ptr0 = rd_ptr0;
    next_rd_ptr1 = rd_ptr1;
    next_rd_side = rd_side;
    next_state = state;
    next_rd_en = 1'b0;
    next_rd_tlast = 1'b0;
    case(state)
        S_IDLE :
        begin
            if (rd_side == 1'b1 && full0 == 1'b1 && almost_full == 1'b0) begin
                next_rd_side = 1'b0;
                next_rd_en = 1'b1;
                next_rd_ptr0 = 0;
                next_state = S_READ0;
            end else if (rd_side == 1'b0 && full1 == 1'b1 && almost_full == 1'b0) begin
                next_rd_side = 1'b1;
                next_rd_en = 1'b1;
                next_rd_ptr1 = 0;
                next_state = S_READ1;
            end
        end
        S_READ0 :
        begin
            if (almost_full == 1'b0) begin
                next_rd_en = 1'b1;
                next_rd_ptr0 = rd_ptr0 + 1;
                if (rd_ptr0 == (wr_full_m1)) begin
                    next_state = S_IDLE;
                    next_rd_tlast = 1'b1;
                end
            end
        end
        S_READ1 :
        begin
            if (almost_full == 1'b0) begin
                next_rd_en = 1'b1;
                next_rd_ptr1 = rd_ptr1 + 1;
                if (rd_ptr1 == wr_full_m1) begin
                    next_state = S_IDLE;
                    next_rd_tlast = 1'b1;
                end
            end
        end
        default :
        begin
        end
    endcase
end

//mux process
always @*
begin
    next_tvalid_fifo = 1'b0;
    next_tlast_fifo = 1'b0;
    next_tdata_fifo = 0;
    if (rd_en_d[2] == 1'b1) begin
        next_tvalid_fifo = 1'b1;
        next_tlast_fifo = rd_tlast_d[2];
        if (rd_side_d[2] == 1'b0) begin
            next_tdata_fifo = tdata0;
        end else begin
            next_tdata_fifo = tdata1;
        end
    end
end

dp_block_read_first_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH))
u_ram0(
    .clk(clk),
    .wea(we0),
    .addra(wr_addr0),
    .addrb(rd_addr0),
    .dia(wr_data),
    .dob(rd_data0)
);

dp_block_read_first_ram #(
    .DATA_WIDTH(DATA_WIDTH),
    .ADDR_WIDTH(ADDR_WIDTH))
u_ram1(
    .clk(clk),
    .wea(we1),
    .addra(wr_addr1),
    .addrb(rd_addr1),
    .dia(wr_data),
    .dob(rd_data1)
);

axi_fifo_19 #(
    .DATA_WIDTH(DATA_WIDTH + ADDR_WIDTH),
    .ALMOST_FULL_THRESH(8),
    .ADDR_WIDTH(4))
out_fifo(
    .clk(clk),
    .sync_reset(sync_reset),
    .s_axis_tvalid(tvalid_fifo),
    .s_axis_tdata(tdata_fifo),
    .s_axis_tlast(tlast_fifo),
    .s_axis_tready(),
    .almost_full(almost_full),
    .m_axis_tvalid(m_axis_tvalid),
    .m_axis_tdata(m_axis_tdata_s),
    .m_axis_tlast(m_axis_tlast),
    .m_axis_tready(m_axis_tready)
);


endmodule
