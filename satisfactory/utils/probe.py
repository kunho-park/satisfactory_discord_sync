import asyncio
import struct
import time

from enum import Enum, auto


class GameState(Enum):
    UNKNOWN = auto()
    NO_GAME_LOADED = auto()
    CREATING_GAME = auto()
    GAME_ONGOING = auto()


protocolMagic = 0xF6D5


class ClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_response, on_error):
        self.on_response = on_response
        self.on_error = on_error

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        self.on_response(data)

    def error_received(self, exc):
        self.on_error(exc)

    def connection_lost(self, exc):
        pass


async def probe(address="127.0.0.1", port=7777, timeout=10):
    loop = asyncio.get_event_loop()
    now = int(time.time() * 1000)
    message = struct.pack("<HBBQ B", protocolMagic, 0, 1, now, 1)

    response_future = loop.create_future()

    def on_response(data):
        if not response_future.done():
            response_future.set_result(data)

    def on_error(exc):
        if not response_future.done():
            response_future.set_exception(exc)

    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ClientProtocol(on_response, on_error), remote_addr=(address, int(port))
    )

    try:
        transport.sendto(message)
        data = await asyncio.wait_for(response_future, timeout)

        buf = data

        magic, messageType, protocolVersion = struct.unpack_from("<HBB", buf, 0)
        if magic == protocolMagic and messageType == 1 and protocolVersion == 1:
            payloadOffset = 4

            (clientData,) = struct.unpack_from("<Q", buf, payloadOffset)
            serverStateByte = buf[payloadOffset + 8]
            serverState = (
                GameState(serverStateByte)
                if serverStateByte < len(GameState)
                else GameState.UNKNOWN
            )

            (serverVersion,) = struct.unpack_from("<I", buf, payloadOffset + 9)
            (serverFlags,) = struct.unpack_from("<Q", buf, payloadOffset + 13)
            numSubStates = buf[payloadOffset + 21]
            subStates = []

            offset = payloadOffset + 22

            for _ in range(numSubStates):
                id = buf[offset]
                (version,) = struct.unpack_from("<H", buf, offset + 1)
                subStates.append({"id": id, "version": version})
                offset += 3

            (serverNameLength,) = struct.unpack_from("<H", buf, offset)
            offset += 2

            serverNameBytes = buf[offset : offset + serverNameLength]
            serverName = serverNameBytes.decode("utf-8", errors="ignore")
            offset += serverNameLength

            lastByte = buf[offset]

            if len(buf) == (offset + 1) and lastByte == 1 and clientData == now:
                return {
                    "protocolVersion": protocolVersion,
                    "clientData": clientData,
                    "serverState": serverState,
                    "serverVersion": serverVersion,
                    "serverFlags": serverFlags,
                    "subStates": subStates,
                    "serverName": serverName,
                }

        raise Exception("Unexpected response")
    except:
        return None
    finally:
        transport.close()
