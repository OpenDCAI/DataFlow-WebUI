<template>
    <baseDrawer v-model="thisValue" :title="title" length="400px" theme="light">
        <template v-slot:content>
            <fv-pivot
                v-model="choosenPivot"
                class="pivot-panel"
                :items="pivotItems"
                :tab="true"
                :fontSize="12"
                background="rgba(255, 255, 255, 1)"
                :sliderBackground="gradient"
                :borderRadius="'8px'"
                padding="0px 5px"
                itemPadding="0px 10px"
                sliderBorderRadius="12px"
            ></fv-pivot>
            <hr />
            <fv-text-box
                :placeholder="local('Search Operators ...')"
                icon="Search"
                class="operator-search-box"
                :revealBorder="true"
                borderRadius="30"
                borderWidth="2"
                :isBoxShadow="true"
                :focusBorderColor="color"
                :revealBorderColor="'rgba(103, 105, 251, 0.6)'"
                :reveal-background-color="['rgba(103, 105, 251, 0.1)', 'rgba(103, 105, 251, 0.6)']"
                @debounce-input="searchText = $event"
            ></fv-text-box>
            <div v-show="searchText" class="search-result-info">
                {{ local('Total') }}: {{ totalNumVisible }} {{ local('operators') }}
                <p class="search-text">"{{ searchText }}"</p>
            </div>
            <hr />
            <div class="panel-operator-content-block">
                <fv-expander
                    v-show="getGroupVisibleLength(key) > 0"
                    v-model="val.expand"
                    v-for="(val, key) in groupOperators"
                    :key="key"
                    class="dataset-item"
                    :title="val.name"
                    :maxHeight="'auto'"
                    background="rgba(255, 255, 255, 1)"
                    expandBackground="rgba(250, 250, 250, 1)"
                >
                    <template v-slot:content>
                        <div class="expander-row-block">
                            <i class="ms-Icon ms-Icon--OEM"></i>
                            <div class="expander-title">{{ val.name }}</div>
                        </div>
                    </template>
                    <div class="collapse-item-content">
                        <listBaseNode
                            v-show="op.show"
                            draggable="true"
                            v-for="(op, opKey) in val.items"
                            :key="opKey"
                            :data="op"
                            style="width: 100%"
                            @dragstart="dragStart($event, op)"
                        >
                            <mdTextBlock
                                class="expander-desc"
                                :modelValue="op.description"
                                style="width: 100%"
                            ></mdTextBlock>
                        </listBaseNode>
                    </div>
                    <template v-slot:extension>
                        <div class="expander-extension-info">
                            {{ numSamples(val) }}
                        </div>
                    </template>
                </fv-expander>
            </div>
        </template>
        <template v-slot:control="{ close }">
            <fv-button
                :borderRadius="8"
                :isBoxShadow="true"
                style="width: 120px; margin-right: 8px"
                @click="close"
                >{{ local('Close') }}</fv-button
            >
        </template>
    </baseDrawer>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'

import baseDrawer from '@/components/general/baseDrawer.vue'
import listBaseNode from '@/components/manage/mainFlow/listNodes/listBaseNode.vue'
import mdTextBlock from '@/components/general/mdTextBlock.vue'

import databaseIcon from '@/assets/flow/database.svg'

export default {
    components: {
        baseDrawer,
        listBaseNode,
        mdTextBlock
    },
    props: {
        modelValue: {
            default: false
        },
        title: {
            default: 'Database'
        }
    },
    data() {
        return {
            thisValue: this.modelValue,
            operators: [],
            groupOperators: {},
            searchText: '',
            choosenPivot: null,
            pivotItems: [
                {
                    key: 'all',
                    name: () => this.local('All')
                },
                {
                    key: 'parser',
                    name: () => this.local('Parser'),
                    show: false
                },
                {
                    key: 'filter',
                    name: () => this.local('Filter')
                },
                {
                    key: 'generate',
                    name: () => this.local('Generate')
                },
                {
                    key: 'eval',
                    name: () => this.local('Evaluate')
                },
                {
                    key: 'refine',
                    name: () => this.local('Refine')
                }
            ],
            styleDict: {
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
            },
            img: {
                database: databaseIcon
            }
        }
    },
    watch: {
        modelValue(val) {
            this.thisValue = val
            if (val) {
                this.getOperators()
            }
        },
        thisValue(val) {
            this.$emit('update:modelValue', val)
        },
        searchText() {
            this.filterValues()
        },
        choosenPivot() {
            this.filterValues()
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['color', 'gradient']),
        numSamples() {
            // 用于显示每个分组下的可见算子数量
            return (item) => {
                if (item && item.items) {
                    let length = this.getGroupVisibleLength(item.key)

                    return `${this.local('Total')}: ${length} ${this.local('operators')}`
                }
                return `${this.local('Total')}: 0 ${this.local('operators')}`
            }
        },
        totalNumVisible() {
            // 计算所有分组下可见算子的总数
            let result = 0
            for (let groupKey in this.groupOperators) {
                result += this.getGroupVisibleLength(groupKey)
            }
            return result
        }
    },
    mounted() {
        this.getOperators()
    },
    methods: {
        async getOperators() {
            this.$api.operators.list_operators().then((res) => {
                if (res.success) {
                    this.operators = res.data
                    for (let operator of this.operators) {
                        let styleKey = operator.type.level_2
                        if (!this.styleDict[styleKey]) {
                            styleKey = 'default'
                        }
                        operator = {
                            status: this.getKeyText(operator.type.level_2),
                            statusColor: this.styleDict[styleKey].statusColor,
                            label: operator.name,
                            icon: this.styleDict[styleKey].icon,
                            iconColor: this.styleDict[styleKey].iconColor,
                            iconBackground: this.styleDict[styleKey].iconBackground,
                            borderColor: this.styleDict[styleKey].borderColor,
                            shadowColor: 'rgba(0, 0, 0, 0.05)',
                            nodeShadowColor: this.styleDict[styleKey].shadowColor,
                            enableDelete: false,
                            show: true,
                            ...operator
                        }

                        if (this.groupOperators[operator.type.level_1]) {
                            this.groupOperators[operator.type.level_1].items.push(operator)
                        } else {
                            this.groupOperators[operator.type.level_1] = {
                                key: operator.type.level_1,
                                name: this.getKeyText(operator.type.level_1),
                                items: [operator],
                                expand: true
                            }
                        }
                    }
                } else {
                    this.$barWarning(res.message, {
                        status: 'warning'
                    })
                }
            })
        },
        filterValues() {
            for (let groupKey in this.groupOperators) {
                let group = this.groupOperators[groupKey]
                for (let operator of group.items) {
                    let show = true
                    if (!this.isSearchShowItem(operator)) show = false
                    if (
                        this.choosenPivot.key !== 'all' &&
                        this.choosenPivot.key.indexOf(operator.type.level_2) === -1
                    )
                        show = false
                    operator.show = show
                }
            }
        },
        getGroupVisibleLength(groupKey) {
            if (!this.groupOperators[groupKey]) return 0
            return this.groupOperators[groupKey].items.filter((item) => item.show).length
        },
        getKeyText(text) {
            let splitText = text.split('_')
            return splitText.map((word) => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
        },
        isSearchShowItem(item) {
            let searchText = this.searchText.toLowerCase()
            return (
                item.label.toLowerCase().includes(searchText) ||
                item.status.toLowerCase().includes(searchText) ||
                item.type.level_2.toLowerCase().includes(searchText) ||
                item.type.level_1.toLowerCase().includes(searchText) ||
                item.description.toLowerCase().includes(searchText)
            )
        },
        dragStart(event, item) {
            if (event.dataTransfer) {
                event.dataTransfer.setData('application/vueflow', JSON.stringify(item))
                event.dataTransfer.setData('event/offsetX', event.offsetX)
            }
        }
    }
}
</script>

<style lang="scss">
.pivot-panel {
    height: 30px;
    flex-shrink: 0;
}
.operator-search-box {
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
.panel-operator-content-block {
    --node-status-color: rgba(128, 128, 128, 1);

    position: relative;
    width: 100%;
    height: 100%;
    gap: 5px;
    display: flex;
    flex-direction: column;
    overflow: overlay;

    .expander-row-block {
        @include Vcenter;

        gap: 5px;
    }

    .expander-extension-info {
        font-size: 10px;
        font-weight: 400;
        color: var(--node-status-color);
    }

    .dataset-item {
        flex-shrink: 0;

        .collapse-item-content {
            position: relative;
            height: auto;
            gap: 5px;
            display: flex;
            flex-direction: column;
            transition: all 0.1s;

            .expander-desc {
                position: relative;
                width: 100%;
                height: auto;
                padding: 5px 15px 15px 15px;
                font-size: 13px;

                ul,
                ol {
                    padding-left: 20px;
                }
            }
        }
    }
}
</style>
