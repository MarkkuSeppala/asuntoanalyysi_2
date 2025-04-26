import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

function Register({ onRegister }) {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    password_confirm: '',
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
    
    // Vahvista salasana
    if (formData.password !== formData.password_confirm) {
      setError('Salasanat eivät täsmää.');
      return;
    }
    
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/auth/register', formData);
      if (response.data.status === 'success') {
        onRegister(response.data.user);
        navigate('/');
      } else {
        setError(response.data.message || 'Rekisteröitymisessä tapahtui virhe.');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'Rekisteröitymisessä tapahtui virhe.');
      console.error('Rekisteröitymisvirhe:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="register-container">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card shadow">
            <div className="card-header bg-primary text-white">
              <h2 className="mb-0">Rekisteröidy</h2>
            </div>
            <div className="card-body">
              {error && (
                <div className="alert alert-danger" role="alert">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="name" className="form-label">Nimi</label>
                  <input
                    type="text"
                    className="form-control"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="email" className="form-label">Sähköposti</label>
                  <input
                    type="email"
                    className="form-control"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label htmlFor="password" className="form-label">Salasana</label>
                  <input
                    type="password"
                    className="form-control"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    minLength="8"
                  />
                  <div className="form-text">
                    Salasanan tulee olla vähintään 8 merkkiä pitkä.
                  </div>
                </div>
                <div className="mb-3">
                  <label htmlFor="password_confirm" className="form-label">Vahvista salasana</label>
                  <input
                    type="password"
                    className="form-control"
                    id="password_confirm"
                    name="password_confirm"
                    value={formData.password_confirm}
                    onChange={handleChange}
                    required
                  />
                </div>
                <div className="d-grid">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                  >
                    {loading ? 'Rekisteröidään...' : 'Rekisteröidy'}
                  </button>
                </div>
              </form>

              <div className="mt-3 text-center">
                <p>
                  Onko sinulla jo tili? <Link to="/login">Kirjaudu sisään</Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Register; 