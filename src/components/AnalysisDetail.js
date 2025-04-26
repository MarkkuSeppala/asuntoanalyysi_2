import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import RiskPieChart from './RiskPieChart';

function AnalysisDetail() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { id } = useParams();

  useEffect(() => {
    const fetchAnalysis = async () => {
      try {
        const response = await axios.get(`/api/analysis/${id}`);
        if (response.data.status === 'success') {
          setAnalysis(response.data.analysis);
        } else {
          setError('Analyysin hakemisessa tapahtui virhe.');
        }
      } catch (error) {
        setError(error.response?.data?.message || 'Palvelinvirhe analyysin hakemisessa.');
        console.error('Virhe analyysin hakemisessa:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [id]);

  const requestRiskAnalysis = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`/api/risk-analysis/${id}`);
      if (response.data.status === 'success') {
        // Päivitä analyysi
        const updatedAnalysisResponse = await axios.get(`/api/analysis/${id}`);
        if (updatedAnalysisResponse.data.status === 'success') {
          setAnalysis(updatedAnalysisResponse.data.analysis);
        }
      } else {
        setError('Riskianalyysin luomisessa tapahtui virhe.');
      }
    } catch (error) {
      setError(error.response?.data?.message || 'Palvelinvirhe riskianalyysin luomisessa.');
      console.error('Virhe riskianalyysin luomisessa:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center my-5">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Ladataan...</span>
        </div>
        <p className="mt-2">Ladataan analyysia...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        <h4 className="alert-heading">Virhe!</h4>
        <p>{error}</p>
        <hr />
        <div className="d-flex justify-content-end">
          <Link to="/analyses" className="btn btn-outline-danger">Takaisin analyyseihin</Link>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="alert alert-warning" role="alert">
        <h4 className="alert-heading">Analyysia ei löydy</h4>
        <p>Pyydettyä analyysia ei löytynyt.</p>
        <hr />
        <div className="d-flex justify-content-end">
          <Link to="/analyses" className="btn btn-outline-warning">Takaisin analyyseihin</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="analysis-detail-container">
      <div className="d-flex justify-content-between align-items-start mb-4">
        <h2>{analysis.title}</h2>
        <div>
          <Link to="/analyses" className="btn btn-outline-secondary me-2">Takaisin</Link>
          {!analysis.risk_analysis && (
            <button 
              className="btn btn-warning" 
              onClick={requestRiskAnalysis}
              disabled={loading}
            >
              {loading ? 'Luodaan...' : 'Luo riskianalyysi'}
            </button>
          )}
        </div>
      </div>

      <div className="row">
        <div className="col-md-12">
          <div className="card mb-4 shadow">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">Kohdeanalyysi</h5>
              <span className="badge bg-primary">{analysis.type}</span>
            </div>
            <div className="card-body">
              <div className="mb-3">
                <small className="text-muted">Luotu: {analysis.created_at}</small>
              </div>
              <div className="markdown-content">
                <ReactMarkdown>{analysis.content}</ReactMarkdown>
              </div>
            </div>
          </div>

          {analysis.risk_analysis && (
            <div className="card mb-4 shadow">
              <div className="card-header bg-warning text-dark">
                <h5 className="mb-0">Riskianalyysi</h5>
              </div>
              <div className="card-body">
                <div className="mb-3">
                  <small className="text-muted">Luotu: {analysis.risk_analysis.created_at}</small>
                </div>
                
                {/* Riskien visuaalinen esitys piirakkakaaviona */}
                <div className="row">
                  <div className="col-md-6">
                    <div className="markdown-content">
                      <ReactMarkdown>{analysis.risk_analysis.content}</ReactMarkdown>
                    </div>
                  </div>
                  <div className="col-md-6">
                    <div className="risk-chart-wrapper py-3">
                      <RiskPieChart riskAnalysisContent={analysis.risk_analysis.content} />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {analysis.kohteet && analysis.kohteet.length > 0 && (
            <div className="card mb-4 shadow">
              <div className="card-header bg-light">
                <h5 className="mb-0">Kohteen tiedot</h5>
              </div>
              <div className="card-body">
                <table className="table table-striped">
                  <thead>
                    <tr>
                      <th>Osoite</th>
                      <th>Tyyppi</th>
                      <th>Hinta</th>
                      <th>Rakennusvuosi</th>
                    </tr>
                  </thead>
                  <tbody>
                    {analysis.kohteet.map(kohde => (
                      <tr key={kohde.id}>
                        <td>{kohde.osoite}</td>
                        <td>{kohde.tyyppi}</td>
                        <td>{kohde.hinta ? `${kohde.hinta} €` : '-'}</td>
                        <td>{kohde.rakennusvuosi || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default AnalysisDetail; 