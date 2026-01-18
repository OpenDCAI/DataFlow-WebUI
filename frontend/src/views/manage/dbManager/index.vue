<template>
    <div class="df-dm-container" :class="[{ dark: theme === 'dark' }]">
        <div class="major-container">
            <div class="title-block">
                <p class="main-title">{{ local('DB Manager') }}</p>
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
                            <p class="serving-item-light-title">{{ local('Description') }}</p>
                            <fv-text-field :theme="theme" v-model="description" :placeholder="local('Description')"
                                border-radius="6" :reveal-border="true" :is-box-shadow="true"
                                style="height: 80px;"></fv-text-field>
                        </div>
                        <hr />
                        <div class="serving-item-row column">
                            <p class="serving-item-light-title">{{ local('Select CLS Name') }}</p>
                            <fv-combobox :theme="theme" v-model="choosenClsItem" :options="createProps"
                                :placeholder="local('Select CLS Name')" :border-radius="6"
                                :input-background="theme === 'dark' ? 'rgba(36, 36, 36, 1)' : 'rgba(252, 252, 252, 1)'"></fv-combobox>
                        </div>
                        <hr />
                        <div v-if="choosenClsItem && choosenClsItem.params"
                            v-for="(param, p_index) in choosenClsItem.params">
                            <div class="serving-item-row column">
                                <p class="serving-item-light-title">{{ param.name }}</p>
                                <fv-text-box :theme="theme" v-if="param.name !== 'selected_db_ids'"
                                    v-model="param.value" :placeholder="local(param.name)" border-radius="6"
                                    :reveal-border="true" :is-box-shadow="true"></fv-text-box>
                                <fv-drop-down :theme="theme" v-if="param.name === 'selected_db_ids'"
                                    v-model="choosenText2SqlDatasetItems" :options="formatedText2SqlDatasets"
                                    :multiple="true" :placeholder="local('Select Text2Sql Dataset')" :border-radius="6"
                                    :input-background="'rgba(252, 252, 252, 1)'"></fv-drop-down>
                            </div>
                            <hr />
                        </div>
                    </template>
                </fv-Collapse>
                <fv-Collapse :theme="theme" v-for="(item, index) in dmManagerList" :key="index" class="serving-item"
                    icon="DialShape4" :title="item.name.value" :content="item.cls_name.value" :max-height="770">
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
                                <p class="serving-item-std-info">{{ item.id.value }}</p>
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
                        <div v-show="key !== 'edit'" v-for="(val, key) in item" :key="key">
                            <div class="serving-item-row column">
                                <p class="serving-item-light-title">{{ key }}</p>
                                <fv-text-box :theme="theme" v-if="key !== 'selected_db_ids'" v-model="item[key].value"
                                    border-radius="6" :disabled="!item.edit" :reveal-border="true"
                                    :is-box-shadow="item.edit"></fv-text-box>
                                <fv-drop-down :theme="theme" v-if="key === 'selected_db_ids'" v-model="item[key].value"
                                    :options="formatedText2SqlDatasets" :multiple="true"
                                    :placeholder="local('Select Text2Sql Dataset')" :border-radius="6"
                                    :disabled="!item.edit" :input-background="'rgba(252, 252, 252, 1)'"></fv-drop-down>
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
import { mapActions, mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import { useDataflow } from '@/stores/dataflow';

export default {
    data() {
        return {
            createProps: [],
            choosenClsItem: {},
            choosenText2SqlDatasetItems: [],
            servingName: '',
            description: '',
            dmManagerList: [],
            defaultValues: {
                str: '',
                int: '0',
                Any: '',
                "List[str]": [],
                'Optional': '',
            },
            formatValues: {
                'str': (val) => val.toString(),
                'int': (val) => parseInt(val),
                'Any': (val) => val.toString(),
                "List[str]": (val) => {
                    let result = []
                    for (let item of val) {
                        if (item.key) result.push(item.key)
                        else result.push(item.toString())
                    }
                    return result
                },
                'Optional': (val) => val.toString()
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
    watch: {
        choosenText2SqlDatasetItems: {
            handler(val) {
                if (!this.choosenClsItem.params) return;
                let selected_db_ids = this.choosenClsItem.params.find((param) => param.name === 'selected_db_ids');
                if (!selected_db_ids.value == undefined) return;
                selected_db_ids.value = val.map((item) => item.id)
            },
            deep: true
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme', 'color', 'gradient']),
        ...mapState(useDataflow, ['text2sqlDatasets']),
        formatedText2SqlDatasets() {
            return this.text2sqlDatasets.map((item) => {
                item.key = item.id
                item.text = item.name
                return item
            })
        }
    },
    mounted() {
        this.getCreateProps()
        this.getBMList()
        this.getText2SqlDatasets();
    },
    methods: {
        ...mapActions(useDataflow, ['getText2SqlDatasets']),
        getCreateProps() {
            this.$api.text2sql_database_manager.list_text2sql_database_manager_classes().then((res) => {
                if (res.data) {
                    let createProps = res.data
                    createProps.forEach((item) => {
                        item.key = item.cls_name
                        item.text = item.cls_name
                        for (let param of item.params) {
                            if (param.default_value !== null)
                                param.value = param.default_value.toString()
                            else param.value = this.defaultValues[param.type]
                        }
                    })
                    this.createProps = createProps
                }
            })
        },
        getBMList() {
            this.$api.text2sql_database_manager.list_text2sql_database_managers().then((res) => {
                if (res.data) {
                    let dmManagerList = res.data
                    dmManagerList.forEach((item) => {
                        for (let key in item) {
                            if (key === 'selected_db_ids') {
                                if (!Array.isArray(item[key])) item[key] = []
                                let selected_db_ids = []
                                for (let db_id of item[key]) {
                                    let formatItem = this.formatedText2SqlDatasets.find((dataset) => dataset.key === db_id)
                                    if (!formatItem) {
                                        formatItem = {
                                            key: db_id,
                                            text: db_id
                                        }
                                    }
                                    selected_db_ids.push(formatItem)
                                }
                                item[key] = selected_db_ids
                            }
                            else item[key] = item[key].toString()
                        }
                        for (let key in item) {
                            item[key] = {
                                key: item[key],
                                value: item[key],
                                default_value: item[key]
                            }
                        }
                        item.edit = false
                    })
                    this.dmManagerList = dmManagerList
                }
            })
        },
        resetAddParams() {
            this.servingName = ''
            if (this.choosenClsItem.params) {
                for (let param of this.choosenClsItem.params) {
                    if (param.default_value !== null) param.value = param.default_value.toString()
                    else param.value = this.defaultValues[param.type]
                }
            }
        },
        resetEditParams(item) {
            for (let key in item) {
                if (key === 'edit') continue
                item[key].value = item[key].default_value
            }
        },
        valueBuilder(item) {
            let type = item.type.toString()
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
            let params = {}
            if (this.choosenClsItem.params) {
                for (let param of this.choosenClsItem.params) {
                    params[param.name] = {
                        name: param.name,
                        value: this.valueBuilder(param)
                    }
                }
            }
            this.$api.text2sql_database_manager
                .create_text2sql_database_manager({
                    name: this.servingName,
                    cls_name: this.choosenClsItem.key,
                    db_type: params.db_type.value,
                    selected_db_ids: params.selected_db_ids.value,
                    description: this.description
                })
                .then((res) => {
                    if (res.code === 200) {
                        this.getBMList()
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
            let selected_db_ids = []
            for (let db_id of item.selected_db_ids.value) {
                selected_db_ids.push(db_id.key)
            }
            this.$api.text2sql_database_manager
                .update_text2sql_database_manager(item.id.value, {
                    name: item.name.value,
                    selected_db_ids: selected_db_ids,
                    description: item.description.value
                })
                .then((res) => {
                    if (res.code === 200) {
                        this.getBMList()
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
        delServing(item) {
            this.$infoBox(this.local('Are you sure to delete this serving?'), {
                status: 'error',
                theme: this.theme,
                confirm: () => {
                    if (!this.lock.delete) return
                    this.lock.delete = false
                    this.$api.text2sql_database_manager
                        .delete_text2sql_database_manager(item.id.value)
                        .then((res) => {
                            if (res.code === 200) {
                                this.getBMList()
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
            for (let key in item) {
                if (key === 'edit') continue
                if (!item[key].value) {
                    return false
                }
            }
            return true
        }
    }
}
</script>

<style lang="scss">
.df-dm-container {
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
