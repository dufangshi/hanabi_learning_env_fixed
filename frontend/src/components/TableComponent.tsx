import React, { useState, useRef } from 'react';
import LobbyComponent from './LobbyComponent';
import GameTableComponent from './GameTableComponent';
import { parseHanabiState } from '../utils/hanabiParser';

const TableComponent: React.FC = () => {
  const [wsConnected, setWsConnected] = useState(false);
  const [roomId, setRoomId] = useState<string>("");
  const [gameStarted, setGameStarted] = useState(false);

  const [parsedState, setParsedState] = useState<any>(null);
  const [waitingMessage, setWaitingMessage] = useState<string>("");
  const [currentObservation, setCurrentObservation] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const handleInitialize = () => {
    if (wsRef.current) {
      console.log("WebSocket already initialized.");
      return;
    }
    const socket = new WebSocket(`wss://${window.location.host}/ws`);
    socket.onopen = () => {
      console.log("✅ Connected to WebSocket server");
      setWsConnected(true);
      socket.send(JSON.stringify({ status: 'connected' }));
    };
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("📩 Received:", data);
        // Update room ID if room_created or joined_room messages are received
        if (data.status === "room_created" || data.status === "joined_room") {
          setRoomId(data.room_id);
          if (data.status === "joined_room") {
            setGameStarted(true);
          }
        }
        // If back end signals game starting, update game view
        if (data.status === "game_starting") {
          setGameStarted(true);
        }
        // Handle game-end event
        if (data.event && data.event.startsWith("game end")) {
          alert(data.event);
          return;
        }
        // When game state updates, push the new observation into the queue
        if (data.info) {
          setGameStarted(true);
          setCurrentObservation(data)
          const parsed = parseHanabiState(data);
          setParsedState(parsed);
        }
        // Update waiting message if provided
        if (data.waiting) {
          setWaitingMessage(data.waiting);
        }
      } catch (err) {
        console.error("❌ Error parsing message:", err);
      }
    };
    socket.onclose = () => {
      console.log("❌ WebSocket connection closed");
      wsRef.current = null;
      setWsConnected(false);
    };
    wsRef.current = socket;
  };


  return (
    <div>
      {!wsConnected && (
        <button onClick={handleInitialize}>Initialize Connection</button>
      )}
      {wsConnected && !gameStarted && (
        <LobbyComponent 
          wsRef={wsRef} 
          roomId={roomId} 
          setRoomId={setRoomId} 
          setGameStarted={setGameStarted} 
        />
      )}
      {wsConnected && gameStarted && currentObservation && (
        <GameTableComponent 
          observation={currentObservation} 
          parsedState={parsedState} 
          wsRef={wsRef} 
          waitingMessage={waitingMessage}
        />
      )}
    </div>
  );
};

export default TableComponent;
