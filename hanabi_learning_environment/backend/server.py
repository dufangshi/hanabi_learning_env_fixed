import sys
import os

root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(root_path)
sys.path.append(root_path+"/agents/rainbow")

from agents.human import HumanAgent, HumanWebAgent
from agents.rainbow.rainbow_agent_wrapper import Agent as RainbowAgent
import rl_env

from fastapi import FastAPI, WebSocket
import json
import uuid
import uvicorn
import asyncio
import threading

class Runner:
    def __init__(self, flags):
        self.flags = flags
        self.environment = rl_env.make('Hanabi-Full', num_players=flags['players'])
        self.agent_class = RainbowAgent
        self.num_players = flags['players']
        self.agent_config = {
            'players': self.num_players,
            'num_moves': self.environment.num_moves(),
            'observation_size': self.environment.vectorized_observation_shape()[0]
        }
        print("Agent config:", self.agent_config)
        self.agent_object = self.agent_class(self.agent_config)

    def run(self, interactive=False, webAgent=None):
        observations = self.environment.reset()
        agents = [self.agent_object, webAgent]
        done = False
        episode_reward = 0

        last_action = {"player_id": -1}  # Keep track the last action from your teamates, to show the animation on the web

        while not done:
            curr_player_id = observations['player_observations'][0]['current_player']
            for agent_id, agent in enumerate(agents):
                if agent_id != curr_player_id:
                    continue
                player_obs = observations['player_observations'][curr_player_id]
                player_obs['last_action'] = last_action
                action = agent.act(player_obs)
                assert action is not None
                current_player_action = action
            print(f'Agent {player_obs["current_player"]} action: {current_player_action}')
            last_action={"player_id": curr_player_id, "action": current_player_action}
            observations, reward, done, unused_info = self.environment.step(current_player_action)
            print('Received reward:', reward)
            episode_reward += (reward if reward > 0 else 0)
        print('Episode Reward: %.3f' % episode_reward)

        webAgent.act(episode_reward)
        return episode_reward


rooms = {}

app = FastAPI()

def run_game(room_id, human_agent):
    print(f"Starting game for room {room_id}")
    flags = {'players': 2, 'num_episodes': 1, 'agent_class': 'RainbowAgent'}
    runner = Runner(flags)
    result = runner.run(interactive=True, webAgent=human_agent)
    print(f"Game in room {room_id} finished with result: {result}")
    if room_id in rooms:
        del rooms[room_id]

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    room_id = str(uuid.uuid4())
    print(f"New websocket connection, room id: {room_id}")

    human_agent = HumanWebAgent()
    human_agent.set_websocket(websocket)
    rooms[room_id] = {'human_agent': human_agent}

    thread = threading.Thread(target=run_game, args=(room_id, human_agent), daemon=True)
    thread.start()
    rooms[room_id]['thread'] = thread


    while True:
        try:
            data = await websocket.receive_text()
        except Exception as e:
            print(f"WebSocket error in room {room_id}: {e}")
            break
        try:
            message = json.loads(data)
            if "action" in message:
                action_idx = int(message["action"])
                print(f"Received action {action_idx} for room {room_id}")
                human_agent.receive_action(action_idx)
        except json.JSONDecodeError:
            print("Invalid JSON received.")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)