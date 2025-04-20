import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';

// Komponentit
import Header from './components/layout/Header';
import Footer from './components/layout/Footer';
import Sidebar from './components/layout/Sidebar';

// Sivut
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import AnalysisForm from './pages/AnalysisForm';
import AnalysisList from './pages/AnalysisList';
import AnalysisDetail from './pages/AnalysisDetail';
import NotFound from './pages/NotFound';

// Tyylitetyt komponentit
import styled from 'styled-components';

// API palvelu
import { getCurrentUser } from './services/authService';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
`;

const MainContent = styled.main`
  flex: 1;
  display: flex;
  margin-top: 80px; // Headerin korkeus
`;

const ContentWrapper = styled.div`
  flex: 1;
  padding: 2rem 0;
`;

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  
  useEffect(() => {
    const checkUser = async () => {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
      } catch (error) {
        setUser(null);
      } finally {
        setLoading(false);
      }
    };
    
    checkUser();
  }, []);
  
  // Näytetään latausruutu kun tarkistetaan kirjautumistilaa
  if (loading) {
    return <div>Ladataan...</div>;
  }
  
  // Reittitarkistus - kirjautumaton käyttäjä voi käydä vain kirjautumissivuilla
  const isAuthPage = location.pathname === '/login' || location.pathname === '/register';
  
  if (!user && !isAuthPage) {
    return <Navigate to="/login" />;
  }
  
  // Kirjautunut käyttäjä ei tarvitse kirjautumissivuja
  if (user && isAuthPage) {
    return <Navigate to="/dashboard" />;
  }

  return (
    <AppContainer>
      <Header user={user} setUser={setUser} />
      
      <MainContent>
        {user && <Sidebar />}
        
        <ContentWrapper>
          <div className="container">
            <Routes>
              {/* Julkiset sivut */}
              <Route path="/login" element={<Login setUser={setUser} />} />
              <Route path="/register" element={<Register />} />
              
              {/* Suojatut sivut */}
              <Route path="/" element={<Home />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/new-analysis" element={<AnalysisForm />} />
              <Route path="/analyses" element={<AnalysisList />} />
              <Route path="/analysis/:id" element={<AnalysisDetail />} />
              
              {/* 404 sivu */}
              <Route path="*" element={<NotFound />} />
            </Routes>
          </div>
        </ContentWrapper>
      </MainContent>
      
      <Footer />
    </AppContainer>
  );
}

export default App; 