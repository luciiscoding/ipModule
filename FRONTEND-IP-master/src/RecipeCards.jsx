import React, { useState, useEffect } from 'react';
import Cards from './Cards.jsx';

function RecipeCards() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/v1/recipes/recipePage');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const json = await response.json();
setData(Array.isArray(json.content) ? json.content : [json.content]);
      } catch (error) {
        console.error('Error:', error);
      }
    };

    fetchData();
  }, []);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
     {data ? data.slice(1, 30).map((recipe) => <Cards key={recipe.recipeId} recipe={recipe} />) : <div>Loading...</div>}
    </div>
  );
}

export default RecipeCards;
//ok