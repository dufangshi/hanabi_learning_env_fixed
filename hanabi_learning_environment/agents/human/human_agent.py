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
        self.player_id = -1
        self.last_action = None
    
    def set_player_id(self, id):
        self.player_id = id

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
        self.last_action = action
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
            'last_action': observation['last_action'],
            'player_id': self.player_id, 
            'waiting': 'Your turn to play'
        }
        print(translate_observation_to_natural_language(data))
        await self.send_observation(data)
        action_idx = await self.wait_for_action()
        return observation['legal_moves'][action_idx]
    
    def act_end(self, episode_reward):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._act_end(episode_reward))
        loop.close()

    async def _act_end(self, episode_reward):
        # Send a game-end notification to the client with the final score.
        await self.send_observation({'event': f'game end with score {episode_reward}'})
    
    def update_observation(self, observation, waiting_message):
        """
        Update the client with the latest observation and a waiting status.
        waiting_message: a string such as "Waiting for opponent to play" or "Your turn to play"
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._update_observation(observation, waiting_message))
        loop.close()
    
    async def _update_observation(self, observation, waiting_message):
        print("observation try to send", observation)
        observation = observation['player_observations'][self.player_id]
        data = {
            'info': parse_hanabi_state(str(observation["pyhanabi"])),
            'actions': {i: move for i, move in enumerate(observation['legal_moves'])},
            'last_action': self.last_action,
            'player_id': self.player_id, 
            'waiting': waiting_message
        }
        await self.send_observation(data)
        print("obs sent")



def translate_observation_to_natural_language(obs: dict) -> str:
    """Translate a Hanabi game observation into a natural language summary."""
    lines = []
    
    # Extract game tokens and basic info
    info = obs.get("info", {})
    life_tokens = info.get("life_tokens", 0)
    info_tokens = info.get("info_tokens", 0)
    lines.append(f"Game Tokens: There are {life_tokens} life token(s) and {info_tokens} information token(s) available.")
    
    # Fireworks status
    fireworks = info.get("fireworks", {})
    if fireworks:
        fireworks_status = ", ".join(f"{color}: {count}" for color, count in fireworks.items())
        lines.append(f"Fireworks Status: {fireworks_status}.")
    
    # Hands
    hands = info.get("hands", {})
    
    # Current player's hand
    cur_player_hand = hands.get("cur_player", [])
    lines.append(f"Current Player's Hand ({len(cur_player_hand)} card(s)):")
    for card in cur_player_hand:
        idx = card.get("index", "?")
        card_val = card.get("card", "Unknown")
        card_info = card.get("info", "Unknown")
        possible_colors = ", ".join(card.get("col", []))
        possible_ranks = ", ".join(card.get("rank", []))
        lines.append(f"  - Card {idx}: Value = {card_val}, Info = {card_info}; possible colors: [{possible_colors}]; possible ranks: [{possible_ranks}].")
    
    # Other players' hands
    others_hand = hands.get("others", [])
    lines.append(f"Other Players' Hands ({len(others_hand)} card(s)):")
    for card in others_hand:
        idx = card.get("index", "?")
        card_val = card.get("card", "Unknown")
        card_info = card.get("info", "Unknown")
        colors = ", ".join(card.get("col", []))
        ranks = ", ".join(card.get("rank", []))
        lines.append(f"  - Card {idx}: Value = {card_val}, Info = {card_info}; colors: [{colors}]; ranks: [{ranks}].")
    
    # Deck size and discards
    deck_size = info.get("deck_size", 0)
    lines.append(f"Deck: There are {deck_size} cards remaining in the deck.")
    discards = info.get("discards", [])
    if discards:
        discards_str = ", ".join(discards)
        lines.append(f"Discards: The discard pile contains: {discards_str}.")
    
    # Actions history
    actions = obs.get("actions", {})
    if actions:
        lines.append("Actions Performed So Far:")
        for key in sorted(actions, key=lambda x: int(x)):
            action = actions[key]
            action_type = action.get("action_type", "UNKNOWN")
            if action_type in ["DISCARD", "PLAY"]:
                card_index = action.get("card_index", "?")
                lines.append(f"  - Action {key}: {action_type} card at index {card_index}.")
            elif action_type == "REVEAL_COLOR":
                target_offset = action.get("target_offset", "?")
                color = action.get("color", "?")
                lines.append(f"  - Action {key}: Reveal color '{color}' to player at offset {target_offset}.")
            elif action_type == "REVEAL_RANK":
                target_offset = action.get("target_offset", "?")
                rank = action.get("rank", "?")
                lines.append(f"  - Action {key}: Reveal rank '{rank+1}' to player at offset {target_offset}.")
            else:
                lines.append(f"  - Action {key}: {action}.")
    
    # Last action details
    last_action = obs.get("last_action", {})
    if last_action:
        player_id = last_action.get("player_id", "?")
        action = last_action.get("action", {})
        action_type = action.get("action_type", "UNKNOWN")
        if action_type in ["DISCARD", "PLAY"]:
            card_index = action.get("card_index", "?")
            last_action_desc = f"{action_type} card at index {card_index}"
        elif action_type == "REVEAL_COLOR":
            target_offset = action.get("target_offset", "?")
            color = action.get("color", "?")
            last_action_desc = f"Reveal color '{color}' to player at offset {target_offset}"
        elif action_type == "REVEAL_RANK":
            target_offset = action.get("target_offset", "?")
            rank = action.get("rank", "?")
            last_action_desc = f"Reveal rank '{rank+1}' to player at offset {target_offset}"
        else:
            last_action_desc = str(action)
        lines.append(f"Last Action: Player {player_id} performed action: {last_action_desc}.")
    
    return "\n".join(lines)




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
        if line.startswith("Cur player"):
            i += 1  # Skip "Hands:" line
            continue
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
        if line.startswith("Cur player"):
            i += 1  # Skip "Hands:" line
            continue
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