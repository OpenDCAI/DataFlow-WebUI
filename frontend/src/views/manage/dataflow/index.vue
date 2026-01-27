<template>
    <div class="df-default-container" :class="[{ dark: theme === 'dark', 'show-pipeline': show.pipeline }]">
        <pipeline v-model="show.pipeline" v-model:loading="lock.loading" v-model:pipeline="currentPipeline"
            :flow-id="flowId" class="df-pipeline-container" @confirm-dataset="confirmDataset($event, true)"
            @select-pipeline="selectPipelineCallback"></pipeline>
        <div class="df-flow-container">
            <mainFlow :id="flowId" v-model:nodes="nodes" v-model:edges="edges" @switch-database="show.dataset = true"
                @connect="onConnect" @connect-start="onConnectStart" @connect-end="onConnectEnd"
                @update-run-value="useEdgeSync.syncRunValue($event, flowId)" @show-details="showExecDetails"
                @download-data="downloadData" @click="show.pipeline = false"></mainFlow>
            <div class="control-menu-block">
                <fv-command-bar :theme="theme" v-model="value" :options="options" :item-border-radius="30"
                    :background="theme === 'dark' ? '' : 'rgba(250, 250, 250, 0.8)'" class="command-bar">
                    <template v-slot:optionItem="x">
                        <div class="command-bar-item-wrapper">
                            <fv-img v-if="x.item.img" class="option-img" :src="x.item.img" alt="" />
                            <i v-else class="ms-Icon icon" :class="[`ms-Icon--${x.valueTrigger(x.item.icon)}`]"
                                :style="{ color: x.valueTrigger(x.item.foreground) }"></i>
                            <p class="option-name" :style="{ color: x.valueTrigger(x.item.foreground) }">
                                {{ x.valueTrigger(x.item.name) }}
                            </p>
                            <i v-show="x.item.secondary.length > 0" class="ms-Icon ms-Icon--ChevronDown icon"></i>
                        </div>
                    </template>
                    <template v-slot:right-space>
                        <div class="command-bar-right-space">
                            <fv-toggle-switch :theme="theme" v-model="isAutoConnectionModel" :width="75"
                                :on="local('Auto')" :off="local('Manual')" :insideContent="true" :height="30"
                                :off-foreground="theme === 'dark' ? 'rgba(255, 255, 255, 1)' : ''"
                                borderColor="rgba(235, 235, 235, 1)" ring-background="rgba(180, 180, 180, 1)"
                                :switch-on-background="gradient" :title="local('Whether Auto Connect Run Edges')">
                            </fv-toggle-switch>
                            <fv-button :theme="currentServing ? 'dark' : theme" :background="currentServing
                                ? 'linear-gradient(135deg, rgba(69, 98, 213, 1), #ff0080, #ff8c00)'
                                : ''
                                " border-radius="30" :disabled="!lock.serving" style="width: 30px; height: 30px"
                                @click="showServing">
                                <transition-group tag="span" name="df-scale-up-to-up">
                                    <i v-show="currentServing" key="0" class="ms-Icon"
                                        :class="[`ms-Icon--DialShape4`]"></i>
                                    <i v-show="!currentServing" key="1" class="ms-Icon" :class="[`ms-Icon--More`]"></i>
                                </transition-group>
                                <i v-show="false" class="ms-Icon"
                                    :class="[`ms-Icon--${currentServing ? 'DialShape4' : 'More'}`]"></i>
                            </fv-button>
                            <fv-button theme="dark"
                                background="linear-gradient(90deg, rgba(69, 98, 213, 1), rgba(161, 145, 206, 1))"
                                foreground="rgba(255, 255, 255, 1)" border-color="rgba(255, 255, 255, 0.3)"
                                border-radius="30" :disabled="!currentPipeline" :reveal-background-color="[
                                    'rgba(255, 255, 255, 0.5)',
                                    'rgba(103, 105, 251, 0.6)'
                                ]" style="width: 120px;" @click="handleRunClick">
                                <i v-show="lock.running" class="ms-Icon ms-Icon--Play" style="margin-right: 5px"></i>
                                <fv-progress-ring v-show="!lock.running" loading="true" :r="10" :border-width="2"
                                    background="rgba(200, 200, 200, 1)" :color="'white'"
                                    style="margin-right: 5px"></fv-progress-ring>
                                <p>{{ this.local('Save & Run') }}</p>
                            </fv-button>
                            <fv-button v-show="!lock.running && executionInfo.task_id" theme="dark"
                                background="rgba(200, 38, 95, 0.9)" font-size="10" foreground="rgba(255, 255, 255, 1)"
                                border-color="whitesmoke" border-radius="30" :title="local('Stop')"
                                style="width: 30px; height: 30px" @click="stopExecution">
                                <i class="ms-Icon ms-Icon--StopSolid"></i>
                            </fv-button>
                            <fv-button theme="dark" background="rgba(191, 95, 95, 0.6)"
                                foreground="rgba(255, 255, 255, 1)" border-color="whitesmoke" border-radius="30"
                                :title="local('Delete')" style="width: 30px; height: 30px" @click="resetFlow">
                                <i class="ms-Icon ms-Icon--Delete"></i>
                            </fv-button>
                        </div>
                    </template>
                </fv-command-bar>
                <current-pipeline-block v-model="currentPipeline" :taskId="executionInfo.task_id"
                    @recover-click="recoverPipeline"></current-pipeline-block>
            </div>
        </div>
        <page-loading :model-value="!lock.loading" title="Loading..."></page-loading>
        <datasetPanel v-model="show.dataset" :title="local('Dataset')" @confirm="confirmDataset"></datasetPanel>
        <operatorPanel v-model="show.operator" :title="local('Operator')"></operatorPanel>
        <fv-right-menu :theme="theme" v-model="show.serving" class="serving-menu" ref="servingMenu"
            :rightMenuWidth="250" :background="theme === 'dark' ? 'rgba(30, 30, 30, 1)' : 'rgba(255, 255, 255, 0.3)'"
            :fullExpandAnimation="true" style="z-index: 6">
            <p style="
                    width: calc(100% - 20px);
                    margin: 10px;
                    font-size: 12px;
                    font-weight: bold;
                    user-select: none;
                    cursor: default;
                ">
                {{ local('Select Serving') }}
            </p>
            <hr />
            <span class="serving-item" :class="{ choosen: currentServing && currentServing.id === servingItem.id }"
                v-for="servingItem in servingList" :key="servingItem.id" @click="chooseServing(servingItem)">
                <p class="main-title">{{ servingItem.name }}</p>
                <p class="sec-title">{{ servingItem.cls_name }}</p>
            </span>
            <hr />
            <fv-button :theme="theme" :icon="servingList.length > 0 ? '' : 'Add'" border-radius="8"
                style="width: calc(100% - 20px); margin-left: 10px; margin-top: 5px"
                @click="$Go('/m/serving'), (show.serving = false)">{{
                    servingList.length > 0 ? local('Serving Manage') : local('Add Serving')
                }}</fv-button>
        </fv-right-menu>
        <pipelinePanel v-model="show.pipelinePanel" :add-panel-mode="'custom'" :title="local('Pipeline')"
            @confirm="addPipeline"></pipelinePanel>
        <execResultPanel v-model="show.execResult" :title="local('Execute Result')" :current-pipeline="currentPipeline"
            :current-step="executionInfo.currentStep" :running-result="executionInfo.runningResult"></execResultPanel>
        <taskPanel v-model="show.taskPanel" :title="local('Executions')" :current-pipeline="currentPipeline"
            @confirm="handleWatchExecution"></taskPanel>
    </div>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import { useDataflow } from '@/stores/dataflow'
import { useVueFlow } from '@vue-flow/core'
import { useEdgeSync } from '@/hooks/dataflow/useEdgeSync'
import { usePipelineOperation } from '@/hooks/dataflow/usePipelineOperation'

import mainFlow from '@/components/manage/mainFlow/index.vue'
import pipeline from '@/components/manage/mainFlow/pipeline/index.vue'
import pipelinePanel from '@/components/manage/mainFlow/panels/piplinePanel.vue'
import datasetPanel from '@/components/manage/mainFlow/panels/datasetPanel/index.vue'
import operatorPanel from '@/components/manage/mainFlow/panels/operatorPanel.vue'
import pageLoading from '@/components/general/pageLoading.vue'
import currentPipelineBlock from '@/components/manage/mainFlow/tools/currentPipelineBlock.vue'
import execResultPanel from '@/components/manage/mainFlow/panels/execResultPanel/index.vue'
import taskPanel from '@/components/manage/mainFlow/panels/taskPanel.vue'

import databaseIcon from '@/assets/flow/database.svg'
import pipelineIcon from '@/assets/flow/pipeline.svg'
import operatorIcon from '@/assets/flow/operator.svg'
import taskIcon from '@/assets/flow/task.svg'
import saveIcon from '@/assets/flow/save.svg'

import axios from '@/axios/config'

export default {
    name: "dataflowPage",
    components: {
        mainFlow,
        pipeline,
        pipelinePanel,
        datasetPanel,
        operatorPanel,
        pageLoading,
        currentPipelineBlock,
        execResultPanel,
        taskPanel
    },
    data() {
        return {
            flowId: 'df-main-flow',
            value: null,
            options: [
                {
                    name: () => this.local('Dataset'),
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
                    name: () => this.local('Execution'),
                    img: taskIcon,
                    show: () => {
                        return this.relatedTasks.length > 0
                    },
                    func: () => {
                        this.show.taskPanel = true
                    }
                },
                {
                    name: () => this.local('Save'),
                    img: saveIcon,
                    func: () => {
                        this.handleSaveClick()
                    }
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
                // }
            ],

            edges: [],
            sourceDatabase: null,
            currentPipeline: null,
            executionInfo: {
                task_id: null,
                currentStep: null,
                runningResult: null,
            },
            timer: {
                exec: null
            },
            useEdgeSync: new useEdgeSync(),
            show: {
                dataset: false,
                pipeline: false,
                pipelinePanel: false,
                operator: false,
                serving: false,
                execResult: false,
                taskPanel: false
            },
            lock: {
                serving: true,
                running: true,
                loading: true
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
        currentPipeline() {
            this.getTasks()
            this.clearExecution()
        },
        isAutoConnection(val) {
            if (val) {
                this.useEdgeSync.autoConnectAllRunEdges(this.flowId, this.$Guid)
            }
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme', 'color', 'gradient']),
        ...mapState(useDataflow, [
            'isAutoConnection',
            'servingList',
            'currentServing',
            'datasets',
            'groupOperators',
            'tasks',
            'execution'
        ]),
        flatFormatedOperators() {
            let operators = []
            for (let key in this.groupOperators) {
                operators.push(...this.groupOperators[key].items)
            }
            return operators
        },
        isTemplate() {
            if (!this.currentPipeline) return false
            let tags = this.currentPipeline.tags
            if (!Array.isArray(tags)) return false
            return tags.includes('template')
        },
        isAutoConnectionModel: {
            get() {
                return this.isAutoConnection
            },
            set(val) {
                this.switchAutoConnection(val)
            }
        },
        relatedTasks() {
            if (!this.currentPipeline) return []
            let tags = this.currentPipeline.tags
            if (!Array.isArray(tags)) return []
            if (tags.includes('template')) return []
            let result = []
            this.tasks.forEach((item) => {
                if (item.pipeline_id === this.currentPipeline.id) {
                    result.push(item)
                }
            })
            return result
        }
    },
    mounted() {
        this.setViewport()
        this.getServing()
    },
    methods: {
        ...mapActions(useDataflow, [
            'switchAutoConnection',
            'getServingList',
            'getDataManagerList',
            'chooseServing',
            'getPipelines',
            'getTasks',
            'getExecution',
            'clearExecution'
        ]),
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
                let position = { x: 500, y: 160 }
                if (this.sourceDatabase.location) {
                    position.x = this.sourceDatabase.location[0]
                    position.y = this.sourceDatabase.location[1]
                }
                flow.addNodes({
                    id: 'db-node',
                    type: 'database-node',
                    position,
                    data: {
                        flowId: this.flowId,
                        label: this.sourceDatabase.name,
                        ...this.sourceDatabase
                    }
                })
            }
        },
        confirmDataset(dataset, refresh = false) {
            this.sourceDatabase = dataset
            this.show.dataset = false
            if (refresh) this.updateDatabaseNode()
        },
        async getServing() {
            if (!this.lock.serving) return
            this.lock.serving = false
            await this.getServingList()
            await this.getDataManagerList()
            this.lock.serving = true
        },
        showServing($event) {
            $event.preventDefault()
            $event.stopPropagation()
            this.$refs.servingMenu.rightClick($event, document.body)
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
        sortPipeline() {
            let flow = useVueFlow(this.flowId)
            let nodeMap = {}
            flow.nodes.value.forEach((node) => {
                nodeMap[node.id] = {
                    id: node.id,
                    target: [],
                    source: []
                }
            })
            let N_nodes = flow.nodes.value.length
            let edges = flow.edges.value
            edges.forEach((edge) => {
                const { source, target } = edge
                nodeMap[source].target.push(target)
                nodeMap[target].source.push(source)
            })
            let results = []
            let outNodes = Object.values(nodeMap).filter((node) => node.source.length === 0)
            while (outNodes.length > 0) {
                let allTargetNodes = []
                let exists = {}
                for (let node of outNodes) {
                    results.push(node)
                    let targetIds = node.target
                    for (let targetId of targetIds) {
                        let targetNode = nodeMap[targetId]
                        targetNode.source = targetNode.source.filter((item) => item !== node.id)
                        if (!exists[targetNode.id]) {
                            allTargetNodes.push(targetNode)
                            exists[targetNode.id] = 1
                        }
                    }
                }
                outNodes = allTargetNodes.filter((node) => node.source.length === 0)
            }
            console.log(results, N_nodes)
            if (results.length !== N_nodes) {
                this.$barWarning(this.local('Pipeline is not a legal DAG'), {
                    status: 'warning'
                })
                return
            }
            let nodeOperators = []
            results.forEach((node) => {
                if (node.id === 'db-node') return
                let oriNode = flow.findNode(node.id)
                nodeOperators.push({
                    name: oriNode.data.name,
                    params: oriNode.data.operatorParams,
                    location: [oriNode.position.x, oriNode.position.y]
                })
            })
            return nodeOperators
        },
        async handleSaveClick() {
            if (!this.currentPipeline || !this.currentPipeline.id) {
                this.show.pipelinePanel = true
                return false
            }
            let tags = this.currentPipeline.tags
            if (!Array.isArray(tags)) tags = []
            if (tags.includes('template')) {
                this.show.pipelinePanel = true
                return false
            }
            return await this.savePipeline()
        },
        async savePipeline() {
            if (!this.sourceDatabase) {
                this.$barWarning(this.local('Please select a dataset'), {
                    status: 'warning'
                })
                return false
            }
            let cancel = false
            if (this.executionInfo.task_id) {
                await new Promise((resolve) => {
                    this.$infoBox(
                        this.local(
                            'Are you sure to override the pipeline with the execution task?'
                        ),
                        {
                            status: 'warning',
                            confirm: () => {
                                cancel = false
                                resolve()
                            },
                            cancel: () => {
                                cancel = true
                                resolve()
                            }
                        }
                    )
                })
            }
            if (cancel) return false
            let nodeOperators = this.sortPipeline()
            const flow = useVueFlow(this.flowId)
            let dbNode = flow.findNode('db-node')
            await this.$api.pipelines
                .update_pipeline(this.currentPipeline.id, {
                    name: this.currentPipeline.name,
                    config: {
                        file_path: this.currentPipeline.config.file_path,
                        input_dataset: {
                            id: this.sourceDatabase.id,
                            location: [dbNode.position.x, dbNode.position.y]
                        },
                        operators: nodeOperators
                    }
                })
                .then((res) => {
                    if (res.code === 200) {
                        this.getPipelines()
                        this.$barWarning(this.local('Pipeline has been updated'), {
                            status: 'correct'
                        })
                    }
                })
                .catch((err) => {
                    this.$barWarning(this.local('Pipeline update failed'), {
                        status: 'error'
                    })
                })
            return true
        },
        addPipeline(name) {
            if (!this.sourceDatabase) {
                this.$barWarning(this.local('Please select a dataset'), {
                    status: 'warning'
                })
                return
            }
            let nodeOperators = this.sortPipeline()
            const flow = useVueFlow(this.flowId)
            let dbNode = flow.findNode('db-node')
            if (!dbNode) {
                this.$barWarning(this.local('Please select a dataset'), {
                    status: 'warning'
                })
                return
            }
            this.$api.pipelines
                .create_pipeline({
                    name: name,
                    config: {
                        file_path: '',
                        input_dataset: {
                            id: this.sourceDatabase.id,
                            location: [dbNode.position.x, dbNode.position.y]
                        },
                        operators: nodeOperators
                    }
                })
                .then((res) => {
                    if (res.code === 200) {
                        this.getPipelines()
                        if (!this.currentPipeline || !this.currentPipeline.id || this.isTemplate) {
                            this.currentPipeline = res.data
                        }
                        this.$barWarning(this.local('Pipeline has been created'), {
                            status: 'correct'
                        })
                        this.show.pipelinePanel = false
                    }
                })
        },
        async executePipeline() {
            if (!this.currentPipeline || !this.currentPipeline.id) {
                this.$barWarning(this.local('Please select a pipeline'), {
                    status: 'warning'
                })
                return
            }
            await this.$api.tasks
                .execute_pipeline_async(this.currentPipeline.id)
                .then((res) => {
                    if (res.code === 200) {
                        this.executionInfo.task_id = res.data.task_id
                        this.watchExecution()
                        this.$barWarning(this.local('Pipeline has been executed'), {
                            status: 'correct'
                        })
                    }
                })
                .catch((err) => {
                    this.$barWarning(this.local('Pipeline execution failed'), {
                        status: 'error'
                    })
                })
        },
        async handleRunClick() {
            if (!this.lock.running) {
                this.$barWarning(this.local('Please wait for the previous pipeline to finish'), {
                    status: 'warning'
                })
                return
            }
            this.lock.running = false
            let isSaved = await this.handleSaveClick()
            if (!isSaved) {
                this.lock.running = true
                return;
            }
            await this.executePipeline()
        },
        showExecDetails(pipeline_idx) {
            if (!this.executionInfo.task_id) return
            this.executionInfo.currentStep = pipeline_idx - 1
            this.$api.tasks
                .get_task_result(this.executionInfo.task_id, this.executionInfo.currentStep, 15)
                .then((res) => {
                    if (res.code === 200) {
                        this.executionInfo.runningResult = res.data
                        this.show.execResult = true
                    }
                })
        },
        downloadData(pipeline_idx) {
            if (!this.executionInfo.task_id) return
            let baseURL = axios.defaults.baseURL
            let url =
                baseURL +
                `/api/v1/tasks/execution/${this.executionInfo.task_id}/download?step=${pipeline_idx - 1}`
            window.open(url, '_blank')
        },
        selectPipelineCallback() {
            this.clearExecution()
            this.executionInfo.task_id = null
        },
        async selectExecutionPipeline(config) {
            console.log(config)
            if (!this.lock.loading) return
            this.lock.loading = false
            const confirmDatasetCall = (_, dataset) => {
                this.confirmDataset(dataset, true)
            }
            await usePipelineOperation().renderPipeline(
                config,
                this.flowId,
                this.datasets,
                this.flatFormatedOperators,
                this,
                this.$nextTick,
                confirmDatasetCall,
                this.$Guid
            )
            this.lock.loading = true
        },
        async recoverPipeline() {
            if (!this.currentPipeline || !this.currentPipeline.config) {
                return
            }
            this.lock.loading = false
            const confirmDatasetCall = (_, dataset) => {
                this.confirmDataset(dataset, true)
            }
            await usePipelineOperation().renderPipeline(
                this.currentPipeline.config,
                this.flowId,
                this.datasets,
                this.flatFormatedOperators,
                this,
                this.$nextTick,
                confirmDatasetCall,
                this.$Guid
            )
            this.selectPipelineCallback()
            this.lock.loading = true
        },
        async handleWatchExecution({ task_id }) {
            this.executionInfo.task_id = task_id
            await this.getExecution(this.executionInfo.task_id)
            await this.selectExecutionPipeline(this.execution.pipeline_config)
            this.watchExecution()
        },
        watchExecution() {
            if (!this.executionInfo.task_id) return
            clearInterval(this.timer.exec)
            this.timer.exec = setInterval(async () => {
                await this.getExecution(this.executionInfo.task_id)
                this.lock.running = false
                if (this.execution.status === 'completed') {
                    clearInterval(this.timer.exec)
                    this.lock.running = true
                } else if (this.execution.status === "cancelled") {
                    clearInterval(this.timer.exec)
                    this.lock.running = true
                } else if (this.execution.status === 'failed') {
                    clearInterval(this.timer.exec)
                    this.lock.running = true
                    this.$barWarning(
                        this.local(
                            'Pipeline execution failed:' + JSON.stringify(this.execution.output)
                        ),
                        {
                            status: 'error',
                            autoClose: -1
                        }
                    )
                }
            }, 3000)
        },
        stopExecution() {
            if (!this.currentPipeline || !this.currentPipeline.config) return
            if (!this.executionInfo.task_id) return
            if (this.execution.status !== 'running') {
                this.$barWarning(this.local('Pipeline execution not running'), {
                    status: 'warning'
                })
                return
            }
            this.$api.tasks.kill_execution(this.executionInfo.task_id).then((res) => {
                if (res.code === 200) {
                    this.lock.running = true
                    this.$barWarning(this.local('Pipeline execution stopped'), {
                        status: 'correct'
                    })
                }
            })
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
        onConnectStart(params) { },
        onConnectEnd(event) {
            console.log(event)
        },
        resetFlow() {
            this.$infoBox(this.local('Are you sure to reset the flow?'), {
                status: 'error',
                theme: this.theme,
                confirm: () => {
                    const flow = useVueFlow(this.flowId)
                    flow.$reset()
                }
            })
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

    &.dark {
        background: rgba(36, 36, 36, 1);

        .df-flow-container {
            background: rgba(30, 30, 30, 1);
            border: rgba(90, 90, 90, 0.1) solid thin;
        }

        .control-menu-block {
            .command-bar {
                .option-name {
                    color: whitesmoke;
                }
            }
        }
    }

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
            max-width: 800px;
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
