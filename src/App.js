import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

// Komponentit
import Home from './components/Home';
import AnalysisList from './components/AnalysisList';
import AnalysisDetail from './components/AnalysisDetail';
import AnalysisForm from './components/AnalysisForm';
import Login from './components/Login';
import Register from './components/Register';

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Tarkista käyttäjän kirjautumistiedot
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Kutsu API-endpointia joka palauttaa kirjautuneen käyttäjän tiedot
        const response = await axios.get('/api/user');
        setUser(response.data.user);
      } catch (error) {
        // Jos käyttäjä ei ole kirjautunut, ohjataan kirjautumissivulle
        console.error('Käyttäjä ei ole kirjautunut tai tapahtui virhe:', error);
        setUser(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  // Uloskirjautuminen
  const handleLogout = async () => {
    try {
      await axios.post('/auth/logout');
      setUser(null);
      navigate('/login');
    } catch (error) {
      console.error('Uloskirjautumisessa tapahtui virhe:', error);
    }
  };

  if (loading) {
    return <div className="loading-spinner">Ladataan...</div>;
  }

  return (
    <div className="app-container">
      <nav className="navbar navbar-expand-lg navbar-dark bg-primary">
        <div className="container">
          <Link className="navbar-brand" to="/">AsuntoAnalyysi</Link>
          <button className="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarNav">
            <ul className="navbar-nav me-auto">
              {user && (
                <>
                  <li className="nav-item">
                    <Link className="nav-link" to="/">Etusivu</Link>
                  </li>
                  <li className="nav-item">
                    <Link className="nav-link" to="/analyses">Analyysit</Link>
                  </li>
                </>
              )}
            </ul>
            <ul className="navbar-nav">
              {user ? (
                <>
                  <li className="nav-item">
                    <span className="nav-link">Hei, {user.name || user.email}</span>
                  </li>
                  <li className="nav-item">
                    <button className="btn btn-light" onClick={handleLogout}>Kirjaudu ulos</button>
                  </li>
                </>
              ) : (
                <>
                  <li className="nav-item">
                    <Link className="nav-link" to="/login">Kirjaudu</Link>
                  </li>
                  <li className="nav-item">
                    <Link className="nav-link" to="/register">Rekisteröidy</Link>
                  </li>
                </>
              )}
            </ul>
          </div>
        </div>
      </nav>

      <div className="container mt-4">
        <Routes>
          <Route path="/" element={user ? <Home user={user} /> : <Login onLogin={(userData) => setUser(userData)} />} />
          <Route path="/analyses" element={user ? <AnalysisList /> : <Login onLogin={(userData) => setUser(userData)} />} />
          <Route path="/analysis/:id" element={user ? <AnalysisDetail /> : <Login onLogin={(userData) => setUser(userData)} />} />
          <Route path="/analyze" element={user ? <AnalysisForm /> : <Login onLogin={(userData) => setUser(userData)} />} />
          <Route path="/login" element={<Login onLogin={(userData) => setUser(userData)} />} />
          <Route path="/register" element={<Register onRegister={(userData) => setUser(userData)} />} />
        </Routes>
      </div>

      <footer className="py-3 bg-light mt-auto">
        <div className="container text-center">
          <p className="mb-0">© {new Date().getFullYear()} AsuntoAnalyysi</p>
        </div>
      </footer>
    </div>
  );
}

export default App; 