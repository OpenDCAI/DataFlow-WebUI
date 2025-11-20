<template>
    <div class="md-text-default-block" v-html="html"></div>
</template>

<script setup>
import { computed } from 'vue'

import MarkdownIt from 'markdown-it'
import markdownItSubscript from 'markdown-it-sub'
import markdownItSuperscript from 'markdown-it-sup'
import markdownItMark from 'markdown-it-mark'

const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true
})
    .use(markdownItSubscript)
    .use(markdownItSuperscript)
    .use(markdownItMark)

const props = defineProps({
    modelValue: {
        type: String,
        default: ''
    }
})

const html = computed(() => {
    return md.render(props.modelValue)
})
</script>

<style lang="scss">
.md-text-default-block {
    color: rgba(55, 65, 81, 1);

    * {
        max-width: 100%;
    }

    p {
        white-space: pre-wrap;
    }

    li {
        margin-left: 15px;
        margin-top: 10px;
    }

    pre {
        width: 100%;
        margin: 15px 0px;
        padding: 15px;
        background-color: rgba(36, 36, 36, 1);
        border-radius: 8px;
        box-sizing: border-box;
        line-height: 2;
        overflow-x: overlay;

        code {
            color: inherit;
            padding: 0;
            background: none;
            font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
            color: whitesmoke;
            line-height: 1.5;

            &::before {
                content: attr(data-language);

                margin-bottom: 10px;
                color: rgba(245, 245, 245, 0.6);
                display: block;
            }
        }
    }

    code {
        padding: 4px 6px;
        background-color: rgba(#616161, 0.1);
        font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
        font-size: 13.8px;
        color: rgba(235, 87, 87, 1);
        border-radius: 3px;
    }

    table {
        border-collapse: collapse;
        table-layout: fixed;
        width: 100%;
        margin: 5px 0px;
        display: table;
        overflow: hidden;
        overflow-y: visible;

        td,
        th {
            min-width: 1em;
            border: thin solid #ced4da;
            padding: 3px 5px;
            vertical-align: top;
            box-sizing: border-box;
            position: relative;

            > * {
                margin-bottom: 0;
            }
        }

        th {
            width: auto;
            font-weight: bold;
            text-align: left;
            background-color: rgba(241, 243, 245, 1);
        }

        .selectedCell:after {
            z-index: 2;
            position: absolute;
            content: '';
            left: 0;
            right: 0;
            top: 0;
            bottom: 0;
            background: rgba(200, 200, 255, 0.4);
            pointer-events: none;
        }

        .column-resize-handle {
            position: absolute;
            right: -2px;
            top: 0;
            bottom: -2px;
            width: 4px;
            background-color: rgba(145, 191, 209, 1);
            pointer-events: none;
        }

        p {
            margin: 0;
        }
    }

    .msg-content-generating-block {
        position: relative;
        top: 2px;
        width: 16px;
        height: 16px;
        margin-left: 10px;
        border-radius: 50%;
        user-select: none;
        animation: flash 0.1s infinite alternate;
        display: inline-block;
    }

    @keyframes flash {
        from {
            opacity: 0;
        }

        to {
            opacity: 1;
            transform: scale(1.2);
        }
    }
}
</style>
