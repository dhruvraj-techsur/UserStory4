import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import styles from './ThemeToggle.module.css';

const ThemeToggle = () => {
  const [theme, setTheme] = useState(() => {
    const localTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    return localTheme || (systemPrefersDark ? 'dark' : 'light');
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  useEffect(() => {
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <button 
      onClick={toggleTheme} 
      className={styles.toggleButton}
      aria-label="Toggle dark and light mode"
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