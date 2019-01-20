# Installation

The easiest way to install giTrack is through pip:

```shell
$ pip install gitrack
```

This though might not serve your purpose as it might collide with your development environments (different virtualenvs etc).
For such a situation there is [pex](https://github.com/pantsbuild/pex) build that can work correctly in any setup.

To install **pex** build you can either manually download the appropriate build from 
[latest release](https://github.com/auhau/gitrack/release/latest) and put it on your `$PATH`, or you can use the automated
script that will do it for you and place it to `/usr/local/bin`:

```shell
$ curl https://raw.githubusercontent.com/AuHau/gitrack/master/bin/install.sh | bash
```

!!! warning "Better safe then sorry"
    It is always good idea to read through the installing script before you run it! Especially those which
    require `sudo` access. You should trust nobody with that privilege! 
    
    That said there is nothing malicious in this one ;-) 