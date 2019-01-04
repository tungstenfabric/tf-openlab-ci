def ciUrl =  'https://github.com/joeych18/tf-openlab-ci.git'
def vrouterUrl = 'https://github.com/Juniper/contrail-vrouter.git'

pipelineJob('smoke_intel_testbed') {
    scm {
      git {
        remote {
          url(vrouterUrl)
          name("origin")
        }
        branch("*/R5.0")
      }
    }

    triggers {
        githubPush()
    }
    
    definition {
        cpsScm {
            scm {
                git(ciUrl)
            }
            scriptPath("./pipeline/intel_testbed.jenkinsfile")
        }
    }
}

listView('smoke_jobs') {
    columns {
        weather()
        status()
        name()
        lastFailure()
        lastSuccess()
        lastDuration()
        progressBar()
        nextPossibleLaunch()
    }

    jobs {
        name('smoke_intel_testbed')
    }
}
