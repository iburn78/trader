import asyncio
import struct
import pickle
from ws_tools import read_pickle, write_pickle
# Central function to read messages from the server
async def read_from_server(reader):
    while True:
        try:
            response = await read_pickle(reader)
            print(f"Received message: {response}")
        except Exception as e:
            print(f"Error: {e}")
            break

# One-time query to the server
async def query_data(writer):
    print("Sending one-time query to the server")

    command = {
        "code": "009530",
        "action": "Dump",
        "quantity": "100",
    }
    await write_pickle(writer, command)
    print("Query sent")

# Main task to handle both querying and listening
async def main():
    reader, writer = await asyncio.open_connection("127.0.0.1", 8888)
    print("Connected to the server")

    # Create tasks for listening and querying
    listen_task = asyncio.create_task(read_from_server(reader))
    query_task = asyncio.create_task(query_data(writer))

    # Wait for the query task to finish; keep listening indefinitely
    await query_task
    await listen_task  # This will run until the server disconnects

    # Close the connection
    writer.close()
    await writer.wait_closed()
    print("Disconnected from server")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("KeyboardInterrupt received. Shutting down...")
