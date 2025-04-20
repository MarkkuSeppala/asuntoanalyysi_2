import axios from 'axios';

// Luodaan Axios-instanssi API-kutsuja varten
const api = axios.create({
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

/**
 * Luo uuden analyysin asunto-URL:n perusteella
 * @param {string} propertyUrl - Analysoitavan asunnon URL
 * @returns {Promise<Object>} - Analyysin tiedot ja tulos
 */
export const createAnalysis = async (propertyUrl) => {
  try {
    const response = await api.post('/api/analyze', { url: propertyUrl });
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

/**
 * Hakee kaikki käyttäjän analyysit
 * @returns {Promise<Array>} - Lista käyttäjän analyyseistä
 */
export const getUserAnalyses = async () => {
  try {
    const response = await api.get('/analyses');
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

/**
 * Hakee yksittäisen analyysin tiedot
 * @param {number} analysisId - Analyysin ID
 * @returns {Promise<Object>} - Analyysin tiedot
 */
export const getAnalysisById = async (analysisId) => {
  try {
    const response = await api.get(`/analysis/${analysisId}`);
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

/**
 * Lataa analyysin tekstitiedostona
 * @param {number} analysisId - Analyysin ID
 * @returns {Promise<Blob>} - Tiedoston sisältö Blobina
 */
export const downloadAnalysis = async (analysisId) => {
  try {
    const response = await api.get(`/analysis/raw/${analysisId}`, {
      responseType: 'blob',
    });
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

/**
 * Poistaa analyysin
 * @param {number} analysisId - Poistettavan analyysin ID
 * @returns {Promise<void>}
 */
export const deleteAnalysis = async (analysisId) => {
  try {
    await api.delete(`/analysis/${analysisId}`);
  } catch (error) {
    throw handleError(error);
  }
};

/**
 * Virheenkäsittelijä API-kutsuille
 * @param {Error} error - Axios-virhe
 * @returns {Error} - Käsitelty virhe
 */
const handleError = (error) => {
  if (error.response) {
    // Palvelin vastasi virheellä
    const { data, status } = error.response;
    const errorMessage = data.error || 'Palvelinvirhe';
    
    // Luo mukautettu virhe viestillä
    const customError = new Error(errorMessage);
    customError.status = status;
    
    return customError;
  }
  
  if (error.request) {
    // Pyyntö tehtiin mutta ei saatu vastausta
    return new Error('Palvelimeen ei saatu yhteyttä. Tarkista verkkoyhteytesi.');
  }
  
  // Virhe tapahtui pyynnön luonnissa
  return new Error('Virhe pyynnön tekemisessä. Yritä uudelleen.');
}; 