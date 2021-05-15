/*****************************************************************************/
//
// Author      : Phil Vallance
// File        : grc_complex_writer.sv
// Description : Simulation utility used to record data to a binary file.
//
//
//
// Rev      Date         Comments
// --   -----------  ------------------------------------------------------
// Module reads a binary file (single line) of small-endian dataread
//
/*****************************************************************************/
// This module collects data and writes the data to a file.
// The module will collect data either as a LISTEN_ONLY device looking for a valid data transaction,
// or as a termination device performing wishbone signaling to the data source.
//
// The data will be accumulated in the array defined by ARRAY_LENGTH.  The data width is define by 16 bits.
// Once the data is full, the buffer will be written to the file defined by FileName_i.  This can be a simple
// directory or a full pathname.  Once the buffer is written, the buffer will cleared and the data will continue
// to be accumulated.  A wr_file = '1' will force the module to write the buffer contents at the next valid data sample.
//
// On the first buffer write to the file, information about the data and its source is written to the start of
// the file followed by the data.  Successive writes will append the original file with more data.  A reset will
// cause the module to create a new file.  During a typical simulation, the module will create a file and continue
// writing data to the file throughout the simulation.  The file size is only limited by the host file system.
// Using a small buffer size will slow simulation due to frequent writes to the filesystem.
// MINIMUM BUFFER SIZE = 3
// Using a large buffer size (100M) may cause problems with availability of system memory. If simulation is stopped
// before the buffer is filled, a file will not be created unless wr_file is activated.
//
//
//
`timescale 1ns/100ps
`define SEEK_SET 0
`define SEEK_CUR 1
`define SEEK_END 2


module grc_word_writer #(
	parameter LISTEN_ONLY = 0,
	parameter ARRAY_LENGTH = 1024,
	parameter NUM_BYTES = 2,
	parameter MAX_WRITES = 1000000)
(
	input clk,
	input sync_reset,
	input enable,

	input wire integer fd,

	input valid,
	input [NUM_BYTES * 8 - 1:0] word,

	input wr_file,
	output [63:0] word_cnt,

	input rdy_i,
	output rdy_o
);

function integer clog2;
 //
 // ceiling( log2( x ) )
 //
 input integer x;
 begin
   if (x<=0) clog2 = -1;
   else clog2 = 0;
   x = x - 1;
   while (x>0) begin
     clog2 = clog2 + 1;
     x = x >> 1;
   end
 end
endfunction

localparam INDEX_BITS = clog2(ARRAY_LENGTH-1);
localparam WORD_MSB = NUM_BYTES * 8 - 1;

reg fifo_full_s;
reg fifo_full_d1, fifo_full_d2;
wire rdy_s;

integer index, next_index;
integer index_copy, next_index_copy;
integer index_wr, next_index_wr;

reg [WORD_MSB:0] word_array [ARRAY_LENGTH-1:0];
reg [WORD_MSB:0] word_array_copy [ARRAY_LENGTH-1:0];
reg [WORD_MSB:0] next_word_array_copy [ARRAY_LENGTH-1:0];
reg [WORD_MSB:0] next_value;

reg [63:0] word_cnt_s, next_word_cnt;

wire take_data;

assign take_data = (LISTEN_ONLY == 0) ? (valid & rdy_i) : valid;
assign rdy_s = (LISTEN_ONLY == 0) ? rdy_i : 1'b1;
assign rdy_o = rdy_s;
assign word_cnt = word_cnt_s;

//integer numRead;
integer temp;
integer position = 0;
// integer file_len;

task tsk_reset;
	#5
	// $display("writer fd = %d",fd);
	// temp = $fseek(fd, position, `SEEK_END);
	// file_len = $ftell(fd);
	// $display("Reader : file length = %d",file_len);
	temp = $fseek(fd, position, `SEEK_SET);
endtask

initial
begin
    tsk_reset();
end

integer ii;
always @(posedge clk) begin:clk_process
	if (sync_reset) begin
		for (ii = 0; ii < ARRAY_LENGTH; ii = ii + 1) begin
			word_array[ii] <= 0;
			word_array_copy[ii] <= 0;
			next_word_array_copy[ii] <= 0;
		end
		index <= 0;
		index_copy <= 0;
		index_wr <= 0;
		fifo_full_d1 <= 1'b0;
		fifo_full_d2 <= 1'b0;
		word_cnt_s <= 0;
	end else if (enable == 1'b1) begin
		index <= next_index;
		index_copy <= next_index_copy;
		index_wr <= next_index_wr;
		word_array[index] <= next_value;
		for (ii = 0; ii < ARRAY_LENGTH; ii = ii + 1) begin
			word_array_copy[ii] <= next_word_array_copy[ii];
		end
		fifo_full_d1 <= fifo_full_s;
		fifo_full_d2 <= fifo_full_d1;
		word_cnt_s <= next_word_cnt;
	end
end

integer num_written = 0;

always @*
begin:array_fil
	next_value = word[index];
	next_index = index;
	next_index_copy = index_copy;
	next_index_wr = index_wr;
	next_word_cnt = word_cnt;
	fifo_full_s = 1'b0;
	next_value = word;
	if (take_data == 1'b1) begin
		next_word_cnt = word_cnt + 1;
		if (wr_file == 1'b1 || index == ARRAY_LENGTH-1) begin
			fifo_full_s = 1'b1;
			next_index = 0;
			next_index_copy = index;
		end else begin
			next_index = index + 1;
		end
	end
	if (fifo_full_d1 == 1'b1) begin
		for (ii = 0; ii < ARRAY_LENGTH; ii = ii + 1) begin
			next_word_array_copy[ii] = word_array[ii];
		end
		next_index_wr = index_copy;
	end
end

always @*
begin:file_write
	integer ii;
	integer jj;
	integer result;
	integer lidx, ridx;

	if (sync_reset == 1'b1) begin
		tsk_reset();
	end else if (fifo_full_d2 == 1'b1) begin
		for (ii = 0; ii < (index_wr + 1); ii = ii + 1) begin
			for (jj = 0; jj < NUM_BYTES; jj = jj + 1) begin
				lidx = (NUM_BYTES - jj) * 8 - 1;
				$fwrite(fd, "%c", word_array_copy[ii][lidx-:8]);
			end
			// $display("writing : %d, %d", word_array_copy[ii], ii);
		end
		result = $ftell(fd);
		$display("File has %0d bytes", result);
		$display("File Descripter %0d", fd);
		$fflush(fd);
		$display("Number of words written = %d", index_wr + 1);
	end
end


endmodule
