import httpx
with httpx.stream('GET', 'http://127.0.0.1:8000/api/stream/leaderboard', timeout=5.0) as r:
    for chunk in r.iter_bytes(chunk_size=128):
        print("CHUNK:", chunk)
        break
