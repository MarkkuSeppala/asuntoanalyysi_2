import React from 'react';
import { Link } from 'react-router-dom';
import styled from 'styled-components';
import { FiMail, FiInstagram, FiTwitter, FiFacebook, FiLinkedin } from 'react-icons/fi';

const FooterContainer = styled.footer`
  background-color: var(--gray-800);
  color: var(--gray-300);
  padding: 3rem 0 1.5rem;
  margin-top: auto;
`;

const FooterContent = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 2rem;
  
  @media (max-width: 992px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: 576px) {
    grid-template-columns: 1fr;
  }
`;

const FooterColumn = styled.div`
  h4 {
    color: white;
    margin-bottom: 1.5rem;
    font-family: var(--font-family-sans);
    font-size: 1.2rem;
  }
  
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  li {
    margin-bottom: 0.75rem;
  }
  
  a {
    color: var(--gray-400);
    transition: var(--transition);
    
    &:hover {
      color: white;
    }
  }
`;

const FooterLogo = styled(Link)`
  display: flex;
  align-items: center;
  font-family: var(--font-family-serif);
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
  margin-bottom: 1rem;
  
  span {
    color: var(--secondary);
  }
`;

const FooterBottom = styled.div`
  border-top: 1px solid var(--gray-700);
  margin-top: 2rem;
  padding-top: 1.5rem;
  display: flex;
  justify-content: space-between;
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: center;
    text-align: center;
    
    p {
      margin-bottom: 1rem;
    }
  }
`;

const SocialLinks = styled.div`
  display: flex;
  gap: 1rem;
  
  a {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background-color: var(--gray-700);
    color: white;
    transition: var(--transition);
    
    &:hover {
      background-color: var(--primary);
    }
  }
`;

const ContactInfo = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
  
  svg {
    margin-right: 0.5rem;
  }
`;

const Footer = () => {
  const currentYear = new Date().getFullYear();
  
  return (
    <FooterContainer>
      <div className="container">
        <FooterContent>
          <FooterColumn>
            <FooterLogo to="/">
              <span>Asunto</span>analyysi
            </FooterLogo>
            <p>Älykkäitä kiinteistöanalyyseja ammattilaisten ja kuluttajien käyttöön.</p>
            <ContactInfo>
              <FiMail /> info@asuntoanalyysi.fi
            </ContactInfo>
          </FooterColumn>
          
          <FooterColumn>
            <h4>Palvelut</h4>
            <ul>
              <li><Link to="/about">Tietoa palvelusta</Link></li>
              <li><Link to="/pricing">Hinnoittelu</Link></li>
              <li><Link to="/for-professionals">Ammattilaisille</Link></li>
              <li><Link to="/market-data">Markkinadata</Link></li>
            </ul>
          </FooterColumn>
          
          <FooterColumn>
            <h4>Käyttäjälle</h4>
            <ul>
              <li><Link to="/faq">Usein kysytyt kysymykset</Link></li>
              <li><Link to="/contact">Ota yhteyttä</Link></li>
              <li><Link to="/blog">Blogi</Link></li>
              <li><Link to="/help">Tukikeskus</Link></li>
            </ul>
          </FooterColumn>
          
          <FooterColumn>
            <h4>Laillisuus</h4>
            <ul>
              <li><Link to="/terms">Käyttöehdot</Link></li>
              <li><Link to="/privacy">Tietosuojaseloste</Link></li>
              <li><Link to="/cookies">Evästekäytäntö</Link></li>
            </ul>
          </FooterColumn>
        </FooterContent>
        
        <FooterBottom>
          <p>&copy; {currentYear} Asuntoanalyysi. Kaikki oikeudet pidätetään.</p>
          
          <SocialLinks>
            <a href="https://facebook.com" target="_blank" rel="noopener noreferrer">
              <FiFacebook />
            </a>
            <a href="https://twitter.com" target="_blank" rel="noopener noreferrer">
              <FiTwitter />
            </a>
            <a href="https://instagram.com" target="_blank" rel="noopener noreferrer">
              <FiInstagram />
            </a>
            <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer">
              <FiLinkedin />
            </a>
          </SocialLinks>
        </FooterBottom>
      </div>
    </FooterContainer>
  );
};

export default Footer; 