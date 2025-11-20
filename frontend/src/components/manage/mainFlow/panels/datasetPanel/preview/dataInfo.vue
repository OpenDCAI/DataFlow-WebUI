<template>
    <div class="collapse-item-content">
        <hr />
        <div class="bp-row column">
            <p class="bp-title">{{ appConfig.local('Pipeline') }}</p>
            <p class="bp-bold-info">{{ item.pipeline }}</p>
        </div>
        <hr />
        <div class="bp-row column">
            <p class="bp-light-title">{{ appConfig.local('ID') }}</p>
            <p class="bp-std-info">{{ item.id }}</p>
        </div>
        <hr />
        <div class="bp-row column">
            <p class="bp-light-title">{{ appConfig.local('Root') }}</p>
            <p class="bp-std-info">{{ item.root }}</p>
        </div>
        <hr />
        <div class="bp-row column">
            <p class="bp-light-title">{{ appConfig.local('Hash') }}</p>
            <p class="bp-std-info">{{ item.hash }}</p>
        </div>
    </div>
</template>

<script setup>
import { useAppConfig } from '@/stores/appConfig'

const appConfig = useAppConfig()

const props = defineProps({
    item: {
        type: Object,
        default: () => ({})
    }
})
</script>
