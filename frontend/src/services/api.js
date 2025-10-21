import axios from 'axios';

// 創建 axios 實例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000/api',
  timeout: 60000, // 增加到60秒
  headers: {
    'Content-Type': 'application/json',
  },
});

// 請求攔截器
api.interceptors.request.use(
  (config) => {
    console.log('API Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// 響應攔截器
api.interceptors.response.use(
  (response) => {
    console.log('API Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.status, error.response?.data);
    return Promise.reject(error);
  }
);

// 聊天 API
export const chatAPI = {
  sendMessage: (message, sessionId = 'default') =>
    api.post('/chat', { message, session_id: sessionId }),
  
  healthCheck: () =>
    api.get('/chat/health'),
};

// 地圖 API
export const mapAPI = {
  getNearbyLocations: (latitude, longitude, type, radius = 50) =>
    api.post('/maps/nearby', { latitude, longitude, type, radius }),
  
  getCities: () =>
    api.get('/maps/cities'),
  
  getLocationsByCity: (cityName, type) =>
    api.get(`/maps/city/${encodeURIComponent(cityName)}?type=${type}`),
};

// 失能給付 API
export const disabilityAPI = {
  getDisabilityLevels: () =>
    api.get('/disability/levels'),
  
  getDisabilityBenefit: (level, injuryType = '普通傷病') =>
    api.post('/disability/benefit', { level: parseInt(level), injury_type: injuryType }),
  
  analyzeBodyPartInjury: (bodyPart, injuryDescription) =>
    api.post('/disability/body-part', { body_part: bodyPart, injury_description: injuryDescription }),
  
  getDisabilityTypes: () =>
    api.get('/disability/types'),
  
  searchDisabilityByKeyword: (keyword) =>
    api.get(`/disability/search?keyword=${encodeURIComponent(keyword)}`),
};

// 通用 API
export const generalAPI = {
  healthCheck: () =>
    api.get('/health'),
};

export default api;
