import tool from "../tools";

const AsyncLoad = tool.AsyncLoad;

export default {
    path: "/a",
    component: () => AsyncLoad(() => import("@/views/admin/index.vue")),
    children: [
        {
            path: '',
            component: () => AsyncLoad(() => import("@/views/admin/dataflow/index.vue"))
        }
    ]
};
