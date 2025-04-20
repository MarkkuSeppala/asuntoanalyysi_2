import axios from 'axios';

// Luodaan Axios-instanssi, joka käsittelee JWT-tokenin automaattisesti
const api = axios.create({
  baseURL: '/auth',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
});

/**
 * Kirjaa käyttäjän sisään
 * @param {string} username - Käyttäjänimi
 * @param {string} password - Salasana
 * @returns {Promise<Object>} - Kirjautuneen käyttäjän tiedot
 */
export const login = async (username, password) => {
  try {
    const response = await api.post('/login', { username, password });
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

/**
 * Kirjaa käyttäjän ulos
 * @returns {Promise<void>}
 */
export const logout = async () => {
  try {
    await api.post('/logout');
  } catch (error) {
    throw handleError(error);
  }
};

/**
 * Rekisteröi uuden käyttäjän
 * @param {Object} userData - Käyttäjän rekisteröintitiedot
 * @returns {Promise<Object>} - Rekisteröidyn käyttäjän tiedot
 */
export const register = async (userData) => {
  try {
    const response = await api.post('/register', userData);
    return response.data;
  } catch (error) {
    throw handleError(error);
  }
};

/**
 * Hakee kirjautuneen käyttäjän tiedot
 * @returns {Promise<Object>} - Kirjautuneen käyttäjän tiedot
 */
export const getCurrentUser = async () => {
  try {
    const response = await api.get('/current-user');
    return response.data;
  } catch (error) {
    // Jos 401, käyttäjä ei ole kirjautunut
    if (error.response && error.response.status === 401) {
      return null;
    }
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