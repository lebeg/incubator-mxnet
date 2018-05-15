#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

"""
Build environment and run virtualized tests
"""

import argparse
import glob
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from itertools import chain
from subprocess import call, check_call
from typing import *

sys.path.append(os.path.dirname(__file__))
from build import get_platforms, default_ccache_dir, load_docker_cache, get_docker_binary, _get_local_image_id, buildir

def get_platforms(path: Optional[str] = "docker"):
    """Get a list of architectures given our dockerfiles"""
    dockerfiles = glob.glob(os.path.join(path, "Dockerfile.build.test.*"))
    dockerfiles = list(filter(lambda x: x[-1] != '~', dockerfiles))
    files = list(map(lambda x: re.sub(r"Dockerfile.build.test.(.*)", r"\1", x), dockerfiles))
    platforms = list(map(lambda x: os.path.split(x)[1], sorted(files)))
    return platforms

def get_docker_tag(platform: str, registry: str) -> str:
    return "{0}/build.test.{1}".format(registry, platform)

def get_dockerfile(platform: str, path="docker") -> str:
    return os.path.join(path, "Dockerfile.build.test.{0}".format(platform))

def build_docker(platform: str, docker_binary: str, registry: str) -> None:
    """
    Build a container for the given platform
    :param platform: Platform
    :param docker_binary: docker binary to use (docker/nvidia-docker)
    :param registry: Dockerhub registry name
    :return: Id of the top level image
    """

    tag = get_docker_tag(platform=platform, registry=registry)
    logging.info("Building container tagged '%s' with %s", tag, docker_binary)
    cmd = [docker_binary, "build",
           "-f", get_dockerfile(platform),
           "--build-arg", "USER_ID={}".format(os.getuid()),
           "--cache-from", tag,
           "-t", tag,
           "docker"]
    logging.info("Running command: '%s'", ' '.join(cmd))
    check_call(cmd)

    # Get image id by reading the tag. It's guaranteed (except race condition) that the tag exists. Otherwise, the
    # check_call would have failed
    image_id = _get_local_image_id(docker_binary=docker_binary, docker_tag=tag)
    if not image_id:
        raise FileNotFoundError('Unable to find docker image id matching with {}'.format(tag))
    return image_id


def container_run(platform: str,
                  docker_binary: str,
                  docker_registry: str,
                  shared_memory_size: str,
                  command: List[str],
                  dry_run: bool = False,
                  into_container: bool = False) -> str:
    tag = get_docker_tag(platform=platform, registry=docker_registry)
    runlist = [docker_binary, 'run', '--rm', '-t',
               '--shm-size={}'.format(shared_memory_size),
               '-u', '{}:{}'.format(os.getuid(), os.getgid()),
               tag]
    runlist.extend(command)
    cmd = ' '.join(runlist)
    if not dry_run and not into_container:
        logging.info("Running %s in container %s", command, tag)
        logging.info("Executing: %s", cmd)
        ret = call(runlist)

    into_cmd = deepcopy(runlist)
    idx = into_cmd.index('-u') + 2
    into_cmd[idx:idx] = ['-ti', '--entrypoint', '/bin/bash']
    docker_run_cmd = ' '.join(into_cmd)
    if not dry_run and into_container:
        check_call(into_cmd)

    if not dry_run and ret != 0:
        logging.error("Running of command in container failed (%s): %s", ret, cmd)
        logging.error("You can try to get into the container by using the following command: %s", docker_run_cmd)

        raise subprocess.CalledProcessError(ret, cmd)

    return docker_run_cmd


def list_platforms() -> str:
    print("\nSupported platforms:\n{}".format('\n'.join(get_platforms())))


def main() -> int:
    # We need to be in the same directory than the script so the commands in the dockerfiles work as
    # expected. But the script can be invoked from a different path
    base = os.path.split(os.path.realpath(__file__))[0]
    os.chdir(base)

    logging.getLogger().setLevel(logging.INFO)

    def script_name() -> str:
        return os.path.split(sys.argv[0])[1]

    logging.basicConfig(format='{}: %(asctime)-15s %(message)s'.format(script_name()))

    parser = argparse.ArgumentParser(description="""Utility for building and testing MXNet on docker
    containers""", epilog="")
    parser.add_argument("-p", "--platform",
                        help="Build and test for a specific platform",
                        type=str)

    parser.add_argument("--build-only",
                        help="Only build the container, don't build the project",
                        action='store_true')

    parser.add_argument("-a", "--all",
                        help="Build and test for all platforms",
                        action='store_true')

    parser.add_argument("-n", "--nvidiadocker",
                        help="Use nvidia docker",
                        action='store_true')

    parser.add_argument("--shm-size",
                        help="Size of the shared memory /dev/shm allocated in the container (e.g '1g')",
                        default='2g',
                        dest="shared_memory_size")

    parser.add_argument("-l", "--list",
                        help="List platforms",
                        action='store_true')

    parser.add_argument("--print-docker-run",
                        help="Print docker run command for manual inspection",
                        action='store_true')

    parser.add_argument("-i", "--into-container",
                        help="Go in a shell inside the container",
                        action='store_true')

    parser.add_argument("-d", "--docker-registry",
                        help="Dockerhub registry name to retrieve cache from. Default is 'mxnetci'",
                        default='mxnetci',
                        type=str)

    parser.add_argument("-c", "--cache", action="store_true",
                        help="Enable docker registry cache")

    parser.add_argument("command",
                        help="Command to run in the container",
                        nargs='*', action='append', type=str)

    args = parser.parse_args()
    def use_cache():
        return args.cache or 'JOB_NAME' in os.environ # we are in Jenkins

    command = list(chain(*args.command))
    docker_binary = get_docker_binary(args.nvidiadocker)
    shared_memory_size = args.shared_memory_size

    if args.list:
        list_platforms()
    elif args.platform:
        platform = args.platform
        tag = get_docker_tag(platform=platform, registry=args.docker_registry)
        if use_cache():
            load_docker_cache(tag=tag, docker_registry=args.docker_registry)
        build_docker(platform, docker_binary, registry=args.docker_registry)
        if args.build_only:
            logging.warning("Container was just built. Exiting due to build-only.")
            return 0

        if command:
            container_run(platform=platform, docker_binary=docker_binary, shared_memory_size=shared_memory_size,
                          command=command, docker_registry=args.docker_registry)
        elif args.print_docker_run:
            print(container_run(platform=platform, docker_binary=docker_binary, shared_memory_size=shared_memory_size,
                                command=[], dry_run=True, docker_registry=args.docker_registry))
        elif args.into_container:
            container_run(platform=platform, docker_binary=docker_binary, shared_memory_size=shared_memory_size,
                          command=[], dry_run=False, into_container=True, docker_registry=args.docker_registry)
        else:
            cmd = ["/work/runtime_test_functions.sh", "test_{}".format(platform)]
            logging.info("No command specified, trying default test: %s", ' '.join(cmd))
            container_run(platform=platform, docker_binary=docker_binary, shared_memory_size=shared_memory_size,
                          command=cmd, docker_registry=args.docker_registry)

    elif args.all:
        platforms = get_platforms()
        logging.info("Building for all architectures: {}".format(platforms))
        logging.info("Artifacts will be produced in the build/ directory.")
        for platform in platforms:
            tag = get_docker_tag(platform=platform, registry=args.docker_registry)
            if use_cache():
                load_docker_cache(tag=tag, docker_registry=args.docker_registry)
            build_docker(platform, docker_binary, args.docker_registry)
            if args.build_only:
                continue
            test_platform = "test_{}".format(platform)
            cmd = ["/work/runtime_test_functions.sh", test_platform]
            shutil.rmtree(buildir(), ignore_errors=True)
            container_run(platform=platform, docker_binary=docker_binary, shared_memory_size=shared_memory_size,
                          command=cmd, docker_registry=args.docker_registry)
            plat_buildir = os.path.join(get_mxnet_root(), build_platform)
            shutil.move(buildir(), plat_buildir)
            logging.info("Built files left in: %s", plat_buildir)

    else:
        parser.print_help()
        list_platforms()
        print("""
Examples:

./test.py -p rpi

    Will build a docker container with test tools setup and qemu emulated tests suite for MXNet for Raspberry Pi by
    running: ci/docker/runtime_test_functions.sh test_rpi inside the container.

./test.py -p rpi ls

    Will execute the given command inside the rpi container.

./test.py -p rpi --print-docker-run

    Will print a docker run command to get inside the container in an interactive shell.

./test.py -p rpi --into-container

    Will execute a shell into the container.

./test.py -a

    Runs the tests for all platforms.

    """)

    return 0


if __name__ == '__main__':
    sys.exit(main())
