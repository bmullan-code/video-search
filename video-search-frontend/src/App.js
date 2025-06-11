import React, { useState, useRef, useEffect } from 'react';
import './App.css';
import { searchByText, searchByImage } from './services/api'; // Import API service

function App() {
  const [searchText, setSearchText] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [image, setImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false); // Loading state
  const [error, setError] = useState(null); // Error state

  const handleSearch = async () => {
    if (!searchText.trim()) {
      setError("Please enter search text.");
      return;
    }
    setSearchResults([]); // Clear previous results
    setError(null); // Clear previous errors
    setIsLoading(true); // Set loading state
    try {
      // const response = await fetch(`/search_by_text/?text=${searchText}`); // Old
      // const data = await response.json(); // Old
      const data = await searchByText(searchText); // Use API service
      console.log(data);
      setSearchResults(data);
    } catch (err) { // Changed error to err to avoid conflict with state variable
      console.error("Error searching:", err);
      setError(err.message || "Failed to search by text. Please try again.");
    } finally {
      setIsLoading(false); // Reset loading state
    }
  };

  const handleImageSearch = async () => {
    if (!image) {
      setError("Please select an image file.");
      return;
    }
    setSearchResults([]); // Clear previous results
    setError(null); // Clear previous errors
    setIsLoading(true); // Set loading state
    try {
      // const formData = new FormData(); // Old
      // formData.append('file', image); // Append the selected image // Old

      // const response = await fetch('/search_by_image', { // Old
      //   method: 'POST', // Old
      //   body: formData, // Old
      // }); // Old

      // const data = await response.json(); // Old
      const data = await searchByImage(image); // Use API service
      setSearchResults(data);
    } catch (err) { // Changed error to err to avoid conflict with state variable
      console.error("Error searching by image:", err);
      setError(err.message || "Failed to search by image. Please try again.");
    } finally {
      setIsLoading(false); // Reset loading state
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

      {/* Status Messages Area */}
      <div className="status-messages">
        {isLoading && <p>Loading...</p>}
        {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      </div>

      <div className="video-grid">
        {searchResults && searchResults.length > 0 ? (
          searchResults.map((result, index) => (
            // Use result.id if available, otherwise fallback to index (though id should be there)
            <div key={result.id || `video-${index}`} className="video-item">
              <video
                controls width="320" height="240"
                // key forces re-render if src changes, useful for some browsers
                key={result.publicUrl + (result.startOffsetSec || '')}
              >
                <source src={`${result.publicUrl}#t=${result.startOffsetSec || 0},${result.endOffsetSec || ''}`} type="video/mp4" />
                Your browser does not support the video tag.
              </video>
              <p>
                File: {result.metadata && result.metadata.fileName ? result.metadata.fileName : (result.publicUrl || '').split('/').pop()}
              </p>
              <p>
                Segment: {result.startOffsetSec}s - {result.endOffsetSec}s
              </p>
              <p>Score: {result.score ? result.score.toFixed(2) : 'N/A'}</p>
              {/* <p>ID: {result.id}</p> */}
            </div>
          ))
        ) : (
          !isLoading && <p>No results found. Try a different search!</p> // Show only if not loading
        )}
      </div>
    </div>
  );
}


export default App;
