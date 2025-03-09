// src/components/FireWorksComponent.tsx
import React from 'react';

// Define the type for the fireworks prop
interface FireWorksProps {
  fireworks: Record<string, number>;
}

const FireWorksComponent: React.FC<FireWorksProps> = ({ fireworks }) => {
  // Assume the maximum value for each color is 5
  const maxFirework = 5;
  const containerStyle = {
    display: 'flex',
    flexDirection: 'row',
    alignItems: 'flex-end',
    position: 'fixed',
    bottom: '20px',
    right: '20px',
    background: 'rgba(0.3,0.3,0.3,0.3)',
    padding: '10px',
    borderRadius: '5px',
    zIndex: 1000,
  };

  const letterToCol: Record<string, string> = {
    'R': 'red',
    'Y': 'yellow',
    'G': 'green',
    'W': 'white',
    'B': 'blue'
  }

  const barBaseStyle = {
    width: '20px',
    margin: '0 5px',
    background: '#ccc',
  };

  return (
    <div style={containerStyle}>
      {Object.keys(fireworks).map(color => {
        const progress = fireworks[color];
        // The height of the bar is proportional to the progress, with a maximum of 100px
        const barHeight = (progress / maxFirework) * 100;
        return (
          <div key={color} style={{ textAlign: 'center', margin: '0 5px' }}>
            <div>{progress}</div>
            <div
              style={{
                ...barBaseStyle,
                height: `${barHeight}px`,
                background: letterToCol[color].toLowerCase(), // Use color name as background color
              }}
            />
            <div>{color}</div>
          </div>
        );
      })}
    </div>
  );
};

export default FireWorksComponent;
