from providers.provider import Provider
from device import devices
from devices.lua import LuaDevice
import socket
import logging
from asyncio import wait_for, start_server, get_event_loop

class LuaProvider(Provider):
    def __init__(self, port = 65398):
        Provider.__init__(self)
        self.device_id = 0
        self.port = port
        self.loop = get_event_loop()
        self.loop.create_task(start_server(self.handle_client, 'localhost', 65398, loop=self.loop))
    
    async def handle_client(self, reader, writer):
        logging.info(f'LuaProvider < New connection')
        lua_device = None
        try:
            # Make sure this is a valid LUA client before setting up device
            writer.write(bytes("Version\n", "utf-8"))
            await wait_for(writer.drain(), 10.0)
            version_str = await wait_for(reader.readline(), 10.0)
            version_str = version_str.decode("utf-8")
            command, protocol, version, *more = version_str.split("|")
            if command == "Version":
                self.device_id += 1
                lua_device = LuaDevice(self.device_id, protocol, version, reader, writer)
                writer.write(bytes(f"SetName|{lua_device.name}\n", "utf-8"))
                await wait_for(writer.drain(), 10.0)
            else:
                writer.close()
                return
        except Exception as ex:
            print(repr(ex))
            lua_device = None
            writer.close()
            return

        devices[lua_device.id] = lua_device


