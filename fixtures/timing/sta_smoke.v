module sta_smoke(input wire clk, input wire d, output wire q);
  wire q1;
  DFF_X1 u1 (.D(d), .CK(clk), .Q(q1), .QN());
  DFF_X1 u2 (.D(q1), .CK(clk), .Q(q), .QN());
endmodule
