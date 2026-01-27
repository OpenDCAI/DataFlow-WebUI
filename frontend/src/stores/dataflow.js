import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { getCurrentInstance } from 'vue'

export const useDataflow = defineStore('useDataflow', () => {
    const instance = getCurrentInstance()
    const proxy = instance.proxy

    const getKeyText = (text) => {
        let splitText = text.split('_')
        return splitText.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
    }

    const operatorStyleDict = ref({
        default: {
            icon: 'Flag',
            statusColor: 'rgba(0, 153, 204, 1)',
            iconColor: 'rgba(255, 255, 255, 1)',
            iconBackground:
                'linear-gradient(90deg, rgba(73, 131, 251, 1) 0%, rgba(100, 161, 252, 1) 100%)',
            borderColor: 'rgba(73, 131, 251, 0.6)',
            shadowColor: 'rgba(73, 131, 251, 0.1)'
        },
        parser: {
            icon: 'Document',
            statusColor: 'rgba(255, 153, 0, 1)',
            iconColor: 'rgba(255, 255, 255, 1)',
            iconBackground:
                'linear-gradient(90deg, rgba(255, 153, 0, 1) 0%, rgba(255, 204, 0, 1) 100%)',
            borderColor: 'rgba(255, 153, 0, 0.6)',
            shadowColor: 'rgba(255, 153, 0, 0.1)'
        },
        filter: {
            icon: 'PostUpdate',
            statusColor: 'rgba(255, 102, 0, 1)',
            iconColor: 'rgba(255, 255, 255, 1)',
            iconBackground:
                'linear-gradient(90deg, rgba(255, 102, 0, 1) 0%, rgba(255, 153, 0, 1) 100%)',
            borderColor: 'rgba(255, 102, 0, 0.6)',
            shadowColor: 'rgba(255, 102, 0, 0.1)'
        },
        generate: {
            icon: 'Library',
            statusColor: 'rgba(255, 51, 0, 1)',
            iconColor: 'rgba(255, 255, 255, 1)',
            iconBackground:
                'linear-gradient(90deg, rgba(255, 51, 0, 1) 0%, rgba(255, 102, 0, 1) 100%)',
            borderColor: 'rgba(255, 51, 0, 0.6)',
            shadowColor: 'rgba(255, 51, 0, 0.1)'
        },
        eval: {
            icon: 'Bullseye',
            statusColor: 'rgba(255, 0, 0, 1)',
            iconColor: 'rgba(255, 255, 255, 1)',
            iconBackground:
                'linear-gradient(90deg, rgba(255, 0, 0, 1) 0%, rgba(255, 51, 0, 1) 100%)',
            borderColor: 'rgba(255, 0, 0, 0.6)',
            shadowColor: 'rgba(255, 0, 0, 0.1)'
        },
        refine: {
            icon: 'Market',
            statusColor: 'rgba(0, 153, 0, 1)',
            iconColor: 'rgba(255, 255, 255, 1)',
            iconBackground:
                'linear-gradient(90deg, rgba(0, 153, 0, 1) 0%, rgba(0, 204, 0, 1) 100%)',
            borderColor: 'rgba(0, 153, 0, 0.6)',
            shadowColor: 'rgba(0, 153, 0, 0.1)'
        }
    })
    const operators = ref([])
    const groupOperators = ref({})
    const getOperators = async (lang = 'zh') => {
        await proxy.$api.operators.list_operators(lang).then((res) => {
            if (res.code === 200) {
                operators.value = res.data
                groupOperators.value = {}
                for (let operator of operators.value) {
                    let styleKey = operator.type.level_2
                    if (!operatorStyleDict.value[styleKey]) {
                        styleKey = 'default'
                    }
                    operator = {
                        status: getKeyText(operator.type.level_2),
                        statusColor: operatorStyleDict.value[styleKey].statusColor,
                        label: operator.name,
                        icon: operatorStyleDict.value[styleKey].icon,
                        iconColor: operatorStyleDict.value[styleKey].iconColor,
                        iconBackground: operatorStyleDict.value[styleKey].iconBackground,
                        borderColor: operatorStyleDict.value[styleKey].borderColor,
                        shadowColor: 'rgba(0, 0, 0, 0.05)',
                        nodeShadowColor: operatorStyleDict.value[styleKey].shadowColor,
                        enableDelete: false,
                        show: true,
                        ...operator
                    }

                    if (groupOperators.value[operator.type.level_1]) {
                        groupOperators.value[operator.type.level_1].items.push(operator)
                    } else {
                        groupOperators.value[operator.type.level_1] = {
                            key: operator.type.level_1,
                            name: getKeyText(operator.type.level_1),
                            items: [operator],
                            expand: true
                        }
                    }
                }
            } else {
                proxy.$barWarning(res.message, {
                    status: 'warning'
                })
            }
        })
    }

    const datasets = ref([])
    const getDatasets = async () => {
        let res = await proxy.$api.datasets.list_datasets().catch((err) => {
            proxy.$barWarning(err, {
                status: 'error'
            })
        })
        if (res.success) {
            let _datasets = res.data
            _datasets.forEach((item) => {
                item.showPreview = false
                item.expanded = false
            })
            datasets.value = _datasets
        } else {
            proxy.$barWarning(res.message, {
                status: 'warning'
            })
        }
    }

    const text2sqlDatasets = ref([])
    const getText2SqlDatasets = async () => {
        await proxy.$api.text2sql_database.list_databases().then((res) => {
            if (res.code === 200) {
                text2sqlDatasets.value = res.data
            } else {
                proxy.$barWarning(res.message, {
                    status: 'warning'
                })
            }
        })
    }

    const servingList = ref([])
    const currentServing = ref(null)
    const getServingList = async () => {
        await proxy.$api.serving.list_serving_instances_api_v1_serving__get().then((res) => {
            if (res.code === 200) {
                res.data.forEach((item) => {
                    item.key = item.id
                    item.text = item.name
                })
                servingList.value = res.data
            } else {
                proxy.$barWarning(res.message, {
                    status: 'warning'
                })
            }
        })
    }
    const chooseServing = (item) => {
        currentServing.value = item
    }

    const dataManagerList = ref([])
    const getDataManagerList = async () => {
        await proxy.$api.text2sql_database_manager.list_text2sql_database_managers().then((res) => {
            if (res.code === 200) {
                res.data.forEach((item) => {
                    item.key = item.id
                    item.text = item.name
                })
                dataManagerList.value = res.data
            } else {
                proxy.$barWarning(res.message, {
                    status: 'warning'
                })
            }
        })
    }

    const pipelines = ref([])
    const getPipelines = async () => {
        await proxy.$api.pipelines.list_pipelines().then((res) => {
            if (res.code === 200) {
                let _pipelines = res.data
                _pipelines.forEach((item) => {
                    item.show = true
                })
                _pipelines.sort((a, b) => {
                    return new Date(b.updated_at) - new Date(a.updated_at)
                })
                pipelines.value = _pipelines
            }
        })
    }

    const tasks = ref([])
    const getTasks = async () => {
        await proxy.$api.tasks.list_executions().then((res) => {
            if (res.code === 200) {
                let _tasks = res.data
                tasks.value = _tasks
            }
        })
    }

    const execution = ref({})
    const executionStep = ref(null)
    const getExecution = async (task_id) => {
        await proxy.$api.tasks.get_execution_status(task_id).then((res) => {
            if (res.code === 200) {
                execution.value = res.data
                try {
                    if (execution.value.status === 'running') {
                        for (let key in execution.value.operators_detail) {
                            let { index, status } = execution.value.operators_detail[key]
                            if (status === 'running') {
                                executionStep.value = index
                                break
                            }
                        }
                    } else {
                        for (let key in execution.value.operators_detail) {
                            let { index, status } = execution.value.operators_detail[key]
                            if (status === 'completed') {
                                if (index > executionStep.value || executionStep.value === null) {
                                    executionStep.value = index
                                }
                            }
                        }
                    }
                } catch (error) {
                    executionStep.value = null
                }
            }
        })
    }
    const clearExecution = () => {
        execution.value = {}
    }

    const isAutoConnection = ref(false)

    const switchAutoConnection = (val) => {
        isAutoConnection.value = val
    }

    return {
        operators,
        groupOperators,
        getOperators,
        datasets,
        getDatasets,
        text2sqlDatasets,
        getText2SqlDatasets,
        servingList,
        currentServing,
        getServingList,
        chooseServing,
        dataManagerList,
        getDataManagerList,
        pipelines,
        getPipelines,
        tasks,
        getTasks,
        execution,
        executionStep,
        getExecution,
        clearExecution,
        isAutoConnection,
        switchAutoConnection
    }
})
