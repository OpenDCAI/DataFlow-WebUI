import { defineAsyncComponent, h } from 'vue'
import loading from "@/components/general/loading.vue";

const AsyncLoad = function (component) {
    const AsyncComp = defineAsyncComponent({
        loader: component,
        loadingComponent: loading,
        errorComponent: loading,
        delay: 200,
        timeout: 10000
    });
    return Promise.resolve({
        render() {
            return h(AsyncComp);
        }
    });
};

export default {
    AsyncLoad
};