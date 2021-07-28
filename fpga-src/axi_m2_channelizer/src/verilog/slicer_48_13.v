
//     Licensed to the Apache Software Foundation (ASF) under one
// or more contributor license agreements.  See the NOTICE file
// distributed with this work for additional information
// regarding copyright ownership.  The ASF licenses this file
// to you under the Apache License, Version 2.0 (the
// "License"); you may not use this file except in compliance
// with the License.  You may obtain a copy of the License at
// 
//   http://www.apache.org/licenses/LICENSE-2.0
// 
// Unless required by applicable law or agreed to in writing,
// software distributed under the License is distributed on an
// "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, either express or implied.  See the License for the
// specific language governing permissions and limitations
// under the License.  


/*****************************************************************************/
//
// Author      : Python Generated
// File        : ./tmp/slicer_48_13.v
// Description : Generates a variable slicer module.
//
//
/*****************************************************************************/


module slicer_48_13(
  input sync_reset,
  input clk,

// Settings offet the slicer from the base value.
  input [0:0] slice_offset_i,

  input valid_i,  // Data Valid Signal.
  input [47:0] signal_i, // Energy dectect signal.

  output valid_o,
  output [12:0] signal_o
);


reg valid_d;

reg [12:0] output_reg, next_output_reg;

assign signal_o = output_reg;
assign valid_o = valid_d;

always @(posedge clk)
begin
    if (sync_reset) begin
        output_reg <= 0;
        valid_d <= 0;
    end else begin
        output_reg <= next_output_reg;
        valid_d <= valid_i;
    end
end


always @*
begin
    case (slice_offset_i)
        1'b0 : next_output_reg = signal_i[12:0];
        1'b1 : next_output_reg = signal_i[12:0];

    endcase

end

endmodule
