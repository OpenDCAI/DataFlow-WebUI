import tool from '../tools'

const AsyncLoad = tool.AsyncLoad

export default {
    path: '/m',
    component: () => AsyncLoad(() => import('@/views/manage/index.vue')),
    children: [
        {
            path: '',
            component: () => AsyncLoad(() => import('@/views/manage/dataflow/index.vue'))
        },
        {
            path: 'serving',
            component: () => AsyncLoad(() => import('@/views/manage/serving/index.vue')),
            meta: {
                title: 'Dataflow-Serving'
            }
        },
        {
            path: 'dm',
            component: () => AsyncLoad(() => import('@/views/manage/dbManager/index.vue')),
            meta: {
                title: 'Dataflow-DBManager'
            }
        },
        {
            path: 'prompts',
            component: () => AsyncLoad(() => import('@/views/manage/prompts/index.vue')),
            meta: {
                title: 'Dataflow-Prompts'
            }
        },
        {
            path: 'schemas',
            component: () => AsyncLoad(() => import('@/views/manage/schemas/index.vue')),
            meta: {
                title: 'Dataflow-Schemas'
            }
        },
        {
            path: 'settings',
            component: () => AsyncLoad(() => import('@/views/manage/settings/index.vue')),
            meta: {
                title: 'Dataflow-Settings'
            }
        },
        {
            path: 'analysis',
            component: () => AsyncLoad(() => import('@/views/manage/analysis/index.vue')),
            meta: {
                title: 'Dataflow-Analysis'
            }
        }
    ],
    meta: {
        title: 'Dataflow-WebUI'
    }
}
