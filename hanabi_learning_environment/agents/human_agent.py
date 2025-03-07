import rl_env
from rl_env import Agent

import asyncio
import json
import uvicorn
from fastapi import FastAPI, WebSocket
import threading



class HumanAgent(Agent):
  """Agent that loads and applies a pretrained rainbow model."""
  def __init__(self):
      pass

  def _parse_observation(self, current_player_observation):
    legal_moves = current_player_observation['legal_moves']
    print("Legal moves:")
    for i, m in enumerate(legal_moves):
      print(f"{i}: {m}")
    while True:
      try:
        selected_index = int(input("Select the index of your move: "))
        if 0 <= selected_index < len(legal_moves):
          return selected_index
        else:
          print("Invalid index. Please select a valid index.")
      except ValueError:
        print("Invalid input. Please enter a number.")

  def act(self, observation):
    if not isinstance(observation, dict):
        return None
    if observation['current_player_offset'] != 0:
      return None
    # print("curr state:", observation)
    print(f"Information:\n{observation['pyhanabi']}")
  
    action = observation['legal_moves'][self._parse_observation(observation)]
    
    return action
  

  
class HumanWebAgent(Agent):
    """Human Agent that communicates with a web frontend via WebSocket."""
    
    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port
        self.action_idx = -1
        self.websocket_connected = False
        self.action_received = False
        self.websocket = None  # Record WebSocket connection



        # Create FastAPI server instance
        self.app = FastAPI()
        
        # Bind WebSocket endpoint
        self.app.add_api_websocket_route("/ws", self.websocket_endpoint)

        # Start WebSocket server in the background
        threading.Thread(target=self.run_server, daemon=True).start()

    def run_server(self):
            """Run FastAPI WebSocket server in the background"""
            uvicorn.run(self.app, host=self.host, port=self.port)

    async def websocket_endpoint(self, websocket: WebSocket):
        """WebSocket server endpoint, waits for frontend connection and processes data"""
        await websocket.accept()
        print("✅ WebSocket client connected")
        
        # Record WebSocket connection
        self.websocket = websocket
        self.websocket_connected = True  # Notify waiting tasks that WebSocket is connected

        while True:
            data = await websocket.receive_text()
            try:
                print(data)
                message = json.loads(data)

                if message.get("status") == "connected":
                    print("✅ Client confirmed connection, waiting for act() to trigger sending observation")

                elif "action" in message:
                    print("📩 Received action from frontend:", message["action"])
                    self.action_idx = int(message["action"])
                    self.action_received = True  # Notify act() to continue execution

            except json.JSONDecodeError:
                print("❌ Received invalid JSON data")

    async def wait_for_action(self):
        """Wait for WebSocket client to return action"""
        
        while not self.action_received:
            import time
            time.sleep(0.1)
        self.action_received = False
        print("Action returned")

    def act(self, observation):
        """When act() is called, actively send observation to client and wait for action"""
        loop = asyncio.get_event_loop()
        if not isinstance(observation, dict):
            loop.run_until_complete(self.send_observation({'event': f'game end with score {observation}'}))
            # Close the WebSocket connection if it exists
  
            if self.websocket is not None:
                self.websocket.close()
                print("WebSocket connection closed")

            # Stop the FastAPI server
            loop = asyncio.get_event_loop()
            loop.stop()
            print("FastAPI server stopped")
            return None
        print("Waiting for action from frontend...")

        # ✅ Use `asyncio.create_task()` to start async task instead of `asyncio.run()`
        
        loop.run_until_complete(self.send_observation({'info': parse_hanabi_state(str(observation["pyhanabi"])), 
                                                       'actions': {i: item for i, item in enumerate(observation['legal_moves'])}}))

        # ✅ `await` directly waits for action, avoiding `asyncio.run()`
        loop.run_until_complete(self.wait_for_action())
        print("act return")
        return observation['legal_moves'][self.action_idx]

    async def send_observation(self, observation_data):
        """Actively send observation to client, block and wait if no WebSocket connection"""
        print("send ovs called")
        if self.websocket is None:
            print("⏳ Waiting for WebSocket client connection...")
            while not self.websocket_connected:
               import time
               time.sleep(0.1)
            print("Connection detected, continue sending")
        # Connection established, send data
        print(observation_data)
        await self.websocket.send_json(observation_data)
        print("✅ Observation data sent")



def parse_card(card_line: str, index: int) -> dict:
    """
    Parse a card string line, format like "XX || X1|RYGWB1"
    Return a dictionary, for example:
      {
         "card": "XX",
         "info": "X1",
         "detail": "RYGWB1"
      }
    """
    parts = card_line.split("||")
    if len(parts) != 2:
        # If format is not as expected, return the original string
        return {"raw": card_line.strip()}
    card = parts[0].strip()
    right = parts[1].strip()
    subparts = right.split("|")
    if len(subparts) == 2:
        info = subparts[0].strip()
        detail = subparts[1].strip()
    else:
        info = right
        detail = ""
    return {"index": index, "card": card, "info": info, "col": [c for c in detail if not c.isdigit()], "rank": [c for c in detail if c.isdigit()]}


def parse_hanabi_state(state_str: str) -> dict:
    """
    Parse Hanabi state string, return a dictionary, format example:
      {
          "life_tokens": 1,
          "info_tokens": 0,
          "fireworks": {"R": 1, "Y": 0, "G": 0, "W": 0, "B": 2},
          "hands": {
              "cur_player": [ {card1}, {card2}, ... ],
              "others": [ {card1}, {card2}, ... ]
          },
          "deck_size": 2,
          "discards": ["Y1", "W3", "G4", ...]
      }
    """
    result = {}
    lines = state_str.splitlines()
    i = 0
    n = len(lines)
    
    # Parse Life tokens
    while i < n:
        line = lines[i].strip()
        if line.startswith("Life tokens:"):
            try:
                result["life_tokens"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                result["life_tokens"] = None
            i += 1
            break
        i += 1

    # Parse Info tokens
    while i < n:
        line = lines[i].strip()
        if line.startswith("Info tokens:"):
            try:
                result["info_tokens"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                result["info_tokens"] = None
            i += 1
            break
        i += 1

    # Parse Fireworks
    while i < n:
        line = lines[i].strip()
        if line.startswith("Fireworks:"):
            fireworks_str = line.split(":", 1)[1].strip()
            fireworks_parts = fireworks_str.split()
            fireworks = {}
            for part in fireworks_parts:
                # Each part like "R1"
                if len(part) >= 2:
                    color = part[0]
                    try:
                        num = int(part[1:])
                    except ValueError:
                        num = None
                    fireworks[color] = num
            result["fireworks"] = fireworks
            i += 1
            break
        i += 1

    # Parse Hands section
    hands = {"cur_player": [], "others": []}
    while i < n:
        line = lines[i].strip()
        if line.startswith("Hands:"):
            i += 1  # Skip "Hands:" line
            break
        i += 1

    # Next line should be "Cur player"
    if i < n and lines[i].strip() == "Cur player":
        i += 1  # Skip this line

    # Current player's hand, until "-----"
    card_idx = 0
    while i < n:
        line = lines[i].strip()
        if line == "-----":
            i += 1  # Skip separator line
            break
        if line:
            card = parse_card(line, card_idx)
            hands["cur_player"].append(card)
        i += 1
        card_idx += 1

    # Other player's hand, until "Deck size:" or end
    card_idx = 0
    while i < n:
        line = lines[i].strip()
        if line.startswith("Deck size:"):
            break
        if line:
            card = parse_card(line, card_idx)
            hands["others"].append(card)
        i += 1
        card_idx += 1
    result["hands"] = hands

    # Parse Deck size
    while i < n:
        line = lines[i].strip()
        if line.startswith("Deck size:"):
            try:
                result["deck_size"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                result["deck_size"] = None
            i += 1
            break
        i += 1

    # Parse Discards
    while i < n:
        line = lines[i].strip()
        if line.startswith("Discards:"):
            discards_str = line.split(":", 1)[1].strip()
            if discards_str:
                result["discards"] = discards_str.split()
            else:
                result["discards"] = []
            i += 1
            break
        i += 1

    return result