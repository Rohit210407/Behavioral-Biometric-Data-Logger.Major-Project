import React, { useState, useRef, useEffect } from 'react';
import './BiometricVerification.css';

const BiometricVerification = ({ userId, onComplete }) => {
  const [cameraPermission, setCameraPermission] = useState(false);
  const [microphonePermission, setMicrophonePermission] = useState(false);
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedImage, setCapturedImage] = useState(null);
  const [verificationStatus, setVerificationStatus] = useState('pending');
  const [verificationMessage, setVerificationMessage] = useState('');
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  // Request camera and microphone permissions on component mount
  useEffect(() => {
    requestPermissions();
    
    return () => {
      // Cleanup media streams
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  const requestPermissions = async () => {
    try {
      // Request camera permission
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      setCameraPermission(true);
      
      // Set up video stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
      
      // Request microphone permission
      const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStream.getTracks().forEach(track => track.stop()); // Stop immediately
      setMicrophonePermission(true);
      
      setVerificationMessage('Camera and microphone permissions granted. Ready for verification.');
    } catch (error) {
      console.error('Permission error:', error);
      setVerificationMessage('Failed to get camera/microphone permissions. Please allow access in browser settings.');
    }
  };

  const captureImage = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    
    setIsCapturing(true);
    setVerificationStatus('capturing');
    setVerificationMessage('Capturing image...');
    
    try {
      // Wait for video to load
      await new Promise(resolve => {
        if (videoRef.current.readyState === 4) {
          resolve();
        } else {
          videoRef.current.onloadeddata = resolve;
        }
      });
      
      // Wait a moment for camera to adjust
      await new Promise(resolve => setTimeout(resolve, 500));
      
      // Capture image
      const canvas = canvasRef.current;
      const video = videoRef.current;
      
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      
      // Convert to data URL
      const imageData = canvas.toDataURL('image/jpeg');
      setCapturedImage(imageData);
      
      // Simulate verification process
      await simulateVerification(imageData);
      
    } catch (error) {
      console.error('Capture error:', error);
      setVerificationMessage('Failed to capture image. Please try again.');
      setVerificationStatus('error');
    } finally {
      setIsCapturing(false);
    }
  };

  const simulateVerification = async (imageData) => {
    setVerificationStatus('verifying');
    setVerificationMessage('Verifying biometric data...');
    
    // Simulate verification process (2 seconds)
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    // Random verification result for demo
    const isSuccess = Math.random() > 0.3; // 70% success rate
    
    if (isSuccess) {
      setVerificationStatus('success');
      setVerificationMessage('Biometric verification successful!');
      
      // Call onComplete after a short delay
      setTimeout(() => {
        onComplete();
      }, 1500);
    } else {
      setVerificationStatus('failed');
      setVerificationMessage('Biometric verification failed. Please try again.');
    }
  };

  const retryVerification = () => {
    setCapturedImage(null);
    setVerificationStatus('pending');
    setVerificationMessage('Ready for verification. Click capture to start.');
  };

  return (
    <div className="biometric-verification">
      <h2>📸 Biometric Verification</h2>
      <p className="verification-instructions">
        Please look at the camera and click "Capture" for biometric verification.
      </p>
      
      <div className="verification-content">
        {/* Camera feed */}
        <div className="camera-section">
          <h3>Camera Feed</h3>
          <div className="camera-container">
            <video 
              ref={videoRef} 
              autoPlay 
              playsInline 
              muted
              className="camera-feed"
              style={{ display: capturedImage ? 'none' : 'block' }}
            />
            {capturedImage && (
              <img 
                src={capturedImage} 
                alt="Captured for verification" 
                className="captured-image"
              />
            )}
            <canvas ref={canvasRef} style={{ display: 'none' }} />
          </div>
        </div>
        
        {/* Verification status */}
        <div className="verification-status">
          <div className={`status-indicator status-${verificationStatus}`}>
            {verificationStatus === 'pending' && '🕒 Waiting'}
            {verificationStatus === 'capturing' && '📸 Capturing...'}
            {verificationStatus === 'verifying' && '🔍 Verifying...'}
            {verificationStatus === 'success' && '✅ Success'}
            {verificationStatus === 'failed' && '❌ Failed'}
            {verificationStatus === 'error' && '⚠️ Error'}
          </div>
          
          <p className="status-message">{verificationMessage}</p>
          
          <div className="permission-status">
            <div className={`permission-item ${cameraPermission ? 'granted' : 'denied'}`}>
              📷 Camera: {cameraPermission ? 'Granted' : 'Denied'}
            </div>
            <div className={`permission-item ${microphonePermission ? 'granted' : 'denied'}`}>
              🎤 Microphone: {microphonePermission ? 'Granted' : 'Denied'}
            </div>
          </div>
        </div>
      </div>
      
      {/* Action buttons */}
      <div className="verification-actions">
        {!capturedImage ? (
          <button 
            onClick={captureImage} 
            disabled={!cameraPermission || isCapturing}
            className="capture-btn"
          >
            {isCapturing ? '📸 Capturing...' : '📸 Capture Image'}
          </button>
        ) : (
          <div className="post-capture-actions">
            <button 
              onClick={retryVerification}
              className="retry-btn"
            >
              🔁 Retry
            </button>
            <button 
              onClick={captureImage}
              disabled={isCapturing}
              className="recapture-btn"
            >
              📸 Recapture
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default BiometricVerification;