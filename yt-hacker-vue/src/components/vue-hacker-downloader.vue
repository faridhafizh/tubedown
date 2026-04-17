<template>
  <div class="hacker-terminal">
    <!-- Header Matrix Effect -->
    <div class="terminal-header">
      <pre class="ascii-art">{{ asciiArt }}</pre>
      <div class="status-bar">
        <span class="status-led" :class="{ online: backendOnline }"></span>
        <span>{{ backendOnline ? 'SYS.ONLINE' : 'SYS.OFFLINE' }}</span>
        <span class="divider">|</span>
        <span>DOWNLOADS: {{ activeDownloads }}/{{ maxParallel }}</span>
        <span class="divider">|</span>
        <span>{{ currentTime }}</span>
      </div>
    </div>

    <!-- Main Terminal Area -->
    <div class="terminal-body" ref="terminalBody">
      <!-- Output Logs -->
      <div class="terminal-output">
        <div v-for="(log, idx) in logs" :key="idx" :class="['log-line', log.type]">
          <span class="prompt">></span>
          <span v-if="log.type === 'system'" class="system-text">{{ log.message }}</span>
          <span v-else-if="log.type === 'error'" class="error-text">{{ log.message }}</span>
          <span v-else-if="log.type === 'success'" class="success-text">{{ log.message }}</span>
          <span v-else>{{ log.message }}</span>
        </div>
      </div>

      <!-- Download Progress Bars -->
      <div v-for="task in tasks" :key="task.id" class="task-progress">
        <div class="task-header">
          <span class="task-id">[TASK_{{ task.id.slice(0, 8) }}]</span>
          <span class="task-title">{{ task.title || 'Fetching info...' }}</span>
          <span class="task-status">{{ task.status }}</span>
        </div>
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: task.percent + '%' }">
            <span class="progress-text">{{ task.percent }}%</span>
          </div>
        </div>
        <div class="task-info">
          <span>⚡ {{ task.speed || '...' }}</span>
          <span>⏱️ ETA: {{ task.eta || '???' }}s</span>
        </div>
      </div>

      <!-- Input Area -->
      <div class="terminal-input-area">
        <span class="input-prompt">$</span>
        <input
          ref="inputField"
          v-model="currentInput"
          @keydown.enter="handleCommand"
          @keydown="handleKeyDown"
          class="terminal-input"
          type="text"
          placeholder="Enter YouTube URL or command..."
          autofocus
        />
      </div>
    </div>

    <!-- Help Panel -->
    <div class="help-panel" v-if="showHelp">
      <pre>{{ helpText }}</pre>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'

// ==================== STATE ====================
const backendOnline = ref(false)
const logs = ref([])
const tasks = ref([])
const currentInput = ref('')
const showHelp = ref(false)
const terminalBody = ref(null)
const inputField = ref(null)
const currentTime = ref('')
const pendingUrl = ref(null)
const availableFormats = ref([])

let ws = null
let reconnectTimer = null
let timeTimer = null

// ==================== COMPUTED ====================
const activeDownloads = computed(() => tasks.value.filter(t => t.status === 'downloading').length)
const maxParallel = ref(3) // Max parallel downloads

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
`

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
`

// ==================== METHODS ====================
function addLog(message, type = 'normal') {
  logs.value.push({ message, type })
  if (logs.value.length > 100) {
    logs.value.shift()
  }
  nextTick(() => {
    if (terminalBody.value) {
      terminalBody.value.scrollTop = terminalBody.value.scrollHeight
    }
  })
}

function generateTaskId() {
  return Date.now().toString(36) + Math.random().toString(36).substr(2, 5)
}

function connectWebSocket() {
  ws = new WebSocket('ws://localhost:8000/ws')

  ws.onopen = () => {
    backendOnline.value = true
    addLog('[SYS] Connected to backend server', 'system')
    addLog('[SYS] Ready to download. Paste YouTube URL to begin.', 'system')
  }

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data)
    handleWebSocketMessage(data)
  }

  ws.onclose = () => {
    backendOnline.value = false
    addLog('[SYS] Connection lost. Reconnecting...', 'error')
    reconnectTimer = setTimeout(connectWebSocket, 3000)
  }

  ws.onerror = () => {
    backendOnline.value = false
  }
}

function handleWebSocketMessage(data) {
  switch (data.type) {
    case 'info':
      const task = tasks.value.find(t => t.id === data.task_id)
      if (task) {
        task.title = data.title
        task.uploader = data.uploader
        addLog(`[INFO] Fetched: ${data.title}`, 'system')
      }
      break

    case 'progress':
      const existingTask = tasks.value.find(t => t.id === data.task_id)
      if (existingTask) {
        existingTask.status = data.status
        existingTask.percent = data.percent
        existingTask.speed = data.speed
        existingTask.eta = data.eta
        existingTask.filename = data.filename
      }
      break

    case 'complete':
      const completedTask = tasks.value.find(t => t.id === data.task_id)
      if (completedTask) {
        completedTask.status = 'completed'
        completedTask.percent = 100
        addLog(`[SUCCESS] Download complete: ${data.title}`, 'success')
        setTimeout(() => {
          tasks.value = tasks.value.filter(t => t.id !== data.task_id)
        }, 5000)
      }
      break

    case 'error':
      const errorTask = tasks.value.find(t => t.id === data.task_id)
      if (errorTask) {
        errorTask.status = 'error'
        addLog(`[ERROR] ${data.error}`, 'error')
        setTimeout(() => {
          tasks.value = tasks.value.filter(t => t.id !== data.task_id)
        }, 5000)
      }
      break

    case 'queued':
      addLog(`[QUEUE] Download task ${data.task_id.slice(0, 8)} queued...`, 'system')
      break
  }
}

function startDownload(url, formatId = 'best') {
  if (!backendOnline.value) {
    addLog('[ERROR] Backend offline. Cannot start download.', 'error')
    return
  }

  // Cek max parallel
  if (activeDownloads.value >= maxParallel.value) {
    addLog('[WARN] Max parallel downloads reached. Please wait.', 'system')
    return
  }

  const taskId = generateTaskId()
  tasks.value.push({
    id: taskId,
    url,
    title: null,
    status: 'queued',
    percent: 0,
    speed: '...',
    eta: '???',
    filename: null,
  })

  ws.send(JSON.stringify({
    action: 'download',
    task_id: taskId,
    url: url,
    quality: formatId,
    format: 'mp4',
  }))

  addLog(`[DOWNLOAD] Starting: ${url} (Quality: ${formatId})`, 'system')
}

async function fetchVideoInfo(url) {
  addLog(`[SYS] Analyzing stream formats for ${url}...`, 'system')
  try {
    const response = await fetch(`http://localhost:8000/info?url=${encodeURIComponent(url)}`)
    const data = await response.json()

    if (data.success) {
      availableFormats.value = data.formats
      pendingUrl.value = url

      let formatList = `[SYS] Available formats for "${data.title}":\n`
      data.formats.forEach((f, i) => {
        formatList += `${i + 1}) ${f.resolution} [${f.ext}] (ID: ${f.format_id})\n`
      })
      formatList += `[SYS] Enter number to select or 'B' for Best Quality:`

      addLog(formatList, 'system')
    } else {
      addLog(`[ERROR] Failed to fetch info: ${data.error}`, 'error')
    }
  } catch (e) {
    addLog(`[ERROR] Network error while fetching info: ${e.message}`, 'error')
  }
}

function handleCommand() {
  const input = currentInput.value.trim()
  if (!input) return

  addLog(`> ${input}`, 'normal')

  if (pendingUrl.value) {
    // We are in quality selection mode
    const selection = input.toUpperCase()
    if (selection === 'B') {
      startDownload(pendingUrl.value, 'best')
      pendingUrl.value = null
      availableFormats.value = []
    } else {
      const index = parseInt(selection) - 1
      if (index >= 0 && index < availableFormats.value.length) {
        const formatId = availableFormats.value[index].format_id
        startDownload(pendingUrl.value, formatId)
        pendingUrl.value = null
        availableFormats.value = []
      } else {
        addLog(`[ERR] Invalid selection. Please enter a number between 1 and ${availableFormats.value.length} or 'B'.`, 'error')
      }
    }
    currentInput.value = ''
    return
  }

  // Commands
  if (input.startsWith('/') || ['help', 'clear', 'status', 'exit', 'quit'].includes(input)) {
    handleBuiltInCommand(input)
  }
  // YouTube URL
  else if (input.includes('youtube.com/watch') || input.includes('youtu.be/')) {
    fetchVideoInfo(input)
  }
  else {
    addLog(`[ERR] Unknown command or invalid URL: ${input}`, 'error')
  }

  currentInput.value = ''
}

function handleBuiltInCommand(cmd) {
  const cleanCmd = cmd.replace(/^\//, '').toLowerCase()

  switch (cleanCmd) {
    case 'help':
      showHelp.value = !showHelp.value
      break

    case 'clear':
      logs.value = []
      addLog('[SYS] Terminal cleared', 'system')
      break

    case 'status':
      addLog(`[SYS] Backend: ${backendOnline.value ? 'ONLINE' : 'OFFLINE'}`, 'system')
      addLog(`[SYS] Active downloads: ${activeDownloads.value}`, 'system')
      addLog(`[SYS] Download directory: ~/Downloads/YT-Hacker`, 'system')
      break

    case 'exit':
    case 'quit':
      addLog('[SYS] Goodbye! Refresh page to restart.', 'system')
      if (ws) ws.close()
      break

    default:
      addLog(`[ERR] Unknown command: ${cmd}`, 'error')
  }
}

function handleKeyDown(e) {
  if (e.key === 'Escape') {
    showHelp.value = false
  }
  if (e.key === 'c' && e.ctrlKey) {
    currentInput.value = ''
    addLog('[SYS] Input cleared (Ctrl+C)', 'system')
  }
}

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-US', { hour12: false })
}

// ==================== LIFECYCLE ====================
onMounted(() => {
  // Matrix intro
  addLog('[BOOT] Initializing YT-Hacker Terminal v1.0...', 'system')
  addLog('[BOOT] Loading kernel modules...', 'system')
  addLog('[BOOT] Establishing backend connection...', 'system')

  connectWebSocket()
  timeTimer = setInterval(updateTime, 1000)
  updateTime()

  // Focus input on mount
  nextTick(() => {
    inputField.value?.focus()
  })

  // Click anywhere to focus input
  document.addEventListener('click', () => {
    inputField.value?.focus()
  })
})

onUnmounted(() => {
  if (ws) ws.close()
  if (reconnectTimer) clearTimeout(reconnectTimer)
  if (timeTimer) clearInterval(timeTimer)
})
</script>

<style scoped>
.hacker-terminal {
  background: #0c0c0c;
  color: #00ff41;
  font-family: 'Courier New', 'Fira Code', 'Consolas', monospace;
  min-height: 100vh;
  padding: 20px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.terminal-header {
  margin-bottom: 20px;
}

.ascii-art {
  color: #00ff41;
  font-size: 12px;
  line-height: 1.2;
  margin: 0 0 10px 0;
  text-shadow: 0 0 5px #00ff41;
}

.status-bar {
  display: flex;
  gap: 15px;
  padding: 8px 15px;
  background: #1a1a1a;
  border: 1px solid #00ff41;
  border-radius: 4px;
  font-size: 14px;
}

.status-led {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ff0000;
  display: inline-block;
  margin-right: 5px;
  box-shadow: 0 0 5px #ff0000;
}

.status-led.online {
  background: #00ff41;
  box-shadow: 0 0 10px #00ff41;
}

.divider {
  color: #333;
}

.terminal-body {
  flex: 1;
  background: #0c0c0c;
  border: 1px solid #00ff41;
  border-radius: 4px;
  padding: 15px;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

.terminal-output {
  margin-bottom: 20px;
}

.log-line {
  line-height: 1.5;
  word-break: break-all;
}

.log-line .prompt {
  color: #00ff41;
  margin-right: 8px;
}

.log-line.system .system-text {
  color: #00bfff;
}

.log-line.error .error-text {
  color: #ff4444;
}

.log-line.success .success-text {
  color: #00ff41;
}

.task-progress {
  margin: 15px 0;
  padding: 10px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
}

.task-header {
  display: flex;
  gap: 15px;
  margin-bottom: 8px;
  font-size: 13px;
}

.task-id {
  color: #ffaa00;
}

.task-title {
  color: #00ff41;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-status {
  color: #00bfff;
}

.progress-bar-container {
  background: #0c0c0c;
  border: 1px solid #00ff41;
  height: 24px;
  border-radius: 2px;
  overflow: hidden;
}

.progress-bar {
  background: linear-gradient(90deg, #00ff41, #00aa2b);
  height: 100%;
  transition: width 0.3s;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding-right: 10px;
}

.progress-text {
  color: #000;
  font-weight: bold;
  font-size: 12px;
}

.task-info {
  display: flex;
  gap: 20px;
  margin-top: 8px;
  font-size: 12px;
  color: #888;
}

.terminal-input-area {
  display: flex;
  align-items: center;
  margin-top: 20px;
  padding: 10px;
  background: #1a1a1a;
  border: 1px solid #00ff41;
  border-radius: 4px;
}

.input-prompt {
  color: #00ff41;
  margin-right: 10px;
  font-weight: bold;
}

.terminal-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #00ff41;
  font-family: inherit;
  font-size: 14px;
  outline: none;
}

.terminal-input::placeholder {
  color: #006600;
}

.help-panel {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: #0c0c0c;
  border: 2px solid #00ff41;
  padding: 20px;
  box-shadow: 0 0 30px rgba(0, 255, 65, 0.3);
  z-index: 1000;
}

.help-panel pre {
  color: #00ff41;
  margin: 0;
  font-family: inherit;
  font-size: 13px;
}

/* Scrollbar Styling */
.terminal-body::-webkit-scrollbar {
  width: 8px;
}

.terminal-body::-webkit-scrollbar-track {
  background: #0c0c0c;
}

.terminal-body::-webkit-scrollbar-thumb {
  background: #00ff41;
  border-radius: 4px;
}

.terminal-body::-webkit-scrollbar-thumb:hover {
  background: #00aa2b;
}
</style>