import React, { useState } from 'react';
import api from '../services/api';
import './Login.css';

const Login = ({ onLoginSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [pin, setPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await api.login(email, pin);
      
      if (response.success) {
        setSuccess('Login successful! Redirecting to biometric verification...');
        setTimeout(() => {
          onLoginSuccess(response.user);
        }, 1500);
      } else {
        setError(response.message);
      }
      setLoading(false);
    } catch (err) {
      setError('Login failed. Please try again.');
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    
    // Validate PINs match
    if (pin !== confirmPin) {
      setError('PINs do not match');
      return;
    }
    
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await api.register(email, pin);
      
      if (response.success) {
        setSuccess('Registration successful! Redirecting to biometric verification...');
        setTimeout(() => {
          onLoginSuccess(response.user);
        }, 1500);
      } else {
        setError(response.message);
      }
      setLoading(false);
    } catch (err) {
      setError('Registration failed. Please try again.');
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h2>{isLogin ? '🔐 Login to Your Account' : '✨ Create New Account'}</h2>
          <p className="login-subtitle">
            {isLogin 
              ? 'Enter your credentials to access the security dashboard' 
              : 'Set up your account for continuous behavioral authentication'}
          </p>
        </div>
        
        {error && <div className="error-message">⚠️ {error}</div>}
        {success && <div className="success-message">✅ {success}</div>}
        
        <form onSubmit={isLogin ? handleLogin : handleRegister}>
          <div className="form-group">
            <label htmlFor="email">📧 Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email address"
              required
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="pin">🔒 Security PIN</label>
            <input
              type="password"
              id="pin"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              placeholder="Enter your 6-digit PIN"
              required
              minLength="6"
              maxLength="6"
              disabled={loading}
            />
            <small className="form-hint">Must be exactly 6 digits for security</small>
          </div>
          
          {!isLogin && (
            <div className="form-group">
              <label htmlFor="confirmPin">🔒 Confirm PIN</label>
              <input
                type="password"
                id="confirmPin"
                value={confirmPin}
                onChange={(e) => setConfirmPin(e.target.value)}
                placeholder="Re-enter your PIN"
                required
                minLength="6"
                maxLength="6"
                disabled={loading}
              />
            </div>
          )}
          
          {isLogin && (
            <div className="form-group checkbox-group">
              <input
                type="checkbox"
                id="rememberMe"
                checked={rememberMe}
                onChange={(e) => setRememberMe(e.target.checked)}
                disabled={loading}
              />
              <label htmlFor="rememberMe">Remember me on this device</label>
            </div>
          )}
          
          <button type="submit" disabled={loading} className="submit-btn">
            {loading ? (
              <span>
                <span className="spinner"></span> Processing...
              </span>
            ) : (
              isLogin ? '🔓 Login to Dashboard' : '🚀 Create Account'
            )}
          </button>
        </form>
        
        <div className="toggle-form">
          <p>
            {isLogin ? "Don't have an account? " : "Already have an account? "}
            <button 
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setSuccess('');
              }} 
              className="toggle-btn"
              disabled={loading}
            >
              {isLogin ? 'Register Now' : 'Login Here'}
            </button>
          </p>
        </div>
        
        <div className="demo-credentials">
          <h4> демо Credentials</h4>
          <p>Email: <code>demo@example.com</code></p>
          <p>PIN: <code>123456</code></p>
        </div>
      </div>
    </div>
  );
};

export default Login;