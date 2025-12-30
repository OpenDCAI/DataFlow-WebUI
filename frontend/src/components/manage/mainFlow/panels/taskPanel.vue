<template>
    <basePanel v-model="thisValue" :title="title" width="800px" height="80%" theme="light">
        <template v-slot:content>
            <div v-show="thisValue" class="panel-task-content-block">
                <fv-Collapse
                    v-for="(item, index) in filteredTasks"
                    :key="index"
                    class="task-item"
                    :title="item.id"
                    :content="item.meta.execution_id"
                    :maxHeight="item.showPreview ? 690 : 380"
                    background="rgba(251, 251, 251, 1)"
                    :disabled-collapse="true"
                >
                    <template v-slot:icon>
                        <fv-img
                            :src="img.task"
                            style="width: auto; height: 30px; margin: 0px 5px"
                        ></fv-img>
                    </template>
                    <template v-slot:extension>
                        <fv-button
                            theme="dark"
                            :icon="'View'"
                            :background="'linear-gradient(130deg, rgba(229, 123, 67, 1), rgba(225, 107, 56, 1))'"
                            :borderRadius="8"
                            :isBoxShadow="true"
                            @click="confirmView(item)"
                            >{{ local('View') }}
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
import { mapState, mapActions } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'
import { useTheme } from '@/stores/theme'

import basePanel from '@/components/general/basePanel.vue'

import taskIcon from '@/assets/flow/task.svg'

export default {
    components: {
        basePanel
    },
    props: {
        modelValue: {
            default: false
        },
        title: {
            default: 'task'
        },
        currentPipeline: {
            default: () => ({})
        }
    },
    data() {
        return {
            thisValue: this.modelValue,
            img: {
                task: taskIcon
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
        ...mapState(useDataflow, ['tasks']),
        ...mapState(useTheme, ['color', 'gradient']),
        filteredTasks() {
            return this.tasks.filter((item) => item.meta.pipeline_id === this.currentPipeline.id)
        }
    },
    mounted() {},
    methods: {
        ...mapActions(useDataflow, ['getTasks']),
        confirmView(item) {
            this.$emit('confirm', {
                exec_id: item.meta.execution_id,
                task_id: item.id
            })
            this.thisValue = false
        }
    }
}
</script>

<style lang="scss">
.panel-task-content-block {
    position: relative;
    width: 100%;
    height: 100%;
    gap: 5px;
    display: flex;
    flex-direction: column;
    overflow: overlay;

    .task-item {
        flex-shrink: 0;

        .collapse-item-content {
            position: relative;
            height: auto;
            transition: all 0.3s;
        }
    }
}
</style>
