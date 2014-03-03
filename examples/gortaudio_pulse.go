package main

import (
    "fmt"
    "strings"

    "bitbucket.org/whitelynx/gortaudio"
)

func main() {
    audio := gortaudio.NewRtAudio(gortaudio.LINUX_PULSE)
    fmt.Printf("Using %s audio API.\n", audio.GetCurrentApi())

    // Determine the number of devices available
    devices := audio.GetDeviceCount()
    fmt.Printf("%d devices found...\n", devices)

    // Scan through devices for various capabilities
    var i uint = 0
    for ; i < devices; i++ {
        info := audio.GetDeviceInfo(i)

        if info.GetProbed() {
            fmt.Printf("\nDevice %d: \033[4;36m%s\033[m\n", i, info.GetName())

            if info.GetIsDefaultInput() {
                fmt.Println("    is the \033[1mdefault input\033[m")
            }
            if info.GetIsDefaultOutput() {
                fmt.Println("    is the \033[1mdefault output\033[m")
            }

            inChans, outChans, dupChans := info.GetInputChannels(), info.GetOutputChannels(), info.GetDuplexChannels()

            if inChans > 0 {
                fmt.Printf("    maximum input channels: \033[1m%d\033[m\n", inChans)
            }
            if outChans > 0 {
                fmt.Printf("    maximum output channels: \033[1m%d\033[m\n", outChans)
            }
            if dupChans > 0 {
                fmt.Printf("    maximum duplex channels: \033[1m%d\033[m\n", dupChans)
            }

            sampleRatesVec := info.GetSampleRates()
            sampleRates := []string {}
            for i := 0; i < sampleRatesVec.Size(); i++ {
                sampleRates = append(sampleRates, fmt.Sprint(sampleRatesVec.Get(i)))
            }
            fmt.Printf("    supported sample rates: \033[1m%s\033[m\n", strings.Join(sampleRates, ", "))

            nativeFormats := info.GetNativeFormats()
            dataFormats := []string {}
			if nativeFormats & uint32(gortaudio.RTAUDIO_SINT8) != 0 {
				dataFormats = append(dataFormats, "8-bit signed integer")
			}
			if nativeFormats & uint32(gortaudio.RTAUDIO_SINT16) != 0 {
				dataFormats = append(dataFormats, "16-bit signed integer")
			}
			if nativeFormats & uint32(gortaudio.RTAUDIO_SINT24) != 0 {
				dataFormats = append(dataFormats, "24-bit signed integer")
			}
			if nativeFormats & uint32(gortaudio.RTAUDIO_SINT32) != 0 {
				dataFormats = append(dataFormats, "32-bit signed integer")
			}
			if nativeFormats & uint32(gortaudio.RTAUDIO_FLOAT32) != 0 {
				dataFormats = append(dataFormats, "single-precision floating-point")
			}
			if nativeFormats & uint32(gortaudio.RTAUDIO_FLOAT64) != 0 {
				dataFormats = append(dataFormats, "double-precision floating-point")
			}
            fmt.Printf("    supported data formats: \033[1m%s\033[m\n", strings.Join(dataFormats, ", "))
        } else {
            fmt.Printf("\n\033[1;33mDevice %d (\033[4;36m%s\033[m) could not be probed!\033[m\n", i, info.GetName())
        }
    }
}
