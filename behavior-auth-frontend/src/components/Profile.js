import React, { useState, useEffect } from 'react';
import api from '../services/api';
import './Profile.css';

const Profile = ({ user }) => {
  const [currentPin, setCurrentPin] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmPin, setConfirmPin] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState(''); // success or error
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(false);

  const [securityOptions, setSecurityOptions] = useState({
    fastTypingDetection: true,
    tabSwitchingMonitoring: true,
    cameraBiometricMonitoring: true,
    microphoneAnalysis: false,
    applicationUsageTracking: true,
    mouseBehaviorAnalysis: true,
    locationTracking: true,
    desktopActivityMonitoring: true
  });

  // Fetch profile data from API
  useEffect(() => {
    const fetchProfileData = async () => {
      try {
        const response = await api.getProfileData(user.id);
        if (response.success) {
          setProfileData(response.data);
        }
      } catch (error) {
        console.error('Failed to fetch profile data:', error);
      }
    };

    fetchProfileData();
  }, [user.id]);

  const handlePinChange = async (e) => {
    e.preventDefault();
    
    if (!currentPin || !newPin || !confirmPin) {
      setMessage('❌ All fields are required');
      setMessageType('error');
      return;
    }
    
    if (newPin !== confirmPin) {
      setMessage('❌ New PINs do not match');
      setMessageType('error');
      return;
    }
    
    if (newPin.length < 6) {
      setMessage('❌ PIN must be at least 6 characters');
      setMessageType('error');
      return;
    }
    
    setLoading(true);
    setMessage('');
    
    try {
      const response = await api.changePin(user.id, currentPin, newPin);
      
      if (response.success) {
        setMessage('✅ PIN changed successfully');
        setMessageType('success');
        setCurrentPin('');
        setNewPin('');
        setConfirmPin('');
      } else {
        setMessage(`❌ ${response.message}`);
        setMessageType('error');
      }
    } catch (error) {
      setMessage('❌ Failed to change PIN. Please try again.');
      setMessageType('error');
    } finally {
      setLoading(false);
    }
  };

  const handleOptionChange = (option) => {
    setSecurityOptions(prev => ({
      ...prev,
      [option]: !prev[option]
    }));
  };

  const requestCameraPermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      stream.getTracks().forEach(track => track.stop());
      setMessage('✅ Camera permission granted successfully');
      setMessageType('success');
    } catch (error) {
      setMessage('❌ Camera permission denied. Please enable in browser settings.');
      setMessageType('error');
    }
  };

  const requestMicrophonePermission = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach(track => track.stop());
      setMessage('✅ Microphone permission granted successfully');
      setMessageType('success');
    } catch (error) {
      setMessage('❌ Microphone permission denied. Please enable in browser settings.');
      setMessageType('error');
    }
  };

  const requestLocationPermission = async () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setMessage('✅ Location permission granted successfully');
          setMessageType('success');
        },
        (error) => {
          setMessage('❌ Location permission denied. Please enable in browser settings.');
          setMessageType('error');
        }
      );
    } else {
      setMessage('❌ Geolocation is not supported by this browser.');
      setMessageType('error');
    }
  };

  return (
    <div className="profile-container">
      <div className="profile-header">
        <h1>👤 User Profile & Security Settings</h1>
        <p>Manage your account settings and security preferences</p>
      </div>

      <div className="profile-content">
        {/* Profile Information */}
        <div className="card profile-info-card">
          <h2>📋 Profile Information</h2>
          <div className="profile-info">
            <div className="info-item">
              <span className="label">📧 Email:</span>
              <span className="value">{profileData?.email || user?.email || 'user@example.com'}</span>
            </div>
            <div className="info-item">
              <span className="label">🆔 User ID:</span>
              <span className="value">{profileData?.userId || user?.id || 'USR-001'}</span>
            </div>
            <div className="info-item">
              <span className="label">📅 Registered:</span>
              <span className="value">{profileData?.registered || '2025-09-29'}</span>
            </div>
            <div className="info-item">
              <span className="label">🔒 Security Level:</span>
              <span className="value security-high">High</span>
            </div>
          </div>
        </div>

        {/* Permission Requests */}
        <div className="card permissions-card">
          <h2>🔐 Device Permissions</h2>
          <p>Grant necessary permissions for enhanced security monitoring</p>
          
          <div className="permissions-grid">
            <div className="permission-item">
              <button onClick={requestCameraPermission} className="permission-btn camera-btn">
                📷 Camera Access
              </button>
              <span className="permission-status granted">Granted</span>
            </div>
            
            <div className="permission-item">
              <button onClick={requestMicrophonePermission} className="permission-btn mic-btn">
                🎤 Microphone Access
              </button>
              <span className="permission-status denied">Denied</span>
            </div>
            
            <div className="permission-item">
              <button onClick={requestLocationPermission} className="permission-btn location-btn">
                📍 Location Access
              </button>
              <span className="permission-status pending">Pending</span>
            </div>
            
            <div className="permission-item">
              <button className="permission-btn desktop-btn">
                🖥️ Desktop Monitoring
              </button>
              <span className="permission-status granted">Granted</span>
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="card security-settings-card">
          <h2>🛡️ Security Monitoring Options</h2>
          <p>Customize which behavioral patterns to monitor for authentication</p>
          
          <div className="security-options">
            {Object.entries(securityOptions).map(([key, value]) => (
              <div key={key} className="option-item">
                <input
                  type="checkbox"
                  id={key}
                  checked={value}
                  onChange={() => handleOptionChange(key)}
                />
                <label htmlFor={key}>
                  {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </label>
              </div>
            ))}
          </div>
          
          <div className="security-summary">
            <h3>📊 Current Security Status</h3>
            <div className="status-bars">
              <div className="status-bar">
                <span className="status-label">Behavioral Analysis</span>
                <div className="status-progress">
                  <div className="status-fill" style={{ width: '92%' }}></div>
                </div>
                <span className="status-value">92%</span>
              </div>
              <div className="status-bar">
                <span className="status-label">Anomaly Detection</span>
                <div className="status-progress">
                  <div className="status-fill" style={{ width: '87%' }}></div>
                </div>
                <span className="status-value">87%</span>
              </div>
              <div className="status-bar">
                <span className="status-label">False Positives</span>
                <div className="status-progress reverse">
                  <div className="status-fill" style={{ width: '8%' }}></div>
                </div>
                <span className="status-value">8%</span>
              </div>
            </div>
          </div>
        </div>

        {/* Change PIN */}
        <div className="card pin-change-card">
          <h2>🔑 Change Security PIN</h2>
          <p>Update your PIN for enhanced account security</p>
          
          <form onSubmit={handlePinChange}>
            <div className="form-group">
              <label htmlFor="currentPin">🔒 Current PIN:</label>
              <input
                type="password"
                id="currentPin"
                value={currentPin}
                onChange={(e) => setCurrentPin(e.target.value)}
                placeholder="Enter current 6-digit PIN"
                minLength="6"
                maxLength="6"
                disabled={loading}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="newPin">🆕 New PIN:</label>
              <input
                type="password"
                id="newPin"
                value={newPin}
                onChange={(e) => setNewPin(e.target.value)}
                placeholder="Enter new 6-digit PIN"
                minLength="6"
                maxLength="6"
                disabled={loading}
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="confirmPin">✅ Confirm New PIN:</label>
              <input
                type="password"
                id="confirmPin"
                value={confirmPin}
                onChange={(e) => setConfirmPin(e.target.value)}
                placeholder="Re-enter new PIN"
                minLength="6"
                maxLength="6"
                disabled={loading}
              />
            </div>
            
            <button type="submit" disabled={loading} className="submit-btn">
              {loading ? '🔄 Updating PIN...' : '💾 Save New PIN'}
            </button>
            
            {message && (
              <div className={`message ${messageType}`}>
                {message}
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default Profile;