<template>
    <div class="value-input">
        <fv-text-box
            v-if="computedUIType === 'text'"
            v-model="thisValue"
            :placeholder="local('Please input') + ` ${itemObj.name}`"
            font-size="12"
            border-radius="3"
            border-width="2"
            :reveal-border="true"
            :border-color="thisData.shadowColor"
            :focus-border-color="thisData.borderColor"
            underline
            style="width: 100%; height: 35px"
        ></fv-text-box>
        <fv-combobox
            v-if="computedUIType === 'llm_serving'"
            :model-value="computedServingItem(itemObj)"
            @update:modelValue="setServingItem(itemObj, $event)"
            :placeholder="local('Select Serving')"
            :options="servingList"
            :choosen-slider-background="thisData.borderColor"
            :reveal-background-color="[thisData.shadowColor, 'rgba(255, 255, 255, 1)']"
            :reveal-border-color="thisData.borderColor"
            border-radius="8"
            style="width: 100%"
        ></fv-combobox>
        <fv-combobox
            v-if="computedUIType === 'database_manager'"
            :model-value="computedDatabaseManagerItem(itemObj)"
            @update:modelValue="setDatabaseManagerItem(itemObj, $event)"
            :placeholder="local('Select Database Manager')"
            :options="dataManagerList"
            :choosen-slider-background="thisData.borderColor"
            :reveal-background-color="[thisData.shadowColor, 'rgba(255, 255, 255, 1)']"
            :reveal-border-color="thisData.borderColor"
            border-radius="8"
            style="width: 100%"
        ></fv-combobox>
    </div>
</template>

<script>
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'
import { mapState } from 'pinia'

export default {
    props: {
        modelValue: {
            default: ''
        },
        itemObj: {
            type: Object,
            default: () => ({})
        },
        thisData: {
            type: Object,
            default: () => ({})
        }
    },
    data() {
        return {
            thisValue: this.modelValue
        }
    },
    watch: {
        modelValue() {
            this.thisValue = this.modelValue
        },
        thisValue() {
            this.$emit('update:modelValue', this.thisValue)
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useDataflow, ['servingList', 'currentServing', 'dataManagerList']),
        computedUIType() {
            if (this.itemObj.name === 'llm_serving') {
                return 'llm_serving'
            }
            if (this.itemObj.name === 'database_manager') {
                return 'database_manager'
            }
            return 'text'
        }
    },
    methods: {
        computedServingItem(item) {
            let selectedItem = this.servingList.find((it) => it.key === item.value)
            if (selectedItem) return selectedItem
            if (this.currentServing) {
                item.value = this.currentServing.key
                return this.currentServing
            }
            return {}
        },
        setServingItem(item, val) {
            if (!val.key) return
            item.value = val.key
        },
        computedDatabaseManagerItem(item) {
            let selectedItem = this.dataManagerList.find((it) => it.key === item.value)
            if (selectedItem) return selectedItem
            return {}
        },
        setDatabaseManagerItem(item, val) {
            if (!val.key) return
            item.value = val.key
        }
    }
}
</script>

<style lang="scss">
.value-input {
    position: relative;
    width: 100%;
    display: flex;
}
</style>
