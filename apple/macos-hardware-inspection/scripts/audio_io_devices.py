#!/usr/bin/env python3
"""List CoreAudio devices with input/output stream counts (macOS, no deps).

Why this exists: device listings that show only output channels make a Mac
look like it has audio when it actually has no capture path at all. Counting
INPUT streams answers "can this machine record audio right now?".

Usage:  python3 audio_io_devices.py
Output: one line per device, then devices_with_input=N
"""

import ctypes

CORE_AUDIO = "/System/Library/Frameworks/CoreAudio.framework/CoreAudio"

kSystemObject = 1
kPropDevices = 0x64657623  # 'dev#'
kPropName = 0x6F6E616D  # 'onam'
kPropStreams = 0x73746D23  # 'stm#'
kScopeGlobal = 0x676C6F62  # 'glob'
kScopeInput = 0x696E7074  # 'inpt'
kScopeOutput = 0x6F757470  # 'outp'

ca = ctypes.CDLL(CORE_AUDIO)


def _addr(selector, scope):
    return (ctypes.c_uint32 * 2)(selector, scope)


def device_ids():
    addr = _addr(kPropDevices, kScopeGlobal)
    size = ctypes.c_uint32(0)
    ca.AudioObjectGetPropertyDataSize(
        ctypes.c_uint32(kSystemObject), addr, ctypes.c_uint32(0), None, ctypes.byref(size)
    )
    count = size.value // 4
    ids = (ctypes.c_uint32 * count)()
    ca.AudioObjectGetPropertyData(
        ctypes.c_uint32(kSystemObject), addr, ctypes.c_uint32(0), None, ctypes.byref(size), ids
    )
    return list(ids)


def device_name(device_id):
    addr = _addr(kPropName, kScopeGlobal)
    size = ctypes.c_uint32(256)
    buf = ctypes.create_string_buffer(256)
    err = ca.AudioObjectGetPropertyData(
        ctypes.c_uint32(device_id), addr, ctypes.c_uint32(0), None, ctypes.byref(size), buf
    )
    # A non-zero OSStatus here is cosmetic: the streams are still the evidence.
    return buf.value.decode("utf-8", "ignore") if err == 0 else "<unnamed>"


def stream_count(device_id, scope):
    addr = _addr(kPropStreams, scope)
    size = ctypes.c_uint32(0)
    err = ca.AudioObjectGetPropertyDataSize(
        ctypes.c_uint32(device_id), addr, ctypes.c_uint32(0), None, ctypes.byref(size)
    )
    return size.value // 4 if err == 0 else 0


def main():
    with_input = 0
    for device_id in device_ids():
        ins = stream_count(device_id, kScopeInput)
        outs = stream_count(device_id, kScopeOutput)
        if ins:
            with_input += 1
        print("id=%-4d in=%d out=%d  %s" % (device_id, ins, outs, device_name(device_id)))
    print("devices_with_input=%d" % with_input)


main()
