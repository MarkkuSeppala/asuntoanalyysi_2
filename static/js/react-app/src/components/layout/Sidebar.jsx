import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { FiHome, FiPlusCircle, FiList, FiBarChart2, FiSettings } from 'react-icons/fi';
import { BiBuildingHouse } from 'react-icons/bi';

const SidebarContainer = styled.aside`
  width: 250px;
  background-color: white;
  border-right: 1px solid var(--gray-200);
  height: calc(100vh - 80px);
  position: sticky;
  top: 80px;
  
  @media (max-width: 992px) {
    display: none;
  }
`;

const SidebarContent = styled.div`
  padding: 2rem 0;
`;

const SidebarHeader = styled.div`
  padding: 0 1.5rem 1.5rem;
  border-bottom: 1px solid var(--gray-200);
  margin-bottom: 1.5rem;
`;

const SidebarTitle = styled.h4`
  font-size: 0.9rem;
  color: var(--gray-600);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 0;
`;

const NavMenu = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`;

const NavItem = styled.li`
  margin-bottom: 0.5rem;
`;

const NavItemLink = styled(Link)`
  display: flex;
  align-items: center;
  padding: 0.75rem 1.5rem;
  color: ${props => props.active ? 'var(--primary)' : 'var(--gray-700)'};
  background-color: ${props => props.active ? 'var(--gray-100)' : 'transparent'};
  border-left: 4px solid ${props => props.active ? 'var(--primary)' : 'transparent'};
  font-weight: ${props => props.active ? '500' : 'normal'};
  transition: var(--transition);
  
  &:hover {
    background-color: var(--gray-100);
    color: var(--primary);
  }
  
  svg {
    margin-right: 0.75rem;
    font-size: 1.2rem;
  }
`;

const SidebarFooter = styled.div`
  padding: 1.5rem;
  border-top: 1px solid var(--gray-200);
  margin-top: auto;
  position: absolute;
  bottom: 0;
  width: 100%;
`;

const PromoBadge = styled.div`
  background-color: var(--secondary-light);
  color: var(--primary-dark);
  padding: 1rem;
  border-radius: var(--border-radius);
  font-size: 0.9rem;
  
  h5 {
    font-size: 1rem;
    margin-bottom: 0.5rem;
  }
  
  p {
    margin-bottom: 0.5rem;
  }
`;

const Sidebar = () => {
  const location = useLocation();
  
  // Tarkistaa onko tämä reitti aktiivinen
  const isActive = (path) => location.pathname === path;
  
  return (
    <SidebarContainer>
      <SidebarContent>
        <SidebarHeader>
          <SidebarTitle>Kiinteistön analyysi</SidebarTitle>
        </SidebarHeader>
        
        <NavMenu>
          <NavItem>
            <NavItemLink to="/dashboard" active={isActive('/dashboard')}>
              <FiHome /> Etusivu
            </NavItemLink>
          </NavItem>
          <NavItem>
            <NavItemLink to="/new-analysis" active={isActive('/new-analysis')}>
              <FiPlusCircle /> Uusi analyysi
            </NavItemLink>
          </NavItem>
          <NavItem>
            <NavItemLink to="/analyses" active={isActive('/analyses')}>
              <FiList /> Omat analyysit
            </NavItemLink>
          </NavItem>
        </NavMenu>
        
        <SidebarHeader style={{ marginTop: '2rem' }}>
          <SidebarTitle>Työkalut</SidebarTitle>
        </SidebarHeader>
        
        <NavMenu>
          <NavItem>
            <NavItemLink to="/market-trends" active={isActive('/market-trends')}>
              <FiBarChart2 /> Markkinatrendit
            </NavItemLink>
          </NavItem>
          <NavItem>
            <NavItemLink to="/property-comparison" active={isActive('/property-comparison')}>
              <BiBuildingHouse /> Vertailutyökalu
            </NavItemLink>
          </NavItem>
        </NavMenu>
        
        <SidebarFooter>
          <PromoBadge>
            <h5>Asuntoanalyysi Pro</h5>
            <p>Saa käyttöösi lisäominaisuudet ja rajaton määrä analyyseja.</p>
            <Link to="/upgrade" className="button secondary" style={{fontSize: '0.8rem', padding: '0.5rem 1rem'}}>
              Päivitä nyt
            </Link>
          </PromoBadge>
        </SidebarFooter>
      </SidebarContent>
    </SidebarContainer>
  );
};

export default Sidebar; 