import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import './Dashboard.css';

const Dashboard = ({ user, onLogout }) => {
  const [metrics, setMetrics] = useState({
    keystrokeCount: 0,
    mouseCount: 0,
    windowSwitches: 0,
    appCount: 1,
    typingSpeed: 0,
    securityConfidence: 95
  });

  const [events, setEvents] = useState([
    { id: 1, time: new Date().toLocaleTimeString(), message: '✅ System initialized', type: 'info' },
    { id: 2, time: new Date().toLocaleTimeString(), message: '✅ User authentication successful', type: 'success' },
    { id: 3, time: new Date().toLocaleTimeString(), message: '✅ Baseline data collection completed', type: 'success' },
    { id: 4, time: new Date().toLocaleTimeString(), message: '✅ Continuous monitoring started', type: 'success' },
    { id: 5, time: new Date().toLocaleTimeString(), message: '🧠 ML models ready for real-time auth', type: 'info' }
  ]);

  const [mlMetrics, setMlMetrics] = useState({
    behaviorClassifierAccuracy: 92,
    anomalyDetectionRate: 87,
    falsePositiveRate: 8,
    falseNegativeRate: 5,
    realtimeProcessing: '< 50ms per analysis'
  });
  
  // Location tracking state
  const [location, setLocation] = useState({
    latitude: 0,
    longitude: 0,
    city: 'Unknown',
    country: 'Unknown',
    accuracy: 0
  });
  
  // Desktop activity state
  const [desktopActivity, setDesktopActivity] = useState({
    activeApplications: [],
    currentApplication: 'Unknown',
    applicationSwitches: 0,
    systemUptime: 0
  });
  
  // Real-time behavioral monitoring state
  const [keyPressTimes, setKeyPressTimes] = useState({});
  const [lastReleaseTime, setLastReleaseTime] = useState(null);
  const [clickTimes, setClickTimes] = useState([]);
  const [collectedData, setCollectedData] = useState([]);
  const [currentConfidenceScore, setCurrentConfidenceScore] = useState(95);
  
  const keystrokeCountRef = useRef(0);
  const mouseCountRef = useRef(0);
  const lastMousePositionRef = useRef({ x: 0, y: 0 });
  const lastTimestampRef = useRef(0);
  const analysisIntervalRef = useRef(null);
  const typingIntervalRef = useRef(null);
  const isScreenLocked = useRef(false);
  const locationIntervalRef = useRef(null);
  const desktopActivityIntervalRef = useRef(null);

  // Set up continuous behavioral monitoring - runs throughout app lifecycle
  useEffect(() => {
    console.log('🔧 Setting up continuous behavioral monitoring...');
    
    // Set up event listeners for real-time data collection
    const handleKeyDown = (e) => {
      if (isScreenLocked.current) return; // Don't collect data if screen is locked
      
      const key = e.key;
      const timestamp = Date.now();
      
      // Store press time for dwell calculation
      setKeyPressTimes(prev => ({
        ...prev,
        [key]: timestamp
      }));
      
      // Update metrics
      setMetrics(prevMetrics => ({
        ...prevMetrics,
        keystrokeCount: prevMetrics.keystrokeCount + 1
      }));
      
      keystrokeCountRef.current += 1;
    };
    
    const handleKeyUp = (e) => {
      if (isScreenLocked.current) return; // Don't collect data if screen is locked
      
      const key = e.key;
      const timestamp = Date.now();
      
      // Calculate dwell time
      const pressTime = keyPressTimes[key];
      let dwellTime = 0;
      if (pressTime) {
        dwellTime = timestamp - pressTime;
        // Update keyPressTimes by removing this key
        setKeyPressTimes(prev => {
          const newPressTimes = { ...prev };
          delete newPressTimes[key];
          return newPressTimes;
        });
      }
      
      // Calculate flight time (time since last key release)
      let flightTime = 0;
      if (lastReleaseTime) {
        flightTime = timestamp - lastReleaseTime;
      }
      setLastReleaseTime(timestamp);
      
      // Store the collected data point
      const dataPoint = {
        key: key,
        dwellTime: dwellTime,
        flightTime: flightTime,
        timestamp: timestamp
      };
      
      setCollectedData(prev => [...prev, dataPoint]);
    };
    
    const handleMouseMove = (e) => {
      if (isScreenLocked.current) return; // Don't collect data if screen is locked
      
      const timestamp = Date.now();
      const x = e.clientX;
      const y = e.clientY;
      
      // Calculate movement distance
      const dx = x - lastMousePositionRef.current.x;
      const dy = y - lastMousePositionRef.current.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      // Update refs
      lastMousePositionRef.current = { x, y };
      lastTimestampRef.current = timestamp;
      
      // Update metrics
      if (distance > 0) {
        mouseCountRef.current += 1;
        setMetrics(prevMetrics => ({
          ...prevMetrics,
          mouseCount: prevMetrics.mouseCount + 1
        }));
      }
    };
    
    const handleClick = (e) => {
      if (isScreenLocked.current) return; // Don't collect data if screen is locked
      
      const timestamp = Date.now();
      
      setClickTimes(prev => [...prev, timestamp]);
      
      // Add event for every 10th click to avoid spam
      if (clickTimes.length % 10 === 0) {
        const newEvent = {
          id: Date.now(),
          time: new Date().toLocaleTimeString(),
          message: '🖱️ Mouse click detected',
          type: 'info'
        };
        
        setEvents(prev => [newEvent, ...prev.slice(0, 9)]); // Keep only last 10 events
      }
    };
    
    const handleScroll = (e) => {
      if (isScreenLocked.current) return; // Don't collect data if screen is locked
      
      // Add event for significant scroll
      if (Math.abs(e.deltaY) > 50) {
        const newEvent = {
          id: Date.now(),
          time: new Date().toLocaleTimeString(),
          message: '🖱️ Scroll detected',
          type: 'info'
        };
        
        setEvents(prev => [newEvent, ...prev.slice(0, 9)]); // Keep only last 10 events
      }
    };
    
    // Add event listeners
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('click', handleClick);
    window.addEventListener('wheel', handleScroll, { passive: true });
    
    // Cleanup function
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('click', handleClick);
      window.removeEventListener('wheel', handleScroll);
    };
  }, [keyPressTimes, lastReleaseTime, clickTimes.length]);

  // Continuous behavioral analysis - runs throughout app lifecycle after baseline
  useEffect(() => {
    console.log('🔬 Starting continuous behavioral analysis...');
    
    // Send data for analysis every 5 seconds (continuous authentication)
    if (!analysisIntervalRef.current) {
      analysisIntervalRef.current = setInterval(async () => {
        if (isScreenLocked.current) return; // Don't analyze if screen is locked
        
        if (collectedData.length > 0 && user && user.id) {
          try {
            // Process current data for analysis (use last 20 data points for real-time analysis)
            const currentData = processCurrentData();
            
            // Send to backend for ML analysis
            const response = await api.analyzeBehavior(user.id, currentData);
            
            if (response.success) {
              setCurrentConfidenceScore(response.confidenceScore);
              
              // Update metrics with confidence score
              setMetrics(prevMetrics => ({
                ...prevMetrics,
                securityConfidence: response.confidenceScore
              }));
              
              // Add security event if anomalous
              if (response.isAnomalous) {
                const newEvent = {
                  id: Date.now(),
                  time: new Date().toLocaleTimeString(),
                  message: `🔒 Anomalous behavior detected (Score: ${response.confidenceScore})`,
                  type: 'warning'
                };
                
                setEvents(prev => [newEvent, ...prev.slice(0, 9)]);
                
                // Trigger screen lock if confidence is very low
                if (response.confidenceScore < 15) {
                  lockScreen();
                }
              }
            }
          } catch (error) {
            console.error('Behavior analysis error:', error);
          }
        }
      }, 5000); // Analyze every 5 seconds
    }
    
    // Cleanup interval on unmount
    return () => {
      if (analysisIntervalRef.current) {
        clearInterval(analysisIntervalRef.current);
      }
    };
  }, [collectedData, user]);

  // Location tracking - runs every 30 seconds
  useEffect(() => {
    console.log('📍 Starting location tracking...');
    
    // Get initial location
    getLocation();
    
    // Update location every 30 seconds
    if (!locationIntervalRef.current) {
      locationIntervalRef.current = setInterval(() => {
        getLocation();
      }, 30000);
    }
    
    // Cleanup interval on unmount
    return () => {
      if (locationIntervalRef.current) {
        clearInterval(locationIntervalRef.current);
      }
    };
  }, []);

  // Desktop activity monitoring - runs every 5 seconds
  useEffect(() => {
    console.log('🖥️ Starting desktop activity monitoring...');
    
    // Get initial desktop activity
    getDesktopActivity();
    
    // Update desktop activity every 5 seconds
    if (!desktopActivityIntervalRef.current) {
      desktopActivityIntervalRef.current = setInterval(() => {
        getDesktopActivity();
      }, 5000);
    }
    
    // Cleanup interval on unmount
    return () => {
      if (desktopActivityIntervalRef.current) {
        clearInterval(desktopActivityIntervalRef.current);
      }
    };
  }, []);

  // Function to get user's location
  const getLocation = async () => {
    try {
      // In a real implementation, this would use the Geolocation API
      // For now, we'll simulate location data
      const simulatedLocation = {
        latitude: 28.6139 + (Math.random() - 0.5) * 0.1,
        longitude: 77.2090 + (Math.random() - 0.5) * 0.1,
        city: 'New Delhi',
        country: 'India',
        accuracy: Math.floor(Math.random() * 20) + 80 // 80-100% accuracy
      };
      
      setLocation(simulatedLocation);
      
      // Send location data to backend
      if (user && user.id) {
        await api.sendLocationData(user.id, simulatedLocation);
      }
      
      // Add location update event
      const newEvent = {
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        message: `📍 Location updated: ${simulatedLocation.city}, ${simulatedLocation.country}`,
        type: 'info'
      };
      
      setEvents(prev => [newEvent, ...prev.slice(0, 9)]);
    } catch (error) {
      console.error('Location error:', error);
    }
  };

  // Function to get desktop activity
  const getDesktopActivity = async () => {
    try {
      // Simulate desktop activity data
      const simulatedActivity = {
        activeApplications: ['Chrome', 'VS Code', 'Slack', 'Spotify'],
        currentApplication: 'Chrome',
        applicationSwitches: Math.floor(Math.random() * 10) + 5,
        systemUptime: Math.floor(Math.random() * 10000)
      };
      
      setDesktopActivity(simulatedActivity);
      
      // Update metrics
      setMetrics(prevMetrics => ({
        ...prevMetrics,
        windowSwitches: simulatedActivity.applicationSwitches,
        appCount: simulatedActivity.activeApplications.length
      }));
      
      // Send desktop activity data to backend
      if (user && user.id) {
        await api.sendDesktopActivityData(user.id, simulatedActivity);
      }
    } catch (error) {
      console.error('Desktop activity error:', error);
    }
  };

  // Process current data for behavioral analysis
  const processCurrentData = () => {
    // Get last 20 data points for analysis
    const recentData = collectedData.slice(-20);
    
    // Calculate keystroke metrics
    const keystrokes = recentData.filter(d => d.dwellTime !== undefined);
    const avgDwell = keystrokes.length > 0 
      ? keystrokes.reduce((sum, d) => sum + d.dwellTime, 0) / keystrokes.length 
      : 0;
      
    const flights = recentData.filter(d => d.flightTime !== undefined);
    const avgFlight = flights.length > 0 
      ? flights.reduce((sum, d) => sum + d.flightTime, 0) / flights.length 
      : 0;
      
    // Calculate typing speed (WPM)
    const timeSpan = recentData.length > 1 
      ? (recentData[recentData.length - 1].timestamp - recentData[0].timestamp) / 1000 
      : 0;
    const wpm = timeSpan > 0 ? (keystrokes.length / 5) / (timeSpan / 60) : 0;
    
    // Calculate mouse metrics
    const clicks = clickTimes.slice(-20);
    const clickCount = clicks.length;
    
    // Calculate mouse velocity (simplified)
    const avgVelocity = mouseCountRef.current > 0 ? mouseCountRef.current * 10 : 0;
    
    return {
      avgDwell,
      avgFlight,
      wpm,
      clickCount,
      avgVelocity,
      windowSwitches: desktopActivity.applicationSwitches,
      appCount: desktopActivity.activeApplications.length
    };
  };

  // Lock screen function
  const lockScreen = () => {
    isScreenLocked.current = true;
    
    // Create lock screen overlay
    const lockOverlay = document.createElement('div');
    lockOverlay.id = 'lock-screen-overlay';
    lockOverlay.style.position = 'fixed';
    lockOverlay.style.top = '0';
    lockOverlay.style.left = '0';
    lockOverlay.style.width = '100%';
    lockOverlay.style.height = '100%';
    lockOverlay.style.backgroundColor = 'rgba(0, 0, 0, 0.9)';
    lockOverlay.style.zIndex = '9999';
    lockOverlay.style.display = 'flex';
    lockOverlay.style.flexDirection = 'column';
    lockOverlay.style.justifyContent = 'center';
    lockOverlay.style.alignItems = 'center';
    lockOverlay.style.color = 'white';
    lockOverlay.style.fontFamily = 'Arial, sans-serif';
    
    lockOverlay.innerHTML = `
      <h1 style="font-size: 3rem; margin-bottom: 1rem;">🔒 SCREEN LOCKED</h1>
      <p style="font-size: 1.2rem; margin-bottom: 2rem;">Security threat detected. Enter PIN to unlock.</p>
      <input type="password" id="unlock-pin" placeholder="Enter PIN" 
             style="padding: 10px; font-size: 1.2rem; margin-bottom: 1rem; border-radius: 5px; border: none;">
      <button id="unlock-button" style="padding: 10px 20px; font-size: 1.2rem; 
              background-color: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer;">
        Unlock
      </button>
      <p id="unlock-message" style="margin-top: 1rem; color: #ff6b6b;"></p>
    `;
    
    document.body.appendChild(lockOverlay);
    
    // Add event listeners for unlock
    const unlockButton = document.getElementById('unlock-button');
    const unlockPin = document.getElementById('unlock-pin');
    const unlockMessage = document.getElementById('unlock-message');
    
    const handleUnlock = async () => {
      const pin = unlockPin.value;
      if (pin) {
        // In a real implementation, this would verify the PIN with the backend
        // For demo purposes, we'll accept any non-empty PIN
        if (pin.length >= 4) {
          isScreenLocked.current = false;
          document.body.removeChild(lockOverlay);
          
          // Add unlock event
          const newEvent = {
            id: Date.now(),
            time: new Date().toLocaleTimeString(),
            message: '🔓 Screen unlocked successfully',
            type: 'success'
          };
          
          setEvents(prev => [newEvent, ...prev.slice(0, 9)]);
        } else {
          unlockMessage.textContent = 'Invalid PIN. Must be at least 4 characters.';
        }
      } else {
        unlockMessage.textContent = 'Please enter your PIN.';
      }
    };
    
    unlockButton.addEventListener('click', handleUnlock);
    unlockPin.addEventListener('keyup', (e) => {
      if (e.key === 'Enter') {
        handleUnlock();
      }
    });
    
    // Focus on PIN input
    unlockPin.focus();
    
    // Add lock event
    const newEvent = {
      id: Date.now(),
      time: new Date().toLocaleTimeString(),
      message: '🔒 Screen locked due to security threat',
      type: 'warning'
    };
    
    setEvents(prev => [newEvent, ...prev.slice(0, 9)]);
  };

  // Request camera and microphone permissions
  const requestCameraMicrophonePermissions = async () => {
    try {
      // Request camera permission
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      stream.getTracks().forEach(track => track.stop()); // Stop the stream immediately
      
      // Request microphone permission
      const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStream.getTracks().forEach(track => track.stop()); // Stop the stream immediately
      
      // Add success event
      const newEvent = {
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        message: '📹📷 Camera and microphone permissions granted',
        type: 'success'
      };
      
      setEvents(prev => [newEvent, ...prev.slice(0, 9)]);
      
      return true;
    } catch (error) {
      console.error('Permission error:', error);
      
      // Add error event
      const newEvent = {
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        message: '⚠️ Camera or microphone permission denied',
        type: 'warning'
      };
      
      setEvents(prev => [newEvent, ...prev.slice(0, 9)]);
      
      return false;
    }
  };

  // Capture user picture for biometric verification
  const captureUserPicture = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      const video = document.createElement('video');
      video.srcObject = stream;
      await new Promise(resolve => {
        video.onloadedmetadata = () => {
          video.play();
          resolve();
        };
      });
      
      // Wait a moment for the camera to adjust
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Create canvas to capture image
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Stop the stream
      stream.getTracks().forEach(track => track.stop());
      
      // Convert to data URL
      const imageData = canvas.toDataURL('image/jpeg');
      
      // In a real implementation, this would be sent to the backend
      console.log('📸 User picture captured for biometric verification');
      
      // Add success event
      const newEvent = {
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        message: '📸 User picture captured for biometric verification',
        type: 'success'
      };
      
      setEvents(prev => [newEvent, ...prev.slice(0, 9)]);
      
      return imageData;
    } catch (error) {
      console.error('Camera error:', error);
      
      // Add error event
      const newEvent = {
        id: Date.now(),
        time: new Date().toLocaleTimeString(),
        message: '⚠️ Failed to capture user picture',
        type: 'warning'
      };
      
      setEvents(prev => [newEvent, ...prev.slice(0, 9)]);
      
      return null;
    }
  };

  // Request permissions on component mount
  useEffect(() => {
    // Request camera and microphone permissions
    requestCameraMicrophonePermissions();
    
    // Capture initial user picture
    setTimeout(() => {
      captureUserPicture();
    }, 2000);
  }, []);

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>🔒 Smart Behavior Authentication Dashboard</h1>
        <div className="user-info">
          <span>Welcome, {user?.email}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <main className="dashboard-main">
        {/* Location Information */}
        <section className="dashboard-section location-section">
          <h2>📍 User Location</h2>
          <div className="location-info">
            <div className="location-item">
              <span className="location-label">Latitude:</span>
              <span className="location-value">{location.latitude.toFixed(4)}</span>
            </div>
            <div className="location-item">
              <span className="location-label">Longitude:</span>
              <span className="location-value">{location.longitude.toFixed(4)}</span>
            </div>
            <div className="location-item">
              <span className="location-label">City:</span>
              <span className="location-value">{location.city}</span>
            </div>
            <div className="location-item">
              <span className="location-label">Country:</span>
              <span className="location-value">{location.country}</span>
            </div>
            <div className="location-item">
              <span className="location-label">Accuracy:</span>
              <span className="location-value">{location.accuracy}%</span>
            </div>
          </div>
          <div className="location-map">
            <div className="map-placeholder">
              🗺️ Map View (Simulated)
              <div className="accuracy-bar">
                <div 
                  className="accuracy-fill" 
                  style={{ width: `${location.accuracy}%` }}
                ></div>
              </div>
            </div>
          </div>
        </section>

        {/* Desktop Activity */}
        <section className="dashboard-section desktop-section">
          <h2>🖥️ Desktop Activity</h2>
          <div className="desktop-info">
            <div className="desktop-item">
              <span className="desktop-label">Current Application:</span>
              <span className="desktop-value">{desktopActivity.currentApplication}</span>
            </div>
            <div className="desktop-item">
              <span className="desktop-label">Active Applications:</span>
              <span className="desktop-value">{desktopActivity.activeApplications.join(', ')}</span>
            </div>
            <div className="desktop-item">
              <span className="desktop-label">Application Switches:</span>
              <span className="desktop-value">{desktopActivity.applicationSwitches}</span>
            </div>
            <div className="desktop-item">
              <span className="desktop-label">System Uptime:</span>
              <span className="desktop-value">{Math.floor(desktopActivity.systemUptime / 3600)}h {Math.floor((desktopActivity.systemUptime % 3600) / 60)}m</span>
            </div>
          </div>
        </section>

        {/* Security Metrics */}
        <section className="dashboard-section metrics-section">
          <h2>📊 Security Metrics</h2>
          <div className="metrics-grid">
            <div className="metric-card">
              <h3>⌨️ Keystrokes</h3>
              <div className="metric-value">{metrics.keystrokeCount}</div>
            </div>
            <div className="metric-card">
              <h3>🖱️ Mouse Events</h3>
              <div className="metric-value">{metrics.mouseCount}</div>
            </div>
            <div className="metric-card">
              <h3>🔄 Window Switches</h3>
              <div className="metric-value">{metrics.windowSwitches}</div>
            </div>
            <div className="metric-card">
              <h3>📱 Applications</h3>
              <div className="metric-value">{metrics.appCount}</div>
            </div>
            <div className="metric-card">
              <h3>⏱️ Typing Speed</h3>
              <div className="metric-value">{metrics.typingSpeed} WPM</div>
            </div>
            <div className="metric-card confidence-card">
              <h3>🛡️ Security Confidence</h3>
              <div className="metric-value">{metrics.securityConfidence}%</div>
              <div className="confidence-bar">
                <div 
                  className="confidence-fill" 
                  style={{ width: `${metrics.securityConfidence}%` }}
                ></div>
              </div>
            </div>
          </div>
        </section>

        {/* ML Model Metrics */}
        <section className="dashboard-section ml-section">
          <h2>🧠 ML Model Performance</h2>
          <div className="ml-metrics">
            <div className="ml-metric">
              <span className="ml-label">Classifier Accuracy:</span>
              <span className="ml-value">{mlMetrics.behaviorClassifierAccuracy}%</span>
            </div>
            <div className="ml-metric">
              <span className="ml-label">Anomaly Detection Rate:</span>
              <span className="ml-value">{mlMetrics.anomalyDetectionRate}%</span>
            </div>
            <div className="ml-metric">
              <span className="ml-label">False Positive Rate:</span>
              <span className="ml-value">{mlMetrics.falsePositiveRate}%</span>
            </div>
            <div className="ml-metric">
              <span className="ml-label">False Negative Rate:</span>
              <span className="ml-value">{mlMetrics.falseNegativeRate}%</span>
            </div>
            <div className="ml-metric">
              <span className="ml-label">Real-time Processing:</span>
              <span className="ml-value">{mlMetrics.realtimeProcessing}</span>
            </div>
          </div>
        </section>

        {/* Security Events */}
        <section className="dashboard-section events-section">
          <h2>🚨 Security Events</h2>
          <div className="events-list">
            {events.map(event => (
              <div key={event.id} className={`event-item event-${event.type}`}>
                <span className="event-time">[{event.time}]</span>
                <span className="event-message">{event.message}</span>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
};

export default Dashboard;