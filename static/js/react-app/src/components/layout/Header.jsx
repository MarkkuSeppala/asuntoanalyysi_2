import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { FiHome, FiUser, FiLogOut, FiMenu, FiX } from 'react-icons/fi';
import { logout } from '../../services/authService';

const HeaderContainer = styled.header`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  background-color: white;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
`;

const HeaderContent = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  height: 80px;
`;

const Logo = styled(Link)`
  display: flex;
  align-items: center;
  font-family: var(--font-family-serif);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
  
  span {
    color: var(--secondary);
  }
`;

const LogoImage = styled.img`
  height: 40px;
  margin-right: 10px;
`;

const Nav = styled.nav`
  display: flex;
  align-items: center;
  
  @media (max-width: 768px) {
    display: ${({ isOpen }) => (isOpen ? 'flex' : 'none')};
    flex-direction: column;
    position: fixed;
    top: 80px;
    left: 0;
    width: 100%;
    height: calc(100vh - 80px);
    background-color: white;
    padding: 2rem;
    z-index: 999;
  }
`;

const NavLink = styled(Link)`
  display: flex;
  align-items: center;
  margin-left: 1.5rem;
  font-weight: 500;
  color: var(--gray-700);
  
  &:hover {
    color: var(--primary);
  }
  
  svg {
    margin-right: 0.5rem;
  }
  
  @media (max-width: 768px) {
    margin: 1rem 0;
    font-size: 1.2rem;
  }
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  margin-left: 1.5rem;
  
  @media (max-width: 768px) {
    margin: 1rem 0;
  }
`;

const UserAvatar = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: var(--primary);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  margin-right: 0.5rem;
`;

const MenuButton = styled.button`
  display: none;
  background: none;
  border: none;
  color: var(--gray-700);
  font-size: 1.5rem;
  cursor: pointer;
  
  @media (max-width: 768px) {
    display: block;
  }
`;

const LogoutButton = styled.button`
  display: flex;
  align-items: center;
  background: none;
  border: none;
  color: var(--gray-700);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  padding: 0;
  margin-left: 1.5rem;
  
  &:hover {
    color: var(--danger);
  }
  
  svg {
    margin-right: 0.5rem;
  }
  
  @media (max-width: 768px) {
    margin: 1rem 0;
    font-size: 1.2rem;
  }
`;

const Header = ({ user, setUser }) => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const navigate = useNavigate();
  
  const handleLogout = async () => {
    try {
      await logout();
      setUser(null);
      navigate('/login');
    } catch (error) {
      console.error('Logout failed', error);
    }
  };
  
  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };
  
  const getInitials = (name) => {
    if (!name) return '?';
    return name.charAt(0).toUpperCase();
  };
  
  return (
    <HeaderContainer>
      <div className="container">
        <HeaderContent>
          <Logo to="/">
            <span>Asunto</span>analyysi
          </Logo>
          
          <MenuButton onClick={toggleMenu}>
            {isMenuOpen ? <FiX /> : <FiMenu />}
          </MenuButton>
          
          <Nav isOpen={isMenuOpen}>
            {user ? (
              <>
                <NavLink to="/dashboard">
                  <FiHome /> Etusivu
                </NavLink>
                <NavLink to="/new-analysis">
                  Uusi analyysi
                </NavLink>
                <NavLink to="/analyses">
                  Analyysit
                </NavLink>
                
                <UserInfo>
                  <UserAvatar>{getInitials(user.username)}</UserAvatar>
                  <span>{user.username}</span>
                </UserInfo>
                
                <LogoutButton onClick={handleLogout}>
                  <FiLogOut /> Kirjaudu ulos
                </LogoutButton>
              </>
            ) : (
              <>
                <NavLink to="/login">Kirjaudu</NavLink>
                <NavLink to="/register">Rekisteröidy</NavLink>
              </>
            )}
          </Nav>
        </HeaderContent>
      </div>
    </HeaderContainer>
  );
};

export default Header; 