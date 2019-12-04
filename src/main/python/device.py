import asyncio

devices = {}
providers = set()

from devices.sd2snes import SD2SNESDevice
from devices.lua import LuaDevice
from providers.lua import LuaProvider
from providers.retroarch import RetroarchProvider

def setup_devices():
    devices = {}

def setup_providers():
    providers = set()
    
    # Initialize lua provider
    providers.add(LuaProvider())

    # Initialize retroarch provider
    providers.add(RetroarchProvider())

def attach(name):
    d = devices[name]
    d.attach()
    return d