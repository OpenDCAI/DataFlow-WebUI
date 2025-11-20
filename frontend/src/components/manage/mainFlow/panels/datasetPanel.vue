<template>
    <basePanel v-model="thisValue" :title="title" width="800px" height="80%" theme="light">
        <template v-slot:content>
            <div class="panel-dataset-content-block">
                <fv-Collapse
                    v-for="(item, index) in datasets"
                    :key="index"
                    class="dataset-item"
                    :title="item.name"
                    :content="numSamples(item)"
                    :maxHeight="380"
                    background="rgba(251, 251, 251, 1)"
                >
                    <template v-slot:icon>
                        <fv-img
                            :src="img.database"
                            style="width: auto; height: 30px; margin: 0px 5px"
                        ></fv-img>
                    </template>
                    <div class="collapse-item-content">
                        <hr />
                        <div class="bp-row column">
                            <p class="bp-title">{{ local('Pipeline') }}</p>
                            <p class="bp-bold-info">{{ item.pipeline }}</p>
                        </div>
                        <hr />
                        <div class="bp-row column">
                            <p class="bp-light-title">{{ local('ID') }}</p>
                            <p class="bp-std-info">{{ item.id }}</p>
                        </div>
                        <hr />
                        <div class="bp-row column">
                            <p class="bp-light-title">{{ local('Root') }}</p>
                            <p class="bp-std-info">{{ item.root }}</p>
                        </div>
                        <hr />
                        <div class="bp-row column">
                            <p class="bp-light-title">{{ local('Hash') }}</p>
                            <p class="bp-std-info">{{ item.hash }}</p>
                        </div>
                    </div>
                    <template v-slot:extension>
                        <fv-button
                            theme="dark"
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

import databaseIcon from '@/assets/flow/database.svg'

export default {
    components: {
        basePanel
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
                    this.datasets = res.data
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
