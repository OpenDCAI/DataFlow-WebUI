<template>
    <div
        class="df-flow-default-node"
        :class="[{ selected: selected }]"
        :style="{
            '--node-background': thisData.background,
            '--node-icon-color': thisData.iconColor,
            '--node-border-color': thisData.borderColor,
            '--node-shadow-color': thisData.shadowColor,
            '--node-group-background': thisData.groupBackground,
            '--node-title-color': thisData.titleColor,
            '--node-status-color': thisData.statusColor,
            '--node-info-title-color': thisData.infoTitleColor,
            '--default-handle-color': thisData.defaultHandleColor,
            '--default-handle-shadow-color': thisData.defaultHandleShadowColor
        }"
    >
        <div class="node-banner">
            <div class="icon-block" :style="{ background: thisData.iconBackground }">
                <i v-if="!thisData.img" class="ms-Icon" :class="[`ms-Icon--${thisData.icon}`]"></i>
                <fv-img v-else class="icon-img" :src="thisData.img"></fv-img>
            </div>
            <div class="content-block">
                <p class="sub-status" :title="thisData.status">{{ thisData.status }}</p>
                <p class="main-title" :title="thisData.label">{{ thisData.label }}</p>
            </div>
            <div class="control-block" @mousedown.stop @click.stop>
                <fv-button
                    v-if="thisData.enableDelete"
                    theme="dark"
                    border-radius="8"
                    :font-size="12"
                    background="rgba(215, 95, 95, 1)"
                    border-color="rgba(255, 255, 255, 0.1)"
                    style="width: 25px; height: 25px"
                    @click="
                        $emit('delete-node', {
                            id: id,
                            data: thisData
                        })
                    "
                >
                    <i class="ms-Icon ms-Icon--Cancel"></i>
                </fv-button>
            </div>
        </div>
        <div class="node-info">
            <p>{{ thisData.nodeInfo }}</p>
        </div>
        <div class="remain-content-block">
            <slot>
                <div class="node-group-item">
                    <div class="node-row-item">
                        <span class="info-title">Selected Info</span>
                        <p class="info-value">{{ selected }}</p>
                    </div>
                    <span class="info-title">Position Info</span>
                    <p class="info-value">{{ x }} {{ y }}</p>
                </div>
            </slot>
        </div>
        <Handle
            v-if="thisData.useTargetHandle"
            :id="`node::target::node`"
            type="target"
            class="handle-item default"
            :position="Position.Left"
            :style="{
                top: thisData.defaultTargetTop
            }"
        />
        <Handle
            v-if="thisData.useSourceHandle"
            :id="`node::source::node`"
            type="source"
            class="handle-item default"
            :position="Position.Right"
            :style="{
                top: thisData.defaultSourceHandleTop
            }"
            Handle
        />
    </div>
</template>

<script setup>
import { computed } from 'vue'
import { Position, Handle } from '@vue-flow/core'

const props = defineProps({
    id: {
        type: String,
        required: true
    },
    position: {
        type: Object,
        required: true
    },
    selected: {
        type: Boolean,
        default: false
    },
    data: {
        type: Object,
        default: () => ({})
    }
})

const defaultData = {
    label: 'Node',
    status: 'Status',
    nodeInfo: '',
    icon: 'EndPoint',
    iconColor: '',
    iconBackground: '',
    background: '',
    titleColor: '',
    statusColor: '',
    infoTitleColor: '',
    borderColor: '',
    shadowColor: '',
    defaultHandleColor: '',
    defaultHandleShadowColor: '',
    groupBackground: '',
    enableDelete: true,
    defaultSourceHandleTop: '',
    defaultTargetHandleTop: '',
    useSourceHandle: true,
    useTargetHandle: true
}
const thisData = computed(() => {
    return {
        ...defaultData,
        ...props.data
    }
})
const x = computed(() => `${Math.round(props.position.x)}px`)
const y = computed(() => `${Math.round(props.position.y)}px`)
</script>

<style lang="scss">
.df-flow-default-node {
    --node-background: rgba(252, 252, 252, 0.8);
    --node-title-color: rgba(100, 108, 126, 1);
    --node-status-color: rgba(168, 170, 176, 1);
    --node-info-title-color: rgba(168, 170, 176, 1);
    --node-shadow-color: rgba(122, 124, 206, 0.3);
    --node-border-color: rgba(163, 164, 236, 1);
    --node-icon-color: rgba(100, 108, 126, 1);
    --node-group-background: rgba(245, 245, 245, 0.8);
    --default-handle-color: rgba(163, 164, 236, 1);
    --default-handle-shadow-color: rgba(122, 124, 206, 0.3);

    position: relative;
    width: 250px;
    padding: 5px 0px;
    background: var(--node-background);
    border: 1px solid rgba(120, 120, 120, 0.1);
    border-radius: 8px;
    outline: 1.5px solid transparent;
    display: flex;
    flex-direction: column;
    transition:
        box-shadow 0.2s ease-in-out,
        outline 0.2s ease-in-out;
    backdrop-filter: blur(6px);
    -webkit-backdrop-filter: blur(6px);
    box-shadow:
        0px 0px 1px var(--node-shadow-color),
        3px 6px 16px transparent,
        -3px 6px 16px transparent;

    &:hover {
        box-shadow:
            0px 0px 1px var(--node-shadow-color),
            3px 6px 16px var(--node-shadow-color),
            -3px 6px 16px var(--node-shadow-color);
    }

    &:active {
        box-shadow:
            0px 0px 1px var(--node-shadow-color),
            2px 3px 8px var(--node-shadow-color),
            -2px 3px 8px var(--node-shadow-color);
    }

    &.selected {
        outline: 1.5px solid var(--node-border-color);
    }

    .node-banner {
        position: relative;
        width: calc(100% - 20px);
        height: auto;
        margin-left: 10px;
        display: flex;
        flex-direction: row;

        .icon-block {
            position: relative;
            width: 35px;
            height: 35px;
            background: rgba(253, 253, 253, 1);
            border: 1px solid rgba(120, 120, 120, 0.1);
            border-radius: 8px;
            color: var(--node-icon-color);
            display: flex;
            flex-direction: row;
            justify-content: center;
            align-items: center;
            box-shadow: 0px 1px 2px rgba(0, 0, 0, 0.1);

            &:hover {
                background: rgba(255, 255, 255, 1);
            }

            &:active {
                background: rgba(252, 252, 252, 1);
            }

            .icon-img {
                width: auto;
                height: 20px;
            }
        }

        .content-block {
            position: relative;
            width: calc(100% - 80px);
            height: 40px;
            flex: 1;
            padding-left: 5px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;

            .main-title {
                position: relative;
                width: 100%;
                height: auto;
                font-size: 13.8px;
                font-weight: 600;
                color: var(--node-title-color);
                text-overflow: ellipsis;
                white-space: nowrap;
                overflow: hidden;
            }

            .sub-status {
                position: relative;
                width: 100%;
                height: auto;
                font-size: 10px;
                font-weight: 400;
                color: var(--node-status-color);
                text-overflow: ellipsis;
                white-space: nowrap;
                overflow: hidden;
            }
        }

        .control-block {
            position: relative;
            width: auto;
            height: 40px;
            padding: 0px;
            display: flex;
            flex-direction: row;
            justify-content: center;
            align-items: center;
        }
    }

    .node-info {
        position: relative;
        width: calc(100% - 20px);
        height: auto;
        margin-top: 5px;
        margin-left: 10px;
        font-size: 8px;
        font-weight: 400;
        color: var(--node-status-color);
    }

    .remain-content-block {
        position: relative;
        width: 100%;
        height: auto;
        margin-top: 5px;
        display: flex;
        flex-direction: column;

        .node-group-item {
            position: relative;
            width: calc(100% - 20px);
            height: auto;
            margin-left: 10px;
            margin-bottom: 5px;
            padding: 5px;
            background: var(--node-group-background);
            font-weight: 400;
            border-radius: 6px;
            line-height: 1.5;

            .node-row-item {
                width: 100%;
                margin-left: 0px;
                padding: 0px;
            }
        }

        .node-row-item {
            position: relative;
            width: 100%;
            height: auto;
            padding: 5px 15px;
            display: flex;
            justify-content: space-between;

            &.col {
                gap: 5px;
                flex-direction: column;
                justify-content: flex-start;
                align-items: flex-start;
            }

            .info-value {
                margin-left: 5px;
                text-overflow: ellipsis;
                text-align: right;
            }
        }

        hr {
            width: calc(100% - 20px);
            margin-left: 10px;
            border: 0px;
            border-top: 1px solid rgba(120, 120, 120, 0.1);
        }

        .info-title {
            font-size: 8px;
            font-weight: 600;
            color: var(--node-info-title-color);
            display: flex;
            align-items: center;
        }

        .info-value {
            flex: 1;
            font-size: 12px;
            font-weight: 400;
            color: var(--node-title-color);
            overflow: hidden;

            &.tiny {
                font-size: 10px;
            }
        }
    }

    .handle-item {
        width: 15px;
        height: 15px;
        background: var(--node-border-color);
        outline: 3px solid transparent;
        border: rgba(250, 250, 250, 1) solid 3px;
        transition: all 0.2s ease-in-out;

        &:hover {
            width: 18px;
            height: 18px;
            outline: 3px solid var(--node-shadow-color);
        }

        &.default {
            background: var(--default-handle-color);

            &:hover {
                outline: 3px solid var(--default-handle-shadow-color);
            }
        }

        &.title {
            &:hover {
                &::before {
                    content: attr(data-title);
                    position: absolute;
                    top: 50%;
                    left: 0;
                    width: auto;
                    height: auto;
                    padding: 5px;
                    font-size: 12px;
                    background: rgba(250, 250, 250, 1);
                    border: 1px solid rgba(120, 120, 120, 0.1);
                    border-radius: 6px;
                    white-space: nowrap;
                    transform: translate(calc(-100% - 10px), -50%);
                }
            }
        }

        &:active {
            width: 16px;
            height: 16px;
        }
    }
}
</style>
