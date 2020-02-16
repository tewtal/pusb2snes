from devices.device import Device
from util import remap_memory
from device import devices
import asyncio
import socket
import json
import math

class RetroarchDevice:
    def __init__(self, socket, address, num, version, name, rom_access, rom_type):
        Device.__init__(self)
        self.name = f"Retroarch {num}"
        self.id = self.name
        self.type = "Retroarch"
        self.version = version
        self.socket = socket
        self.address = address
        self.rom_name = name
        self.rom_access = rom_access
        self.rom_type = rom_type  
        self.block_size = 512         
        self.lock = asyncio.Lock()
        self.loop = asyncio.get_event_loop()
        self.connected = True
        print(f"RetroarchDevice < Created {self.name}")

    def __del__(self):
        print(f"RetroarchDevice > Deleted {self.name}")

    def attach(self):
        pass

    def stop(self):
        del devices[self.id]
        self.connected = False

    def remap(self, memtype, addr):        
        if self.rom_access == True:
            if memtype == "CARTROM":
                if self.rom_type == 0:
                    # lorom
                    if addr < 0x400000:
                        addr = 0x800000 + (addr + (0x8000 * int(math.floor((addr + 0x8000) / 0x8000))))
                    else:
                        # exlorom
                        addr = (addr + (0x8000 * int(math.floor((addr + 0x8000) / 0x8000))))
                else:
                    # hirom
                    if addr < 0x400000:                        
                        addr = 0xC00000 + addr
                    else:
                        # exhirom
                        addr = 0x400000 + addr
            elif memtype == "CARTRAM":
                if self.rom_type == 0:
                    # lorom
                    addr += 0x700000
                else:
                    # hirom
                    bank = int(math.floor(addr / 0x2000)) + 0xA0
                    saddr = 0x6000 + (addr % 0x2000)
                    addr = (bank << 16) | saddr
            elif memtype == "WRAM":
                addr += 0x7E0000
        else:
            if memtype == "CARTROM":
                return None
            elif memtype == "CARTRAM":
                addr += 0x020000

        return int(addr)
    
    async def read_core_ram(self, address, length):
        read_str = f"READ_CORE_RAM {address:x} {length}\n"
        self.socket.sendto(bytes(read_str, "utf-8"), self.address)
        data = await asyncio.wait_for(self.loop.sock_recv(self.socket, 2048), 1.0)
        response = data.decode("utf-8")
        command, address, ram = response.split(" ", 2)
        return ram.strip()

    def write_core_ram(self, address, data):
        hexbytes = " ".join([f"{d:02X}" for d in data])
        write_str = f"WRITE_CORE_RAM {address:x} {hexbytes}\n"
        self.socket.sendto(bytes(write_str, "utf-8"), self.address)
        return True

    async def read(self, ws, space, address, length):
        if space == "SNES":
            async with self.lock:
                try:
                    memtype, addr = remap_memory(address)
                    address = self.remap(memtype, addr)
                    if address == None:
                        return bytes([0]*length)

                    data = []
                    cur_len = 0
                    cur_addr = address
                    next_addr = 0
                    read_len = 0
                    while cur_len < length:
                        if cur_len + self.block_size < length:
                            read_len = self.block_size
                        else:
                            read_len = length - cur_len
                        
                        if ((cur_addr + read_len) & 0xFFFF) < (cur_addr & 0xFFFF):
                            read_len = 0x10000 - (cur_addr & 0xFFFF)
                            next_addr = (address & 0xFF0000) + 0x010000
                            if self.rom_type == 0 and memtype == "CARTROM":
                                next_addr += 0x8000
                        else:
                            next_addr = cur_addr + read_len
                        ram_data = await self.read_core_ram(cur_addr, read_len)
                        if ram_data == "-1":
                            return bytes([0]*length)

                        ram = [int(x, 16) for x in ram_data.split(" ")]
                        data += ram
                        cur_len += read_len
                        cur_addr = next_addr
                    
                    return bytes(data)
                except Exception as ex:
                    self.stop()
                    return None
        else:
            return bytes([])


    async def write(self, space, address, data):
        if space == "SNES":
            async with self.lock:
                try:
                    memtype, addr = remap_memory(address)
                    address = self.remap(memtype, addr)
                    cur_len = 0
                    cur_pos = 0
                    cur_addr = address
                    next_addr = 0
                    write_len = 0
                    length = len(data)
                    while cur_len < length:
                        if cur_len + self.block_size < length:
                            write_len = self.block_size
                        else:
                            write_len = length - cur_len
                        
                        if ((cur_addr + write_len) & 0xFFFF) < (cur_addr & 0xFFFF):
                            write_len = 0x10000 - (cur_addr & 0xFFFF)
                            next_addr = (address & 0xFF0000) + 0x010000
                            if self.rom_type == 0 and memtype == "CARTROM":
                                next_addr += 0x8000
                        else:
                            next_addr = cur_addr + write_len
                        
                        self.write_core_ram(cur_addr, data[cur_len:write_len])
                        cur_len += write_len
                        cur_addr = next_addr
                    
                    return True
                except Exception as ex:
                    self.stop()
                    return None
        else:
            return False