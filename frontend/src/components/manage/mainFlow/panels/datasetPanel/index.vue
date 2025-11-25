<template>
    <basePanel v-model="thisValue" :title="title" width="800px" height="80%" theme="light">
        <template v-slot:content>
            <div class="panel-dataset-content-block">
                <fv-Collapse
                    v-model="item.expanded"
                    v-for="(item, index) in datasets"
                    :key="index"
                    class="dataset-item"
                    :title="item.name"
                    :content="numSamples(item)"
                    :maxHeight="item.showPreview ? 690 : 380"
                    background="rgba(251, 251, 251, 1)"
                >
                    <template v-slot:icon>
                        <fv-img
                            :src="img.database"
                            style="width: auto; height: 30px; margin: 0px 5px"
                        ></fv-img>
                    </template>
                    <data-info v-if="!item.showPreview" :item="item"></data-info>
                    <table-info
                        v-if="item.showPreview"
                        :item="item"
                        @back="item.showPreview = false"
                    ></table-info>
                    <template v-slot:extension>
                        <fv-button
                            theme="dark"
                            :icon="item.showPreview ? 'Hide' : 'View'"
                            :background="'linear-gradient(130deg, rgba(229, 123, 67, 1), rgba(225, 107, 56, 1))'"
                            :borderRadius="8"
                            :isBoxShadow="true"
                            style="margin-right: 5px"
                            @click="showPreview(item, $event)"
                            >{{ item.showPreview ? local('Hide') : local('Preview') }}
                        </fv-button>
                        <fv-button
                            theme="dark"
                            icon="Touch"
                            :background="gradient"
                            :borderRadius="8"
                            :isBoxShadow="true"
                            @click="selectDataset($event, item)"
                            >{{ local('Select') }}
                        </fv-button>
                    </template>
                </fv-Collapse>
            </div>
        </template>
        <template v-slot:control="{ close }">
            <fv-button
                :borderRadius="8"
                :isBoxShadow="true"
                style="width: 120px; margin-right: 8px"
                @click="close"
                >{{ local('Close') }}</fv-button
            >
        </template>
    </basePanel>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'

import basePanel from '@/components/general/basePanel.vue'
import dataInfo from './preview/dataInfo.vue'
import tableInfo from './preview/tableInfo.vue'

import databaseIcon from '@/assets/flow/database.svg'

export default {
    components: {
        basePanel,
        dataInfo,
        tableInfo
    },
    props: {
        modelValue: {
            default: false
        },
        title: {
            default: 'Database'
        }
    },
    data() {
        return {
            thisValue: this.modelValue,
            datasets: [],
            img: {
                database: databaseIcon
            }
        }
    },
    watch: {
        modelValue(val) {
            this.thisValue = val
            if (val) {
                this.getDatasets()
            }
        },
        thisValue(val) {
            this.$emit('update:modelValue', val)
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['color', 'gradient']),
        numSamples() {
            return (item) => {
                let num = item.num_samples ? item.num_samples : 0
                return `${this.local('Total')}: ${num} ${this.local('samples')}, ${this.local('Size')}: ${(item.file_size / 1000).toFixed(2)} KB`
            }
        }
    },
    mounted() {},
    methods: {
        async getDatasets() {
            this.$api.datasets.list_datasets().then((res) => {
                if (res.success) {
                    let datasets = res.data
                    datasets.forEach((item) => {
                        item.showPreview = false
                        item.expanded = false
                    })
                    this.datasets = datasets
                } else {
                    this.$barWarning(res.message, {
                        status: 'warning'
                    })
                }
            })
        },
        selectDataset(event, item) {
            event.stopPropagation()
            this.$emit('confirm', item)
        },
        showPreview(item, event) {
            event.stopPropagation()
            item.expanded = true
            item.showPreview = !item.showPreview
        }
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
