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
            path: 'settings',
            component: () => AsyncLoad(() => import('@/views/manage/settings/index.vue')),
            meta: {
                title: 'Dataflow-Settings'
            }
        }
    ],
    meta: {
        title: 'Dataflow-WebUI'
    }
}
