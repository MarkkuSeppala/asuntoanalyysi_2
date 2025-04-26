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
    <div className="login-container">
      <div className="row justify-content-center">
        <div className="col-md-6">
          <div className="card shadow">
            <div className="card-header bg-primary text-white">
              <h2 className="mb-0">Kirjaudu sisään</h2>
            </div>
            <div className="card-body">
              {error && (
                <div className="alert alert-danger" role="alert">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit}>
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
                  />
                </div>
                <div className="d-grid">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={loading}
                  >
                    {loading ? 'Kirjaudutaan...' : 'Kirjaudu'}
                  </button>
                </div>
              </form>

              <div className="mt-3 text-center">
                <p>
                  Eikö sinulla ole tiliä? <Link to="/register">Rekisteröidy</Link>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Login; 