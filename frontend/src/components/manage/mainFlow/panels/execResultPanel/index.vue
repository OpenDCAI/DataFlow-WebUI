<template>
    <basePanel v-model="thisValue" :title="title" width="clamp(350px, 90%, 1600px)" height="clamp(500px, 90%, 800px)"
        :theme="theme" :teleport="true">
        <template v-slot:content>
            <div class="panel-result-content-block">
                <div class="left-block">
                    <div v-if="runningResult" class="info-bar-block">
                        <p class="title">{{ local('Task ID') }}: {{ runningResult.task_id }}</p>
                        <time-rounder :model-value="new Date(runningResult.completed_at)" :foreground="color"
                            style="width: auto"></time-rounder>
                    </div>
                    <span class="title-block">{{ local('Execution Sampled Data') }}</span>
                    <table-info :theme="theme" v-if="runningResult && runningResult.sample_data"
                        :table-info="runningResult.sample_data"></table-info>
                    <span class="title-block">{{ local('Current Step Logs') }}</span>
                    <div v-if="operatorLogs.length > 0" class="log-container step">
                        <p v-for="(item, index) in operatorLogs" :key="index" class="log-item">
                            {{ item }}
                        </p>
                    </div>
                </div>
                <div class="right-block">
                    <div v-if="runningResult && runningResult.operators_detail" class="chart-container"
                        :class="[{ dark: theme === 'dark' }]">
                        <span class="title-block">{{ local('Sample Count') }}</span>
                        <sample-chart :theme="theme" :raw-data="runningResult.operators_detail"></sample-chart>
                    </div>
                    <span class="title-block">{{ local('Logs') }}</span>
                    <div v-if="runningResult" class="log-container">
                        <p v-for="(item, index) in runningResult.logs" :key="index" class="log-item">
                            {{ item }}
                        </p>
                    </div>
                </div>
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
import timeRounder from '@/components/general/timeRounder.vue'
import tableInfo from './preview/tableInfo.vue'
import sampleChart from './preview/sampleChart.vue'

export default {
    components: {
        basePanel,
        timeRounder,
        tableInfo,
        sampleChart,
    },
    props: {
        modelValue: {
            default: false
        },
        title: {
            default: 'Execute Result'
        },
        pipeline: {
            default: () => ({})
        },
        currentStep: {
            default: null
        },
        runningResult: {
            default: () => ({})
        }
    },
    data() {
        return {
            thisValue: this.modelValue
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
        ...mapState(useTheme, ['theme', 'color', 'gradient']),
        operators() {
            try {
                return this.runningResult.output.execution_results
            } catch (error) {
                return []
            }
        },
        operatorLogs() {
            try {
                let _step = this.runningResult.operator_logs.length - 1;
                if (this.currentStep !== null) _step = this.currentStep
                let operatorLogs = this.runningResult.operator_logs;
                for (let key in operatorLogs) {
                    let step = parseInt(key.split('_')[1]);
                    if (step == _step) {
                        return operatorLogs[key];
                    }
                }
                return []
            } catch (error) {
                return []
            }
        }
    },
    mounted() {
    },
    methods: {}
}
</script>

<style lang="scss">
.panel-result-content-block {
    position: relative;
    width: 100%;
    height: 100%;
    gap: 5px;
    display: flex;
    overflow: overlay;

    .left-block {
        position: relative;
        width: 50%;
        height: 100%;
        flex: 1;
        gap: 5px;
        display: flex;
        flex-direction: column;
        overflow-x: hidden;
        overflow-y: overlay;
    }

    .right-block {
        position: relative;
        width: 50%;
        height: 100%;
        flex: 1;
        gap: 5px;
        display: flex;
        flex-direction: column;
        overflow-x: hidden;
        overflow-y: overlay;
    }

    .info-bar-block {
        @include HbetweenVcenter;

        position: relative;
        width: 100%;

        .title {
            font-size: 12px;
            font-weight: bold;
        }
    }

    .title-block {
        position: relative;
        width: 100%;
        margin: 5px 0px;
        font-size: 12px;
        font-weight: bold;
    }

    .operators-list {
        @include HcenterC;

        position: relative;
        width: 100%;
        height: 300px;
        gap: 15px;
        overflow: overlay;
        overflow-x: hidden;

        .operator-item {
            @include Vcenter;

            position: relative;
            width: min(300px, 100%);
            height: 50px;
            gap: 5px;
            flex-shrink: 0;
            padding: 10px;
            background: rgba(255, 255, 255, 0.6);
            border: rgba(120, 120, 120, 0.1) solid thin;
            border-radius: 8px;
            transition: background 0.3s;
            cursor: default;

            &:hover {
                background: white;
            }

            &::after {
                content: '';
                position: absolute;
                left: 50%;
                top: 100%;
                width: 2px;
                height: 15px;
                background: rgba(177, 146, 247, 1);
            }

            &:last-child {
                &::after {
                    display: none;
                }
            }

            .operator-icon {
                @include HcenterVcenter;

                width: 30px;
                height: 30px;
                border-radius: 5px;
                color: white;
            }

            .operator-name {
                @include nowrap;

                flex: 1;
                font-size: 15px;
                font-weight: 500;
                color: #222222;
            }
        }
    }

    .log-container {
        @include HstartC;

        position: relative;
        width: 100%;
        height: 300px;
        flex: 1;
        padding: 5px;
        font-size: 12px;
        background: rgba(0, 0, 0, 0.8);
        color: whitesmoke;
        border-radius: 8px;
        overflow: overlay;
        overflow-x: hidden;
        box-shadow: 1px 0px 3px rgba(0, 0, 0, 0.1);

        &.step {
            p {
                color: rgba(193, 252, 167, 1);
            }
        }
    }

    .chart-container {
        position: relative;
        width: 100%;
        height: auto;
        flex-shrink: 0;
        padding: 5px 10px;
        gap: 17px;
        font-size: 12px;
        background: rgba(255, 255, 255, 0.9);
        border: rgba(120, 120, 120, 0.1) solid thin;
        border-radius: 8px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        box-shadow: 0px 0px 3px rgba(0, 0, 0, 0.1);

        &.dark {
            color: whitesmoke;
            background: rgba(200, 200, 200, 0.1);
        }
    }
}
</style>
