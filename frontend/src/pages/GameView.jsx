import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import mqtt from 'mqtt';
import { Chessground } from 'chessground';
import { surrenderGame } from '../api/game';

import 'chessground/assets/chessground.base.css';
import 'chessground/assets/chessground.brown.css';
import 'chessground/assets/chessground.cburnett.css';

const coordsToSquare = (coords) => {
    if (!coords || coords[0] < 0 || coords[1] < 0) return null;
    const files = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'];
    return `${files[coords[1]]}${coords[0] + 1}`;
};

const GameView = () => {
    const { gameId } = useParams();
    const navigate = useNavigate();
    const boardRef = useRef(null);
    const cgRef = useRef(null);
    
    const [mqttStatus, setMqttStatus] = useState('Подключение...');
    const [engineState, setEngineState] = useState(null);
    const [showExitModal, setShowExitModal] = useState(false);
    const [errorNote, setErrorNote] = useState(null);
    const [isLongLoading, setIsLongLoading] = useState(false);

    const handleSurrender = async () => {
        try {
            await surrenderGame(gameId);
            setShowExitModal(false);
            navigate('/');
        } catch (err) {
            setErrorNote(err.response?.data?.detail || "Ошибка при остановке игры");
            setTimeout(() => setErrorNote(null), 3000);
            setShowExitModal(false);
        }
    };

    useEffect(() => {
        if (boardRef.current && !cgRef.current) {
            cgRef.current = Chessground(boardRef.current, {
                fen: 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR',
                viewOnly: true,
                coordinates: true,
                animation: { enabled: true, duration: 250 },
                drawable: { enabled: true }
            });
        }
        return () => cgRef.current?.destroy();
    }, []);

    useEffect(() => {
        if (!gameId) return;
        const client = mqtt.connect(import.meta.env.VITE_MQTT_URL);

        client.on('connect', () => {
            setMqttStatus('В эфире 🟢');
            client.subscribe(`game/${gameId}/state`);
        });

        client.on('message', (topic, message) => {
            try {
                if (message.length === 0) return;
                const data = JSON.parse(message.toString());
                
                if (data.game_status === 'aborted') {
                    navigate('/');
                    return;
                }

                setEngineState(data);
                setIsLongLoading(false);

                if (cgRef.current) {
                    const shapes = [];
                    let checkSquare = false;

                    if (data.status && Array.isArray(data.status)) {
                        data.status.forEach(s => {
                            const sq = coordsToSquare(s.square);
                            if (!sq) return;

                            if (s.description === 'check') checkSquare = sq;
                            else if (s.description === 'wrongmove') shapes.push({ orig: sq, brush: 'red' });
                            else if (s.description === 'missing_piece') shapes.push({ orig: sq, brush: 'blue' });
                            else if (s.description === 'available_moves') shapes.push({ orig: sq, brush: 'green' });
                        });
                    }

                    const cgConfig = {
                        fen: data.fen.split(' ')[0],
                        check: checkSquare,
                        lastMove: data.last_move ? [data.last_move.slice(0, 2), data.last_move.slice(2, 4)] : [],
                        drawable: { autoShapes: shapes }
                    };

                    if (data.engine_state === "PIECE_LIFTED" && data.lifted_sq) {
                        const liftedKey = coordsToSquare(data.lifted_sq);
                        cgConfig.selected = liftedKey;
                        cgConfig.highlight = { lastMove: true, check: true };
                    } else {
                        cgConfig.selected = null;
                    }

                    cgRef.current.set(cgConfig);
                }
            } catch (e) {
                console.error(e);
            }
        });

        const timeout = setTimeout(() => {
            if (!engineState) setIsLongLoading(true);
        }, 8000);

        return () => {
            client.end();
            clearTimeout(timeout);
        };
    }, [gameId, engineState, navigate]);

    return (
        <div className="min-h-screen bg-[#161512] text-[#bababa] p-4 font-sans selection:bg-orange-500/30 overflow-hidden">
            {errorNote && (
                <div className="fixed top-5 right-5 z-[100] bg-red-600 text-white px-6 py-3 rounded shadow-2xl animate-bounce text-sm font-bold uppercase tracking-widest">
                    {errorNote}
                </div>
            )}

            {showExitModal && (
                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm transition-all">
                    <div className="bg-[#262421] border border-[#3c3934] p-8 rounded-lg max-w-sm w-full shadow-2xl text-center">
                        <h3 className="text-white text-xl font-black uppercase mb-4 tracking-tighter">Завершить матч?</h3>
                        <p className="text-[#7d7d7d] text-sm mb-8">Это действие остановит игровой движок и удалит текущую сессию.</p>
                        <div className="flex gap-3">
                            <button onClick={() => setShowExitModal(false)} className="flex-1 py-3 rounded font-bold text-xs uppercase tracking-widest text-[#7d7d7d] hover:bg-[#3c3934] transition-colors">Отмена</button>
                            <button onClick={handleSurrender} className="flex-1 py-3 bg-red-600 hover:bg-red-500 text-white rounded font-bold text-xs uppercase tracking-widest transition-transform active:scale-95 shadow-lg shadow-red-600/20">Подтвердить</button>
                        </div>
                    </div>
                </div>
            )}

            <div className="max-w-6xl mx-auto">
                <div className="flex justify-between items-center mb-6 bg-[#262421] p-4 rounded border border-[#3c3934] shadow-xl">
                    <div className="flex gap-4">
                        <button onClick={() => navigate('/')} className="hover:text-white transition-colors uppercase text-[10px] font-black tracking-widest bg-[#1c1b18] px-4 py-2 rounded border border-[#3c3934]">← В Лобби</button>
                        <button onClick={() => setShowExitModal(true)} className="bg-red-900/10 hover:bg-red-900/30 text-red-500 px-4 py-2 rounded text-[10px] font-black uppercase tracking-widest border border-red-900/30 transition-all">Прервать матч</button>
                    </div>

                    <div className="px-4 py-2 rounded bg-[#1c1b18] text-emerald-500 text-[10px] font-black border border-[#3c3934] shadow-inner tracking-widest">
                        {mqttStatus}
                    </div>
                </div>

                {engineState?.engine_state === "DESYNC" && (
                    <div className="mb-6 bg-red-600/10 border border-red-500/50 p-4 rounded-lg flex items-center gap-4 animate-pulse">
                        <div className="w-8 h-8 bg-red-600/20 rounded-full flex items-center justify-center text-red-500 shrink-0 text-xs">⚠️</div>
                        <div className="text-red-400 font-black uppercase tracking-widest text-[10px]">Ошибка расстановки: проверьте доску</div>
                    </div>
                )}

                {!engineState && mqttStatus.includes('🟢') && (
                    <div className="mb-6 bg-blue-600/10 border border-blue-500/50 p-4 rounded-lg flex items-center justify-between animate-pulse">
                        <div className="flex items-center gap-4">
                            <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin"></div>
                            <div className="text-blue-400 font-black uppercase tracking-widest text-[10px]">
                                {isLongLoading ? "Ожидание второго игрока или данных с камеры..." : "Синхронизация оборудования..."}
                            </div>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                    <div className="lg:col-span-7 flex flex-col items-center">
                        <div className="p-1.5 bg-[#3c3934] rounded shadow-2xl relative">
                            {engineState?.engine_state === "GAME_OVER" && (
                                <div className="absolute inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col items-center justify-center rounded transition-all">
                                    <div className="bg-[#262421] p-10 rounded border border-[#3c3934] text-center shadow-2xl">
                                        <div className="text-[10px] text-orange-500 font-bold uppercase tracking-[0.3em] mb-2">Матч завершен</div>
                                        <h2 className="text-4xl font-black text-white mb-6 uppercase tracking-tighter">
                                            {engineState.game_status === 'mate' ? 'Шах и мат' : 'Конец игры'}
                                        </h2>
                                        <button onClick={() => navigate('/')} className="w-full py-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded font-black uppercase text-xs tracking-widest transition-all">
                                            Вернуться в меню
                                        </button>
                                    </div>
                                </div>
                            )}
                            <div ref={boardRef} style={{ width: '560px', height: '560px' }} className="cg-board-wrapper" />
                        </div>
                    </div>

                    <div className="lg:col-span-5 space-y-4">
                        <div className="bg-[#262421] p-8 rounded shadow-xl border border-[#3c3934]">
                            <h2 className="text-[10px] font-black text-[#7d7d7d] uppercase mb-8 tracking-[0.2em] border-b border-[#3c3934] pb-2">Информация</h2>
                            {engineState ? (
                                <div className="space-y-8">
                                    <div className="flex justify-between items-center">
                                        <span className="text-[#7d7d7d] text-[10px] font-bold uppercase tracking-widest opacity-50">Очередь</span>
                                        <span className={`text-2xl font-black tracking-tighter ${engineState.is_white_turn ? 'text-white' : 'text-gray-500'}`}>
                                            {engineState.is_white_turn ? 'БЕЛЫЕ' : 'ЧЕРНЫЕ'}
                                        </span>
                                    </div>
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-[#1c1b18] p-4 rounded border border-[#3c3934]">
                                            <div className="text-[9px] text-[#7d7d7d] uppercase mb-2 font-bold opacity-50 tracking-widest">Движок</div>
                                            <div className={`font-mono text-xs uppercase font-black tracking-widest ${
                                                engineState.engine_state === 'PLAYING' ? 'text-emerald-400' :
                                                engineState.engine_state === 'DESYNC' ? 'text-red-500' : 'text-orange-500'
                                            }`}>
                                                {engineState.engine_state}
                                            </div>
                                        </div>
                                        <div className="bg-[#1c1b18] p-4 rounded border border-[#3c3934]">
                                            <div className="text-[9px] text-[#7d7d7d] uppercase mb-2 font-bold opacity-50 tracking-widest">Датчики</div>
                                            <div className={`text-[10px] font-bold uppercase tracking-widest ${engineState.is_piece_chosen ? 'text-emerald-400' : 'text-[#4d4b47]'}`}>
                                                {engineState.is_piece_chosen ? 'Поднята' : 'На доске'}
                                            </div>
                                        </div>
                                    </div>
                                    <div className="bg-[#1c1b18] p-4 rounded border border-[#3c3934]">
                                        <div className="text-[9px] text-[#7d7d7d] uppercase mb-3 font-bold tracking-widest opacity-50">Текущий FEN</div>
                                        <div className="text-[10px] font-mono text-[#5e5b56] break-all leading-tight">
                                            {engineState.fen}
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="py-24 text-center">
                                    <div className="w-10 h-10 border-2 border-orange-500/20 border-t-orange-500 rounded-full animate-spin mx-auto mb-4"></div>
                                    <div className="text-[#4d4b47] uppercase text-[10px] font-black tracking-[0.2em]">Ждем начала...</div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GameView;