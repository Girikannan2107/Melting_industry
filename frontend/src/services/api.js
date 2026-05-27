import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const documentApi = {
    uploadDocument: async (file) => {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await axios.post(`${API_BASE_URL}/documents/process`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    checkStatus: async (taskId) => {
        const response = await axios.get(`${API_BASE_URL}/documents/status/${taskId}`);
        return response.data;
    }
};