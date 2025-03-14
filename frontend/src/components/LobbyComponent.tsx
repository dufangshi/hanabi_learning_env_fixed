import React, { useState } from 'react';

type LobbyProps = {
  wsRef: React.MutableRefObject<WebSocket | null>;
  roomId: string;
  setRoomId: (roomId: string) => void;
  setGameStarted: (gameStarted: boolean) => void;
};

const LobbyComponent: React.FC<LobbyProps> = ({ wsRef, roomId, setRoomId, setGameStarted }) => {
  const [inputRoomId, setInputRoomId] = useState("");
  // New state to select room mode: "human" (wait for another player) or "rainbow_agent" (play with AI)
  const [roomMode, setRoomMode] = useState<"human" | "rainbow_agent">("human");

  const handleCreateRoom = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      // Send create_room command with the chosen mode
      const createMsg = { command: "create_room", mode: roomMode };
      wsRef.current.send(JSON.stringify(createMsg));
      console.log("✅ Sent create_room command:", createMsg);
    } else {
      console.log("❌ WebSocket not connected");
    }
  };

  const handleJoinRoom = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && inputRoomId.trim() !== "") {
      // Send join_room command with the room id from input
      const joinMsg = { command: "join_room", room_id: inputRoomId.trim() };
      wsRef.current.send(JSON.stringify(joinMsg));
      console.log("✅ Sent join_room command:", joinMsg);
    } else {
      console.log("❌ WebSocket not connected or room ID is empty");
    }
  };

  return (
    <div>
      <h3>Lobby</h3>
      <div style={{ marginBottom: '1rem' }}>
        <label>
          <input 
            type="radio" 
            value="human" 
            checked={roomMode === "human"}
            onChange={() => setRoomMode("human")}
          />
          Wait for another player
        </label>
        <label style={{ marginLeft: '1rem' }}>
          <input 
            type="radio" 
            value="rainbow_agent" 
            checked={roomMode === "rainbow_agent"}
            onChange={() => setRoomMode("rainbow_agent")}
          />
          Play with Rainbow Agent
        </label>
      </div>
      <div style={{ marginBottom: '1rem' }}>
        <button onClick={handleCreateRoom}>Create Room</button>
        <button onClick={handleJoinRoom}>Join Room</button>
      </div>
      <div style={{ marginTop: '1rem' }}>
        <input 
          type="text"
          placeholder="Room ID"
          value={roomId ? roomId : inputRoomId}
          onChange={(e) => {
            // Allow input only if roomId is not already set from creation
            if (!roomId) {
              setInputRoomId(e.target.value);
            }
          }}
          readOnly={roomId ? true : false}
        />
      </div>
      {roomMode === "human" && (
        <p>Waiting for another player to join...</p>
      )}
      {roomMode === "rainbow_agent" && (
        <p>Game will start immediately with a Rainbow Agent.</p>
      )}
    </div>
  );
};

export default LobbyComponent;
