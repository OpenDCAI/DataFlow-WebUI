<template>
    <div class="df-main-flow-container">
        <VueFlow :id="id" v-model:nodes="thisNodes" v-model:edges="thisEdges">
            <Background
                variant="dots"
                gap="20"
                size="3"
                color="rgba(200, 200, 200, 0.3)"
            ></Background>
            <template #node-base-node="nodeProps">
                <baseNode v-bind="nodeProps" />
            </template>
            <template #node-database-node="nodeProps">
                <databaseNode v-bind="nodeProps" @switch-database="switchDatabase" />
            </template>

            <template #connection-line="connectionLineProps">
                <baseConnectionLine v-bind="connectionLineProps"></baseConnectionLine>
            </template>
            <template #edge-base-edge="edgeProps">
                <baseEdge v-bind="edgeProps" />
            </template>
        </VueFlow>
    </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import baseNode from './nodes/baseNode.vue'
import baseEdge from './edges/baseEdge.vue'
import databaseNode from './nodes/databaseNode.vue'
import baseConnectionLine from './edges/baseConnectionLine.vue'

const emits = defineEmits(['switch-database', 'update:nodes', 'update:edges'])

const props = defineProps({
    id: {
        type: String,
        required: true
    },
    nodes: {
        type: Array,
        default: () => []
    },
    edges: {
        type: Array,
        default: () => []
    }
})

const thisNodes = ref(props.nodes)
const thisEdges = ref(props.edges)
watch(
    () => props.nodes,
    (newNodes) => {
        thisNodes.value = newNodes
    }
)
watch(
    () => props.edges,
    (newEdges) => {
        thisEdges.value = newEdges
    }
)
watch(
    () => thisNodes.value,
    (newNodes) => {
        emits('update:nodes', newNodes)
    }
)
watch(
    () => thisEdges.value,
    (newEdges) => {
        emits('update:edges', newEdges)
    }
)

const switchDatabase = (dataset) => {
    emits('switch-database', dataset)
}
</script>

<style lang="scss">
/* import the necessary styles for Vue Flow to work */
@import '@vue-flow/core/dist/style.css';

/* import the default theme, this is optional but generally recommended */
@import '@vue-flow/core/dist/theme-default.css';

.df-main-flow-container {
    position: relative;
    width: 100%;
    height: 100%;
}
</style>
