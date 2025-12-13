<template>
    <base-node v-bind="props" :data="thisData">
        <div class="fv-loading-block">
            <fv-progress-ring
                v-if="loading"
                :loading="true"
                :r="18"
                :border-width="3"
                background="white"
                :color="thisData.borderColor"
            ></fv-progress-ring>
        </div>
        <div class="node-row-item">
            <span class="info-title" style="font-size: 13px; color: rgba(52, 199, 89, 1)">{{
                appConfig.local('Init. Parameters')
            }}</span>
        </div>
        <hr />
        <div v-if="allowedPrompts.length > 0" class="node-row-item col" @mousedown.stop @click.stop>
            <span class="info-title">{{ appConfig.local('Prompt Template') }}</span>
            <fv-combobox
                v-model="promptTemplateModel"
                :placeholder="appConfig.local('Select Prompt')"
                :options="allowedPrompts"
                :choosen-slider-background="thisData.borderColor"
                :reveal-background-color="[thisData.shadowColor, 'rgba(255, 255, 255, 1)']"
                :reveal-border-color="thisData.borderColor"
                border-radius="8"
                style="width: 100%"
            ></fv-combobox>
        </div>
        <div
            v-if="thisData.operatorParams"
            v-show="item.show"
            v-for="(item, index) in thisData.operatorParams.init"
            :key="`init_${index}`"
            class="node-row-item col"
        >
            <span class="info-title">{{ item.name }}</span>
            <fv-text-box
                v-if="item.name.indexOf('_serving') === -1"
                v-model="item.value"
                :placeholder="appConfig.local('Please input') + ` ${item.name}`"
                font-size="12"
                border-radius="8"
                :reveal-border="true"
                style="width: 100%; height: 35px"
                @mousedown.stop
                @click.stop
            ></fv-text-box>
            <fv-combobox
                v-if="item.name.indexOf('_serving') !== -1"
                :model-value="computedServingItem(item)"
                @update:modelValue="setServingItem(item, $event)"
                :placeholder="appConfig.local('Select Serving')"
                :options="servingList"
                :choosen-slider-background="thisData.borderColor"
                :reveal-background-color="[thisData.shadowColor, 'rgba(255, 255, 255, 1)']"
                :reveal-border-color="thisData.borderColor"
                border-radius="8"
                style="width: 100%"
                @mousedown.stop
                @click.stop
            ></fv-combobox>
        </div>
        <div class="node-row-item">
            <span class="info-title" style="font-size: 13px; color: rgba(0, 122, 255, 1)">{{
                appConfig.local('Run Parameters')
            }}</span>
        </div>
        <hr />
        <div
            v-if="thisData.operatorParams"
            v-for="(item, index) in thisData.operatorParams.run"
            :key="`run_${index}`"
            class="node-row-item col"
        >
            <span class="info-title">{{ item.name }}</span>
            <Handle
                :id="`${item.name}::target::run_key`"
                type="target"
                class="handle-item"
                :position="Position.Left"
            />
            <Handle
                :id="`${item.name}::source::run_key`"
                type="source"
                class="handle-item"
                :position="Position.Right"
            />
            <fv-text-box
                v-model="item.value"
                :placeholder="appConfig.local('Please input') + ` ${item.name}`"
                font-size="12"
                border-radius="8"
                :reveal-border="true"
                style="width: 100%; height: 35px"
                @update:modelValue="emitUpdateRunValue(item)"
                @mousedown.stop
                @click.stop
            ></fv-text-box>
        </div>
    </base-node>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useGlobal } from '@/hooks/general/useGlobal'
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'
import { Position, Handle } from '@vue-flow/core'

import baseNode from '@/components/manage/mainFlow/nodes/baseNode.vue'

const { $api } = useGlobal()

const emits = defineEmits(['switch-database', 'update-node-data', 'update-run-value'])

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
const dataflow = useDataflow()

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

const servingList = computed(() => {
    return dataflow.servingList
})
const computedServingItem = (item) => {
    let selectedItem = servingList.value.find((it) => it.key === item.value)
    return selectedItem || dataflow.currentServing || {}
}
const setServingItem = (item, val) => {
    if (!val.key) return
    item.value = val.key
}

const loading = ref(false)
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

onMounted(() => {
    getNodeDetail()
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
}
</style>
