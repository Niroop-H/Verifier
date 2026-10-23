library ieee;
use ieee.std_logic_1164.all;

entity logic is
    port (a : in std_logic; b : in std_logic; y : out std_logic);
end entity;

architecture rtl of logic is
begin
    y <= a xor b;
end architecture;
