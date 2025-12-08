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
            <span class="info-title">{{ appConfig.local('Pipeline') }}</span>
            <p class="info-value">{{ thisData.pipeline }}</p>
        </div>
        <div class="node-row-item">
            <span class="info-title">{{ appConfig.local('Num. Samples') }}</span>
            <p class="info-value">{{ thisData.num_samples }}</p>
        </div>
        <div class="node-group-item">
            <div class="node-row-item">
                <span class="info-title">{{ appConfig.local('ID') }}</span>
                <p class="info-value tiny" :title="thisData.id">{{ thisData.id }}</p>
            </div>
            <div class="node-row-item">
                <span class="info-title">{{ appConfig.local('Root') }}</span>
                <p class="info-value tiny" :title="thisData.root">{{ thisData.root }}</p>
            </div>
            <div class="node-row-item">
                <span class="info-title">{{ appConfig.local('Hash') }}</span>
                <p class="info-value tiny" :title="thisData.hash">{{ thisData.hash }}</p>
            </div>
            <hr style="margin: 10px 8px" />
            <div
                v-if="thisData.operatorParams"
                v-for="(item, index) in thisData.operatorParams.run"
                :key="`run_${index}`"
                class="node-row-item col"
            >
                <Handle
                    :id="`${item.name}::source::run_key`"
                    type="source"
                    class="handle-item"
                    :position="Position.Right"
                    style="margin-right: -15px"
                />
                <fv-text-box
                    v-model="item.value"
                    :placeholder="appConfig.local('Please input') + ` ${item.name}`"
                    font-size="12"
                    border-radius="8"
                    :reveal-border="true"
                    readonly
                    @mousedown.stop
                    @click.stop
                    style="width: 100%; height: 35px; margin-top: 5px"
                ></fv-text-box>
            </div>
            <div class="node-row-item">
                <fv-button
                    theme="dark"
                    background="linear-gradient(130deg, rgba(161, 145, 206, 0.8), rgba(119, 93, 160, 0.8))"
                    border-color="rgba(119, 93, 160, 0.1)"
                    border-radius="8"
                    :disabled="loading"
                    :is-box-shadow="true"
                    @click="$emit('switch-database', thisData)"
                    @mousedown.stop
                    @click.stop
                    style="width: 100%; margin-top: 15px; cursor: pointer"
                    >{{ appConfig.local('Switch Dataset') }}</fv-button
                >
            </div>
        </div>
    </base-node>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue'
import { useAppConfig } from '@/stores/appConfig'
import { useGlobal } from '@/hooks/general/useGlobal'
import { Position, Handle } from '@vue-flow/core'

import baseNode from '@/components/manage/mainFlow/nodes/baseNode.vue'

import databaseIcon from '@/assets/flow/database.svg'

const { $api } = useGlobal()

const emits = defineEmits(['switch-database', 'update-node-data'])

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

const defaultData = {
    label: 'Dataset',
    status: 'Dataset',
    nodeInfo: 'This is a Dataset node.',
    img: databaseIcon,
    background: 'linear-gradient(130deg, rgba(161, 145, 206, 0.8), rgba(252, 252, 252, 0.8))',
    titleColor: '',
    statusColor: 'rgba(90, 90, 90, 1)',
    infoTitleColor: 'rgba(90, 90, 90, 1)',
    borderColor: 'rgba(177, 146, 247, 1)',
    shadowColor: '',
    groupBackground: 'rgba(255, 255, 255, 0.8)',
    useTargetHandle: false,
    enableDelete: true,
    defaultSourceHandleTop: '50px'
}
const thisData = computed(() => {
    return {
        ...defaultData,
        ...props.data
    }
})

const appConfig = useAppConfig()

const loading = ref(false)
const getNodeDetail = async () => {
    if (!props.data || !props.data.name) return
    loading.value = true
    const res = await $api.datasets.get_dataset_columns(props.data.id).catch(() => {
        loading.value = false
    })
    loading.value = false
    if (res.code === 200) {
        let keys = res.data
        let runPrams = []
        keys.forEach((item) => {
            runPrams.push({
                name: item,
                value: item,
                default_value: item
            })
        })
        let operatorParams = {
            init: [],
            run: []
        }
        operatorParams.run = runPrams
        emits('update-node-data', {
            id: props.id,
            data: {
                ...props.data,
                operatorParams
            }
        })
    }
}

watch(
    () => props.data.id,
    (newVal, oldVal) => {
        getNodeDetail()
    }
)

onMounted(() => {
    getNodeDetail()
})
</script>
