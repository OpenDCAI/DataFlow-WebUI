import { useVueFlow } from '@vue-flow/core'

/**
 * 边同步Hook，提供数据流图中边的相关操作功能
 * @returns 边操作相关的方法集合
 */
export function useEdgeSync() {
    /**
     * 解析Handle标识符字符串，转换为标准化的Handle对象
     * 
     * @param {string|null|undefined} handleItem - Handle标识符字符串，格式为"name::direction::edgeType"
     * @returns {Object} 包含Handle信息的对象
     * @returns {string} return.name - Handle属性名
     * @returns {string} return.direction - 出入边方向（source/target）
     * @returns {string} return.edgeType - 边类型
     */
    const decHandle = (handleItem) => {
        // 如果Handle标识符不存在，返回默认Handle配置
        if (!handleItem) return {
            name: 'default',
            direction: 'source',
            edgeType: 'default',
        }

        let items = handleItem.split('::');

        return {
            name: items[0],       // Handle属性名
            direction: items[1],  // 出入边方向
            edgeType: items[2],   // 边类型
        }
    }

    /**
     * 同步算子节点的运行参数值到目标节点的运行参数中
     * 
     * @param {Object} operatorNodeItem - 算子节点对象，包含节点ID和属性名
     * @param {string} flowId - 流程ID，用于获取VueFlow实例
     */
    const syncRunValue = (operatorNodeItem, flowId) => {
        const flow = useVueFlow(flowId)
        let edges = flow.edges.value.filter((edge) => edge.source === operatorNodeItem.nodeId)
        for (let edge of edges) {
            let sourceKeyName = edge.sourceHandle ? edge.sourceHandle.split('::')[0] : null
            if (sourceKeyName !== operatorNodeItem.name) continue
            let targetNode = flow.findNode(edge.target)
            let targetKeyName = edge.targetHandle ? edge.targetHandle.split('::')[0] : null
            if (targetNode) {
                let targetIndex = targetNode.data.operatorParams.run.findIndex(
                    (item) => item.name === targetKeyName
                )
                if (targetIndex !== -1) {
                    targetNode.data.operatorParams.run[targetIndex].value = operatorNodeItem.value
                }
            }
        }
    }

    /** 
     * 自动连接算子节点的运行参数边
     * 
     * @param {string} source - 源算子节点ID
     * @param {string} target - 目标算子节点ID
     * @param {string} flowId - 流程ID，用于获取VueFlow实例
     * @param {function} guid_func - 生成唯一ID的函数
     */
    const autoConnectRunEdges = (source, target, flowId, guid_func) => {
        const flow = useVueFlow(flowId)
        let sourceNode = flow.findNode(source)
        let targetNode = flow.findNode(target)
        if (!sourceNode || !targetNode) return
        let targetRuns = targetNode.data.operatorParams.run || [];
        let sourceRuns = sourceNode.data.operatorParams.run || [];
        for (let i = 0; i < sourceRuns.length; i++) {
            let sourceRun = sourceRuns[i]
            let targetIndex = targetRuns.findIndex((item) => item.name === sourceRun.name)
            if (targetIndex !== -1) {
                let existsEdge = flow.edges.value.find((edge) => edge.source === source && edge.target === target && edge.sourceHandle === `${sourceRun.name}::source::run_key` && edge.targetHandle === `${sourceRun.name}::target::run_key`)
                if (existsEdge) continue
                flow.addEdges({
                    id: guid_func(),
                    type: 'base-edge',
                    source: source,
                    target: target,
                    sourceHandle: `${sourceRun.name}::source::run_key`,
                    targetHandle: `${sourceRun.name}::target::run_key`,
                    animated: true,
                    data: {
                        label: 'Key',
                        edgeType: 'run_key',
                    }
                })
            }
        }
    }

    /** 
     * 自动连接所有算子节点的运行参数边
     * 
     * @param {string} flowId - 流程ID，用于获取VueFlow实例
     * @param {function} guid_func - 生成唯一ID的函数
     */
    const autoConnectAllRunEdges = (flowId, guid_func) => {
        const flow = useVueFlow(flowId)
        let edges = flow.edges.value
        for (let i = 0; i < edges.length; i++) {
            let edge = edges[i]
            if (edge.data.edgeType === 'node') {
                autoConnectRunEdges(edge.source, edge.target, flowId, guid_func)
            }
        }
    }

    /** 
     * 移除算子节点的运行参数边
     * 
     * @param {string} source - 源算子节点ID
     * @param {string} target - 目标算子节点ID
     * @param {string} flowId - 流程ID，用于获取VueFlow实例
     */
    const removeRunEdges = (source, target, flowId) => {
        const flow = useVueFlow(flowId)
        let edges = flow.edges.value.filter((edge) => edge.source === source && edge.target === target)
        for (let edge of edges) {
            flow.removeEdges([edge.id])
        }
    }

    return {
        decHandle,
        syncRunValue,
        autoConnectRunEdges,
        autoConnectAllRunEdges,
        removeRunEdges,
    }
}