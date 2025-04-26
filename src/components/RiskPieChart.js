import React, { useEffect, useState } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Pie } from 'react-chartjs-2';

// Rekisteröidään tarvittavat ChartJS-komponentit
ChartJS.register(ArcElement, Tooltip, Legend);

// Tehostevärin eri sävyt
const generateColors = (baseColor = '#007bff', count = 5) => {
  // Muutetaan hex-väri RGB-muotoon
  const hexToRgb = (hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
    return result ? {
      r: parseInt(result[1], 16),
      g: parseInt(result[2], 16),
      b: parseInt(result[3], 16)
    } : { r: 0, g: 0, b: 0 };
  };

  const rgb = hexToRgb(baseColor);
  const colors = [];
  const transparencies = [];

  // Luodaan variaatioita väristä muuttamalla kirkkautta ja saturaatiota
  for (let i = 0; i < count; i++) {
    // Säädä sinistä komponentia tummuuden säätelyyn
    const adjustedR = Math.min(255, rgb.r - 20 + i * 25);
    const adjustedG = Math.min(255, rgb.g - 20 + i * 15);
    const adjustedB = Math.min(255, rgb.b + i * 5);
    
    colors.push(`rgb(${adjustedR}, ${adjustedG}, ${adjustedB})`);
    transparencies.push(`rgba(${adjustedR}, ${adjustedG}, ${adjustedB}, 0.7)`);
  }

  return { backgroundColor: colors, borderColor: transparencies };
};

// Löydä riskikategoriat ja niiden prosentuaaliset osuudet tekstistä
const extractRiskData = (content) => {
  // Jos sisältö puuttuu, palauta oletusdata
  if (!content) {
    return {
      labels: ['Ei riskitietoja'],
      data: [100]
    };
  }

  // Yritetään etsiä käyttökelpoista dataa sisällöstä
  // Tässä vaiheessa etsimme prosenttimerkintöjä ja niihin liittyviä kategorioita
  const riskMatches = content.match(/(?:riski|haitta|ongelma|haaste|uhka)[^:\.]*?(?:\s+on\s+|\:\s*)(\d+)(?:\s*\%|\s+prosenttia)/gi);
  const percentageMatches = content.match(/(\d+)(?:\s*\%|\s+prosenttia\b)/gi);
  
  // Etsi myös erityisiä riskikategorioita
  const categories = [
    'hintariski', 'hinnoitteluriski', 'sijaintiriski', 'tekninen riski', 'rakenneriskit', 
    'korjausriski', 'markkinariski', 'remontointiriski', 'alueriski', 'taloyhtiöriski',
    'taloudellinen riski', 'rahoitusriski', 'vakuusriski', 'kaavoitusriski', 'ympäristöriski'
  ];
  
  // Jos suoraan prosenttisia riskejä ei löydy, yritetään tekstianalyysia 
  if (!riskMatches || riskMatches.length === 0) {
    // Etsi riskikategorioihin viittaavat lauseet
    const extractedCategories = {};
    let totalRisks = 0;
    
    // Splittaa teksti lauseiksi ja analysoi jokainen
    const sentences = content.split(/[.!?]+/);
    
    for (const sentence of sentences) {
      // Etsi lauseesta riskikategorioita
      for (const category of categories) {
        if (sentence.toLowerCase().includes(category)) {
          // Arvioi riskin vakavuus lauseessa esiintyvien sanojen perusteella
          const severity = 
            sentence.match(/(?:merkittävä|suuri|korkea|vakava|huomattava)/i) ? 3 :
            sentence.match(/(?:kohtalainen|keskitason|huomioitava)/i) ? 2 : 
            sentence.match(/(?:vähäinen|pieni|matala|lievä)/i) ? 1 : 2;
          
          extractedCategories[category] = (extractedCategories[category] || 0) + severity;
          totalRisks += severity;
        }
      }
    }
    
    // Jos riskikategorioita löytyi, tehdään niistä data
    if (Object.keys(extractedCategories).length > 0) {
      const labels = Object.keys(extractedCategories);
      const data = labels.map(label => Math.round((extractedCategories[label] / totalRisks) * 100));
      
      return { labels, data };
    }
    
    // Jos riskilausekkeita ei löytynyt, luodaan synteettinen data tekstin perusteella
    return createSyntheticRiskData(content);
  }
  
  // Käsittele suoraan tunnistetut riskit
  const riskData = {};
  
  // Etsi riskit, joilla on prosenttiosuudet
  for (const match of riskMatches) {
    const parts = match.split(/(?:on\s+|:\s*)/);
    if (parts.length >= 2) {
      const category = parts[0].trim().replace(/^[^a-zA-Z]+/, '');
      const percentage = parseInt(parts[1].trim().match(/\d+/)[0]);
      if (category && !isNaN(percentage)) {
        riskData[category] = percentage;
      }
    }
  }
  
  // Jos dataa ei ole tarpeeksi, käytä synteettistä dataa
  if (Object.keys(riskData).length < 2) {
    return createSyntheticRiskData(content);
  }
  
  // Normalisoi data vastaamaan 100%
  const total = Object.values(riskData).reduce((sum, value) => sum + value, 0);
  const labels = Object.keys(riskData);
  const data = labels.map(label => Math.round((riskData[label] / total) * 100));
  
  return { labels, data };
};

// Luo synteettinen data tekstianalyysin perusteella
const createSyntheticRiskData = (content) => {
  const riskTypes = [
    { label: 'Hintariski', keywords: ['hinta', 'hinnoittelu', 'ylihinnoiteltu', 'kallis'] },
    { label: 'Sijaintiriski', keywords: ['sijainti', 'alue', 'ympäristö', 'saavutettavuus'] },
    { label: 'Tekninen riski', keywords: ['kunto', 'rakennus', 'tekniikka', 'korjaus', 'remontti'] },
    { label: 'Taloyhtiöriski', keywords: ['taloyhtiö', 'yhtiö', 'yhtiölaina', 'vastike'] },
    { label: 'Tuottoriski', keywords: ['tuotto', 'vuokra', 'sijoitus', 'arvonnousu'] }
  ];

  const riskScores = {};
  
  // Laske jokaiselle riskityypille pisteet tekstin perusteella
  for (const riskType of riskTypes) {
    let score = 0;
    const lowercaseContent = content.toLowerCase();
    
    for (const keyword of riskType.keywords) {
      // Laske avainsanan esiintymiskerrat ja painota niitä
      const matches = lowercaseContent.match(new RegExp(keyword, 'gi'));
      if (matches) {
        score += matches.length;
      }
    }
    
    riskScores[riskType.label] = score > 0 ? score : 1; // Vähintään 1 piste jokaiselle tyypille
  }
  
  // Normalisoi pisteet prosenteiksi
  const total = Object.values(riskScores).reduce((sum, value) => sum + value, 0);
  const labels = Object.keys(riskScores);
  const data = labels.map(label => Math.round((riskScores[label] / total) * 100));
  
  return { labels, data };
};

function RiskPieChart({ riskAnalysisContent }) {
  const [chartData, setChartData] = useState(null);
  
  useEffect(() => {
    // Kun riskianalyysin sisältö muuttuu, päivitä kaavio
    if (riskAnalysisContent) {
      const { labels, data } = extractRiskData(riskAnalysisContent);
      const { backgroundColor, borderColor } = generateColors('#007bff', labels.length);
      
      setChartData({
        labels,
        datasets: [{
          data,
          backgroundColor,
          borderColor,
          borderWidth: 1,
        }]
      });
    }
  }, [riskAnalysisContent]);
  
  if (!chartData) {
    return <div className="text-center my-3">Ei riskitietoja saatavilla</div>;
  }

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          font: {
            size: 14
          },
          padding: 20
        }
      },
      tooltip: {
        callbacks: {
          label: function(context) {
            return `${context.label}: ${context.raw}%`;
          }
        }
      }
    }
  };
  
  return (
    <div className="risk-chart-container">
      <h5 className="text-center mb-4">Riskien jakautuminen</h5>
      <div style={{ maxWidth: '500px', margin: '0 auto' }}>
        <Pie data={chartData} options={options} />
      </div>
    </div>
  );
}

export default RiskPieChart; 