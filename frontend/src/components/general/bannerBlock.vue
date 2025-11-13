<template>
    <div class="main_block">
        <div class="d-1">
            <div class="left-block" @click="$Go('/')">
                <img
                    src="@/assets/logo/logo.png"
                    class="logo"
                    draggable="false"
                    width="110"
                    height="58"
                    alt
                    ondragstart="return false;"
                    oncontextmenu="return false;"
                />
                <p class="left-info">Dataflow</p>
            </div>
            <div v-show="screenWidth > 1024" class="link-block">
                <a
                    v-for="(item, index) in navOptions"
                    :key="`a: ${index}`"
                    class="a_link"
                    onselectstart="return false;"
                    @click="
                        () => {
                            if (item.href) $Go(item.href)
                        }
                    "
                    >{{ item.name }}</a
                >
                <fv-button
                    v-if="!islogin && !$route.fullPath.startsWith('/login')"
                    background="#244362"
                    theme="dark"
                    font-size="12"
                    font-weight="600"
                    border-radius="8"
                    :is-box-shadow="true"
                    style="width: 80px; height: 30px; margin-right: 15px"
                    @click="$Go('/login')"
                    >Login</fv-button
                >

                <fv-callout
                    v-if="islogin"
                    :lockScroll="true"
                    :theme="theme"
                    :position="'bottomRight'"
                    :beak="10"
                    :space="0"
                    :popper-style="{ width: '150px' }"
                    :visible.sync="show.menu"
                >
                    <div v-if="islogin" class="sosd-avatar-container">
                        <fv-img :src="avatar"></fv-img>
                    </div>
                    <main class="drop-down-block">
                        <div class="drop-down-item">
                            <fv-animated-icon
                                icon="IDBadge"
                                style="width: 100%; margin: 10px 0px"
                                @click="show.profile = true"
                            >
                                <template v-slot:content>
                                    <div
                                        style="
                                            margin-left: 15px;
                                            font-size: 13px;
                                            user-select: none;
                                        "
                                    >
                                        User Profile
                                    </div>
                                </template>
                            </fv-animated-icon>
                        </div>
                        <div v-if="role.includes('admin')" class="drop-down-item">
                            <fv-animated-icon
                                value="bounceRotate"
                                icon="Settings"
                                style="width: 100%; margin: 10px 0px"
                                @click="$Go('/m')"
                            >
                                <template v-slot:content>
                                    <div
                                        style="
                                            margin-left: 15px;
                                            font-size: 13px;
                                            user-select: none;
                                        "
                                    >
                                        Admin Center
                                    </div>
                                </template>
                            </fv-animated-icon>
                        </div>
                        <hr style="opacity: 0.3" />
                        <div class="drop-down-item">
                            <fv-animated-icon
                                icon="AzureKeyVault"
                                style="width: 100%; margin: 10px 0px"
                                @click="logout"
                            >
                                <template v-slot:content>
                                    <div
                                        style="
                                            margin-left: 15px;
                                            font-size: 13px;
                                            user-select: none;
                                        "
                                    >
                                        {{ local('Logout') }}
                                    </div>
                                </template>
                            </fv-animated-icon>
                        </div>
                    </main>
                </fv-callout>
            </div>
            <transition :name="show.mobileNav ? 'move-top-to-bottom' : ''">
                <div v-show="show.mobileNav" class="s-link-block">
                    <fv-callout
                        v-if="islogin"
                        :theme="theme"
                        :lockScroll="true"
                        :position="'bottomCenter'"
                        :beak="10"
                        :space="0"
                        :popper-style="{ width: '150px' }"
                        :visible.sync="show.mobileMenu"
                    >
                        <div v-if="islogin" class="sosd-avatar-container">
                            <fv-img :src="avatar"></fv-img>
                        </div>
                        <main class="drop-down-block">
                            <div class="drop-down-item">
                                <fv-animated-icon
                                    value="bounceRotate"
                                    icon="IDBadge"
                                    style="width: 100%; margin: 10px 0px"
                                    @click="show.profile = true"
                                >
                                    <template v-slot:content>
                                        <div
                                            style="
                                                margin-left: 15px;
                                                font-size: 13px;
                                                user-select: none;
                                            "
                                        >
                                            User Profile
                                        </div>
                                    </template>
                                </fv-animated-icon>
                            </div>
                            <div v-if="role.includes('admin')" class="drop-down-item">
                                <fv-animated-icon
                                    value="bounceRotate"
                                    icon="Settings"
                                    style="width: 100%; margin: 10px 0px"
                                    @click="$Go('/m')"
                                >
                                    <template v-slot:content>
                                        <div
                                            style="
                                                margin-left: 15px;
                                                font-size: 13px;
                                                user-select: none;
                                            "
                                        >
                                            Admin Center
                                        </div>
                                    </template>
                                </fv-animated-icon>
                            </div>
                            <hr style="opacity: 0.3" />
                            <div class="drop-down-item">
                                <fv-animated-icon
                                    icon="AzureKeyVault"
                                    style="width: 100%; margin: 10px 0px"
                                    @click="logout"
                                >
                                    <template v-slot:content>
                                        <div
                                            style="
                                                margin-left: 15px;
                                                font-size: 13px;
                                                user-select: none;
                                            "
                                        >
                                            {{ local('Logout') }}
                                        </div>
                                    </template>
                                </fv-animated-icon>
                            </div>
                        </main>
                    </fv-callout>
                    <a
                        v-for="(item, index) in navOptions"
                        :key="`b: ${index}`"
                        class="s-link"
                        onselectstart="return false;"
                        @click="
                            () => {
                                if (item.href) $Go(item.href)
                            }
                        "
                        >{{ item.name }}</a
                    >
                    <fv-button
                        v-if="!islogin && !$route.fullPath.startsWith('/login')"
                        background="#244362"
                        theme="dark"
                        font-size="12"
                        font-weight="600"
                        border-radius="12"
                        :is-box-shadow="true"
                        style="width: 180px; height: 30px; margin-top: 15px"
                        @click="$Go('/login')"
                        >Login</fv-button
                    >
                    <fv-button
                        theme="dark"
                        background="transparent"
                        border-radius="15"
                        border-color="rgba(242,242,242,0.8)"
                        style="width: 120px; margin-top: 25px"
                        @click="show.mobileNav ^= true"
                        >Close</fv-button
                    >
                </div>
            </transition>
            <span
                v-show="screenWidth <= 1024"
                class="nav-icon ms-Icon ms-Icon--GlobalNavButton"
                @click="show.mobileNav ^= true"
            ></span>
        </div>
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'
import defaultAvatar from '@/assets/logo/logo.png'

export default {
    components: {},
    data() {
        return {
            navOptions: [{ name: 'Console', href: '/m' }],
            img: {
                defaultAvatar: defaultAvatar
            },
            show: {
                menu: false,
                mobileNav: false,
                mobileMenu: false,
                profile: false
            }
        }
    },
    computed: {
        ...mapState(useAppConfig, {
            screenWidth: 'screenWidth',
            local: 'local'
        }),
        ...mapState(useTheme, ['color', 'gradient', 'theme']),
        role() {
            return ''
        },
        islogin() {
            return false
        },
        avatar() {
            if (!this.userAvatar) return this.img.defaultAvatar
            return this.userAvatar
        }
    },
    methods: {
        logout() {}
    }
}
</script>

<style lang="scss">
.main_block {
    position: fixed;
    width: 100%;
    height: auto;
    background-size: cover;
    z-index: 30;

    .sosd-avatar-container {
        position: relative;
        width: 30px;
        height: 30px;
        margin-right: 15px;
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        user-select: none;
        height: 100%;
        overflow: hidden;
    }

    .drop-down-block {
        @include HcenterVcenterC;

        position: relative;
        width: 100%;
        height: auto;

        .drop-down-item {
            @include HcenterVcenter;

            position: relative;
            width: 100%;
            height: 45px;
        }
    }

    .d-1 {
        position: relative;
        width: 100%;
        height: 80px;
        background: linear-gradient(rgba(0, 0, 0, 1), rgba(0, 0, 0, 0));
        display: flex;
        justify-content: space-between;
        align-items: center;
        z-index: 2;

        .left-block {
            @include Vcenter;

            .logo {
                width: auto;
                height: 35px;
                margin-left: 15px;
                z-index: 2;
                filter: grayscale(0.6) brightness(150%);
            }

            .left-info {
                margin-left: 10px;
                font-size: 20px;
                color: rgba(225, 220, 220, 0.92);
                font-weight: 400;
                font-style: italic;
                user-select: none;
            }
        }

        .link-block {
            position: relative;
            width: 90%;
            flex: 1;
            height: 100%;
            display: flex;
            justify-content: flex-end;
            align-items: center;

            .a_link {
                margin-right: 30px;
                font-size: 16px;
                font-family: '微软雅黑';
                color: rgba(234, 233, 238, 0.8);
                text-decoration: none;
                transition: all 0.3s;
                cursor: pointer;

                &:hover {
                    color: rgba(255, 255, 255, 1);
                }

                &:active {
                    color: rgba(234, 233, 238, 1);
                }
            }
        }
    }

    .s-link-block {
        @include HcenterC;

        position: fixed;
        width: 100%;
        height: 100%;
        padding: 15px;
        padding-top: 75px;

        .s-link {
            width: 100%;
            height: auto;
            padding-left: 15px;
            margin-top: 5px;
            margin-bottom: 15px;
            font-family: '微软雅黑';
            font-size: 13.8px;
            color: rgba(234, 233, 238, 0.8);
            text-align: left;
            text-decoration: none;
            float: left;
            cursor: pointer;

            &:hover {
                color: rgba(255, 255, 255, 1);
            }

            &:active {
                color: rgba(234, 233, 238, 1);
            }
        }
    }

    .nav-icon {
        width: auto;
        height: 35x;
        margin: 5px 25px 0 25px;
        color: rgba(242, 242, 242, 1);
        font-size: 18px;
        visibility: hidden;
        display: none;
        float: right;
        z-index: 2;
    }
}

@media screen and (max-width: 1024px) {
    .main_block {
        .left-block {
            @include Vcenter;

            .left-info {
                display: none;
            }
        }

        .link-block {
            display: none;
        }

        .s-link-block {
            position: fixed;
            left: 0px;
            top: 0px;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            text-align: center;
            z-index: -1;
            display: flex;
            backdrop-filter: blur(8px);
            -webkit-backdrop-filter: blur(8px);
        }

        .nav-icon {
            visibility: visible;
            display: flex;
        }
    }
}
</style>
