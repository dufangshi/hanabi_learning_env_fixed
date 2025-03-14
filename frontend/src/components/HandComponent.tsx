// src/components/HandComponent.tsx
import React, { useState } from 'react';
import '../styles/HandComponent.css';

// Define the union type for animations.
export type AnimationType =
  | { type: 'play' | 'discard'; player_id: number; cardIndex: number }
  | { type: 'hint'; player_id: number; hint: { type: 'color' | 'rank'; value: string } };

interface Card {
  index: number;
  card: string;  // For own hand: always "XX"; for opponent's hand: e.g. "W2"
  info: string;  // e.g. "X1", "YX", "XX", etc.
  col: string[]; // Possible colors, e.g. ["R", "Y", "G", "W", "B"]
  rank: string[]; // Possible ranks, e.g. ["1"] or ["2", "3", "4", "5"]
}

interface Action {
  action_type: string;
  card_index?: number;
  target_offset?: number;
  color?: string;
  rank?: number;
}

interface HandComponentProps {
  cards: Card[];
  isOwn: boolean;
  actions: { [key: string]: Action };
  onSelectAction: (actionKey: string) => void;
  animation?: AnimationType | null;
}

// Mapping from letter to color name
const letterToCol: { [key: string]: string } = {
  R: 'red',
  Y: 'yellow',
  G: 'green',
  W: 'white',
  B: 'blue'
};

// Base style for each card block
const cardStyleBase: React.CSSProperties = {
  width: '60px',
  height: '90px',
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  border: '2px solid black',
  borderRadius: '5px',
  position: 'relative',
  cursor: 'pointer',
  margin: '5px'
};

// Tooltip style shown on hover
const tooltipStyle: React.CSSProperties = {
  position: 'absolute',
  top: '-85px',
  left: '50%',
  transform: 'translateX(-50%)',
  background: 'rgba(0, 0, 0, 0.8)',
  color: 'white',
  padding: '5px',
  borderRadius: '5px',
  whiteSpace: 'nowrap',
  zIndex: 10
};

// Small color block style for showing possible colors in the tooltip
const smallBlockStyle = (color: string): React.CSSProperties => ({
  width: '20px',
  height: '20px',
  backgroundColor: letterToCol[color] || 'gray',
  display: 'inline-block',
  margin: '0 2px'
});

// Container style for hand cards, arranged horizontally. Position depends on isOwn.
const getCardContainerStyle = (isOwn: boolean): React.CSSProperties => ({
  display: 'flex',
  flexDirection: 'row',
  position: 'fixed',
  bottom: isOwn ? '100px' : undefined,
  top: !isOwn ? '120px' : undefined,
  right: '50%',
  gap: '10px',
  margin: '10px'
});

// Return available action keys for a given card.
const getAvailableActionKeys = (
  card: Card,
  isOwn: boolean,
  actions: { [key: string]: Action }
): { playKey?: string; discardKey?: string; revealColorKey?: string; revealRankKey?: string } => {
  let available: { playKey?: string; discardKey?: string; revealColorKey?: string; revealRankKey?: string } = {};

  if (isOwn) {
    // For own hand, match PLAY and DISCARD by card_index.
    Object.entries(actions).forEach(([key, action]) => {
      if (action.action_type === 'PLAY' && action.card_index === card.index) {
        available.playKey = key;
      }
      if (action.action_type === 'DISCARD' && action.card_index === card.index) {
        available.discardKey = key;
      }
    });
  } else {
    // For opponent's hand, match REVEAL_COLOR and REVEAL_RANK.
    const cardVal = card.card; // e.g. "W2"
    const cardColor = cardVal.charAt(0);
    const cardRank = cardVal.charAt(1);
    Object.entries(actions).forEach(([key, action]) => {
      if (action.action_type === 'REVEAL_COLOR' && action.color === cardColor) {
        available.revealColorKey = key;
      }
      if (
        action.action_type === 'REVEAL_RANK' &&
        action.rank !== undefined &&
        (action.rank + 1).toString() === cardRank
      ) {
        available.revealRankKey = key;
      }
    });
  }
  return available;
};

interface Highlight {
  type: 'color' | 'rank';
  value: string;
}

const HandComponent: React.FC<HandComponentProps> = ({
  cards,
  isOwn,
  actions,
  onSelectAction,
  animation
}) => {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const [selectedCardIndex, setSelectedCardIndex] = useState<number | null>(null);
  const [highlight, setHighlight] = useState<Highlight | null>(null);

  const handleCardClick = (cardIndex: number) => {
    setSelectedCardIndex(prev => (prev === cardIndex ? null : cardIndex));
  };

  if(animation){
    console.log("hand animation", animation)
  }

  return (
    <div style={getCardContainerStyle(isOwn)}>
      {cards.map((card, index) => {
        let bgColor = 'gray';
        let displayText = '';
        if (isOwn) {
          if (card.info.charAt(0) !== 'X') {
            bgColor = letterToCol[card.info.charAt(0)] || 'gray';
          }
          displayText = card.info;
        } else {
          const cardVal = card.card;
          bgColor = letterToCol[cardVal.charAt(0)] || 'gray';
          displayText = cardVal;
        }

        const cardStyle = {
          ...cardStyleBase,
          backgroundColor: bgColor,
          color: (bgColor === 'white' || bgColor === 'yellow') ? 'black' : 'white'
        };

        // Determine if this card should be highlighted (from button hover in opponent's hand)
        const isHighlighted = !isOwn && highlight && (
          (highlight.type === 'color' && card.card.charAt(0) === highlight.value) ||
          (highlight.type === 'rank' && card.card.charAt(1) === highlight.value)
        );

        // Animation styles
        let animatedStyle: React.CSSProperties = {};

        let extraHintElement: JSX.Element | null = null;

        if (animation) {
        if (animation.type === 'play' || animation.type === 'discard') {
            if (card.index === animation.cardIndex) {
            animatedStyle = {
                transition: 'transform 1.5s ease',
                transform: animation.type === 'discard'
                ? 'translate(40vw, 0vh)'
                : (isOwn ? 'translate(0vw, -40vh)' : 'translate(0vw, 40vh)'),
                zIndex: 1000
            };
            }
        }
        
        if (animation.type === 'hint' && animation.hint.idx.includes(index)) {
            // Flashing
            if (animation.hint.type === 'color') {
            const hintColor = letterToCol[animation.hint.value] || 'green';
            animatedStyle = {
                ...animatedStyle,
                outline: `3px solid ${hintColor}`,
                animation: 'blinker 1s linear infinite',
                backgroundColor: hintColor, // 设置卡牌背景色为hint颜色
            };
            }
            if (animation.hint.type === 'rank') {
            animatedStyle = {
                ...animatedStyle,
                outline: '3px solid red',
                animation: 'blinker 1s linear infinite'
            };
            // Show number hint
            extraHintElement = (
                <div style={{
                position: 'absolute',
                top: '10px',
                left: '50%',
                transform: 'translateX(-50%)',
                color: 'gold',
                fontSize: '24px',
                fontWeight: 'bold',
                pointerEvents: 'none'
                }}>
                {animation.hint.value}
                </div>
            );
            }
        }
        }

        const finalCardStyle = {
          ...cardStyle,
          ...animatedStyle,
          ...(isHighlighted ? { outline: '3px solid orange' } : {})
        };

        // Get available action keys for this card.
        const availableActions = getAvailableActionKeys(card, isOwn, actions);

        return (
          <div
            key={card.index}
            style={finalCardStyle}
            onMouseEnter={() => setHoverIndex(index)}
            onMouseLeave={() => setHoverIndex(null)}
            onClick={() => handleCardClick(card.index)}
          >
            {displayText}
            {hoverIndex === index && (
              <div style={tooltipStyle}>
                <div>
                  Possible Colors:{' '}
                  {card.col.map((c, i) => (
                    <span key={i} style={smallBlockStyle(c)}></span>
                  ))}
                </div>
                <div>
                  Possible Ranks:{' '}
                  {card.rank.map((r, i) => (
                    <span key={i} style={{ margin: '0 3px' }}>{r}</span>
                  ))}
                </div>
              </div>
            )}
            {selectedCardIndex === card.index && (
              <div
                style={{ position: 'absolute', bottom: '-25px', left: '50%', transform: 'translateX(-50%)' }}
                onMouseLeave={() => { setSelectedCardIndex(null); setHighlight(null); }}
              >
                {isOwn ? (
                  <>
                    {availableActions.playKey && (
                      <button
                        className="hand-action-button"
                        onClick={() => {
                          onSelectAction(availableActions.playKey!);
                          setSelectedCardIndex(null);
                          setHighlight(null);
                        }}
                      >
                        Play
                      </button>
                    )}
                    {availableActions.discardKey && (
                      <button
                        className="hand-action-button"
                        onClick={() => {
                          onSelectAction(availableActions.discardKey!);
                          setSelectedCardIndex(null);
                          setHighlight(null);
                        }}
                      >
                        Discard
                      </button>
                    )}
                  </>
                ) : (
                  <>
                    {availableActions.revealColorKey && !animation && (
                      <button
                        className="hand-action-button"
                        onMouseEnter={() =>
                          setHighlight({ type: 'color', value: actions[availableActions.revealColorKey].color! })
                        }
                        onMouseLeave={() => setHighlight(null)}
                        onClick={() => {
                          onSelectAction(availableActions.revealColorKey!);
                          setSelectedCardIndex(null);
                          setHighlight(null);
                        }}
                      >
                        Color
                      </button>
                    )}
                    {availableActions.revealRankKey && !animation && (
                      <button
                        className="hand-action-button"
                        onMouseEnter={() =>
                          setHighlight({
                            type: 'rank',
                            value: ((actions[availableActions.revealRankKey].rank ?? 0) + 1).toString()
                          })
                        }
                        onMouseLeave={() => setHighlight(null)}
                        onClick={() => {
                          onSelectAction(availableActions.revealRankKey!);
                          setSelectedCardIndex(null);
                          setHighlight(null);
                        }}
                      >
                        Rank
                      </button>
                    )}
                  </>
                )}
              </div>
            )}
            {extraHintElement}
          </div>
          
        );
      })}
    </div>
  );
};

export default HandComponent;
