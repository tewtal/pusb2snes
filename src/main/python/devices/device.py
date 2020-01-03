import asyncio
import random

class Device:
    def __init__(self):
        self.name = "Dummy device"
        self.id = "Dummy device " + str(random.randint(0, 1000000))
        self.type = "Dummy"
        self.version = "1.0"        
        self.lock = asyncio.Lock()
        
    def attach(self):
        pass

    async def read(self, ws, space, address, length):
        async with self.lock:
            pass
        return bytes([0xDD] * length)

    async def write(self, space, address, data):
        async with self.lock:
            pass
        return True