import asyncio

devices = {}

class Device:
    def __init__(self):
        self.name = "Dummy device"
        self.type = "Dummy"
        self.lock = asyncio.Lock()

    def attach(self):
        pass

    async def read(self, space, address, length):
        async with self.lock:
            pass
        return bytes([0xDD] * length)

    async def write(self, space, address, data):
        async with self.lock:
            pass
        return True

from sd2snes import SD2SNESDevice

def setup():
    d = Device()
    devices[d.name] = d
    d = SD2SNESDevice("COM2")
    devices[d.name] = d

def attach(name):
    d = devices[name]
    d.attach()
    return d