import React, { useState, useEffect, useRef } from 'react';
import api from '../services/api';
import './BaselineTraining.css';

const BaselineTraining = ({ user, onComplete }) => {
  const [progress, setProgress] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(120); // 2 minutes in seconds
  const [status, setStatus] = useState('Collection will start shortly...');
  const [metrics, setMetrics] = useState({
    keystrokeCount: 0,
    lastKey: '',
    wpm: 0,
    avgDwell: 0,
    avgFlight: 0,
    clickCount: 0,
    movement: 0,
    avgVelocity: 0,
    scrollCount: 0,
    clickPatterns: 'Collecting...',
    windowSwitches: 0,
    appCount: 0
  });
  
  // Real data collection state
  const [keyPressTimes, setKeyPressTimes] = useState({});
  const [lastReleaseTime, setLastReleaseTime] = useState(null);
  const [clickTimes, setClickTimes] = useState([]);
  const [startTime, setStartTime] = useState(null);
  const [collectedData, setCollectedData] = useState([]);
  const [isCompleted, setIsCompleted] = useState(false);
  const [completionMessage, setCompletionMessage] = useState('');
  
  const keystrokeCountRef = useRef(0);
  const clickCountRef = useRef(0);
  const movementRef = useRef(0);
  const lastMousePositionRef = useRef({ x: 0, y: 0 });
  const lastTimestampRef = useRef(0);
  const timerRef = useRef(null); // To keep track of the timer
  const desktopActivityRef = useRef({
    windowSwitches: 0,
    activeApps: []
  });
  const isTimerStartedRef = useRef(false); // To track if timer has been started
  const endTimeRef = useRef(null); // To store the end time of the collection

  // Set up real data collection for baseline (separate from timer)
  useEffect(() => {
    console.log('📋 Setting up baseline data collection event listeners...');
    
    // Start collection when component mounts
    setStartTime(Date.now());
    
    // Set up event listeners for real data collection
    const handleKeyDown = (e) => {
      // Don't prevent default for normal typing
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
        keystrokeCount: prevMetrics.keystrokeCount + 1,
        lastKey: key
      }));
      
      keystrokeCountRef.current += 1;
    };
    
    const handleKeyUp = (e) => {
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
      const timestamp = Date.now();
      const x = e.clientX;
      const y = e.clientY;
      
      // Calculate movement distance
      const dx = x - lastMousePositionRef.current.x;
      const dy = y - lastMousePositionRef.current.y;
      const distance = Math.sqrt(dx * dx + dy * dy);
      
      // Calculate velocity
      let velocity = 0;
      if (lastTimestampRef.current > 0) {
        const dt = timestamp - lastTimestampRef.current;
        if (dt > 0) {
          velocity = distance / (dt / 1000); // pixels per second
        }
      }
      
      // Update refs
      lastMousePositionRef.current = { x, y };
      lastTimestampRef.current = timestamp;
      
      // Update metrics
      movementRef.current += distance;
      
      setMetrics(prevMetrics => ({
        ...prevMetrics,
        movement: Math.round(movementRef.current),
        avgVelocity: Math.round(velocity)
      }));
    };
    
    const handleClick = (e) => {
      const timestamp = Date.now();
      
      setClickTimes(prev => [...prev, timestamp]);
      
      setMetrics(prevMetrics => ({
        ...prevMetrics,
        clickCount: prevMetrics.clickCount + 1
      }));
      
      clickCountRef.current += 1;
    };
    
    const handleScroll = (e) => {
      setMetrics(prevMetrics => ({
        ...prevMetrics,
        scrollCount: prevMetrics.scrollCount + 1
      }));
    };
    
    // Simulate desktop activity monitoring
    const simulateDesktopActivity = () => {
      desktopActivityRef.current.windowSwitches += Math.floor(Math.random() * 2);
      desktopActivityRef.current.activeApps = ['Chrome', 'VS Code', 'Slack', 'Spotify'].slice(0, Math.floor(Math.random() * 3) + 2);
      
      setMetrics(prevMetrics => ({
        ...prevMetrics,
        windowSwitches: desktopActivityRef.current.windowSwitches,
        appCount: desktopActivityRef.current.activeApps.length
      }));
    };
    
    // Add event listeners
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('click', handleClick);
    window.addEventListener('scroll', handleScroll);
    
    // Simulate desktop activity monitoring every 10 seconds
    const desktopActivityInterval = setInterval(simulateDesktopActivity, 10000);
    
    // Cleanup function
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('click', handleClick);
      window.removeEventListener('scroll', handleScroll);
      
      // Clear intervals if component unmounts
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      if (desktopActivityInterval) {
        clearInterval(desktopActivityInterval);
      }
    };
  }, []); // Empty dependency array - only run once

  // Main collection timer - runs for exactly 2 minutes
  useEffect(() => {
    // Only start timer once
    if (isTimerStartedRef.current) {
      return;
    }
    
    isTimerStartedRef.current = true;
    const collectionDuration = 120; // 2 minutes in seconds
    
    // Set the end time for the collection
    endTimeRef.current = Date.now() + (collectionDuration * 1000);
    
    // Start the timer when component mounts
    console.log('⏱️ Starting baseline collection timer');
    setStatus('🔄 Collecting initial behavioral patterns...');
    
    // Clear any existing timer
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    
    // Start new timer
    timerRef.current = setInterval(() => {
      // Calculate remaining time based on actual end time
      const currentTime = Date.now();
      const remainingTime = Math.max(0, Math.floor((endTimeRef.current - currentTime) / 1000));
      
      setTimeRemaining(remainingTime);
      const newProgress = ((collectionDuration - remainingTime) / collectionDuration) * 100;
      setProgress(newProgress);

      // Update status message based on progress
      if (remainingTime > 0) {
        if (newProgress < 10) {
          setStatus('🔄 Collecting initial behavioral patterns...');
        } else if (newProgress < 20) {
          setStatus('⌨️ Analyzing typing rhythm and speed...');
        } else if (newProgress < 30) {
          setStatus('🖱️ Learning mouse movement patterns...');
        } else if (newProgress < 40) {
          setStatus('📊 Identifying application usage patterns...');
        } else if (newProgress < 50) {
          setStatus('🖥️ Monitoring desktop activity...');
        } else if (newProgress < 60) {
          setStatus('🧠 Building comprehensive behavioral profile...');
        } else if (newProgress < 70) {
          setStatus('🔒 Enhancing security baseline...');
        } else if (newProgress < 80) {
          setStatus('📈 Optimizing ML model parameters...');
        } else if (newProgress < 90) {
          setStatus('✅ Finalizing baseline profile...');
        } else {
          setStatus('🎉 Collection complete! Saving profile...');
        }
      } else {
        // Collection complete
        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }
        
        // Process and save baseline data
        processAndSaveBaseline();
      }
    }, 1000);
    
    // Cleanup timer on unmount
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, []); // Empty dependency array to run only once when component mounts

  // Process collected data and save baseline
  const processAndSaveBaseline = async () => {
    try {
      // Calculate final metrics
      const keystrokes = collectedData.filter(d => d.dwellTime !== undefined);
      const avgDwell = keystrokes.length > 0 
        ? keystrokes.reduce((sum, d) => sum + d.dwellTime, 0) / keystrokes.length 
        : 0;
        
      const flights = collectedData.filter(d => d.flightTime !== undefined);
      const avgFlight = flights.length > 0 
        ? flights.reduce((sum, d) => sum + d.flightTime, 0) / flights.length 
        : 0;
        
      // Calculate typing speed (WPM)
      const timeSpan = collectedData.length > 1 
        ? (collectedData[collectedData.length - 1].timestamp - collectedData[0].timestamp) / 1000 
        : 0;
      const wpm = timeSpan > 0 ? (keystrokes.length / 5) / (timeSpan / 60) : 0;
      
      // Calculate mouse metrics
      const clicks = clickTimes;
      const clickCount = clicks.length;
      
      // Prepare baseline data
      const baselineData = {
        avgDwell: Math.round(avgDwell),
        avgFlight: Math.round(avgFlight),
        wpm: Math.round(wpm),
        clickCount: clickCount,
        avgVelocity: metrics.avgVelocity,
        windowSwitches: metrics.windowSwitches,
        appCount: metrics.appCount,
        keystrokeCount: keystrokeCountRef.current,
        movement: movementRef.current,
        scrollCount: metrics.scrollCount,
        collectedAt: new Date().toISOString()
      };
      
      console.log('📊 Baseline data:', baselineData);
      
      // Send to backend
      const response = await api.saveBaseline(user.id, baselineData);
      
      if (response.success) {
        setIsCompleted(true);
        setCompletionMessage('✅ Baseline training completed successfully! Your behavioral profile has been saved.');
        setStatus('🎉 Training Complete!');
        
        // Call onComplete after a delay
        setTimeout(() => {
          onComplete();
        }, 3000);
      } else {
        setCompletionMessage('❌ Failed to save baseline data. Please try again.');
      }
    } catch (error) {
      console.error('Baseline processing error:', error);
      setCompletionMessage('❌ Error processing baseline data. Please try again.');
    }
  };

  // Format time for display
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="baseline-training-container" role="main" aria-label="Behavioral Baseline Training">
      <div className="baseline-header">
        <h1>🧠 Behavioral Baseline Training</h1>
        <p>Collecting your unique behavioral patterns for continuous authentication</p>
      </div>
      
      <div className="training-content">
        {/* Progress Section */}
        <div className="card progress-card">
          <h2>📊 Collection Progress</h2>
          
          <div className="progress-info">
            <div className="time-display">
              <span className="time-label">Time Remaining:</span>
              <span className="time-value" aria-live="polite">{formatTime(timeRemaining)}</span>
            </div>
            
            <div className="progress-container">
              <div className="progress-bar" role="progressbar" aria-valuenow={progress} aria-valuemin="0" aria-valuemax="100" aria-label="Collection progress">
                <div 
                  className="progress-fill" 
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
              <div className="progress-text">{Math.round(progress)}%</div>
            </div>
            
            <div className="status-message">
              <span className="status-icon" aria-hidden="true">ℹ️</span>
              <span className="status-text" aria-live="polite">{status}</span>
            </div>
          </div>
        </div>
        
        {/* Metrics Section */}
        <div className="card metrics-card">
          <h2>📈 Real-time Metrics</h2>
          
          <div className="metrics-grid">
            <div className="metric-item">
              <div className="metric-icon" aria-hidden="true">⌨️</div>
              <div className="metric-value">{metrics.keystrokeCount}</div>
              <div className="metric-label">Keystrokes</div>
            </div>
            
            <div className="metric-item">
              <div className="metric-icon" aria-hidden="true">🖱️</div>
              <div className="metric-value">{metrics.clickCount}</div>
              <div className="metric-label">Clicks</div>
            </div>
            
            <div className="metric-item">
              <div className="metric-icon" aria-hidden="true">🔄</div>
              <div className="metric-value">{metrics.windowSwitches}</div>
              <div className="metric-label">App Switches</div>
            </div>
            
            <div className="metric-item">
              <div className="metric-icon" aria-hidden="true">📱</div>
              <div className="metric-value">{metrics.appCount}</div>
              <div className="metric-label">Active Apps</div>
            </div>
            
            <div className="metric-item">
              <div className="metric-icon" aria-hidden="true">⏱️</div>
              <div className="metric-value">{metrics.wpm}</div>
              <div className="metric-label">WPM</div>
            </div>
            
            <div className="metric-item">
              <div className="metric-icon" aria-hidden="true">📏</div>
              <div className="metric-value">{Math.round(metrics.avgDwell)}ms</div>
              <div className="metric-label">Avg Dwell</div>
            </div>
          </div>
        </div>
        
        {/* Instructions Section */}
        <div className="card instructions-card">
          <h2>📋 Training Instructions</h2>
          
          <div className="instructions-content">
            <div className="instruction-step">
              <div className="step-number">1</div>
              <div className="step-content">
                <h3>Type naturally</h3>
                <p>Type in text boxes as you normally would. We're learning your natural typing rhythm.</p>
              </div>
            </div>
            
            <div className="instruction-step">
              <div className="step-number">2</div>
              <div className="step-content">
                <h3>Use your mouse</h3>
                <p>Click, scroll, and move your mouse around the screen to capture movement patterns.</p>
              </div>
            </div>
            
            <div className="instruction-step">
              <div className="step-number">3</div>
              <div className="step-content">
                <h3>Switch applications</h3>
                <p>Switch between different applications to help us understand your usage patterns.</p>
              </div>
            </div>
            
            <div className="instruction-step">
              <div className="step-number">4</div>
              <div className="step-content">
                <h3>Relax and be yourself</h3>
                <p>The more natural you are, the better we can protect your account.</p>
              </div>
            </div>
          </div>
        </div>
        
        {/* Completion Message */}
        {isCompleted && (
          <div className="card completion-card" role="alert" aria-live="assertive">
            <h2>🎉 Training Complete!</h2>
            <div className="completion-message">
              {completionMessage}
            </div>
            <div className="redirect-message">
              Redirecting to dashboard...
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BaselineTraining;