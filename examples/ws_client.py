import asyncio
import websockets
import json

async def test_client():
    uri = "ws://localhost:8000/ws"
    
    async with websockets.connect(uri) as websocket:
        print("✅ Successfully connected to WebSocket server")

        # Send a connection success confirmation message
        await websocket.send(json.dumps({"status": "connected"}))
        print("✅ Connection confirmation message sent")

        try:
            while True:
                # Receive observation from the server
                data = await websocket.recv()
                try:
                    observation = json.loads(data)
                    print("📩 Received observation from server:", observation)
                except json.JSONDecodeError:
                    print("❌ Server sent invalid JSON data:", data)
                    continue

                # Let the user input an action
                try:
                    chosen_action = -1
                    print("Number of actions:", len(observation['actions']))
                    while not (0 <= chosen_action < len(observation['actions'])):
                        try:
                            chosen_action = int(input("🔵 Please enter the action to perform: "))
                        except ValueError:
                            print("❌ Invalid input, please enter an integer!")

                    # Send action back to the server
                    await websocket.send(json.dumps({"action": chosen_action}))
                    print(f"✅ Action sent: {chosen_action}")
                except Exception as e:
                    print("Error on decode observation")
        except websockets.exceptions.ConnectionClosed:
            print("❌ Server closed the connection")

asyncio.run(test_client())
