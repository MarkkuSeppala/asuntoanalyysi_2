import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { 
  FiPlusCircle, 
  FiBarChart2, 
  FiTrendingUp, 
  FiHome, 
  FiList,
  FiBookmark,
  FiCalendar,
  FiAlertCircle
} from 'react-icons/fi';
import { BiBuildingHouse } from 'react-icons/bi';
import { getUserAnalyses } from '../services/analysisService';

const DashboardContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 2rem;
`;

const DashboardHeader = styled.div`
  margin-bottom: 1rem;
`;

const WelcomeMessage = styled.div`
  background-color: var(--primary);
  color: white;
  border-radius: var(--border-radius);
  padding: 2rem;
  margin-bottom: 2rem;
  
  h1 {
    color: white;
    margin-bottom: 0.5rem;
  }
  
  p {
    opacity: 0.9;
    max-width: 600px;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 1rem;
  margin-top: 1.5rem;
  
  @media (max-width: 576px) {
    flex-direction: column;
  }
`;

const ActionButton = styled(Link)`
  display: inline-flex;
  align-items: center;
  background-color: ${props => props.secondary ? 'rgba(255, 255, 255, 0.2)' : 'white'};
  color: ${props => props.secondary ? 'white' : 'var(--primary)'};
  border-radius: var(--border-radius);
  padding: 0.75rem 1.5rem;
  font-weight: 500;
  transition: var(--transition);
  
  &:hover {
    background-color: ${props => props.secondary ? 'rgba(255, 255, 255, 0.3)' : 'var(--gray-100)'};
    color: ${props => props.secondary ? 'white' : 'var(--primary)'};
  }
  
  svg {
    margin-right: 0.5rem;
  }
`;

const ContentSection = styled.div`
  margin-bottom: 2rem;
`;

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  
  h2 {
    margin-bottom: 0;
  }
`;

const ViewAllLink = styled(Link)`
  display: flex;
  align-items: center;
  font-weight: 500;
  font-size: 0.875rem;
  
  svg {
    margin-left: 0.25rem;
  }
`;

const CardGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
  
  @media (max-width: 576px) {
    grid-template-columns: 1fr;
  }
`;

const Card = styled.div`
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 1.5rem;
  transition: var(--transition);
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
  }
`;

const ActionCard = styled(Link)`
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 2rem 1.5rem;
  transition: var(--transition);
  color: var(--gray-800);
  
  svg {
    font-size: 2.5rem;
    color: var(--primary);
    margin-bottom: 1rem;
  }
  
  h3 {
    margin-bottom: 0.5rem;
    color: var(--gray-900);
  }
  
  p {
    color: var(--gray-600);
    margin-bottom: 0;
  }
  
  &:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
    color: var(--gray-800);
  }
`;

const PropertyCard = styled(Link)`
  display: block;
  color: var(--gray-800);
  
  &:hover {
    color: var(--gray-800);
  }
  
  h3 {
    font-size: 1.25rem;
    margin-bottom: 0.5rem;
    color: var(--primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
`;

const PropertyMeta = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
  font-size: 0.875rem;
  color: var(--gray-600);
  
  svg {
    margin-right: 0.25rem;
  }
  
  span + span {
    margin-left: 1rem;
  }
`;

const PropertyTags = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const PropertyTag = styled.span`
  background-color: var(--gray-100);
  color: var(--gray-700);
  border-radius: 20px;
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 500;
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

const Dashboard = () => {
  const [recentAnalyses, setRecentAnalyses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const fetchAnalyses = async () => {
      try {
        const analyses = await getUserAnalyses();
        setRecentAnalyses(analyses?.slice(0, 3) || []);
      } catch (err) {
        setError('Analyysien hakeminen epäonnistui');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchAnalyses();
  }, []);
  
  // Tämä formatoi päivämäärän
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fi-FI');
  };
  
  return (
    <DashboardContainer>
      <WelcomeMessage>
        <h1>Tervetuloa Asuntoanalyysiin</h1>
        <p>
          Löydä täydelliset asuntotiedot, syvälliset analyysit ja vertailukelpoiset arviot 
          kiinteistöjä varten. Tee tietopohjaisia päätöksiä tekoälyn avulla.
        </p>
        
        <ActionButtons>
          <ActionButton to="/new-analysis">
            <FiPlusCircle /> Uusi analyysi
          </ActionButton>
          <ActionButton to="/analyses" secondary>
            <FiList /> Kaikki analyysit
          </ActionButton>
        </ActionButtons>
      </WelcomeMessage>
      
      <ContentSection>
        <SectionHeader>
          <h2>Mitä haluat tehdä tänään?</h2>
        </SectionHeader>
        
        <CardGrid>
          <ActionCard to="/new-analysis">
            <FiHome />
            <h3>Analysoi asunto</h3>
            <p>Syötä Oikotie-linkki ja saa tekoälyanalyysi kohteesta</p>
          </ActionCard>
          
          <ActionCard to="/market-trends">
            <FiBarChart2 />
            <h3>Markkinatrendit</h3>
            <p>Tarkastele tämänhetkisiä asuntomarkkinoiden trendejä</p>
          </ActionCard>
          
          <ActionCard to="/property-comparison">
            <BiBuildingHouse />
            <h3>Vertaile asuntoja</h3>
            <p>Vertaile eri asuntojen ominaisuuksia vierekkäin</p>
          </ActionCard>
        </CardGrid>
      </ContentSection>
      
      <ContentSection>
        <SectionHeader>
          <h2>Viimeisimmät analyysisi</h2>
          {recentAnalyses.length > 0 && (
            <ViewAllLink to="/analyses">
              Näytä kaikki
            </ViewAllLink>
          )}
        </SectionHeader>
        
        {loading ? (
          <p>Ladataan analyysejä...</p>
        ) : error ? (
          <EmptyState>
            <FiAlertCircle />
            <h3>Analyysien hakeminen epäonnistui</h3>
            <p>{error}</p>
            <Link to="/new-analysis" className="button">
              Kokeile uuden analyysin luomista
            </Link>
          </EmptyState>
        ) : recentAnalyses.length > 0 ? (
          <CardGrid>
            {recentAnalyses.map((analysis) => (
              <Card key={analysis.id}>
                <PropertyCard to={`/analysis/${analysis.id}`}>
                  <h3>{analysis.title || 'Nimetön analyysi'}</h3>
                  <PropertyMeta>
                    <span>
                      <FiCalendar />
                      {formatDate(analysis.created_at)}
                    </span>
                  </PropertyMeta>
                  <p>
                    {analysis.property_url ? (
                      <>Lähde: {analysis.property_url.replace(/^https?:\/\//, '').split('/')[0]}</>
                    ) : (
                      'Ei lähdetietoja'
                    )}
                  </p>
                  <PropertyTags>
                    <PropertyTag>Asunto</PropertyTag>
                    <PropertyTag>Analyysi</PropertyTag>
                  </PropertyTags>
                </PropertyCard>
              </Card>
            ))}
          </CardGrid>
        ) : (
          <EmptyState>
            <FiBookmark />
            <h3>Ei vielä analyysejä</h3>
            <p>
              Täällä näet viimeisimmät analyysisi. Aloita tekemällä 
              ensimmäinen asuntoanalyysisi.
            </p>
            <Link to="/new-analysis" className="button">
              <FiPlusCircle /> Luo ensimmäinen analyysi
            </Link>
          </EmptyState>
        )}
      </ContentSection>
    </DashboardContainer>
  );
};

export default Dashboard; 