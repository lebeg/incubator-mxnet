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

if(NOT USE_CUDA)
  add_definitions(-DMSHADOW_USE_CUDA=0)
  add_definitions(-DMXNET_USE_CUDA=0)
  add_definitions(-DMXNET_USE_NCCL=0)
  add_definitions(-DMSHADOW_USE_CUDNN=0)

  return()
endif()

cmake_minimum_required(VERSION 3.10.0 FATAL_ERROR)

project(mxnet C CXX CUDA)

add_definitions(-DMSHADOW_USE_CUDA=1)
add_definitions(-DMXNET_USE_CUDA=1)

if(USE_NCCL)
  find_package(NCCL)
  if(NCCL_FOUND)
    add_definitions(-DMXNET_USE_NCCL=1)
    include_directories(${NCCL_INCLUDE_DIRS})
    list(APPEND mxnet_LINKER_LIBS ${NCCL_LIBRARIES})
  else()
    add_definitions(-DMXNET_USE_NCCL=0)
    message(WARNING "Could not find NCCL libraries")
  endif()
endif()

# cudnn detection
if(USE_CUDNN)
  detect_cudnn()
  if(HAVE_CUDNN)
    add_definitions(-DUSE_CUDNN)
    include_directories(SYSTEM ${CUDNN_INCLUDE})
    list(APPEND mxnet_LINKER_LIBS ${CUDNN_LIBRARY})
    add_definitions(-DMSHADOW_USE_CUDNN=1)
  endif()
endif()
