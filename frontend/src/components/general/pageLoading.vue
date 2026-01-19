<template>
    <div v-show="modelValue" class="df-page-loading" :class="[{ dark: theme === 'dark' }]">
        <fv-progress-ring loading="true"
            :background="theme === 'dark' ? 'rgba(36, 36, 36, 0.8)' : 'rgba(245, 245, 245, 0.8)'"
            :color="color"></fv-progress-ring>
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
        ...mapState(useTheme, ['theme', 'color'])
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

    &.dark {
        background-color: rgba(0, 0, 0, 0.8);
        color: whitesmoke;

        .df-page-loading-title {
            color: whitesmoke;
        }
    }

    .df-page-loading-title {
        margin-top: 10px;
        font-size: 16px;
        font-weight: bold;
        color: #333;
        user-select: none;
    }
}
</style>
