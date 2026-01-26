<template>
    <div v-show="thisValue" class="panel-dataset-content-block">
        <fv-Collapse :theme="theme" v-model="show.add" class="db-add-item" icon="Marquee" :title="local('Add Database')"
            :content="local('Add new database information.')" :disabled-collapse="true" :max-height="'auto'">
            <template v-slot:icon>
                <fv-img :src="img.database" style="width: auto; height: 30px; margin: 0px 5px"></fv-img>
            </template>
            <template v-slot:extension>
                <fv-button v-show="show.add" theme="dark" :is-box-shadow="true" :background="gradient"
                    :disabled="!lock.add || !checkAdd()" border-radius="6" style="width: 90px; margin-right: 5px"
                    @click="confirmAdd">
                    <fv-progress-ring v-model="progress" v-show="progress > 0 && (!lock.add || !checkAdd())" :r="10"
                        :border-width="2" background="rgba(200, 200, 200, 1)" :color="'white'"
                        style="margin-right: 5px"></fv-progress-ring>
                    {{ local('Confirm') }}
                </fv-button>
                <fv-button :theme="show.add ? theme : 'dark'" :is-box-shadow="true"
                    :background="show.add ? '' : gradient" border-radius="6" style="width: 90px" @click="handleAdd">
                    {{ show.add ? local('Cancel') : local('Add') }}
                </fv-button>
            </template>
            <template v-slot:default>
                <div class="db-add-item-row column">
                    <p class="db-add-item-light-title">{{ local('File') }}</p>
                    <div class="db-add-item-row no-pad">
                        <fv-button theme="dark" icon="Add" :is-box-shadow="true" :background="gradient"
                            border-radius="6" style="width: 90px" @click="handleAddFile">
                            {{ local('Add File') }}
                        </fv-button>
                        <p v-show="filePath" class="db-add-item-info" style="margin-left: 15px;">{{ filePath }}</p>
                    </div>
                    <input type="file" style="display: none" ref="fileInput">
                </div>
                <hr />
                <div class="db-add-item-row column">
                    <p class="db-add-item-light-title">{{ local('Database Name') }}</p>
                    <fv-text-box :theme="theme" v-model="databaseName" :placeholder="local('Database Name')"
                        border-radius="6" :reveal-border="true" :is-box-shadow="true"></fv-text-box>
                </div>
                <hr />
                <div class="db-add-item-row column">
                    <p class="db-add-item-light-title">{{ local('Description') }}</p>
                    <fv-text-box :theme="theme" v-model="databaseDescription" :placeholder="local('Description')"
                        border-radius="6" :reveal-border="true" :is-box-shadow="true"></fv-text-box>
                </div>
            </template>
        </fv-Collapse>
        <fv-Collapse :theme="theme" v-model="item.expanded" v-for="(item, index) in datasets" :key="index"
            class="dataset-item" :title="item.name" :content="numSamples(item)"
            :maxHeight="item.showPreview ? 690 : 380" background="rgba(251, 251, 251, 1)">
            <template v-slot:icon>
                <fv-img :src="img.database" style="width: auto; height: 30px; margin: 0px 5px"></fv-img>
            </template>
            <data-info v-if="!item.showPreview" :item="item"></data-info>
            <table-info v-if="item.showPreview" :item="item" @back="item.showPreview = false"></table-info>
            <template v-slot:extension>
                <fv-button theme="dark" :icon="item.showPreview ? 'Hide' : 'View'"
                    :background="'linear-gradient(130deg, rgba(229, 123, 67, 1), rgba(225, 107, 56, 1))'"
                    :borderRadius="8" :isBoxShadow="true" style="margin-right: 5px"
                    @click="showPreview(item, $event)">{{ item.showPreview ? local('Hide') : local('Preview') }}
                </fv-button>
                <fv-button theme="dark" icon="Touch" :background="gradient" :borderRadius="8" :isBoxShadow="true"
                    @click="selectDataset($event, item)">{{ local('Select') }}
                </fv-button>
            </template>
        </fv-Collapse>
    </div>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'
import { useTheme } from '@/stores/theme'

import dataInfo from '../preview/dataInfo.vue'
import tableInfo from '../preview/tableInfo.vue'

import databaseIcon from '@/assets/flow/database.svg'

export default {
    components: {
        dataInfo,
        tableInfo
    },
    props: {
        modelValue: {
            default: false
        }
    },
    data() {
        return {
            thisValue: this.modelValue,
            databaseName: '',
            databaseDescription: '',
            filePath: '',
            progress: 0,
            img: {
                database: databaseIcon
            },
            show: {
                add: false
            },
            lock: {
                add: true
            }
        }
    },
    watch: {
        modelValue(val) {
            this.thisValue = val
        },
        thisValue(val) {
            this.$emit('update:modelValue', val)
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useDataflow, ['datasets']),
        ...mapState(useTheme, ['theme', 'color', 'gradient']),
        numSamples() {
            return (item) => {
                let num = item.num_samples ? item.num_samples : 0
                return `${this.local('Total')}: ${num} ${this.local('samples')}, ${this.local('Size')}: ${(item.file_size / 1000).toFixed(2)} KB`
            }
        }
    },
    mounted() {
        this.eventInit()
    },
    methods: {
        ...mapActions(useDataflow, ['getDatasets']),
        eventInit() {
            this.$refs.fileInput.addEventListener('change', (e) => {
                this.handleFileChange(e)
            })
        },
        handleFileChange(event) {
            const file = event.target.files[0]
            if (file) {
                this.filePath = file.name
            }
        },
        selectDataset(event, item) {
            event.stopPropagation()
            this.$emit('confirm', item)
        },
        showPreview(item, event) {
            event.stopPropagation()
            item.expanded = true
            item.showPreview = !item.showPreview
        },
        handleAddFile() {
            this.$refs.fileInput.click()
        },
        checkAdd() {
            if (this.databaseName === '' || this.databaseDescription === '' || this.filePath === '') {
                return false
            }
            return true
        },
        handleAdd() {
            this.show.add ^= true
            this.databaseName = ''
            this.databaseDescription = ''
            this.filePath = ''
            this.$refs.fileInput.value = null
        },
        confirmAdd() {
            if (!this.checkAdd()) {
                return
            }
            if (!this.lock.add) {
                return
            }
            this.lock.add = false
            this.$api.datasets.upload_dataset(this.databaseName, {
                file: this.$refs.fileInput.files[0]
            }, null, (event) => {
                this.progress = event.loaded / event.total * 100
            }).then((res) => {
                if (res.code === 200) {
                    this.$barWarning(this.local('Add Database Success'), {
                        status: 'correct'
                    })
                    this.handleAdd()
                    this.getDatasets()
                    this.progress = 0
                } else {
                    this.$barWarning(this.local('Add Database Failed') + ': ' + res.message, {
                        status: 'warning'
                    })
                }
                this.lock.add = true
            })
        },
    }
}
</script>

<style lang="scss">
.panel-dataset-content-block {
    position: relative;
    width: 100%;
    height: 100%;
    gap: 5px;
    display: flex;
    flex-direction: column;
    overflow: overlay;

    .dataset-item {
        flex-shrink: 0;

        .collapse-item-content {
            position: relative;
            height: auto;
            transition: all 0.3s;
        }
    }
}
</style>
