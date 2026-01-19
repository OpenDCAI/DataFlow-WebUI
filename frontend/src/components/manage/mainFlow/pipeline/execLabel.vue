<template>
    <div
        v-if="isShow"
        class="exec-label-container"
        :title="local('Total') + `: ${currentTasks.length} ` + local('Running')"
    >
        <fv-img :src="img.task" class="exec-label-icon"></fv-img>
        <p class="task-title">{{ currentTasks.length }}</p>
    </div>
</template>

<script>
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'

import taskIcon from '@/assets/flow/task.svg'
import { mapState } from 'pinia'

export default {
    props: {
        modelValue: {
            default: () => ({})
        }
    },
    data() {
        return {
            img: {
                task: taskIcon
            }
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useDataflow, ['tasks']),
        currentTasks() {
            if (!this.modelValue) return []
            let tags = this.modelValue.tags
            if (!Array.isArray(tags)) return []
            if (tags.includes('template')) return []
            let result = []
            this.tasks.forEach((item) => {
                if (item.pipeline_id === this.modelValue.id) {
                    result.push(item)
                }
            })
            return result
        },
        isShow() {
            return this.currentTasks.length > 0
        }
    },
    methods: {}
}
</script>

<style lang="scss">
.exec-label-container {
    @include Vcenter;

    position: relative;
    width: auto;
    height: auto;
    gap: 3px;

    .exec-label-icon {
        width: 16px;
        height: 16px;
    }

    .task-title {
        font-size: 12px;
        color: rgba(232, 151, 50, 1);
        font-weight: bold;
    }
}
</style>
