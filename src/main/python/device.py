import asyncio

devices = {}
providers = set()

from providers.lua import LuaProvider
from providers.retroarch import RetroarchProvider
from providers.sd2snes import SD2SNESProvider

def setup_devices():
    devices = {}

def setup_providers():
    providers = set()
    
    # Initialize lua provider
    providers.add(LuaProvider())

    # Initialize retroarch provider
    providers.add(RetroarchProvider())

    # Initialize SD2SNES provider
    providers.add(SD2SNESProvider())

def attach(name):
    d = devices[name]
    d.attach()
    return d