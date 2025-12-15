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
                    @click="(show.add = true), (addPanelMode = 'add')"
                    >{{ local('New Pipeline') }}</fv-button
                >
                <div v-show="!lock.pipeline" class="pipeline-list-loading">
                    <fv-progress-ring
                        loading="true"
                        :r="20"
                        :border-width="3"
                        :color="color"
                        :background="'rgba(245, 245, 245, 1)'"
                    ></fv-progress-ring>
                </div>
                <div class="pipeline-list-block">
                    <div
                        v-show="item.show"
                        v-for="(item, index) in pipelines"
                        :key="item.id"
                        class="pipeline-item"
                        :class="[{ choosen: thisPipeline === item }]"
                        @click="selectPipeline(item)"
                        @contextmenu="showRightMenu($event, item)"
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
            <pipeline-panel
                v-model="show.add"
                :obj="currentContextItem"
                :addPanelMode="addPanelMode"
            ></pipeline-panel>
            <fv-right-menu v-model="show.rightMenu" ref="rightMenu">
                <span @click="(show.add = true), (addPanelMode = 'add')">
                    <i class="ms-Icon ms-Icon--Add" :style="{ color: color }"></i>
                    <p>{{ local('New Pipeline') }}</p>
                </span>
                <span @click="(show.add = true), (addPanelMode = 'rename')">
                    <i class="ms-Icon ms-Icon--Rename" :style="{ color: color }"></i>
                    <p>{{ local('Rename Pipeline') }}</p>
                </span>
                <hr />
                <span @click="delPipeline(currentContextItem)">
                    <i class="ms-Icon ms-Icon--Delete" :style="{ color: '#c8323b' }"></i>
                    <p>{{ local('Delete Pipeline') }}</p>
                </span>
            </fv-right-menu>
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
import pipelinePanel from '@/components/manage/mainFlow/panels/piplinePanel.vue'

import pipelineIcon from '@/assets/flow/pipeline.svg'

export default {
    name: 'pipeline',
    components: {
        timeRounder,
        pipelinePanel
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
            thisPipeline: null,
            currentContextItem: null,
            addPanelMode: 'add',
            show: {
                add: false,
                rightMenu: false
            },
            img: {
                pipeline: pipelineIcon
            },
            lock: {
                pipeline: true
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
        ...mapState(useDataflow, ['datasets', 'groupOperators', 'pipelines']),
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
        this.getPipelineList()
    },
    methods: {
        ...mapActions(useDataflow, ['getDatasets', 'getOperators', 'getPipelines']),
        async getPipelineList() {
            if (!this.lock.pipeline) return
            this.lock.pipeline = false
            await this.getPipelines()
            this.lock.pipeline = true
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
            await this.$nextTick()
            if (!item.config) return
            this.thisLoading = false
            const { input_dataset, operators } = item.config
            const basicPos = {
                x: 1300,
                y: 160
            }
            let dataset = this.datasets.find((item) => item.id === input_dataset.id)
            if (!dataset) {
                this.thisLoading = true
                this.$barWarning(this.local('Input dataset not found'), {
                    status: 'warning'
                })
            } else {
                dataset = Object.assign({}, dataset)
                dataset.location = input_dataset.location
                this.$emit('confirm-dataset', dataset)
            }
            let formatOperators = []
            let promiseList = []
            // 在这里的设计是为了保险起见还是重新获取所有operator的预定义参数, 然后结合当前pipeline获取的参数进行合并, 然而当前事实上其实还是直接用了当前pipeline获取的参数, 后续若有需求再考虑是否需要修改
            operators.forEach((item, idx) => {
                promiseList.push(
                    this.$api.operators.get_operator_detail_by_name(item.name).then((res) => {
                        if (res.code === 200) {
                            let operator = this.flatFormatedOperators.find(
                                (it) => it.name === item.name
                            )
                            operator = Object.assign({}, operator)
                            operator = Object.assign(operator, res.data)
                            operator.location = item.location
                            operator._cache_parameter = {
                                init: [],
                                run: []
                            }
                            operator._cache_parameter.init = item.params.init
                            operator._cache_parameter.run = item.params.run
                            operator.pipeline_idx = idx + 1
                            formatOperators.push(operator)
                        }
                    })
                )
            })
            await Promise.all(promiseList)
            formatOperators.sort((a, b) => a.pipeline_idx - b.pipeline_idx)
            formatOperators.forEach((item, idx) => {
                if (Array.isArray(item.location)) {
                    item.location = {
                        x: item.location[0],
                        y: item.location[1]
                    }
                }
                if (item.location.x === 0 || item.location.y === 0)
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
        delPipeline(item) {
            if (!item) return
            this.$infoBox(this.local('Are you sure to delete this pipeline?'), {
                status: 'error',
                confirm: () => {
                    this.$api.pipelines.delete_pipeline(item.id).then((res) => {
                        if (res.code === 200) {
                            this.getPipelineList()
                        } else
                            this.$barWarning(res.msg || this.local('Delete pipeline failed'), {
                                status: 'warning'
                            })
                    })
                }
            })
        },
        showRightMenu($event, item) {
            this.currentContextItem = item
            $event.preventDefault()
            $event.stopPropagation()
            this.$refs.rightMenu.rightClick($event, document.body)
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

        .pipeline-list-loading {
            position: absolute;
            top: 150px;
            left: 50%;
            transform: translate(-50%, -50%);
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
</style>
