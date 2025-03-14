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
import time


rooms = {}

class Runner:
    def __init__(self, flags, agents):
        self.flags = flags
        self.environment = rl_env.make('Hanabi-Full', num_players=flags['players'])
        self.num_players = flags['players']
        # Initialize agents, creating a RainbowAgent if any agent slot is None
        self.agents = []
        for i, agent in enumerate(agents):
            if agent is None:
                agent_config = {
                    'players': self.num_players,
                    'num_moves': self.environment.num_moves(),
                    'observation_size': self.environment.vectorized_observation_shape()[0]
                }
                print(f"Creating RainbowAgent for player {i}, config:", agent_config)
                agent_instance = RainbowAgent(agent_config)
                self.agents.append(agent_instance)
            else:
                self.agents.append(agent)
        print("Game starting with agents:", self.agents)

    def run(self):
        observations = self.environment.reset()
        done = False
        episode_reward = 0
        last_action = {"player_id": -1}  # Track last action for animation display on frontend
        
        if hasattr(self.agents[1], "update_observation"):
            self.agents[1].update_observation(observations, "Waiting for opponent to play")

        while not done:
            # Determine which agent should act based on the current player ID
            curr_player_id = observations['player_observations'][0]['current_player']
            for agent_id, agent in enumerate(self.agents):
                if agent_id != curr_player_id:
                    continue
                player_obs = observations['player_observations'][curr_player_id]
                player_obs['last_action'] = last_action
                action = agent.act(player_obs)
                assert action is not None
                print(f'Player {curr_player_id} action: {action}')
                last_action = {"player_id": curr_player_id, "action": action}
                observations, reward, done, _ = self.environment.step(action)
                print("Received reward:", reward)
                episode_reward += (reward if reward > 0 else 0)
                
                # Determine the new current player after the step
                new_current_player = observations['player_observations'][0]['current_player']
                # Update observation for all human agents with a waiting message.
                if hasattr(agent, "update_observation"):
                    if agent_id == new_current_player:
                        waiting_message = "Your turn to play"
                    else:
                        waiting_message = "Waiting for opponent to play"
                    agent.update_observation(observations, waiting_message)
        print('Total episode reward: %.3f' % episode_reward)

        # Notify agents when the game ends (useful for human players' UI updates)
        for agent in self.agents:
            if hasattr(agent, "act_end"):
                agent.act_end(episode_reward)
        return episode_reward


def start_game(room_id, players, mode):
    print(f"Starting game for room {room_id}, mode: {mode}")
    flags = {'players': 2, 'num_episodes': 1}
    runner = Runner(flags, agents=players)
    result = runner.run()
    print(f"Game in room {room_id} finished with result: {result}")

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    human_agent = HumanWebAgent()
    human_agent.set_websocket(websocket)
    current_room_id = None  # Track the room ID associated with this connection

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"status": "error", "message": "Invalid JSON"}))
                continue

            command = message.get("command")
            if command == "create_room":
                # Client requests to create a room, mode can be "human" or "rainbow_agent"
                mode = message.get("mode", "rainbow_agent")
                room_id = str(uuid.uuid4())
                current_room_id = room_id
                human_agent.set_player_id(0)
                if mode == "human":
                    
                    # In human mode, wait for another player to join
                    rooms[room_id] = {'players': [human_agent], 'mode': mode}
                    await websocket.send_text(json.dumps({
                        "status": "room_created",
                        "room_id": room_id,
                        "mode": mode
                    }))
                    print(f"Room {room_id} created (human mode), waiting for another player to join.")
                elif mode == "rainbow_agent":
                    # Start the game immediately with a RainbowAgent as the second player
                    players = [human_agent, None]
                    await websocket.send_text(json.dumps({
                        "status": "game_starting",
                        "mode": mode
                    }))
                    thread = threading.Thread(target=start_game, args=(room_id, players, mode), daemon=True)
                    thread.start()
                else:
                    await websocket.send_text(json.dumps({"status": "error", "message": "Invalid mode"}))
            elif command == "join_room":
                # A player requests to join a specific room
                room_id = message.get("room_id")
                if room_id in rooms:
                    room = rooms[room_id]
                    if room['mode'] == "human":
                        human_agent.set_player_id(1)
                        room['players'].append(human_agent)
                        current_room_id = room_id
                        await websocket.send_text(json.dumps({
                            "status": "joined_room",
                            "room_id": room_id
                        }))
                        print(f"A player joined room {room_id}, starting the game.")
                        # Start the game when there are two human players
                        players = room['players']
                        del rooms[room_id]  # Remove room record before starting the game
                        thread = threading.Thread(target=start_game, args=(room_id, players, "human"), daemon=True)
                        thread.start()
                    else:
                        await websocket.send_text(json.dumps({"status": "error", "message": "Room mode mismatch"}))
                else:
                    await websocket.send_text(json.dumps({"status": "error", "message": "Room does not exist"}))
            elif "action" in message:
                # Process an action from a player and forward it to the appropriate agent
                try:
                    action_idx = int(message["action"])
                    print(f"Received action {action_idx} from room {current_room_id}")
                    human_agent.receive_action(action_idx)
                except ValueError:
                    await websocket.send_text(json.dumps({"status": "error", "message": "Invalid action value"}))
            else:
                await websocket.send_text(json.dumps({"status": "error", "message": "Unknown command"}))
    except Exception as e:
        print(f"WebSocket connection error: {e}")
    finally:
        print(f"Connection closed, associated room: {current_room_id}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)