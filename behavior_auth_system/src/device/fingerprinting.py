"""
Device fingerprinting module for unique device identification and context validation.
Implements comprehensive device profiling for security and authentication.
"""

import hashlib
import platform
import socket
import uuid
import json
import time
import subprocess
from typing import Dict, Any, Optional, List
import logging

try:
    import psutil
except ImportError:
    psutil = None
    logging.warning("psutil not available - some device features will be limited")

class DeviceFingerprinter:
    """Generates unique device fingerprints from hardware and software characteristics."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.enabled_components = config.get('device', {}).get('fingerprinting', {}).get('components', [])
        
    def generate_fingerprint(self) -> Dict[str, Any]:
        """Generate comprehensive device fingerprint."""
        
        fingerprint = {
            'timestamp': time.time(),
            'components': {}
        }
        
        try:
            # Hardware identification
            if 'hardware_id' in self.enabled_components:
                fingerprint['components']['hardware'] = self._get_hardware_info()
                
            # Screen and display information
            if 'screen_resolution' in self.enabled_components:
                fingerprint['components']['display'] = self._get_display_info()
                
            # System and OS information
            fingerprint['components']['system'] = self._get_system_info()
            
            # Timezone information
            if 'timezone' in self.enabled_components:
                fingerprint['components']['timezone'] = self._get_timezone_info()
                
            # Network interfaces
            if 'network_interfaces' in self.enabled_components:
                fingerprint['components']['network'] = self._get_network_info()
                
            # Installed software (limited for privacy)
            if 'installed_software' in self.enabled_components:
                fingerprint['components']['software'] = self._get_software_info()
                
            # Generate composite hash
            fingerprint['device_id'] = self._generate_device_hash(fingerprint['components'])
            
        except Exception as e:
            self.logger.error(f"Fingerprint generation failed: {e}")
            fingerprint['error'] = str(e)
            
        return fingerprint
        
    def _get_hardware_info(self) -> Dict[str, Any]:
        """Get hardware-specific information."""
        
        hardware = {}
        
        try:
            # CPU information
            if psutil:
                hardware['cpu_count'] = psutil.cpu_count()
                hardware['cpu_freq'] = psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
                
            # Memory information
            if psutil:
                memory = psutil.virtual_memory()
                hardware['total_memory'] = memory.total
                
            # Disk information
            if psutil:
                disk_usage = psutil.disk_usage('/')
                hardware['disk_total'] = disk_usage.total
                
            # Machine UUID (if available)
            try:
                if platform.system() == 'Windows':
                    result = subprocess.run(['wmic', 'csproduct', 'get', 'UUID'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        if len(lines) > 1:
                            hardware['machine_uuid'] = lines[1].strip()
                elif platform.system() == 'Linux':
                    try:
                        with open('/etc/machine-id', 'r') as f:
                            hardware['machine_uuid'] = f.read().strip()
                    except:
                        pass
            except Exception:
                pass
                
        except Exception as e:
            self.logger.warning(f"Hardware info collection failed: {e}")
            
        return hardware
        
    def _get_display_info(self) -> Dict[str, Any]:
        """Get display and screen information."""
        
        display = {}
        
        try:
            if platform.system() == 'Windows':
                try:
                    import tkinter as tk
                    root = tk.Tk()
                    display['screen_width'] = root.winfo_screenwidth()
                    display['screen_height'] = root.winfo_screenheight()
                    display['dpi'] = root.winfo_fpixels('1i')
                    root.destroy()
                except Exception:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Display info collection failed: {e}")
            
        return display
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system and OS information."""
        
        system = {
            'platform': platform.platform(),
            'system': platform.system(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'architecture': platform.architecture(),
            'python_version': platform.python_version()
        }
        
        try:
            # Boot time
            if psutil:
                system['boot_time'] = psutil.boot_time()
                
        except Exception as e:
            self.logger.warning(f"System info collection failed: {e}")
            
        return system
        
    def _get_timezone_info(self) -> Dict[str, Any]:
        """Get timezone and locale information."""
        
        timezone = {}
        
        try:
            import datetime
            
            # Timezone offset
            now = datetime.datetime.now()
            timezone['utc_offset'] = now.utcoffset().total_seconds() if now.utcoffset() else 0
            timezone['timezone_name'] = str(now.astimezone().tzinfo)
            
            # Locale information
            try:
                import locale
                timezone['locale'] = locale.getdefaultlocale()
            except Exception:
                pass
                
        except Exception as e:
            self.logger.warning(f"Timezone info collection failed: {e}")
            
        return timezone
        
    def _get_network_info(self) -> Dict[str, Any]:
        """Get network interface information."""
        
        network = {}
        
        try:
            # MAC addresses (hashed for privacy)
            if psutil:
                interfaces = psutil.net_if_addrs()
                mac_addresses = []
                
                for interface, addrs in interfaces.items():
                    for addr in addrs:
                        if addr.family == psutil.AF_LINK:  # MAC address
                            # Hash MAC address for privacy
                            mac_hash = hashlib.sha256(addr.address.encode()).hexdigest()[:16]
                            mac_addresses.append(mac_hash)
                            
                network['mac_hashes'] = sorted(mac_addresses)  # Sort for consistency
                
            # Hostname
            network['hostname'] = socket.gethostname()
            
        except Exception as e:
            self.logger.warning(f"Network info collection failed: {e}")
            
        return network
        
    def _get_software_info(self) -> Dict[str, Any]:
        """Get limited software information (privacy-conscious)."""
        
        software = {}
        
        try:
            # Installed Python packages (limited list for privacy)
            import pkg_resources
            
            # Only track security-relevant packages
            security_packages = ['cryptography', 'pynput', 'psutil', 'requests']
            installed_packages = {}
            
            for package in pkg_resources.working_set:
                if package.project_name.lower() in security_packages:
                    installed_packages[package.project_name] = package.version
                    
            software['python_packages'] = installed_packages
            
        except Exception as e:
            self.logger.warning(f"Software info collection failed: {e}")
            
        return software
        
    def _generate_device_hash(self, components: Dict[str, Any]) -> str:
        """Generate a unique hash from device components."""
        
        try:
            # Create deterministic string from components
            component_string = json.dumps(components, sort_keys=True, default=str)
            
            # Generate SHA-256 hash
            device_hash = hashlib.sha256(component_string.encode()).hexdigest()
            
            return device_hash
            
        except Exception as e:
            self.logger.error(f"Device hash generation failed: {e}")
            return hashlib.sha256(str(time.time()).encode()).hexdigest()
            
    def compare_fingerprints(self, fp1: Dict[str, Any], fp2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two device fingerprints and return similarity metrics."""
        
        comparison = {
            'identical': fp1.get('device_id') == fp2.get('device_id'),
            'similarity_score': 0.0,
            'differences': [],
            'match_details': {}
        }
        
        try:
            if 'components' in fp1 and 'components' in fp2:
                # Compare each component
                for component in fp1['components']:
                    if component in fp2['components']:
                        if fp1['components'][component] == fp2['components'][component]:
                            comparison['match_details'][component] = True
                        else:
                            comparison['match_details'][component] = False
                            comparison['differences'].append(f"{component}_mismatch")
                    else:
                        comparison['differences'].append(f"{component}_missing")
                        
                # Calculate similarity score
                total_components = len(fp1['components'])
                matching_components = sum(comparison['match_details'].values())
                comparison['similarity_score'] = matching_components / total_components if total_components > 0 else 0.0
                
        except Exception as e:
            self.logger.error(f"Fingerprint comparison failed: {e}")
            comparison['error'] = str(e)
            
        return comparison

class GeolocationValidator:
    """Validates user location for security context."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.max_distance_km = config.get('device', {}).get('geolocation', {}).get('max_distance_km', 100)
        self.vpn_detection = config.get('device', {}).get('geolocation', {}).get('vpn_detection', True)
        
    def get_location_info(self, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Get location information from IP address."""
        
        location = {
            'timestamp': time.time(),
            'ip_address': ip_address,
            'location_available': False
        }
        
        try:
            if not ip_address:
                # Try to get public IP
                import requests
                response = requests.get('https://api.ipify.org?format=json', timeout=5)
                if response.status_code == 200:
                    ip_address = response.json().get('ip')
                    location['ip_address'] = ip_address
                    
            if ip_address:
                # For demo purposes - in production, use a proper geolocation service
                # This is a placeholder for actual geolocation API integration
                location.update({
                    'location_available': True,
                    'country': 'Unknown',
                    'city': 'Unknown',
                    'latitude': 0.0,
                    'longitude': 0.0,
                    'estimated': True
                })
                
                # VPN/Proxy detection (placeholder)
                if self.vpn_detection:
                    location['vpn_detected'] = self._detect_vpn(ip_address)
                    
        except Exception as e:
            self.logger.warning(f"Location info collection failed: {e}")
            location['error'] = str(e)
            
        return location
        
    def _detect_vpn(self, ip_address: str) -> bool:
        """Detect if IP address is from VPN/proxy (placeholder)."""
        
        # This is a simplified placeholder
        # In production, use proper VPN detection services
        
        try:
            # Check for common VPN IP ranges (very basic)
            vpn_indicators = [
                '10.',      # Private IP
                '192.168.', # Private IP
                '172.'      # Private IP
            ]
            
            for indicator in vpn_indicators:
                if ip_address.startswith(indicator):
                    return True
                    
        except Exception:
            pass
            
        return False
        
    def validate_location_change(self, previous_location: Dict[str, Any],
                                current_location: Dict[str, Any]) -> Dict[str, Any]:
        """Validate location change between sessions."""
        
        validation = {
            'significant_change': False,
            'distance_km': 0.0,
            'risk_level': 'low',
            'details': []
        }
        
        try:
            # Check if both locations are available
            if (not previous_location.get('location_available') or 
                not current_location.get('location_available')):
                validation['details'].append('location_data_unavailable')
                return validation
                
            # Calculate distance (simplified - use proper geolocation calculation in production)
            prev_lat = previous_location.get('latitude', 0)
            prev_lon = previous_location.get('longitude', 0)
            curr_lat = current_location.get('latitude', 0)
            curr_lon = current_location.get('longitude', 0)
            
            # Haversine formula for distance calculation
            distance = self._calculate_distance(prev_lat, prev_lon, curr_lat, curr_lon)
            validation['distance_km'] = distance
            
            # Check for significant change
            if distance > self.max_distance_km:
                validation['significant_change'] = True
                validation['risk_level'] = 'high'
                validation['details'].append('large_distance_change')
                
            # Check for VPN changes
            prev_vpn = previous_location.get('vpn_detected', False)
            curr_vpn = current_location.get('vpn_detected', False)
            
            if prev_vpn != curr_vpn:
                validation['details'].append('vpn_status_change')
                if validation['risk_level'] == 'low':
                    validation['risk_level'] = 'medium'
                    
        except Exception as e:
            self.logger.error(f"Location validation failed: {e}")
            validation['error'] = str(e)
            
        return validation
        
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        
        import math
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        earth_radius = 6371
        
        return c * earth_radius

class TimePatternAnalyzer:
    """Analyzes temporal patterns for anomaly detection."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.enable_analysis = config.get('device', {}).get('time_patterns', {}).get('enable_analysis', True)
        self.unusual_threshold = config.get('device', {}).get('time_patterns', {}).get('unusual_hours_threshold', 0.1)
        
    def analyze_access_pattern(self, access_history: List[float]) -> Dict[str, Any]:
        """Analyze user access time patterns."""
        
        analysis = {
            'pattern_available': False,
            'current_unusual': False,
            'risk_score': 0.0,
            'details': {}
        }
        
        if not self.enable_analysis or not access_history:
            return analysis
            
        try:
            import datetime
            
            # Convert timestamps to hours
            hours = []
            days_of_week = []
            
            for timestamp in access_history:
                dt = datetime.datetime.fromtimestamp(timestamp)
                hours.append(dt.hour)
                days_of_week.append(dt.weekday())
                
            # Analyze hour patterns
            hour_analysis = self._analyze_hour_patterns(hours)
            dow_analysis = self._analyze_day_patterns(days_of_week)
            
            # Current time analysis
            current_time = datetime.datetime.now()
            current_hour = current_time.hour
            current_dow = current_time.weekday()
            
            # Check if current access is unusual
            hour_probability = hour_analysis.get('hour_probabilities', {}).get(current_hour, 0)
            dow_probability = dow_analysis.get('dow_probabilities', {}).get(current_dow, 0)
            
            # Calculate risk score
            hour_risk = 1 - hour_probability if hour_probability > 0 else 0.5
            dow_risk = 1 - dow_probability if dow_probability > 0 else 0.5
            
            risk_score = (hour_risk + dow_risk) / 2
            
            analysis.update({
                'pattern_available': True,
                'current_unusual': risk_score > self.unusual_threshold,
                'risk_score': risk_score,
                'details': {
                    'hour_analysis': hour_analysis,
                    'dow_analysis': dow_analysis,
                    'current_hour': current_hour,
                    'current_dow': current_dow,
                    'hour_probability': hour_probability,
                    'dow_probability': dow_probability
                }
            })
            
        except Exception as e:
            self.logger.error(f"Time pattern analysis failed: {e}")
            analysis['error'] = str(e)
            
        return analysis
        
    def _analyze_hour_patterns(self, hours: List[int]) -> Dict[str, Any]:
        """Analyze hourly access patterns."""
        
        # Count accesses by hour
        hour_counts = {}
        for hour in hours:
            hour_counts[hour] = hour_counts.get(hour, 0) + 1
            
        # Calculate probabilities
        total_accesses = sum(hour_counts.values())
        hour_probabilities = {}
        
        for hour in range(24):
            count = hour_counts.get(hour, 0)
            hour_probabilities[hour] = count / total_accesses if total_accesses > 0 else 0
            
        # Identify peak hours
        peak_hours = sorted(hour_probabilities.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            'hour_counts': hour_counts,
            'hour_probabilities': hour_probabilities,
            'peak_hours': [hour for hour, _ in peak_hours],
            'total_accesses': total_accesses
        }
        
    def _analyze_day_patterns(self, days: List[int]) -> Dict[str, Any]:
        """Analyze day-of-week access patterns."""
        
        # Count accesses by day of week
        dow_counts = {}
        for day in days:
            dow_counts[day] = dow_counts.get(day, 0) + 1
            
        # Calculate probabilities
        total_accesses = sum(dow_counts.values())
        dow_probabilities = {}
        
        for day in range(7):
            count = dow_counts.get(day, 0)
            dow_probabilities[day] = count / total_accesses if total_accesses > 0 else 0
            
        return {
            'dow_counts': dow_counts,
            'dow_probabilities': dow_probabilities,
            'total_accesses': total_accesses
        }

class ContextValidator:
    """Main context validation manager."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.device_fingerprinter = DeviceFingerprinter(config)
        self.geolocation_validator = GeolocationValidator(config)
        self.time_analyzer = TimePatternAnalyzer(config)
        
    def validate_context(self, current_context: Dict[str, Any],
                        historical_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Perform comprehensive context validation."""
        
        validation = {
            'timestamp': time.time(),
            'overall_risk': 'low',
            'risk_factors': [],
            'components': {}
        }
        
        try:
            # Device fingerprint validation
            if historical_context and 'device_fingerprint' in historical_context:
                current_fp = self.device_fingerprinter.generate_fingerprint()
                historical_fp = historical_context['device_fingerprint']
                
                fp_comparison = self.device_fingerprinter.compare_fingerprints(
                    historical_fp, current_fp
                )
                
                validation['components']['device_fingerprint'] = fp_comparison
                
                if not fp_comparison['identical'] and fp_comparison['similarity_score'] < 0.8:
                    validation['risk_factors'].append('device_fingerprint_change')
                    
            # Geolocation validation
            current_location = self.geolocation_validator.get_location_info(
                current_context.get('ip_address')
            )
            
            if historical_context and 'location' in historical_context:
                location_validation = self.geolocation_validator.validate_location_change(
                    historical_context['location'], current_location
                )
                validation['components']['location'] = location_validation
                
                if location_validation['significant_change']:
                    validation['risk_factors'].append('significant_location_change')
                    
            # Time pattern analysis
            access_history = current_context.get('access_history', [])
            time_analysis = self.time_analyzer.analyze_access_pattern(access_history)
            validation['components']['time_pattern'] = time_analysis
            
            if time_analysis['current_unusual']:
                validation['risk_factors'].append('unusual_access_time')
                
            # Determine overall risk level
            validation['overall_risk'] = self._calculate_overall_risk(validation['risk_factors'])
            
        except Exception as e:
            self.logger.error(f"Context validation failed: {e}")
            validation['error'] = str(e)
            validation['overall_risk'] = 'high'  # Fail secure
            
        return validation
        
    def _calculate_overall_risk(self, risk_factors: List[str]) -> str:
        """Calculate overall risk level from individual factors."""
        
        if not risk_factors:
            return 'low'
            
        high_risk_factors = [
            'device_fingerprint_change',
            'significant_location_change'
        ]
        
        medium_risk_factors = [
            'unusual_access_time'
        ]
        
        if any(factor in risk_factors for factor in high_risk_factors):
            return 'high'
        elif any(factor in risk_factors for factor in medium_risk_factors):
            return 'medium'
        else:
            return 'low'