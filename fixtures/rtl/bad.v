default_nettype none
module bad(input wire a, output wire y);
  assign y = missing_signal & a;
endmodule
default_nettype wire
