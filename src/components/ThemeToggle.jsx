import React, { useEffect, useState } from 'react';
import PropTypes from 'prop-types';
import './ThemeToggle.css';

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
    <button onClick={toggleTheme} className="theme-toggle">
      Switch to {theme === 'light' ? 'Dark' : 'Light'} Mode
    </button>
  );
};

ThemeToggle.propTypes = {
  theme: PropTypes.string.isRequired,
  setTheme: PropTypes.func.isRequired,
};

export default ThemeToggle;