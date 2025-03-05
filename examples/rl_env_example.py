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

sys.path.append(parent_dir+"/hanabi_learning_environment")

parent_dir+="/hanabi_learning_environment/agents/rainbow"
# idx = parent_dir.rfind("/")
# parent_dir = parent_dir[:idx]
print("import dir:", parent_dir)
sys.path.append(parent_dir)

import getopt
from hanabi_learning_environment import rl_env
from hanabi_learning_environment.agents.random_agent import RandomAgent
from hanabi_learning_environment.agents.simple_agent import SimpleAgent
from rainbow_agent_wrapper import Agent

AGENT_CLASSES = {'SimpleAgent': SimpleAgent, 'RandomAgent': RandomAgent}


        # self.num_players = args.num_players
        # self.num_games = args.num_games
        # self.environment = rl_env.make('Hanabi-Full', num_players=self.num_players)
        # self.agent_config = {
        #         'players': self.num_players,
        #         'num_moves': self.environment.num_moves(),
        #         'observation_size': self.environment.vectorized_observation_shape()[0]}
        # print(self.agent_config)
        # self.agent_object = rainbow.Agent(self.agent_config)

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
    self.agent_object = Agent(self.agent_config)

  def run(self):
    """Run episodes."""
    rewards = []
    for episode in range(flags['num_episodes']):
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
      print('Max Reward: %.3f' % max(rewards))
    return rewards

if __name__ == "__main__":
  flags = {'players': 2, 'num_episodes': 1, 'agent_class': 'SimpleAgent'}
  options, arguments = getopt.getopt(sys.argv[1:], '',
                                     ['players=',
                                      'num_episodes=',
                                      'agent_class='])
  if arguments:
    sys.exit('usage: rl_env_example.py [options]\n'
             '--players       number of players in the game.\n'
             '--num_episodes  number of game episodes to run.\n'
             '--agent_class   {}'.format(' or '.join(AGENT_CLASSES.keys())))
  for flag, value in options:
    flag = flag[2:]  # Strip leading --.
    flags[flag] = type(flags[flag])(value)
  runner = Runner(flags)
  runner.run()
