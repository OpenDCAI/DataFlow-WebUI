<template>
    <div class="value-input">
        <fv-text-box :theme="theme" v-if="computedUIType === 'text'" v-model="thisValue"
            :placeholder="local('Please input') + ` ${itemObj.name}`" font-size="12" border-radius="3" border-width="2"
            :reveal-border="true" :border-color="thisData.shadowColor" :focus-border-color="thisData.borderColor"
            underline style="width: 100%; height: 35px"></fv-text-box>
        <fv-combobox :theme="theme" v-if="computedUIType === 'llm_serving'" :model-value="computedServingItem(itemObj)"
            @update:modelValue="setServingItem(itemObj, $event)" :placeholder="local('Select Serving')"
            :options="servingList" :choosen-slider-background="thisData.borderColor"
            :reveal-background-color="[thisData.shadowColor, 'rgba(255, 255, 255, 1)']"
            :reveal-border-color="thisData.borderColor" border-radius="8" style="width: 100%"></fv-combobox>
        <fv-combobox :theme="theme" v-if="computedUIType === 'database_manager'"
            :model-value="computedDatabaseManagerItem(itemObj)"
            @update:modelValue="setDatabaseManagerItem(itemObj, $event)" :placeholder="local('Select Database Manager')"
            :options="dataManagerList" :choosen-slider-background="thisData.borderColor"
            :reveal-background-color="[thisData.shadowColor, 'rgba(255, 255, 255, 1)']"
            :reveal-border-color="thisData.borderColor" border-radius="8" style="width: 100%"></fv-combobox>
        <!-- JSON Schema: choose from saved schemas, fall back to inline JSON -->
        <div v-if="computedUIType === 'json_schema'" class="value-input__schema">
            <fv-combobox :theme="theme" :model-value="computedSchemaItem(itemObj)"
                @update:modelValue="setSchemaItem(itemObj, $event)"
                :placeholder="jsonSchemaList.length ? local('Select JSON Schema') : local('No saved schemas')"
                :options="jsonSchemaList" :choosen-slider-background="thisData.borderColor"
                :reveal-background-color="[thisData.shadowColor, 'rgba(255, 255, 255, 1)']"
                :reveal-border-color="thisData.borderColor" border-radius="8"
                style="width: 100%; margin-bottom: 4px"></fv-combobox>
            <fv-text-box :theme="theme" v-model="thisValue"
                :placeholder="local('…or paste JSON Schema directly')"
                font-size="12" border-radius="3" border-width="2"
                :reveal-border="true" :border-color="thisData.shadowColor"
                :focus-border-color="thisData.borderColor" underline
                style="width: 100%; height: 35px"></fv-text-box>
        </div>
        <kv-input v-if="computedUIType === 'kv_input'" v-model="thisValue"></kv-input>
    </div>
</template>

<script>
import { useAppConfig } from '@/stores/appConfig'
import { useDataflow } from '@/stores/dataflow'
import { mapState, mapActions } from 'pinia'

import kvInput from './kvInput.vue';

// Parameter names that should render the JSON Schema picker.
// Match exact names and *_schema suffix.
const JSON_SCHEMA_PARAM_NAMES = new Set([
    'json_schema',
    'output_schema',
    'response_schema',
    'structured_output_schema',
    'response_format_schema',
])

export default {
    components: {
        kvInput
    },
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
        },
        theme: {
            default: 'light'
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
        ...mapState(useDataflow, ['servingList', 'currentServing', 'dataManagerList', 'jsonSchemaList']),
        computedUIType() {
            if (this.itemObj.name === 'llm_serving' || this.itemObj.name === 'embedding_serving') {
                return 'llm_serving'
            }
            if (this.itemObj.name === 'database_manager') {
                return 'database_manager'
            }
            if (this.isJsonSchemaParam(this.itemObj.name)) {
                return 'json_schema'
            }
            if (this.itemObj.kind === 'VAR_KEYWORD')
                return 'kv_input'
            return 'text'
        }
    },
    mounted() {
        if (this.computedUIType === 'json_schema' && !this.jsonSchemaList.length) {
            this.getJsonSchemaList()
        }
    },
    methods: {
        ...mapActions(useDataflow, ['getJsonSchemaList']),
        isJsonSchemaParam(name) {
            if (!name) return false
            if (JSON_SCHEMA_PARAM_NAMES.has(name)) return true
            return /_schema$/.test(name) || /^schema$/.test(name)
        },
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
        },
        // JSON Schema picker:
        //   - value is stored as "schema_ref:<id>" when the user picks a saved schema
        //   - falls back to raw JSON string when typed into the textbox
        computedSchemaItem(item) {
            const v = item.value || ''
            if (typeof v === 'string' && v.startsWith('schema_ref:')) {
                const id = v.slice('schema_ref:'.length)
                const found = this.jsonSchemaList.find((s) => s.key === id)
                if (found) return found
            }
            return {}
        },
        setSchemaItem(item, val) {
            if (!val || !val.key) return
            item.value = `schema_ref:${val.key}`
            this.thisValue = item.value
        }
    }
}
</script>

<style lang="scss">
.value-input {
    position: relative;
    width: 100%;
    display: flex;

    .value-input__schema {
        width: 100%;
        display: flex;
        flex-direction: column;
    }
}
</style>
