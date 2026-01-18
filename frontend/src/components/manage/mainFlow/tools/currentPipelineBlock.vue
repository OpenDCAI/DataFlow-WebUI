<template>
    <div class="df-current-pipeline-container" :class="[{ template: isTemplate || taskId, dark: theme === 'dark' }]"
        @mouseenter="inside = true" @mouseleave="inside = false">
        <div class="row-item">
            <div class="df-current-pipeline-title" :title="local('Current Pipeline')">
                {{ displayName }}
            </div>
            <transition name="df-cp-scale-up-to-up">
                <time-rounder v-if="modelValue" v-show="inside" :model-value="new Date(modelValue.updated_at)"
                    :foreground="color" style="width: auto"></time-rounder>
            </transition>
        </div>
        <div v-if="isTemplate" class="row-item">
            <p class="df-current-sec-info">
                {{ local('Created from') }}: {{ modelValue ? modelValue.name : '' }}
            </p>
        </div>
        <div v-if="taskId" class="row-item">
            <fv-button :theme="theme" :border-radius="20" font-size="10"
                style="width: 25px; height: 20px; flex-shrink: 0" :title="local('Recover Pipeline')"
                @click="$emit('recover-click')">
                <i class="ms-Icon ms-Icon--Reply"></i>
            </fv-button>
            <p class="df-current-sec-info">{{ local('Execution') }}: {{ taskId }}</p>
        </div>
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
        },
        taskId: {
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
        ...mapState(useTheme, ['theme', 'color']),
        isTemplate() {
            if (!this.thisValue) return false
            let tags = this.thisValue.tags
            if (!Array.isArray(tags)) return false
            return tags.includes('template')
        },
        displayName() {
            if (this.isTemplate) return this.local('Temp. Pipeline')
            return this.modelValue ? this.modelValue.name : this.local('Temp. Pipeline')
        }
    }
}
</script>

<style lang="scss">
.df-current-pipeline-container {
    @include VcenterC;

    position: absolute;
    right: 15px;
    width: auto;
    height: 40px;
    max-width: 120px;
    gap: 5px;
    padding: 0px 15px;
    background: rgba(245, 245, 245, 0.3);
    border: rgba(120, 120, 120, 0.1) solid thin;
    border-radius: 50px;
    flex-direction: column;
    transition:
        background 0.3s ease-out,
        transform 0.3s ease-in-out,
        max-width 0.8s ease-out;
    backdrop-filter: blur(10px);
    box-shadow: 0px 0px 1px rgba(0, 0, 0, 0.1);
    z-index: 30;

    &.dark {
        background: rgba(9, 9, 9, 0.3);
        border: rgba(255, 255, 255, 0.1) solid thin;

        &:hover {
            background: rgba(9, 9, 9, 0.1);
        }
    }

    &.template {
        height: 50px;
    }

    &:hover {
        max-width: 50%;
        background: rgba(250, 250, 250, 0.6);
        transform: scale(1.05);
    }

    &:active {
        transform: scale(0.99);
    }

    .row-item {
        @include nowrap;
        @include Vcenter;

        position: relative;
        width: 100%;
        gap: 15px;
        height: auto;
        flex-shrink: 0;
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

    .df-current-sec-info {
        @include nowrap;

        font-size: 10px;
        color: rgba(120, 120, 120, 1);
        user-select: none;
    }
}

.df-cp-scale-up-to-up-enter-active {
    animation: scaleUp 0.3s ease both;
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
