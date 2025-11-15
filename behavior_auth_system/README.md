# 🔒 Smart Behavior-Based Continuous Authentication System

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen.svg)

> A comprehensive security system that continuously authenticates users based on behavioral biometrics (keystrokes, mouse/touch interactions) while integrating advanced security mechanisms.

## 🚀 Features

### 🔐 Core Security
- **Behavioral Biometrics**: Real-time keystroke dynamics and mouse pattern analysis
- **Continuous Authentication**: Background monitoring with adaptive thresholds
- **Anomaly Detection**: Machine learning-powered threat detection
- **Multi-Factor Authentication**: Risk-based authentication triggers
- **Device Fingerprinting**: Hardware and software-based device identification

### 🛡️ Privacy & Security
- **AES-256 Encryption**: All data encrypted at rest and in transit
- **Zero-Knowledge Architecture**: Behavioral patterns stored as encrypted hashes
- **Differential Privacy**: Statistical noise injection for privacy protection
- **GDPR Compliant**: Data minimization and user consent mechanisms
- **OAuth2/OpenID Connect**: Industry-standard authentication protocols

### 📊 Intelligence
- **Machine Learning Models**: XGBoost and Random Forest classifiers
- **Real-time Scoring**: Continuous authentication confidence scoring
- **Adaptive Learning**: Models improve with user interaction data
- **Geolocation Analytics**: Time and location-based anomaly detection

## 📦 Quick Installation

### Option 1: Ready-to-Use Executable (Recommended)

**Windows Users:**
```bash
# Download and run the pre-built executable
# No Python installation required!
BehaviorAuth.exe
```

### Option 2: From Source

```bash
# Clone the repository
git clone https://github.com/yourusername/behavior-auth-system.git
cd behavior-auth-system

# Install dependencies
pip install -r requirements.txt

# Configure settings
cp config/settings.yaml.example config/settings.yaml

# Run setup
python scripts/setup.py

# Start the system
python start.py
```

## 🎯 Quick Start Guide

### 1. **Launch Dashboard**
```bash
python run_enhanced_dashboard.py
```

### 2. **Start Background Monitoring**
```bash
python run_background_monitor.py
```

### 3. **Run 15-Minute Training**
```bash
python demo_15min_training.py
```

## 🏗️ Project Structure

```
behavior_auth_system/
├── 📁 src/
│   ├── 🔧 core/                 # Behavioral capture & analysis
│   ├── 🛡️ security/            # Encryption & security layers
│   ├── 🤖 ml/                  # Machine learning models
│   ├── 🔐 auth/                # Authentication management
│   ├── 📱 device/              # Device fingerprinting
│   ├── ⚙️ service/             # Background services
│   └── 🖥️ ui/                  # User interfaces
├── 📁 build/                   # Executable builders
├── 📁 config/                  # Configuration files
├── 📁 tests/                   # Test suites
├── 📁 docs/                    # Documentation
├── 📄 requirements.txt         # Dependencies
└── 🚀 start.py                # Main launcher
```

## 💻 Supported Platforms

| Platform | Status | Features |
|----------|--------|---------|
| Windows 10/11 | ✅ Full Support | Complete feature set |
| Linux (Ubuntu/Fedora) | ✅ Full Support | Complete feature set |
| macOS | ⚠️ Limited | Core features only |
| Android | 🔄 In Development | Mobile behavioral patterns |

## 🔧 Configuration

Edit [`config/settings.yaml`](config/settings.yaml) to customize:

```yaml
app:
  name: "BehaviorAuth"
  debug: false
  
security:
  encryption_key_size: 256
  session_timeout: 3600
  
ml:
  model_type: "xgboost"
  training_samples: 1000
  confidence_threshold: 0.8
```

## 📊 Demo & Testing

### Live Demo
```bash
# Full-featured demo with GUI
python demo_enhanced_security.py

# Simplified console demo
python demo_simplified.py

# 15-minute training simulation
python demo_15min_training.py
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run specific test suite
python tests/test_core.py
python tests/test_security.py
```

## 🚀 Building Executables

### Windows EXE
```bash
cd build
python build_windows.py
# Creates: output/BehaviorAuth.exe
```

### Android APK
```bash
cd build
python build_android.py
# Creates: bin/BehaviorAuth.apk
```

### Build All Platforms
```bash
cd build
python build_all.py
```

## 📖 Documentation

- 📋 **[Distribution Guide](DISTRIBUTION_GUIDE.md)** - How to package and distribute
- 🔒 **[Security Summary](ENHANCED_SECURITY_SUMMARY.md)** - Security architecture details
- ⚡ **[Quick Training](README_15MIN_TRAINING.md)** - 15-minute setup guide
- 🎯 **[EXE Ready Guide](EXE_READY_GUIDE.md)** - Executable deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Security Notice

This system collects behavioral biometric data. Ensure compliance with:
- GDPR (EU)
- CCPA (California)
- Local privacy regulations

All data is encrypted and stored locally by default.

## 🎯 Use Cases

- **Enterprise Security**: Continuous employee authentication
- **Financial Services**: Fraud detection and prevention
- **Healthcare**: Patient identity verification
- **Education**: Exam integrity and identity verification
- **Government**: Secure facility access control

## 📞 Support

- 📧 **Issues**: [GitHub Issues](https://github.com/yourusername/behavior-auth-system/issues)
- 📖 **Documentation**: See [`docs/`](docs/) directory
- 💬 **Discussions**: [GitHub Discussions](https://github.com/yourusername/behavior-auth-system/discussions)

---

<div align="center">
  <strong>🔒 Secure • 🚀 Fast • 🔒 Private • 🛡️ Reliable</strong>
</div>