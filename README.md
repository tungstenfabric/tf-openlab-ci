# tf-openlab-ci
Jenkins configuration for Tungsten Fabric OpenLab test automation


# Jenkins Plugin Dependency

**Job DSL**, https://wiki.jenkins.io/display/JENKINS/Job+DSL+Plugin

**Workspace Cleanup**, http://wiki.jenkins-ci.org/display/JENKINS/Workspace+Cleanup+Plugin

**Performance Publisher plugin**, https://wiki.jenkins.io/display/JENKINS/PerfPublisher+Plugin


# Directory structure
├── build    - Scripts to build and install the vRouter on the VMs used in perf testing
├── dsl      - Jenkins job triggers
├── pipeline - Jenkins job pipeline specification
├── test     - Tests to be run
├── images   - Any images required in order to setup test environment
├── LICENSE
└── README.md


# Workflow
1. Monitor git repo changes/timer trigger
2. Update repo to latest revision
3. Build whole Tungsten Fabric by [contrail-dev-env](https://github.com/Juniper/contrail-dev-env)
4. Copy the contrail-vrouter-dpdk binary to prepared testbeds, see [Peformance Test Suite](https://wiki.tungsten.io/display/TUN/Performance+Test+Suite)
5. Run test suites on testbeds

# Test Cases
Test Cases on Intel testbed, see [Peformance Test Suite](https://wiki.tungsten.io/display/TUN/Performance+Test+Suite)
1. iPerf TCP throughput
2. VPPV throughput

