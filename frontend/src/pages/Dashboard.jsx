import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import mqtt from 'mqtt';
import { getMe } from '../api/auth';
import { activateStand, getMyStands, getAllUsers, getActiveGames } from '../api/game';

const inviteToGame = async (payload) => {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${import.meta.env.VITE_API_URL}/games/invite`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(payload)
    });
    if (!response.ok) {
        const error = await response.json();
        throw { response: { data: error } };
    }
    return response.json();
};

const Dashboard = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(null);
    const [stands, setStands] = useState([]);
    const [users, setUsers] = useState([]);
    const [activeGames, setActiveGames] = useState([]);
    
    const [pinCode, setPinCode] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [note, setNote] = useState(null);
    const [useMocks, setUseMocks] = useState(false);

    const showNote = (message, isError = false) => {
        setNote({ message, isError });
        setTimeout(() => setNote(null), 3000);
    };

    const fetchData = async () => {
        try {
            const userData = await getMe();
            setUser(userData);
            
            const [standsData, usersData, gamesData] = await Promise.all([
                getMyStands(),
                getAllUsers(),
                getActiveGames()
            ]);
            
            setStands(standsData);
            setUsers(usersData);
            setActiveGames(gamesData);
        } catch (err) {
            if (err.response?.status === 401) {
                localStorage.removeItem('access_token');
                navigate('/auth');
            }
        }
    };

    useEffect(() => {
        fetchData();
        const interval = setInterval(() => {
            getActiveGames().then(setActiveGames).catch(() => {});
        }, 5000);
        return () => clearInterval(interval);
    }, [navigate]);

    useEffect(() => {
        if (!user) return;
        const client = mqtt.connect(import.meta.env.VITE_MQTT_URL);

        client.on('connect', () => {
            client.subscribe(`notifications/user_${user.id}`);
        });

        client.on('message', (topic, message) => {
            try {
                const data = JSON.parse(message.toString());
                if (data.action === "game_started" && data.game_id) {
                    navigate(`/game/${data.game_id}`);
                }
            } catch (e) {
                console.error("Notification error:", e);
            }
        });

        return () => {
            if (client) client.end();
        };
    }, [user, navigate]);

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        navigate('/auth');
    };

    const handleActivateStand = async (e) => {
        e.preventDefault();
        if (pinCode.length < 4) return;
        try {
            await activateStand(pinCode);
            showNote("Стенд успешно привязан");
            setPinCode('');
            fetchData();
        } catch (err) {
            showNote(err.response?.data?.detail || "Ошибка активации", true);
        }
    };

    const handleInvite = async (opponentUsername) => {
        setIsLoading(true);
        try {
            const data = await inviteToGame({ 
                opponent_username: opponentUsername, 
                use_mocks: useMocks 
            });
            navigate(`/game/${data.game_id}`);
        } catch (err) {
            showNote(err.response?.data?.detail || "Не удалось отправить вызов", true);
        } finally {
            setIsLoading(false);
        }
    };

    if (!user) return (
        <div className="min-h-screen bg-[#161512] flex items-center justify-center">
            <div className="w-12 h-12 border-4 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin"></div>
        </div>
    );

    return (
        <div className="min-h-screen bg-[#161512] text-[#bababa] p-4 md:p-8 font-sans selection:bg-emerald-500/30">
            {note && (
                <div className={`fixed top-6 right-6 z-50 px-6 py-3 rounded shadow-2xl font-bold text-xs uppercase tracking-widest animate-in fade-in slide-in-from-right-4 ${
                    note.isError ? 'bg-red-600 text-white' : 'bg-emerald-600 text-white'
                }`}>
                    {note.message}
                </div>
            )}

            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex flex-col md:flex-row justify-between items-center bg-[#262421] p-6 rounded border border-[#3c3934] shadow-2xl gap-4">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-emerald-600 rounded flex items-center justify-center text-white font-black text-2xl shadow-lg shadow-emerald-900/20">
                            {user.username[0].toUpperCase()}
                        </div>
                        <div>
                            <h1 className="text-xl font-black text-white uppercase tracking-tighter leading-none">AR CHESS</h1>
                            <p className="text-[#7d7d7d] text-[10px] uppercase tracking-widest mt-1 font-bold">Система управления</p>
                        </div>
                    </div>
                    
                    <div className="flex items-center gap-6 w-full md:w-auto justify-between md:justify-end">
                        <div className="text-right">
                            <div className="text-[9px] text-[#7d7d7d] uppercase font-bold tracking-widest">Авторизован как</div>
                            <div className="text-emerald-500 font-black uppercase text-sm">{user.username}</div>
                        </div>
                        <button onClick={handleLogout} className="bg-[#1c1b18] hover:bg-red-950/30 hover:text-red-500 p-3 rounded border border-[#3c3934] transition-all">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" /></svg>
                        </button>
                    </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
                    <div className="md:col-span-4 bg-[#262421] p-6 rounded border border-[#3c3934] shadow-lg flex flex-col h-[500px]">
                        <h2 className="text-[10px] font-black text-[#7d7d7d] uppercase mb-6 tracking-[0.2em] border-b border-[#3c3934] pb-2">Мои Устройства</h2>
                        <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                            {stands.length === 0 ? (
                                <p className="text-center py-10 opacity-30 text-[10px] uppercase font-bold tracking-widest">Нет устройств</p>
                            ) : (
                                stands.map(stand => (
                                    <div key={stand.id} className="bg-[#1c1b18] p-4 rounded border border-emerald-900/20 flex justify-between items-center group">
                                        <span className="font-mono text-xs text-emerald-500 font-bold">{stand.id}</span>
                                        <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_8px_rgba(16,185,129,0.6)]"></div>
                                    </div>
                                ))
                            )}
                        </div>
                        <form onSubmit={handleActivateStand} className="mt-6 pt-6 border-t border-[#3c3934] space-y-3">
                            <input 
                                type="text" placeholder="Введите ПИН-код" 
                                className="w-full bg-[#1c1b18] text-white border border-[#3c3934] rounded p-3 text-xs font-bold focus:border-emerald-500 outline-none"
                                value={pinCode} onChange={(e) => setPinCode(e.target.value)} required
                            />
                            <button type="submit" className="w-full bg-emerald-600 hover:bg-emerald-500 text-white p-3 rounded text-[10px] font-black uppercase tracking-widest transition-all">Привязать стенд</button>
                        </form>
                    </div>

                    <div className="md:col-span-4 bg-[#262421] p-6 rounded border border-[#3c3934] shadow-lg flex flex-col h-[500px]">
                        <h2 className="text-[10px] font-black text-[#7d7d7d] uppercase mb-6 tracking-[0.2em] border-b border-[#3c3934] pb-2">Игроки онлайн</h2>
                        <div className="flex-1 overflow-y-auto space-y-2 pr-2">
                            {users.length === 0 ? (
                                <div className="text-center py-10 opacity-30 text-[10px] uppercase font-bold tracking-widest italic">Поиск оппонентов...</div>
                            ) : (
                                users.map(u => (
                                    <div key={u.id} className="bg-[#1c1b18] p-4 rounded border border-[#3c3934] flex justify-between items-center hover:bg-[#2c2a27] transition-all">
                                        <span className="font-bold text-sm tracking-tight text-[#bababa]">{u.username}</span>
                                        <button onClick={() => handleInvite(u.username)} disabled={isLoading} className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded text-[10px] font-black uppercase tracking-widest transition-all disabled:opacity-20 shadow-lg">Вызов</button>
                                    </div>
                                ))
                            )}
                        </div>
                        <div className="mt-4 pt-4 border-t border-[#3c3934]">
                            <label className="flex items-center gap-3 cursor-pointer group">
                                <div className="relative">
                                    <input type="checkbox" checked={useMocks} onChange={(e) => setUseMocks(e.target.checked)} className="sr-only" />
                                    <div className={`block w-10 h-6 rounded-full transition-colors ${useMocks ? 'bg-emerald-600' : 'bg-[#3c3934]'}`}></div>
                                    <div className={`dot absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition-transform ${useMocks ? 'transform translate-x-4' : ''}`}></div>
                                </div>
                                <span className="text-[10px] font-bold text-[#7d7d7d] uppercase tracking-widest group-hover:text-white transition-colors">Симуляция (Mocks)</span>
                            </label>
                        </div>
                    </div>

                    <div className="md:col-span-4 bg-[#262421] p-6 rounded border border-[#3c3934] shadow-lg flex flex-col h-[500px]">
                        <h2 className="text-[10px] font-black text-[#7d7d7d] uppercase mb-6 tracking-[0.2em] border-b border-[#3c3934] pb-2">Активные матчи (LIVE)</h2>
                        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                            {activeGames.length === 0 ? (
                                <p className="text-center py-20 opacity-30 text-[10px] uppercase font-bold tracking-widest">Нет игр</p>
                            ) : (
                                activeGames.map(game => (
                                    <div key={game.game_id} onClick={() => navigate(`/game/${game.game_id}`)} className="bg-[#1c1b18] p-4 rounded border border-[#3c3934] cursor-pointer hover:border-orange-500/50 transition-all">
                                        <div className="flex justify-between items-center mb-1">
                                            <span className="text-[9px] text-orange-500 font-black uppercase tracking-widest">Live Stream</span>
                                            <span className="text-[8px] text-[#5e5b56] font-mono">{game.game_id.slice(0,8)}</span>
                                        </div>
                                        <span className="text-xs font-bold text-gray-400">Смотреть партию</span>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;