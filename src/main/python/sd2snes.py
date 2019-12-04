from device import Device
import asyncio

class SD2SNESDevice(Device):
    def __init__(self, port):
        Device.__init__(self)
        self.name = f"SD2SNES {port}"
        self.type = "SD2SNES"
        self.port = port

    async def read(self, space, address, length):
        async with self.lock:
            # Read data and do things
            pass

        return bytes([0xFF] * length)

    async def write(self, space, address, data):
        async with self.lock:
            pass

        return True