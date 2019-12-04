def remap_memory(addr):
    if addr < 0xE00000:
        return ("CARTROM", addr)
    elif addr >= 0xE00000 and addr <= 0xF50000:
        return ("CARTRAM", addr - 0xE00000)
    else:
        return ("WRAM", addr - 0xF50000)