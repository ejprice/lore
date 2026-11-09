"""RULING-14 B2 trigger replay: come_up() on a port someone took during go_down() must fail LOUDLY (EADDRINUSE),
never come up on another port. CONTROL: with the port free, come_up() serves on the SAME port."""
import asyncio, errno, socket, sys
sys.path.insert(0, "loremaster/tests")
from _sdk3_proxy import StoreBounceProxy

UPSTREAM = "ws://127.0.0.1:18000/rpc"

async def leg(occupy: bool) -> str:
    proxy = StoreBounceProxy(UPSTREAM)
    await proxy.start()
    port = proxy._port
    await proxy.go_down()
    squatter = None
    if occupy:
        squatter = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        squatter.bind(("127.0.0.1", port)); squatter.listen()   # another session takes the number
    try:
        await proxy.come_up()
        return f"came up, port {proxy._port} (same={proxy._port == port})"
    except OSError as error:
        return f"RAISED {type(error).__name__} errno={error.errno} ({errno.errorcode.get(error.errno)})"
    finally:
        if squatter: squatter.close()
        await proxy.close()

print("CONTROL port free :", asyncio.run(leg(False)))
print("TRIGGER port taken:", asyncio.run(leg(True)))
