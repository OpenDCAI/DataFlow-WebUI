<template>
    <div class="manage-container">
        <div class="manage-content-block">
            <fv-navigation-view
                v-model="currentNav"
                :title="local(`Dataflow`)"
                :options="navList"
                :expand.sync="isExpand"
                :foreground="color"
                :flyout-display="1368"
                :mobile-display="1024"
                class="navigation-view"
                :show-back="false"
                :show-setting="false"
                @item-click="handleItemClick"
                @back="$Back()"
            >
                <template v-slot:title="{ show }">
                    <div v-show="show" class="title-block name">
                        <img :src="img.logo" alt="" />
                        <p class="name title">{{ local(`Dataflow`) }}</p>
                    </div>
                </template>
            </fv-navigation-view>
            <router-view></router-view>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'

import logo from '@/assets/logo/logo.png'

export default {
    data() {
        return {
            currentNav: {
                key: 0,
                name: () => this.local('Playground'),
                icon: 'World',
                route: '/a/'
            },
            isExpand: true,
            navList: [
                {
                    key: 0,
                    name: () => this.local('Playground'),
                    icon: 'World',
                    route: '/a/'
                },
                {
                    key: 1,
                    name: () => this.local('RL Analyizer'),
                    icon: 'Diagnostic',
                    route: '/a/rla'
                },
                {
                    key: 2,
                    name: () => this.local('Quality Manager'),
                    icon: 'Leaf',
                    route: '/a/qm'
                },
                {
                    key: -1,
                    name: () => this.local('Home'),
                    icon: 'Home',
                    route: '/'
                }
            ],
            img: {
                logo: logo
            }
        }
    },
    watch: {
        $route() {
            this.routeFormat()
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        ...mapState(useTheme, ['color', 'gradient', 'theme'])
    },
    mounted() {
        this.routeFormat()
    },
    methods: {
        handleItemClick(item) {
            this.$Go(`${item.route}`)
        },
        routeFormat() {
            let path = this.$route.path
            for (let item of this.navList) {
                if (item.route === '') continue
                let targetPath = `/a/${item.route}`
                if (path.startsWith(targetPath)) {
                    this.currentNav = item
                    break
                }
            }
        }
    }
}
</script>

<style lang="scss">
.manage-container {
    @include app;

    background: rgba(250, 250, 250, 1);
    display: flex;
    flex-direction: column;

    .manage-content-block {
        position: relative;
        width: 100%;
        flex: 1;
        box-sizing: border-box;
        display: flex;
        overflow: hidden;

        .navigation-view {
            z-index: 2;

            .title-block {
                @include Vcenter;

                img {
                    width: 30px;
                    height: 30px;
                    object-fit: cover;
                }
            }
        }
    }
}
</style>
