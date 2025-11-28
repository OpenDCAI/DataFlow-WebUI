<template>
    <div class="df-serving-container">
        <div class="major-container">
            <div class="title-block">
                <p class="main-title">{{ local('Serving') }}</p>
            </div>
            <div class="content-block">
                <fv-Collapse
                    v-model="show.add"
                    class="serving-item"
                    icon="Marquee"
                    :title="local('Add Serving')"
                    :content="local('Add new serving information.')"
                    :disabled-collapse="true"
                    :max-height="'auto'"
                >
                    <template v-slot:extension>
                        <fv-button
                            v-show="show.add"
                            theme="dark"
                            :is-box-shadow="true"
                            :background="gradient"
                            :disabled="!checkAdd()"
                            border-radius="6"
                            style="width: 90px; margin-right: 5px"
                        >
                            {{ local('Confirm') }}
                        </fv-button>
                        <fv-button
                            :theme="show.add ? 'light' : 'dark'"
                            :is-box-shadow="true"
                            :background="show.add ? '' : gradient"
                            border-radius="6"
                            style="width: 90px"
                            @click="handleAdd"
                        >
                            {{ show.add ? local('Cancel') : local('Add') }}
                        </fv-button>
                    </template>
                    <template v-slot:default>
                        <div class="serving-item-row column">
                            <p class="serving-item-light-title">{{ local('Serving Name') }}</p>
                            <fv-text-box
                                v-model="servingName"
                                :placeholder="local('Serving Name')"
                                border-radius="6"
                                :reveal-border="true"
                                :is-box-shadow="true"
                            ></fv-text-box>
                        </div>
                        <hr />
                        <hr />
                        <div class="serving-item-row column">
                            <p class="serving-item-light-title">{{ local('Select CLS Name') }}</p>
                            <fv-combobox
                                v-model="choosenClsItem"
                                :options="createProps"
                                :placeholder="local('Select CLS Name')"
                                :border-radius="6"
                                :input-background="'rgba(252, 252, 252, 1)'"
                            ></fv-combobox>
                        </div>
                        <hr />
                        <div
                            v-if="choosenClsItem && choosenClsItem.params"
                            v-for="(param, p_index) in choosenClsItem.params"
                        >
                            <div class="serving-item-row column">
                                <p class="serving-item-light-title">{{ param.name }}</p>
                                <fv-text-box
                                    v-model="param.value"
                                    :placeholder="local(param.name)"
                                    border-radius="6"
                                    :reveal-border="true"
                                    :is-box-shadow="true"
                                ></fv-text-box>
                            </div>
                            <hr />
                        </div>
                    </template>
                </fv-Collapse>
                <fv-Collapse
                    v-for="(item, index) in servingList"
                    :key="index"
                    class="serving-item"
                    icon="Cloud"
                    :title="item.name"
                    :content="item.cls_name"
                    :max-height="670"
                >
                    <template v-slot:default>
                        <hr />
                        <div class="serving-item-row sep">
                            <div class="serving-item-row column no-pad" style="flex: 1">
                                <p class="serving-item-light-title">{{ local('ID') }}</p>
                                <p class="serving-item-std-info">{{ item.id }}</p>
                            </div>
                            <fv-button
                                v-show="item.edit"
                                theme="dark"
                                :is-box-shadow="true"
                                :background="gradient"
                                border-radius="6"
                                :disabled="!checkEdit(item)"
                                style="width: 90px; margin-right: 5px"
                            >
                                {{ local('Confirm') }}
                            </fv-button>
                            <fv-button
                                :icon="item.edit ? 'Cancel' : 'Edit'"
                                :is-box-shadow="true"
                                border-radius="6"
                                style="width: 90px"
                                @click="handleEdit(item)"
                            >
                                {{ item.edit ? local('Cancel') : local('Edit') }}
                            </fv-button>
                        </div>
                        <hr />
                        <div class="serving-item-row column">
                            <p class="serving-item-light-title">{{ local('Serving Name') }}</p>
                            <fv-text-box
                                v-model="item.serving_name"
                                border-radius="6"
                                :disabled="!item.edit"
                                :reveal-border="true"
                                :is-box-shadow="item.edit"
                            ></fv-text-box>
                        </div>
                        <hr />
                        <div v-for="(param, p_index) in item.params">
                            <div class="serving-item-row column">
                                <p class="serving-item-light-title">{{ param.name }}</p>
                                <fv-text-box
                                    v-model="param.value"
                                    border-radius="6"
                                    :disabled="!item.edit"
                                    :reveal-border="true"
                                    :is-box-shadow="item.edit"
                                ></fv-text-box>
                            </div>
                            <hr />
                        </div>
                    </template>
                </fv-Collapse>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'

export default {
    data() {
        return {
            createProps: [],
            choosenClsItem: {},
            servingName: '',
            servingList: [],
            show: {
                add: false
            }
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme', 'color', 'gradient'])
    },
    mounted() {
        this.getCreateProps()
        this.getServingList()
    },
    methods: {
        getCreateProps() {
            this.$api.serving.list_serving_classes().then((res) => {
                if (res.data) {
                    let createProps = res.data
                    createProps.forEach((item) => {
                        item.key = item.cls_name
                        item.text = item.cls_name
                        for (let param of item.params) {
                            param.value = param.default.toString()
                        }
                    })
                    this.createProps = createProps
                }
            })
        },
        getServingList() {
            this.$api.serving.list_serving_instances_api_v1_serving__get().then((res) => {
                if (res.data) {
                    let servingList = res.data
                    servingList.forEach((item) => {
                        this.resetEditParams(item)
                    })
                    this.servingList = servingList
                }
            })
        },
        resetAddParams() {
            if (this.choosenClsItem.params) {
                for (let param of this.choosenClsItem.params) {
                    param.value = param.default.toString()
                }
            }
        },
        resetEditParams(item) {
            item.serving_name = item.name
            if (item.params) {
                for (let param of item.params) {
                    param.value = param.default.toString()
                }
            }
        },
        handleAdd() {
            this.show.add ^= true
            this.resetAddParams()
        },
        handleEdit(item) {
            item.edit ^= true
            this.resetEditParams(item)
        },
        checkAdd() {
            if (!this.servingName) {
                return false
            }
            if (!this.choosenClsItem.cls_name) {
                return false
            }
            if (this.choosenClsItem.params) {
                for (let param of this.choosenClsItem.params) {
                    if (!param.value) {
                        return false
                    }
                }
            }
            return true
        },
        checkEdit(item) {
            if (!item.serving_name) {
                return false
            }
            if (!item.cls_name) {
                return false
            }
            if (item.params) {
                for (let param of item.params) {
                    if (!param.value) {
                        return false
                    }
                }
            }
            return true
        }
    }
}
</script>

<style lang="scss">
.df-serving-container {
    position: relative;
    width: 100%;
    height: 100%;
    background-color: rgba(241, 241, 241, 1);
    display: flex;
    justify-content: center;

    .major-container {
        width: 100%;
        max-width: 1200px;
        height: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;

        .title-block {
            position: absolute;
            width: 100%;
            padding: 15px;
            padding-top: 30px;
            z-index: 1;
            backdrop-filter: blur(20px);

            .main-title {
                font-size: 28px;
                font-weight: 400;
                color: rgba(26, 26, 26, 1);
            }
        }

        .content-block {
            position: relative;
            width: 100%;
            height: 100%;
            gap: 5px;
            padding: 15px;
            padding-top: 100px;
            display: flex;
            flex-direction: column;
            overflow: overlay;

            .serving-item {
                flex-shrink: 0;

                .collapse-item-content {
                    position: relative;
                    height: auto;
                    transition: all 0.3s;
                }

                .serving-item-title {
                    margin: 5px 0px;
                    font-size: 13.8px;
                    font-weight: bold;
                    color: rgba(123, 139, 209, 1);
                    user-select: none;
                }

                .serving-item-light-title {
                    margin: 5px 0px;
                    font-size: 12px;
                    color: rgba(95, 95, 95, 1);
                    user-select: none;
                }

                .serving-item-info {
                    margin: 5px 0px;
                    font-size: 12px;
                    color: rgba(120, 120, 120, 1);
                    user-select: none;
                }

                .serving-item-std-info {
                    font-size: 13.8px;
                    color: rgba(27, 27, 27, 1);
                    user-select: none;
                }

                .serving-item-bold-info {
                    margin: 5px 0px;
                    font-size: 16px;
                    font-weight: bold;
                    color: rgba(27, 27, 27, 1);
                    user-select: none;
                }

                .serving-item-p-block {
                    position: relative;
                    width: 100%;
                    height: auto;
                    padding: 15px 0px;
                    box-sizing: border-box;
                    line-height: 3;
                    display: flex;
                    flex-direction: column;
                }

                .serving-item-row {
                    position: relative;
                    width: 100%;
                    padding: 0px 42px;
                    flex-wrap: wrap;
                    box-sizing: border-box;
                    display: flex;
                    align-items: center;

                    &.no-pad {
                        padding: 0px;
                    }

                    &.sep {
                        justify-content: space-between;
                    }

                    &.column {
                        flex-direction: column;
                        align-items: flex-start;
                    }

                    &.full {
                        flex: 1;
                    }

                    &.auto {
                        overflow: auto;
                    }
                }

                hr {
                    margin: 10px 0px;
                    border: none;
                    border-top: rgba(120, 120, 120, 0.1) solid thin;
                }
            }
        }
    }
}
</style>
