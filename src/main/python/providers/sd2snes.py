from providers.provider import Provider
from device import devices
from devices.sd2snes import SD2SNESDevice
from asyncio import get_event_loop, sleep
from serial.tools.list_ports import grep
from functools import partial
import serial_asyncio

class SD2SNESProvider(Provider):
    def __init__(self):
        Provider.__init__(self)
        self.device_id = 0
        self.loop = get_event_loop()
        self.loop.create_task(self.handle_devices())
        self.running = True
    
    async def handle_devices(self):
        while self.running:
            try:
                comports = [p.device for p in grep("1209:5A22")]
                for port in comports:
                    if f'SD2SNES {port}' not in devices:
                        # device missing, create it
                        self.device_id += 1
                        sd2snes_device = partial(SD2SNESDevice, self.device_id, port, f'SD2SNES {port}')
                        self.loop.create_task(serial_asyncio.create_serial_connection(self.loop, sd2snes_device, port, baudrate=115200))
                        await sleep(1)
                
                for dev in [d for d in devices.values()]:
                    if dev.port not in comports:
                        del devices[dev.id]

            except Exception as ex:
                pass

            await sleep(1)



