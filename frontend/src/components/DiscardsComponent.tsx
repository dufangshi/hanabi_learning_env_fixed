// src/components/DiscardsComponent.tsx
import React from 'react';

// Mapping from letter to color name
const letterToCol: { [key: string]: string } = {
  R: 'red',
  Y: 'yellow',
  G: 'green',
  W: 'white',
  B: 'blue'
};

interface DiscardsComponentProps {
  discards: string[];
}

// Utility function to chunk an array into groups of given size
const chunkArray = <T,>(arr: T[], chunkSize: number): T[][] => {
  const result: T[][] = [];
  for (let i = 0; i < arr.length; i += chunkSize) {
    result.push(arr.slice(i, i + chunkSize));
  }
  return result;
};

const DiscardsComponent: React.FC<DiscardsComponentProps> = ({ discards }) => {
  // Group cards by their color letter (first character of the card string)
  const grouped: { [color: string]: string[] } = {};
  discards.forEach((card) => {
    const letter = card.charAt(0); // e.g. 'B' from "B3"
    if (!grouped[letter]) {
      grouped[letter] = [];
    }
    grouped[letter].push(card);
  });

  // Sort each color group by rank in ascending order
  Object.keys(grouped).forEach((letter) => {
    grouped[letter].sort((a, b) => parseInt(a[1], 10) - parseInt(b[1], 10));
  });

  // For each color group, chunk the sorted cards into rows of at most 3 cards
  const rows: { color: string; cardRows: string[][] }[] = [];
  Object.keys(grouped).forEach((letter) => {
    const cardRows = chunkArray(grouped[letter], 3);
    rows.push({ color: letter, cardRows });
  });

  // Container style for the component, positioned on the right side above FireWorksComponent
  const containerStyle: React.CSSProperties = {
    position: 'fixed',
    right: '20px',
    bottom: '250px', // adjust so it sits above FireWorksComponent
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    padding: '10px',
    borderRadius: '5px'
  };

  // Style for each card block
  const cardStyle = (color: string): React.CSSProperties => ({
    width: '24px',
    height: '36px',
    backgroundColor: letterToCol[color] || 'gray',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    color: color === 'W' || color === 'Y' ? 'black' : 'white', // use black text on white background
    fontWeight: 'bold',
    margin: '5px',
    border: '2px solid black', 
    borderRadius: '5px', 
    boxShadow: '2px 2px 5px rgba(0, 0, 0, 0.3)'
  });

  return (
    <div style={containerStyle}>
      {rows.map((group, groupIndex) => (
        <div key={groupIndex} style={{ marginBottom: '10px' }}>
          <div style={{ marginBottom: '5px', fontWeight: 'bold' }}>
            {letterToCol[group.color]} Discards
          </div>
          {group.cardRows.map((row, rowIndex) => (
            <div key={rowIndex} style={{ display: 'flex', flexDirection: 'row' }}>
              {row.map((card, cardIndex) => {
                // The card string is two characters (e.g. "B3"), where the second char is the rank
                const rank = card.charAt(1);
                return (
                  <div key={cardIndex} style={cardStyle(group.color)}>
                    {rank}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

export default DiscardsComponent;
