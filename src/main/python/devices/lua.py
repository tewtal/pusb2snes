from devices.device import Device
from util import remap_memory
from device import devices
import asyncio
import socket
import json

class LuaDevice(Device):
    def __init__(self, num, protocol, version, reader, writer):
        Device.__init__(self)
        self.num = num
        self.version = version
        self.name = f"LuaDevice {self.version} {self.num}"
        self.id = f"LuaDevice {self.num}"
        self.type = "Lua"
        self.reader = reader
        self.writer = writer
        self.protocol = protocol
        print(f"LuaDevice < Created {self.name}")

    def __del__(self):
        # Close socket
        self.writer.close()
        print(f"LuaDevice > Deleted {self.name}")

    def stop(self):
        del devices[self.id]

    async def read(self, ws, space, address, length):
        if space == "SNES":
            async with self.lock:
                try:
                    memtype, address = remap_memory(address)
                    self.writer.write(bytes(f"Read|{address}|{length}|{memtype}\n", "utf-8"))
                    await asyncio.wait_for(self.writer.drain(), 10.0)
                    json_data = await asyncio.wait_for(self.reader.readline(), 10.0)
                    data = json.loads(json_data)
                    d = bytes(data["data"])
                    return d
                except Exception as ex:
                    print(repr(ex))
                    self.stop()
                    return None
        else:
            return bytes([])

    async def write(self, space, address, data):
        if space == "SNES":
            async with self.lock:
                try:
                    memtype, address = remap_memory(address)
                    write_str = f"Write|{address}|{memtype}|"
                    write_str += "|".join([str(x) for x in data])
                    self.writer.write(bytes(write_str + "\n", "utf-8"))
                    await asyncio.wait_for(self.writer.drain(), 10.0)
                    return True
                except Exception as ex:
                    print(repr(ex))
                    self.stop()
                    return None
        return False