import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, register } from '../api/auth';

const Auth = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);
        
        try {
            if (isLogin) {
                const data = await login(username, password);
                localStorage.setItem('access_token', data.access_token);
                navigate('/');
            } else {
                await register(username, password);
                const data = await login(username, password);
                localStorage.setItem('access_token', data.access_token);
                navigate('/');
            }
        } catch (err) {
            setError(err.response?.data?.detail || 'Ошибка авторизации');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-[#161512] font-sans selection:bg-emerald-500/30 p-4">
            <div className="w-full max-w-md">
                
                {/* LOGO */}
                <div className="text-center mb-10">
                    <div className="inline-block bg-emerald-600 text-white font-black text-4xl px-4 py-2 rounded shadow-2xl mb-4 shadow-emerald-900/20">AR</div>
                    <h1 className="text-2xl font-black text-white uppercase tracking-[0.3em] ml-2">CHESS</h1>
                    <div className="h-1 w-12 bg-emerald-600 mx-auto mt-4 rounded-full"></div>
                </div>

                <div className="bg-[#262421] p-8 rounded-lg border border-[#3c3934] shadow-2xl">
                    <h2 className="text-xs font-black text-[#7d7d7d] uppercase text-center mb-8 tracking-[0.4em]">
                        {isLogin ? 'Авторизация' : 'Регистрация'}
                    </h2>
                    
                    {error && (
                        <div className="bg-red-900/20 border border-red-500/30 text-red-400 p-4 rounded mb-6 text-[10px] font-black uppercase text-center tracking-widest animate-shake">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-[#5e5b56] uppercase tracking-widest ml-1">Username</label>
                            <input 
                                type="text" 
                                className="w-full bg-[#1c1b18] text-white border border-[#3c3934] rounded px-4 py-3 text-sm font-bold focus:outline-none focus:border-emerald-600 transition-all placeholder:text-[#3c3934]"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Имя игрока"
                                required
                            />
                        </div>
                        <div className="space-y-1">
                            <label className="text-[10px] font-black text-[#5e5b56] uppercase tracking-widest ml-1">Password</label>
                            <input 
                                type="password" 
                                className="w-full bg-[#1c1b18] text-white border border-[#3c3934] rounded px-4 py-3 text-sm font-bold focus:outline-none focus:border-emerald-600 transition-all placeholder:text-[#3c3934]"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                            />
                        </div>
                        
                        <button 
                            type="submit" 
                            disabled={isLoading}
                            className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-black py-4 px-4 rounded text-xs uppercase tracking-[0.2em] transition-all active:scale-95 disabled:opacity-50 mt-4 shadow-lg shadow-emerald-900/20"
                        >
                            {isLoading ? 'Загрузка...' : (isLogin ? 'Войти в игру' : 'Создать аккаунт')}
                        </button>
                    </form>

                    <div className="mt-8 text-center pt-6 border-t border-[#3c3934]">
                        <button 
                            onClick={() => { setIsLogin(!isLogin); setError(''); }} 
                            className="text-[10px] font-black text-[#5e5b56] hover:text-emerald-500 uppercase tracking-widest transition-colors"
                        >
                            {isLogin ? 'Нет аккаунта? Зарегистрироваться' : 'Есть аккаунт? Авторизоваться'}
                        </button>
                    </div>
                </div>

                <p className="text-center text-[#3c3934] text-[9px] font-bold uppercase tracking-widest mt-10">
                    &copy; 2024 IoT Chess System. Все права защищены.
                </p>
            </div>
        </div>
    );
};

export default Auth;