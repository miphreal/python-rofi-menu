ARG ROFI_VERSION=1.6.1

FROM ubuntu:20.04 as builder

ARG DEBIAN_FRONTEND=noninteractive

RUN mkdir /tmp/rofi
WORKDIR /tmp/rofi

RUN apt update && apt install -y rofi-dev qalc libtool  \
  git \
  pkg-config \
  gcc make \
  autoconf \
  bison \
  flex \
  check \
  libglib2.0-0 \
  libtool \
  libpango1.0-dev \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libstartup-notification0 \
  libstartup-notification0-dev \
  librsvg2-bin \
  libxcb-composite0 \
  libxcb-randr0-dev \
  libxcb-util-dev \
  libxcb-xinerama0-dev \
  libxinerama-dev \
  libxkbcommon-dev \
  libxkbcommon-x11-dev \
  libxft-dev wget

## some packages taken from : https://github.com/davatorium/rofi/blob/next/.travis.yml
RUN apt install -y discount  doxygen  fluxbox  gdb  graphviz  jq  lcov  libpango1.0-dev  libstartup-notification0-dev  libxcb-ewmh-dev  libxcb-icccm4-dev  libxcb-randr0-dev  libxcb-util0-dev  libxcb-xinerama0-dev  libxcb-xkb-dev  libxcb-xrm-dev  libxkbcommon-dev  libxkbcommon-dev  libxkbcommon-x11-dev  ninja-build  python3-pip  python3-setuptools  python3-wheel  texi2html  texinfo  xdotool  xfonts-base  xterm  xutils-dev \
  libgdk-pixbuf2.0-dev


FROM builder as rofi-builder

ARG ROFI_VERSION

RUN wget https://github.com/davatorium/rofi/releases/download/${ROFI_VERSION}/rofi-${ROFI_VERSION}.tar.gz && \
  tar xzvf rofi-${ROFI_VERSION}.tar.gz && \
  cd rofi-${ROFI_VERSION} && \
  autoreconf -i && \
  mkdir build && cd build/ && ../configure --disable-check && \
  make

RUN rofi -version


FROM builder as rofi-menu-tester

ARG ROFI_VERSION

RUN apt-get update && apt-get install -y xvfb tesseract-ocr

COPY --from=rofi-builder /tmp/rofi/rofi-${ROFI_VERSION}/build/rofi /usr/bin/

RUN pip install pyvirtualdisplay==3.0 pillow==9.1 pytesseract==0.3.9 pytest==7.1
