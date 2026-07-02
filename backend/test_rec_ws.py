import asyncio
import json
import sys

sys.path.insert(0='backend')

async def test():
    import websockets
    uri = 'ws://localhost:8000/ws/rec'
    async with websockets.connect(uri) as ws:
        print('connected', flush=True)
        await ws.send(json.dumps({'cmd': 'start', 'url': 'https://example.com'}))
        print('sent start', flush=True)
        
        for i in range(10):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=2)
                data = json.loads(msg)
                ev = data.get('event', '?')
                if ev == 'error':
                    msg_text = data.get('message', '') or '(empty)'
                    print(f'[{i}] ERROR: {msg_text}', flush=True)
                elif ev == 'step':
                    print(f'[{i}] STEP: {data.get("step", {})}', flush=True)
                elif ev == 'done':
                    print(f'[{i}] DONE', flush=True)
                    break
                else:
                    print(f'[{i}] EVENT: {ev}', flush=True)
            except asyncio.TimeoutError:
                print(f'[{i}] timeout', flush=True)
        
        await ws.send(json.dumps({'cmd': 'stop'}))
        try:
            final = await asyncio.wait_for(ws.recv(), timeout=2)
            print('STOPPED:', json.loads(final), flush=True)
        except:
            print('no stop ack', flush=True)

asyncio.run(test())
