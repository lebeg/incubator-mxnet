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

set -ex

# Multipackage installation does not fail in yum
yum -y install epel-release
yum -y install git
yum -y install wget
yum -y install atlas-devel # Provide clbas headerfiles
yum -y install openblas-devel
yum -y install lapack-devel
yum -y install opencv-devel
yum -y install openssl-devel
yum -y install gcc-c++-4.8.*
yum -y install make
yum -y install cmake3
yum -y install wget
yum -y install unzip
yum -y install ninja-build
yum -y install zeromq-devel
yum -y install protobuf-devel
yum -y install ninja-build

alternatives --install /usr/local/bin/cmake cmake /usr/bin/cmake3 20 \
    --slave /usr/local/bin/ctest ctest /usr/bin/ctest3 \
    --slave /usr/local/bin/cpack cpack /usr/bin/cpack3 \
    --slave /usr/local/bin/ccmake ccmake /usr/bin/ccmake3 \
    --family cmake

alternatives --install /usr/local/bin/ninja ninja /usr/bin/ninja-build 20
