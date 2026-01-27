<template>
    <transition name="pipeline-slide">
        <div v-show="thisValue" class="df-pipeline-container" :class="[{ dark: theme === 'dark' }]">
            <div class="df-pipeline-header">
                <div class="left-block">
                    <fv-img class="logo" :src="img.pipeline" alt="pipeline"></fv-img>
                    <p class="title">Pipeline</p>
                </div>
                <fv-button :theme="theme" border-radius="8" style="width: 35px; height: 35px"
                    @click="thisValue = false">
                    <i class="ms-Icon ms-Icon--ChevronLeft"></i>
                </fv-button>
            </div>
            <div class="df-pipeline-content">
                <fv-pivot :theme="theme" v-model="choosenPivot" class="pivot-panel" :items="pivotItems" :tab="true"
                    :fontSize="12" :background="theme === 'dark' ? 'rgba(40, 40, 40, 1)' : 'rgba(255, 255, 255, 1)'"
                    :sliderBackground="gradient" :borderRadius="8" padding="0px 5px" itemPadding="0px 10px"
                    :sliderBorderRadius="12"></fv-pivot>
                <hr />
                <div class="search-block">
                    <fv-text-box :theme="theme" :placeholder="local('Search Pipelines ...')" icon="Search"
                        class="pipeline-search-box" :revealBorder="true" borderRadius="30" borderWidth="2"
                        :isBoxShadow="true" :focusBorderColor="color" :revealBorderColor="'rgba(103, 105, 251, 0.6)'"
                        :reveal-background-color="[
                            'rgba(103, 105, 251, 0.1)',
                            'rgba(103, 105, 251, 0.6)'
                        ]" @debounce-input="searchText = $event"></fv-text-box>
                    <div v-show="searchText" class="search-result-info">
                        {{ local('Total') }}: {{ totalNumVisible }} {{ local('pipelines') }}
                        <p class="search-text">"{{ searchText }}"</p>
                    </div>
                </div>
                <hr />
                <fv-button :theme="theme" icon="Add"
                    :background="theme === 'dark' ? 'rgba(40, 40, 40, 0.6)' : 'rgba(255, 255, 255, 0.6)'"
                    :foreground="theme === 'dark' ? 'rgba(255, 255, 255, 1)' : 'rgba(90, 90, 90, 1)'" border-radius="8"
                    :is-box-shadow="true" style="width: calc(100% - 20px); height: 40px; margin-left: 10px"
                    @click="(show.add = true), (addPanelMode = 'add')">{{ local('New Pipeline') }}</fv-button>
                <div v-show="!lock.pipeline" class="pipeline-list-loading">
                    <fv-progress-ring loading="true" :r="20" :border-width="3" :color="color"
                        :background="'rgba(245, 245, 245, 1)'"></fv-progress-ring>
                </div>
                <div class="pipeline-list-block" :class="[{ dark: theme === 'dark' }]">
                    <div v-show="item.show" v-for="(item, index) in filteredPipelines" :key="item.id"
                        class="pipeline-item" :class="[{ choosen: thisPipeline && thisPipeline.id === item.id }]"
                        @click="selectPipeline(item)" @contextmenu="showRightMenu($event, item)">
                        <div class="pipeline-item-main">
                            <div class="main-icon" :style="{
                                background:
                                    choosenPivot && choosenPivot.key === 'custom'
                                        ? gradient
                                        : ''
                            }">
                                <i class="ms-Icon" :class="[
                                    `ms-Icon--${choosenPivot && choosenPivot.key === 'custom' ? 'CalendarWeek' : 'DialShape3'}`
                                ]"></i>
                            </div>

                            <div class="content-block">
                                <div class="row-item">
                                    <p class="pipeline-name" :title="item.name">{{ item.name }}</p>
                                    <exec-label :model-value="item"></exec-label>
                                </div>
                                <div class="row-item">
                                    <p class="pipeline-info">
                                        {{ local('Total') }}: {{ item.config.operators.length }}
                                        {{ local('operators') }}
                                    </p>
                                    <time-rounder :model-value="new Date(item.updated_at)" :foreground="color"
                                        style="width: auto"></time-rounder>
                                </div>
                            </div>
                        </div>
                        <hr />
                    </div>
                </div>
            </div>
            <pipeline-panel v-model="show.add" :obj="currentContextItem" :addPanelMode="addPanelMode"></pipeline-panel>
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
import { usePipelineOperation } from '@/hooks/dataflow/usePipelineOperation'

import timeRounder from '@/components/general/timeRounder.vue'
import pipelinePanel from '@/components/manage/mainFlow/panels/piplinePanel.vue'
import execLabel from '@/components/manage/mainFlow/pipeline/execLabel.vue'

import pipelineIcon from '@/assets/flow/pipeline.svg'

export default {
    name: 'pipeline',
    components: {
        timeRounder,
        pipelinePanel,
        execLabel
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
            choosenPivot: null,
            pivotItems: [
                {
                    key: 'template',
                    name: () => this.local('Template')
                },
                {
                    key: 'custom',
                    name: () => this.local('Custom Pipeline')
                }
            ],
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
                this.getOperators(this.language === 'cn' ? 'zh' : 'en')
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
        ...mapState(useAppConfig, ['local', 'language']),
        ...mapState(useDataflow, ['datasets', 'groupOperators', 'pipelines']),
        ...mapState(useTheme, ['theme', 'color', 'gradient']),
        flatFormatedOperators() {
            let operators = []
            for (let key in this.groupOperators) {
                operators.push(...this.groupOperators[key].items)
            }
            return operators
        },
        filteredPipelines() {
            let mode = this.choosenPivot ? this.choosenPivot.key : 'template'
            if (mode === 'template')
                return this.pipelines.filter((item) => item.tags && item.tags.includes('template'))
            else
                return this.pipelines.filter(
                    (item) => !item.tags || !item.tags.includes('template')
                )
        },
        totalNumVisible() {
            return this.filteredPipelines.filter((item) => item.show).length
        }
    },
    mounted() {
        this.getPipelineList()
    },
    methods: {
        ...mapActions(useDataflow, ['getDatasets', 'getOperators', 'getPipelines', 'getTasks']),
        async getPipelineList() {
            if (!this.lock.pipeline) return
            this.lock.pipeline = false
            await this.getPipelines()
            await this.getTasks()
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
            const position = {
                x: data.location.x,
                y: data.location.y + parseInt(5 * Math.random())
            }
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
        async selectPipeline(pipelineItem) {
            console.log(pipelineItem)
            if (!this.thisLoading) return
            this.thisLoading = false
            this.thisPipeline = pipelineItem
            await usePipelineOperation().renderPipeline(
                pipelineItem.config,
                this.flowId,
                this.datasets,
                this.flatFormatedOperators,
                this,
                this.$nextTick,
                this.$emit,
                this.$Guid
            )
            this.thisLoading = true
            this.$emit('select-pipeline', pipelineItem)
        },
        delPipeline(item) {
            if (!item) return
            this.$infoBox(this.local('Are you sure to delete this pipeline?'), {
                status: 'error',
                theme: this.theme,
                confirm: () => {
                    this.$api.pipelines.delete_pipeline(item.id).then((res) => {
                        if (res.code === 200) {
                            if (item.id === this.thisPipeline.id) {
                                this.thisPipeline = null
                            }
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

    &.dark {
        background: rgba(36, 36, 36, 0.3);
        border: rgba(120, 120, 120, 0.1) solid thin;
    }

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
        align-items: center;
        flex-direction: column;

        .pivot-panel {
            width: calc(100% - 20px);
            height: 30px;
            flex-shrink: 0;
        }

        hr {
            width: calc(100% - 20px);
        }

        .search-block {
            position: relative;
            width: 100%;
            height: auto;
            padding: 0px 10px;
            display: flex;
            flex-direction: column;

            .pipeline-search-box {
                width: 100%;
                height: 35px;
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

            &.dark {
                .pipeline-item {


                    &:hover {
                        background: rgba(79, 80, 89, 0.6);

                        .pipeline-item-main {
                            .content-block {
                                .pipeline-name {
                                    color: rgba(115, 186, 241, 1);
                                }
                            }
                        }
                    }

                    &:active {
                        background: rgba(103, 106, 116, 0.8);
                    }

                    &.choosen {
                        background: rgba(149, 152, 172, 0.6);
                    }

                    .pipeline-item-main {

                        .content-block {

                            .pipeline-name {
                                color: rgb(245, 245, 245, 1);
                            }

                            .pipeline-info {
                                color: rgba(200, 200, 200, 1);
                            }
                        }
                    }
                }
            }

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
                        background: linear-gradient(114.95deg,
                                rgba(235, 0, 255, 0.5) 0%,
                                rgba(0, 71, 255, 0) 34.35%),
                            linear-gradient(180deg, #004b5b 0%, #ffa7a7 100%),
                            linear-gradient(244.35deg, #ffb26a 0%, #3676b1 50.58%, #00a3ff 100%),
                            linear-gradient(244.35deg, #ffffff 0%, #004a74 49.48%, #ff0000 100%),
                            radial-gradient(100% 233.99% at 0% 100%, #b70000 0%, #ad00ff 100%),
                            linear-gradient(307.27deg, #1dac92 0.37%, #2800c6 100%),
                            radial-gradient(100% 140% at 100% 0%,
                                #eaff6b 0%,
                                #006c7a 57.29%,
                                #2200aa 100%);
                        background-blend-mode: hard-light, overlay, overlay, overlay, difference,
                            difference, normal;
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
