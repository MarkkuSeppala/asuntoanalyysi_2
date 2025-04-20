import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { FiHome, FiSearch } from 'react-icons/fi';

const NotFoundContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 4rem 1rem;
`;

const ErrorCode = styled.h1`
  font-size: 8rem;
  color: var(--primary);
  margin: 0;
  line-height: 1;
  
  @media (max-width: 576px) {
    font-size: 6rem;
  }
`;

const ErrorTitle = styled.h2`
  font-size: 2rem;
  margin-bottom: 1.5rem;
`;

const ErrorMessage = styled.p`
  font-size: 1.125rem;
  color: var(--gray-600);
  max-width: 500px;
  margin-bottom: 2rem;
`;

const ButtonContainer = styled.div`
  display: flex;
  gap: 1rem;
  
  @media (max-width: 576px) {
    flex-direction: column;
  }
`;

const HomeButton = styled(Link)`
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  
  svg {
    margin-right: 0.5rem;
  }
`;

const SearchButton = styled(Link)`
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  background-color: transparent;
  border: 2px solid var(--primary);
  color: var(--primary);
  
  &:hover {
    background-color: var(--primary);
    color: white;
  }
  
  svg {
    margin-right: 0.5rem;
  }
`;

const NotFound = () => {
  return (
    <NotFoundContainer>
      <ErrorCode>404</ErrorCode>
      <ErrorTitle>Sivua ei löytynyt</ErrorTitle>
      <ErrorMessage>
        Valitettavasti etsimääsi sivua ei löytynyt. Tarkista onko URL-osoite oikein tai 
        palaa takaisin etusivulle.
      </ErrorMessage>
      
      <ButtonContainer>
        <HomeButton to="/dashboard" className="button">
          <FiHome /> Etusivulle
        </HomeButton>
        <SearchButton to="/new-analysis" className="button outline">
          <FiSearch /> Uusi analyysi
        </SearchButton>
      </ButtonContainer>
    </NotFoundContainer>
  );
};

export default NotFound; 