<template>
    <transition name="pipeline-slide">
        <div class="df-pipeline-container">
            <div class="df-pipeline-header">
                <fv-img class="logo" :src="img.pipeline" alt="pipeline"></fv-img>
                <p class="title">Pipeline</p>
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
                    border-radius="12"
                    :is-box-shadow="true"
                    style="width: calc(100% - 20px); height: 45px; margin-left: 10px"
                    >{{ local('Create Pipeline') }}</fv-button
                >
                <div class="pipeline-list-block"></div>
            </div>
        </div>
    </transition>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'

import pipelineIcon from '@/assets/flow/pipeline.svg'

export default {
    name: 'pipeline',
    data() {
        return {
            searchText: '',
            img: {
                pipeline: pipelineIcon
            }
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['color']),
        totalNumVisible() {
            return 0
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
        gap: 15px;

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

        .pipeline-list-block {
            position: relative;
            width: 100%;
            height: 10px;
            flex: 1;
            margin-top: 5px;
            overflow: overlay;
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
