<template>
    <div class="kv-input">
        <fv-button v-show="modelValue.length === 0" theme="dark" :background="gradient" :border-radius="8"
            style="width: 100%;" @click="addItem(-1)">{{ local('Add Key-Value') }}</fv-button>
        <div class="kv-input-item" v-for="(item, index) in modelValue" :key="index">
            <fv-button v-show="!readonly" theme="dark" font-size="8" border-radius="50"
                background="rgba(200, 38, 45, 1)" style="width: 18px; height: 18px; flex-shrink: 0;"
                @click="removeItem(index)">
                <i class="ms-Icon ms-Icon--Remove"></i>
            </fv-button>
            <fv-text-box :theme="theme" v-model="item.name" placeholder="Key" :disabled="readonly" font-size="8"
                border-radius="3" border-width="2" :reveal-border="true" :focus-border-color="color" underline
                style="width: 150px; height: 30px;"></fv-text-box>
            <fv-text-field :theme="theme" v-model="item.value" placeholder="Value" font-size="8" border-radius="3"
                border-width="2" :reveal-border="true" :focus-border-color="color" underline></fv-text-field>
            <fv-button v-show="!readonly" theme="dark" font-size="12" border-radius="50"
                background="rgba(0, 204, 153, 1)" style="width: 18px; height: 18px; flex-shrink: 0;"
                @click="addItem(index)">
                <i class="ms-Icon ms-Icon--Add"></i>
            </fv-button>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia';
import { useAppConfig } from '@/stores/appConfig';
import { useTheme } from '@/stores/theme';

export default {
    props: {
        modelValue: {
            default: () => []
        },
        readonly: {
            default: false
        }
    },
    data() {
        return {

        }
    },
    watch: {

    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['theme', 'color', 'gradient'])
    },
    methods: {
        addItem(index) {
            if (!Array.isArray(this.modelValue)) {
                this.$emit('update:modelValue', [{ key: '', value: '', kind: 'POSITIONAL_OR_KEYWORD' }])
                return
            }
            this.modelValue.splice(index + 1, 0, { key: '', value: '', kind: 'POSITIONAL_OR_KEYWORD' })
        },
        removeItem(index) {
            this.modelValue.splice(index, 1)
        }
    }
}
</script>

<style lang="scss">
.kv-input {
    position: relative;
    width: 100%;
    height: auto;
    gap: 5px;
    display: flex;
    flex-direction: column;

    .kv-input-item {
        position: relative;
        width: 100%;
        height: auto;
        flex-shrink: 0;
        gap: 3px;
        display: flex;
        flex-direction: row;
        align-items: center;
        cursor: pointer;
    }
}
</style>