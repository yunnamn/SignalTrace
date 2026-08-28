import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

export const getProfiles = () => axios.get(`${API_URL}/profiles`);
export const updateProfile = (id, profile) => axios.put(`${API_URL}/profiles/${id}`, profile);
export const moderateContent = (payload) => 
  axios.post(`${API_URL}/moderate`, payload);
export const getLogs = () => axios.get(`${API_URL}/logs`);

export const addToQueue = (url, profileId) => 
  axios.post(`${API_URL}/queue/add`, { url, profile_id: profileId });

export const startQueue = (profileId) => 
  axios.post(`${API_URL}/queue/start`, { profile_id: profileId });

export const stopQueue = () => 
  axios.post(`${API_URL}/queue/stop`);

export const getQueueStatus = () => 
  axios.get(`${API_URL}/queue/status`);

export const clearLogs = () => axios.delete(`${API_URL}/logs`);

export const analyzeProfile = (payload) => axios.post(`${API_URL}/profile/analyze`, payload);

export const moderateAudio = (profileId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  return axios.post(`${API_URL}/moderate/audio?profile_id=${profileId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
};

export const getGraph = (minDegree = 1) => axios.get(`${API_URL}/graph?min_degree=${minDegree}`);

export const getWatchlist = () => axios.get(`${API_URL}/watchlist`);
export const addWatchlist = (payload) => axios.post(`${API_URL}/watchlist`, payload);
export const deleteWatchlist = (id) => axios.delete(`${API_URL}/watchlist/${id}`);
