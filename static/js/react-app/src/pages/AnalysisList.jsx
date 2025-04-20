import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { 
  FiPlusCircle, 
  FiCalendar, 
  FiDownload,
  FiExternalLink,
  FiSearch,
  FiFilter,
  FiAlertCircle,
  FiLoader
} from 'react-icons/fi';
import { getUserAnalyses, downloadAnalysis } from '../services/analysisService';

const PageContainer = styled.div`
  max-width: 1000px;
  margin: 0 auto;
`;

const PageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
`;

const HeaderTitle = styled.div`
  h1 {
    margin-bottom: 0.25rem;
  }
  
  p {
    color: var(--gray-600);
    margin-bottom: 0;
  }
`;

const NewAnalysisButton = styled(Link)`
  display: flex;
  align-items: center;
  white-space: nowrap;
  
  svg {
    margin-right: 0.5rem;
  }
  
  @media (max-width: 768px) {
    width: 100%;
    justify-content: center;
  }
`;

const FiltersRow = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 1.5rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 1rem;
  }
`;

const SearchBox = styled.div`
  position: relative;
  width: 100%;
  max-width: 400px;
  
  @media (max-width: 768px) {
    max-width: none;
  }
`;

const SearchInput = styled.input`
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid var(--gray-300);
  border-radius: var(--border-radius);
  font-size: 1rem;
  
  &:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 2px rgba(45, 93, 124, 0.2);
  }
`;

const SearchIcon = styled.div`
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--gray-500);
`;

const FilterButtons = styled.div`
  display: flex;
  gap: 0.5rem;
`;

const FilterButton = styled.button`
  display: flex;
  align-items: center;
  background-color: ${props => props.active ? 'var(--primary)' : 'white'};
  color: ${props => props.active ? 'white' : 'var(--gray-700)'};
  border: 1px solid ${props => props.active ? 'var(--primary)' : 'var(--gray-300)'};
  border-radius: var(--border-radius);
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  transition: var(--transition);
  
  &:hover {
    background-color: ${props => props.active ? 'var(--primary-dark)' : 'var(--gray-100)'};
  }
  
  svg {
    margin-right: 0.25rem;
  }
`;

const AnalysisList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
`;

const AnalysisCard = styled.div`
  display: flex;
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  transition: var(--transition);
  overflow: hidden;
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  }
  
  @media (max-width: 576px) {
    flex-direction: column;
  }
`;

const AnalysisContent = styled.div`
  flex: 1;
  padding: 1.5rem;
  
  h3 {
    margin-top: 0;
    margin-bottom: 0.5rem;
    font-size: 1.25rem;
  }
  
  p {
    color: var(--gray-600);
    margin-bottom: 0.5rem;
  }
`;

const AnalysisActions = styled.div`
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const ActionButton = styled(Link)`
  display: flex;
  align-items: center;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  border-radius: var(--border-radius);
  
  svg {
    margin-right: 0.25rem;
  }
`;

const DownloadButton = styled.button`
  display: flex;
  align-items: center;
  background-color: transparent;
  color: var(--gray-700);
  border: 1px solid var(--gray-300);
  border-radius: var(--border-radius);
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  transition: var(--transition);
  
  &:hover {
    background-color: var(--gray-100);
  }
  
  svg {
    margin-right: 0.25rem;
  }
`;

const AnalysisMeta = styled.div`
  display: flex;
  align-items: center;
  font-size: 0.875rem;
  color: var(--gray-600);
  margin-bottom: 0.75rem;
  
  svg {
    margin-right: 0.25rem;
  }
  
  span + span {
    margin-left: 1rem;
  }
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background-color: var(--gray-100);
  border-radius: var(--border-radius);
  padding: 3rem 1.5rem;
  
  svg {
    font-size: 3rem;
    color: var(--gray-400);
    margin-bottom: 1rem;
  }
  
  h3 {
    margin-bottom: 0.5rem;
  }
  
  p {
    color: var(--gray-600);
    margin-bottom: 1.5rem;
    max-width: 400px;
  }
`;

const Loading = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 3rem 1rem;
  
  svg {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: var(--primary);
    animation: spin 1.5s linear infinite;
  }
  
  h3 {
    margin-bottom: 0.5rem;
  }
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const Notification = styled.div`
  background-color: var(--secondary-light);
  color: var(--primary-dark);
  padding: 1rem;
  border-radius: var(--border-radius);
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  
  svg {
    margin-right: 0.5rem;
    flex-shrink: 0;
  }
`;

const AnalysisListPage = () => {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState('all');
  const location = useLocation();
  
  // Tarkistetaan, tuliko käyttäjä juuri tekemästä uutta analyysiä
  const isNewAnalysis = location.state?.newAnalysis;
  
  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        const data = await getUserAnalyses();
        setAnalyses(data || []);
      } catch (err) {
        setError(err.message || 'Analyysien hakeminen epäonnistui');
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalyses();
  }, []);
  
  // Päivämäärän formatointi
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fi-FI');
  };
  
  // Hakusuodatin
  const filteredAnalyses = analyses
    .filter((analysis) => {
      const searchMatch = searchTerm === '' || 
        (analysis.title && analysis.title.toLowerCase().includes(searchTerm.toLowerCase())) || 
        (analysis.property_url && analysis.property_url.toLowerCase().includes(searchTerm.toLowerCase()));
      
      if (filter === 'all') return searchMatch;
      
      // Tässä voisi olla lisää suodattimia, kuten 'recent' tms.
      return searchMatch;
    })
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  
  // Analyysin lataus
  const handleDownload = async (analysisId, title) => {
    try {
      const blob = await downloadAnalysis(analysisId);
      
      // Luodaan download-linkki
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `${title || 'analyysi'}.txt`;
      document.body.appendChild(a);
      a.click();
      
      // Siivotaan
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Lataus epäonnistui', err);
      alert('Analyysin lataaminen epäonnistui. Yritä uudelleen.');
    }
  };
  
  if (loading) {
    return (
      <PageContainer>
        <Loading>
          <FiLoader />
          <h3>Ladataan analyysejä...</h3>
        </Loading>
      </PageContainer>
    );
  }
  
  return (
    <PageContainer>
      <PageHeader>
        <HeaderTitle>
          <h1>Omat analyysit</h1>
          <p>Selaa ja hallinnoi luomiasi asuntoanalyysejä</p>
        </HeaderTitle>
        
        <NewAnalysisButton to="/new-analysis" className="button">
          <FiPlusCircle /> Uusi analyysi
        </NewAnalysisButton>
      </PageHeader>
      
      {isNewAnalysis && (
        <Notification>
          <FiAlertCircle />
          <span>Uusi analyysi luotu onnistuneesti!</span>
        </Notification>
      )}
      
      <FiltersRow>
        <SearchBox>
          <SearchIcon>
            <FiSearch />
          </SearchIcon>
          <SearchInput
            type="text"
            placeholder="Hae analyysejä..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </SearchBox>
        
        <FilterButtons>
          <FilterButton 
            active={filter === 'all'} 
            onClick={() => setFilter('all')}
          >
            <FiFilter /> Kaikki
          </FilterButton>
        </FilterButtons>
      </FiltersRow>
      
      {error ? (
        <EmptyState>
          <FiAlertCircle />
          <h3>Analyysien hakeminen epäonnistui</h3>
          <p>{error}</p>
          <Link to="/new-analysis" className="button">
            Kokeile uuden analyysin luomista
          </Link>
        </EmptyState>
      ) : filteredAnalyses.length > 0 ? (
        <AnalysisList>
          {filteredAnalyses.map((analysis) => (
            <AnalysisCard key={analysis.id}>
              <AnalysisContent>
                <h3>{analysis.title || 'Nimetön analyysi'}</h3>
                
                <AnalysisMeta>
                  <span>
                    <FiCalendar />
                    {formatDate(analysis.created_at)}
                  </span>
                </AnalysisMeta>
                
                <p>
                  {analysis.property_url ? (
                    <>Lähde: {analysis.property_url.replace(/^https?:\/\//, '').split('/')[0]}</>
                  ) : (
                    'Ei lähdetietoja'
                  )}
                </p>
                
                <AnalysisActions>
                  <ActionButton to={`/analysis/${analysis.id}`} className="button">
                    Näytä analyysi
                  </ActionButton>
                  
                  <DownloadButton onClick={() => handleDownload(analysis.id, analysis.title)}>
                    <FiDownload /> Lataa
                  </DownloadButton>
                  
                  {analysis.property_url && (
                    <ActionButton 
                      as="a" 
                      href={analysis.property_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="button outline"
                    >
                      <FiExternalLink /> Alkuperäinen ilmoitus
                    </ActionButton>
                  )}
                </AnalysisActions>
              </AnalysisContent>
            </AnalysisCard>
          ))}
        </AnalysisList>
      ) : (
        <EmptyState>
          <FiAlertCircle />
          <h3>Ei analyysejä</h3>
          <p>
            Et ole vielä tehnyt yhtään analyysiä. Aloita luomalla 
            ensimmäinen asuntoanalyysisi.
          </p>
          <Link to="/new-analysis" className="button">
            <FiPlusCircle /> Luo ensimmäinen analyysi
          </Link>
        </EmptyState>
      )}
    </PageContainer>
  );
};

export default AnalysisListPage; 