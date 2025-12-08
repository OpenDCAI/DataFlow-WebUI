<template>
    <div v-show="modelValue" class="df-page-loading">
        <fv-progress-ring
            loading="true"
            background="rgba(245, 245, 245, 0.8)"
            :color="color"
        ></fv-progress-ring>
        <div class="df-page-loading-title">{{ title }}</div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useTheme } from '@/stores/theme'

export default {
    props: {
        modelValue: {
            type: Boolean,
            default: false
        },
        title: {
            type: String,
            default: ''
        }
    },
    data() {
        return {
            thisValue: this.modelValue
        }
    },
    watch: {
        modelValue(newVal, oldVal) {
            this.thisValue = newVal
        },
        thisValue(newVal, oldVal) {
            this.$emit('update:modelValue', newVal)
        }
    },
    computed: {
        ...mapState(useTheme, ['color'])
    }
}
</script>

<style lang="scss">
.df-page-loading {
    @include HcenterVcenterC;

    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(255, 255, 255, 0.8);
    z-index: 9999;

    .df-page-loading-title {
        margin-top: 10px;
        font-size: 16px;
        font-weight: bold;
        color: #333;
        user-select: none;
    }
}
</style>
