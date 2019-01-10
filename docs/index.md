# Welcome to giTrack

[![giTrack demonstration](./assets/demonstration-short.gif)](https://asciinema.org/a/220104)

## Zero-touch time tracking

giTrack is an utility that aims to make developer's life simpler by automatizing the frequent management's requirement of
reporting the time spent. It does so using Git's commit messages and times for creating time entries, which to my
experience correlates quiet a lot. It won't produce 100% accurate reports, but it should be "good enough" to meet the
requirement (and it will at least motivate the developer to write proper commit's messages).

## Requirements

* Python 3.5 and higher
* Git
* Platform: Linux or MacOS

## Quick start

Install giTrack:

```shell
# Either using pip
$ pip install gitrack

# Or using pex build
$ curl https://raw.githubusercontent.com/AuHau/gitrack/master/bin/install.sh | bash
```

Go to the repository you want to track, initialize it and start tracking!

```shell
$ gitrack init

$ gitrack start

# Do your work and commit it, when you are finished stop tracking

$ gitrack stop
```

## Features

* Tracking time using Git
* Support for tasks
* Support for projects
* Prompt integration

## Providers

giTracks has notion of providers which are the backends where the time entries are stored. Currently supported providers:

* [Toggl](./providers.md#toggl)
  