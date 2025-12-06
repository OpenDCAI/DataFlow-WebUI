<template>
    <div class="df-default-container" :class="[{ 'show-pipeline': show.pipeline }]">
        <pipeline v-show="show.pipeline" class="df-pipeline-container"></pipeline>
        <div class="df-flow-container">
            <mainFlow
                :id="flowId"
                v-model:nodes="nodes"
                v-model:edges="edges"
                @switch-database="show.dataset = true"
                @connect="onConnect"
                @connect-start="onConnectStart"
                @connect-end="onConnectEnd"
                @update-run-value="useEdgeSync.syncRunValue($event, flowId)"
            ></mainFlow>
            <div class="control-menu-block">
                <fv-command-bar
                    v-model="value"
                    :options="options"
                    :item-border-radius="30"
                    background="rgba(250, 250, 250, 0.8)"
                    class="command-bar"
                >
                    <template v-slot:optionItem="x">
                        <div class="command-bar-item-wrapper">
                            <fv-img v-if="x.item.img" class="option-img" :src="x.item.img" alt="" />
                            <i
                                v-else
                                class="ms-Icon icon"
                                :class="[`ms-Icon--${x.valueTrigger(x.item.icon)}`]"
                                :style="{ color: x.valueTrigger(x.item.foreground) }"
                            ></i>
                            <p
                                class="option-name"
                                :style="{ color: x.valueTrigger(x.item.foreground) }"
                            >
                                {{ x.valueTrigger(x.item.name) }}
                            </p>
                            <i
                                v-show="x.item.secondary.length > 0"
                                class="ms-Icon ms-Icon--ChevronDown icon"
                            ></i>
                        </div>
                    </template>
                    <template v-slot:right-space>
                        <div class="command-bar-right-space">
                            <fv-toggle-switch
                                v-model="isAutoConnectionModel"
                                :width="75"
                                :on="local('Auto')"
                                :off="local('Manual')"
                                :insideContent="true"
                                :height="30"
                                :switch-on-background="gradient"
                                :title="local('Whether Auto Connect Run Edges')"
                            >
                            </fv-toggle-switch>
                            <fv-button
                                :theme="currentServing ? 'dark' : 'light'"
                                :background="
                                    currentServing
                                        ? 'linear-gradient(135deg, rgba(69, 98, 213, 1), #ff0080, #ff8c00)'
                                        : ''
                                "
                                border-radius="30"
                                style="width: 30px; height: 30px"
                                @click="showServing"
                            >
                                <transition-group tag="span" name="df-scale-up-to-up">
                                    <i
                                        v-show="currentServing"
                                        key="0"
                                        class="ms-Icon"
                                        :class="[`ms-Icon--DialShape4`]"
                                    ></i>
                                    <i
                                        v-show="!currentServing"
                                        key="1"
                                        class="ms-Icon"
                                        :class="[`ms-Icon--More`]"
                                    ></i>
                                </transition-group>
                                <i
                                    v-show="false"
                                    class="ms-Icon"
                                    :class="[`ms-Icon--${currentServing ? 'DialShape4' : 'More'}`]"
                                ></i>
                            </fv-button>
                            <fv-button
                                theme="dark"
                                icon="Play"
                                background="linear-gradient(90deg, rgba(69, 98, 213, 1), rgba(161, 145, 206, 1))"
                                foreground="rgba(255, 255, 255, 1)"
                                border-color="rgba(255, 255, 255, 0.3)"
                                border-radius="30"
                                :reveal-background-color="[
                                    'rgba(255, 255, 255, 0.5)',
                                    'rgba(103, 105, 251, 0.6)'
                                ]"
                            >
                                {{ this.local('Run') }}
                            </fv-button>
                            <fv-button
                                theme="dark"
                                background="rgba(191, 95, 95, 0.6)"
                                foreground="rgba(255, 255, 255, 1)"
                                border-color="whitesmoke"
                                border-radius="30"
                                :title="local('Delete')"
                                style="width: 30px; height: 30px"
                            >
                                <i class="ms-Icon ms-Icon--Delete"></i>
                            </fv-button>
                        </div>
                    </template>
                </fv-command-bar>
            </div>
        </div>
        <datasetPanel
            v-model="show.dataset"
            :title="local('Database')"
            @confirm="confirmDataset"
        ></datasetPanel>
        <operatorPanel v-model="show.operator" :title="local('Operator')"></operatorPanel>
        <fv-right-menu
            v-model="show.serving"
            class="serving-menu"
            ref="servingMenu"
            :rightMenuWidth="250"
            background="rgba(255, 255, 255, 0.3)"
            :fullExpandAnimation="true"
            style="z-index: 6"
        >
            <p
                style="
                    width: calc(100% - 20px);
                    margin: 10px;
                    font-size: 12px;
                    font-weight: bold;
                    user-select: none;
                    cursor: default;
                "
            >
                {{ local('Select Serving') }}
            </p>
            <hr />
            <span
                class="serving-item"
                :class="{ choosen: currentServing && currentServing.id === servingItem.id }"
                v-for="servingItem in servingList"
                :key="servingItem.id"
                @click="chooseServing(servingItem)"
            >
                <p class="main-title">{{ servingItem.name }}</p>
                <p class="sec-title">{{ servingItem.cls_name }}</p>
            </span>
            <hr />
            <fv-button
                :icon="servingList.length > 0 ? '' : 'Add'"
                border-radius="8"
                style="width: calc(100% - 20px); margin-left: 10px; margin-top: 5px"
                @click="$Go('/m/serving'), (show.serving = false)"
                >{{
                    servingList.length > 0 ? local('Serving Manage') : local('Add Serving')
                }}</fv-button
            >
        </fv-right-menu>
    </div>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import { useDataflow } from '@/stores/dataflow'
import { useVueFlow } from '@vue-flow/core'
import { useEdgeSync } from '@/hooks/dataflow/useEdgeSync'

import mainFlow from '@/components/manage/mainFlow/index.vue'
import pipeline from '@/components/manage/pipeline/index.vue'
import datasetPanel from '@/components/manage/mainFlow/panels/datasetPanel/index.vue'
import operatorPanel from '@/components/manage/mainFlow/panels/operatorPanel.vue'

import databaseIcon from '@/assets/flow/database.svg'
import pipelineIcon from '@/assets/flow/pipeline.svg'
import operatorIcon from '@/assets/flow/operator.svg'
import saveIcon from '@/assets/flow/save.svg'

export default {
    components: {
        mainFlow,
        pipeline,
        datasetPanel,
        operatorPanel
    },
    data() {
        return {
            flowId: 'df-main-flow',
            value: null,
            options: [
                {
                    name: () => this.local('Database'),
                    icon: 'Play',
                    img: databaseIcon,
                    func: () => {
                        this.show.dataset = true
                    }
                },
                {
                    name: () => this.local('Pipeline'),
                    img: pipelineIcon,
                    func: () => {
                        this.show.pipeline ^= true
                    }
                },
                {
                    name: () => this.local('Operator'),
                    img: operatorIcon,
                    func: () => {
                        this.show.operator = true
                    }
                },
                {
                    name: () => this.local('Save'),
                    img: saveIcon
                }
            ],
            nodes: [
                // {
                //     id: '1',
                //     type: 'base-node',
                //     position: { x: 70, y: 160 },
                //     data: {
                //         label: 'Node 1',
                //         nodeInfo:
                //             'Node Info: This is node info block for displaying node information.',
                //         iconColor: 'rgba(0, 108, 126, 1)'
                //     }
                // },
                // {
                //     id: '2',
                //     type: 'base-node',
                //     position: { x: 100, y: 400 },
                //     data: {
                //         label: 'Node 2',
                //         nodeInfo:
                //             'Node Info: This is node info block for displaying node information.',
                //         icon: 'Accept'
                //     }
                // },
                // {
                //     id: '3',
                //     type: 'base-node',
                //     position: { x: 400, y: 800 },
                //     data: { label: 'Node 3', icon: 'Cloud' }
                // }
            ],

            edges: [
                // {
                //     id: 'e1->2',
                //     type: 'base-edge',
                //     source: '1',
                //     target: '2'
                // },
                // {
                //     id: 'e2->3',
                //     type: 'base-edge',
                //     source: '2',
                //     target: '3',
                //     animated: true,
                //     data: {
                //         label: 'world'
                //     }
                // }
            ],
            sourceDatabase: null,
            servingList: [],
            currentServing: null,
            useEdgeSync: new useEdgeSync(),
            show: {
                dataset: false,
                pipeline: false,
                operator: false,
                serving: false
            },
            lock: {
                serving: true
            }
        }
    },
    watch: {
        sourceDatabase: {
            handler(newVal, oldVal) {
                if (newVal !== oldVal) {
                    this.updateDatabaseNode()
                }
            },
            deep: true
        },
        isAutoConnection(val) {
            if (val) {
                this.useEdgeSync.autoConnectAllRunEdges(this.flowId, this.$Guid)
            }
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['color', 'gradient']),
        ...mapState(useDataflow, ['isAutoConnection']),
        isAutoConnectionModel: {
            get() {
                return this.isAutoConnection
            },
            set(val) {
                this.switchAutoConnection(val)
            }
        }
    },
    mounted() {
        this.setViewport()
        this.getServingList()
    },
    methods: {
        ...mapActions(useDataflow, ['switchAutoConnection']),
        setViewport() {
            const flow = useVueFlow(this.flowId)
            flow.setViewport({
                x: 0,
                y: 0,
                zoom: 1
            })
        },
        updateDatabaseNode() {
            if (!this.sourceDatabase) return
            const flow = useVueFlow(this.flowId)
            const existsNode = this.nodes.find((node) => node.type === 'database-node')
            if (existsNode) {
                flow.updateNodeData(existsNode.id, {
                    ...existsNode.data,
                    label: this.sourceDatabase.name,
                    ...this.sourceDatabase
                })
            } else {
                flow.addNodes({
                    id: 'db-node',
                    type: 'database-node',
                    position: { x: 500, y: 160 },
                    data: {
                        flowId: this.flowId,
                        label: this.sourceDatabase.name,
                        ...this.sourceDatabase
                    }
                })
            }
        },
        confirmDataset(dataset) {
            this.sourceDatabase = dataset
            this.show.dataset = false
        },
        getServingList() {
            if (!this.lock.serving) return
            this.lock.serving = false
            this.$api.serving.list_serving_instances_api_v1_serving__get().then((res) => {
                if (res.code === 200) {
                    this.servingList = res.data
                    this.lock.serving = true
                } else {
                    this.$barWarning(res.message, {
                        status: 'warning'
                    })
                }
            })
        },
        showServing($event) {
            $event.preventDefault()
            $event.stopPropagation()
            this.$refs.servingMenu.rightClick($event, document.body)
        },
        chooseServing(servingItem) {
            this.currentServing = servingItem
        },
        syncRunValue(item) {
            const flow = useVueFlow(this.flowId)
            let edges = flow.edges.value.filter((edge) => edge.source === item.nodeId)
            for (let edge of edges) {
                let sourceKeyName = edge.sourceHandle ? edge.sourceHandle.split('::')[0] : null
                if (sourceKeyName !== item.name) continue
                let targetNode = flow.findNode(edge.target)
                let targetKeyName = edge.targetHandle ? edge.targetHandle.split('::')[0] : null
                if (targetNode) {
                    let targetIndex = targetNode.data.operatorParams.run.findIndex(
                        (item) => item.name === targetKeyName
                    )
                    if (targetIndex !== -1) {
                        targetNode.data.operatorParams.run[targetIndex].value = item.value
                    }
                }
            }
        },
        onConnect(connection) {
            const { source, sourceHandle, target, targetHandle } = connection
            let sourceHandleObj = this.useEdgeSync.decHandle(sourceHandle)
            let targetHandleObj = this.useEdgeSync.decHandle(targetHandle)
            let sourceType = sourceHandleObj.direction
            let targetType = targetHandleObj.direction
            let sourceKeyName = sourceHandleObj.name
            let targetKeyName = targetHandleObj.name
            let sourceKeyType = sourceHandleObj.edgeType
            let targetKeyType = targetHandleObj.edgeType
            if (sourceType === targetType) return
            if (sourceKeyType !== targetKeyType) {
                this.$barWarning(this.local('Illegal connection'), {
                    status: 'warning'
                })
                return
            }
            const flow = useVueFlow(this.flowId)
            let existsEdge = this.edges.find(
                (edge) =>
                    edge.source === source &&
                    edge.target === target &&
                    edge.sourceHandle === sourceHandle &&
                    edge.targetHandle === targetHandle
            )
            if (existsEdge) {
                if (existsEdge.data.edgeType === 'node' && this.isAutoConnection) {
                    this.useEdgeSync.removeRunEdges(source, target, this.flowId)
                }
                flow.removeEdges(existsEdge.id)
            } else {
                flow.addEdges({
                    id: this.$Guid(),
                    type: 'base-edge',
                    source: source,
                    target: target,
                    sourceHandle: sourceHandle,
                    targetHandle: targetHandle,
                    animated: sourceKeyType !== 'node',
                    data: {
                        label: sourceKeyType === 'node' ? 'Node' : 'Key',
                        edgeType: sourceKeyType
                    }
                })
                if (sourceKeyType === 'run_key') {
                    let sourceNode = flow.findNode(source)
                    let targetNode = flow.findNode(target)
                    if (sourceNode && targetNode) {
                        let targetIndex = targetNode.data.operatorParams.run.findIndex(
                            (item) => item.name === targetKeyName
                        )
                        let sourceIndex = sourceNode.data.operatorParams.run.findIndex(
                            (item) => item.name === sourceKeyName
                        )
                        if (targetIndex !== -1 && sourceIndex !== -1) {
                            targetNode.data.operatorParams.run[targetIndex].value =
                                sourceNode.data.operatorParams.run[sourceIndex].value
                        }
                    }
                } else {
                    if (this.isAutoConnection)
                        this.useEdgeSync.autoConnectRunEdges(
                            source,
                            target,
                            this.flowId,
                            this.$Guid
                        )
                }
            }
        },
        onConnectStart(params) {},
        onConnectEnd(event) {
            console.log(event)
        }
    }
}
</script>

<style lang="scss">
.df-default-container {
    position: relative;
    width: 100%;
    height: 100%;
    padding: 15px;
    background-color: rgba(241, 241, 241, 1);
    display: flex;

    .df-pipeline-container {
        position: absolute;
        left: 0px;
        top: 15px;
        width: 300px;
        height: calc(100% - 30px);
        border-top-left-radius: 15px;
        border-bottom-left-radius: 15px;
        box-shadow: 1px 0px 2px rgba(120, 120, 120, 0.1);
        z-index: 2;
    }

    .df-flow-container {
        position: relative;
        width: 100%;
        height: 100%;
        flex: 1;
        background: rgba(250, 250, 250, 1);
        border: rgba(120, 120, 120, 0.1) solid thin;
        border-radius: 15px;
        box-shadow: inset 0px 0px 6px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }

    .control-menu-block {
        position: absolute;
        left: 0px;
        top: 0px;
        width: 100%;
        height: auto;
        padding: 35px 0px;
        display: flex;
        justify-content: center;

        .command-bar {
            min-width: 320px;
            width: 70%;
            max-width: 700px;
            border: rgba(120, 120, 120, 0.1) solid thin;
            border-radius: 30px;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1);

            .command-bar-item {
                &:hover {
                    .option-img {
                        filter: grayscale(0);
                    }
                }
            }

            .command-bar-item-wrapper {
                position: relative;
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;

                &:hover {
                    .option-img {
                        filter: grayscale(0);
                    }
                }
            }

            .option-img {
                width: auto;
                height: 15px;
                filter: grayscale(100%);
                transition: filter 0.2s;
            }

            .option-name {
                margin-left: 8px;
                font-size: 12px;
                color: rgba(45, 48, 56, 1);
            }

            .command-bar-right-space {
                @include Vcenter;

                position: relative;
                width: auto;
                height: 100%;
                padding-right: 5px;
                gap: 3px;
            }
        }
    }
}

.serving-menu {
    .serving-item {
        position: relative;
        flex-direction: column;
        line-height: 1.5;

        &.choosen {
            &::before {
                content: '';
                position: absolute;
                left: 0px;
                top: 10px;
                width: 3px;
                height: calc(100% - 20px);
                background: linear-gradient(135deg, rgba(69, 98, 213, 1), #ff0080);
                border-radius: 8px;
            }

            .main-title {
                @include color-rainbow;

                color: rgba(69, 98, 213, 1);
            }
        }

        .main-title {
            font-size: 16px;
        }

        .sec-title {
            font-size: 10px;
            color: rgba(120, 120, 120, 1);
        }
    }
}

.df-scale-up-to-up-enter-active {
    animation: scaleUp 0.7s ease both;
    animation-delay: 0.3s;
}
.df-scale-up-to-up-leave-active {
    position: absolute;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    animation: scaleDownUp 0.7s ease both;
    z-index: 8;
}
@keyframes scaleUp {
    from {
        opacity: 0;
        transform: scale(0.3);
    }
}
@keyframes scaleDownUp {
    to {
        opacity: 0;
        transform: scale(1.2);
    }
}
</style>
