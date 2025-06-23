import React, { useEffect, useState } from 'react';
import './ThemeToggle.css';

const ThemeToggle = () => {
  const [theme, setTheme] = useState(() => {
    const savedTheme = typeof window.localStorage !== 'undefined' ? localStorage.getItem('theme') : null;
    return savedTheme || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    if (typeof window.localStorage !== 'undefined') {
      localStorage.setItem('theme', theme);
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <button onClick={toggleTheme} className="theme-toggle" role="switch">
      {theme === 'light' ? 'Activate Dark Mode' : 'Activate Light Mode'}
    </button>
  );
};

export default ThemeToggle;