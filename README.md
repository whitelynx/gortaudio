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

You can try running any of the example apps in the `examples/` directory; for instance, to test out GoRtAudio using the
default API:

```bash
env LD_LIBRARY_PATH=$GOPATH/pkg/linux_amd64/bitbucket.org/whitelynx go run examples/gortaudio_default.go
```


Installing
----------

```bash
./waf install
```


License
-------

GoRtAudio is released under the terms of the MIT license; see the [LICENSE](./LICENSE) file for details.
