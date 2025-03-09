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
  
import queue
class HumanWebAgent(Agent):
    def __init__(self):
        self.action_queue = queue.Queue()
        self.websocket = None

    def set_websocket(self, websocket: WebSocket):
        self.websocket = websocket

    def receive_action(self, action_idx):
        self.action_queue.put(action_idx)

    async def send_observation(self, observation_data):
        while self.websocket is None:
            await asyncio.sleep(0.1)
        await self.websocket.send_json(observation_data)

    async def wait_for_action(self):
        while self.action_queue.empty():
            await asyncio.sleep(0.1)
        return self.action_queue.get()

    def act(self, observation):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        action = loop.run_until_complete(self._act(observation))
        loop.close()
        return action

    async def _act(self, observation):
        if not isinstance(observation, dict):
            await self.send_observation({'event': f'game end with score {observation}'})
            if self.websocket is not None:
                await self.websocket.close()
            return None
        data = {
            'info': parse_hanabi_state(str(observation["pyhanabi"])),
            'actions': {i: move for i, move in enumerate(observation['legal_moves'])},
            'last_action': observation['last_action']
        }
        await self.send_observation(data)
        action_idx = await self.wait_for_action()
        return observation['legal_moves'][action_idx]



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