import React from 'react';
import { Link } from 'react-router-dom';

function LandingPage() {
  return (
    <div className="landing-page">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="container">
          <div className="row align-items-center hero-content">
            <div className="col-lg-7 col-md-12">
              <h1 className="hero-title">Tee <span className="accent-text">fiksumpia asuntopäätöksiä</span> tekoälyn avulla</h1>
              <p className="hero-subtitle">Kotolyysi auttaa sinua analysoimaan potentiaalisia asuntokohteita syvällisesti ja tunnistamaan piilevät riskit ja mahdollisuudet.</p>
              <div className="d-flex flex-wrap">
                <Link to="/register" className="btn btn-accent mb-2 mb-lg-0">Rekisteröidy nyt</Link>
                <Link to="/login" className="btn btn-outline d-inline-block">Kirjaudu sisään</Link>
              </div>
            </div>
            <div className="col-lg-5 d-none d-lg-block">
              <img src="/static/img/hero-image.svg" alt="Kotolyysi" className="img-fluid" onError={(e) => {e.target.style.display='none'}} />
            </div>
          </div>
        </div>
      </section>

      {/* Logo Section */}
      <div style={{height: '100px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '400px', marginBottom: '30px'}} className="logo-section">
        <img src="/static/img/etuovi-logo.png" alt="Etuovi Logo" style={{maxHeight: '35px'}} />
        <img src="/static/img/oikotie-logo.png" alt="Oikotie Logo" style={{maxHeight: '50px'}} />
      </div>

      {/* Features Section */}
      <section className="feature-section">
        <div className="container" style={{paddingTop: '50px'}}>
          <div className="row text-center mb-5">
            <div className="col-lg-12">
              <h2 className="section-title mx-auto">Ominaisuudet</h2>
              <p className="section-subtitle mx-auto">Kotolyysi tarjoaa kattavan työkalupaketin, joka auttaa sinua tekemään parempia sijoituspäätöksiä.</p>
            </div>
          </div>
          
          <div className="row">
            <div className="col-lg-4 col-md-6 col-sm-12">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="fas fa-magnifying-glass-chart"></i>
                </div>
                <h3 className="feature-title">Syvällinen analyysi</h3>
                <p>Tekoäly analysoi asuntoilmoituksen ja tuottaa yksityiskohtaisen raportin kohteen vahvuuksista ja heikkouksista.</p>
              </div>
            </div>
            
            <div className="col-lg-4 col-md-6 col-sm-12">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="fas fa-shield-alt"></i>
                </div>
                <h3 className="feature-title">Riskianalyysi</h3>
                <p>Tunnista kohteeseen liittyvät riskit jo ennen ostopäätöstä. Saat tarkan riskiprofiilin jokaisesta kohteesta.</p>
              </div>
            </div>
            
            <div className="col-lg-4 col-md-6 col-sm-12">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="fas fa-bullseye"></i>
                </div>
                <h3 className="feature-title">Sijoituspotentiaali</h3>
                <p>Arvioimme kohteen potentiaalin sijoituksena ja tunnistamme mahdolliset kehityskohteet arvonnousun maksimoimiseksi.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="feature-section">
        <div className="container">
          <div className="row text-center mb-5">
            <div className="col-lg-12">
              <h2 className="section-title mx-auto">Näin se toimii</h2>
              <p className="section-subtitle mx-auto">Kotolyysi on suunniteltu helppokäyttöiseksi. Näin pääset alkuun:</p>
            </div>
          </div>
          
          <div className="row">
            <div className="col-lg-3 col-md-6 col-sm-6">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="fas fa-user-plus"></i>
                </div>
                <h3 className="feature-title">1. Rekisteröidy</h3>
                <p>Luo tili muutamassa sekunnissa ja kirjaudu sisään palveluun.</p>
              </div>
            </div>
            
            <div className="col-lg-3 col-md-6 col-sm-6">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="fas fa-paste"></i>
                </div>
                <h3 className="feature-title">2. Liitä URL</h3>
                <p>Kopioi Oikotie- tai Etuovi-asuntoilmoituksen linkki ja liitä se analyysityökaluun.</p>
              </div>
            </div>
            
            <div className="col-lg-3 col-md-6 col-sm-6">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="fas fa-robot"></i>
                </div>
                <h3 className="feature-title">3. Odota analyysia</h3>
                <p>Tekoäly analysoi kohteen ja tuottaa kattavan raportin muutamassa sekunnissa.</p>
              </div>
            </div>
            
            <div className="col-lg-3 col-md-6 col-sm-6">
              <div className="feature-card">
                <div className="feature-icon">
                  <i className="fas fa-chart-line"></i>
                </div>
                <h3 className="feature-title">4. Tee päätös</h3>
                <p>Hyödynnä saamaasi tietoa päätöksenteossa ja valitse parhaat sijoituskohteet.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="cta-section">
        <div className="container text-center">
          <h2 className="cta-title">Aloita asuntojen älykäs analysointi tänään</h2>
          <p className="cta-subtitle mx-auto">Rekisteröidy nyt ja saat käyttöösi tekoälyavusteisen asuntoanalyysityökalun, joka auttaa sinua tekemään parempia asuntopäätöksiä.</p>
          <Link to="/register" className="btn btn-light btn-lg my-2">Rekisteröidy ilmaiseksi</Link>
        </div>
      </section>
    </div>
  );
}

export default LandingPage; 