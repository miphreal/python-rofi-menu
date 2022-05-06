#
# Base image for building and running rofi
#
FROM ubuntu:20.04 as builder

ARG DEBIAN_FRONTEND=noninteractive

RUN apt update && apt install -y \
  autoconf \
  bison \
  check \
  discount \
  doxygen \
  flex \
  gcc \
  gdb \
  git \
  graphviz \
  jq \
  lcov \
  libgdk-pixbuf2.0-dev \
  libglib2.0-0 \
  libpango-1.0-0 \
  libpango1.0-dev \
  libpangocairo-1.0-0 \
  librsvg2-bin \
  libstartup-notification0 \
  libstartup-notification0-dev \
  libtool \
  libxcb-composite0 \
  libxcb-ewmh-dev \
  libxcb-icccm4-dev \
  libxcb-randr0-dev \
  libxcb-util0-dev \
  libxcb-util-dev \
  libxcb-xinerama0-dev \
  libxcb-xkb-dev \
  libxcb-xrm-dev \
  libxft-dev \
  libxinerama-dev \
  libxkbcommon-dev \
  libxkbcommon-x11-dev \
  make \
  ninja-build \
  pkg-config \
  python3-pip \
  python3-setuptools \
  python3-wheel \
  rofi-dev \
  texi2html \
  texinfo \
  wget \
  xdotool \
  xfonts-base \
  xterm \
  xutils-dev


#
# Rofi builder image (builds all supported rofi versions)
#
FROM builder as rofi-builder

ARG WORKDIR="/tmp/rofi"
RUN mkdir ${WORKDIR}
COPY ./scripts/install-rofi.sh ${WORKDIR}
COPY ./supported-rofi-versions.txt ${WORKDIR}
RUN bash -c "for version in $(cat ${WORKDIR}/supported-rofi-versions.txt); do /tmp/install-rofi.sh $version ${WORKDIR}/rofi-$version; done"


#
# `rofi-menu` dev and testing environment (both unit and e2e tests)
#
FROM builder as dev

# tesing dependencies
RUN apt-get update && apt-get install -y xvfb tesseract-ocr

ARG WORKDIR="/tmp/rofi"
WORKDIR ${WORKDIR}

COPY --from=rofi-builder ${WORKDIR} ${WORKDIR}

# TODO: install pyenv and all supported python versions
# TODO: move to pyproject.toml and install via poetry
RUN pip install pyvirtualdisplay==3.0 pillow==9.1 pytesseract==0.3.9 pytest==7.1

# TODO: Implement matrix testing [py37,38,39,...] vs [rofi15,16,17]
