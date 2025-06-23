import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';

export default function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const history = useHistory();

  const loginUser = async () => {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    return response;
  };

  useEffect(() => {
    const submitForm = async () => {
      setLoading(true);
      setError('');
      try {
        const response = await loginUser();
        if (response.ok) {
          const data = await response.json();
          localStorage.setItem('authToken', data.token);
          history.push('/dashboard');
        } else {
          const errorData = await response.json();
          setError(errorData.message || 'Login failed');
        }
      } catch (err) {
        setError('Network error. Please try again.');
      } finally {
        setLoading(false);
      }
    };
    submitForm();
  }, [email, password]);

  return (
    <form onSubmit={(e) => e.preventDefault()} disabled={loading}>
      <h2>Login</h2>
      
      {error && <div style={{ color: 'red', marginBottom: '10px' }}>{error}</div>}
      
      <div>
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
          disabled={loading}
        />
      </div>
      
      <div>
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
        />
      </div>
      
      <button type="submit" disabled={loading}>
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}