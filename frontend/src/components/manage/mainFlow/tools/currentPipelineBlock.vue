<template>
    <div
        class="df-current-pipeline-container"
        @mouseenter="inside = true"
        @mouseleave="inside = false"
    >
        <div class="df-current-pipeline-title" :title="local('Current Pipeline')">
            {{ modelValue ? modelValue.name : local('Temp. Pipeline') }}
        </div>
        <transition name="df-cp-scale-up-to-up">
            <time-rounder
                v-if="modelValue"
                v-show="inside"
                :model-value="new Date(modelValue.updated_at)"
                :foreground="color"
                style="width: auto"
            ></time-rounder>
        </transition>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import timeRounder from '@/components/general/timeRounder.vue'

export default {
    components: {
        timeRounder
    },
    props: {
        modelValue: {
            default: null
        }
    },
    data() {
        return {
            thisValue: this.modelValue,
            inside: false
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
        ...mapState(useTheme, ['color'])
    }
}
</script>

<style lang="scss">
.df-current-pipeline-container {
    @include Vcenter;

    position: absolute;
    right: 15px;
    width: auto;
    height: 40px;
    max-width: 120px;
    gap: 15px;
    padding: 0px 10px;
    background: rgba(245, 245, 245, 0.3);
    border: rgba(120, 120, 120, 0.1) solid thin;
    border-radius: 50px;
    transition:
        background 0.3s ease-out,
        transform 0.3s ease-in-out,
        max-width 0.8s ease-out;
    backdrop-filter: blur(10px);
    box-shadow: 0px 0px 1px rgba(0, 0, 0, 0.1);

    &:hover {
        max-width: 50%;
        background: rgba(250, 250, 250, 0.6);
        transform: scale(1.05);
    }

    &:active {
        transform: scale(0.99);
    }

    .df-current-pipeline-title {
        @include nowrap;
        @include color-golden;

        font-size: 12px;
        font-weight: bold;
        color: #333;
        transition: all 0.3s;
        user-select: none;
    }
}

.df-cp-scale-up-to-up-enter-active {
    animation: scaleUp 0.7s ease both;
    animation-delay: 0.3s;
}
.df-cp-scale-up-to-up-leave-active {
    position: absolute;
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    animation: scaleDownUp 0.1s ease both;
    z-index: 8;
}
@keyframes scaleUp {
    from {
        opacity: 0;
        transform: scale(0.3);
    }
}
@keyframes scaleDownUp {
    to {
        opacity: 0;
        transform: scale(1.2);
    }
}
</style>
