<script setup>
import { onMounted, onBeforeUnmount, watch, ref } from 'vue'
import {
    Chart,
    LineController,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Tooltip
} from 'chart.js'

// 注册必须组件（Tree Shaking 需要）
Chart.register(
    LineController,
    LineElement,
    PointElement,
    LinearScale,
    CategoryScale,
    Tooltip
)

const canvasRef = ref(null)
let chartInstance = null

const props = defineProps({
    label: {
        default: 'Sample Count'
    },
    rawData: {
        default: () => ([])
    },
    theme: {
        default: 'light'
    }
})

watch(() => props.rawData, (newVal, oldVal) => {
    if (newVal === oldVal) return

    chartInstance?.destroy()
    updateChart()
})

function updateChart() {
    const steps = Object.values(props.rawData)
        .sort((a, b) => a.index - b.index)

    const labels = steps.map(i => `S${i.index + 1}: ${i.name}`)
    const values = steps.map(i => i.sample_count)

    chartInstance = new Chart(canvasRef.value, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: props.label,
                    data: values,
                    tension: 0.4,     // 平滑曲线
                    fill: true,       // 填充面积
                    borderColor: '#4F46E5',        // 折线颜色
                    backgroundColor: 'rgba(79, 70, 229, 0.15)', // 填充区域
                    pointBackgroundColor: '#4F46E5',
                    pointBorderColor: '#ffffff',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    borderWidth: 2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: ctx => {
                            const step = steps[ctx[0].dataIndex]
                            return `Step: ${step.index + 1}\n${step.name}`
                        },
                        label: ctx => `Samples: ${ctx.parsed.y}`
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: props.theme === 'dark' ? 'rgba(200, 200, 200, 0.1)' : 'rgba(120, 120, 120, 0.1)'
                    },
                    ticks: {
                        maxRotation: 0, // 最大旋转角度
                        minRotation: 0, // 最小旋转角度
                        color: props.theme === 'dark' ? 'whitesmoke' : 'rgba(0, 0, 0, 0.7)',
                        callback: function (value) {
                            const label = this.getLabelForValue(value)
                            const maxLen = 16
                            return label.length > maxLen
                                ? label.slice(0, maxLen) + '…'
                                : label
                        }
                    }
                },
                y: {
                    grid: {
                        color: props.theme === 'dark' ? 'rgba(200, 200, 200, 0.1)' : 'rgba(120, 120, 120, 0.1)'
                    },
                    beginAtZero: true,
                    ticks: {
                        color: props.theme === 'dark' ? 'whitesmoke' : 'rgba(0, 0, 0, 0.7)'
                    }
                }
            }
        }
    })
}

onMounted(() => {
    updateChart()
})

onBeforeUnmount(() => {
    chartInstance?.destroy()
})
</script>

<template>
    <div style="width: 100%; height: 300px;">
        <canvas ref="canvasRef" />
    </div>
</template>
