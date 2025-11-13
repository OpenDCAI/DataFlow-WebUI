// src/composables/useGlobal.ts
import { getCurrentInstance } from 'vue'

export function useGlobal() {
    const instance = getCurrentInstance()
    if (!instance || !instance.proxy) {
        throw new Error('useGlobal must be called within setup()')
    }

    const proxy = instance.proxy

    return {
        $api: proxy.$api,
        $axios: proxy.$axios,
        $router: proxy.$router,
        $Go: proxy.$Go,
        $Back: proxy.$Back,
        $Jump: proxy.$Jump,
    }
}