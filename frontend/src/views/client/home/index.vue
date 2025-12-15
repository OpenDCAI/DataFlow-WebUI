<template>
    <div class="home-container">
        <banner-block></banner-block>
        <fv-img
            class="main-bg"
            :src="img.mainBG"
            alt=""
            :style="{ height: `${screenWidth / 1.98}px` }"
        ></fv-img>
        <div
            class="d-block-1"
            style="margin-bottom: 150px"
            :style="{ height: `${screenWidth / 2.18}px` }"
        >
            <div class="left-block">
                <div class="intro-title-block">
                    <p class="intro-title">DAIR Lab</p>
                    <p class="intro-sub-title">Data and Intelligence Research in PKU</p>
                </div>
            </div>
            <div class="right-block">
                <p class="intro-content">
                    Welcome to the DAIR Lab! We are part of the School of Computer Science at Peking
                    University (PKU). Together we enjoy working on Database, ML Systems,
                    Data-centric ML, AutoML, etc.
                </p>
            </div>
        </div>
        <arrow-block style="width: 90%; max-width: 1368px; margin: 175px 0px"></arrow-block>
        <div class="d-block-1">
            <div v-for="(item, index) in unitBlockList" :key="index" class="unit-block">
                <p class="unit-title">{{ item.title }}</p>
                <p class="unit-content">
                    {{ item.content }}
                </p>
                <p
                    class="unit-link"
                    @click="
                        () => {
                            item.url ? $Jump(item.url) : ''
                        }
                    "
                >
                    Read More
                </p>
            </div>
        </div>
        <bottom-block></bottom-block>
        <div class="ret-top-div" @click="retop">
            <span class="ms-Icon ms-Icon--ChevronUp" style="color: rgba(242, 242, 242, 1)"></span>
        </div>
    </div>
</template>

<script>
import gsap from 'gsap'
import bannerBlock from '@/components/general/bannerBlock.vue'
import bottomBlock from './bottomBlock.vue'
import arrowBlock from '@/components/home/arrowBlock.vue'
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'

import mainBG from '@/assets/pku/pku.jpg'

export default {
    components: {
        bannerBlock,
        bottomBlock,
        arrowBlock
    },
    data() {
        return {
            unitBlockList: [
                {
                    title: 'Research Directions',
                    content:
                        'Our lab explores innovative areas such as ML System, Data-Centric, Database and AutoML. We focus on developing algorithms and systems that understand, learn, and interact with the world intelligently.',
                    url: 'https://github.com/PKU-DAIR/Starter-Guide?tab=readme-ov-file#ai%E7%B3%BB%E7%BB%9F%E6%96%B9%E5%90%91-'
                },
                {
                    title: 'Research Publications',
                    content:
                        'Discover our latest research contributions through our published papers. Our work covers theoretical foundations and practical applications in ML System, Data-Centric and related fields.',
                    url: '/pub'
                },
                {
                    title: 'Open Source Projects',
                    content:
                        'We actively contribute to the AI community through open-source projects. Explore our tools, libraries, and frameworks designed to advance research and collaboration in AI.',
                    url: '/projs'
                }
            ],
            img: {
                mainBG
            },
            show: {
                mobileNav: false
            }
        }
    },
    watch: {},
    mounted() {
        this.$Go('/m')
    },
    computed: {
        ...mapState(useAppConfig, {
            screenWidth: 'screenWidth'
        })
    },
    methods: {
        retop() {
            gsap.to(document.querySelector('.home-container'), {
                scrollTop: 0,
                duration: 0.5
            })
        }
    }
}
</script>

<style lang="scss">
.home-container {
    @include app;

    width: 100%;
    height: 100%;
    background: rgba(23, 17, 24, 1);
    display: flex;
    flex-direction: column;
    align-items: center;
    overflow: auto;
    overflow-x: hidden;

    .main-bg {
        position: absolute;
        width: 100%;
        min-height: 600px;
        object-fit: cover;
        object-position: 50% 50%;
        opacity: 0.2;
        filter: saturate(0.6);
    }

    .d-block-1 {
        position: relative;
        width: 100%;
        max-width: 1360px;
        min-height: 600px;
        height: auto;
        flex-shrink: 0;
        padding-top: 200px;
        color: rgba(234, 233, 238, 1);
        display: flex;
        justify-content: space-between;
        align-items: flex-start;

        .left-block {
            @include HcenterVcenterC;

            position: relative;
            width: 40%;
            max-width: 400px;
            height: 100%;
            line-height: 2;

            .intro-title-block {
                @include HcenterVcenterC;

                position: relative;
                width: 350px;

                .intro-title {
                    font-weight: 600;
                    font-size: 58px;
                }

                .intro-sub-title {
                    font-size: 18px;
                    font-weight: 600;
                }
            }
        }

        .right-block {
            @include HcenterVcenterC;

            position: relative;
            width: 10px;
            flex: 1;
            height: 100%;

            .intro-content {
                max-width: 500px;
                font-weight: 400;
                font-size: 24px;
                line-height: 2;
                color: rgba(200, 194, 201, 1);
                text-align: left;
            }
        }

        .unit-block {
            @include HstartC;

            position: relative;
            width: 50%;
            flex: 1;
            padding: 15px 35px;
            line-height: 1.5;

            .unit-title {
                margin-bottom: 25px;
                font-weight: 400;
                font-size: 24px;
            }

            .unit-content {
                margin-bottom: 25px;
                max-width: 300px;
                font-size: 13px;
                color: rgba(200, 194, 201, 1);
                text-align: left;
            }

            .unit-link {
                font-size: 13px;
                font-family: 'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande',
                    'Lucida Sans Unicode', Geneva, Verdana, sans-serif;
                color: rgba(200, 194, 201, 1);
                border-bottom: rgba(200, 194, 201, 1) solid 2px;
                text-align: left;
                user-select: none;
                transition: all 0.3s;
                cursor: pointer;

                &:hover {
                    transform: translateY(5%);
                }

                &:active {
                    transform: translateY(5%) scale(0.9);
                }
            }
        }
    }

    .d-block-2 {
        position: relative;
        width: 100%;
        height: auto;
        flex-shrink: 0;

        .team-banner {
            position: absolute;
            width: 100%;
            height: 100%;
            object-fit: cover;
            object-position: 50% 50%;
        }

        .mask-container {
            @include HcenterVcenter;

            position: relative;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.6);
        }
    }

    .ret-top-div {
        position: fixed;
        bottom: 45px;
        right: 0;
        width: 35px;
        height: 35px;
        background: rgba(0, 0, 0, 0.8);
        border-top-left-radius: 5px;
        border-bottom-left-radius: 5px;
        cursor: pointer;
        display: flex;
        justify-content: center;
        align-items: center;
        transition: all 0.5s;

        &:hover {
            background: rgba(0, 120, 212, 1);
        }
    }

    .login {
        font-size: 18px;
        font-family: '微软雅黑';
        font-weight: 100;
        text-align: center;
        color: rgba(255, 255, 255, 1);
        border: rgba(255, 255, 255, 1) solid 1px;
        border-radius: 5px;
        cursor: pointer;
    }
}

@media screen and (max-width: 1024px) {
    .home-container {
        .d-block-1 {
            flex-direction: column;
            flex-wrap: wrap;

            .left-block {
                width: 100%;
                max-width: 100%;
                height: 500px;
                flex-direction: column;
                flex-wrap: wrap;
            }

            .right-block {
                width: 100%;
                height: auto;
                padding: 25px;
            }

            .unit-block {
                width: 100%;
            }
        }
    }

    .container-text {
        position: relative;
        width: 100%;
        height: 100px;
        left: 0;
        top: 0;
        font-family: '微软雅黑';
        font-size: 24px;
        font-weight: 100;
        color: rgba(36, 36, 36, 0.7);
        text-shadow: 1px 1px 10px rgba(36, 36, 36, 0.3);
        text-align: center;
        float: left;
    }
}
</style>
