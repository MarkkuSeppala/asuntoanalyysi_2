import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import styled from 'styled-components';
import { FiLink, FiSearch, FiAlertCircle, FiLoader } from 'react-icons/fi';
import { createAnalysis } from '../services/analysisService';

const FormContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
`;

const FormHeader = styled.div`
  margin-bottom: 2rem;
`;

const FormCard = styled.div`
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  padding: 2rem;
  margin-bottom: 2rem;
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
`;

const InputWrapper = styled.div`
  position: relative;
`;

const Input = styled.input`
  width: 100%;
  padding: 0.75rem 1rem 0.75rem 2.5rem;
  border: 1px solid ${props => props.hasError ? 'var(--danger)' : 'var(--gray-300)'};
  border-radius: var(--border-radius);
  font-size: 1rem;
  transition: var(--transition);
  
  &:focus {
    outline: none;
    border-color: ${props => props.hasError ? 'var(--danger)' : 'var(--primary)'};
    box-shadow: 0 0 0 2px ${props => props.hasError ? 'rgba(234, 67, 53, 0.2)' : 'rgba(45, 93, 124, 0.2)'};
  }
`;

const InputIcon = styled.div`
  position: absolute;
  left: 1rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--gray-500);
`;

const ErrorMessage = styled.div`
  color: var(--danger);
  font-size: 0.875rem;
  margin-top: 0.5rem;
  display: flex;
  align-items: center;
  
  svg {
    margin-right: 0.25rem;
  }
`;

const SubmitButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  
  svg {
    margin-right: 0.5rem;
  }
`;

const FormError = styled.div`
  background-color: rgba(234, 67, 53, 0.1);
  color: var(--danger);
  padding: 0.75rem;
  border-radius: var(--border-radius);
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  
  svg {
    margin-right: 0.5rem;
    flex-shrink: 0;
  }
`;

const InfoPanel = styled.div`
  background-color: var(--gray-100);
  border-radius: var(--border-radius);
  padding: 1.5rem;
  
  h3 {
    margin-top: 0;
    margin-bottom: 1rem;
    font-size: 1.25rem;
  }
  
  ul {
    padding-left: 1.5rem;
    margin-bottom: 0;
  }
  
  li {
    margin-bottom: 0.5rem;
  }
  
  p:last-child {
    margin-bottom: 0;
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

const AnalysisForm = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  
  const { 
    register, 
    handleSubmit, 
    formState: { errors } 
  } = useForm();
  
  const validatePropertyUrl = (value) => {
    if (!value) {
      return 'Asunnon URL on pakollinen';
    }
    if (!value.includes('oikotie.fi')) {
      return 'URL:n tulee olla Oikotie.fi-sivuston asuntosivu';
    }
    return true;
  };
  
  const onSubmit = async (data) => {
    setLoading(true);
    setError(null);
    
    try {
      // Luodaan analyysi
      const result = await createAnalysis(data.propertyUrl);
      
      // Ohjataan käyttäjä analyysin tulosivulle
      navigate('/analyses', { state: { newAnalysis: true }});
    } catch (err) {
      setError(err.message || 'Analyysin luominen epäonnistui. Yritä uudelleen.');
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <FormContainer>
        <Loading>
          <FiLoader />
          <h3>Analysoidaan asuntoa...</h3>
          <p>Tekoäly käsittelee tietoja. Tämä voi kestää muutaman minuutin.</p>
        </Loading>
      </FormContainer>
    );
  }
  
  return (
    <FormContainer>
      <FormHeader>
        <h1>Uusi asuntoanalyysi</h1>
        <p>Syötä analysoitavan asunnon URL Oikotie.fi-palvelusta</p>
      </FormHeader>
      
      <FormCard>
        {error && (
          <FormError>
            <FiAlertCircle />
            <span>{error}</span>
          </FormError>
        )}
        
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormGroup>
            <Label htmlFor="propertyUrl">Asunnon URL</Label>
            <InputWrapper>
              <InputIcon>
                <FiLink />
              </InputIcon>
              <Input
                id="propertyUrl"
                type="text"
                placeholder="https://asunnot.oikotie.fi/myytavat-asunnot/..."
                hasError={!!errors.propertyUrl}
                {...register('propertyUrl', { 
                  validate: validatePropertyUrl
                })}
              />
            </InputWrapper>
            {errors.propertyUrl && (
              <ErrorMessage>
                <FiAlertCircle />
                <span>{errors.propertyUrl.message}</span>
              </ErrorMessage>
            )}
          </FormGroup>
          
          <SubmitButton type="submit">
            <FiSearch /> Analysoi asunto
          </SubmitButton>
        </form>
      </FormCard>
      
      <InfoPanel>
        <h3>Tietoa analyysistä</h3>
        <p>
          Tekoälyanalyysimme käy läpi asunnon tiedot ja tuottaa kokonaisvaltaisen arvion 
          seuraavista asioista:
        </p>
        <ul>
          <li>Kohteen hinta-arvio ja vertailu alueen muihin kohteisiin</li>
          <li>Sijainnin vahvuudet ja heikkoudet</li>
          <li>Taloyhtiön kunto ja tulevat remontit</li>
          <li>Asunnon varustelutaso ja kunto</li>
          <li>Mahdolliset riskitekijät ostajan kannalta</li>
          <li>Jälleenmyyntinäkymä</li>
        </ul>
        <p>
          Analyysi perustuu Oikotie.fi-sivustolta kerättyihin tietoihin. 
          Varmistathan aina tärkeät yksityiskohdat asuntonäytöllä tai 
          kiinteistövälittäjältä.
        </p>
      </InfoPanel>
    </FormContainer>
  );
};

export default AnalysisForm; 