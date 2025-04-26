import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

function Login({ onLogin }) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/auth/login', formData);
      if (response.data.status === 'success') {
        onLogin(response.data.user);
        navigate('/');
      } else {
        setError(response.data.message || 'Kirjautumisessa tapahtui virhe.');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'Virheelliset kirjautumistiedot.');
      console.error('Kirjautumisvirhe:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="container">
        <div className="row justify-content-center">
          <div className="col-md-10 col-lg-8">
            <div className="row">
              {/* Vasen puoli - Kirjautumislomake */}
              <div className="col-lg-6">
                <div className="login-card">
                  <div className="login-header">
                    <h2>Kirjaudu sisään</h2>
                    <p className="login-subtitle">Jatka asuntoanalyysityökalun käyttöä</p>
                  </div>
                  
                  {error && (
                    <div className="alert alert-custom" role="alert">
                      <i className="fas fa-exclamation-circle me-2"></i>
                      {error}
                    </div>
                  )}

                  <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-floating mb-4">
                      <input
                        type="email"
                        className="form-control custom-input"
                        id="email"
                        name="email"
                        placeholder="nimi@esimerkki.fi"
                        value={formData.email}
                        onChange={handleChange}
                        required
                      />
                      <label htmlFor="email">Sähköposti</label>
                    </div>
                    
                    <div className="form-floating mb-4">
                      <input
                        type="password"
                        className="form-control custom-input"
                        id="password"
                        name="password"
                        placeholder="Salasana"
                        value={formData.password}
                        onChange={handleChange}
                        required
                      />
                      <label htmlFor="password">Salasana</label>
                    </div>
                    
                    <div className="form-check mb-4">
                      <div className="remember-me">
                        <input className="form-check-input" type="checkbox" id="rememberMe" />
                        <label className="form-check-label" htmlFor="rememberMe">
                          Muista minut
                        </label>
                      </div>
                      <Link to="/forgot-password" className="forgot-password">
                        Unohditko salasanasi?
                      </Link>
                    </div>
                    
                    <div className="d-grid">
                      <button
                        type="submit"
                        className="btn btn-accent login-btn"
                        disabled={loading}
                      >
                        {loading ? (
                          <>
                            <span className="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                            Kirjaudutaan...
                          </>
                        ) : (
                          'Kirjaudu sisään'
                        )}
                      </button>
                    </div>
                  </form>

                  <div className="login-footer">
                    <p>
                      Eikö sinulla ole vielä tiliä? <Link to="/register" className="register-link">Rekisteröidy nyt</Link>
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Oikea puoli - Ominaisuusesittely */}
              <div className="col-lg-6 d-none d-lg-block">
                <div className="login-feature-panel">
                  <div className="login-feature-title">
                    <h2>Tee <span className="accent-text">fiksumpia asuntopäätöksiä</span> tekoälyn avulla</h2>
                  </div>
                  
                  <div className="login-feature-list">
                    <div className="login-feature-item">
                      <div className="login-feature-icon">
                        <i className="fas fa-magnifying-glass-chart"></i>
                      </div>
                      <div className="login-feature-content">
                        <h4>Syvällinen analyysi</h4>
                        <p>Tekoäly analysoi asuntoilmoituksen ja tuottaa yksityiskohtaisen raportin kohteen vahvuuksista ja heikkouksista.</p>
                      </div>
                    </div>
                    
                    <div className="login-feature-item">
                      <div className="login-feature-icon">
                        <i className="fas fa-shield-alt"></i>
                      </div>
                      <div className="login-feature-content">
                        <h4>Riskianalyysi</h4>
                        <p>Tunnista kohteeseen liittyvät riskit jo ennen ostopäätöstä. Saat tarkan riskiprofiilin jokaisesta kohteesta.</p>
                      </div>
                    </div>
                    
                    <div className="login-feature-item">
                      <div className="login-feature-icon">
                        <i className="fas fa-bullseye"></i>
                      </div>
                      <div className="login-feature-content">
                        <h4>Sijoituspotentiaali</h4>
                        <p>Arvioimme kohteen potentiaalin sijoituksena ja tunnistamme mahdolliset kehityskohteet arvonnousun maksimoimiseksi.</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            {/* Mobiililla näytettävät ominaisuudet */}
            <div className="d-block d-lg-none">
              <div className="login-features">
                <div className="feature-item">
                  <i className="fas fa-magnifying-glass-chart"></i>
                  <span>Syvällinen analyysi</span>
                </div>
                <div className="feature-item">
                  <i className="fas fa-shield-alt"></i>
                  <span>Tarkka riskiarviointi</span>
                </div>
                <div className="feature-item">
                  <i className="fas fa-bullseye"></i>
                  <span>Sijoituspotentiaali</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login; 