module formal_bad(input wire a, input wire b);
  always @* assert(a == b);
endmodule
