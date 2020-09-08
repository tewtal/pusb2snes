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

    async def boot(self, path):
        async with self.lock:
            pass
        return False
    
    async def reset(self):
        async with self.lock:
            pass
        return False

    async def menu(self):
        async with self.lock:
            pass
        return False

    async def mv(self, source, target):
        async with self.lock:
            pass
        return False

    async def mkdir(self, target):
        async with self.lock:
            pass
        return False

    async def rm(self, target):
        async with self.lock:
            pass
        return False

    async def ls(self, target):
        async with self.lock:
            pass
        return None

    async def upload(self, source, target):
        async with self.lock:
            pass
        return False

    async def download(self, target):
        async with self.lock:
            pass
        return None
