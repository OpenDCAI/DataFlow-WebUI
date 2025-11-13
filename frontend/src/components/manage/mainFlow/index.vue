<template>
    <div class="df-main-flow-container">
        <VueFlow :nodes="nodes" :edges="edges">
            <template #node-base-node="nodeProps">
                <baseNode v-bind="nodeProps" />
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
import { ref } from 'vue'
import { VueFlow } from '@vue-flow/core'
import baseNode from './nodes/baseNode.vue'
import baseEdge from './edges/baseEdge.vue'
import baseConnectionLine from './edges/baseConnectionLine.vue'

const nodes = ref([
    {
        id: '1',
        type: 'base-node',
        position: { x: 70, y: 160 },
        data: {
            label: 'Node 1',
            nodeInfo: 'Node Info: This is node info block for displaying node information.',
            iconColor: 'rgba(0, 108, 126, 1)'
        }
    },

    {
        id: '2',
        type: 'base-node',
        position: { x: 100, y: 400 },
        data: {
            label: 'Node 2',
            nodeInfo: 'Node Info: This is node info block for displaying node information.',
            icon: 'Accept'
        }
    },

    {
        id: '3',
        type: 'base-node',
        position: { x: 400, y: 800 },
        data: { label: 'Node 3', icon: 'Cloud' }
    },

    {
        id: '4',
        type: 'base-node',
        position: { x: 600, y: 600 },
        data: {
            label: 'Node 4',
            hello: 'world',
            icon: 'World'
        }
    }
])

const edges = ref([
    {
        id: 'e1->2',
        type: 'base-edge',
        source: '1',
        target: '2'
    },

    {
        id: 'e2->3',
        type: 'base-edge',
        source: '2',
        target: '3',
        animated: true
    },

    {
        id: 'e3->4',
        type: 'base-edge',
        source: '3',
        target: '4',

        data: {
            label: 'world'
        }
    }
])
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
