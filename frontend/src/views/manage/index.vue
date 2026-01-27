<template>
    <div class="manage-container" :class="[{ dark: theme === 'dark' }]">
        <div class="manage-content-block">
            <fv-navigation-view :theme="theme" v-model="currentNav" :title="''" :options="navList"
                v-model:expand="isExpand" :foreground="color"
                :background="theme === 'dark' ? 'rgba(36, 36, 36, 1)' : ''" expand-width="300" :flyout-display="1368"
                :mobile-display="1024" class="navigation-view" :show-back="false" :show-search="false"
                :setting-title="local('Settings')" @item-click="handleItemClick" @setting-click="handleSettingClick"
                @back="$Back()">
                <template v-slot:banner>
                    <div class="title-block name">
                        <img class="nav-icon" :src="img.logo" alt="" />
                        <p v-show="isExpand" class="title">{{ local(`Dataflow`) }}</p>
                    </div>
                </template>
                <template v-slot:listItem="x">
                    <div class="nav-item" :class="{ collapse: !isExpand }">
                        <img v-show="x.item.type !== 'header' && x.item.img" class="nav-item-icon" :src="x.item.img"
                            alt="" />
                        <i v-show="x.item.type !== 'header' && !x.item.img" class="ms-Icon nav-item-icon"
                            :class="['ms-Icon--' + x.item.icon]"></i>
                        <p class="name" :style="{ color: x.item.type === 'header' ? color : '' }">
                            {{ x.valueTrigger(x.item.name) }}
                        </p>
                    </div>
                </template>
            </fv-navigation-view>
            <router-view v-slot="{ Component }">
                <KeepAlive>
                    <component :is="Component" />
                </KeepAlive>
            </router-view>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'

import logo from '@/assets/logo/logo.png'
import dataflow from '@/assets/nav/dataflow.svg'
import serving from '@/assets/nav/serving.svg'
import dbManager from '@/assets/nav/dbManager.svg'

export default {
    data() {
        return {
            currentNav: {
                key: 0,
                name: () => this.local('Dataflow'),
                icon: 'World',
                route: '/m/'
            },
            isExpand: true,
            navList: [
                {
                    key: -1,
                    name: () => this.local('Data Preparation'),
                    type: 'header'
                },
                {
                    key: 0,
                    name: () => this.local('Dataflow Hub'),
                    icon: 'World',
                    img: dataflow,
                    route: '/m/'
                },
                {
                    key: 1,
                    name: () => this.local('Serving Manager'),
                    icon: 'World',
                    img: serving,
                    route: '/m/serving'
                },
                {
                    key: 1,
                    name: () => this.local('DB Manager'),
                    icon: 'World',
                    img: dbManager,
                    route: '/m/dm'
                },
                {
                    key: -1,
                    name: () => this.local('Home'),
                    icon: 'Home',
                    route: '/',
                    show: false
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
                if (!item.route || item.type === 'header') continue
                let targetPath = item.route
                if (path == targetPath) {
                    this.currentNav = item
                    break
                }
            }
        },
        handleSettingClick() {
            this.$Go('/m/settings')
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

    &.dark {
        background: rgba(36, 36, 36, 1);

        .manage-content-block {
            .navigation-view {
                .title-block {
                    .title {
                        color: whitesmoke;
                    }
                }
            }
        }
    }

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

                position: relative;
                width: 100%;
                height: 60px;
                padding: 0px 10px;
                user-select: none;

                .nav-icon {
                    width: 28px;
                    height: auto;
                    margin-left: 5px;
                    object-fit: cover;
                }

                .title {
                    @include color-dataflow-title;

                    margin-left: 5px;
                    font-size: 20px;
                    font-weight: 600;
                    color: rgba(0, 0, 0, 1);
                }
            }

            .nav-item {
                @include Vcenter;

                position: relative;
                width: 100%;
                height: 40px;
                user-select: none;

                &.collapse {
                    .nav-item-icon {
                        margin-left: 5px;
                    }
                }

                .nav-item-icon {
                    width: 15px;
                    height: 15px;
                    margin-left: 15px;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    object-fit: cover;
                }
            }
        }
    }
}
</style>
