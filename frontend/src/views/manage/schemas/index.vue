<template>
    <div class="df-schemas-container" :class="[{ dark: theme === 'dark' }]">
        <div class="major-container">
            <div class="title-block">
                <p class="main-title">{{ local('JSON Schema Manager') }}</p>
            </div>
            <div class="content-block">
                <!-- Create New Schema -->
                <fv-Collapse :theme="theme" v-model="show.add" class="schema-item" icon="Add"
                    :title="local('Create Schema')" :content="local('Create a new JSON schema')"
                    :disabled-collapse="true" :max-height="'auto'">
                    <template v-slot:extension>
                        <fv-button v-show="show.add" theme="dark" :is-box-shadow="true" :background="gradient"
                            :disabled="!checkAdd() || !lock.add" border-radius="6"
                            style="width: 90px; margin-right: 5px" @click="confirmAdd">
                            {{ local('Confirm') }}
                        </fv-button>
                        <fv-button :theme="show.add ? theme : 'dark'" :is-box-shadow="true"
                            :background="show.add ? '' : gradient" border-radius="6" style="width: 90px"
                            @click="handleAdd">
                            {{ show.add ? local('Cancel') : local('Create') }}
                        </fv-button>
                    </template>
                    <template v-slot:default>
                        <div class="schema-item-row column">
                            <p class="schema-item-light-title">{{ local('Schema Name') }}</p>
                            <fv-text-box :theme="theme" v-model="newSchema.name" :placeholder="local('Schema Name')"
                                border-radius="6" :reveal-border="true" :is-box-shadow="true"></fv-text-box>
                        </div>
                        <hr />
                        <div class="schema-item-row column">
                            <p class="schema-item-light-title">{{ local('Description') }}</p>
                            <fv-text-box :theme="theme" v-model="newSchema.description" 
                                :placeholder="local('Optional description')" border-radius="6" 
                                :reveal-border="true" :is-box-shadow="true" :max-rows="3"></fv-text-box>
                        </div>
                        <hr />
                        <div class="schema-item-row column">
                            <p class="schema-item-light-title">{{ local('JSON Schema') }}</p>
                            <textarea v-model="newSchema.schema" class="schema-editor"
                                :class="[{ dark: theme === 'dark' }]"
                                :placeholder="local('Enter JSON Schema...')"
                                @input="validateSchemaJson"></textarea>
                            <p v-if="schemaError" class="error-message">{{ schemaError }}</p>
                        </div>
                        <hr />
                        <div class="schema-item-row column">
                            <p class="schema-item-light-title">{{ local('Example Data') }}</p>
                            <textarea v-model="newSchema.example" class="schema-editor"
                                :class="[{ dark: theme === 'dark' }]"
                                :placeholder="local('Example JSON data that matches this schema...')"></textarea>
                        </div>
                    </template>
                </fv-Collapse>

                <!-- List of Existing Schemas -->
                <fv-Collapse :theme="theme" v-for="(item, index) in schemaList" :key="index" class="schema-item"
                    icon="Table" :title="item.name" :content="item.description || 'No description'" 
                    :max-height="740">
                    <template v-slot:extension>
                        <fv-button v-show="!item.edit" theme="dark" background="rgba(191, 95, 95, 1)" 
                            foreground="rgba(255, 255, 255, 1)" border-radius="6" :is-box-shadow="true" 
                            style="width: 90px" @click="$event.stopPropagation(), deleteSchema(item)"
                            :disabled="!lock.delete">
                            {{ local('Delete') }}
                        </fv-button>
                        <fv-button v-show="!item.edit" :theme="theme" :icon="item.edit ? 'Cancel' : 'Edit'" 
                            :is-box-shadow="true" border-radius="6" style="width: 90px; margin-left: 5px"
                            @click="$event.stopPropagation(), handleEdit(item)">
                            {{ local('Edit') }}
                        </fv-button>
                    </template>
                    <template v-slot:default>
                        <hr />
                        <div class="schema-item-row sep">
                            <div class="schema-item-row column no-pad" style="flex: 1">
                                <p class="schema-item-light-title">{{ local('ID') }}</p>
                                <p class="schema-item-std-info">{{ item.id }}</p>
                            </div>
                            <fv-button v-show="item.edit" theme="dark" :is-box-shadow="true" :background="gradient"
                                border-radius="6" :disabled="!checkEdit(item) || !lock.edit"
                                style="width: 90px; margin-right: 5px" @click="confirmEdit(item)">
                                {{ local('Confirm') }}
                            </fv-button>
                            <fv-button v-show="item.edit" :theme="theme" :is-box-shadow="true"
                                border-radius="6" style="width: 90px"
                                @click="$event.stopPropagation(), handleEdit(item)">
                                {{ local('Cancel') }}
                            </fv-button>
                        </div>
                        <hr />
                        
                        <!-- Display Mode -->
                        <div v-if="!item.edit">
                            <div class="schema-item-row column">
                                <p class="schema-item-light-title">{{ local('Description') }}</p>
                                <p class="schema-item-std-info">{{ item.description || local('No description') }}</p>
                            </div>
                            <hr />
                            <div class="schema-item-row column">
                                <p class="schema-item-light-title">{{ local('Schema') }}</p>
                                <pre class="schema-code-block" :class="[{ dark: theme === 'dark' }]">{{ formatJson(item.schema) }}</pre>
                                <fv-button :theme="theme" :icon="copyLabel === item.id ? 'CheckMark' : 'Copy'" 
                                    :is-box-shadow="true" border-radius="6" style="margin-top: 10px; width: 90px"
                                    @click="copyToClipboard(item.schema, item.id)">
                                    {{ copyLabel === item.id ? local('Copied') : local('Copy') }}
                                </fv-button>
                            </div>
                            <hr />
                            <div v-if="item.example" class="schema-item-row column">
                                <p class="schema-item-light-title">{{ local('Example Data') }}</p>
                                <pre class="schema-code-block" :class="[{ dark: theme === 'dark' }]">{{ formatJson(item.example) }}</pre>
                            </div>
                        </div>

                        <!-- Edit Mode -->
                        <div v-else>
                            <div class="schema-item-row column">
                                <p class="schema-item-light-title">{{ local('Description') }}</p>
                                <fv-text-box :theme="theme" v-model="item.description" border-radius="6"
                                    :reveal-border="true" :is-box-shadow="true" :max-rows="3"></fv-text-box>
                            </div>
                            <hr />
                            <div class="schema-item-row column">
                                <p class="schema-item-light-title">{{ local('Schema') }}</p>
                                <textarea v-model="item.schema" class="schema-editor"
                                    :class="[{ dark: theme === 'dark' }]"
                                    @input="validateSchemaJson"></textarea>
                                <p v-if="editError[item.id]" class="error-message">{{ editError[item.id] }}</p>
                            </div>
                            <hr />
                            <div class="schema-item-row column">
                                <p class="schema-item-light-title">{{ local('Example Data') }}</p>
                                <textarea v-model="item.example" class="schema-editor"
                                    :class="[{ dark: theme === 'dark' }]"></textarea>
                            </div>
                        </div>

                        <hr />
                        <div class="schema-item-row column">
                            <p class="schema-item-light-title">{{ local('Usage') }}</p>
                            <p class="schema-item-std-info">
                                {{ local('Use this schema in operator parameters to structure LLM outputs') }}
                            </p>
                        </div>
                    </template>
                </fv-Collapse>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import axios from 'axios'

const BASE = '/api/v1/json_schemas'

export default {
    data() {
        return {
            schemaList: [],
            newSchema: {
                name: '',
                description: '',
                schema: '',
                example: ''
            },
            show: {
                add: false
            },
            schemaError: '',
            editError: {},
            copyLabel: '',
            lock: {
                add: true,
                edit: true,
                delete: true
            }
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme', 'color', 'gradient'])
    },
    mounted() {
        this.loadSchemas()
    },
    methods: {
        async loadSchemas() {
            try {
                const res = await axios.get(`${BASE}/`)
                if (res.data?.code === 200) {
                    this.schemaList = res.data.data || []
                    this.schemaList.forEach(item => {
                        item.edit = false
                    })
                }
            } catch (e) {
                console.error('Failed to load schemas', e)
                this.$barWarning({ status: 'warning', title: 'Failed to load schemas' })
            }
        },
        validateSchemaJson(event) {
            const target = event.target || event
            const value = target.value
            try {
                if (value.trim()) {
                    JSON.parse(value)
                    this.schemaError = ''
                    Object.keys(this.editError).forEach(key => {
                        delete this.editError[key]
                    })
                }
            } catch (e) {
                const msg = e.message || 'Invalid JSON'
                this.schemaError = msg
            }
        },
        formatJson(json) {
            try {
                if (typeof json === 'string') {
                    return JSON.stringify(JSON.parse(json), null, 2)
                }
                return JSON.stringify(json, null, 2)
            } catch (e) {
                return json
            }
        },
        checkAdd() {
            return this.newSchema.name.trim() && this.newSchema.schema.trim() && !this.schemaError
        },
        checkEdit(item) {
            return item.name.trim() && item.schema.trim() && !this.editError[item.id]
        },
        handleAdd() {
            this.show.add = !this.show.add
            if (!this.show.add) {
                this.newSchema = { name: '', description: '', schema: '', example: '' }
                this.schemaError = ''
            }
        },
        confirmAdd() {
            if (!this.checkAdd() || !this.lock.add) return
            
            this.lock.add = false
            axios.post(`${BASE}/`, {
                name: this.newSchema.name,
                description: this.newSchema.description,
                schema: this.newSchema.schema,
                example: this.newSchema.example
            }).then((res) => {
                if (res.data?.code === 200) {
                    this.loadSchemas()
                    this.show.add = false
                    this.newSchema = { name: '', description: '', schema: '', example: '' }
                    this.schemaError = ''
                    this.$barWarning({ status: 'correct', title: this.local('Schema created successfully') })
                } else {
                    this.$barWarning({ status: 'warning', title: res.data?.message || 'Creation failed' })
                }
                this.lock.add = true
            }).catch((err) => {
                this.$barWarning({ status: 'error', title: err.message || 'Failed to create schema' })
                this.lock.add = true
            })
        },
        handleEdit(item) {
            item.edit = !item.edit
            if (!item.edit) {
                this.loadSchemas()
                delete this.editError[item.id]
            }
        },
        confirmEdit(item) {
            if (!this.checkEdit(item) || !this.lock.edit) return
            
            try {
                JSON.parse(item.schema)
                if (item.example) {
                    JSON.parse(item.example)
                }
            } catch (e) {
                this.$barWarning({ status: 'warning', title: 'Invalid JSON' })
                return
            }
            
            this.lock.edit = false
            axios.put(`${BASE}/${item.id}`, {
                name: item.name,
                description: item.description,
                schema: item.schema,
                example: item.example
            }).then((res) => {
                if (res.data?.code === 200) {
                    item.edit = false
                    delete this.editError[item.id]
                    this.$barWarning({ status: 'correct', title: this.local('Schema updated successfully') })
                    this.loadSchemas()
                } else {
                    this.$barWarning({ status: 'warning', title: res.data?.message || 'Update failed' })
                }
                this.lock.edit = true
            }).catch((err) => {
                this.$barWarning({ status: 'error', title: err.message || 'Failed to update schema' })
                this.lock.edit = true
            })
        },
        deleteSchema(item) {
            this.$dialog.warning({
                title: this.local('Delete Schema'),
                content: `${this.local('Are you sure to delete')} "${item.name}"?`,
                okText: this.local('Delete'),
                cancelText: this.local('Cancel')
            }).then(res => {
                if (res) {
                    this.lock.delete = false
                    axios.delete(`${BASE}/${item.id}`).then((res) => {
                        if (res.data?.code === 200) {
                            this.$barWarning({ status: 'correct', title: this.local('Schema deleted successfully') })
                            this.loadSchemas()
                        } else {
                            this.$barWarning({ status: 'warning', title: res.data?.message || 'Delete failed' })
                        }
                        this.lock.delete = true
                    }).catch((err) => {
                        this.$barWarning({ status: 'error', title: err.message || 'Failed to delete schema' })
                        this.lock.delete = true
                    })
                }
            })
        },
        copyToClipboard(text, itemId) {
            try {
                navigator.clipboard.writeText(typeof text === 'string' ? text : JSON.stringify(JSON.parse(text), null, 2))
                this.copyLabel = itemId
                setTimeout(() => {
                    this.copyLabel = ''
                }, 2000)
            } catch (e) {
                this.$barWarning({ status: 'warning', title: this.local('Copy failed') })
            }
        }
    }
}
</script>

<style lang="scss" scoped>
.df-schemas-container {
    @include app;
    background: rgba(250, 250, 250, 1);
    display: flex;
    flex-direction: column;

    &.dark {
        background: rgba(36, 36, 36, 1);

        .major-container {
            .title-block {
                .main-title {
                    color: whitesmoke;
                }
            }

            .content-block {
                .schema-item {
                    &:hover {
                        background: rgba(50, 50, 50, 1);
                    }
                }

                .schema-editor {
                    background: rgba(40, 40, 40, 1);
                    color: rgba(200, 200, 200, 1);
                    border: 1px solid rgba(70, 70, 70, 1);

                    &:focus {
                        border-color: rgba(100, 100, 100, 1);
                        outline: none;
                    }
                }

                .schema-code-block {
                    background: rgba(40, 40, 40, 1);
                    color: rgba(200, 200, 200, 1);
                    border: 1px solid rgba(70, 70, 70, 1);
                }
            }
        }
    }

    .major-container {
        position: relative;
        width: 100%;
        height: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        overflow: hidden;

        .title-block {
            position: relative;
            width: 100%;
            padding: 20px 30px;
            box-sizing: border-box;
            border-bottom: 1px solid rgba(200, 200, 200, 0.3);

            .main-title {
                margin: 0;
                font-size: 24px;
                font-weight: 600;
                color: rgba(0, 0, 0, 1);
            }
        }

        .content-block {
            position: relative;
            width: 100%;
            flex: 1;
            box-sizing: border-box;
            padding: 20px 30px;
            overflow-y: auto;
            overflow-x: hidden;

            .schema-item {
                position: relative;
                margin-bottom: 10px;
                border-radius: 6px;
                border: 1px solid rgba(200, 200, 200, 0.3);

                &:hover {
                    background: rgba(240, 240, 240, 1);
                }

                &:last-child {
                    margin-bottom: 0;
                }

                .schema-item-row {
                    position: relative;
                    width: 100%;
                    display: flex;
                    align-items: center;
                    padding: 0 20px;

                    &.sep {
                        padding: 15px 20px;
                        border-bottom: 1px solid rgba(200, 200, 200, 0.2);
                    }

                    &.column {
                        flex-direction: column;
                        align-items: flex-start;
                        padding: 15px 20px;

                        &.no-pad {
                            padding: 0;
                        }
                    }

                    .schema-item-light-title {
                        font-size: 13px;
                        font-weight: 500;
                        color: rgba(100, 100, 100, 1);
                        margin: 0 0 10px 0;
                    }

                    .schema-item-std-info {
                        font-size: 14px;
                        color: rgba(80, 80, 80, 1);
                        margin: 0;
                        word-break: break-word;
                    }

                    .schema-item-bold-info {
                        font-size: 14px;
                        font-weight: 500;
                        color: rgba(60, 60, 60, 1);
                        margin: 0;
                    }
                }

                hr {
                    position: relative;
                    width: calc(100% - 40px);
                    height: 0;
                    border: none;
                    border-top: 1px solid rgba(200, 200, 200, 0.2);
                    margin: 0;
                }
            }

            .schema-editor {
                width: 100%;
                min-height: 150px;
                max-height: 300px;
                padding: 10px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 12px;
                border-radius: 4px;
                border: 1px solid rgba(200, 200, 200, 0.3);
                background: rgba(250, 250, 250, 1);
                color: rgba(30, 30, 30, 1);
                resize: vertical;
                box-sizing: border-box;

                &:focus {
                    border-color: rgba(100, 100, 200, 1);
                    outline: none;
                }
            }

            .schema-code-block {
                width: 100%;
                padding: 15px;
                background: rgba(245, 245, 245, 1);
                border: 1px solid rgba(200, 200, 200, 0.3);
                border-radius: 4px;
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                font-size: 12px;
                color: rgba(30, 30, 30, 1);
                white-space: pre-wrap;
                word-wrap: break-word;
                overflow-x: auto;
                margin: 10px 0;
            }

            .error-message {
                font-size: 12px;
                color: rgba(191, 95, 95, 1);
                margin: 5px 0 0 0;
            }
        }
    }
}
</style>
