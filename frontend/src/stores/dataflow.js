import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useDataflow = defineStore('useDataflow', () => {
    const isAutoConnection = ref(false)

    const switchAutoConnection = (val) => {
        isAutoConnection.value = val
    }

    return {
        isAutoConnection,
        switchAutoConnection,
    }
})