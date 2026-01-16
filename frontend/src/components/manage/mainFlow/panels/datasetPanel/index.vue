<template>
    <basePanel v-model="thisValue" :title="title" width="800px" height="80%" :theme="theme">
        <template v-slot:content>
            <div class="panel-dataset-content-wrapper">
                <fv-pivot :theme="theme" v-model="choosenPivot" class="pivot-panel" :items="pivotItems" :tab="true"
                    :fontSize="12" :sliderBackground="gradient" :borderRadius="8" padding="0px 5px"
                    itemPadding="0px 10px" :sliderBorderRadius="12"></fv-pivot>
                <hr />
                <common-dataset :model-value="choosenPivot && choosenPivot.key === 'Common'"
                    @confirm="$emit('confirm', $event)"></common-dataset>
                <text2sql-dataset :model-value="choosenPivot && choosenPivot.key === 'text2sql'"></text2sql-dataset>
            </div>
        </template>
        <template v-slot:control="{ close }">
            <fv-button :theme="theme" :borderRadius="8" :isBoxShadow="true" style="width: 120px; margin-right: 8px"
                @click="close">{{
                    local('Close') }}</fv-button>
        </template>
    </basePanel>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'
import { useTheme } from '@/stores/theme'

import basePanel from '@/components/general/basePanel.vue'
import commonDataset from './commonDataset/index.vue'
import text2sqlDataset from './text2sqlDataset/index.vue'

export default {
    components: {
        basePanel,
        commonDataset,
        text2sqlDataset
    },
    props: {
        modelValue: {
            default: false
        },
        title: {
            default: 'Dataset'
        }
    },
    data() {
        return {
            thisValue: this.modelValue,
            choosenPivot: null,
            pivotItems: [
                {
                    key: 'Common',
                    name: () => this.local('Common')
                },
                {
                    key: 'text2sql',
                    name: () => this.local('Text2SQL'),
                }
            ],
        }
    },
    watch: {
        modelValue(val) {
            this.thisValue = val
            if (val) {
                this.getDatasets()
                this.getText2SqlDatasets()
            }
        },
        thisValue(val) {
            this.$emit('update:modelValue', val)
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useDataflow, ['datasets']),
        ...mapState(useTheme, ['theme', 'color', 'gradient']),
    },
    mounted() { },
    methods: {
        ...mapActions(useDataflow, ['getDatasets', 'getText2SqlDatasets']),
    }
}
</script>

<style lang="scss">
.panel-dataset-content-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    gap: 5px;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .pivot-panel {
        height: 30px;
        flex-shrink: 0;
    }
}
</style>
