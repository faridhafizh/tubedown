import React, { useState, useEffect, useRef, useCallback } from 'react';
import './HackerDownloader.css';

const HackerDownloader = () => {
  // ==================== STATE ====================
  const [backendOnline, setBackendOnline] = useState(false);
  const [logs, setLogs] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [currentInput, setCurrentInput] = useState('');
  const [showHelp, setShowHelp] = useState(false);
  const [currentTime, setCurrentTime] = useState('');
  const [pendingUrl, setPendingUrl] = useState(null);
  const [availableFormats, setAvailableFormats] = useState([]);

  const terminalBodyRef = useRef(null);
  const inputRef = useRef(null);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);
  const timeTimerRef = useRef(null);

  const maxParallel = 3;

  // ==================== CONSTANTS ====================
  const asciiArt = `
╔═══════════════════════════════════════════════════════════════╗
║    ██╗   ██╗████████╗    ██╗  ██╗ █████╗  ██████╗██╗  ██╗   ║
║    ╚██╗ ██╔╝╚══██╔══╝    ██║  ██║██╔══██╗██╔════╝██║ ██╔╝   ║
║     ╚████╔╝    ██║       ███████║███████║██║     █████╔╝    ║
║      ╚██╔╝     ██║       ██╔══██║██╔══██║██║     ██╔═██╗    ║
║       ██║      ██║       ██║  ██║██║  ██║╚██████╗██║  ██╗   ║
║       ╚═╝      ╚═╝       ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ║
╠═══════════════════════════════════════════════════════════════╣
║         PARALLEL VIDEO DOWNLOADER - TERMINAL EDITION          ║
╚═══════════════════════════════════════════════════════════════╝
`;

  const helpText = `
╔═══════════════════════════════════════════════════════════════╗
║                         COMMANDS                              ║
╠═══════════════════════════════════════════════════════════════╣
║  /help, help     - Show this help panel                       ║
║  /clear, clear   - Clear terminal output                      ║
║  /status         - Check backend connection                   ║
║  /exit, quit     - Close terminal (refresh page)              ║
║  [URL]           - Paste YouTube URL to start download        ║
╠═══════════════════════════════════════════════════════════════╣
║  Press ESC to close this panel                                ║
╚═══════════════════════════════════════════════════════════════╝
`;

  // ==================== UTILITY FUNCTIONS ====================
  const addLog = useCallback((message, type = 'normal') => {
    setLogs(prev => {
      const newLogs = [...prev, { message, type }];
      return newLogs.length > 100 ? newLogs.slice(1) : newLogs;
    });
    // Auto-scroll
    setTimeout(() => {
      if (terminalBodyRef.current) {
        terminalBodyRef.current.scrollTop = terminalBodyRef.current.scrollHeight;
      }
    }, 50);
  }, []);

  const generateTaskId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
  };

  const activeDownloads = tasks.filter(t => t.status === 'downloading').length;

  // ==================== WEBSOCKET HANDLING ====================
  const connectWebSocket = useCallback(() => {
    const ws = new WebSocket('ws://localhost:8000/ws');
    wsRef.current = ws;

    ws.onopen = () => {
      setBackendOnline(true);
      addLog('[SYS] Connected to backend server', 'system');
      addLog('[SYS] Ready to download. Paste YouTube URL to begin.', 'system');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    ws.onclose = () => {
      setBackendOnline(false);
      addLog('[SYS] Connection lost. Reconnecting...', 'error');
      reconnectTimerRef.current = setTimeout(connectWebSocket, 3000);
    };

    ws.onerror = () => {
      setBackendOnline(false);
    };
  }, [addLog]);

  const handleWebSocketMessage = useCallback((data) => {
    switch (data.type) {
      case 'info':
        setTasks(prev => prev.map(t => 
          t.id === data.task_id ? { ...t, title: data.title, uploader: data.uploader } : t
        ));
        addLog(`[INFO] Fetched: ${data.title}`, 'system');
        break;

      case 'progress':
        setTasks(prev => prev.map(t => 
          t.id === data.task_id ? {
            ...t,
            status: data.status,
            percent: data.percent,
            speed: data.speed,
            eta: data.eta,
            filename: data.filename
          } : t
        ));
        break;

      case 'complete':
        setTasks(prev => prev.map(t => 
          t.id === data.task_id ? { ...t, status: 'completed', percent: 100 } : t
        ));
        addLog(`[SUCCESS] Download complete: ${data.title}`, 'success');
        setTimeout(() => {
          setTasks(prev => prev.filter(t => t.id !== data.task_id));
        }, 5000);
        break;

      case 'error':
        setTasks(prev => prev.map(t => 
          t.id === data.task_id ? { ...t, status: 'error' } : t
        ));
        addLog(`[ERROR] ${data.error}`, 'error');
        setTimeout(() => {
          setTasks(prev => prev.filter(t => t.id !== data.task_id));
        }, 5000);
        break;

      case 'queued':
        addLog(`[QUEUE] Download task ${data.task_id.slice(0, 8)} queued...`, 'system');
        break;

      default:
        break;
    }
  }, [addLog]);

  // ==================== COMMAND HANDLING ====================
  const startDownload = useCallback((url, formatId = 'best') => {
    if (!backendOnline) {
      addLog('[ERROR] Backend offline. Cannot start download.', 'error');
      return;
    }

    if (activeDownloads >= maxParallel) {
      addLog('[WARN] Max parallel downloads reached. Please wait.', 'system');
      return;
    }

    const taskId = generateTaskId();
    setTasks(prev => [...prev, {
      id: taskId,
      url,
      title: null,
      status: 'queued',
      percent: 0,
      speed: '...',
      eta: '???',
      filename: null,
    }]);

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'download',
        task_id: taskId,
        url: url,
        quality: formatId,
        format: 'mp4',
      }));
    }

    addLog(`[DOWNLOAD] Starting: ${url} (Quality: ${formatId})`, 'system');
  }, [backendOnline, activeDownloads, addLog]);

  const fetchVideoInfo = useCallback(async (url) => {
    addLog(`[SYS] Analyzing stream formats for ${url}...`, 'system');
    try {
      const response = await fetch(`http://localhost:8000/info?url=${encodeURIComponent(url)}`);
      const data = await response.json();

      if (data.success) {
        setAvailableFormats(data.formats);
        setPendingUrl(url);

        let formatList = `[SYS] Available formats for "${data.title}":\n`;
        data.formats.forEach((f, i) => {
          formatList += `${i + 1}) ${f.resolution} [${f.ext}] (ID: ${f.format_id})\n`;
        });
        formatList += `[SYS] Enter number to select or 'B' for Best Quality:`;

        addLog(formatList, 'system');
      } else {
        addLog(`[ERROR] Failed to fetch info: ${data.error}`, 'error');
      }
    } catch (e) {
      addLog(`[ERROR] Network error while fetching info: ${e.message}`, 'error');
    }
  }, [addLog]);
    const cleanCmd = cmd.replace(/^\//, '').toLowerCase();

    switch (cleanCmd) {
      case 'help':
        setShowHelp(prev => !prev);
        break;

      case 'clear':
        setLogs([]);
        addLog('[SYS] Terminal cleared', 'system');
        break;

      case 'status':
        addLog(`[SYS] Backend: ${backendOnline ? 'ONLINE' : 'OFFLINE'}`, 'system');
        addLog(`[SYS] Active downloads: ${activeDownloads}`, 'system');
        addLog(`[SYS] Download directory: ~/Downloads/YT-Hacker`, 'system');
        break;

      case 'exit':
      case 'quit':
        addLog('[SYS] Goodbye! Refresh page to restart.', 'system');
        if (wsRef.current) wsRef.current.close();
        break;

      default:
        addLog(`[ERR] Unknown command: ${cmd}`, 'error');
    }
  }, [backendOnline, activeDownloads, addLog]);

  const handleCommand = useCallback(() => {
    const input = currentInput.trim();
    if (!input) return;

    addLog(`> ${input}`, 'normal');

    if (pendingUrl) {
      // We are in quality selection mode
      const selection = input.toUpperCase();
      if (selection === 'B') {
        startDownload(pendingUrl, 'best');
        setPendingUrl(null);
        setAvailableFormats([]);
      } else {
        const index = parseInt(selection) - 1;
        if (index >= 0 && index < availableFormats.length) {
          const formatId = availableFormats[index].format_id;
          startDownload(pendingUrl, formatId);
          setPendingUrl(null);
          setAvailableFormats([]);
        } else {
          addLog(`[ERR] Invalid selection. Please enter a number between 1 and ${availableFormats.length} or 'B'.`, 'error');
        }
      }
      setCurrentInput('');
      return;
    }

    if (input.startsWith('/') || ['help', 'clear', 'status', 'exit', 'quit'].includes(input)) {
      handleBuiltInCommand(input);
    } else if (input.includes('youtube.com/watch') || input.includes('youtu.be/')) {
      fetchVideoInfo(input);
    } else {
      addLog(`[ERR] Unknown command or invalid URL: ${input}`, 'error');
    }

    setCurrentInput('');
  }, [currentInput, addLog, handleBuiltInCommand, startDownload, pendingUrl, availableFormats, fetchVideoInfo]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') {
      setShowHelp(false);
    }
    if (e.key === 'c' && e.ctrlKey) {
      setCurrentInput('');
      addLog('[SYS] Input cleared (Ctrl+C)', 'system');
    }
  }, [addLog]);

  const updateTime = useCallback(() => {
    const now = new Date();
    setCurrentTime(now.toLocaleTimeString('en-US', { hour12: false }));
  }, []);

  // ==================== EFFECTS ====================
  useEffect(() => {
    addLog('[BOOT] Initializing YT-Hacker Terminal v1.0...', 'system');
    addLog('[BOOT] Loading kernel modules...', 'system');
    addLog('[BOOT] Establishing backend connection...', 'system');

    connectWebSocket();
    timeTimerRef.current = setInterval(updateTime, 1000);
    updateTime();

    inputRef.current?.focus();

    const handleClick = () => inputRef.current?.focus();
    document.addEventListener('click', handleClick);

    return () => {
      if (wsRef.current) wsRef.current.close();
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (timeTimerRef.current) clearInterval(timeTimerRef.current);
      document.removeEventListener('click', handleClick);
    };
  }, [addLog, connectWebSocket, updateTime]);

  // ==================== RENDER ====================
  return (
    <div className="hacker-terminal">
      {/* Header */}
      <div className="terminal-header">
        <pre className="ascii-art">{asciiArt}</pre>
        <div className="status-bar">
          <span className={`status-led ${backendOnline ? 'online' : ''}`}></span>
          <span>{backendOnline ? 'SYS.ONLINE' : 'SYS.OFFLINE'}</span>
          <span className="divider">|</span>
          <span>DOWNLOADS: {activeDownloads}/{maxParallel}</span>
          <span className="divider">|</span>
          <span>{currentTime}</span>
        </div>
      </div>

      {/* Terminal Body */}
      <div className="terminal-body" ref={terminalBodyRef}>
        {/* Output Logs */}
        <div className="terminal-output">
          {logs.map((log, idx) => (
            <div key={idx} className={`log-line ${log.type}`}>
              <span className="prompt">&gt;</span>
              <span className={`${log.type}-text`}>{log.message}</span>
            </div>
          ))}
        </div>

        {/* Download Progress Bars */}
        {tasks.map(task => (
          <div key={task.id} className="task-progress">
            <div className="task-header">
              <span className="task-id">[TASK_{task.id.slice(0, 8)}]</span>
              <span className="task-title">{task.title || 'Fetching info...'}</span>
              <span className="task-status">{task.status}</span>
            </div>
            <div className="progress-bar-container">
              <div className="progress-bar" style={{ width: `${task.percent}%` }}>
                <span className="progress-text">{task.percent}%</span>
              </div>
            </div>
            <div className="task-info">
              <span>⚡ {task.speed || '...'}</span>
              <span>⏱️ ETA: {task.eta || '???'}s</span>
            </div>
          </div>
        ))}

        {/* Input Area */}
        <div className="terminal-input-area">
          <span className="input-prompt">$</span>
          <input
            ref={inputRef}
            value={currentInput}
            onChange={(e) => setCurrentInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCommand()}
            onKeyUp={handleKeyDown}
            className="terminal-input"
            type="text"
            placeholder="Enter YouTube URL or command..."
            autoFocus
          />
        </div>
      </div>

      {/* Help Panel */}
      {showHelp && (
        <div className="help-panel">
          <pre>{helpText}</pre>
        </div>
      )}
    </div>
  );
};

export default HackerDownloader;