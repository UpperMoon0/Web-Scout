import asyncio
import time
import httpx

async def make_request(client, i):
    start = time.time()
    try:
        # Using a query that should return results
        response = await client.get(f"http://localhost:8000/api/search?query=python+asyncio+tutorial+{i}&mode=summary", timeout=60.0)
        duration = time.time() - start
        print(f"Request {i}: Status {response.status_code} in {duration:.2f}s")
        return response.status_code, duration
    except Exception as e:
        print(f"Request {i}: Failed - {str(e)}")
        return "Error", time.time() - start

async def main():
    print("Starting concurrency test...")
    async with httpx.AsyncClient() as client:
        # Fire 3 simultaneous requests
        tasks = [make_request(client, i) for i in range(3)]
        results = await asyncio.gather(*tasks)
    
    print("\nTest Complete.")
    for i, (status, duration) in enumerate(results):
        print(f"Result {i}: {status} ({duration:.2f}s)")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Test stopped.")
