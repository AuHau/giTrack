# giTrack

[![giTrack demonstration](https://raw.githubusercontent.com/AuHau/giTrack/master/docs/assets/demonstration-short.gif)](https://asciinema.org/a/220104)

![Platform](https://img.shields.io/badge/platform-macos%20%7C%20linux-lightgrey.svg)
[![PyPI version](https://badge.fury.io/py/gitrack.svg)](https://badge.fury.io/py/gitrack) 
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/gitrack.svg)](https://pypi.org/project/gitrack)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/gitrack.svg)](https://pypi.org/project/gitrack/) 
[![codecov](https://codecov.io/gh/AuHau/gitrack/branch/master/graph/badge.svg)](https://codecov.io/gh/AuHau/gitrack) 
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/fd28ce2a500a4b1fab6f9a0a40e2fa80)](https://app.codacy.com/app/AuHau/giTrack?utm_source=github.com&utm_medium=referral&utm_content=AuHau/giTrack&utm_campaign=Badge_Grade_Dashboard)
[![Updates](https://pyup.io/repos/github/AuHau/giTrack/shield.svg)](https://pyup.io/repos/github/AuHau/giTrack/)

> Zero-touch time tracking using Git

## Background

giTrack is an utility that aims to make developer's life simpler by taking out the frequent management's requirement of
reporting the time spent. It does so using Git's commit messages and times for creating time entries, which to my
experience correlates quiet a lot. It won't produce 100% accurate reports, but it should be "good enough" to meet the
requirement (and it will at least motivate the developer to write proper commit's messages).

### Providers

giTracks has notion of providers which are the backends where the time entries are stored. Current providers:

* [Toggl](https://toggl.com)
 
Feel free to open an issue with a request for new providers! Anything that has an API should be possible to plug-in.

## Install

Easiest way to install this package is through PyPi:

```shell
$ pip install gitrack
```

It is also possible to use [pex](https://github.com/pantsbuild/pex) build which leaves out the hassle around `pip` (virtualenvs etc.).
You can download the build from [latest release](https://github.com/auhau/gitrack/release/latest) either manually or using
small installer script:

```shell
$ curl https://raw.githubusercontent.com/AuHau/gitrack/master/bin/install.sh | bash
```

## Usage

For full overview of giTrack's capabilities please see [full documentation](https://gitrack.adam-uhlir.me).

```shell
# Initialize Git repo for giTrack's usage
$ gitrack init

# Start giTrack's tracking
$ gitrack start

# If you want to see the status of giTrack in your shell
$ gitrack prompt

# Do your work and commit it, giTrack will pick it up

# At the end of your work stop giTrack's tracking
$ gitrack stop
```

## Contributing

Feel free to dive in, contributions are welcomed! [Open an issue](https://github.com/auhau/gitrack/issues/new) or submit PRs.

For PRs and tips about development please see [contribution guideline](https://github.com/AuHau/giTrack/blob/master/CONTRIBUTING.md).

## License

[MIT ©  Adam Uhlir](https://github.com/AuHau/giTrack/blob/master/LICENSE)