import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';

function AnalysisList() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        const response = await axios.get('/api/analyses');
        if (response.data.status === 'success') {
          setAnalyses(response.data.analyses);
        } else {
          setError('Analyysien hakemisessa tapahtui virhe.');
        }
      } catch (error) {
        setError(error.response?.data?.message || 'Palvelinvirhe analyysien hakemisessa.');
        console.error('Virhe analyysien hakemisessa:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalyses();
  }, []);

  const handleAnalysisClick = (id) => {
    navigate(`/analysis/${id}`);
  };

  if (loading) {
    return (
      <div className="text-center my-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Ladataan...</span>
        </div>
        <p className="mt-2">Ladataan analyysejä...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        <h4 className="alert-heading">Virhe!</h4>
        <p>{error}</p>
      </div>
    );
  }

  if (analyses.length === 0) {
    return (
      <div className="text-center my-5">
        <div className="card shadow">
          <div className="card-body">
            <h3 className="card-title">Ei analyysejä</h3>
            <p className="card-text">Sinulla ei ole vielä yhtään analyysiä.</p>
            <Link to="/" className="btn btn-primary">Luo uusi analyysi</Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="analyses-container">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Analyysit</h2>
        <Link to="/" className="btn btn-primary">Uusi analyysi</Link>
      </div>

      <div className="row">
        {analyses.map(analysis => (
          <div className="col-md-6 mb-4" key={analysis.id}>
            <div className="card h-100 shadow-sm" onClick={() => handleAnalysisClick(analysis.id)} style={{ cursor: 'pointer' }}>
              <div className="card-header d-flex justify-content-between">
                <h5 className="mb-0">{analysis.title}</h5>
                <span className="badge bg-primary">{analysis.type}</span>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <small className="text-muted">Luotu: {analysis.created_at}</small>
                </div>
                <p className="card-text">
                  {analysis.content && analysis.content.substring(0, 150)}
                  {analysis.content && analysis.content.length > 150 ? '...' : ''}
                </p>
              </div>
              <div className="card-footer bg-transparent text-end">
                <button 
                  className="btn btn-sm btn-outline-primary"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAnalysisClick(analysis.id);
                  }}
                >
                  Näytä analyysi
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AnalysisList; 