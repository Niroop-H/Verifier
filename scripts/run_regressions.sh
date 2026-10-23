#!/usr/bin/env bash
set -euo pipefail
mkdir -p artifacts fixtures/rtl
status=0
log() { echo "[$(date -u +%FT%TZ)] $*" | tee -a artifacts/regression.log; }
run() { local name="$1"; shift; if "$@" >"artifacts/$name.log" 2>&1; then log "$name PASS"; else local rc=$?; log "$name FAIL (exit=$rc)"; status=1; fi; }
need() { command -v "$1" >/dev/null 2>&1; }
cat > fixtures/rtl/good.v <<'EOF'
module good(input wire a, input wire b, output wire y);
  assign y = a & b;
endmodule
EOF
cat > fixtures/rtl/bad.v <<'EOF'
module bad(input wire a, output wire y);
  assign y = missing_signal & a;
endmodule
EOF
if need iverilog && need vvp; then
  run iverilog_good iverilog -g2012 -s good -o artifacts/good.vvp fixtures/rtl/good.v
  run iverilog_bad_should_compile_fail bash -c 'iverilog -g2012 -s bad -o artifacts/bad.vvp fixtures/rtl/bad.v && exit 1 || test $? -ne 1'
else log "iverilog BLOCKED: iverilog/vvp not on PATH"; fi
if need verilator; then
  run verilator_good verilator --lint-only --Wall -Wno-fatal fixtures/rtl/good.v
  # Undefined signal should produce a fatal lint diagnostic.
  run verilator_bad_should_fail bash -c 'verilator --lint-only -Wno-fatal fixtures/rtl/bad.v >/dev/null 2>&1; test $? -ne 0'
else log "verilator BLOCKED: verilator not on PATH"; fi
if need yosys; then
  run yosys_good yosys -p 'read_verilog fixtures/rtl/good.v; hierarchy -check -top good; proc; check; stat'
  run yosys_bad_should_fail bash -c 'yosys -p "read_verilog fixtures/rtl/bad.v; hierarchy -check -top bad; proc; check" >/dev/null 2>&1; test $? -ne 0'
else log "yosys BLOCKED: yosys not on PATH"; fi
if need ghdl; then
  cat > fixtures/rtl/good.vhd <<'EOF'
library ieee;
use ieee.std_logic_1164.all;
entity good_vhdl is port(a,b: in std_logic; y: out std_logic); end entity;
architecture rtl of good_vhdl is begin y <= a and b; end architecture;
EOF
  run ghdl_good ghdl -a --std=08 --workdir=artifacts fixtures/rtl/good.vhd
else log "ghdl BLOCKED: ghdl not on PATH"; fi
if need z3; then run z3_smoke z3 --version; else log "z3 BLOCKED: z3 not on PATH"; fi
if need boolector; then run boolector_smoke boolector --version; else log "boolector BLOCKED: boolector not on PATH"; fi
if need klayout; then run klayout_smoke klayout -v; else log "klayout BLOCKED: klayout not on PATH"; fi
if need sta; then run opensta_smoke sta -version; else log "opensta BLOCKED: sta not on PATH"; fi
python3 scripts/check_environment.py > artifacts/tool-environment.json
exit "$status"
