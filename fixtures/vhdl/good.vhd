library ieee;
use ieee.std_logic_1164.all;
entity mqv_vhdl_good is
  port (a : in std_logic; b : in std_logic; y : out std_logic);
end entity;
architecture rtl of mqv_vhdl_good is
begin
  y <= a and b;
end architecture;
