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
        self.block_size = 16384
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
                    data = []
                    cur_len = 0
                    read_len = 0
                    cur_addr = address
                    while cur_len < length:
                        if cur_len + self.block_size < length:
                            read_len = self.block_size
                        else:
                            read_len = length - cur_len

                        self.writer.write(bytes(f"Read|{cur_addr}|{read_len}|{memtype}\n", "utf-8"))
                        await asyncio.wait_for(self.writer.drain(), 10.0)
                        json_data = await asyncio.wait_for(self.reader.readline(), 10.0)
                        response = json.loads(json_data)
                        data += response["data"]
                        cur_len += read_len
                        cur_addr += read_len
                    return bytes(data)
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
                    cur_len = 0
                    write_len = 0
                    cur_addr = address
                    length = len(data)
                    while cur_len < length:
                        if cur_len + self.block_size < length:
                            write_len = self.block_size
                        else:
                            write_len = length - cur_len

                        write_str = f"Write|{cur_addr}|{memtype}|"
                        write_str += "|".join([str(x) for x in data[cur_len:write_len]])
                        self.writer.write(bytes(write_str + "\n", "utf-8"))
                        await asyncio.wait_for(self.writer.drain(), 10.0)
                        cur_len += write_len
                        cur_addr += write_len

                    return True
                except Exception as ex:
                    print(repr(ex))
                    self.stop()
                    return None
        return False