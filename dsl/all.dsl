
def gitUrl = 'https://github.com/tungstenfabric/tf-openlab-ci.git'

job('nightly_seed') {
    scm {
      git {
        remote {
          url(gitUrl)
          name("origin")
        }
        branch("*/master")
      }
    }

    triggers {
        scm('H/5 * * * *')
    }
  
    steps {
      dsl {
        external("./dsl/nightly.dsl")
        removeAction("IGNORE")
        ignoreExisting(false)
      }
    }
}


job('weekly_seed') {
    scm {
      git {
        remote {
          url(gitUrl)
          name("origin")
          credentials('Teamforge')
        }
        branch("*/master")
      }
    }

    triggers {
        scm('H/5 * * * *')
    }
  
    steps {
      dsl {
        external("./dsl/weekly.dsl")
        removeAction("IGNORE")
        ignoreExisting(false)
      }
    }
}


job('release_seed') {
    scm {
      git {
        remote {
          url(gitUrl)
          name("origin")
          credentials('Teamforge')
        }
        branch("*/master")
      }
    }

    triggers {
        scm('H/5 * * * *')
    }
  
    steps {
      dsl {
        external("./dsl/release.dsl")
        removeAction("IGNORE")
        ignoreExisting(false)
      }
    }
}


job('smoke_seed') {
    scm {
      git {
        remote {
          url(gitUrl)
          name("origin")
          credentials('Teamforge')
        }
        branch("*/master")
      }
    }

    triggers {
        scm('H/5 * * * *')
    }
  
    steps {
      dsl {
        external("./dsl/smoke.dsl")
        removeAction("IGNORE")
        ignoreExisting(false)
      }
    }
}



listView('seeds') {
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
        name('nightly_seed')
        name('weekly_seed')
        name('release_seed')
        name('smoke_seed')
    }
}
