import { createRouter, createWebHashHistory } from 'vue-router'

import tool from "./tools";

import Admin from "./Admin";

import home from "@/views/client/home/index.vue";

const router = createRouter({
    history: createWebHashHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/',
            name: 'home',
            component: home,
            meta: {
                title: "Dataflow"
            }
        },
        Admin
    ]
})

export default router
