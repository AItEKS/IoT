import apiClient from './client';

export const activateStand = async (pinCode) => {
    const response = await apiClient.post('/stands/activate', { pin_code: pinCode });
    return response.data; 
};

export const getMyStands = async () => {
    const response = await apiClient.get('/stands/my');
    return response.data;
};

export const getAllUsers = async () => {
    const response = await apiClient.get('/auth/users');
    return response.data;
};

export const inviteToGame = async (opponentUsername) => {
    const response = await apiClient.post('/games/invite', { opponent_username: opponentUsername });
    return response.data;
};

export const getActiveGames = async () => {
    const response = await apiClient.get('/games/active');
    return response.data;
};

export const surrenderGame = async (gameId) => {
    const response = await apiClient.post(`/games/${gameId}/surrender`);
    return response.data;
};