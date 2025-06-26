// src/components/LoginForm.js
import React, { useState } from 'react';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('authToken', data.token);
        // Redirect to dashboard
        window.location.href = '/dashboard';
      } else if (response.status === 401) {
        const body = await response.json();
        setError(body.message || 'Invalid email or password');
      } else {
        // handle other HTTP errors if needed
        setError('Login failed. Please try again.');
      }
    } catch (err) {
      // network errors, CORS issues, etc.
      setError('Network error. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} data-testid="login-form">
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
          data-testid="email-input"
        />
      </div>

      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={e => setPassword(e.target.value)}
          required
          data-testid="password-input"
        />
      </div>

      {error && (
        <div role="alert" data-testid="error-message">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        data-testid="login-button"
      >
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
