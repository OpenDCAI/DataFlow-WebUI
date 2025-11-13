<template>
    <div class="df-default-container">
        <div class="df-flow-container">
            <mainFlow></mainFlow>
        </div>
    </div>
</template>

<script>
import mainFlow from '@/components/manage/mainFlow/index.vue'

export default {
    components: {
        mainFlow
    }
}
</script>

<style lang="scss">
.df-default-container {
    position: relative;
    width: 100%;
    height: 100%;
    padding: 15px;
    background-color: rgba(241, 241, 241, 1);
    display: flex;

    .df-flow-container {
        position: relative;
        width: 100%;
        height: 100%;
        background: rgba(250, 250, 250, 1);
        border: rgba(120, 120, 120, 0.1) solid thin;
        border-radius: 15px;
        box-shadow: inset 0px 0px 10px rgba(0, 0, 0, 0.1);
        overflow: hidden;
    }
}
</style>
