import React from 'react';
import ThemeToggle from './components/ThemeToggle';
import './App.css';

const App = () => {
  return (
    <div className="App">
      <ThemeToggle />
      <h1>Welcome to the React UI</h1>
      <p>This is a basic app with dark mode support.</p>
    </div>
  );
};

export default App;