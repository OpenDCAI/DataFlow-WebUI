<template>
    <fv-panel
        v-model="thisValue"
        :title="title"
        :theme="theme"
        :width="width"
        :height="height"
        :background="theme === 'dark' ? 'rgba(0, 0, 0, 0.8)' : 'rgba(250, 250, 250, 0.3)'"
        :title-size="18"
        :isAcrylic="true"
        :is-central-side="true"
        :is-footer="isFooter"
    >
        <template v-slot:container>
            <div class="base-panel-container" @keyup.enter="$emit('confirm')">
                <slot name="content"></slot>
            </div>
        </template>
        <template v-slot:footer>
            <div class="bp-control">
                <slot name="control" :close="close">
                    <fv-button></fv-button>
                </slot>
            </div>
        </template>
    </fv-panel>
</template>

<script>
export default {
    props: {
        modelValue: {
            default: true
        },
        title: {
            default: 'Title'
        },
        width: {
            default: '800px'
        },
        height: {
            default: '80%'
        },
        isFooter: {
            default: true
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
        modelValue(val) {
            this.thisValue = val
        },
        thisValue(val) {
            this.$emit('update:modelValue', val)
        }
    },
    methods: {
        close() {
            this.thisValue = false
        }
    }
}
</script>

<style lang="scss">
.base-panel-container {
    position: relative;
    width: 100%;
    height: 100%;
    padding: 15px;
    color: rgba(28, 30, 41, 1);
    font-family:
        Akkurat Std,
        -apple-system,
        BlinkMacSystemFont,
        Segoe UI,
        Roboto,
        Oxygen,
        Ubuntu,
        Cantarell,
        Helvetica Neue,
        sans-serif;
    font-weight: 400;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .bp-title {
        margin: 5px 0px;
        font-size: 13.8px;
        font-weight: bold;
        color: rgba(123, 139, 209, 1);
        user-select: none;
    }

    .bp-light-title {
        margin: 5px 0px;
        font-size: 12px;
        color: rgba(95, 95, 95, 1);
        user-select: none;
    }

    .bp-info {
        margin: 5px 0px;
        font-size: 12px;
        color: rgba(120, 120, 120, 1);
        user-select: none;
    }

    .bp-std-info {
        font-size: 13.8px;
        color: rgba(27, 27, 27, 1);
        user-select: none;
    }

    .bp-bold-info {
        margin: 5px 0px;
        font-size: 16px;
        font-weight: bold;
        color: rgba(27, 27, 27, 1);
        user-select: none;
    }

    .bp-p-block {
        position: relative;
        width: 100%;
        height: auto;
        padding: 15px 0px;
        box-sizing: border-box;
        line-height: 3;
        display: flex;
        flex-direction: column;
    }

    .bp-row {
        position: relative;
        width: 100%;
        padding: 0px 42px;
        flex-wrap: wrap;
        box-sizing: border-box;
        display: flex;
        align-items: center;

        &.no-pad {
            padding: 0px;
        }

        &.sep {
            justify-content: space-between;
        }

        &.column {
            flex-direction: column;
            align-items: flex-start;
        }

        &.full {
            flex: 1;
        }

        &.auto {
            overflow: auto;
        }
    }

    hr {
        margin: 10px 0px;
        border: none;
        border-top: rgba(120, 120, 120, 0.1) solid thin;
    }
}

.bp-control {
    position: relative;
    width: 100%;
    height: auto;
    padding: 15px 0px;
    gap: 5px;
    box-sizing: border-box;
    display: flex;
    justify-content: flex-end;
}
</style>
