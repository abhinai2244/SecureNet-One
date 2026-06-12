import asyncio
import logging
import socket

logging.basicConfig(level=logging.INFO, format='%(message)s')

async def handle_client(reader, writer):
    try:
        # Read the CONNECT request
        request = await reader.readuntil(b'\r\n\r\n')
        lines = request.split(b'\r\n')
        method_line = lines[0].decode('utf-8')
        method, target, _ = method_line.split(' ')

        if method != 'CONNECT':
            writer.close()
            return

        host, port = target.split(':')
        port = int(port)

        # Connect to the real destination
        remote_reader, remote_writer = await asyncio.open_connection(host, port)

        # Disable Nagle's algorithm to force immediate transmission of the fragmented packets
        sock = remote_writer.get_extra_info('socket')
        if sock is not None:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

        # Tell the browser the connection is established
        writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
        await writer.drain()

        # Read the first packet from the browser (this is the TLS ClientHello containing the SNI)
        first_packet = await reader.read(4096)
        if not first_packet:
            writer.close()
            return

        # DPI BYPASS MAGIC: 
        # ISPs look for the SNI in the first packet. We split the packet into two separate TCP segments.
        # Most ISP DPI boxes are stateless and won't reassemble them, so they can't read the SNI!
        split_point = len(first_packet) // 2
        
        logging.info(f"🚀 Bypassing DPI for {host} (splitting {len(first_packet)} byte ClientHello)")
        
        # Send first half
        remote_writer.write(first_packet[:split_point])
        await remote_writer.drain()
        
        # Sleep to physically guarantee the first packet is dispatched by the OS network stack
        await asyncio.sleep(0.1)
        
        # Send second half
        remote_writer.write(first_packet[split_point:])
        await remote_writer.drain()

        # Now just pipe the rest of the connection back and forth normally
        async def pipe(r, w):
            try:
                while True:
                    data = await r.read(8192)
                    if not data:
                        break
                    w.write(data)
                    await w.drain()
            except Exception:
                pass
            finally:
                w.close()

        await asyncio.gather(
            pipe(reader, remote_writer),
            pipe(remote_reader, writer)
        )

    except Exception as e:
        logging.error(f"❌ Error handling {host if 'host' in locals() else 'unknown'}: {e}")
    finally:
        writer.close()

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8080)
    logging.info("🛡️ SecureNet DPI-Bypass Proxy running on 127.0.0.1:8080")
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
