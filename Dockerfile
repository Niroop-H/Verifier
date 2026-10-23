FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential cmake git curl ca-certificates python3 python3-pip \
    iverilog verilator yosys ghdl z3 boolector ruby tcl-dev swig bison flex \
    automake autotools-dev libeigen3-dev libfmt-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*
RUN curl --fail --location --retry 3 \
    https://www.klayout.org/downloads/Ubuntu-24/klayout_0.30.10-1_amd64.deb \
    --output /tmp/klayout.deb \
    && echo "674a26b464841ac7385dec3cc47c2c60  /tmp/klayout.deb" | md5sum --check - \
    && apt-get update && apt-get install -y /tmp/klayout.deb \
    && rm -f /tmp/klayout.deb && rm -rf /var/lib/apt/lists/*
RUN git clone https://github.com/cuddorg/cudd.git /tmp/cudd \
    && git -C /tmp/cudd checkout 3.0.0 \
    && cd /tmp/cudd && ./configure --prefix=/usr/local \
    && make -o aclocal.m4 -o Makefile.in -o configure -j2 \
    && make -o aclocal.m4 -o Makefile.in -o configure install \
    && rm -rf /tmp/cudd
RUN git clone https://github.com/parallaxsw/OpenSTA.git /tmp/OpenSTA \
    && git -C /tmp/OpenSTA checkout bdc4e054cb917e1b7058444829191838b302cccd \
    && cmake -S /tmp/OpenSTA -B /tmp/OpenSTA/build -DCMAKE_BUILD_TYPE=Release -DCUDD_DIR=/usr/local \
    && cmake --build /tmp/OpenSTA/build --parallel 2 \
    && install -m 0755 /tmp/OpenSTA/build/sta /usr/local/bin/sta \
    && rm -rf /tmp/OpenSTA
RUN git clone https://github.com/YosysHQ/sby.git /tmp/sby \
    && git -C /tmp/sby checkout 79fc9eddca5e33a28cc2f2cd19c9825efd9a7255 \
    && make -C /tmp/sby install PREFIX=/usr/local \
    && rm -rf /tmp/sby
WORKDIR /opt/mah-quantum-verify
COPY . .
RUN python3 -m pip install --no-cache-dir -r requirements-dev.txt
CMD ["bash", "scripts/run_regressions.sh"]
