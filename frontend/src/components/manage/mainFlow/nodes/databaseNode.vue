<template>
    <base-node v-bind="props" :data="thisData">
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
            <div class="node-row-item">
                <fv-button
                    theme="dark"
                    background="linear-gradient(130deg, rgba(161, 145, 206, 0.8), rgba(119, 93, 160, 0.8))"
                    border-color="rgba(119, 93, 160, 0.1)"
                    border-radius="8"
                    :is-box-shadow="true"
                    @click="$emit('switch-database', thisData)"
                    style="width: 100%; margin-top: 15px; cursor: pointer"
                    >{{ appConfig.local('Switch Database') }}</fv-button
                >
            </div>
        </div>
    </base-node>
</template>

<script setup>
import { computed } from 'vue'
import { useAppConfig } from '@/stores/appConfig'

import baseNode from '@/components/manage/mainFlow/nodes/baseNode.vue'

import databaseIcon from '@/assets/flow/database.svg'

const emits = defineEmits(['switch-database'])

const props = defineProps({
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
    label: 'Database',
    status: 'Database',
    nodeInfo: 'This is a Database node.',
    img: databaseIcon,
    background: 'linear-gradient(130deg, rgba(161, 145, 206, 0.8), rgba(252, 252, 252, 0.8))',
    titleColor: '',
    statusColor: 'rgba(90, 90, 90, 1)',
    borderColor: '',
    shadowColor: '',
    groupBackground: 'rgba(255, 255, 255, 0.8)',
    enableDelete: true
}
const thisData = computed(() => {
    return {
        ...defaultData,
        ...props.data
    }
})

const appConfig = useAppConfig()
</script>
