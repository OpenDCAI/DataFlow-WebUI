<template>
    <div class="df-prompts-page" :class="[{ dark: theme === 'dark' }]">
        <!-- Tab 切换 -->
        <div class="prompts-tabs">
            <div class="prompts-tab" :class="{ active: tab === 'builtin' }" @click="tab = 'builtin'">
                <i class="ms-Icon ms-Icon--Library" style="margin-right: 6px;"></i>
                {{ local('Built-in Prompts') }}
            </div>
            <div class="prompts-tab" :class="{ active: tab === 'user' }" @click="tab = 'user'">
                <i class="ms-Icon ms-Icon--FavoriteStar" style="margin-right: 6px;"></i>
                {{ local('My Templates') }}
                <span v-if="userTemplates.length" class="prompts-tab-count">{{ userTemplates.length }}</span>
            </div>
        </div>

        <!-- ── Built-in prompts browser ───────────────────────── -->
        <div v-if="tab === 'builtin'" class="df-prompts-container" :class="[{ dark: theme === 'dark' }]">
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

        <!-- ── My Templates (user-defined) ───────────────────────── -->
        <div v-else class="df-user-prompts" :class="[{ dark: theme === 'dark' }]">
            <!-- 左侧：模板列表 -->
            <div class="user-prompts-sidebar">
                <div class="sidebar-header">
                    <span style="flex: 1;">{{ local('My Templates') }}</span>
                    <a class="sidebar-new-btn" @click="startNewTemplate">
                        <i class="ms-Icon ms-Icon--Add"></i>
                        {{ local('New') }}
                    </a>
                </div>
                <div class="sidebar-scroll">
                    <div
                        v-for="t in userTemplates"
                        :key="t.id"
                        class="user-prompt-item"
                        :class="{ active: selectedUserId === t.id }"
                        @click="selectUserTemplate(t.id)"
                    >
                        <div class="user-prompt-name">{{ t.name || '(untitled)' }}</div>
                        <div v-if="t.description" class="user-prompt-desc">{{ t.description }}</div>
                        <div class="user-prompt-meta">
                            <span>{{ (t.allowed_operators || []).length }} op(s)</span>
                            <span>·</span>
                            <span>{{ placeholderPreview(t.template) }}</span>
                        </div>
                    </div>
                    <div v-if="userTemplates.length === 0" class="sidebar-empty">
                        {{ local('No templates yet') }}
                    </div>
                </div>
            </div>

            <!-- 右侧：编辑器 -->
            <div class="user-prompts-editor" v-if="editingTemplate">
                <div class="editor-row">
                    <label>{{ local('Name') }}</label>
                    <input v-model="editingTemplate.name" class="editor-input" />
                </div>
                <div class="editor-row">
                    <label>{{ local('Description') }}</label>
                    <input v-model="editingTemplate.description" class="editor-input" />
                </div>
                <div class="editor-row">
                    <label>
                        {{ local('Template (f-string, use {placeholder} syntax)') }}
                    </label>
                    <textarea
                        v-model="editingTemplate.template"
                        class="editor-textarea"
                        rows="8"
                        @input="onTemplateEdit"
                    ></textarea>
                    <div v-if="detectedPlaceholders.length" class="placeholder-list">
                        <span class="placeholder-label">{{ local('Placeholders') }}:</span>
                        <span
                            v-for="p in detectedPlaceholders"
                            :key="p"
                            class="placeholder-chip"
                        >{{ p }}</span>
                    </div>
                </div>
                <div class="editor-row">
                    <label>{{ local('Allowed operators (optional)') }}</label>
                    <input
                        :value="(editingTemplate.allowed_operators || []).join(', ')"
                        @input="updateAllowedOps($event.target.value)"
                        class="editor-input"
                        :placeholder="local('Comma-separated, e.g. OperatorA, OperatorB')"
                    />
                </div>
                <div class="editor-row">
                    <label>{{ local('Example variables (for preview)') }}</label>
                    <div
                        v-for="p in detectedPlaceholders"
                        :key="'ex-' + p"
                        class="kv-row"
                    >
                        <span class="kv-key">{{ p }}</span>
                        <input
                            :value="editingTemplate.example_variables[p] || ''"
                            @input="setExampleVar(p, $event.target.value)"
                            class="editor-input"
                        />
                    </div>
                </div>
                <div class="editor-row">
                    <label>{{ local('Preview') }}</label>
                    <pre class="preview-block">{{ previewRendered || local('(no preview yet)') }}</pre>
                    <p v-if="previewMissing.length" class="preview-missing">
                        {{ local('Missing variables') }}: {{ previewMissing.join(', ') }}
                    </p>
                </div>
                <div class="editor-actions">
                    <button class="btn-primary" @click="saveTemplate">
                        {{ editingTemplate.id ? local('Update') : local('Create') }}
                    </button>
                    <button v-if="editingTemplate.id" class="btn-danger" @click="deleteTemplate">
                        {{ local('Delete') }}
                    </button>
                    <button class="btn-secondary" @click="cancelEdit">
                        {{ local('Cancel') }}
                    </button>
                </div>
            </div>
            <div v-else class="user-prompts-editor empty">
                <i class="ms-Icon ms-Icon--EditNote" style="font-size: 48px; opacity: 0.2;"></i>
                <p>{{ local('Select a template or create a new one') }}</p>
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
            // 顶层 Tab
            tab: 'builtin', // 'builtin' | 'user'
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

            // ── 用户自定义模板 ──
            userTemplates: [],
            selectedUserId: '',
            editingTemplate: null,        // { id?, name, description, template, allowed_operators, example_variables }
            detectedPlaceholders: [],
            previewRendered: '',
            previewMissing: [],
            previewDebounce: null,
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
        this.loadUserTemplates()
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

        // ── 用户自定义模板 ────────────────────────────────────
        async loadUserTemplates() {
            try {
                const res = await axios.get(`${BASE}/user`)
                this.userTemplates = (res.data && res.data.data) || []
            } catch (e) {
                console.warn('[Prompts] loadUserTemplates failed', e)
            }
        },

        extractPlaceholders(tpl) {
            if (!tpl) return []
            const seen = []
            const re = /\{([A-Za-z_][A-Za-z0-9_]*)\}/g
            let m
            while ((m = re.exec(tpl)) !== null) {
                if (!seen.includes(m[1])) seen.push(m[1])
            }
            return seen
        },

        placeholderPreview(tpl) {
            const ps = this.extractPlaceholders(tpl)
            if (!ps.length) return this.local('no placeholders')
            if (ps.length <= 3) return ps.map((p) => `{${p}}`).join(' ')
            return ps.slice(0, 3).map((p) => `{${p}}`).join(' ') + ` +${ps.length - 3}`
        },

        startNewTemplate() {
            this.selectedUserId = ''
            this.editingTemplate = {
                id: null,
                name: '',
                description: '',
                template: '',
                allowed_operators: [],
                example_variables: {},
            }
            this.detectedPlaceholders = []
            this.previewRendered = ''
            this.previewMissing = []
        },

        selectUserTemplate(id) {
            const t = this.userTemplates.find((x) => x.id === id)
            if (!t) return
            this.selectedUserId = id
            this.editingTemplate = {
                id: t.id,
                name: t.name || '',
                description: t.description || '',
                template: t.template || '',
                allowed_operators: [...(t.allowed_operators || [])],
                example_variables: { ...(t.example_variables || {}) },
            }
            this.detectedPlaceholders = this.extractPlaceholders(t.template || '')
            this.requestPreview()
        },

        onTemplateEdit() {
            if (!this.editingTemplate) return
            this.detectedPlaceholders = this.extractPlaceholders(this.editingTemplate.template)
            // 去掉已删掉的占位符对应的 example_variables 键
            const keys = Object.keys(this.editingTemplate.example_variables || {})
            keys.forEach((k) => {
                if (!this.detectedPlaceholders.includes(k)) {
                    delete this.editingTemplate.example_variables[k]
                }
            })
            this.requestPreview()
        },

        setExampleVar(name, value) {
            if (!this.editingTemplate) return
            this.editingTemplate.example_variables[name] = value
            this.requestPreview()
        },

        updateAllowedOps(text) {
            if (!this.editingTemplate) return
            this.editingTemplate.allowed_operators = text
                .split(',')
                .map((s) => s.trim())
                .filter(Boolean)
        },

        requestPreview() {
            if (this.previewDebounce) clearTimeout(this.previewDebounce)
            this.previewDebounce = setTimeout(async () => {
                if (!this.editingTemplate) return
                try {
                    const res = await axios.post(`${BASE}/user/preview`, {
                        template: this.editingTemplate.template,
                        variables: this.editingTemplate.example_variables || {},
                    })
                    const data = (res.data && res.data.data) || {}
                    this.previewRendered = data.rendered || ''
                    this.previewMissing = data.missing || []
                } catch (e) {
                    this.previewRendered = ''
                    this.previewMissing = []
                }
            }, 200)
        },

        async saveTemplate() {
            if (!this.editingTemplate) return
            const payload = {
                name: this.editingTemplate.name.trim(),
                description: this.editingTemplate.description || '',
                template: this.editingTemplate.template || '',
                allowed_operators: this.editingTemplate.allowed_operators || [],
                example_variables: this.editingTemplate.example_variables || {},
            }
            if (!payload.name) {
                this.$barWarning && this.$barWarning({ status: 'warning', title: this.local('Name is required') })
                return
            }
            try {
                let res
                if (this.editingTemplate.id) {
                    res = await axios.put(`${BASE}/user/${this.editingTemplate.id}`, payload)
                } else {
                    res = await axios.post(`${BASE}/user`, payload)
                }
                const saved = (res.data && res.data.data) || null
                await this.loadUserTemplates()
                if (saved && saved.id) this.selectUserTemplate(saved.id)
                this.$barWarning && this.$barWarning({ status: 'correct', title: this.local('Template saved') })
            } catch (e) {
                this.$barWarning && this.$barWarning({ status: 'error', title: e.message || 'Save failed' })
            }
        },

        async deleteTemplate() {
            if (!this.editingTemplate || !this.editingTemplate.id) return
            if (!window.confirm(`${this.local('Delete template')} "${this.editingTemplate.name}"?`)) return
            try {
                await axios.delete(`${BASE}/user/${this.editingTemplate.id}`)
                this.editingTemplate = null
                this.selectedUserId = ''
                await this.loadUserTemplates()
            } catch (e) {
                this.$barWarning && this.$barWarning({ status: 'error', title: e.message || 'Delete failed' })
            }
        },

        cancelEdit() {
            this.editingTemplate = null
            this.selectedUserId = ''
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

/* ── Tabs + My Templates ─────────────────────────────────── */
.df-prompts-page {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: rgba(250, 250, 250, 1);

    &.dark {
        background: rgba(36, 36, 36, 1);
        color: rgba(220, 220, 220, 1);
    }
}
.prompts-tabs {
    display: flex;
    gap: 4px;
    padding: 8px 12px 0;
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
}
.df-prompts-page.dark .prompts-tabs {
    border-bottom-color: rgba(255, 255, 255, 0.08);
}
.prompts-tab {
    padding: 8px 14px;
    cursor: pointer;
    font-size: 13px;
    border-radius: 6px 6px 0 0;
    opacity: 0.65;
    display: flex;
    align-items: center;
}
.prompts-tab:hover { opacity: 0.85; }
.prompts-tab.active {
    opacity: 1;
    font-weight: 600;
    background: rgba(255, 255, 255, 1);
    box-shadow: 0 -1px 0 rgba(69, 98, 213, 0.6) inset;
}
.df-prompts-page.dark .prompts-tab.active {
    background: rgba(50, 50, 50, 1);
}
.prompts-tab-count {
    margin-left: 6px;
    padding: 0 6px;
    font-size: 11px;
    border-radius: 8px;
    background: rgba(69, 98, 213, 0.12);
    color: #4562d5;
}

.df-prompts-page .df-prompts-container {
    flex: 1;
    min-height: 0;
}

.df-user-prompts {
    flex: 1;
    min-height: 0;
    display: flex;
    overflow: hidden;

    .user-prompts-sidebar {
        width: 280px;
        border-right: 1px solid rgba(0, 0, 0, 0.08);
        display: flex;
        flex-direction: column;

        .sidebar-header {
            display: flex;
            align-items: center;
            padding: 10px 12px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.06);
            font-weight: 600;
        }
        .sidebar-new-btn {
            color: #4562d5;
            cursor: pointer;
            font-size: 12px;
            display: flex;
            align-items: center;
            gap: 2px;
        }
        .sidebar-scroll {
            flex: 1;
            overflow-y: auto;
        }
        .user-prompt-item {
            padding: 8px 12px;
            border-bottom: 1px solid rgba(0, 0, 0, 0.04);
            cursor: pointer;

            &:hover { background: rgba(69, 98, 213, 0.05); }
            &.active { background: rgba(69, 98, 213, 0.12); }
        }
        .user-prompt-name {
            font-weight: 500;
            font-size: 13px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .user-prompt-desc {
            font-size: 11px;
            opacity: 0.6;
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .user-prompt-meta {
            font-size: 11px;
            opacity: 0.5;
            margin-top: 2px;
            display: flex;
            gap: 4px;
        }
        .sidebar-empty {
            padding: 18px;
            opacity: 0.5;
            font-size: 12px;
            text-align: center;
        }
    }

    .user-prompts-editor {
        flex: 1;
        overflow-y: auto;
        padding: 16px 24px;

        &.empty {
            display: flex;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            color: rgba(100, 100, 100, 0.6);
            text-align: center;
        }

        .editor-row {
            margin-bottom: 14px;

            label {
                display: block;
                font-size: 12px;
                font-weight: 500;
                opacity: 0.7;
                margin-bottom: 4px;
            }
        }
        .editor-input {
            width: 100%;
            padding: 6px 10px;
            font-size: 13px;
            border-radius: 4px;
            border: 1px solid rgba(0, 0, 0, 0.15);
            outline: none;
            box-sizing: border-box;
        }
        .editor-input:focus { border-color: #4562d5; }
        .editor-textarea {
            width: 100%;
            padding: 8px 10px;
            font-size: 13px;
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            border-radius: 4px;
            border: 1px solid rgba(0, 0, 0, 0.15);
            outline: none;
            box-sizing: border-box;
            resize: vertical;
        }
        .editor-textarea:focus { border-color: #4562d5; }
        .placeholder-list {
            margin-top: 6px;
            font-size: 11px;
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }
        .placeholder-label { opacity: 0.55; margin-right: 4px; }
        .placeholder-chip {
            background: rgba(69, 98, 213, 0.1);
            color: #4562d5;
            padding: 1px 6px;
            border-radius: 8px;
            font-family: ui-monospace, Menlo, monospace;
        }
        .kv-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;

            .kv-key {
                width: 100px;
                font-size: 12px;
                font-family: ui-monospace, Menlo, monospace;
                opacity: 0.7;
            }
            .editor-input { flex: 1; }
        }
        .preview-block {
            background: rgba(246, 246, 250, 0.8);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 4px;
            padding: 10px 12px;
            font-family: ui-monospace, Menlo, monospace;
            font-size: 12px;
            white-space: pre-wrap;
            word-break: break-word;
            max-height: 240px;
            overflow-y: auto;
            margin: 0;
        }
        .preview-missing {
            margin: 4px 0 0 0;
            font-size: 11px;
            color: #d64545;
        }
        .editor-actions {
            margin-top: 16px;
            display: flex;
            gap: 8px;
        }
        .btn-primary, .btn-secondary, .btn-danger {
            padding: 6px 14px;
            font-size: 13px;
            border-radius: 4px;
            border: none;
            cursor: pointer;
        }
        .btn-primary { background: #4562d5; color: white; }
        .btn-primary:hover { background: #3550c2; }
        .btn-secondary { background: rgba(0, 0, 0, 0.05); }
        .btn-danger { background: #d64545; color: white; }
        .btn-danger:hover { background: #c23838; }
    }
}

.df-prompts-page.dark .df-user-prompts {
    .user-prompts-sidebar,
    .user-prompts-sidebar .sidebar-header { border-color: rgba(255, 255, 255, 0.08); }
    .user-prompt-item { border-bottom-color: rgba(255, 255, 255, 0.05); }
    .editor-input, .editor-textarea {
        background: rgba(40, 40, 40, 1);
        color: rgba(220, 220, 220, 1);
        border-color: rgba(255, 255, 255, 0.15);
    }
    .preview-block {
        background: rgba(40, 40, 40, 0.7);
        border-color: rgba(255, 255, 255, 0.08);
        color: rgba(220, 220, 220, 1);
    }
    .btn-secondary { background: rgba(255, 255, 255, 0.08); color: #e0e0e0; }
}
</style>
