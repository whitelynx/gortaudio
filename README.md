GoRtAudio
=========

[Go](http://golang.org/) bindings for [RtAudio](http://www.music.mcgill.ca/~gary/rtaudio/)


Prerequisites
-------------

- [Go](http://golang.org/) version 1.x
- [RtAudio](http://www.music.mcgill.ca/~gary/rtaudio/) version 4.x
- [SWIG](http://www.swig.org/) version 2.0 or newer


Building
--------

```bash
./waf configure build
```


Testing
-------

```bash
cd build
./test_gortaudio
```

Or, to test the installed version:

```bash
env LD_LIBRARY_PATH=$GOPATH/pkg/linux_amd64/bitbucket.org/whitelynx $GOPATH/bin/test_gortaudio
```


Installing
----------

```bash
./waf install
```
