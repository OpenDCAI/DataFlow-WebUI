<template>
    <transition name="pipeline-slide">
        <div v-show="thisValue" class="df-pipeline-container">
            <div class="df-pipeline-header">
                <div class="left-block">
                    <fv-img class="logo" :src="img.pipeline" alt="pipeline"></fv-img>
                    <p class="title">Pipeline</p>
                </div>
                <fv-button
                    border-radius="8"
                    style="width: 35px; height: 35px"
                    @click="thisValue = false"
                >
                    <i class="ms-Icon ms-Icon--ChevronLeft"></i>
                </fv-button>
            </div>
            <div class="df-pipeline-content">
                <hr />
                <div class="search-block">
                    <fv-text-box
                        :placeholder="local('Search Pipelines ...')"
                        icon="Search"
                        class="pipeline-search-box"
                        :revealBorder="true"
                        borderRadius="30"
                        borderWidth="2"
                        :isBoxShadow="true"
                        :focusBorderColor="color"
                        :revealBorderColor="'rgba(103, 105, 251, 0.6)'"
                        :reveal-background-color="[
                            'rgba(103, 105, 251, 0.1)',
                            'rgba(103, 105, 251, 0.6)'
                        ]"
                        @debounce-input="searchText = $event"
                    ></fv-text-box>
                    <div v-show="searchText" class="search-result-info">
                        {{ local('Total') }}: {{ totalNumVisible }} {{ local('pipelines') }}
                        <p class="search-text">"{{ searchText }}"</p>
                    </div>
                </div>
                <hr />
                <fv-button
                    icon="Add"
                    border-radius="8"
                    :is-box-shadow="true"
                    style="width: calc(100% - 20px); height: 40px; margin-left: 10px"
                    @click="show.add ^= true"
                    >{{ local('Create Pipeline') }}</fv-button
                >
                <transition name="add-fold-down">
                    <div v-show="show.add" class="pipeline-new-item">
                        <div class="pipeline-item-main">
                            <div class="main-icon">
                                <i class="ms-Icon ms-Icon--DialShape3"></i>
                            </div>

                            <div class="content-block">
                                <fv-text-box
                                    v-model="addName"
                                    :placeholder="local('Input the new pipeline name')"
                                    border-radius="6"
                                    underline
                                    border-width="2"
                                    :focus-border-color="color"
                                    :is-box-shadow="true"
                                    style="width: 100%; height: 40px"
                                ></fv-text-box>
                            </div>
                        </div>
                        <fv-button
                            theme="dark"
                            :background="'linear-gradient(130deg, rgba(229, 123, 67, 1), rgba(252, 98, 32, 1))'"
                            border-radius="12"
                            :disabled="!addName"
                            :is-box-shadow="true"
                            style="width: calc(100% - 20px); height: 40px; margin-left: 10px"
                            @click="addPipeline"
                            >{{ local('Confirm') }}</fv-button
                        >
                    </div>
                </transition>
                <div class="pipeline-list-block">
                    <div
                        v-show="item.show"
                        v-for="(item, index) in pipelines"
                        :key="item.id"
                        class="pipeline-item"
                        :class="[{ choosen: thisPipeline === item }]"
                        @click="selectPipeline(item)"
                    >
                        <div class="pipeline-item-main">
                            <div class="main-icon">
                                <i class="ms-Icon ms-Icon--DialShape3"></i>
                            </div>

                            <div class="content-block">
                                <p class="pipeline-name" :title="item.name">{{ item.name }}</p>
                                <div class="row-item">
                                    <p class="pipeline-info">
                                        {{ local('Total') }}: {{ item.config.operators.length }}
                                        {{ local('operators') }}
                                    </p>
                                    <time-rounder
                                        :model-value="new Date(item.updated_at)"
                                        :foreground="color"
                                        style="width: auto"
                                    ></time-rounder>
                                </div>
                            </div>
                        </div>
                        <hr />
                    </div>
                </div>
            </div>
        </div>
    </transition>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'
import { useVueFlow } from '@vue-flow/core'
import { useTheme } from '@/stores/theme'

import timeRounder from '@/components/general/timeRounder.vue'

import pipelineIcon from '@/assets/flow/pipeline.svg'

export default {
    name: 'pipeline',
    components: {
        timeRounder
    },
    props: {
        modelValue: {
            default: false
        },
        flowId: {
            default: ''
        },
        pipeline: {
            default: null
        },
        loading: {
            default: false
        }
    },
    data() {
        return {
            thisValue: this.modelValue,
            thisLoading: this.loading,
            searchText: '',
            addName: '',
            thisPipeline: null,
            pipelines: [],
            show: {
                add: false
            },
            img: {
                pipeline: pipelineIcon
            }
        }
    },
    watch: {
        modelValue(newValue) {
            this.thisValue = newValue
            if (newValue) {
                this.getDatasets()
                this.getOperators()
            }
        },
        thisValue(newValue) {
            this.$emit('update:modelValue', newValue)
        },
        loading(newValue) {
            this.thisLoading = newValue
        },
        thisLoading(newValue) {
            this.$emit('update:loading', newValue)
        },
        pipeline(newValue) {
            this.thisPipeline = newValue
        },
        thisPipeline() {
            this.$emit('update:pipeline', this.thisPipeline)
        },
        searchText() {
            this.filterValues()
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useDataflow, ['datasets', 'groupOperators']),
        ...mapState(useTheme, ['color', 'gradient']),
        flatFormatedOperators() {
            let operators = []
            for (let key in this.groupOperators) {
                operators.push(...this.groupOperators[key].items)
            }
            return operators
        },
        totalNumVisible() {
            return this.pipelines.filter((item) => item.show).length
        }
    },
    mounted() {
        this.getPipelines()
    },
    methods: {
        ...mapActions(useDataflow, ['getDatasets', 'getOperators']),
        getPipelines() {
            this.$api.pipelines.list_pipelines().then((res) => {
                if (res.code === 200) {
                    let pipelines = res.data
                    pipelines.forEach((item) => {
                        item.show = true
                    })
                    pipelines.sort((a, b) => {
                        return new Date(b.updated_at) - new Date(a.updated_at)
                    })
                    this.pipelines = pipelines
                }
            })
        },
        filterValues() {
            this.pipelines.forEach((item) => {
                item.show = this.isSearchShowItem(item)
            })
        },
        isSearchShowItem(item) {
            let searchText = this.searchText.toLowerCase()
            return item.name.toLowerCase().includes(searchText)
        },
        addPipelineNode(data) {
            data.enableDelete = true
            const flow = useVueFlow(this.flowId)
            const { screenToFlowCoordinate } = useVueFlow(this.flowId)
            const position = screenToFlowCoordinate({
                x: data.location.x,
                y: data.location.y + parseInt(5 * Math.random())
            })
            const newNode = {
                id: data.nodeId,
                type: 'operator-node',
                position: position,
                data: {
                    flowId: this.flowId,
                    ...data
                }
            }
            flow.addNodes(newNode)
        },
        async selectPipeline(item) {
            console.log(item)
            if (!this.thisLoading) return
            this.thisPipeline = item
            const flow = useVueFlow(this.flowId)
            flow.$reset()
            flow.setViewport({
                x: 0,
                y: 0,
                zoom: 1
            })
            if (!item.config) return
            this.thisLoading = false
            const { input_dataset, operators } = item.config
            const basicPos = {
                x: 1300,
                y: 160
            }
            let dataset = this.datasets.find((item) => item.id === input_dataset)
            if (!dataset) {
                this.thisLoading = true
                this.$barWarning(this.local('Input dataset not found'), {
                    status: 'warning'
                })
                return
            }
            this.$emit('confirm-dataset', dataset)
            let formatOperators = []
            let promiseList = []
            operators.forEach((item, idx) => {
                promiseList.push(
                    this.$api.operators.get_operator_detail_by_name(item.name).then((res) => {
                        if (res.code === 200) {
                            let operator = this.flatFormatedOperators.find(
                                (it) => it.name === item.name
                            )
                            operator = Object.assign(operator, res.data)
                            operator.location = item.location
                            operator.parameter.init = item.params.init
                            operator.parameter.run = item.params.run
                            operator.pipeline_idx = idx + 1
                            formatOperators.push(operator)
                        }
                    })
                )
            })
            await Promise.all(promiseList)
            formatOperators.sort((a, b) => a.pipeline_idx - b.pipeline_idx)
            formatOperators.forEach((item, idx) => {
                if (item.location[0] === 0 || item.location[1] === 0)
                    item.location = {
                        x: idx === 0 ? basicPos.x : formatOperators[idx - 1].location.x + 350,
                        y: basicPos.y
                    }
                item.nodeId = this.$Guid()
                this.addPipelineNode(item)
            })
            let existsDatasetNode = flow.findNode('db-node')
            formatOperators.forEach((item, idx) => {
                if (idx === 0 && !existsDatasetNode) return
                let last_id = idx === 0 ? 'db-node' : formatOperators[idx - 1].nodeId
                flow.addEdges({
                    id: this.$Guid(),
                    type: 'base-edge',
                    source: last_id,
                    target: item.nodeId,
                    sourceHandle: 'node::source::node',
                    targetHandle: 'node::target::node',
                    animated: false,
                    data: {
                        label: 'Node',
                        edgeType: 'node'
                    }
                })
            })
            this.thisLoading = true
        },
        addPipeline() {
            this.$api.pipelines
                .create_pipeline({
                    name: this.addName,
                    config: {
                        file_path: '',
                        input_dataset: ''
                    }
                })
                .then((res) => {
                    if (res.code === 200) {
                        this.$barWarning(this.local('Add pipeline success'))
                        this.show.add = false
                        this.addName = ''
                        this.getPipelines()
                    }
                })
        }
    }
}
</script>

<style lang="scss">
.df-pipeline-container {
    position: relative;
    width: 100%;
    height: 100%;
    background: rgba(250, 250, 250, 0.3);
    border: rgba(120, 120, 120, 0.1) solid thin;
    display: flex;
    flex-direction: column;
    backdrop-filter: blur(10px);

    hr {
        margin: 10px 0px;
        border: none;
        border-top: rgba(120, 120, 120, 0.1) solid thin;
    }

    .df-pipeline-header {
        position: relative;
        width: 100%;
        height: 50px;
        margin-top: 20px;
        padding: 15px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 15px;

        .left-block {
            @include Vcenter;
        }

        .title {
            @include color-dataflow-title;

            font-size: 18px;
            font-weight: bold;
            user-select: none;
        }

        .logo {
            width: 25px;
            height: 25px;
        }
    }

    .df-pipeline-content {
        position: relative;
        width: 100%;
        height: 10px;
        flex: 1;
        display: flex;
        flex-direction: column;

        .search-block {
            position: relative;
            width: 100%;
            height: auto;
            padding: 0px 10px;
            display: flex;
            flex-direction: column;

            .pipeline-search-box {
                width: 100%;
                height: 40px;
            }

            .search-result-info {
                @include Vcenter;

                height: 35px;
                margin-top: 5px;
                padding: 0px 10px;
                background: rgba(239, 239, 239, 1);
                border-radius: 8px;
                font-size: 12px;
                font-weight: 400;
                color: var(--node-status-color);

                .search-text {
                    margin-left: 5px;
                    font-size: 12px;
                    font-weight: 400;
                    color: rgba(0, 90, 158, 1);
                }
            }
        }

        .pipeline-new-item {
            position: relative;
            width: calc(100% - 20px);
            height: 120px;
            flex-shrink: 0;
            margin-left: 10px;
            margin-top: 5px;
            padding: 10px;
            background: rgba(255, 255, 255, 0.6);
            border: rgba(120, 120, 120, 0.1) solid thin;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            transition: background 0.3s;

            .pipeline-item-main {
                position: relative;
                width: 100%;
                flex: 1;
                display: flex;
                align-items: center;

                .main-icon {
                    @include HcenterVcenter;

                    position: relative;
                    width: 40px;
                    height: 40px;
                    flex-shrink: 0;
                    background: linear-gradient(
                        90deg,
                        rgba(73, 131, 251, 1) 0%,
                        rgba(100, 161, 252, 1) 100%
                    );
                    border: 1px solid rgba(120, 120, 120, 0.1);
                    border-radius: 8px;
                    color: whitesmoke;
                    box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1);
                }

                .content-block {
                    @include HstartC;

                    position: relative;
                    width: 50px;
                    flex: 1;
                    height: 100%;
                    padding: 10px;
                    line-height: 2;
                    user-select: none;
                }
            }
        }

        .pipeline-list-block {
            position: relative;
            width: 100%;
            height: 10px;
            flex: 1;
            margin-top: 5px;
            overflow: overlay;

            .pipeline-item {
                position: relative;
                width: 100%;
                height: 80px;
                padding: 0px 10px;
                display: flex;
                flex-direction: column;
                transition: background 0.3s;

                &:hover {
                    background: rgba(227, 231, 251, 0.6);
                    .pipeline-item-main {
                        .content-block {
                            .pipeline-name {
                                color: rgba(0, 90, 158, 1);
                            }
                        }
                    }
                }

                &:active {
                    background: rgba(227, 231, 251, 0.8);
                }

                &.choosen {
                    background: rgba(227, 231, 251, 1);
                }

                .pipeline-item-main {
                    position: relative;
                    width: 100%;
                    flex: 1;
                    display: flex;
                    align-items: center;

                    .main-icon {
                        @include HcenterVcenter;

                        position: relative;
                        width: 40px;
                        height: 40px;
                        flex-shrink: 0;
                        background: linear-gradient(
                            90deg,
                            rgba(73, 131, 251, 1) 0%,
                            rgba(100, 161, 252, 1) 100%
                        );
                        border: 1px solid rgba(120, 120, 120, 0.1);
                        border-radius: 8px;
                        color: whitesmoke;
                        box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1);
                    }

                    .content-block {
                        @include HstartC;

                        position: relative;
                        width: 50px;
                        flex: 1;
                        height: 100%;
                        padding: 10px;
                        line-height: 2;
                        user-select: none;

                        .row-item {
                            @include HbetweenVcenter;

                            position: relative;
                            width: 100%;
                        }

                        .pipeline-name {
                            @include nowrap;

                            position: relative;
                            width: 100%;
                            font-size: 12.8px;
                            font-weight: bold;
                            color: rgba(58, 61, 79, 1);
                            transition: color 0.3s;
                        }

                        .pipeline-info {
                            font-size: 10px;
                            color: rgba(120, 120, 120, 1);
                        }
                    }
                }

                hr {
                    margin-top: 5px;
                }
            }
        }
    }
}
.pipeline-slide-enter-active {
    transition: all 0.6s ease-out;
}
.pipeline-slide-leave-active {
    transition: all 0.3s;
}

.pipeline-slide-enter-from,
.pipeline-slide-leave-to {
    width: 0px;
    max-width: 0px;
}

.pipeline-slide-enter-to,
.pipeline-slide-leave-from {
    width: 100%;
    max-width: 100%;
}

.add-fold-down-enter-active,
.add-fold-down-leave-active {
    transition: all 0.3s ease;
    overflow: hidden;
}

.add-fold-down-enter-from,
.add-fold-down-leave-to {
    height: 0px;
    max-height: 0px;
}

.add-fold-down-enter-to,
.add-fold-down-leave-from {
    height: 120px;
    max-height: 120px;
}
</style>
