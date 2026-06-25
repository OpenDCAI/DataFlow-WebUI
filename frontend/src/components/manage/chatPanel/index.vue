<template>
    <div class="chat-panel" :class="{ dark: theme === 'dark' }">
        <!-- 顶部工具栏 -->
        <div class="chat-header">
            <div class="chat-title">
                <i class="ms-Icon ms-Icon--Robot" style="margin-right: 6px; font-size: 16px;"></i>
                <span>DataFlow 助手</span>
                <select
                    class="chat-agent-select"
                    :value="agentKind"
                    :disabled="isLoading"
                    :title="isLoading ? '当前对话进行中，无法切换 agent' : '选择代码 agent'"
                    @change="onAgentChange"
                >
                    <option v-for="a in availableAgents" :key="a.kind" :value="a.kind">
                        {{ a.label }}
                    </option>
                </select>
            </div>
            <div class="chat-header-actions">
                <!-- 历史会话列表 -->
                <fv-button
                    :theme="theme"
                    title="历史会话"
                    style="width: 28px; height: 28px; border-radius: 50%;"
                    @click="toggleHistoryPanel"
                >
                    <i class="ms-Icon ms-Icon--History" style="font-size: 12px;"></i>
                </fv-button>
                <!-- 新建会话：脱离当前 session，保留历史 -->
                <fv-button
                    :theme="theme"
                    title="新建对话"
                    style="width: 28px; height: 28px; border-radius: 50%; margin-left: 4px;"
                    @click="newSession"
                >
                    <i class="ms-Icon ms-Icon--Add" style="font-size: 12px;"></i>
                </fv-button>
                <!-- 终止并清除：kill 正在运行的 claude 进程，同时清空对话历史 -->
                <fv-button
                    :theme="theme"
                    :title="isLoading ? '终止运行并清除对话' : '清除对话历史'"
                    style="width: 28px; height: 28px; border-radius: 50%; margin-left: 4px;"
                    @click="abortAndClear"
                >
                    <i
                        class="ms-Icon"
                        :class="isLoading ? 'ms-Icon--StopSolid' : 'ms-Icon--Delete'"
                        style="font-size: 12px;"
                    ></i>
                </fv-button>
            </div>
        </div>

        <!-- 历史会话抽屉 -->
        <div v-if="showHistoryPanel" class="history-overlay" @click.self="showHistoryPanel = false">
            <div class="history-panel">
                <div class="history-head">
                    <span>历史会话</span>
                    <i class="ms-Icon ms-Icon--Cancel history-close" @click="showHistoryPanel = false"></i>
                </div>
                <div v-if="historyList.length === 0" class="history-empty">
                    还没有历史对话
                </div>
                <div v-else class="history-list">
                    <div
                        v-for="s in historyList"
                        :key="s.session_id"
                        class="history-item"
                        :class="{ active: s.session_id === currentSessionId }"
                        @click="switchSession(s.session_id)"
                    >
                        <div class="history-item-title">{{ s.title || s.session_id }}</div>
                        <div class="history-item-meta">
                            <span>{{ formatTime(s.updated_at) }}</span>
                            <span>· {{ s.message_count || 0 }} 轮</span>
                        </div>
                        <i
                            class="ms-Icon ms-Icon--Delete history-item-del"
                            title="删除"
                            @click.stop="deleteSession(s.session_id)"
                        ></i>
                    </div>
                </div>
            </div>
        </div>

        <!-- 消息列表区 -->
        <div class="chat-messages" ref="messagesContainer">
            <div v-if="messages.length === 0" class="chat-empty">
                <i class="ms-Icon ms-Icon--ChatInviteFriend" style="font-size: 40px; opacity: 0.3; display: block; text-align: center; margin-bottom: 12px;"></i>
                <p>你好！我是 DataFlow 助手。</p>
                <p>你可以告诉我需要构建什么样的数据处理 Pipeline，我来帮你设计和创建。</p>
                <p class="chat-empty-hint">
                    使用 Cursor IDE？把它的 MCP 指向本后端
                    （<code>./scripts/setup_agent.sh cursor</code>），就能在 Cursor 里直接对话并把
                    pipeline 推到这个画布上。
                </p>
            </div>
            <div
                v-for="(msg, idx) in messages"
                :key="idx"
                class="chat-message"
                :class="msg.role"
            >
                <div class="message-avatar">
                    <i v-if="msg.role === 'user'" class="ms-Icon ms-Icon--Contact"></i>
                    <i v-else-if="msg.role === 'tool'" class="ms-Icon ms-Icon--Settings"></i>
                    <i v-else class="ms-Icon ms-Icon--Robot"></i>
                </div>
                <div class="message-content">
                    <!-- Agent 工具调用条目 -->
                    <div v-if="msg.role === 'tool'" class="tool-call-card" :class="msg.status">
                        <div class="tool-call-head" @click="msg.expanded = !msg.expanded">
                            <i
                                class="ms-Icon"
                                :class="msg.status === 'running'
                                    ? 'ms-Icon--ProgressRingDots'
                                    : (msg.is_error ? 'ms-Icon--ErrorBadge' : 'ms-Icon--CheckMark')"
                                style="margin-right: 6px;"
                            ></i>
                            <span class="tool-name">{{ formatToolName(msg.name) }}</span>
                            <span v-if="msg.status === 'running'" class="tool-status">调用中…</span>
                            <span v-else-if="msg.is_error" class="tool-status error">失败</span>
                            <span v-else class="tool-status done">完成</span>
                            <i
                                class="ms-Icon ms-Icon--ChevronDown tool-toggle"
                                :class="{ expanded: msg.expanded }"
                            ></i>
                        </div>
                        <div v-if="msg.expanded" class="tool-call-body">
                            <div v-if="msg.input_preview" class="tool-kv">
                                <div class="tool-kv-label">input</div>
                                <pre class="tool-kv-value">{{ msg.input_preview }}</pre>
                            </div>
                            <div v-if="msg.output_preview" class="tool-kv">
                                <div class="tool-kv-label">output</div>
                                <pre class="tool-kv-value">{{ msg.output_preview }}</pre>
                            </div>
                        </div>
                    </div>
                    <div
                        v-else-if="msg.role === 'assistant'"
                        class="message-text markdown-body"
                        v-html="renderMarkdown(msg.content)"
                    ></div>
                    <div v-else class="message-text">{{ msg.content }}</div>
                    <span v-if="msg.streaming" class="streaming-cursor">▋</span>
                </div>
            </div>
            <!-- 加载指示器 -->
            <div v-if="isLoading && !hasStreamingMessage" class="chat-message assistant">
                <div class="message-avatar">
                    <i class="ms-Icon ms-Icon--Robot"></i>
                </div>
                <div class="message-content">
                    <div class="loading-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>
            </div>
        </div>

        <!-- 底部输入区 -->
        <div class="chat-input-area">
            <div class="chat-input-wrapper">
                <textarea
                    ref="inputRef"
                    v-model="inputText"
                    class="chat-input"
                    :placeholder="isLoading ? '等待回复中...' : '输入你的需求，例如：帮我创建一个 QA 生成 pipeline...'"
                    :disabled="isLoading"
                    @keydown.enter.exact.prevent="sendMessage"
                    @keydown.shift.enter="inputText += '\n'"
                    rows="3"
                ></textarea>
                <fv-button
                    theme="dark"
                    background="linear-gradient(90deg, rgba(69, 98, 213, 1), rgba(161, 145, 206, 1))"
                    foreground="rgba(255, 255, 255, 1)"
                    border-radius="8"
                    :disabled="isLoading || !inputText.trim()"
                    style="width: 72px; height: 36px; flex-shrink: 0;"
                    @click="sendMessage"
                >
                    <i class="ms-Icon ms-Icon--Send" style="font-size: 14px;"></i>
                </fv-button>
            </div>
            <p class="chat-hint">Enter 发送，Shift+Enter 换行</p>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import { useDataflow } from '@/stores/dataflow'
import MarkdownIt from 'markdown-it'
import axios from 'axios'

const md = new MarkdownIt({
    html: false,
    linkify: true,
    typographer: true,
    breaks: true,
})

// 生成唯一用户 ID（存在 sessionStorage，刷新后保持）
function getUserId() {
    let uid = sessionStorage.getItem('df_agent_user_id')
    if (!uid) {
        uid = 'user_' + Math.random().toString(36).slice(2, 10)
        sessionStorage.setItem('df_agent_user_id', uid)
    }
    return uid
}

// 上次选用的 agent 类型（claude / codex），跨刷新保留
// Cursor 不在此列表中：Cursor 在 IDE 内通过 MCP 直接连本 WebUI（render_pipeline_in_editor），
// 不需要 WebUI 后端把它 spawn 成 headless 子进程。
const AGENT_KIND_KEY = 'df_agent_kind'
const DEFAULT_AGENT_KIND = 'claude'
const KNOWN_AGENT_KINDS = ['claude', 'codex']
function getStoredAgentKind() {
    try {
        const v = localStorage.getItem(AGENT_KIND_KEY)
        return KNOWN_AGENT_KINDS.includes(v) ? v : DEFAULT_AGENT_KIND
    } catch (e) {
        return DEFAULT_AGENT_KIND
    }
}

// 根据当前页面协议/主机动态构造 WebSocket URL。
// 开发模式下 vite.config.js 的 proxy (/api, ws:true) 会把 WS 转发到后端；
// 生产模式下后端直接托管前端静态文件，同样同源可达。
// 关键：**不要**写死 localhost —— 当用户通过局域网 IP 访问前端时，
// localhost 指的是用户本机，而不是运行后端的机器。
function buildWsUrl() {
    if (typeof window === 'undefined' || !window.location) {
        return 'ws://localhost:8000/api/v1/agent/ws'
    }
    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${window.location.host}/api/v1/agent/ws`
}

export default {
    name: 'ChatPanel',
    data() {
        return {
            messages: [],
            inputText: '',
            isLoading: false,
            ws: null,
            userId: getUserId(),
            wsUrl: buildWsUrl(),
            reconnectTimer: null,
            // 历史会话相关
            showHistoryPanel: false,
            historyList: [],
            currentSessionId: null,
            // 代码 agent 选择（claude / codex）。Cursor 在 IDE 内独立连 MCP，
            // 不在 WebUI 后端的 dispatch 列表里。
            agentKind: getStoredAgentKind(),
            availableAgents: [
                { kind: 'claude', label: 'Claude Code' },
                { kind: 'codex', label: 'Codex' },
            ],
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme']),
        hasStreamingMessage() {
            return this.messages.some((m) => m.streaming)
        },
    },
    mounted() {
        this.connectWebSocket()
        this.loadHistory()
        this.loadAvailableAgents()
    },
    beforeUnmount() {
        this.disconnectWebSocket()
    },
    methods: {
        ...mapActions(useDataflow, ['syncFromAgent']),

        connectWebSocket() {
            const url = `${this.wsUrl}?user_id=${this.userId}&agent=${encodeURIComponent(this.agentKind)}`
            this.ws = new WebSocket(url)

            this.ws.onopen = () => {
                console.log('[ChatPanel] WebSocket connected')
            }

            this.ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data)
                    this.handleServerMessage(msg)
                } catch (e) {
                    console.error('[ChatPanel] Failed to parse message:', e)
                }
            }

            this.ws.onclose = () => {
                console.log('[ChatPanel] WebSocket disconnected, reconnecting in 3s...')
                this.reconnectTimer = setTimeout(() => this.connectWebSocket(), 3000)
            }

            this.ws.onerror = (err) => {
                console.error('[ChatPanel] WebSocket error:', err)
            }
        },

        disconnectWebSocket() {
            if (this.reconnectTimer) clearTimeout(this.reconnectTimer)
            if (this.ws) {
                this.ws.onclose = null  // 防止触发重连
                this.ws.close()
                this.ws = null
            }
        },

        handleServerMessage(msg) {
            if (msg.type === 'text_chunk') {
                this.appendToCurrentMessage(msg.content)

            } else if (msg.type === 'tool_call_start') {
                // Agent 开始调用一个工具：把当前 streaming 的 assistant 消息先 finalize，
                // 插入一条 role=tool 消息，后续 text_chunk 会另起一条新的 assistant 消息。
                this.finalizeCurrentMessage()
                this.messages.push({
                    role: 'tool',
                    tool_use_id: msg.tool_use_id,
                    name: msg.name,
                    input_preview: msg.input_preview || '',
                    output_preview: '',
                    status: 'running',
                    is_error: false,
                    expanded: false,
                    streaming: false,
                })
                this.$nextTick(() => this.scrollToBottom())

            } else if (msg.type === 'tool_call_end') {
                // 找到对应的 tool 消息，回填输出
                const toolMsg = [...this.messages].reverse().find(
                    (m) => m.role === 'tool' && m.tool_use_id === msg.tool_use_id
                )
                if (toolMsg) {
                    toolMsg.output_preview = msg.output_preview || ''
                    toolMsg.is_error = !!msg.is_error
                    toolMsg.status = msg.is_error ? 'error' : 'done'
                }
                this.$nextTick(() => this.scrollToBottom())

            } else if (msg.type === 'sync_pipeline') {
                // 同步 pipeline 到 DAG 编辑器
                this.syncFromAgent(msg)
                // 显示系统提示
                this.addSystemMessage(`✅ Pipeline "${msg.pipeline?.name || ''}" 已同步到编辑器`)

            } else if (msg.type === 'done') {
                this.finalizeCurrentMessage()
                this.isLoading = false

            } else if (msg.type === 'session_aborted') {
                this.isLoading = false
                this.messages = []
                this.currentSessionId = null
                this.addSystemMessage('⏹ 已终止运行并开始新会话（历史保留）')
                this.loadHistory()

            } else if (msg.type === 'session_cleared') {
                this.isLoading = false
                this.messages = []
                this.currentSessionId = null
                this.addSystemMessage('已开始新会话（历史保留）')
                this.loadHistory()

            } else if (msg.type === 'session_switched') {
                this.isLoading = false
                this.messages = []
                this.currentSessionId = msg.session_id
                this.addSystemMessage(`↩ 已切换到历史会话 ${msg.session_id.slice(0, 8)}…，继续对话将从上次记忆恢复`)
                this.showHistoryPanel = false
                this.loadHistory()

            } else if (msg.type === 'error') {
                this.isLoading = false
                this.addSystemMessage(`❌ 错误: ${msg.message}`)
            }
        },

        formatToolName(name) {
            if (!name) return 'tool'
            // mcp__dataflow__list_operators → list_operators
            const m = name.match(/^mcp__[^_]+__(.+)$/)
            return m ? m[1] : name
        },

        formatTime(isoStr) {
            if (!isoStr) return ''
            try {
                const d = new Date(isoStr)
                const now = new Date()
                const diff = (now - d) / 1000
                if (diff < 60) return '刚刚'
                if (diff < 3600) return `${Math.floor(diff / 60)} 分钟前`
                if (diff < 86400) return `${Math.floor(diff / 3600)} 小时前`
                return d.toLocaleDateString()
            } catch (e) {
                return isoStr
            }
        },

        async toggleHistoryPanel() {
            this.showHistoryPanel = !this.showHistoryPanel
            if (this.showHistoryPanel) {
                await this.loadHistory()
            }
        },

        async loadHistory() {
            try {
                const res = await axios.get('/api/v1/agent/sessions', {
                    params: { user_id: this.userId },
                })
                const data = res.data && res.data.data ? res.data.data : res.data
                this.historyList = data.history || []
                this.currentSessionId = data.current || null
            } catch (e) {
                console.warn('[ChatPanel] loadHistory failed:', e)
            }
        },

        newSession() {
            // 通过 WS 让后端脱离当前 session；若断开则仅清空本地视图
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'new_session' }))
            } else {
                this.messages = []
                this.currentSessionId = null
            }
        },

        switchSession(sessionId) {
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                this.addSystemMessage('⚠️ 连接已断开，正在重连…')
                this.connectWebSocket()
                return
            }
            this.ws.send(JSON.stringify({ type: 'switch_session', session_id: sessionId }))
        },

        async deleteSession(sessionId) {
            try {
                await axios.delete(`/api/v1/agent/sessions/${sessionId}`, {
                    params: { user_id: this.userId },
                })
                if (sessionId === this.currentSessionId) {
                    this.messages = []
                    this.currentSessionId = null
                }
                await this.loadHistory()
            } catch (e) {
                console.warn('[ChatPanel] deleteSession failed:', e)
            }
        },

        appendToCurrentMessage(text) {
            const lastMsg = this.messages[this.messages.length - 1]
            if (lastMsg && lastMsg.role === 'assistant' && lastMsg.streaming) {
                lastMsg.content += text
            } else {
                this.messages.push({ role: 'assistant', content: text, streaming: true })
            }
            this.$nextTick(() => this.scrollToBottom())
        },

        finalizeCurrentMessage() {
            const lastMsg = this.messages[this.messages.length - 1]
            if (lastMsg && lastMsg.streaming) {
                lastMsg.streaming = false
            }
        },

        addSystemMessage(text) {
            this.messages.push({ role: 'system', content: text, streaming: false })
            this.$nextTick(() => this.scrollToBottom())
        },

        sendMessage() {
            const text = this.inputText.trim()
            if (!text || this.isLoading) return
            if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
                this.addSystemMessage('⚠️ 连接已断开，正在重连...')
                this.connectWebSocket()
                return
            }

            this.messages.push({ role: 'user', content: text, streaming: false })
            this.inputText = ''
            this.isLoading = true

            this.ws.send(JSON.stringify({ type: 'chat', message: text, agent: this.agentKind }))
            this.$nextTick(() => this.scrollToBottom())
        },

        onAgentChange(event) {
            const newKind = event.target.value
            if (!KNOWN_AGENT_KINDS.includes(newKind) || newKind === this.agentKind) return
            this.agentKind = newKind
            try {
                localStorage.setItem(AGENT_KIND_KEY, newKind)
            } catch (e) {
                // localStorage 不可用时静默忽略
            }
            // 切换 agent 等同于开新会话：让后端立即丢弃当前 session_id（避免错配 session_id 给新 agent）
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'new_session' }))
            }
            this.currentSessionId = null
            this.addSystemMessage(`已切换到 ${this.availableAgents.find(a => a.kind === newKind)?.label || newKind}`)
        },

        async loadAvailableAgents() {
            try {
                const resp = await axios.get('/api/v1/agent/agents')
                const data = resp?.data?.data
                if (Array.isArray(data) && data.length > 0) {
                    this.availableAgents = data
                        .filter((a) => a && KNOWN_AGENT_KINDS.includes(a.kind))
                        .map((a) => ({ kind: a.kind, label: a.label || a.kind }))
                }
                if (!this.availableAgents.find((a) => a.kind === this.agentKind)) {
                    this.agentKind = this.availableAgents[0]?.kind || DEFAULT_AGENT_KIND
                }
            } catch (e) {
                // 后端不支持该端点时静默回退到本地默认列表
                console.warn('[ChatPanel] /agents endpoint unavailable, using static list')
            }
        },

        clearSession() {
            // 保留兼容性：仅清除 session，不终止进程
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'clear_session' }))
            } else {
                this.messages = []
            }
        },

        abortAndClear() {
            // 终止正在运行的 claude 子进程并清除对话历史
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({ type: 'abort_session' }))
                // 如果当前没有在运行（isLoading=false），前端也立刻清空
                // （后端会回复 session_aborted，但这里做兜底）
                if (!this.isLoading) {
                    this.messages = []
                    this.addSystemMessage('对话历史已清除，开始新会话')
                }
            } else {
                // WS 断线时直接清空前端历史
                this.messages = []
                this.isLoading = false
            }
        },

        scrollToBottom() {
            const container = this.$refs.messagesContainer
            if (container) {
                container.scrollTop = container.scrollHeight
            }
        },

        renderMarkdown(text) {
            if (!text) return ''
            return md.render(text)
        },
    },
}
</script>

<style scoped>
.chat-panel {
    position: relative;
    display: flex;
    flex-direction: column;
    height: 100%;
    background: rgba(252, 252, 252, 1);
    border-left: 1px solid rgba(230, 230, 230, 1);
    font-size: 13px;
}

.chat-panel.dark {
    background: rgba(32, 32, 32, 1);
    border-left-color: rgba(60, 60, 60, 1);
    color: rgba(220, 220, 220, 1);
}

/* 顶部工具栏 */
.chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-bottom: 1px solid rgba(230, 230, 230, 1);
    flex-shrink: 0;
    background: rgba(248, 248, 248, 1);
}

.dark .chat-header {
    background: rgba(40, 40, 40, 1);
    border-bottom-color: rgba(60, 60, 60, 1);
}

.chat-title {
    font-weight: 600;
    font-size: 14px;
    display: flex;
    align-items: center;
    color: rgba(69, 98, 213, 1);
}

.chat-agent-select {
    margin-left: 10px;
    padding: 2px 8px;
    font-size: 11px;
    line-height: 1.4;
    border: 1px solid rgba(0, 0, 0, 0.15);
    border-radius: 6px;
    background: transparent;
    color: inherit;
    cursor: pointer;
}

.chat-agent-select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.dark .chat-agent-select {
    border-color: rgba(255, 255, 255, 0.2);
    background: rgba(255, 255, 255, 0.04);
    color: rgba(255, 255, 255, 0.85);
}

.chat-header-actions {
    display: flex;
    gap: 4px;
}

/* 消息列表 */
.chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 12px 14px;
    display: flex;
    flex-direction: column;
    gap: 12px;
}

.chat-empty {
    text-align: center;
    padding: 40px 20px;
    color: rgba(150, 150, 150, 1);
    line-height: 1.7;
}

.chat-empty-hint {
    margin-top: 16px;
    padding: 8px 12px;
    font-size: 12px;
    color: rgba(120, 120, 120, 1);
    background: rgba(0, 0, 0, 0.03);
    border-radius: 6px;
    line-height: 1.6;
}

.chat-empty-hint code {
    padding: 1px 5px;
    background: rgba(0, 0, 0, 0.06);
    border-radius: 3px;
    font-size: 11px;
}

.dark .chat-empty-hint {
    background: rgba(255, 255, 255, 0.04);
    color: rgba(180, 180, 180, 1);
}

.dark .chat-empty-hint code {
    background: rgba(255, 255, 255, 0.08);
}

.chat-message {
    display: flex;
    gap: 8px;
    align-items: flex-start;
}

.chat-message.user {
    flex-direction: row-reverse;
}

.chat-message.system {
    justify-content: center;
}

.chat-message.system .message-content {
    background: rgba(240, 240, 240, 0.8);
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
    color: rgba(100, 100, 100, 1);
    max-width: 90%;
    text-align: center;
}

.dark .chat-message.system .message-content {
    background: rgba(60, 60, 60, 0.8);
    color: rgba(180, 180, 180, 1);
}

.message-avatar {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 14px;
    background: rgba(230, 230, 230, 1);
}

.dark .message-avatar {
    background: rgba(60, 60, 60, 1);
}

.chat-message.user .message-avatar {
    background: linear-gradient(135deg, rgba(69, 98, 213, 1), rgba(161, 145, 206, 1));
    color: white;
}

.message-content {
    max-width: 82%;
    position: relative;
}

.message-text {
    padding: 8px 12px;
    border-radius: 10px;
    line-height: 1.6;
    word-break: break-word;
    background: rgba(255, 255, 255, 1);
    border: 1px solid rgba(230, 230, 230, 1);
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.dark .message-text {
    background: rgba(50, 50, 50, 1);
    border-color: rgba(70, 70, 70, 1);
}

.chat-message.user .message-text {
    background: linear-gradient(135deg, rgba(69, 98, 213, 0.9), rgba(120, 105, 200, 0.9));
    color: white;
    border-color: transparent;
}

.streaming-cursor {
    display: inline-block;
    animation: blink 1s infinite;
    color: rgba(69, 98, 213, 1);
    margin-left: 2px;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
}

/* 加载动画 */
.loading-dots {
    display: flex;
    gap: 4px;
    padding: 8px 12px;
}

.loading-dots span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: rgba(69, 98, 213, 0.6);
    animation: dots 1.2s infinite;
}

.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }

@keyframes dots {
    0%, 100% { transform: scale(0.8); opacity: 0.5; }
    50% { transform: scale(1.2); opacity: 1; }
}

/* 底部输入区 */
.chat-input-area {
    padding: 10px 14px;
    border-top: 1px solid rgba(230, 230, 230, 1);
    flex-shrink: 0;
    background: rgba(250, 250, 250, 1);
}

.dark .chat-input-area {
    background: rgba(40, 40, 40, 1);
    border-top-color: rgba(60, 60, 60, 1);
}

.chat-input-wrapper {
    display: flex;
    gap: 8px;
    align-items: flex-end;
}

.chat-input {
    flex: 1;
    padding: 8px 10px;
    border: 1px solid rgba(200, 200, 200, 1);
    border-radius: 8px;
    resize: none;
    font-size: 13px;
    line-height: 1.5;
    outline: none;
    background: rgba(255, 255, 255, 1);
    color: inherit;
    font-family: inherit;
    transition: border-color 0.2s;
}

.dark .chat-input {
    background: rgba(55, 55, 55, 1);
    border-color: rgba(80, 80, 80, 1);
    color: rgba(220, 220, 220, 1);
}

.chat-input:focus {
    border-color: rgba(69, 98, 213, 0.7);
}

.chat-input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.chat-hint {
    font-size: 11px;
    color: rgba(160, 160, 160, 1);
    margin-top: 5px;
    text-align: right;
}

/* Markdown 渲染样式 */
.markdown-body :deep(p) {
    margin: 0 0 8px 0;
}
.markdown-body :deep(p:last-child) {
    margin-bottom: 0;
}
.markdown-body :deep(code) {
    background: rgba(100, 100, 100, 0.15);
    border-radius: 3px;
    padding: 1px 5px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 12px;
}
.markdown-body :deep(pre) {
    background: rgba(40, 44, 52, 1);
    color: rgba(220, 220, 220, 1);
    border-radius: 6px;
    padding: 10px 12px;
    overflow-x: auto;
    margin: 8px 0;
}
.markdown-body :deep(pre code) {
    background: none;
    padding: 0;
    color: inherit;
}
.markdown-body :deep(ul),
.markdown-body :deep(ol) {
    padding-left: 20px;
    margin: 6px 0;
}
.markdown-body :deep(li) {
    margin: 2px 0;
}
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
    margin: 8px 0 4px 0;
    font-weight: 600;
}
.markdown-body :deep(blockquote) {
    border-left: 3px solid rgba(69, 98, 213, 0.5);
    padding-left: 10px;
    margin: 6px 0;
    color: rgba(120, 120, 120, 1);
}
.markdown-body :deep(a) {
    color: rgba(69, 98, 213, 1);
    text-decoration: none;
}
.markdown-body :deep(a:hover) {
    text-decoration: underline;
}
.markdown-body :deep(table) {
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 12px;
    width: 100%;
}
.markdown-body :deep(th),
.markdown-body :deep(td) {
    border: 1px solid rgba(200, 200, 200, 1);
    padding: 4px 8px;
}
.markdown-body :deep(th) {
    background: rgba(230, 230, 230, 0.5);
    font-weight: 600;
}

/* ── Tool call card ───────────────────────────────────────────── */
.tool-call-card {
    border: 1px solid rgba(0, 0, 0, 0.1);
    border-radius: 6px;
    background: rgba(246, 246, 250, 0.7);
    overflow: hidden;
    font-size: 12px;
}
.chat-panel.dark .tool-call-card {
    background: rgba(255, 255, 255, 0.04);
    border-color: rgba(255, 255, 255, 0.12);
}
.tool-call-card.running {
    border-left: 3px solid #4562d5;
}
.tool-call-card.done {
    border-left: 3px solid #3fa46a;
}
.tool-call-card.error {
    border-left: 3px solid #d64545;
}
.tool-call-head {
    display: flex;
    align-items: center;
    padding: 6px 8px;
    cursor: pointer;
    user-select: none;
    gap: 4px;
}
.tool-name {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-weight: 600;
}
.tool-status {
    margin-left: 6px;
    font-size: 11px;
    color: #4562d5;
}
.tool-status.done { color: #3fa46a; }
.tool-status.error { color: #d64545; }
.tool-toggle {
    margin-left: auto;
    font-size: 10px;
    transition: transform 0.15s;
}
.tool-toggle.expanded {
    transform: rotate(180deg);
}
.tool-call-body {
    border-top: 1px solid rgba(0, 0, 0, 0.08);
    padding: 6px 8px;
}
.chat-panel.dark .tool-call-body {
    border-top-color: rgba(255, 255, 255, 0.1);
}
.tool-kv + .tool-kv {
    margin-top: 6px;
}
.tool-kv-label {
    font-size: 10px;
    text-transform: uppercase;
    opacity: 0.55;
    margin-bottom: 2px;
    letter-spacing: 0.05em;
}
.tool-kv-value {
    margin: 0;
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 11px;
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
    max-height: 180px;
    overflow: auto;
}
.chat-message.tool .message-avatar {
    background: rgba(69, 98, 213, 0.1);
    color: #4562d5;
}

/* ── History drawer ───────────────────────────────────────── */
.history-overlay {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.15);
    display: flex;
    justify-content: flex-end;
    z-index: 20;
}
.history-panel {
    width: 280px;
    max-width: 100%;
    background: #fff;
    height: 100%;
    display: flex;
    flex-direction: column;
    box-shadow: -2px 0 12px rgba(0, 0, 0, 0.08);
}
.chat-panel.dark .history-panel {
    background: #1f2022;
    color: #e0e0e0;
}
.history-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 12px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
    font-weight: 600;
}
.chat-panel.dark .history-head {
    border-bottom-color: rgba(255, 255, 255, 0.1);
}
.history-close {
    cursor: pointer;
    font-size: 12px;
    opacity: 0.6;
}
.history-close:hover { opacity: 1; }
.history-list {
    flex: 1;
    overflow-y: auto;
}
.history-empty {
    padding: 20px;
    text-align: center;
    opacity: 0.55;
    font-size: 13px;
}
.history-item {
    position: relative;
    padding: 8px 28px 8px 12px;
    border-bottom: 1px solid rgba(0, 0, 0, 0.05);
    cursor: pointer;
    transition: background 0.12s;
}
.history-item:hover {
    background: rgba(69, 98, 213, 0.06);
}
.history-item.active {
    background: rgba(69, 98, 213, 0.12);
}
.history-item-title {
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.history-item-meta {
    font-size: 11px;
    opacity: 0.55;
    margin-top: 2px;
    display: flex;
    gap: 4px;
}
.history-item-del {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    font-size: 11px;
    opacity: 0;
    cursor: pointer;
    transition: opacity 0.12s;
}
.history-item:hover .history-item-del { opacity: 0.6; }
.history-item-del:hover { opacity: 1; color: #d64545; }
</style>
