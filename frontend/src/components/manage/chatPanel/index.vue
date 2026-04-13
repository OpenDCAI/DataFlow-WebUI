<template>
    <div class="chat-panel" :class="{ dark: theme === 'dark' }">
        <!-- 顶部工具栏 -->
        <div class="chat-header">
            <div class="chat-title">
                <i class="ms-Icon ms-Icon--Robot" style="margin-right: 6px; font-size: 16px;"></i>
                <span>DataFlow 助手</span>
            </div>
            <div class="chat-header-actions">
                <!-- 终止并清除：kill 正在运行的 claude-internal 进程，同时清空对话历史 -->
                <fv-button
                    :theme="theme"
                    :title="isLoading ? '终止运行并清除对话' : '清除对话历史'"
                    style="width: 28px; height: 28px; border-radius: 50%;"
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

        <!-- 消息列表区 -->
        <div class="chat-messages" ref="messagesContainer">
            <div v-if="messages.length === 0" class="chat-empty">
                <i class="ms-Icon ms-Icon--ChatInviteFriend" style="font-size: 40px; opacity: 0.3; display: block; text-align: center; margin-bottom: 12px;"></i>
                <p>你好！我是 DataFlow 助手。</p>
                <p>你可以告诉我需要构建什么样的数据处理 Pipeline，我来帮你设计和创建。</p>
            </div>
            <div
                v-for="(msg, idx) in messages"
                :key="idx"
                class="chat-message"
                :class="msg.role"
            >
                <div class="message-avatar">
                    <i v-if="msg.role === 'user'" class="ms-Icon ms-Icon--Contact"></i>
                    <i v-else class="ms-Icon ms-Icon--Robot"></i>
                </div>
                <div class="message-content">
                    <div
                        v-if="msg.role === 'assistant'"
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

export default {
    name: 'ChatPanel',
    data() {
        return {
            messages: [],
            inputText: '',
            isLoading: false,
            ws: null,
            userId: getUserId(),
            wsUrl: `ws://localhost:8000/api/v1/agent/ws`,
            reconnectTimer: null,
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
    },
    beforeUnmount() {
        this.disconnectWebSocket()
    },
    methods: {
        ...mapActions(useDataflow, ['syncFromAgent']),

        connectWebSocket() {
            const url = `${this.wsUrl}?user_id=${this.userId}`
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
                this.addSystemMessage('⏹ 已终止运行并清除对话历史，开始新会话')

            } else if (msg.type === 'session_cleared') {
                this.isLoading = false
                this.messages = []
                this.addSystemMessage('对话历史已清除，开始新会话')

            } else if (msg.type === 'error') {
                this.isLoading = false
                this.addSystemMessage(`❌ 错误: ${msg.message}`)
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

            this.ws.send(JSON.stringify({ type: 'chat', message: text }))
            this.$nextTick(() => this.scrollToBottom())
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
            // 终止正在运行的 claude-internal 子进程并清除对话历史
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
</style>
