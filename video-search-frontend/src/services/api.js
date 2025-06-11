// Simple API service module

// Define the base URL for the API.
// In a real application, this might come from an environment variable.
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

/**
 * Performs a text search by calling the backend API.
 * @param {string} searchText The text to search for.
 * @returns {Promise<Array<Object>>} A promise that resolves to an array of search results.
 * @throws {Error} If the network response is not ok.
 */
export const searchByText = async (searchText) => {
    const url = `${API_BASE_URL}/search_by_text/?text=${encodeURIComponent(searchText)}`;

    const response = await fetch(url);

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
        throw new Error(errorData.detail || `Network response was not ok (${response.status})`);
    }

    return response.json();
};

/**
 * Performs an image search by calling the backend API.
 * @param {File} imageFile The image file to search with.
 * @returns {Promise<Array<Object>>} A promise that resolves to an array of search results.
 * @throws {Error} If the network response is not ok.
 */
export const searchByImage = async (imageFile) => {
    const url = `${API_BASE_URL}/search_by_image/`;
    const formData = new FormData();
    formData.append('file', imageFile); // The backend expects the file under the key 'file'

    const response = await fetch(url, {
        method: 'POST',
        body: formData,
        // Note: 'Content-Type': 'multipart/form-data' is automatically set by the browser
        // when using FormData with fetch, so it's usually not needed to set it manually.
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error occurred' }));
        // errorData.detail might contain the specific message from HTTPException in FastAPI
        throw new Error(errorData.detail || `Network response was not ok (${response.status})`);
    }

    return response.json();
};
