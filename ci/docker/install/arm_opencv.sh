#!/usr/bin/env bash

# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# build and install are separated so changes to build don't invalidate
# the whole docker cache for the image

#sudo apt-get -y --force-yes install \
#     build-essential \
#     checkinstall \
#     cmake \
#     pkg-config \
#     yasm \
#     git \
#     gfortran \
#     libjpeg62-turbo-dev \
#     libjasper-dev \
#     libpng12-dev \
#     libtiff5-dev \
#     libtiff-dev \
#     libavcodec-dev \
#     libavformat-dev \
#     libswscale-dev \
#     libdc1394-22-dev \
#     libxine2-dev \
#     libv4l-dev \
#     libgstreamer0.10-dev \
#     libgstreamer-plugins-base0.10-dev \
#     libgtk2.0-dev \
#     libtbb-dev \
#     qt5-default \
#     libatlas-base-dev \
#     libmp3lame-dev \
#     libtheora-dev \
#     libvorbis-dev \
#     libxvidcore-dev \
#     libx264-dev \
#     libopencore-amrnb-dev \
#     libopencore-amrwb-dev \
#     libavresample-dev \
#     x264 \
#     v4l-utils \
#     libprotobuf-dev \
#     protobuf-compiler \
#     libgoogle-glog-dev \
#     libgflags-dev \
#     libgphoto2-dev \
#     libeigen3-dev \
#     libhdf5-dev \
#     doxygen

#cd /usr/include/linux
#sudo ln -s -f ../libv4l1-videodev.h videodev.h
#cd $cwd

git clone https://github.com/opencv/opencv_contrib.git
cd opencv_contrib
git checkout 3.2.0
cd ..

git clone https://github.com/opencv/opencv.git
cd opencv
git checkout 3.2.0
mkdir -p build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE \
      -D CMAKE_TOOLCHAIN_FILE=${CROSS_ROOT}/Toolchain.cmake \
      -D CMAKE_CROSSCOMPILING=ON \
      -D CMAKE_INSTALL_PREFIX=${CROSS_ROOT}/${CROSS_TRIPLE} \
      -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
      -D BUILD_opencv_legacy=OFF \
      -D INSTALL_C_EXAMPLES=OFF \
      -D INSTALL_PYTHON_EXAMPLES=OFF \
      -D WITH_TBB=OFF \
      -D WITH_V4L=OFF \
      -D WITH_QT=OFF \
      -D WITH_OPENGL=ON \
      -D BUILD_EXAMPLES=OFF ..

#-D OPENCV_PYTHON3_INSTALL_PATH=$cwd/OpenCV-$cvVersion-py3/lib/python3.5/site-packages \

make -j$(nproc)
make install --ignore-errors

cd ../..
