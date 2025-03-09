// src/components/TableComponent.tsx
import React, { useState, useRef } from 'react';
import { parseHanabiState } from '../utils/hanabiParser';
import FireWorksComponent from './FireWorksComponent';
import DiscardsComponent from './DiscardsComponent';
import HandComponent from './HandComponent';
import InfoComponent from './InfoComponent';

type AnimationType = 
  | { type: 'play' | 'discard'; player_id: number; cardIndex: number }
  | { type: 'hint'; player_id: number; hint: { type: 'color' | 'rank'; value: string } };

const TableComponent: React.FC = () => {
  const [observation, setObservation] = useState<any>(null);
  const [parsedState, setParsedState] = useState<any>(null);
  // Cache the previous info portion of observation.info
  const [cachedInfo, setCachedInfo] = useState<any>(null);
  // Animation trigger state (if non-null, an animation is in progress)
  const [animation, setAnimation] = useState<AnimationType | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  const self_player_id=1;

  // Initialize connection on button click
  const handleInitialize = () => {
    if (wsRef.current) {
      console.log("WebSocket already initialized.");
      return;
    }
    const socket = new WebSocket('ws://localhost:8000/ws');
    socket.onopen = () => {
      console.log('✅ Connected to WebSocket server');
      socket.send(JSON.stringify({ status: 'connected' }));
    };
    let cached_info=null;
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('📩 Received state:', data);
        // Check if this is not the first action.
        if (data.last_action && data.last_action.player_id !== -1 && cached_info) {
          console.log("last action:", data.last_action)
          // If the last action is play/discard
          const lst_act = data.last_action.action;
          if (lst_act.action_type === 'PLAY' ||
            lst_act.action_type === 'DISCARD') {
            console.log("is play")
            // Trigger play/discard animation.
            // We assume that for play/discard, the action includes card_index.
            const animation = {
                type: lst_act.action_type.toLowerCase() as 'play' | 'discard',
                player_id: data.last_action.player_id,
                cardIndex: lst_act.card_index!
              };
            console.log(animation);
            setAnimation(animation);
            // Hold the cached info during the animation (1s move + 2s hold = 3s)
            setTimeout(() => {
              setObservation(data);
              setCachedInfo(data.info);
              cached_info=data.info;
              setAnimation(null);
              console.log("animation for play ended!");
            }, 1500);
          } else if (lst_act.action_type === 'REVEAL_COLOR' ||
                     lst_act.action_type === 'REVEAL_RANK') {
            // For hint actions, determine the hint details.
            const hintType = lst_act.action_type === 'REVEAL_COLOR' ? 'color' : 'rank';
            let value: string;
            if (hintType === 'color') {
              value = lst_act.color;
            } else {
              // action.rank is 0-based; convert to 1-based string.
              value = ((lst_act.rank ?? 0) + 1).toString();
            }
            // We need to look at the new observation to know about corresponding cards.
            const target_player_id = 1-data.last_action.player_id;
            let target_index=[-1];
            if(self_player_id===target_player_id){
                const new_hand = data.info.hands.cur_player;
                for (const { index, info } of new_hand) {
                    if(hintType==='color' && info.charAt(0)===value){
                        target_index.push(index)
                    }else if(hintType==='rank' && info.charAt(1)===value){
                        target_index.push(index)
                    }
                }
            }

            const animation = {
                type: 'hint',
                player_id: target_player_id,
                hint: { type: hintType, idx: target_index, value: value}
              };
            console.log(animation);
            setAnimation(animation);
            // Hold the cached info during the hint animation (3 seconds)
            setTimeout(() => {
              setObservation(data);
              setCachedInfo(data.info);
              cached_info = data.info;
              setAnimation(null);
              console.log("animation for hint ended!");
            }, 1500);
          }
        } else {
          // If it's the very first action or no cached info, update normally.
          console.log("add cached info", data.info)
          setObservation(data);
          setCachedInfo(data.info);
          cached_info = data.info;
        }
        // Also update parsedState regardless.
        const parsed = parseHanabiState(data);
        setParsedState(parsed);
      } catch (error) {
        console.error('❌ Invalid JSON from server:', event.data);
      }
    };
    socket.onclose = () => {
      console.log('❌ WebSocket connection closed');
      wsRef.current = null;
    };
    wsRef.current = socket;
  };

  const showPlayCardAnimation = (action: Record<string, any>, hands: any) =>{
    const lst_act = action;
          if (lst_act.action_type === 'PLAY' ||
            lst_act.action_type === 'DISCARD') {
            console.log("is play")
            // Trigger play/discard animation.
            // We assume that for play/discard, the action includes card_index.
            const animation = {
                type: lst_act.action_type.toLowerCase() as 'play' | 'discard',
                player_id: self_player_id,
                cardIndex: lst_act.card_index!
              };
            console.log(animation);
            setAnimation(animation);
            // Hold the cached info during the animation (1s move + 2s hold = 3s)
            setTimeout(() => {
              setAnimation(null);
              console.log("animation for play ended!");
            }, 1500);
          } else if (lst_act.action_type === 'REVEAL_COLOR' ||
                     lst_act.action_type === 'REVEAL_RANK') {
            // For hint actions, determine the hint details.
            const hintType = lst_act.action_type === 'REVEAL_COLOR' ? 'color' : 'rank';
            let value: string;
            if (hintType === 'color') {
              value = lst_act.color;
            } else {
              // action.rank is 0-based; convert to 1-based string.
              value = ((lst_act.rank ?? 0) + 1).toString();
            }
            // We need to look at the new observation to know about corresponding cards.
            const target_player_id = 1-self_player_id;
            let target_index=[-1];
            if(self_player_id!==target_player_id){
                console.log("others hands", hands)
                for (const { index, card } of hands) {
                    if(hintType==='color' && card.charAt(0)===value){
                        target_index.push(index)
                    }else if(hintType==='rank' && card.charAt(1)===value){
                        target_index.push(index)
                    }
                }
            }

            const animation = {
                type: 'hint',
                player_id: target_player_id,
                hint: { type: hintType, idx: target_index, value: value}
              };
            console.log(animation);
            setAnimation(animation);
            
            // Hold the cached info during the hint animation (3 seconds)
            setTimeout(() => {
              setAnimation(null);
              console.log("animation for hint ended!");
            }, 1500);
          }

  };

  // Callback to send a selected action via the WebSocket
  const handleSelectAction = (actionKey: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      console.log('✅ Sent selected action:', actionKey, observation.actions[actionKey]);
      showPlayCardAnimation(observation.actions[actionKey], observation.info.hands.others);
      setTimeout(() => {
        wsRef.current.send(JSON.stringify({ action: actionKey }));
      }, 2500);
    } else {
      console.log('❌ WebSocket not connected');
    }
  };

  return (
    <div>
      <h2>Table Component</h2>
      <button onClick={handleInitialize}>Initialize Connection</button>
      <div style={{ marginTop: '1rem' }}>
        <h3>Observation</h3>
        <pre>{JSON.stringify(observation, null, 2)}</pre>
      </div>
      {/* Display FireWorksComponent if fireworks data exists */}
      {parsedState && parsedState.fireworks && (
        <FireWorksComponent fireworks={parsedState.fireworks} />
      )}
      {/* Display DiscardsComponent if discards exist */}
      {observation && observation.info && observation.info.discards && (
        <DiscardsComponent discards={observation.info.discards} />
      )}
      {/* Display own hand */}
      {observation && observation.info && observation.info.hands && observation.info.hands.cur_player && (
        <HandComponent
          cards={observation.info.hands.cur_player}
          isOwn={true}
          actions={observation.actions}
          onSelectAction={handleSelectAction}
          // Pass animation only if the acting player is self (assume self id = 0)
          animation={animation && animation.player_id === self_player_id ? animation : null}
        />
      )}
      {/* Display opponent's hand */}
      {observation && observation.info && observation.info.hands && observation.info.hands.others && (
        <HandComponent
          cards={observation.info.hands.others}
          isOwn={false}
          actions={observation.actions}
          onSelectAction={handleSelectAction}
          // Pass animation for opponent if player_id is not 0.
          animation={animation && animation.player_id !== self_player_id ? animation : null}
        />
      )}
      {/* Display info */}
      {observation && observation.info && (
        <InfoComponent
          lifeTokens={observation.info.life_tokens}
          infoTokens={observation.info.info_tokens}
        />
      )}
    </div>
  );
};

export default TableComponent;
