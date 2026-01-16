import tool from "../tools";

const AsyncLoad = tool.AsyncLoad;

export default {
    path: "/m",
    component: () => AsyncLoad(() => import("@/views/manage/index.vue")),
    children: [
        {
            path: '',
            component: () => AsyncLoad(() => import("@/views/manage/dataflow/index.vue"))
        },
        {
            path: 'serving',
            component: () => AsyncLoad(() => import("@/views/manage/serving/index.vue"))
        },
        {
            path: 'dm',
            component: () => AsyncLoad(() => import("@/views/manage/dbManager/index.vue"))
        },
        {
            path: 'settings',
            component: () => AsyncLoad(() => import("@/views/manage/settings/index.vue"))
        }
    ]
};
