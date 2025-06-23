import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import styles from './ThemeToggle.module.css';

const ThemeToggle = () => {
  const [theme, setTheme] = useState(() => {
    const localTheme = localStorage.getItem('theme');
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    return localTheme || systemTheme || 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <button 
      onClick={toggleTheme} 
      className={styles.toggleButton} 
      aria-label="Switch theme"
    >
      Switch to {theme === 'light' ? 'Dark' : 'Light'} Mode
    </button>
  );
};

ThemeToggle.propTypes = {
  theme: PropTypes.string.isRequired,
  setTheme: PropTypes.func.isRequired,
};

export default ThemeToggle;