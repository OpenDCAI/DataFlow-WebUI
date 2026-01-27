<template>
    <base-node v-bind="props" :data="thisData" :theme="theme">
        <div class="fv-loading-block">
            <fv-progress-ring v-if="loading" :loading="true" :r="18" :border-width="3" background="white"
                :color="thisData.borderColor"></fv-progress-ring>
        </div>
        <div class="node-row-item">
            <span class="info-title" style="font-size: 13px; color: rgba(52, 199, 89, 1)">{{
                appConfig.local('Init. Parameters')
            }}</span>
        </div>
        <hr />
        <div v-if="allowedPrompts.length > 0 && isPromptTemplate" class="node-row-item col" @mousedown.stop @click.stop>
            <span class="info-title">{{ appConfig.local('Prompt Template') }}</span>
            <fv-combobox :theme="theme" v-model="promptTemplateModel" :placeholder="appConfig.local('Select Prompt')"
                :options="allowedPrompts" :choosen-slider-background="thisData.borderColor"
                :reveal-background-color="[thisData.shadowColor, 'rgba(255, 255, 255, 1)']"
                :reveal-border-color="thisData.borderColor" border-radius="8" style="width: 100%"></fv-combobox>
        </div>
        <div v-if="thisData.operatorParams" v-show="item.show" v-for="(item, index) in thisData.operatorParams.init"
            :key="`init_${index}`" class="node-row-item col">
            <span class="info-title">{{ item.name }}</span>
            <value-input :theme="theme" v-model="item.value" :item-obj="item" :this-data="thisData" @mousedown.stop
                @click.stop></value-input>
        </div>
        <div class="node-row-item">
            <span class="info-title" style="font-size: 13px; color: rgba(0, 122, 255, 1)">{{
                appConfig.local('Run Parameters')
            }}</span>
        </div>
        <hr />
        <div v-if="thisData.operatorParams" v-show="hiddenParam(item)"
            v-for="(item, index) in thisData.operatorParams.run" :key="`run_${index}`" class="node-row-item col">
            <span class="info-title">{{ item.name }}</span>
            <Handle :id="`${item.name}::target::run_key`" type="target" class="handle-item" :position="Position.Left" />
            <Handle :id="`${item.name}::source::run_key`" type="source" class="handle-item"
                :position="Position.Right" />
            <fv-text-box :theme="theme" v-model="item.value"
                :placeholder="appConfig.local('Please input') + ` ${item.name}`" font-size="12" border-radius="3"
                :border-width="2" :reveal-border="true" :border-color="thisData.shadowColor"
                :focus-border-color="thisData.borderColor" underline style="width: 100%; height: 35px"
                @update:modelValue="emitUpdateRunValue(item)" @mousedown.stop @click.stop></fv-text-box>
        </div>
        <div v-if="currentLog" class="node-group-item"
            :style="{ background: theme === 'dark' ? 'rgba(0, 0, 0, 1)' : '' }">
            <p class="info-title">Execution Logs</p>
            <fv-progress-bar v-show="currentProgress > -1 && currentProgress < 100" :model-value="currentProgress"
                :foreground="thisData.borderColor" style="width: 100%; margin: 5px 0px;"></fv-progress-bar>
            <div class="log-list" @wheel.stop>
                <p v-for="(text, index) in currentLog" :key="index">{{ text }}</p>
            </div>
            <div class="node-row-item" style="gap: 5px">
                <fv-button v-show="isOverStep" theme="dark" icon="Diagnostic" :background="thisData.borderColor"
                    border-radius="8" font-size="10" :is-box-shadow="true" style="width: 100%; margin-top: 5px"
                    @mousedown.stop @click.stop @click="showDetails">{{ appConfig.local('Show Details') }}</fv-button>
                <fv-button v-show="isOverStep" theme="dark" icon="Download" :background="thisData.borderColor"
                    border-radius="8" font-size="10" :is-box-shadow="true" style="width: 100%; margin-top: 5px"
                    @mousedown.stop @click.stop @click="downloadData">{{ appConfig.local('Download Data') }}</fv-button>
            </div>
        </div>
    </base-node>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useGlobal } from '@/hooks/general/useGlobal'
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'
import { useTheme } from '@/stores/theme'
import { Position, Handle } from '@vue-flow/core'

import baseNode from '@/components/manage/mainFlow/nodes/baseNode.vue'
import valueInput from './valueInput.vue'

const { $api } = useGlobal()

const emits = defineEmits(['update-node-data', 'update-run-value', 'show-details'])

const props = defineProps({
    id: {
        type: String,
        required: true
    },
    position: {
        type: Object,
        required: true
    },
    selected: {
        type: Boolean,
        default: false
    },
    data: {
        type: Object,
        default: () => ({})
    }
})

const appConfig = useAppConfig()
const _theme = useTheme()
const dataflow = useDataflow()

const theme = computed(() => {
    return _theme.theme
})

const defaultData = {
    label: 'Operator',
    status: 'Operator',
    nodeInfo: '',
    background: '',
    titleColor: '',
    statusColor: 'rgba(90, 90, 90, 1)',
    infoTitleColor: 'rgba(28, 28, 30, 1)',
    borderColor: '',
    shadowColor: '',
    groupBackground: 'rgba(255, 255, 255, 0.8)',
    enableDelete: true
}
const thisData = computed(() => {
    return {
        ...defaultData,
        ...props.data,
        shadowColor: props.data.nodeShadowColor ? props.data.nodeShadowColor : 'rgba(0, 0, 0, 0.05)'
    }
})
const allowedPrompts = computed(() => {
    let allowed_prompts = thisData.value.allowed_prompts || []
    let results = []
    allowed_prompts.forEach((item, index) => {
        results.push({
            key: item,
            text: item
        })
    })
    return results
})
const isPromptTemplate = computed(() => {
    try {
        return thisData.value.operatorParams.init.some((item) => item.name === 'prompt_template')
    } catch (error) {
        return false
    }
})
const promptTemplateModel = computed({
    get() {
        try {
            let prompt_template = thisData.value.operatorParams.init.find(
                (item) => item.name === 'prompt_template'
            )
            if (!prompt_template.value) return {}
            return {
                key: prompt_template.value,
                text: prompt_template.value
            }
        } catch (error) {
            return {}
        }
    },
    set(val) {
        if (!val.key) return
        if (thisData.value.operatorParams.init) {
            let prompt_template = thisData.value.operatorParams.init.find(
                (item) => item.name === 'prompt_template'
            )
            prompt_template.value = val.key
        }
    }
})
const hiddenParam = (item) => {
    let filter_keys = ['storage'];
    if (filter_keys.includes(item.name)) return false
    return true
}

const loading = ref(false) // for data loading display
const paramsWrapper = (objs) => {
    for (let item of objs) {
        if (!item.value) item.value = item.default_value || ''
        item.show = true
        if (item.name === 'prompt_template') {
            let val = item.value
            if (val.indexOf("'") > -1) {
                val = val.match(/'(.*)'/)
                if (val) {
                    val = val[1]
                    val = val.split('.')
                    val = val[val.length - 1]
                } else val = ''
            }
            item.value = val
            item.show = false
        }
    }
    return objs
}
const getNodeDetail = async () => {
    if (!props.data || !props.data.name || !props.data.flowId) return
    if (!thisData.value._cache_parameter) {
        loading.value = true
        const res = await $api.operators.get_operator_detail_by_name(props.data.name).catch(() => {
            loading.value = false
        })
        loading.value = false
        if (res.code === 200) {
            thisData.value._cache_parameter = res.data.parameter
        } else {
            loading.value = false
            return
        }
    }
    let parameter = thisData.value._cache_parameter
    let operatorParams = {
        init: [],
        run: []
    }
    operatorParams.init = paramsWrapper(parameter.init)
    operatorParams.run = paramsWrapper(parameter.run)
    emits('update-node-data', {
        id: props.id,
        data: {
            ...props.data,
            operatorParams
        }
    })
}

watch(
    () => props.id,
    (newVal, oldVal) => {
        getNodeDetail()
    }
)

watch(
    () => dataflow.executionStep,
    (newVal, oldVal) => {
        syncLoading()
    }
)

watch(
    () => dataflow.execution.status,
    (newVal, oldVal) => {
        syncLoading()
    }
)

const currentLog = computed(() => {
    if (!dataflow.execution) return null
    if (!dataflow.execution.task_id) return null
    let currentKey = `${thisData.value.label}_${thisData.value.pipeline_idx - 1}`
    let currentOutput = dataflow.execution.operator_logs[currentKey]
    if (!currentOutput) return null
    return currentOutput || []
})
const currentProgress = computed(() => {
    if (!dataflow.execution) return null
    if (!dataflow.execution.task_id) return null
    let currentKey = `${thisData.value.label}_${thisData.value.pipeline_idx - 1}`
    let currentDetail = dataflow.execution.operators_detail[currentKey]
    if (!currentDetail) return null
    if (!currentDetail.progress_percentage) return -1
    return currentDetail.progress_percentage
})
const isOverStep = computed(() => {
    if (!dataflow.execution) return null
    if (!dataflow.execution.task_id) return null
    let pipeline_idx = thisData.value.pipeline_idx - 1
    return dataflow.executionStep > pipeline_idx || dataflow.execution.status === 'completed'
})
const syncLoading = () => {
    if (!dataflow.execution) return null
    if (!dataflow.execution.task_id) return null
    let pipeline_idx = thisData.value.pipeline_idx - 1
    let current_step = dataflow.executionStep
    if (current_step === pipeline_idx && dataflow.execution.status !== 'completed') {
        props.data.loading = true // for execution loading display
    } else {
        props.data.loading = false
    }
}

const showDetails = () => {
    emits('show-details', {
        pipeline_idx: thisData.value.pipeline_idx
    })
}
const downloadData = () => {
    emits('download-data', {
        pipeline_idx: thisData.value.pipeline_idx
    })
}

onMounted(async () => {
    await getNodeDetail()
    syncLoading()
})

const emitUpdateRunValue = (item) => {
    emits('update-run-value', {
        nodeId: props.id,
        ...item
    })
}
</script>

<style lang="scss">
.df-flow-default-node {
    .fv-loading-block {
        @include HcenterVcenter;
    }

    .log-list {
        position: relative;
        width: 100%;
        height: auto;
        max-height: 200px;
        padding: 3px;
        background: black;
        font-size: 8px;
        color: rgba(193, 252, 167, 1);
        border-radius: 3px;
        overflow: overlay;
    }
}
</style>
