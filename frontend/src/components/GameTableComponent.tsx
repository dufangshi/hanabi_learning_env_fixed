import React, { useState, useEffect } from 'react';
import FireWorksComponent from './FireWorksComponent';
import DiscardsComponent from './DiscardsComponent';
import HandComponent from './HandComponent';
import InfoComponent from './InfoComponent';

type AnimationType = 
  | { type: 'play' | 'discard'; player_id: number; cardIndex: number }
  | { type: 'hint'; player_id: number; hint: { type: 'color' | 'rank'; idx?: number[]; value: string } };

type GameTableProps = {
  observation: any;
  parsedState: any;
  wsRef: React.MutableRefObject<WebSocket | null>;
  waitingMessage: string;
  onAnimationComplete: () => void;
};

const GameTableComponent: React.FC<GameTableProps> = ({ observation, parsedState, wsRef, waitingMessage }) => {
  const [lastObservation, setLastObservation] = useState<any>(null);
  const [currObservation, setCurrObservation] = useState<any>(null);
  const [animation, setAnimation] = useState<AnimationType | null>(null);
  const [showObservation, setShowObservation] = useState(false);
  // Assume the local player id is provided in observation (e.g. observation.player_id)
  const self_player_id = observation['player_id'];

  useEffect(() => {
    if(observation !== currObservation){
        setCurrObservation(observation);
        setLastObservation(currObservation);
    }
    // if (observation && observation.last_action) {
    //     triggerAnimation();
    // }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [observation]);

  // Function to trigger an animation based on the observation's last_action.
  // The waitingMessage is used to determine whether the last_action was from the opponent.
  useEffect(() => {
    if (currObservation && currObservation.last_action) {
      const lastAct = currObservation.last_action.action;
      if (lastAct) {
        const isOpponentAction = waitingMessage.includes("Your");
        let anim: AnimationType | null = null;
        if (lastAct.action_type === 'PLAY' || lastAct.action_type === 'DISCARD') {
          anim = {
            type: lastAct.action_type.toLowerCase() as 'play' | 'discard',
            // If opponent action, assign animation to opponent's hand; otherwise, local hand.
            player_id: isOpponentAction ? (1 - self_player_id) : self_player_id,
            cardIndex: lastAct.card_index
          };
        } else if (lastAct.action_type === 'REVEAL_COLOR' || lastAct.action_type === 'REVEAL_RANK') {
          const hintType = lastAct.action_type === 'REVEAL_COLOR' ? 'color' : 'rank';
          let value: string;
          if (hintType === 'color') {
            value = lastAct.color;
          } else {
            value = ((lastAct.rank ?? 0) + 1).toString();
          }
          // Determine target player's id for hint based on waitingMessage.
          const target_player_id = isOpponentAction ? self_player_id : (1 - self_player_id);
          let target_index: number[] = [-1];
          if (self_player_id !== target_player_id) {
            // Loop through opponent's hand to identify matching cards.
            for (const { index, card } of currObservation.info.hands.others) {
              if (hintType === 'color' && card.charAt(0) === value) {
                target_index.push(index);
              } else if (hintType === 'rank' && card.charAt(1) === value) {
                target_index.push(index);
              }
            }
          }else{
            console.log("constructing self hinted")
            for (const { index, info } of currObservation.info.hands.cur_player) {
                if (hintType === 'color' && info.charAt(0) === value) {
                  target_index.push(index);
                } else if (hintType === 'rank' && info.charAt(1) === value) {
                  target_index.push(index);
                }
              }
          }
          anim = {
            type: 'hint',
            player_id: target_player_id,
            hint: { type: hintType, idx: target_index, value: value }
          };
        }
        if (anim) {
          setAnimation(anim);
          console.log("animation setted", anim)
          // Block new observation extraction while animation plays.
          setTimeout(() => {
            setAnimation(null);
            console.log("Animation ended, proceeding to next observation.");
          }, 1500);
        } else {
        }
      } else {
      }
    } else {
      // No last_action found; simply call onAnimationComplete.
    }
  }, [currObservation]);

  const showPlayCardAnimation = (action: any) => {
    const lastAct = action;
    let anim: AnimationType | null = null;
    if (lastAct.action_type === 'PLAY' || lastAct.action_type === 'DISCARD') {
    anim = {
        type: lastAct.action_type.toLowerCase() as 'play' | 'discard',
        // If opponent action, assign animation to opponent's hand; otherwise, local hand.
        player_id: self_player_id,
        cardIndex: lastAct.card_index
    };
    } else if (lastAct.action_type === 'REVEAL_COLOR' || lastAct.action_type === 'REVEAL_RANK') {
    const hintType = lastAct.action_type === 'REVEAL_COLOR' ? 'color' : 'rank';
    let value: string;
    if (hintType === 'color') {
        value = lastAct.color;
    } else {
        value = ((lastAct.rank ?? 0) + 1).toString();
    }
    // Determine target player's id for hint based on waitingMessage.
    const target_player_id = (1 - self_player_id);
    let target_index: number[] = [-1];
    if (self_player_id !== target_player_id) {
        // Loop through opponent's hand to identify matching cards.
        for (const { index, card } of currObservation.info.hands.others) {
        if (hintType === 'color' && card.charAt(0) === value) {
            target_index.push(index);
        } else if (hintType === 'rank' && card.charAt(1) === value) {
            target_index.push(index);
        }
        }
    }else{
        console.log("constructing self hinted")
        for (const { index, info } of currObservation.info.hands.cur_player) {
            if (hintType === 'color' && info.charAt(0) === value) {
            target_index.push(index);
            } else if (hintType === 'rank' && info.charAt(1) === value) {
            target_index.push(index);
            }
        }
    }
    anim = {
        type: 'hint',
        player_id: target_player_id,
        hint: { type: hintType, idx: target_index, value: value }
    };
    }
    if (anim) {
    setAnimation(anim);
    console.log("animation setted", anim)
    // Block new observation extraction while animation plays.
    setTimeout(() => {
        setAnimation(null);
        console.log("Animation ended, proceeding to next observation.");
    }, 1500);
    }
  };


  // Disable onSelectAction when waitingMessage does not include "Your" (i.e. it's not your turn)
  const handleSelectAction = (actionKey: string) => {
    if (!waitingMessage.includes("Your")) {
      console.log("Not your turn to play. Action disabled.");
      return;
    }
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && currObservation) {
      console.log('✅ Sent selected action:', actionKey, currObservation.actions[actionKey]);
      showPlayCardAnimation(currObservation.actions[actionKey]);
      setTimeout(() => {
        wsRef.current!.send(JSON.stringify({ action: actionKey }));
      }, 2500);
    } else {
      console.log('❌ WebSocket not connected');
    }
  };

  return (
    <div>

{waitingMessage && (
  <div 
    style={{
      position: 'fixed',   // Fix position on screen
      top: '10px',         // Distance from top
      left: '50%',         // Center horizontally
      transform: 'translateX(-50%)', // Ensure it's centered properly
      padding: '0.5rem 1rem',
      backgroundColor: '#f0f0f0',
      borderRadius: '8px',
      fontSize: '1.2rem',
      fontWeight: 'bold',
      textAlign: 'center',
      boxShadow: '0px 4px 6px rgba(0, 0, 0, 0.1)',
      zIndex: 1000 // Ensure it stays above other elements
    }}
  >
    {waitingMessage}
  </div>
)}
        <div style={{ marginTop: '1rem' }}>
        <button 
        onClick={() => setShowObservation(!showObservation)} 
        style={{ marginBottom: '0.5rem' }}
        >
        {showObservation ? "Hide Debug Observation JSON" : "Show Debug Observation JSON"}
        </button>
        
        {showObservation && (
        <div>
            <h3>Observation</h3>
            <pre>{JSON.stringify(observation, null, 2)}</pre>
        </div>
        )}
        </div>
      {parsedState && parsedState.fireworks && (
        <FireWorksComponent fireworks={parsedState.fireworks} />
      )}
      {observation && observation.info && observation.info.discards && (
        <DiscardsComponent discards={observation.info.discards} />
      )}
      {observation && observation.info && observation.info.hands && observation.info.hands.cur_player && (
        <HandComponent
          cards={(!(animation && animation.player_id === self_player_id) || !lastObservation || animation.type === 'hint') ? observation.info.hands.cur_player : lastObservation.info.hands.cur_player}
          isOwn={true}
          actions={observation.actions}
          onSelectAction={handleSelectAction}
          animation={animation && animation.player_id === self_player_id ? animation : null}
        />
      )}
      {observation && observation.info && observation.info.hands && observation.info.hands.others && (
        <HandComponent
          cards={(!(animation && animation.player_id !== self_player_id) || !lastObservation || animation.type === 'hint') ? observation.info.hands.others : lastObservation.info.hands.others}
          isOwn={false}
          actions={observation.actions}
          onSelectAction={handleSelectAction}
          animation={animation && animation.player_id !== self_player_id ? animation : null}
        />
      )}
      {observation && observation.info && (
        <InfoComponent
          lifeTokens={observation.info.life_tokens}
          infoTokens={observation.info.info_tokens}
          deckSize={observation.info.deck_size}
        />
      )}
    </div>
  );
};

export default GameTableComponent;
