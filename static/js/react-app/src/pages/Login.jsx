import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import styled from 'styled-components';
import { FiUser, FiLock, FiAlertCircle } from 'react-icons/fi';
import { login } from '../services/authService';

const LoginContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 0;
`;

const LoginCard = styled.div`
  background-color: white;
  border-radius: var(--border-radius);
  box-shadow: var(--box-shadow);
  width: 100%;
  max-width: 450px;
  padding: 2.5rem;
  
  @media (max-width: 576px) {
    padding: 1.5rem;
  }
`;

const LoginHeader = styled.div`
  text-align: center;
  margin-bottom: 2rem;
  
  h1 {
    margin-bottom: 0.5rem;
  }
  
  p {
    color: var(--gray-600);
  }
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
  position: relative;
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

const RememberMeWrapper = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 1.5rem;
`;

const Checkbox = styled.input`
  margin-right: 0.5rem;
`;

const SubmitButton = styled.button`
  width: 100%;
  padding: 0.75rem;
  margin-bottom: 1.5rem;
`;

const ForgotPassword = styled(Link)`
  display: block;
  text-align: center;
  margin-bottom: 1.5rem;
  font-size: 0.9rem;
`;

const RegisterPrompt = styled.div`
  text-align: center;
  font-size: 0.9rem;
  
  a {
    font-weight: 500;
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

const Login = ({ setUser }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();
  
  const { 
    register, 
    handleSubmit, 
    formState: { errors } 
  } = useForm();
  
  const onSubmit = async (data) => {
    setLoading(true);
    setError(null);
    
    try {
      const userData = await login(data.username, data.password);
      setUser(userData);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Kirjautuminen epäonnistui. Tarkista tunnuksesi ja yritä uudelleen.');
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <LoginContainer>
      <LoginCard>
        <LoginHeader>
          <h1>Kirjaudu sisään</h1>
          <p>Tervetuloa takaisin Asuntoanalyysiin</p>
        </LoginHeader>
        
        {error && (
          <FormError>
            <FiAlertCircle />
            <span>{error}</span>
          </FormError>
        )}
        
        <form onSubmit={handleSubmit(onSubmit)}>
          <FormGroup>
            <Label htmlFor="username">Käyttäjänimi</Label>
            <InputWrapper>
              <InputIcon>
                <FiUser />
              </InputIcon>
              <Input
                id="username"
                type="text"
                placeholder="Käyttäjänimesi"
                hasError={!!errors.username}
                {...register('username', { 
                  required: 'Käyttäjänimi on pakollinen' 
                })}
              />
            </InputWrapper>
            {errors.username && (
              <ErrorMessage>
                <FiAlertCircle />
                <span>{errors.username.message}</span>
              </ErrorMessage>
            )}
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="password">Salasana</Label>
            <InputWrapper>
              <InputIcon>
                <FiLock />
              </InputIcon>
              <Input
                id="password"
                type="password"
                placeholder="Salasanasi"
                hasError={!!errors.password}
                {...register('password', { 
                  required: 'Salasana on pakollinen' 
                })}
              />
            </InputWrapper>
            {errors.password && (
              <ErrorMessage>
                <FiAlertCircle />
                <span>{errors.password.message}</span>
              </ErrorMessage>
            )}
          </FormGroup>
          
          <RememberMeWrapper>
            <Checkbox 
              type="checkbox" 
              id="remember" 
              {...register('remember')} 
            />
            <Label htmlFor="remember" style={{ margin: 0 }}>Muista minut</Label>
          </RememberMeWrapper>
          
          <SubmitButton type="submit" disabled={loading}>
            {loading ? 'Kirjaudutaan...' : 'Kirjaudu sisään'}
          </SubmitButton>
          
          <ForgotPassword to="/forgot-password">
            Unohditko salasanasi?
          </ForgotPassword>
          
          <RegisterPrompt>
            Eikö sinulla ole vielä tiliä?{' '}
            <Link to="/register">Rekisteröidy</Link>
          </RegisterPrompt>
        </form>
      </LoginCard>
    </LoginContainer>
  );
};

export default Login; 