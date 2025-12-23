<template>
    <div v-show="thisValue" class="panel-dataset-content-block">
        <fv-Collapse v-model="item.expanded" v-for="(item, index) in datasets" :key="index" class="dataset-item"
            :title="item.name" :content="numSamples(item)" :maxHeight="item.showPreview ? 690 : 380"
            background="rgba(251, 251, 251, 1)">
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
            img: {
                database: databaseIcon
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
        ...mapState(useTheme, ['color', 'gradient']),
        numSamples() {
            return (item) => {
                let num = item.num_samples ? item.num_samples : 0
                return `${this.local('Total')}: ${num} ${this.local('samples')}, ${this.local('Size')}: ${(item.file_size / 1000).toFixed(2)} KB`
            }
        }
    },
    mounted() { },
    methods: {
        ...mapActions(useDataflow, ['getDatasets']),
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
