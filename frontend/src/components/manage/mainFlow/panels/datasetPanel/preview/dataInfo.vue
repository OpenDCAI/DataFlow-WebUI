<template>
    <div class="collapse-item-content">
        <hr />
        <div v-if="item.pipeline" class="bp-row column">
            <p class="bp-title">{{ local('Pipeline') }}</p>
            <p class="bp-bold-info">{{ item.pipeline }}</p>
        </div>
        <hr v-if="item.pipeline" />
        <div class="bp-row column">
            <p class="bp-light-title">{{ local('ID') }}</p>
            <p class="bp-std-info">{{ item.id }}</p>
        </div>
        <hr />
        <div v-if="item.root" class="bp-row column">
            <p class="bp-light-title">{{ local('Root') }}</p>
            <p class="bp-std-info">{{ item.root }}</p>
        </div>
        <hr v-if="item.root" />
        <div v-if="item.hash" class="bp-row column">
            <p class="bp-light-title">{{ local('Hash') }}</p>
            <p class="bp-std-info">{{ item.hash }}</p>
        </div>
        <hr v-if="item.hash" />
        <div v-if="item.file_name" class="bp-row column">
            <p class="bp-light-title">{{ local('File Name') }}</p>
            <p class="bp-std-info">{{ item.file_name }}</p>
        </div>
        <hr v-if="item.file_name" />
        <div v-if="item.uploaded_at" class="bp-row column">
            <p class="bp-light-title">{{ local('Uploaded At') }}</p>
            <p class="bp-std-info">{{ item.uploaded_at }}</p>
        </div>

        <!-- Distribution Chart Section -->
        <template v-if="columns.length || loadingChart">
            <hr />
            <div class="dist-section">
                <div class="dist-header">
                    <p class="bp-title">{{ local('Distribution') }}</p>
                    <div v-if="loadingChart" class="dist-loading">
                        <i class="ms-Icon ms-Icon--ProgressRingDots"></i>
                    </div>
                    <div v-if="columns.length" class="col-tabs">
                        <span v-for="col in columns" :key="col" class="col-tab"
                            :class="{ active: selectedCol === col, dark: theme === 'dark' }"
                            @click="selectedCol = col">
                            {{ col }}
                        </span>
                    </div>
                </div>
                <div v-show="columns.length" class="dist-chart-container">
                    <canvas ref="chartCanvas"></canvas>
                </div>
            </div>
        </template>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import {
    Chart,
    BarController,
    BarElement,
    CategoryScale,
    LinearScale,
    Tooltip
} from 'chart.js'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip)

export default {
    props: {
        item: {
            type: Object,
            default: () => ({})
        }
    },
    data() {
        return {
            columns: [],
            selectedCol: '',
            previewData: [],
            loadingChart: false,
            chartInstance: null
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme']),
        distribution() {
            if (!this.selectedCol || !this.previewData.length) return { labels: [], values: [] }
            const freq = {}
            for (const row of this.previewData) {
                const raw = row[this.selectedCol]
                const val = raw === null || raw === undefined
                    ? '(null)'
                    : typeof raw === 'object'
                        ? JSON.stringify(raw)
                        : String(raw)
                const key = val.length > 40 ? val.slice(0, 40) + '…' : val
                freq[key] = (freq[key] || 0) + 1
            }
            const sorted = Object.entries(freq)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 10)
            return {
                labels: sorted.map(([k]) => k),
                values: sorted.map(([, v]) => v)
            }
        }
    },
    watch: {
        selectedCol() {
            this.$nextTick(() => this.renderChart())
        },
        theme() {
            this.$nextTick(() => this.renderChart())
        },
        columns(val) {
            if (val.length) {
                this.$nextTick(() => this.renderChart())
            }
        }
    },
    mounted() {
        this.fetchPreview()
    },
    beforeUnmount() {
        this.chartInstance?.destroy()
    },
    methods: {
        fetchPreview() {
            if (!this.item.id) return
            this.loadingChart = true
            this.$api.datasets
                .get_dataset_preview(this.item.id, 100)
                .then((res) => {
                    this.loadingChart = false
                    if (res.code === 200 && Array.isArray(res.data) && res.data.length) {
                        this.previewData = res.data
                        this.columns = Object.keys(res.data[0])
                        this.selectedCol = this.columns[0] || ''
                    }
                })
                .catch(() => {
                    this.loadingChart = false
                })
        },
        renderChart() {
            if (!this.$refs.chartCanvas || !this.selectedCol) return
            this.chartInstance?.destroy()
            const { labels, values } = this.distribution
            if (!labels.length) return

            const isDark = this.theme === 'dark'
            const gridColor = isDark
                ? 'rgba(200, 200, 200, 0.1)'
                : 'rgba(120, 120, 120, 0.1)'
            const tickColor = isDark ? 'rgba(245, 245, 245, 0.85)' : 'rgba(0, 0, 0, 0.7)'

            this.chartInstance = new Chart(this.$refs.chartCanvas, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [
                        {
                            data: values,
                            backgroundColor: labels.map(
                                (_, i) => `hsla(${(i * 47) % 360}, 70%, 55%, 0.5)`
                            ),
                            borderColor: labels.map(
                                (_, i) => `hsla(${(i * 47) % 360}, 70%, 45%, 0.8)`
                            ),
                            borderWidth: 1,
                            borderRadius: 4,
                            barThickness: 16
                        }
                    ]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ` Count: ${ctx.parsed.x}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            grid: { color: gridColor },
                            ticks: { color: tickColor, precision: 0 }
                        },
                        y: {
                            grid: { display: false },
                            ticks: {
                                color: tickColor,
                                callback(value) {
                                    const label = this.getLabelForValue(value)
                                    return label.length > 20
                                        ? label.slice(0, 20) + '…'
                                        : label
                                }
                            }
                        }
                    }
                }
            })
        }
    }
}
</script>

<style lang="scss">
.collapse-item-content {
    .dist-section {
        position: relative;
        width: 100%;
        padding: 0 5px;
        box-sizing: border-box;

        .dist-header {
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 6px;
            margin-bottom: 8px;

            .bp-title {
                margin-right: 4px;
                flex-shrink: 0;
            }

            .dist-loading {
                font-size: 14px;
                color: rgba(120, 120, 120, 0.7);

                .ms-Icon {
                    animation: spin 1s linear infinite;
                }
            }

            .col-tabs {
                display: flex;
                flex-wrap: wrap;
                gap: 4px;

                .col-tab {
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                    cursor: pointer;
                    user-select: none;
                    background: rgba(120, 120, 120, 0.08);
                    color: rgba(0, 0, 0, 0.6);
                    border: 1px solid rgba(120, 120, 120, 0.15);
                    transition: all 0.15s;

                    &:hover {
                        background: rgba(69, 98, 213, 0.12);
                        color: rgba(69, 98, 213, 0.9);
                    }

                    &.active {
                        background: rgba(69, 98, 213, 0.15);
                        color: rgba(69, 98, 213, 1);
                        border-color: rgba(69, 98, 213, 0.4);
                        font-weight: 600;
                    }

                    &.dark {
                        color: rgba(245, 245, 245, 0.6);
                        background: rgba(200, 200, 200, 0.08);
                        border-color: rgba(200, 200, 200, 0.15);

                        &:hover {
                            background: rgba(100, 120, 220, 0.2);
                            color: rgba(160, 180, 255, 0.9);
                        }

                        &.active {
                            background: rgba(100, 120, 220, 0.25);
                            color: rgba(160, 180, 255, 1);
                            border-color: rgba(100, 120, 220, 0.5);
                        }
                    }
                }
            }
        }

        .dist-chart-container {
            width: 100%;
            height: 220px;
        }
    }
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
</style>
