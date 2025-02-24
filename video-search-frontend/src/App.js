import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [searchText, setSearchText] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [image, setImage] = useState(null);

  const handleSearch = async () => {
    try {
      setSearchResults([]);
      const response = await fetch(`/search_by_text/?text=${searchText}`);
      const data = await response.json();
      console.log(data)
      setSearchResults(data);
    } catch (error) {
      console.error("Error searching:", error);
    }
  };

  const handleImageSearch = async () => {
    try {
      setSearchResults([]);
      const formData = new FormData();
      formData.append('file', image); // Append the selected image

      const response = await fetch('/search_by_image', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      setSearchResults(data);

    } catch (error) {
      console.error("Error searching by image:", error);
    }
  }


  const handleImageChange = (e) => {
    setImage(e.target.files[0]);
  }

  return (
    
    <div className="App">
      <h1>Video Search</h1>
      <input
        type="text"
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        placeholder="Enter search text"
      />
      <button onClick={handleSearch}>Search by Text</button>

      <input 
        type="file"
        accept="image/*"
        onChange={handleImageChange}
      />
      <button onClick={handleImageSearch}>Search by Image</button>

      <h2>Search Results</h2>
      <div className="video-grid">
        {
        searchResults.map((result, index) => { // Added index for unique keys

          return (
            <div key={index} className="video-item"> {/* Use index as key */}
              <video
                controls width="320" height="240"
              >
                {/* <source src={result.metadata.publicUrl} type="video/mp4" /> */}
                <source src={result.publicUrl+"#t="+(result.startOffsetSec+2)} type="video/mp4" />

                  Your browser does not support the video tag.
              </video>

              <p>Start: {result.startOffsetSec} End: {result.endOffsetSec} Score: {result.score.toFixed(2)}</p> 
              <p>{result.publicUrl.split('/').pop()}</p>
              {/* ... (rest of your video item display) */}
            </div>
          );
          
        })}
      </div>


    </div>
  );
}


export default App;
