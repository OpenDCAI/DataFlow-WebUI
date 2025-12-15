<template>
    <basePanel
        v-model="thisValue"
        :title="computedTitle"
        width="350px"
        height="300px"
        theme="light"
        :teleport="true"
    >
        <template v-slot:content>
            <div class="panel-pipeline-content-block">
                <div class="pipeline-item-main">
                    <div class="main-icon">
                        <i class="ms-Icon ms-Icon--DialShape3"></i>
                    </div>

                    <div class="content-block">
                        <fv-text-box
                            v-model="addName"
                            :placeholder="local('Input the pipeline name')"
                            border-radius="6"
                            underline
                            border-width="2"
                            :focus-border-color="color"
                            :is-box-shadow="true"
                            ref="addName"
                            style="width: 100%; height: 40px"
                        ></fv-text-box>
                    </div>
                </div>
            </div>
        </template>
        <template v-slot:control="{ close }">
            <fv-button
                theme="dark"
                :background="'linear-gradient(130deg, rgba(229, 123, 67, 1), rgba(252, 98, 32, 1))'"
                :border-radius="8"
                :disabled="!addName"
                :is-box-shadow="true"
                style="width: 120px; margin-right: 10px"
                @click="handleConfirm"
                >{{ local('Confirm') }}</fv-button
            >
            <fv-button
                :borderRadius="8"
                :isBoxShadow="true"
                style="width: 120px; margin-right: 8px"
                @click="close"
                >{{ local('Close') }}</fv-button
            >
        </template>
    </basePanel>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'
import { useTheme } from '@/stores/theme'

import basePanel from '@/components/general/basePanel.vue'

export default {
    components: {
        basePanel
    },
    props: {
        modelValue: {
            default: false
        },
        title: {
            default: 'New Pipeline'
        },
        obj: {
            default: () => ({})
        },
        addPanelMode: {
            default: 'add'
        }
    },
    data() {
        return {
            thisValue: this.modelValue,
            addName: ''
        }
    },
    watch: {
        modelValue(val) {
            this.thisValue = val
        },
        thisValue(val) {
            this.$emit('update:modelValue', val)
        },
        addPanelMode() {
            this.refreshName()
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['color', 'gradient']),
        computedTitle() {
            return this.addPanelMode === 'add'
                ? this.local('New Pipeline')
                : this.local('Rename Pipeline')
        }
    },
    mounted() {
        this.refreshName()
    },
    methods: {
        ...mapActions(useDataflow, ['getPipelines']),
        refreshName() {
            if (this.addPanelMode === 'add') {
                this.addName = ''
            } else {
                this.addName = this.obj.name
            }
            this.$nextTick(() => {
                this.$refs.addName.focus()
            })
        },
        handleConfirm() {
            if (this.addPanelMode === 'add') {
                this.addPipeline()
            } else if (this.addPanelMode === 'rename') {
                this.renamePipeline()
            } else if (this.addPanelMode === 'custom') {
                this.$emit('confirm', this.addName)
            }
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
                        this.thisValue = false
                        this.addName = ''
                        this.getPipelines()
                    }
                })
        },
        renamePipeline() {
            if (!this.obj.id) return
            console.log(this.obj)
            this.$api.pipelines
                .update_pipeline(this.obj.id, {
                    name: this.addName
                })
                .then((res) => {
                    if (res.code === 200) {
                        this.$barWarning(this.local('Rename pipeline success'))
                        this.thisValue = false
                        this.addName = ''
                        this.getPipelines()
                    }
                })
        }
    }
}
</script>

<style lang="scss">
.panel-pipeline-content-block {
    position: relative;
    width: 100%;
    height: 100%;
    gap: 5px;
    display: flex;
    flex-direction: column;
    overflow: overlay;

    .pipeline-item-main {
        position: relative;
        width: 100%;
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
</style>
