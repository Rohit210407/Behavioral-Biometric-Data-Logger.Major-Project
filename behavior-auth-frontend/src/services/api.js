// api.js
const API_BASE_URL = 'http://localhost:5004/api'; // Changed from 5003 to 5004

class ApiService {
  async login(email, pin) {
    const response = await fetch(`${API_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, pin }),
    });
    
    return response.json();
  }
  
  async register(email, pin) {
    const response = await fetch(`${API_BASE_URL}/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, pin }),
    });
    
    return response.json();
  }
  
  async saveBaseline(userId, baselineData) {
    const response = await fetch(`${API_BASE_URL}/baseline`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId, baselineData }),
    });
    
    return response.json();
  }
  
  async analyzeBehavior(userId, currentData) {
    const response = await fetch(`${API_BASE_URL}/behavior/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId, currentData }),
    });
    
    return response.json();
  }
  
  async sendLocationData(userId, locationData) {
    const response = await fetch(`${API_BASE_URL}/location`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId, locationData }),
    });
    
    return response.json();
  }
  
  async sendDesktopActivityData(userId, activityData) {
    const response = await fetch(`${API_BASE_URL}/desktop/activity`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId, activityData }),
    });
    
    return response.json();
  }
  
  async getDashboardData(userId) {
    const response = await fetch(`${API_BASE_URL}/dashboard/${userId}`);
    return response.json();
  }
  
  async getProfileData(userId) {
    const response = await fetch(`${API_BASE_URL}/profile/${userId}`);
    return response.json();
  }
  
  async changePin(userId, currentPin, newPin) {
    const response = await fetch(`${API_BASE_URL}/profile/pin`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ userId, currentPin, newPin }),
    });
    
    return response.json();
  }
}

export default new ApiService();