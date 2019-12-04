#
# TODO: Rewrite UDP handling to be properly async instead of blocking
#

from providers.provider import Provider
from device import devices
from devices.retroarch import RetroarchDevice
import socket
from asyncio import wait_for, start_server, get_event_loop, sleep

STATE_NONE = 0
STATE_DETECT_GAME = 1
STATE_DETECT_HEADER = 2
STATE_RUNNING = 3

class RetroarchProvider(Provider):
    def __init__(self, host = "localhost", port = 55355):
        Provider.__init__(self)
        self.device_id = 0
        self.port = port
        self.host = host
        self.running = True
        self.connected = False
        self.state = STATE_NONE
        self.address = (host, port)
        self.loop = get_event_loop()
        self.rom_access = False
        self.rom_type = 0
        self.rom_name = "Unknown"
        self.version = "Unknown"
        self.loop.create_task(self.handle_connection())
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.socket.settimeout(0.1)
        self.device = None

    def read_core_ram(self, address, length):
        self.socket.sendto(bytes(f"READ_CORE_RAM {address:x} {length}\n", "utf-8"), self.address)
        data, server = self.socket.recvfrom(2048)
        response = data.decode("utf-8")
        command, address, ram = response.split(" ", 2)
        return ram.strip()

    async def handle_connection(self):
        while self.running:
            try:
                if not self.connected:
                    self.socket.sendto(bytes("VERSION\n", "utf-8"), self.address)
                    data, server = self.socket.recvfrom(1024)
                    if data is not None:
                        version = data.decode("utf-8").strip()
                        self.version = version
                        print(f"RetroarchProvider < Got RA Version {version}")
                        self.connected = True
                        self.state = STATE_DETECT_GAME
                
                if self.connected:
                    if self.state == STATE_DETECT_GAME:
                        ram = self.read_core_ram(0, 1)
                        if ram != "-1":
                            print(f"RetroarchProvider < Detected running game")
                            self.state = STATE_DETECT_HEADER
                    
                    if self.state == STATE_DETECT_HEADER:
                        ram = [int(x, 16) for x in self.read_core_ram(0xFFC0, 32).split(" ")]
                        rom_name = "".join([chr(x) for x in ram[:21]])
                        rom_makeup = ram[21]
                        rom_type = ram[22]
                        rom_size = ram[23]
                        rom_sram = ram[24]
                        rom_id = ram[26]

                        if (rom_makeup & 0b11100000) == 0x20:
                            if rom_size < 0x10 and rom_sram < 0x10:
                                if rom_id < 0x05 or rom_id == 0x33:
                                    self.rom_access = True
                                    self.rom_name = rom_name
                                    self.rom_type = (rom_type & 0x01)
                        
                        self.device_id += 1
                        self.socket.settimeout(5) # Raise timout while we're doing things to account for interruptions
                        self.device = RetroarchDevice(self.socket, self.address, self.device_id, self.version, self.rom_name, self.rom_access, self.rom_type)
                        devices[self.device.id] = self.device                        
                        self.state = STATE_RUNNING
                    
                    if self.state == STATE_RUNNING:
                        if self.device.connected == False:
                            if self.device in devices:
                                del devices[self.device.id]
                            self.device = None
                            self.connected = False
                            self.socket.settimeout(0.1) # low timeout when attempting to connect to not block event loop for too long
                            self.state = STATE_NONE

            except Exception as ex:
                if self.device is not None:
                    if self.device in devices:
                        del devices[self.device.id]
                    self.device = None
                self.connected = False
                self.socket.settimeout(0.1) # low timeout when attempting to connect to not block event loop for too long
                self.state = STATE_NONE

            await sleep(5)

            




    