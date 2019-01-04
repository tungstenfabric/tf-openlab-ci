# tf-openlab-ci
Jenkins configuration for Tungsten Fabric OpenLab test automation


# Jenkins Plugin Dependency

**Job DSL**, https://wiki.jenkins.io/display/JENKINS/Job+DSL+Plugin

**Workspace Cleanup**, http://wiki.jenkins-ci.org/display/JENKINS/Workspace+Cleanup+Plugin

**Performance Publisher plugin**, https://wiki.jenkins.io/display/JENKINS/PerfPublisher+Plugin


# Directory structure
├── dsl

│   ├── all.dsl

│   └── nightly.dsl

│   └── weekly.dsl

│   └── smoke.dsl

├── LICENSE

├── pipeline

│   └── intel_testbed.jenkinsfile

└── README.md

# Workflow
1. Monitor git repo changes/timer trigger
2. Update repo to latest revision
3. Build whole Tungsten Fabric by [contrail-dev-env](https://github.com/Juniper/contrail-dev-env)
4. Copy the contrail-vrouter-dpdk binary to prepared testbeds, see (Peformance Test Suite)[https://wiki.tungsten.io/display/TUN/Performance+Test+Suite]
5. Run test suites on testbeds

# Test Suites

