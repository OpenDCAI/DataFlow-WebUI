<template>
    <div class="collapse-item-content">
        <hr />
        <div v-if="item.pipeline" class="bp-row column">
            <p class="bp-title">{{ appConfig.local('Pipeline') }}</p>
            <p class="bp-bold-info">{{ item.pipeline }}</p>
        </div>
        <hr v-if="item.pipeline" />
        <div class="bp-row column">
            <p class="bp-light-title">{{ appConfig.local('ID') }}</p>
            <p class="bp-std-info">{{ item.id }}</p>
        </div>
        <hr />
        <div v-if="item.root" class="bp-row column">
            <p class="bp-light-title">{{ appConfig.local('Root') }}</p>
            <p class="bp-std-info">{{ item.root }}</p>
        </div>
        <hr v-if="item.root" />
        <div v-if="item.hash" class="bp-row column">
            <p class="bp-light-title">{{ appConfig.local('Hash') }}</p>
            <p class="bp-std-info">{{ item.hash }}</p>
        </div>
        <hr v-if="item.hash" />
        <div v-if="item.file_name" class="bp-row column">
            <p class="bp-light-title">{{ appConfig.local('File Name') }}</p>
            <p class="bp-std-info">{{ item.file_name }}</p>
        </div>
        <hr v-if="item.file_name" />
        <div v-if="item.uploaded_at" class="bp-row column">
            <p class="bp-light-title">{{ appConfig.local('Uploaded At') }}</p>
            <p class="bp-std-info">{{ item.uploaded_at }}</p>
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
