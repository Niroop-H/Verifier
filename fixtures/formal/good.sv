module formal_good(input wire a, input wire b);
  wire y = a & b;
  always @* assert(y == (a & b));
endmodule
