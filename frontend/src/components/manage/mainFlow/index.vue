<template>
    <div class="df-main-flow-container">
        <VueFlow
            class="main-flow"
            :id="id"
            v-model:nodes="thisNodes"
            v-model:edges="thisEdges"
            @dragover="dragOver"
            @drop="drop"
            @dragleave="dragLeave"
            @connect="$emit('connect', $event)"
            @connect-end="$emit('connect-end', $event)"
            @connect-start="$emit('connect-start', $event)"
        >
            <Background
                variant="dots"
                gap="20"
                size="3"
                :color="'rgba(200, 200, 200, 0.3)'"
                :style="{
                    backgroundColor: isDragOver ? 'rgba(87, 99, 206, 0.05)' : 'transparent',
                    transition: 'background-color 0.2s ease'
                }"
            ></Background>
            <template #node-base-node="nodeProps">
                <baseNode v-bind="nodeProps" @delete-node="deleteNode" />
            </template>
            <template #node-database-node="nodeProps">
                <databaseNode
                    v-bind="nodeProps"
                    @delete-node="deleteNode"
                    @switch-database="switchDatabase"
                    @update-node-data="updateNodeData"
                />
            </template>
            <template #node-operator-node="nodeProps">
                <operatorNode
                    v-bind="nodeProps"
                    @delete-node="deleteNode"
                    @update-node-data="updateNodeData"
                    @update-run-value="updateRunValue"
                    @show-details="showDetails"
                    @download-data="downloadData"
                />
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
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { useGlobal } from '@/hooks/general/useGlobal'
import { useAppConfig } from '@/stores/appConfig'
import { Background } from '@vue-flow/background'
import baseNode from './nodes/baseNode.vue'
import baseEdge from './edges/baseEdge.vue'
import databaseNode from './nodes/databaseNode.vue'
import operatorNode from './nodes/operatorNode/index.vue'
import baseConnectionLine from './edges/baseConnectionLine.vue'

const { $Guid, $infoBox } = useGlobal()
const appConfig = useAppConfig()
const emits = defineEmits([
    'switch-database',
    'update:nodes',
    'update:edges',
    'connect',
    'connect-end',
    'connect-start',
    'update-run-value',
    'show-details'
])

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

const updateNodeData = (nodeInfo) => {
    const flow = useVueFlow(props.id)
    const existsNode = flow.findNode(nodeInfo.id)
    if (existsNode) {
        flow.updateNodeData(existsNode.id, nodeInfo.data)
    }
}

const updateRunValue = (runValue) => {
    emits('update-run-value', runValue)
}

const isDragOver = ref(false)
const dragOver = (event) => {
    event.preventDefault()
    isDragOver.value = true
}
const drop = (event) => {
    event.preventDefault()
    let data = event.dataTransfer.getData('application/vueflow')
    let offsetX = event.dataTransfer.getData('event/offsetX')
    if (!data) return
    data = JSON.parse(data)
    data.enableDelete = true
    const flow = useVueFlow(props.id)
    const { screenToFlowCoordinate } = useVueFlow(props.id)
    const position = screenToFlowCoordinate({
        x: event.clientX - offsetX,
        y: event.clientY - 30
    })
    const newNode = {
        id: $Guid(),
        type: 'operator-node',
        position: position,
        data: {
            flowId: props.id,
            ...data
        }
    }
    flow.addNodes(newNode)
    console.log(data)

    isDragOver.value = false
}
const dragLeave = (event) => {
    event.preventDefault()
    isDragOver.value = false
}

const deleteNode = (nodeInfo) => {
    $infoBox(appConfig.local(`Are you sure to delete this node?`), {
        status: 'error',
        confirm: () => {
            const flow = useVueFlow(props.id)
            flow.removeNodes(nodeInfo.id)
        }
    })
}

const showDetails = ({ pipeline_idx }) => {
    emits('show-details', pipeline_idx)
}
const downloadData = ({ pipeline_idx }) => {
    emits('download-data', pipeline_idx)
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
