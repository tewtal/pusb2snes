import asyncio
import websockets
import json
import device

connected = set()

MSG_JSON = 0
MSG_BINARY_WRITE = 1

class Client:
    def __init__(self, websocket):
        self.websocket = websocket
        self.name = "Undefined"
        self.device = None
        self.protocol = 1
        self.msg_state = MSG_JSON
        self.msg_data = None
        self.data = bytes([])
    
    async def handle_message(self, message):
        if self.msg_state == MSG_JSON:
            data = json.loads(message)
            opcode = data["Opcode"] if "Opcode" in data else ""
            space = data["Space"] if "Space" in data else "SNES"
            operands = data["Operands"] if "Operands" in data else []
            flags = data["Flags"] if "Flags" in data else []

            #print(f"{self.name} < Opcode[{opcode}], Space[{space}], Operands{operands}")
            
            if opcode == "DeviceList":
                await self.websocket.send(json.dumps({"Results": [d.id for d in device.devices.values()]}))
            elif opcode == "Name":
                self.name = operands[0] or "Undefined"
            elif opcode == "AppVersion":
                await self.websocket.send(json.dumps({"Results": ["pUsb2Snes"]}))
            elif opcode == "Info":
                await self.websocket.send(json.dumps({"Results": [self.device.version, self.device.type, ""]}))
            elif opcode == "Attach":
                if operands[0]:
                    self.device = device.attach(operands[0])
            elif opcode == "GetAddress":
                read_data = await self.device.read(self.websocket, space, int(operands[0], 16), int(operands[1], 16))
                
                if read_data == None:                
                    await self.websocket.close()
                    return
                
                #print(f"{self.name} > Binary data >> {len(read_data)} bytes")
                if read_data != False:
                    await self.websocket.send(read_data)
            elif opcode == "PutAddress":
                self.msg_data = (space, int(operands[0], 16), int(operands[1], 16))
                self.msg_state = MSG_BINARY_WRITE            
            else:
                raise Exception("Invalid command")
        
        elif self.msg_state == MSG_BINARY_WRITE:
            space, address, length = self.msg_data
            #print(f"{self.name} < Binary data << {len(message)}/{length} bytes")
            self.data += message
            length -= len(message)
            if length <= 0:
                ret = await self.device.write(space, address, self.data)
                if ret == None:
                    await self.websocket.close()
                    return
                
                self.msg_state = MSG_JSON
                self.msg_data = None
                self.data = bytes([])
            else:
                self.msg_data = (space, address, length)
        
        else:
            raise Exception("Invalid message state")


async def connect(websocket, path):
    client = Client(websocket)
    connected.add(client)
    try:
        async for message in websocket:
            try:
                await client.handle_message(message)
            except Exception as ex:
                await client.websocket.send('{\n\t"Error":%s\n}' % (repr(ex)))
    except:
        print(f"Client {client.name} < Disconnected")
    finally:
        connected.remove(client)
