import React, { useState, useEffect } from 'react';
import './App.css';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import BaselineTraining from './components/BaselineTraining';
import Profile from './components/Profile';
import BiometricVerification from './components/BiometricVerification';

function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeView, setActiveView] = useState('login'); // login, dashboard, baseline, profile, biometric
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // Handle successful login
  const handleLoginSuccess = (user) => {
    console.log(`🟢 User logged in: ${user.email}`);
    setCurrentUser(user);
    setIsAuthenticated(true);
    setActiveView('biometric'); // Redirect to biometric verification after login
  };

  // Handle logout
  const handleLogout = () => {
    console.log(`🔴 User logged out: ${currentUser?.email}`);
    setCurrentUser(null);
    setIsAuthenticated(false);
    setActiveView('login');
  };

  // Handle biometric verification completion
  const handleBiometricComplete = () => {
    setActiveView('baseline'); // Redirect to baseline training after biometric verification
  };

  // Render the appropriate view based on state
  const renderView = () => {
    switch (activeView) {
      case 'login':
        return <Login onLoginSuccess={handleLoginSuccess} />;
      case 'biometric':
        return <BiometricVerification userId={currentUser?.id} onComplete={handleBiometricComplete} />;
      case 'dashboard':
        return <Dashboard user={currentUser} onLogout={handleLogout} />;
      case 'baseline':
        return <BaselineTraining user={currentUser} onComplete={() => setActiveView('dashboard')} />;
      case 'profile':
        return <Profile user={currentUser} />;
      default:
        return <Login onLoginSuccess={handleLoginSuccess} />;
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🔒 Smart Behavior Authentication System</h1>
        {isAuthenticated && activeView !== 'login' && activeView !== 'biometric' && (
          <nav className="main-nav">
            <button onClick={() => setActiveView('dashboard')}>Dashboard</button>
            <button onClick={() => setActiveView('profile')}>Profile</button>
            <button onClick={handleLogout}>Logout</button>
          </nav>
        )}
      </header>
      <main className="App-main">
        {renderView()}
      </main>
    </div>
  );
}

export default App;