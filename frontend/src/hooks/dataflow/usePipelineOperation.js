import { useAppConfig } from '@/stores/appConfig'
import { useVueFlow } from '@vue-flow/core'
import { getCurrentInstance } from 'vue'
import { useGlobal } from '@/hooks/general/useGlobal'

/**
 * 管道操作Hook，提供数据流图中管道的相关操作功能
 * 包括添加管道节点和渲染完整管道
 * @returns 管道操作相关的方法集合
 */
export function usePipelineOperation() {

    /**
     * 添加管道节点到Vue Flow流程图中
     * @param {Object} data - 节点数据，包含节点配置信息
     * @param {string} flowId - Vue Flow实例的ID
     */
    const addPipelineNode = (data, flowId) => {
        // 启用节点删除功能
        data.enableDelete = true
        // 获取指定ID的Vue Flow实例
        const flow = useVueFlow(flowId)
        // 计算节点位置，Y轴添加随机偏移
        const position = {
            x: data.location.x,
            y: data.location.y + parseInt(5 * Math.random())
        }
        // 构建新节点对象
        const newNode = {
            id: data.nodeId, // 节点唯一标识
            type: 'operator-node', // 节点类型
            position: position, // 节点位置
            data: {
                flowId: flowId, // 流程图ID
                ...data // 节点数据
            }
        }
        // 将新节点添加到流程图中
        flow.addNodes(newNode)
    }

    /**
     * 渲染完整的管道配置到Vue Flow流程图中
     * @async
     * @param {Object} pipelineConfig - 管道配置信息
     * @param {string} flowId - Vue Flow实例的ID
     * @param {Array} datasets - 数据集列表
     * @param {Array} flatFormatedOperators - 格式化的操作符列表
     * @param {Function} $nextTick - Vue的nextTick函数
     * @param {Function} $emit - 组件的事件发射函数
     */
    const renderPipeline = async (pipelineConfig, flowId, datasets, flatFormatedOperators, $nextTick, $emit) => {
        // 获取Vue组件实例和代理
        const instance = getCurrentInstance()
        const proxy = instance.proxy
        // 获取应用配置
        const appConfig = useAppConfig()
        // 获取全局工具函数
        const { $Guid, $infoBox } = useGlobal()

        // 打印管道配置（调试用）
        console.log(pipelineConfig)
        // 获取指定ID的Vue Flow实例
        const flow = useVueFlow(flowId)
        // 重置流程图状态
        flow.$reset()
        // 设置默认视口位置和缩放比例
        flow.setViewport({
            x: 0,
            y: 0,
            zoom: 1
        })
        // 等待DOM更新完成
        await $nextTick()

        // 如果没有管道配置，直接返回
        if (!pipelineConfig) return

        // 解析管道配置
        const { input_dataset, operators } = pipelineConfig
        // 设置节点基础位置
        const basicPos = {
            x: 350,
            y: 0
        }

        // 查找输入数据集
        let dataset = datasets.find((item) => item.id === input_dataset.id)
        if (!dataset) {
            // 如果未找到数据集，显示警告信息
            proxy.$barWarning(appConfig.local('Input dataset not found'), {
                status: 'warning'
            })
        } else {
            // 复制数据集对象并更新位置信息
            dataset = Object.assign({}, dataset)
            dataset.location = input_dataset.location
            // 发射数据集确认事件
            $emit('confirm-dataset', dataset)
        }

        // 格式化后的操作符列表
        let formatOperators = []
        // 用于并行处理API请求的Promise列表
        let promiseList = []
        // 在这里的设计是为了保险起见还是重新获取所有operator的预定义参数, 然后结合当前pipeline获取的参数进行合并, 然而当前事实上其实还是直接用了当前pipeline获取的参数, 后续若有需求再考虑是否需要修改
        operators.forEach((item, idx) => {
            // 添加API请求到Promise列表
            promiseList.push(
                proxy.$api.operators.get_operator_detail_by_name(item.name).then((res) => {
                    if (res.code === 200) {
                        // 查找对应的格式化操作符
                        let operator = flatFormatedOperators.find(
                            (it) => it.name === item.name
                        )
                        // 深拷贝操作符对象
                        operator = Object.assign({}, operator)
                        // 合并API返回的详细信息
                        operator = Object.assign(operator, res.data)
                        // 更新操作符位置
                        operator.location = item.location
                        // 缓存操作符参数
                        operator._cache_parameter = {
                            init: [],
                            run: []
                        }
                        operator._cache_parameter.init = item.params.init
                        operator._cache_parameter.run = item.params.run
                        // 设置操作符在管道中的索引
                        operator.pipeline_idx = idx + 1
                        // 添加到格式化操作符列表
                        formatOperators.push(operator)
                    }
                })
            )
        })

        // 等待所有API请求完成
        await Promise.all(promiseList)
        // 按索引排序操作符
        formatOperators.sort((a, b) => a.pipeline_idx - b.pipeline_idx)

        // 处理每个操作符并添加到流程图中
        formatOperators.forEach((item, idx) => {
            // 如果位置是数组格式，转换为对象格式
            if (Array.isArray(item.location)) {
                item.location = {
                    x: item.location[0],
                    y: item.location[1]
                }
            }
            // 如果位置未设置或为0，计算默认位置
            if (item.location.x === 0 || item.location.y === 0)
                item.location = {
                    x: idx === 0 ? basicPos.x : formatOperators[idx - 1].location.x + 350,
                    y: basicPos.y
                }
            // 生成节点唯一ID
            item.nodeId = $Guid()
            // 添加节点到流程图
            addPipelineNode(item, flowId)
        })

        // 检查是否存在数据集节点
        let existsDatasetNode = flow.findNode('db-node')

        // 为操作符之间添加连接线
        formatOperators.forEach((item, idx) => {
            // 如果是第一个操作符且没有数据集节点，则跳过
            if (idx === 0 && !existsDatasetNode) return
            // 确定源节点ID
            let last_id = idx === 0 ? 'db-node' : formatOperators[idx - 1].nodeId
            // 添加连接线
            flow.addEdges({
                id: $Guid(), // 边唯一标识
                type: 'base-edge', // 边类型
                source: last_id, // 源节点ID
                target: item.nodeId, // 目标节点ID
                sourceHandle: 'node::source::node', // 源节点手柄
                targetHandle: 'node::target::node', // 目标节点手柄
                animated: false, // 禁用动画
                data: {
                    label: 'Node', // 边标签
                    edgeType: 'node' // 边类型标识
                }
            })
        })
    }

    // 返回管道操作方法
    return {
        addPipelineNode, // 添加管道节点方法
        renderPipeline // 渲染管道方法
    }
}