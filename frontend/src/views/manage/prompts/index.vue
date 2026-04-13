<template>
    <div class="df-prompts-container" :class="[{ dark: theme === 'dark' }]">
        <!-- 左侧：算子分组列表 -->
        <div class="prompts-sidebar">
            <div class="sidebar-header">
                <i class="ms-Icon ms-Icon--Filter" style="margin-right: 6px; font-size: 13px;"></i>
                <input
                    v-model="searchText"
                    class="search-input"
                    :placeholder="local('Search...')"
                />
            </div>
            <div class="sidebar-scroll">
                <template v-for="(prompts, opName) in filteredOperatorMap" :key="opName">
                    <div
                        class="op-group"
                        :class="{ active: selectedOp === opName }"
                        @click="selectOperator(opName)"
                    >
                        <i class="ms-Icon ms-Icon--Code" style="font-size: 12px; margin-right: 6px; flex-shrink: 0;"></i>
                        <span class="op-name">{{ opName }}</span>
                        <span class="op-count">{{ prompts.length }}</span>
                    </div>
                </template>
                <div v-if="Object.keys(filteredOperatorMap).length === 0" class="sidebar-empty">
                    {{ local('No results') }}
                </div>
            </div>
        </div>

        <!-- 中间：Prompt 列表 -->
        <div class="prompts-list-panel">
            <div class="panel-header">
                <span v-if="selectedOp">
                    <i class="ms-Icon ms-Icon--Code" style="margin-right: 6px;"></i>
                    {{ selectedOp }}
                </span>
                <span v-else class="panel-placeholder">{{ local('Select an operator') }}</span>
            </div>
            <div class="prompts-list-scroll">
                <div
                    v-for="pName in currentPromptNames"
                    :key="pName"
                    class="prompt-item"
                    :class="{ active: selectedPrompt === pName }"
                    @click="selectPrompt(pName)"
                >
                    <div class="prompt-item-name">{{ pName }}</div>
                    <div v-if="promptInfoMap[pName]" class="prompt-item-meta">
                        <span class="badge primary">{{ promptInfoMap[pName].primary_type }}</span>
                        <span class="badge secondary">{{ promptInfoMap[pName].secondary_type }}</span>
                    </div>
                </div>
                <div v-if="!selectedOp" class="list-empty">
                    <i class="ms-Icon ms-Icon--BulletedList" style="font-size: 32px; opacity: 0.2; display: block; margin-bottom: 8px;"></i>
                    {{ local('Choose an operator from the left') }}
                </div>
                <div v-else-if="currentPromptNames.length === 0" class="list-empty">
                    {{ local('No prompts available') }}
                </div>
            </div>
        </div>

        <!-- 右侧：Prompt 详情 -->
        <div class="prompts-detail-panel">
            <template v-if="selectedPrompt && promptInfoMap[selectedPrompt]">
                <div class="detail-header">
                    <div class="detail-title">{{ selectedPrompt }}</div>
                    <div class="detail-badges">
                        <span class="badge primary">{{ promptInfoMap[selectedPrompt].primary_type }}</span>
                        <span class="badge secondary">{{ promptInfoMap[selectedPrompt].secondary_type }}</span>
                    </div>
                </div>

                <!-- Docstring -->
                <div v-if="promptInfoMap[selectedPrompt].description" class="detail-section">
                    <div class="section-title">
                        <i class="ms-Icon ms-Icon--Info" style="margin-right: 4px;"></i>
                        {{ local('Description') }}
                    </div>
                    <div class="docstring-block">{{ promptInfoMap[selectedPrompt].description }}</div>
                </div>

                <!-- 适用算子 -->
                <div class="detail-section">
                    <div class="section-title">
                        <i class="ms-Icon ms-Icon--Link" style="margin-right: 4px;"></i>
                        {{ local('Used by operators') }}
                    </div>
                    <div class="tag-row">
                        <span
                            v-for="op in promptInfoMap[selectedPrompt].operator"
                            :key="op"
                            class="op-tag"
                            @click="selectOperator(op)"
                        >{{ op }}</span>
                        <span v-if="!promptInfoMap[selectedPrompt].operator?.length" class="muted">—</span>
                    </div>
                </div>

                <!-- 参数信息 -->
                <div class="detail-section">
                    <div class="section-title">
                        <i class="ms-Icon ms-Icon--Parameter" style="margin-right: 4px;"></i>
                        {{ local('Parameters') }}
                    </div>
                    <div v-if="hasParams(promptInfoMap[selectedPrompt])">
                        <div v-if="promptInfoMap[selectedPrompt].parameter.init?.length" class="param-group">
                            <div class="param-group-label">__init__</div>
                            <table class="param-table">
                                <thead>
                                    <tr>
                                        <th>{{ local('Name') }}</th>
                                        <th>{{ local('Default') }}</th>
                                        <th>{{ local('Kind') }}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="p in promptInfoMap[selectedPrompt].parameter.init" :key="p.name">
                                        <td><code>{{ p.name }}</code></td>
                                        <td><code>{{ p.default_value !== null ? p.default_value : '—' }}</code></td>
                                        <td><span class="kind-badge">{{ p.kind }}</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div v-if="promptInfoMap[selectedPrompt].parameter.build_prompt?.length" class="param-group">
                            <div class="param-group-label">build_prompt</div>
                            <table class="param-table">
                                <thead>
                                    <tr>
                                        <th>{{ local('Name') }}</th>
                                        <th>{{ local('Default') }}</th>
                                        <th>{{ local('Kind') }}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="p in promptInfoMap[selectedPrompt].parameter.build_prompt" :key="p.name">
                                        <td><code>{{ p.name }}</code></td>
                                        <td><code>{{ p.default_value !== null ? p.default_value : '—' }}</code></td>
                                        <td><span class="kind-badge">{{ p.kind }}</span></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div v-else class="muted">{{ local('No parameters') }}</div>
                </div>

                <!-- 源码 -->
                <div class="detail-section source-section">
                    <div class="section-title">
                        <i class="ms-Icon ms-Icon--Code" style="margin-right: 4px;"></i>
                        {{ local('Source Code') }}
                        <fv-button
                            :theme="theme"
                            style="width: 72px; height: 26px; margin-left: auto; font-size: 12px;"
                            border-radius="4"
                            @click="copySource"
                        >
                            <i class="ms-Icon ms-Icon--Copy" style="font-size: 11px; margin-right: 4px;"></i>
                            {{ copyLabel }}
                        </fv-button>
                    </div>
                    <div v-if="loadingSource" class="source-loading">
                        <div class="loading-dots">
                            <span></span><span></span><span></span>
                        </div>
                    </div>
                    <pre v-else-if="sourceCode" class="source-block"><code>{{ sourceCode }}</code></pre>
                    <div v-else class="muted source-na">{{ local('Source not available') }}</div>
                </div>
            </template>

            <!-- 未选中 prompt 时的占位 -->
            <div v-else class="detail-placeholder">
                <i class="ms-Icon ms-Icon--TextDocument" style="font-size: 48px; opacity: 0.15; display: block; margin-bottom: 12px;"></i>
                <p>{{ local('Select a prompt template to view details') }}</p>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import axios from 'axios'

const BASE = '/api/v1/prompts'

export default {
    name: 'PromptsManager',
    data() {
        return {
            // 数据
            operatorMap: {},      // { operatorName: [promptName, ...] }
            promptInfoMap: {},    // { promptName: PromptInfoOut }
            // 交互状态
            selectedOp: '',
            selectedPrompt: '',
            searchText: '',
            // 源码
            sourceCode: '',
            loadingSource: false,
            // 复制按钮
            copyLabel: 'Copy',
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme', 'gradient']),

        filteredOperatorMap() {
            const q = this.searchText.trim().toLowerCase()
            if (!q) return this.operatorMap
            const result = {}
            for (const [op, prompts] of Object.entries(this.operatorMap)) {
                if (
                    op.toLowerCase().includes(q) ||
                    prompts.some(p => p.toLowerCase().includes(q))
                ) {
                    result[op] = prompts
                }
            }
            return result
        },

        currentPromptNames() {
            if (!this.selectedOp) return []
            return this.operatorMap[this.selectedOp] || []
        },
    },
    mounted() {
        this.loadData()
    },
    methods: {
        async loadData() {
            try {
                const [opRes, infoRes] = await Promise.all([
                    axios.get(`${BASE}/operator-mapping`),
                    axios.get(`${BASE}/prompt-info`),
                ])
                this.operatorMap = opRes.data?.data?.operator_prompts || {}
                this.promptInfoMap = infoRes.data?.data?.prompts || {}
            } catch (e) {
                console.error('[Prompts] Failed to load data', e)
            }
        },

        selectOperator(opName) {
            if (!this.operatorMap[opName]) return
            this.selectedOp = opName
            this.selectedPrompt = ''
            this.sourceCode = ''
        },

        async selectPrompt(pName) {
            this.selectedPrompt = pName
            this.sourceCode = ''
            this.loadingSource = true
            try {
                const res = await axios.get(`${BASE}/source/${pName}`)
                this.sourceCode = res.data?.data?.source || ''
            } catch (e) {
                this.sourceCode = ''
            } finally {
                this.loadingSource = false
            }
        },

        hasParams(info) {
            if (!info?.parameter) return false
            return (info.parameter.init?.length > 0) || (info.parameter.build_prompt?.length > 0)
        },

        async copySource() {
            if (!this.sourceCode) return
            try {
                await navigator.clipboard.writeText(this.sourceCode)
                this.copyLabel = 'Copied!'
                setTimeout(() => { this.copyLabel = 'Copy' }, 1800)
            } catch {
                this.copyLabel = 'Error'
                setTimeout(() => { this.copyLabel = 'Copy' }, 1800)
            }
        },
    }
}
</script>

<style lang="scss" scoped>
.df-prompts-container {
    display: flex;
    height: 100%;
    overflow: hidden;
    background: rgba(250, 250, 250, 1);
    font-size: 13px;

    &.dark {
        background: rgba(36, 36, 36, 1);
        color: rgba(220, 220, 220, 1);

        .prompts-sidebar {
            background: rgba(30, 30, 30, 1);
            border-right-color: rgba(55, 55, 55, 1);

            .sidebar-header {
                border-bottom-color: rgba(55, 55, 55, 1);
                background: rgba(38, 38, 38, 1);
            }

            .search-input {
                background: rgba(50, 50, 50, 1);
                border-color: rgba(70, 70, 70, 1);
                color: rgba(220, 220, 220, 1);
            }

            .op-group {
                &:hover { background: rgba(50, 50, 50, 1); }
                &.active { background: rgba(69, 98, 213, 0.2); }
            }
        }

        .prompts-list-panel {
            background: rgba(36, 36, 36, 1);
            border-right-color: rgba(55, 55, 55, 1);

            .panel-header {
                background: rgba(38, 38, 38, 1);
                border-bottom-color: rgba(55, 55, 55, 1);
            }

            .prompt-item {
                border-bottom-color: rgba(50, 50, 50, 1);
                &:hover { background: rgba(50, 50, 50, 1); }
                &.active { background: rgba(69, 98, 213, 0.2); border-left-color: rgba(69, 98, 213, 1); }
            }
        }

        .prompts-detail-panel {
            .detail-header {
                background: rgba(38, 38, 38, 1);
                border-bottom-color: rgba(55, 55, 55, 1);
            }

            .detail-section {
                border-bottom-color: rgba(50, 50, 50, 1);

                .section-title {
                    color: rgba(160, 160, 160, 1);
                }
            }

            .docstring-block {
                background: rgba(45, 45, 45, 1);
                border-color: rgba(60, 60, 60, 1);
            }

            .source-block {
                background: rgba(28, 30, 36, 1);
            }

            .param-table {
                th { background: rgba(45, 45, 45, 1); }
                td, th { border-color: rgba(60, 60, 60, 1); }
            }
        }
    }
}

/* ── 左侧算子导航 ─────────────────────────────────── */
.prompts-sidebar {
    width: 220px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    background: rgba(246, 246, 246, 1);
    border-right: 1px solid rgba(230, 230, 230, 1);
    overflow: hidden;
}

.sidebar-header {
    display: flex;
    align-items: center;
    padding: 10px 10px;
    border-bottom: 1px solid rgba(230, 230, 230, 1);
    background: rgba(250, 250, 250, 1);
    flex-shrink: 0;
}

.search-input {
    flex: 1;
    border: 1px solid rgba(210, 210, 210, 1);
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
    outline: none;
    background: rgba(255, 255, 255, 1);

    &:focus {
        border-color: rgba(69, 98, 213, 0.6);
    }
}

.sidebar-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 4px 0;
}

.op-group {
    display: flex;
    align-items: center;
    padding: 7px 12px;
    cursor: pointer;
    border-left: 3px solid transparent;
    transition: background 0.15s;

    &:hover {
        background: rgba(240, 240, 240, 1);
    }

    &.active {
        background: rgba(69, 98, 213, 0.08);
        border-left-color: rgba(69, 98, 213, 1);

        .op-name {
            color: rgba(69, 98, 213, 1);
            font-weight: 600;
        }
    }

    .op-name {
        flex: 1;
        font-size: 12px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .op-count {
        font-size: 11px;
        background: rgba(200, 200, 200, 0.5);
        border-radius: 10px;
        padding: 1px 6px;
        flex-shrink: 0;
    }
}

.sidebar-empty {
    padding: 20px;
    text-align: center;
    font-size: 12px;
    color: rgba(160, 160, 160, 1);
}

/* ── 中间 Prompt 列表 ──────────────────────────────── */
.prompts-list-panel {
    width: 220px;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    border-right: 1px solid rgba(230, 230, 230, 1);
    overflow: hidden;
}

.panel-header {
    padding: 12px 14px;
    font-weight: 600;
    font-size: 13px;
    border-bottom: 1px solid rgba(230, 230, 230, 1);
    background: rgba(250, 250, 250, 1);
    flex-shrink: 0;
    display: flex;
    align-items: center;
    min-height: 44px;
    box-sizing: border-box;
}

.panel-placeholder {
    color: rgba(160, 160, 160, 1);
    font-weight: 400;
    font-size: 12px;
}

.prompts-list-scroll {
    flex: 1;
    overflow-y: auto;
}

.prompt-item {
    padding: 10px 14px;
    cursor: pointer;
    border-bottom: 1px solid rgba(240, 240, 240, 1);
    border-left: 3px solid transparent;
    transition: background 0.15s;

    &:hover {
        background: rgba(240, 240, 240, 1);
    }

    &.active {
        background: rgba(69, 98, 213, 0.08);
        border-left-color: rgba(69, 98, 213, 1);

        .prompt-item-name {
            color: rgba(69, 98, 213, 1);
            font-weight: 600;
        }
    }
}

.prompt-item-name {
    font-size: 12px;
    margin-bottom: 4px;
    word-break: break-all;
}

.prompt-item-meta {
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
}

.list-empty {
    padding: 30px 20px;
    text-align: center;
    color: rgba(160, 160, 160, 1);
    font-size: 12px;
    line-height: 1.8;
}

/* ── 右侧详情 ─────────────────────────────────────── */
.prompts-detail-panel {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
}

.detail-placeholder {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: rgba(160, 160, 160, 1);
    text-align: center;
    padding: 40px;
}

.detail-header {
    padding: 14px 20px 12px;
    border-bottom: 1px solid rgba(230, 230, 230, 1);
    background: rgba(250, 250, 250, 1);
    flex-shrink: 0;
}

.detail-title {
    font-size: 16px;
    font-weight: 700;
    margin-bottom: 6px;
    color: rgba(69, 98, 213, 1);
}

.detail-badges {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}

.detail-section {
    padding: 14px 20px;
    border-bottom: 1px solid rgba(240, 240, 240, 1);
}

.section-title {
    font-size: 11px;
    font-weight: 600;
    color: rgba(130, 130, 130, 1);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
}

.docstring-block {
    background: rgba(246, 248, 250, 1);
    border: 1px solid rgba(220, 220, 220, 1);
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 12px;
    line-height: 1.7;
    white-space: pre-wrap;
    word-break: break-word;
}

.tag-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
}

.op-tag {
    background: rgba(69, 98, 213, 0.1);
    color: rgba(69, 98, 213, 1);
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 12px;
    cursor: pointer;

    &:hover {
        background: rgba(69, 98, 213, 0.2);
    }
}

/* 参数表格 */
.param-group {
    margin-bottom: 12px;
}

.param-group-label {
    font-size: 12px;
    font-weight: 600;
    font-family: 'Consolas', monospace;
    margin-bottom: 6px;
    color: rgba(100, 100, 100, 1);
}

.param-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;

    th, td {
        border: 1px solid rgba(220, 220, 220, 1);
        padding: 5px 10px;
        text-align: left;
    }

    th {
        background: rgba(246, 246, 246, 1);
        font-weight: 600;
        color: rgba(100, 100, 100, 1);
    }

    code {
        background: rgba(100, 100, 100, 0.1);
        border-radius: 3px;
        padding: 1px 4px;
        font-family: 'Consolas', monospace;
    }
}

.kind-badge {
    font-size: 10px;
    background: rgba(200, 200, 200, 0.4);
    border-radius: 3px;
    padding: 1px 5px;
    font-family: monospace;
}

/* 源码区域 */
.source-section {
    flex: 1;

    .section-title {
        margin-bottom: 10px;
    }
}

.source-block {
    background: rgba(28, 30, 36, 1);
    color: rgba(220, 220, 220, 1);
    border-radius: 6px;
    padding: 14px 16px;
    overflow-x: auto;
    font-size: 12px;
    line-height: 1.6;
    font-family: 'Consolas', 'Monaco', monospace;
    white-space: pre;
    max-height: 420px;
    overflow-y: auto;
    margin: 0;

    code {
        background: none;
        padding: 0;
        font-size: inherit;
        font-family: inherit;
    }
}

.source-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px 0;
}

.source-na {
    padding: 12px 0;
}

/* 通用 badges */
.badge {
    font-size: 10px;
    border-radius: 3px;
    padding: 2px 6px;
    font-weight: 600;

    &.primary {
        background: rgba(69, 98, 213, 0.12);
        color: rgba(69, 98, 213, 1);
    }

    &.secondary {
        background: rgba(161, 145, 206, 0.15);
        color: rgba(120, 100, 180, 1);
    }
}

.muted {
    color: rgba(160, 160, 160, 1);
    font-size: 12px;
}

/* 加载动画 */
.loading-dots {
    display: flex;
    gap: 4px;

    span {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: rgba(69, 98, 213, 0.6);
        animation: dots 1.2s infinite;

        &:nth-child(2) { animation-delay: 0.2s; }
        &:nth-child(3) { animation-delay: 0.4s; }
    }
}

@keyframes dots {
    0%, 100% { transform: scale(0.8); opacity: 0.5; }
    50% { transform: scale(1.2); opacity: 1; }
}
</style>
