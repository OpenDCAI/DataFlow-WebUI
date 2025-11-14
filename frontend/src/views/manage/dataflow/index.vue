<template>
    <div class="df-default-container">
        <div class="df-flow-container">
            <mainFlow
                :id="flowId"
                v-model:nodes="nodes"
                v-model:edges="edges"
                @switch-database="show.dataset = true"
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
                    </template>
                    <template v-slot:right-space>
                        <div class="command-bar-right-space">
                            <fv-button
                                theme="dark"
                                icon="Play"
                                background="rgba(97, 112, 211, 0.6)"
                                foreground="rgba(255, 255, 255, 1)"
                                border-color="whitesmoke"
                                border-radius="30"
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
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useVueFlow } from '@vue-flow/core'

import mainFlow from '@/components/manage/mainFlow/index.vue'
import datasetPanel from '@/components/manage/mainFlow/panels/datasetPanel.vue'

import databaseIcon from '@/assets/flow/database.svg'
import pipelineIcon from '@/assets/flow/pipeline.svg'
import saveIcon from '@/assets/flow/save.svg'

export default {
    components: {
        mainFlow,
        datasetPanel
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
                    img: pipelineIcon
                },
                {
                    name: () => this.local('Save'),
                    img: saveIcon
                }
            ],
            nodes: [
                {
                    id: '1',
                    type: 'base-node',
                    position: { x: 70, y: 160 },
                    data: {
                        label: 'Node 1',
                        nodeInfo:
                            'Node Info: This is node info block for displaying node information.',
                        iconColor: 'rgba(0, 108, 126, 1)'
                    }
                },

                {
                    id: '2',
                    type: 'base-node',
                    position: { x: 100, y: 400 },
                    data: {
                        label: 'Node 2',
                        nodeInfo:
                            'Node Info: This is node info block for displaying node information.',
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
            ],

            edges: [
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
            ],
            sourceDatabase: null,
            show: {
                dataset: false
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
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local'])
    },
    methods: {
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
                        label: this.sourceDatabase.name,
                        ...this.sourceDatabase
                    }
                })
            }
        },
        confirmDataset(dataset) {
            this.sourceDatabase = dataset
            this.show.dataset = false
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

    .df-flow-container {
        position: relative;
        width: 100%;
        height: 100%;
        background: rgba(250, 250, 250, 1);
        border: rgba(120, 120, 120, 0.1) solid thin;
        border-radius: 15px;
        box-shadow: inset 0px 0px 10px rgba(0, 0, 0, 0.1);
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

            .option-img {
                width: auto;
                height: 15px;
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
</style>
