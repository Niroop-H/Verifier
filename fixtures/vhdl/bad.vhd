library ieee;
use ieee.std_logic_1164.all;
entity mqv_vhdl_bad is
  port (a : in std_logic; y : out std_logic);
end entity;
architecture rtl of mqv_vhdl_bad is
begin
  y <= a and ;
end architecture;
