# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A simple episode runner using the RL environment."""

from __future__ import print_function

import sys, os
parent_dir = os.path.abspath(os.path.dirname(__file__))
idx = parent_dir.rfind("/")
parent_dir = parent_dir[:idx]
sys.path.append(parent_dir)

sys.path.append(parent_dir+"/hanabi_learning_environment")


# idx = parent_dir.rfind("/")
# parent_dir = parent_dir[:idx]
sys.path.append(parent_dir+"/hanabi_learning_environment/agents/rainbow")


sys.path.append(parent_dir+"/hanabi_learning_environment/agents")

import getopt
import random
# from hanabi_learning_environment import rl_env
from hanabi_learning_environment.agents.random_agent import RandomAgent
from hanabi_learning_environment.agents.simple_agent import SimpleAgent
from rainbow_agent_wrapper import Agent as RainbowAgent
from hanabi_learning_environment import rl_env
print(sys.path)
from agents.human import HumanAgent, HumanWebAgent

AGENT_CLASSES = {'SimpleAgent': SimpleAgent, 'RandomAgent': RandomAgent, 'RainbowAgent': RainbowAgent, 'HumanAgent': HumanAgent}


class Runner(object):
  """Runner class."""

  def __init__(self, flags):
    """Initialize runner."""
    self.flags = flags
    self.agent_config = {'players': flags['players']}
    self.environment = rl_env.make('Hanabi-Full', num_players=flags['players'])
    self.agent_class = AGENT_CLASSES[flags['agent_class']]

    self.num_players = flags['players']
    self.agent_config = {
            'players': self.num_players,
            'num_moves': self.environment.num_moves(),
            'observation_size': self.environment.vectorized_observation_shape()[0]}
    print(self.agent_config)
    self.agent_object = self.agent_class(self.agent_config)

  def run(self, interactive=False, webAgent=None):
    """Run episodes."""
    if interactive: # Play with human
      observations = self.environment.reset()
      # agents = [self.agent_class(self.agent_config)
      #           for _ in range(self.flags['players'])]
      agents = []
      agents.append(self.agent_object)
      if not webAgent:
        human_agent = HumanAgent()
        agents.append(human_agent)
      else:
        agents.append(webAgent)
      done = False
      episode_reward = 0
      
      while not done:
        curr_player_id=observations['player_observations'][0]['current_player']
        for agent_id, agent in enumerate(agents):
          if agent_id != curr_player_id:
            continue
          player_obs = observations['player_observations'][curr_player_id]
          action = agent.act(player_obs)
          assert action is not None
          current_player_action = action
        # Make an environment step.
        print('Agent: {} action: {}'.format(player_obs['current_player'],
                                            current_player_action))
        observations, reward, done, unused_info = self.environment.step(
            current_player_action)
        print('get reward:' , reward)
        episode_reward += (reward if reward > 0 else 0)
      print('Curr Reward: %.3f' % episode_reward)
      agents[1].act(episode_reward) #close connection
      return episode_reward



    rewards = []
    for episode in range(self.flags['num_episodes']):
      observations = self.environment.reset()
      # agents = [self.agent_class(self.agent_config)
      #           for _ in range(self.flags['players'])]
      agents = []
      agents.append(self.agent_object)
      agents.append(self.agent_object)
      done = False
      episode_reward = 0
      while not done:
        for agent_id, agent in enumerate(agents):
          observation = observations['player_observations'][agent_id]
          action = agent.act(observation)
          if observation['current_player'] == agent_id:
            assert action is not None
            current_player_action = action
          else:
            assert action is None
        # Make an environment step.
        print('Agent: {} action: {}'.format(observation['current_player'],
                                            current_player_action))
        observations, reward, done, unused_info = self.environment.step(
            current_player_action)
        episode_reward += reward
      rewards.append(episode_reward)
      print('Running episode: %d' % episode)
      print('Curr Reward: %.3f' % episode_reward)
    return rewards
  
humanWebPlayer = HumanWebAgent()
def webPlay():
  runner = Runner({'players': 2, 'num_episodes': 1, 'agent_class': 'RainbowAgent'})
  runner.run(True, humanWebPlayer)


if __name__ == "__main__":
  webPlay()
  # flags = {'players': 2, 'num_episodes': 200, 'agent_class': 'RainbowAgent'}
  # options, arguments = getopt.getopt(sys.argv[1:], '',
  #                                    ['players=',
  #                                     'num_episodes=',
  #                                     'agent_class='])
  # if arguments:
  #   sys.exit('usage: rl_env_example.py [options]\n'
  #            '--players       number of players in the game.\n'
  #            '--num_episodes  number of game episodes to run.\n'
  #            '--agent_class   {}'.format(' or '.join(AGENT_CLASSES.keys())))
  # for flag, value in options:
  #   flag = flag[2:]  # Strip leading --.
  #   flags[flag] = type(flags[flag])(value)
  # runner = Runner(flags)
  # rewards = runner.run(True)
  # print("score list:", rewards)
  # print("average score:", sum(rewards)/len(rewards))
