// src/components/InfoComponent.tsx
import React from 'react';

interface InfoComponentProps {
  lifeTokens: number; // Maximum 3; 0 means game over.
  infoTokens: number; // Maximum 8.
}

const InfoComponent: React.FC<InfoComponentProps> = ({ lifeTokens, infoTokens }) => {
  const maxLife = 3;
  const maxInfo = 8;

  // Heart style: filled hearts are red, lost hearts are transparent with red outline.
  const heartStyle = (filled: boolean): React.CSSProperties => ({
    fontSize: '24px',
    color: filled ? 'red' : 'transparent',
    WebkitTextStroke: filled ? 'none' : '1px red',
    marginRight: '5px'
  });

  // Coin style: available coins are blue, used ones are gray.
  const coinStyle = (available: boolean): React.CSSProperties => ({
    width: '20px',
    height: '20px',
    borderRadius: '50%',
    backgroundColor: available ? 'blue' : 'gray',
    marginRight: '3px',
    display: 'inline-block'
  });

  // Container style: positioned at the bottom right,
  // and (as required) should be placed to the left of the FireWorksComponent.
  const containerStyle: React.CSSProperties = {
    position: 'fixed',
    bottom: '20px',
    right: '300px',
    backgroundColor: 'rgba(255,255,255,0.8)',
    padding: '10px',
    borderRadius: '5px',
    border: '2px solid black',
    zIndex: 1000,
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center'
  };

  return (
    <div style={containerStyle}>
      <div>
        {Array.from({ length: maxLife }, (_, i) => (
          <span key={i} style={heartStyle(i < lifeTokens)}>
            ♥
          </span>
        ))}
      </div>
      <div style={{ marginTop: '10px' }}>
        {Array.from({ length: maxInfo }, (_, i) => (
          <span key={i} style={coinStyle(i < infoTokens)}></span>
        ))}
      </div>
    </div>
  );
};

export default InfoComponent;
