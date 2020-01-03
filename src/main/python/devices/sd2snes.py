from devices.device import Device
from device import devices
from serial import Serial
import math
import asyncio
import serial_asyncio

OP_GET = 0
OP_PUT = 1
OP_VGET = 2
OP_VPUT = 3
OP_LS = 4
OP_MKDIR = 5
OP_RM = 6
OP_MV = 7
OP_RESET = 8
OP_BOOT = 9
OP_POWER_CYCLE = 10
OP_INFO = 11
OP_MENU_RESET = 12
OP_STREAM = 13
OP_TIME = 14
OP_RESPONSE = 15

SPACE_FILE = 0
SPACE_SNES = 1
SPACE_MSU = 2
SPACE_CMD = 3
SPACE_CONFIG = 4

FLAG_NONE = 0
FLAG_SKIPRESET = 1
FLAG_ONLYRESET = 2
FLAG_CLRX = 4
FLAG_SETX = 8
FLAG_STREAM_BURST = 16
FLAG_NORESP = 64
FLAG_DATA64B = 128

space_map = {
    "FILE": SPACE_FILE,
    "SNES": SPACE_SNES,
    "MSU" : SPACE_MSU,
    "CMD" : SPACE_CMD,
    "CONFIG": SPACE_CONFIG
}

class SD2SNESDevice(Device, asyncio.Protocol):
    def __init__(self, dev_id, port, name):
        super().__init__()
        self.device_id = dev_id
        self.port = port
        self.id = name
        self.name = name
        self.type = "SD2SNES"
        self.transport = None
        self.data = None
        self.data_len = 0
        self.data_available = asyncio.Event()
        devices[self.id] = self
        print(f"SD2SNESDevice < Created {self.name}")

    def connection_made(self, transport):
        self.transport = transport
        self.transport.serial.dtr = True
        print(f"SD2SNESDevice < Connected {self.name}")
    
    def connection_lost(self, exc):
        print(f"SD2SNESDevice > Disconnected {self.name}")
        self.transport.serial.dtr = False
        if self.id in devices:
            del devices[self.id]
    
    def data_received(self, data):
        self.data += data
        if len(self.data) >= self.data_len:
            self.data_available.set()

    def __del__(self):
        print(f"SD2SNESDevice > Deleted {self.name}")
        try:
            self.transport.close()
        except:
            pass

    def stop(self):
        self.transport.close()

    def pad_or_truncate(self, padlist, padlen):
        return padlist[:padlen] + [0] * (padlen - len(padlist))

    def pad_or_truncate_bytes(self, padlist, padlen):
        return padlist[:padlen] + bytes([0] * (padlen - len(padlist)))

    async def send_command(self, opcode, space, flags, args):        
        buf = self.pad_or_truncate([ord(c) for c in "USBA"] + [opcode, space, flags], 256)
        block_size = 512

        if space == SPACE_SNES:                
            if opcode == OP_GET or opcode == OP_PUT:
                buf[252] = (args[1] >> 24) & 0xFF
                buf[253] = (args[1] >> 16) & 0xFF
                buf[254] = (args[1] >> 8) & 0xFF
                buf[255] = args[1] & 0xFF

                buf += [
                    (args[0] >> 24) & 0xFF,
                    (args[0] >> 16) & 0xFF,
                    (args[0] >> 8) & 0xFF,
                    args[0] & 0xFF]

                buf = self.pad_or_truncate(buf, 512)
            else:
                buf = self.pad_or_truncate(buf + [ord(a) for a in args], 512)

        cmd_size = 64 if opcode == OP_VGET or opcode == OP_VPUT else len(buf)
        data = bytes(buf[:cmd_size])

        self.data = bytes()
        self.data_len = 0

        if opcode == OP_GET or opcode == OP_VGET:
            self.data_len = (math.ceil(args[1] / block_size) * block_size)
        
        if flags & FLAG_NORESP == 0:
            self.data_len += block_size

        ret = bytes()
        self.transport.write(data)
        if self.data_len > 0:
            await self.data_available.wait()
            ret = self.data
            self.data_available.clear()
            
        return ret

    async def read_mem(self, space, address, size):
        data = await self.send_command(OP_GET, space, FLAG_NORESP, [address, size])
        return data[:size]

    async def write_mem(self, space, address, data):
        resp = await self.send_command(OP_PUT, space, FLAG_NORESP, [address, len(data)])
        block_size = 512
        padded_size = (math.ceil(len(data)/512)*block_size)
        padded_data = self.pad_or_truncate_bytes(data, padded_size)
        cur_size = 0
        while cur_size < padded_size:
            self.transport.write(padded_data[cur_size:(cur_size + block_size)])
            cur_size += block_size
    
    async def boot(self, rom):
        await self.send_command(OP_BOOT, SPACE_SNES, FLAG_NORESP, rom)
    
    async def reset(self):
        await self.send_command(OP_RESET, SPACE_SNES, FLAG_NORESP, "")
    
    async def menu(self):
        await self.send_command(OP_MENU_RESET, SPACE_SNES, FLAG_NORESP, "")

    async def read(self, ws, space, address, length):
        async with self.lock:
            try:
                data = await self.read_mem(space_map[space], address, length)
            except Exception as ex:
                #print(repr(ex))
                self.stop()
                data = None
        return data

    async def write(self, space, address, data):
        async with self.lock:
            try:
                await self.write_mem(space_map[space], address, data)
            except Exception as ex:
                #print(repr(ex))
                self.stop()
                return False
        return True