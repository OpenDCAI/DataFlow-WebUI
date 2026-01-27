<template>
    <div class="df-serving-container" :class="[{ dark: theme === 'dark' }]">
        <div class="major-container">
            <div class="title-block">
                <p class="main-title">{{ local('Serving') }}</p>
            </div>
            <div class="content-block">
                <fv-Collapse :theme="theme" v-model="show.add" class="serving-item" icon="Marquee"
                    :title="local('Add Serving')" :content="local('Add new serving information.')"
                    :disabled-collapse="true" :max-height="'auto'">
                    <template v-slot:extension>
                        <fv-button v-show="show.add" theme="dark" :is-box-shadow="true" :background="gradient"
                            :disabled="!checkAdd() || !lock.add" border-radius="6"
                            style="width: 90px; margin-right: 5px" @click="confirmAdd">
                            {{ local('Confirm') }}
                        </fv-button>
                        <fv-button :theme="show.add ? theme : 'dark'" :is-box-shadow="true"
                            :background="show.add ? '' : gradient" border-radius="6" style="width: 90px"
                            @click="handleAdd">
                            {{ show.add ? local('Cancel') : local('Add') }}
                        </fv-button>
                    </template>
                    <template v-slot:default>
                        <div class="serving-item-row column">
                            <p class="serving-item-light-title">{{ local('Serving Name') }}</p>
                            <fv-text-box :theme="theme" v-model="servingName" :placeholder="local('Serving Name')"
                                border-radius="6" :reveal-border="true" :is-box-shadow="true"></fv-text-box>
                        </div>
                        <hr />
                        <div class="serving-item-row column">
                            <p class="serving-item-light-title">{{ local('Select CLS Name') }}</p>
                            <fv-combobox :theme="theme" v-model="choosenClsItem" :options="createProps"
                                :placeholder="local('Select CLS Name')" :border-radius="6"
                                :input-background="theme === 'dark' ? 'rgba(40, 40, 40, 1)' : 'rgba(252, 252, 252, 1)'"></fv-combobox>
                        </div>
                        <hr />
                        <div v-if="choosenClsItem && choosenClsItem.params"
                            v-for="(param, p_index) in choosenClsItem.params">
                            <div class="serving-item-row column">
                                <p class="serving-item-light-title">{{ param.name }}</p>
                                <fv-text-box :theme="theme" v-model="param.value" :placeholder="local(param.name)"
                                    border-radius="6" :reveal-border="true" :is-box-shadow="true"></fv-text-box>
                            </div>
                            <hr />
                        </div>
                    </template>
                </fv-Collapse>
                <fv-Collapse :theme="theme" v-for="(item, index) in servingList" :key="index" class="serving-item"
                    icon="DialShape4" :title="item.name" :content="item.cls_name" :max-height="740">
                    <template v-slot:extension>
                        <fv-button theme="dark" background="rgba(191, 95, 95, 1)" foreground="rgba(255, 255, 255, 1)"
                            border-radius="6" :is-box-shadow="true" style="width: 90px"
                            @click="$event.stopPropagation(), delServing(item)">
                            {{ local('Delete') }}
                        </fv-button>
                    </template>
                    <template v-slot:default>
                        <hr />
                        <div class="serving-item-row sep">
                            <div class="serving-item-row column no-pad" style="flex: 1">
                                <p class="serving-item-light-title">{{ local('ID') }}</p>
                                <p class="serving-item-std-info">{{ item.id }}</p>
                            </div>
                            <fv-button v-show="item.edit" theme="dark" :is-box-shadow="true" :background="gradient"
                                border-radius="6" :disabled="!checkEdit(item) || !lock.edit"
                                style="width: 90px; margin-right: 5px" @click="confirmEdit(item)">
                                {{ local('Confirm') }}
                            </fv-button>
                            <fv-button :theme="theme" :icon="item.edit ? 'Cancel' : 'Edit'" :is-box-shadow="true"
                                border-radius="6" style="width: 90px" @click="handleEdit(item)">
                                {{ item.edit ? local('Cancel') : local('Edit') }}
                            </fv-button>
                        </div>
                        <hr />
                        <div class="serving-item-row column">
                            <p class="serving-item-light-title">{{ local('Serving Name') }}</p>
                            <fv-text-box :theme="theme" v-model="item.serving_name" border-radius="6"
                                :disabled="!item.edit" :reveal-border="true" :is-box-shadow="item.edit"></fv-text-box>
                        </div>
                        <hr />
                        <div v-for="(param, p_index) in item.params">
                            <div class="serving-item-row column">
                                <p class="serving-item-light-title">{{ param.name }}</p>
                                <fv-text-box :theme="theme" v-model="param.value" border-radius="6"
                                    :disabled="!item.edit" :reveal-border="true"
                                    :is-box-shadow="item.edit"></fv-text-box>
                            </div>
                            <hr />
                        </div>
                        <div class="serving-item-row column">
                            <p class="serving-item-title">{{ local('Serving Testing') }}</p>
                            <div class="serving-item-row no-pad">
                                <fv-button :theme="theme" border-radius="8" style="width: 30px; height: 30px"
                                    :disabled="!lock.test" :reveal-border-gradient-list="[
                                        '#40e0d0',
                                        '#40e0d0',
                                        '#ff8c00',
                                        '#ff8c00',
                                        '#ff0080',
                                        'rgba(255, 255, 255, 0)'
                                    ]" @click="testServing(item)">
                                    <i class="ms-Icon ms-Icon--ProgressRingDots rainbow"
                                        :class="[{ 'ring-animation': !lock.test }]"></i>
                                </fv-button>
                                <p class="serving-item-bold-info" style="margin-left: 15px">
                                    {{ local('Response') }}: {{ item.response }}
                                </p>
                            </div>
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
            defaultValues: {
                str: '',
                int: '0',
                Any: '',
                float: '0.0',
                'dict': {}
            },
            formatValues: {
                str: (val) => val.toString(),
                int: (val) => parseInt(val),
                Any: (val) => val.toString(),
                float: (val) => parseFloat(val),
                'dict': (val) => {
                    try {
                        return JSON.parse(val)
                    }
                    catch (error) {
                        return {}
                    }
                }
            },
            show: {
                add: false
            },
            lock: {
                add: true,
                edit: true,
                test: true,
                delete: true
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
                            if (param.default_value !== null)
                                param.value = this.formatPropsValue(param.default_value)
                            else param.value = this.defaultValues[param.type]
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
                        this.resetEditParams(item, true)
                    })
                    this.servingList = servingList
                }
            })
        },
        formatPropsValue(val) {
            if (val === null) return null
            if (typeof val === 'string') return val
            if (typeof val === 'object') return JSON.stringify(val)
            return val.toString()
        },
        resetAddParams() {
            this.servingName = ''
            if (this.choosenClsItem.params) {
                for (let param of this.choosenClsItem.params) {
                    if (param.default_value !== null) param.value = this.formatPropsValue(param.default_value)
                    else param.value = this.defaultValues[param.type]
                }
            }
        },
        resetEditParams(item, overide = false) {
            item.serving_name = item.name
            if (item.params) {
                for (let param of item.params) {
                    param.value = this.formatPropsValue(param.value)
                    if (overide) {
                        if (param.value !== null) param.default_value = this.formatPropsValue(param.value)
                    } else {
                        if (param.default_value !== null)
                            param.value = this.formatPropsValue(param.default_value)
                        else param.value = this.defaultValues[param.type]
                    }
                }
            }
        },
        valueBuilder(item) {
            let type = item.type
            return this.formatValues[type](item.value)
        },
        handleAdd() {
            this.show.add ^= true
            this.resetAddParams()
        },
        confirmAdd() {
            if (!this.lock.add) return
            if (!this.checkAdd()) return
            this.lock.add = false
            let params = []
            if (this.choosenClsItem.params) {
                for (let param of this.choosenClsItem.params) {
                    params.push({
                        name: param.name,
                        value: this.valueBuilder(param)
                    })
                }
            }
            this.$api.serving
                .create_serving_instance(this.servingName, this.choosenClsItem.cls_name, params)
                .then((res) => {
                    if (res.code === 200) {
                        this.getServingList()
                        this.resetAddParams()
                        this.show.add ^= true
                    } else {
                        this.$barWarning(res.message, {
                            status: 'warning'
                        })
                    }
                    this.lock.add = true
                })
                .catch((err) => {
                    this.$barWarning(err, {
                        status: 'error'
                    })
                    this.lock.add = true
                })
        },
        confirmEdit(item) {
            if (!this.lock.edit) return
            if (!this.checkEdit(item)) return
            this.lock.edit = false
            let params = []
            if (item.params) {
                for (let param of item.params) {
                    params.push({
                        name: param.name,
                        value: this.valueBuilder(param)
                    })
                }
            }
            this.$api.serving
                .update_serving_instance(item.id, {
                    name: item.serving_name,
                    params
                })
                .then((res) => {
                    if (res.code === 200) {
                        this.getServingList()
                        item.edit ^= true
                        this.resetEditParams(item)
                        this.$barWarning(this.local('Update Success'), {
                            status: 'correct'
                        })
                    } else {
                        this.$barWarning(res.message, {
                            status: 'warning'
                        })
                    }
                    this.lock.edit = true
                })
                .catch((err) => {
                    this.$barWarning(err, {
                        status: 'error'
                    })
                    this.lock.edit = true
                })
        },
        handleEdit(item) {
            item.edit ^= true
            this.resetEditParams(item)
        },
        testServing(item) {
            if (!this.lock.test) return
            this.lock.test = false
            this.$api.serving
                .test_serving_instance(item.id, {
                    prompt: '你好'
                })
                .then((res) => {
                    if (res.code === 200) {
                        item.response = res.data.response
                    } else {
                        this.$barWarning(res.message, {
                            status: 'warning'
                        })
                    }
                    this.lock.test = true
                })
        },
        delServing(item) {
            this.$infoBox(this.local('Are you sure to delete this serving?'), {
                status: 'error',
                theme: this.theme,
                confirm: () => {
                    if (!this.lock.delete) return
                    this.lock.delete = false
                    this.$api.serving
                        .delete_serving_instance(item.id)
                        .then((res) => {
                            if (res.code === 200) {
                                this.getServingList()
                                this.$barWarning(this.local('Delete Success'), {
                                    status: 'correct'
                                })
                            } else {
                                this.$barWarning(res.message, {
                                    status: 'warning'
                                })
                            }
                            this.lock.delete = true
                        })
                        .catch((err) => {
                            this.$barWarning(err, {
                                status: 'error'
                            })
                            this.lock.delete = true
                        })
                }
            })
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

    &.dark {
        background: rgba(36, 36, 36, 1);

        .major-container {
            .title-block {
                .main-title {
                    color: whitesmoke;
                }
            }
        }
    }

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

    .rainbow {
        @include color-rainbow;

        color: black;
    }

    .ring-animation {
        animation: ring-rotate 1s linear infinite;
    }

    @keyframes ring-rotate {
        0% {
            transform: rotate(0deg);
        }

        100% {
            transform: rotate(360deg);
        }
    }
}
</style>
