import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

function Home({ user }) {
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
    <div className="home-container">
      <div className="row justify-content-center">
        <div className="col-md-8">
          <div className="card shadow">
            <div className="card-header bg-primary text-white">
              <h2 className="mb-0">Asuntoanalyysi</h2>
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
                </div>
                <button 
                  type="submit" 
                  className="btn btn-primary" 
                  disabled={loading || !url}
                >
                  {loading ? 'Analysoidaan...' : 'Analysoi'}
                </button>
              </form>
            </div>
          </div>

          <div className="card mt-4 shadow">
            <div className="card-header bg-light">
              <h3 className="mb-0">Viimeisimmät analyysit</h3>
            </div>
            <div className="card-body">
              <RecentAnalyses />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Apukomponentti viimeisimpien analyysien näyttämiseen
function RecentAnalyses() {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  React.useEffect(() => {
    const fetchRecentAnalyses = async () => {
      try {
        const response = await axios.get('/api/analyses');
        if (response.data.status === 'success') {
          setAnalyses(response.data.analyses.slice(0, 5));
        }
      } catch (error) {
        console.error('Virhe analyysien hakemisessa:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRecentAnalyses();
  }, []);

  if (loading) {
    return <p>Ladataan viimeisimpiä analyysejä...</p>;
  }

  if (analyses.length === 0) {
    return <p>Ei aiempia analyysejä.</p>;
  }

  return (
    <div className="list-group">
      {analyses.map(analysis => (
        <button
          key={analysis.id}
          className="list-group-item list-group-item-action"
          onClick={() => navigate(`/analysis/${analysis.id}`)}
        >
          <div className="d-flex w-100 justify-content-between">
            <h5 className="mb-1">{analysis.title}</h5>
            <small>{analysis.created_at}</small>
          </div>
          <p className="mb-1">{analysis.type}</p>
        </button>
      ))}
    </div>
  );
}

export default Home; 