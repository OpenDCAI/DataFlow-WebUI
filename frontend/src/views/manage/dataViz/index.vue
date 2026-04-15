<template>
    <div class="df-dataviz-container" :class="[{ dark: theme === 'dark' }]">
        <div class="major-container">
            <div class="title-block">
                <p class="main-title">{{ local('Data Visualization') }}</p>
                <p class="sub-title">{{ local('Explore and analyze your datasets') }}</p>
            </div>
            
            <div class="content-block">
                <!-- Dataset Selector Section -->
                <div class="selector-section">
                    <div class="selector-row">
                        <div class="selector-item">
                            <p class="selector-label">{{ local('Select Dataset') }}</p>
                            <fv-combobox :theme="theme" v-model="selectedDataset" :options="datasetOptions"
                                :placeholder="local('Choose a dataset')" :border-radius="6"
                                :input-background="theme === 'dark' ? 'rgba(40, 40, 40, 1)' : 'rgba(252, 252, 252, 1)'"
                                @change="handleDatasetChange">
                            </fv-combobox>
                        </div>
                        
                        <div class="selector-item">
                            <p class="selector-label">{{ local('Preview Rows') }}</p>
                            <fv-spin-button :theme="theme" v-model="rowCount" :minimum="1" :maximum="100"
                                :border-radius="6" :is-box-shadow="true">
                            </fv-spin-button>
                        </div>

                        <div class="selector-item">
                            <p class="selector-label">{{ local('View Type') }}</p>
                            <fv-combobox :theme="theme" v-model="viewType" :options="viewTypeOptions"
                                :placeholder="local('Select view type')" :border-radius="6"
                                :input-background="theme === 'dark' ? 'rgba(40, 40, 40, 1)' : 'rgba(252, 252, 252, 1)'"
                                @change="handleViewTypeChange">
                            </fv-combobox>
                        </div>
                    </div>

                    <div class="selector-actions">
                        <fv-button :theme="theme" :is-box-shadow="true" border-radius="6" 
                            :disabled="!selectedDataset || loading" @click="loadDatasetPreview">
                            {{ loading ? local('Loading...') : local('Load Data') }}
                        </fv-button>
                        <fv-button v-if="selectedDataset" :theme="theme" :is-box-shadow="true" border-radius="6"
                            :disabled="loading" @click="exportData">
                            {{ local('Export') }}
                        </fv-button>
                    </div>
                </div>

                <!-- Loading State -->
                <div v-if="loading" class="loading-container">
                    <i class="ms-Icon ms-Icon--ProgressRingDots"></i>
                    <p>{{ local('Loading dataset...') }}</p>
                </div>

                <!-- Content Views -->
                <template v-else-if="selectedDataset && previewData.length">
                    <!-- Table View -->
                    <div v-if="viewType.key === 'table'" class="view-section">
                        <div class="section-header">
                            <p class="section-title">{{ local('Data Table') }}</p>
                            <span class="data-info">{{ previewData.length }} {{ local('rows') }}, {{ columns.length }} {{ local('columns') }}</span>
                        </div>
                        <div class="table-container">
                            <table class="data-table" :class="[{ dark: theme === 'dark' }]">
                                <thead>
                                    <tr>
                                        <th v-for="col in columns" :key="col" class="table-header">{{ col }}</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr v-for="(row, rowIdx) in previewData" :key="rowIdx" :class="{ 'alt-row': rowIdx % 2 === 1 }">
                                        <td v-for="col in columns" :key="col" class="table-cell">
                                            {{ formatCellValue(row[col]) }}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                    <!-- Distribution View -->
                    <div v-else-if="viewType.key === 'distribution'" class="view-section">
                        <div class="section-header">
                            <p class="section-title">{{ local('Value Distribution') }}</p>
                            <div v-if="columns.length" class="column-selector">
                                <span class="label">{{ local('Column') }}:</span>
                                <select v-model="selectedColumn" class="column-select" :class="[{ dark: theme === 'dark' }]">
                                    <option v-for="col in columns" :key="col" :value="col">{{ col }}</option>
                                </select>
                            </div>
                        </div>
                        <div class="chart-container">
                            <canvas ref="chartCanvas"></canvas>
                        </div>
                    </div>

                    <!-- Statistics View -->
                    <div v-else-if="viewType.key === 'statistics'" class="view-section">
                        <div class="section-header">
                            <p class="section-title">{{ local('Dataset Statistics') }}</p>
                        </div>
                        <div class="stats-grid">
                            <div class="stat-card" :class="[{ dark: theme === 'dark' }]">
                                <p class="stat-label">{{ local('Total Rows') }}</p>
                                <p class="stat-value">{{ previewData.length }}</p>
                            </div>
                            <div class="stat-card" :class="[{ dark: theme === 'dark' }]">
                                <p class="stat-label">{{ local('Total Columns') }}</p>
                                <p class="stat-value">{{ columns.length }}</p>
                            </div>
                            <div class="stat-card" :class="[{ dark: theme === 'dark' }]">
                                <p class="stat-label">{{ local('Memory Usage') }}</p>
                                <p class="stat-value">{{ formatBytes(estimateMemoryUsage()) }}</p>
                            </div>
                            <div class="stat-card" :class="[{ dark: theme === 'dark' }]">
                                <p class="stat-label">{{ local('Data Types') }}</p>
                                <p class="stat-value">{{ uniqueDataTypes }}</p>
                            </div>
                        </div>

                        <!-- Column Statistics -->
                        <div class="columns-stats">
                            <p class="columns-title">{{ local('Column Details') }}</p>
                            <div class="columns-list">
                                <div v-for="(col, idx) in columns" :key="idx" class="column-stat">
                                    <div class="col-name">{{ col }}</div>
                                    <div class="col-type">{{ getColumnType(col) }}</div>
                                    <div class="col-stats">
                                        <span class="stat-badge">{{ countMissingValues(col) }} {{ local('missing') }}</span>
                                        <span class="stat-badge" v-if="getColumnStats(col)">{{ getColumnStats(col) }}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Null Values View -->
                    <div v-else-if="viewType.key === 'nulls'" class="view-section">
                        <div class="section-header">
                            <p class="section-title">{{ local('Missing Values Analysis') }}</p>
                        </div>
                        <div class="null-chart-container">
                            <canvas ref="nullChartCanvas"></canvas>
                        </div>
                        <div class="null-details">
                            <div v-for="(count, col) in nullCounts" :key="col" class="null-detail-row">
                                <span class="col-name">{{ col }}</span>
                                <span class="null-count">{{ count }} / {{ previewData.length }}</span>
                                <div class="null-bar">
                                    <div class="null-fill" :style="{ width: ((count / previewData.length) * 100) + '%' }"></div>
                                </div>
                                <span class="null-percent">{{ ((count / previewData.length) * 100).toFixed(1) }}%</span>
                            </div>
                        </div>
                    </div>
                </template>

                <!-- Empty State -->
                <div v-else-if="!loading" class="empty-state">
                    <i class="ms-Icon ms-Icon--Info"></i>
                    <p>{{ local('Select a dataset and click Load Data to begin visualization') }}</p>
                </div>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import axios from 'axios'
import {
    Chart,
    BarController,
    BarElement,
    CategoryScale,
    LinearScale,
    Tooltip,
    Legend
} from 'chart.js'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

export default {
    data() {
        return {
            datasets: [],
            selectedDataset: {},
            selectedColumn: '',
            previewData: [],
            loading: false,
            rowCount: 10,
            viewType: { key: 'table', text: 'Table' },
            viewTypeOptions: [
                { key: 'table', text: 'Table' },
                { key: 'distribution', text: 'Distribution' },
                { key: 'statistics', text: 'Statistics' },
                { key: 'nulls', text: 'Missing Values' }
            ],
            chartInstance: null,
            nullChartInstance: null,
            columns: [],
            nullCounts: {}
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme']),
        datasetOptions() {
            return this.datasets.map(ds => ({
                key: ds.id,
                text: `${ds.id} (${ds.num_samples} rows)`
            }))
        },
        uniqueDataTypes() {
            const types = new Set()
            this.columns.forEach(col => {
                types.add(this.getColumnType(col))
            })
            return types.size
        }
    },
    watch: {
        selectedColumn() {
            this.$nextTick(() => {
                if (this.viewType.key === 'distribution') {
                    this.renderDistributionChart()
                }
            })
        },
        theme() {
            this.$nextTick(() => {
                if (this.viewType.key === 'distribution') {
                    this.renderDistributionChart()
                }
                if (this.viewType.key === 'nulls') {
                    this.renderNullChart()
                }
            })
        }
    },
    mounted() {
        this.loadDatasets()
    },
    beforeUnmount() {
        this.chartInstance?.destroy()
        this.nullChartInstance?.destroy()
    },
    methods: {
        loadDatasets() {
            this.$api.datasets.list_datasets().then((res) => {
                if (res.code === 200) {
                    this.datasets = res.data || []
                }
            }).catch((err) => {
                console.error('Failed to load datasets', err)
            })
        },
        handleDatasetChange() {
            this.previewData = []
            this.columns = []
            this.selectedColumn = ''
            this.nullCounts = {}
        },
        handleViewTypeChange() {
            this.$nextTick(() => {
                if (this.viewType.key === 'distribution') {
                    this.renderDistributionChart()
                } else if (this.viewType.key === 'nulls') {
                    this.renderNullChart()
                }
            })
        },
        loadDatasetPreview() {
            if (!this.selectedDataset || !this.selectedDataset.key) return
            
            this.loading = true
            this.$api.datasets
                .get_dataset_preview(this.selectedDataset.key, this.rowCount)
                .then((res) => {
                    if (res.code === 200 && Array.isArray(res.data) && res.data.length) {
                        this.previewData = res.data
                        this.columns = Object.keys(res.data[0])
                        this.selectedColumn = this.columns[0]
                        this.calculateNullCounts()
                        
                        this.$nextTick(() => {
                            if (this.viewType.key === 'distribution') {
                                this.renderDistributionChart()
                            } else if (this.viewType.key === 'nulls') {
                                this.renderNullChart()
                            }
                        })
                    }
                })
                .catch((err) => {
                    this.$barWarning({ status: 'error', title: this.local('Failed to load dataset') })
                    console.error(err)
                })
                .finally(() => {
                    this.loading = false
                })
        },
        calculateNullCounts() {
            this.nullCounts = {}
            this.columns.forEach(col => {
                let count = 0
                this.previewData.forEach(row => {
                    if (row[col] === null || row[col] === undefined || row[col] === '') {
                        count++
                    }
                })
                this.nullCounts[col] = count
            })
        },
        renderDistributionChart() {
            if (!this.$refs.chartCanvas || !this.selectedColumn || !this.previewData.length) return
            
            this.chartInstance?.destroy()
            
            const freq = {}
            this.previewData.forEach(row => {
                const raw = row[this.selectedColumn]
                const val = raw === null || raw === undefined
                    ? '(null)'
                    : typeof raw === 'object'
                        ? JSON.stringify(raw)
                        : String(raw)
                const key = val.length > 40 ? val.slice(0, 40) + '…' : val
                freq[key] = (freq[key] || 0) + 1
            })
            
            const sorted = Object.entries(freq)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 15)
            
            const labels = sorted.map(([k]) => k)
            const values = sorted.map(([, v]) => v)
            
            const isDark = this.theme === 'dark'
            const gridColor = isDark
                ? 'rgba(200, 200, 200, 0.1)'
                : 'rgba(120, 120, 120, 0.1)'
            const tickColor = isDark ? 'rgba(245, 245, 245, 0.85)' : 'rgba(0, 0, 0, 0.7)'
            
            this.chartInstance = new Chart(this.$refs.chartCanvas, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: this.local('Frequency'),
                        data: values,
                        backgroundColor: labels.map(
                            (_, i) => `hsla(${(i * 47) % 360}, 70%, 55%, 0.7)`
                        ),
                        borderColor: labels.map(
                            (_, i) => `hsla(${(i * 47) % 360}, 70%, 45%, 0.9)`
                        ),
                        borderWidth: 1,
                        borderRadius: 4,
                        barThickness: 24
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: true },
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
                                    return label.length > 25 ? label.slice(0, 25) + '…' : label
                                }
                            }
                        }
                    }
                }
            })
        },
        renderNullChart() {
            if (!this.$refs.nullChartCanvas || !this.columns.length) return
            
            this.nullChartInstance?.destroy()
            
            const labels = this.columns
            const data = labels.map(col => this.nullCounts[col] || 0)
            
            const isDark = this.theme === 'dark'
            const gridColor = isDark
                ? 'rgba(200, 200, 200, 0.1)'
                : 'rgba(120, 120, 120, 0.1)'
            const tickColor = isDark ? 'rgba(245, 245, 245, 0.85)' : 'rgba(0, 0, 0, 0.7)'
            
            this.nullChartInstance = new Chart(this.$refs.nullChartCanvas, {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: this.local('Missing Values'),
                        data,
                        backgroundColor: 'rgba(191, 95, 95, 0.7)',
                        borderColor: 'rgba(191, 95, 95, 0.9)',
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'x',
                    plugins: {
                        legend: { display: true }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: gridColor },
                            ticks: { color: tickColor, precision: 0 }
                        },
                        x: {
                            grid: { display: false },
                            ticks: {
                                color: tickColor
                            }
                        }
                    }
                }
            })
        },
        getColumnType(col) {
            if (!this.previewData.length) return 'unknown'
            
            const sample = this.previewData[0][col]
            if (sample === null || sample === undefined) {
                for (let row of this.previewData) {
                    if (row[col] !== null && row[col] !== undefined) {
                        return typeof row[col]
                    }
                }
                return 'null'
            }
            
            const type = typeof sample
            if (type === 'number') return 'number'
            if (type === 'boolean') return 'boolean'
            if (Array.isArray(sample)) return 'array'
            if (type === 'object') return 'object'
            return 'string'
        },
        countMissingValues(col) {
            return this.nullCounts[col] || 0
        },
        getColumnStats(col) {
            const type = this.getColumnType(col)
            const missing = this.countMissingValues(col)
            
            if (type === 'number') {
                const values = this.previewData
                    .map(row => row[col])
                    .filter(v => v !== null && v !== undefined)
                    .map(v => Number(v))
                
                if (values.length) {
                    const min = Math.min(...values)
                    const max = Math.max(...values)
                    const avg = (values.reduce((a, b) => a + b, 0) / values.length).toFixed(2)
                    return `min: ${min}, max: ${max}, avg: ${avg}`
                }
            }
            
            return null
        },
        formatCellValue(value) {
            if (value === null || value === undefined) return '(null)'
            if (typeof value === 'object') return JSON.stringify(value)
            if (typeof value === 'string' && value.length > 50) {
                return value.slice(0, 50) + '…'
            }
            return String(value)
        },
        formatBytes(bytes) {
            if (bytes === 0) return '0 B'
            const k = 1024
            const sizes = ['B', 'KB', 'MB', 'GB']
            const i = Math.floor(Math.log(bytes) / Math.log(k))
            return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
        },
        estimateMemoryUsage() {
            let total = 0
            this.previewData.forEach(row => {
                Object.values(row).forEach(val => {
                    if (typeof val === 'string') {
                        total += val.length * 2
                    } else if (typeof val === 'number') {
                        total += 8
                    } else if (typeof val === 'boolean') {
                        total += 4
                    } else if (val !== null && val !== undefined) {
                        total += JSON.stringify(val).length
                    }
                })
            })
            return total
        },
        exportData() {
            if (!this.previewData.length) return
            
            const csv = [
                this.columns.join(','),
                ...this.previewData.map(row =>
                    this.columns.map(col => {
                        const val = row[col]
                        if (val === null || val === undefined) return ''
                        if (typeof val === 'string' && val.includes(',')) {
                            return `"${val.replace(/"/g, '""')}"`
                        }
                        return val
                    }).join(',')
                )
            ].join('\n')
            
            const blob = new Blob([csv], { type: 'text/csv' })
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `${this.selectedDataset.key}_preview.csv`
            a.click()
            window.URL.revokeObjectURL(url)
        }
    }
}
</script>

<style lang="scss" scoped>
.df-dataviz-container {
    @include app;
    background: rgba(250, 250, 250, 1);
    display: flex;
    flex-direction: column;

    &.dark {
        background: rgba(36, 36, 36, 1);

        .major-container {
            .title-block {
                .main-title {
                    color: whitesmoke;
                }
                .sub-title {
                    color: rgba(180, 180, 180, 1);
                }
            }

            .content-block {
                .selector-section {
                    background: rgba(45, 45, 45, 1);
                    border-color: rgba(70, 70, 70, 1);

                    .selector-label {
                        color: rgba(200, 200, 200, 1);
                    }
                }

                .loading-container {
                    color: rgba(200, 200, 200, 1);
                }

                .empty-state {
                    color: rgba(150, 150, 150, 1);
                }

                .view-section {
                    .section-header {
                        .section-title {
                            color: whitesmoke;
                        }
                        .data-info {
                            color: rgba(150, 150, 150, 1);
                        }
                    }

                    .table-container {
                        .data-table {
                            &.dark {
                                background: rgba(40, 40, 40, 1);
                                border-color: rgba(70, 70, 70, 1);

                                thead tr {
                                    background: rgba(50, 50, 50, 1);
                                    border-color: rgba(70, 70, 70, 1);

                                    th {
                                        color: rgba(200, 200, 200, 1);
                                    }
                                }

                                tbody tr {
                                    border-color: rgba(70, 70, 70, 1);
                                    td {
                                        color: rgba(200, 200, 200, 1);
                                    }
                                    &.alt-row {
                                        background: rgba(45, 45, 45, 1);
                                    }
                                    &:hover {
                                        background: rgba(55, 55, 55, 1);
                                    }
                                }
                            }
                        }
                    }

                    .column-select {
                        background: rgba(40, 40, 40, 1);
                        color: rgba(200, 200, 200, 1);
                        border-color: rgba(70, 70, 70, 1);
                    }

                    .stats-grid {
                        .stat-card {
                            &.dark {
                                background: rgba(50, 50, 50, 1);
                                border-color: rgba(70, 70, 70, 1);

                                .stat-label {
                                    color: rgba(150, 150, 150, 1);
                                }
                                .stat-value {
                                    color: rgba(100, 200, 255, 1);
                                }
                            }
                        }
                    }

                    .columns-stats {
                        .columns-title {
                            color: whitesmoke;
                        }

                        .column-stat {
                            background: rgba(50, 50, 50, 1);
                            border-color: rgba(70, 70, 70, 1);

                            .col-name {
                                color: rgba(100, 200, 255, 1);
                            }
                            .col-type {
                                color: rgba(150, 150, 150, 1);
                            }
                            .stat-badge {
                                color: rgba(200, 200, 200, 1);
                                background: rgba(60, 60, 60, 1);
                            }
                        }
                    }

                    .null-details {
                        .null-detail-row {
                            .col-name {
                                color: rgba(200, 200, 200, 1);
                            }
                            .null-count {
                                color: rgba(150, 150, 150, 1);
                            }
                            .null-percent {
                                color: rgba(150, 150, 150, 1);
                            }
                            .null-bar {
                                background: rgba(60, 60, 60, 1);
                                .null-fill {
                                    background: rgba(191, 95, 95, 0.8);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    .major-container {
        position: relative;
        width: 100%;
        height: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        overflow: hidden;

        .title-block {
            position: relative;
            width: 100%;
            padding: 25px 30px;
            box-sizing: border-box;
            border-bottom: 1px solid rgba(200, 200, 200, 0.3);

            .main-title {
                margin: 0 0 5px 0;
                font-size: 28px;
                font-weight: 600;
                color: rgba(0, 0, 0, 1);
            }

            .sub-title {
                margin: 0;
                font-size: 14px;
                color: rgba(120, 120, 120, 1);
            }
        }

        .content-block {
            position: relative;
            width: 100%;
            flex: 1;
            box-sizing: border-box;
            padding: 20px 30px;
            overflow-y: auto;
            overflow-x: hidden;

            .selector-section {
                position: relative;
                background: rgba(245, 245, 245, 1);
                border: 1px solid rgba(200, 200, 200, 0.3);
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-sizing: border-box;

                .selector-row {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 15px;

                    .selector-item {
                        display: flex;
                        flex-direction: column;

                        .selector-label {
                            font-size: 13px;
                            font-weight: 500;
                            color: rgba(100, 100, 100, 1);
                            margin-bottom: 8px;
                        }
                    }
                }

                .selector-actions {
                    display: flex;
                    gap: 10px;
                    padding-top: 10px;
                    border-top: 1px solid rgba(200, 200, 200, 0.2);
                }
            }

            .loading-container {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 60px 20px;
                color: rgba(120, 120, 120, 1);

                i {
                    font-size: 48px;
                    margin-bottom: 15px;
                    animation: spin 1s linear infinite;
                }

                p {
                    font-size: 16px;
                    margin: 0;
                }
            }

            .empty-state {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 100px 20px;
                color: rgba(120, 120, 120, 1);
                text-align: center;

                i {
                    font-size: 64px;
                    margin-bottom: 15px;
                }

                p {
                    font-size: 16px;
                    margin: 0;
                }
            }

            .view-section {
                margin-bottom: 20px;
                background: rgba(248, 248, 248, 1);
                border: 1px solid rgba(200, 200, 200, 0.3);
                border-radius: 8px;
                padding: 20px;
                box-sizing: border-box;

                .section-header {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    margin-bottom: 15px;
                    padding-bottom: 10px;
                    border-bottom: 1px solid rgba(200, 200, 200, 0.2);

                    .section-title {
                        margin: 0;
                        font-size: 18px;
                        font-weight: 600;
                        color: rgba(0, 0, 0, 1);
                    }

                    .data-info {
                        font-size: 13px;
                        color: rgba(120, 120, 120, 1);
                    }

                    .column-selector {
                        display: flex;
                        align-items: center;
                        gap: 10px;

                        .label {
                            font-size: 13px;
                            color: rgba(100, 100, 100, 1);
                            font-weight: 500;
                        }

                        .column-select {
                            padding: 6px 10px;
                            border: 1px solid rgba(200, 200, 200, 0.3);
                            border-radius: 4px;
                            font-size: 13px;
                            background: white;
                            color: rgba(0, 0, 0, 1);
                            cursor: pointer;

                            &:focus {
                                outline: none;
                                border-color: rgba(69, 98, 213, 0.5);
                            }
                        }
                    }
                }

                .table-container {
                    width: 100%;
                    overflow-x: auto;

                    .data-table {
                        width: 100%;
                        border-collapse: collapse;
                        font-size: 13px;
                        background: white;
                        border: 1px solid rgba(200, 200, 200, 0.3);

                        thead tr {
                            background: rgba(245, 245, 245, 1);
                            border-bottom: 1px solid rgba(200, 200, 200, 0.3);

                            th {
                                padding: 12px 10px;
                                text-align: left;
                                font-weight: 600;
                                color: rgba(0, 0, 0, 1);
                                white-space: nowrap;
                            }
                        }

                        tbody tr {
                            border-bottom: 1px solid rgba(200, 200, 200, 0.15);

                            td {
                                padding: 10px;
                                color: rgba(60, 60, 60, 1);
                                word-break: break-word;
                                max-width: 300px;
                            }

                            &.alt-row {
                                background: rgba(250, 250, 250, 1);
                            }

                            &:hover {
                                background: rgba(240, 245, 255, 1);
                            }
                        }
                    }
                }

                .chart-container {
                    width: 100%;
                    height: 400px;
                    position: relative;
                }

                .null-chart-container {
                    width: 100%;
                    height: 300px;
                    position: relative;
                    margin-bottom: 20px;
                }

                .stats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin-bottom: 25px;

                    .stat-card {
                        background: white;
                        border: 1px solid rgba(200, 200, 200, 0.3);
                        border-radius: 6px;
                        padding: 15px;
                        text-align: center;

                        .stat-label {
                            font-size: 12px;
                            color: rgba(120, 120, 120, 1);
                            margin: 0 0 8px 0;
                            font-weight: 500;
                        }

                        .stat-value {
                            font-size: 24px;
                            font-weight: 600;
                            color: rgba(69, 98, 213, 1);
                            margin: 0;
                        }
                    }
                }

                .columns-stats {
                    margin-top: 20px;

                    .columns-title {
                        font-size: 16px;
                        font-weight: 600;
                        color: rgba(0, 0, 0, 1);
                        margin: 0 0 15px 0;
                    }

                    .columns-list {
                        display: grid;
                        grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                        gap: 12px;

                        .column-stat {
                            background: white;
                            border: 1px solid rgba(200, 200, 200, 0.3);
                            border-radius: 6px;
                            padding: 12px;

                            .col-name {
                                font-size: 14px;
                                font-weight: 600;
                                color: rgba(69, 98, 213, 1);
                                margin: 0 0 4px 0;
                            }

                            .col-type {
                                font-size: 12px;
                                color: rgba(120, 120, 120, 1);
                                margin: 0 0 8px 0;
                            }

                            .col-stats {
                                display: flex;
                                flex-wrap: wrap;
                                gap: 6px;

                                .stat-badge {
                                    font-size: 11px;
                                    background: rgba(240, 240, 240, 1);
                                    color: rgba(80, 80, 80, 1);
                                    padding: 3px 8px;
                                    border-radius: 3px;
                                    white-space: nowrap;
                                }
                            }
                        }
                    }
                }

                .null-details {
                    margin-top: 15px;

                    .null-detail-row {
                        display: flex;
                        align-items: center;
                        gap: 12px;
                        padding: 8px 0;
                        font-size: 13px;

                        .col-name {
                            flex: 0 0 150px;
                            color: rgba(0, 0, 0, 1);
                            font-weight: 500;
                        }

                        .null-count {
                            flex: 0 0 60px;
                            text-align: right;
                            color: rgba(100, 100, 100, 1);
                        }

                        .null-bar {
                            flex: 1 1 auto;
                            height: 20px;
                            background: rgba(240, 240, 240, 1);
                            border-radius: 3px;
                            overflow: hidden;
                            min-width: 100px;

                            .null-fill {
                                height: 100%;
                                background: rgba(191, 95, 95, 0.7);
                                transition: width 0.3s ease;
                            }
                        }

                        .null-percent {
                            flex: 0 0 50px;
                            text-align: right;
                            color: rgba(100, 100, 100, 1);
                        }
                    }
                }
            }
        }
    }
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}
</style>
