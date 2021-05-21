/*****************************************************************************/
//
// Author      : PJV
// File        : axi_fifo_51
// Description : Generates FIFO with AXI interface. 
//
//                Latency = 3.
//
/*****************************************************************************/

module axi_fifo_51
#( parameter DATA_WIDTH=32,
   parameter ALMOST_FULL_THRESH=16,
   parameter TUSER_WIDTH=8,
   parameter ADDR_WIDTH=8)
(
    input clk,
    input sync_reset,
    
    input s_axis_tvalid,
    input [DATA_WIDTH-1:0] s_axis_tdata,
    input s_axis_tlast,
    input [TUSER_WIDTH-1:0] s_axis_tuser,
    output s_axis_tready,
    output almost_full,

    output m_axis_tvalid,
    output [DATA_WIDTH-1:0] m_axis_tdata,
    output m_axis_tlast,
    output [TUSER_WIDTH-1:0] m_axis_tuser,
    input m_axis_tready
);

localparam ADDR_P1 = ADDR_WIDTH + 1;
localparam FIFO_WIDTH = DATA_WIDTH + TUSER_WIDTH + 1;
localparam FIFO_MSB = FIFO_WIDTH - 1;
localparam ADDR_MSB = ADDR_WIDTH - 1;
localparam DEPTH = 2 ** ADDR_WIDTH;
localparam [ADDR_WIDTH:0] high_thresh = ALMOST_FULL_THRESH;

reg [ADDR_WIDTH:0] data_cnt_s = {{ADDR_P1{{1'b0}}}};
reg [ADDR_P1:0] high_compare;
reg [ADDR_WIDTH:0] wr_ptr = 0, next_wr_ptr;
reg [ADDR_WIDTH:0] wr_addr = 0, next_wr_addr;
reg [ADDR_WIDTH:0] rd_ptr = 0, next_rd_ptr;

(* ram_style = "distributed" *) reg [FIFO_MSB:0] buffer [DEPTH-1:0];
wire [FIFO_MSB:0] wr_data;

// full when first MSB different but rest same
wire full;
// empty when pointers match exactly
wire empty;

// control signals
reg wr;
reg rd;
reg [1:0] occ_reg = 2'b00, next_occ_reg;
reg [FIFO_MSB:0] data_d0, data_d1, next_data_d0, next_data_d1;

// control signals
assign full = ((wr_ptr[ADDR_WIDTH] != rd_ptr[ADDR_WIDTH]) && (wr_ptr[ADDR_MSB:0] == rd_ptr[ADDR_MSB:0]));
assign s_axis_tready = ~full;
assign m_axis_tvalid = occ_reg[1];
assign empty = (wr_ptr == rd_ptr) ? 1'b1 : 1'b0;

assign wr_data = {s_axis_tlast, s_axis_tuser, s_axis_tdata};
assign m_axis_tdata = data_d1[DATA_WIDTH-1:0];
assign m_axis_tuser = data_d1[FIFO_MSB-1:DATA_WIDTH];
assign m_axis_tlast = data_d1[FIFO_MSB];
assign almost_full = high_compare[ADDR_WIDTH];

integer i;
initial begin
    for (i = 0; i < DEPTH; i=i+1) begin
        buffer[i] = 0;
    end
end

// Write logic
always @* begin
    wr = 1'b0;
    next_wr_ptr = wr_ptr;
    next_wr_addr = wr_addr;

    if (s_axis_tvalid) begin
        // input data valid
        if (~full) begin
            // not full, perform write
            wr = 1'b1;
            next_wr_ptr = wr_ptr + 1;
            next_wr_addr = wr_addr + 1;
        end
    end
end

// Data Cnt Logic
always @(posedge clk) begin
    data_cnt_s <= next_wr_ptr - next_rd_ptr + occ_reg[0];
    high_compare <= high_thresh - data_cnt_s;
end

always @(posedge clk) begin
    if (sync_reset) begin
        wr_ptr <= 0;
        wr_addr <= 0;
        occ_reg <= 0;
        data_d0 <= 0;
        data_d1 <= 0;
    end else begin
        wr_ptr <= next_wr_ptr;
        wr_addr <= next_wr_addr;
        occ_reg <= next_occ_reg;
        data_d0 <= next_data_d0;
        data_d1 <= next_data_d1;
    end

    if (wr) begin
        buffer[wr_addr[ADDR_MSB:0]] <= wr_data;
    end
end

// Read logic
always @* begin
    rd = 1'b0;
    next_rd_ptr = rd_ptr;
    next_occ_reg[0] = occ_reg[0];
    next_occ_reg[1] = occ_reg[1];
    next_data_d0 = data_d0;
    next_data_d1 = data_d1;
    if (occ_reg != 2'b11 | m_axis_tready == 1'b1) begin
        // output data not valid OR currently being transferred
        if (~empty) begin
            // not empty, perform read
            rd = 1'b1;
            next_rd_ptr = rd_ptr + 1;
        end
    end

    if (rd) begin
        next_occ_reg[0] = 1'b1;
    end else if (m_axis_tready == 1'b1 || occ_reg[1] == 1'b0) begin
        next_occ_reg[0] = 1'b0;
    end
    if (m_axis_tready == 1'b1 || occ_reg[1] == 1'b0) begin
        next_occ_reg[1] = occ_reg[0];
    end

    if (rd) begin
        next_data_d0 = buffer[rd_ptr[ADDR_MSB:0]];
    end
    if (m_axis_tready | ~occ_reg[1]) begin
        next_data_d1 = data_d0;
    end
end

always @(posedge clk) begin
    if (sync_reset) begin
        rd_ptr <= 0;
    end else begin
        rd_ptr <= next_rd_ptr;
    end

end


endmodule
