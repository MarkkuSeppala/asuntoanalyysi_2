import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function AnalysisForm() {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('/api/analyze', { url });
      if (response.data.status === 'success') {
        navigate(`/analysis/${response.data.analysis_id}`);
      } else {
        setError(response.data.message || 'Analyysin luomisessa tapahtui virhe.');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'Palvelinvirhe analyysin luomisessa.');
      console.error('Analyysivirhe:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="analysis-form-container">
      <div className="row justify-content-center">
        <div className="col-md-8">
          <div className="card shadow">
            <div className="card-header bg-primary text-white">
              <h2 className="mb-0">Luo uusi asuntoanalyysi</h2>
            </div>
            <div className="card-body">
              <p className="card-text">
                Syötä Etuovi.com tai Oikotie.fi asuntoilmoituksen URL-osoite alle saadaksesi kattavan analyysin kohteesta.
              </p>

              {error && (
                <div className="alert alert-danger" role="alert">
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="urlInput" className="form-label">Asunnon URL-osoite</label>
                  <input
                    type="url"
                    className="form-control"
                    id="urlInput"
                    placeholder="https://www.etuovi.com/kohde/... tai https://asunnot.oikotie.fi/..."
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    required
                  />
                  <div className="form-text">
                    Tuetut lähteet: Etuovi.com ja Oikotie.fi
                  </div>
                </div>
                <div className="d-flex justify-content-between">
                  <button 
                    type="button" 
                    className="btn btn-outline-secondary"
                    onClick={() => navigate('/analyses')}
                  >
                    Peruuta
                  </button>
                  <button 
                    type="submit" 
                    className="btn btn-primary" 
                    disabled={loading || !url}
                  >
                    {loading ? 'Analysoidaan...' : 'Analysoi'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AnalysisForm; 