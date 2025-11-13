<template>
    <svg>
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
        <defs>
            <!-- 定义一个发光滤镜 -->
            <filter id="edge-glow" x="-50%" y="-50%" width="200%" height="200%">
                <feDropShadow
                    dx="0"
                    dy="1"
                    stdDeviation="3"
                    :flood-color="edgeColors[0]"
                    flood-opacity="0.3"
                />
            </filter>
        </defs>
        <BaseEdge
            :path="path[0]"
            :style="{
                stroke: 'url(#edge-gradient)',
                strokeWidth: 3,
                filter: 'url(#edge-glow)'
            }"
        />
    </svg>
    <!-- Use the `EdgeLabelRenderer` to escape the SVG world of edges and render your own custom label in a `<div>` ctx -->
    <EdgeLabelRenderer>
        <div
            v-show="thisData.label"
            :style="{
                pointerEvents: 'all',
                position: 'absolute',
                background: edgeColors[0],
                transform: `translate(-50%, -50%) translate(${path[1]}px,${path[2]}px)`
            }"
            class="nodrag nopan df-flow-default-edge-label"
        >
            {{ thisData.label }}
        </div>
    </EdgeLabelRenderer>
</template>

<script setup>
import { BaseEdge, EdgeLabelRenderer, getBezierPath } from '@vue-flow/core'
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
    targetX: {
        type: Number,
        required: true
    },
    targetY: {
        type: Number,
        required: true
    },
    sourcePosition: {
        type: String,
        required: true
    },
    targetPosition: {
        type: String,
        required: true
    },
    data: {
        type: Object,
        required: true
    }
})

const path = computed(() => getBezierPath(props))
const defaultData = {
    label: '',
    colors: ['#3498db', '#9b59b6']
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

<script>
export default {
    inheritAttrs: false
}
</script>

<style lang="scss">
.df-flow-default-edge-label {
    height: 20px;
    padding: 10px;
    font-size: 12px;
    color: whitesmoke;
    border-radius: 12px;
    display: flex;
    justify-content: center;
    align-items: center;
}
</style>
