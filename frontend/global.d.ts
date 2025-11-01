import 'vue'
import type * as apiType from '@/axios/api'

declare module 'vue' {
    interface ComponentCustomProperties {
        $api: typeof apiType
    }
}