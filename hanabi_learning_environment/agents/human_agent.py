import rl_env
from rl_env import Agent


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
    print("act is called")
    if observation['current_player_offset'] != 0:
      return None
    # print("curr state:", observation)
    print(f"Information:\n{observation['pyhanabi']}")
  
    action = observation['legal_moves'][self._parse_observation(observation)]
    
    return action
