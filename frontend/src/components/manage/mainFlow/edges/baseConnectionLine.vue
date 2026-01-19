<template>
    <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow: visible">
        <defs>
            <!-- 定义一个线性渐变 -->
            <linearGradient id="edge-gradient" x1="0" y1="0" x2="1" y2="0">
                <stop
                    v-for="(value, index) in edgeColors"
                    :key="index"
                    :offset="(index * 100) / (edgeColorsLength - 1) + '%'"
                    :stop-color="value"
                />
            </linearGradient>
        </defs>
        <g>
            <path
                class="vue-flow__connection"
                fill="none"
                :stroke="'url(#edge-gradient)'"
                :stroke-width="3"
                :d="getBezierPath(props)[0]"
            />

            <circle
                :cx="targetX"
                :cy="targetY"
                fill="#fff"
                :r="4"
                stroke="#6F3381"
                :stroke-width="1.5"
            />
        </g>
    </svg>
</template>

<script setup>
import { getBezierPath } from '@vue-flow/core'
import { computed } from 'vue'

const props = defineProps({
    sourceX: {
        type: Number,
        required: true
    },
    sourceY: {
        type: Number,
        required: true
    },
    sourcePosition: {
        type: String,
        required: true
    },
    targetX: {
        type: Number,
        required: true
    },
    targetY: {
        type: Number,
        required: true
    },
    targetPosition: {
        type: String,
        required: true
    },
    data: {
        type: Object
    }
})

const defaultData = {
    colors: ['rgba(229, 123, 67, 1)', 'rgba(225, 107, 56, 1)']
}
const thisData = computed(() => {
    return {
        ...defaultData,
        ...props.data
    }
})
const edgeColors = computed(() => {
    if (thisData.value.colors && thisData.value.colors.length > 0) {
        return thisData.value.colors
    }
    return defaultData.colors
})
const edgeColorsLength = computed(() => edgeColors.value.length)
</script>
