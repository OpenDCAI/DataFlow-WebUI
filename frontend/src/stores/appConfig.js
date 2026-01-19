import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useAppConfig = defineStore('useAppConfig', () => {
    const screenWidth = ref(999999999);
    const config = ref({
        language: 'en'
    })
    const i18n = ref({})

    function setScreenWidth(obj) {
        screenWidth.value = obj
    }

    function reviseI18N(val) {
        i18n.value = val
    }

    const language = computed(() => {
        return config.value.language
    })

    function reviseLanguage(val) {
        config.value.language = val
    }

    const local = text => {
        return computed(() => {
            let result = i18n.value[text];
            if (!result)
                return text;
            return result[config.value.language];
        }).value
    }

    return {
        language,
        screenWidth,
        setScreenWidth,
        reviseI18N,
        reviseLanguage,
        local
    }
})