<template>
    <div class="df-settings-container" :class="[{ dark: theme === 'dark' }]">
        <div class="major-container">
            <div class="title-block">
                <p class="main-title">{{ local('Settings') }}</p>
            </div>
            <div class="content-block">
                <fv-Collapse :theme="theme" class="serving-item" :icon="theme === 'light' ? 'Light' : 'QuietHours'"
                    :title="local('Switch Theme')" :content="local('Change the theme of the DataFlow WebUI.')"
                    :disabled-collapse="true" :max-height="'auto'">
                    <template #extension>
                        <fv-toggle-switch :theme="theme" v-model="themeModel" :on="'Dark'"
                            :off="'Light'"></fv-toggle-switch>
                    </template>
                </fv-Collapse>
                <fv-Collapse :theme="theme" class="serving-item" icon="LocaleLanguage" :title="local('Language')"
                    :content="local('Change the language of the DataFlow WebUI.')" :disabled-collapse="true"
                    :max-height="'auto'">
                    <template #extension>
                        <fv-combobox :theme="theme" v-model="languageModel" :options="languageList"
                            style="width: 120px;"></fv-combobox>
                    </template>
                </fv-Collapse>
            </div>
        </div>
    </div>
</template>

<script>
import { mapState, mapActions } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'
import { useTheme } from '@/stores/theme'

export default {
    data() {
        return {
            languageList: [
                {
                    key: 'en',
                    text: 'English'
                },
                {
                    key: 'zh',
                    text: '中文'
                }
            ],
            lock: {
                update: true
            }
        }
    },
    watch: {
        language() {
            this.reviseConfig()
        },
        theme() {
            this.reviseConfig()
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local', 'language']),
        ...mapState(useTheme, ['theme', 'color', 'gradient']),
        themeModel: {
            get() {
                if (this.theme == undefined) return false
                return this.theme === 'light' ? false : true
            },
            set(val) {
                this.reviseTheme(val ? 'dark' : 'light')
            }
        },
        languageModel: {
            get() {
                if (this.language == undefined) return {
                    key: 'en',
                    text: 'English'
                }
                return this.languageList.find(item => item.key === this.language)
            },
            set(val) {
                let language = this.languageList.find(item => item.key === val.key)
                if (language) {
                    this.reviseLanguage(language.key)
                }
            }
        },
    },
    mounted() {
        this.getConfig()
    },
    methods: {
        ...mapActions(useAppConfig, ['reviseLanguage']),
        ...mapActions(useTheme, ['reviseTheme']),
        getConfig() {
            this.$api.preferences.get_preferences_api_v1_preferences__get().then(res => {
                if (res.code === 200) {
                    if (res.data.language) {
                        this.reviseLanguage(res.data.language)
                    }
                    if (res.data.theme) {
                        this.reviseTheme(res.data.theme)
                    }
                }
            })
        },
        reviseConfig() {
            if (!this.lock.update) return
            this.lock.update = false
            this.$api.preferences.set_preferences_api_v1_preferences__post({
                language: this.language,
                theme: this.theme
            }).then(res => {
                if (res.code === 200) {
                    this.lock.update = true
                }
            }).finally(() => {
                this.lock.update = true
            })
        }
    }
}
</script>

<style lang="scss">
.df-settings-container {
    position: relative;
    width: 100%;
    height: 100%;
    background-color: rgba(241, 241, 241, 1);
    display: flex;
    justify-content: center;

    &.dark {
        background: rgba(36, 36, 36, 1);

        .major-container {
            .title-block {
                .main-title {
                    color: whitesmoke;
                }
            }
        }
    }

    .major-container {
        width: 100%;
        max-width: 1200px;
        height: 100%;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;

        .title-block {
            position: absolute;
            width: 100%;
            padding: 15px;
            padding-top: 30px;
            z-index: 1;
            backdrop-filter: blur(20px);

            .main-title {
                font-size: 28px;
                font-weight: 400;
                color: rgba(26, 26, 26, 1);
            }
        }

        .content-block {
            position: relative;
            width: 100%;
            height: 100%;
            gap: 5px;
            padding: 15px;
            padding-top: 100px;
            display: flex;
            flex-direction: column;
            overflow: overlay;

            .serving-item {
                flex-shrink: 0;

                .collapse-item-content {
                    position: relative;
                    height: auto;
                    transition: all 0.3s;
                }

                .serving-item-title {
                    margin: 5px 0px;
                    font-size: 13.8px;
                    font-weight: bold;
                    color: rgba(123, 139, 209, 1);
                    user-select: none;
                }

                .serving-item-light-title {
                    margin: 5px 0px;
                    font-size: 12px;
                    color: rgba(95, 95, 95, 1);
                    user-select: none;
                }

                .serving-item-info {
                    margin: 5px 0px;
                    font-size: 12px;
                    color: rgba(120, 120, 120, 1);
                    user-select: none;
                }

                .serving-item-std-info {
                    font-size: 13.8px;
                    color: rgba(27, 27, 27, 1);
                    user-select: none;
                }

                .serving-item-bold-info {
                    margin: 5px 0px;
                    font-size: 16px;
                    font-weight: bold;
                    color: rgba(27, 27, 27, 1);
                    user-select: none;
                }

                .serving-item-p-block {
                    position: relative;
                    width: 100%;
                    height: auto;
                    padding: 15px 0px;
                    box-sizing: border-box;
                    line-height: 3;
                    display: flex;
                    flex-direction: column;
                }

                .serving-item-row {
                    position: relative;
                    width: 100%;
                    padding: 0px 42px;
                    flex-wrap: wrap;
                    box-sizing: border-box;
                    display: flex;
                    align-items: center;

                    &.no-pad {
                        padding: 0px;
                    }

                    &.sep {
                        justify-content: space-between;
                    }

                    &.column {
                        flex-direction: column;
                        align-items: flex-start;
                    }

                    &.full {
                        flex: 1;
                    }

                    &.auto {
                        overflow: auto;
                    }
                }

                hr {
                    margin: 10px 0px;
                    border: none;
                    border-top: rgba(120, 120, 120, 0.1) solid thin;
                }
            }
        }
    }

    .rainbow {
        @include color-rainbow;

        color: black;
    }

    .ring-animation {
        animation: ring-rotate 1s linear infinite;
    }

    @keyframes ring-rotate {
        0% {
            transform: rotate(0deg);
        }

        100% {
            transform: rotate(360deg);
        }
    }
}
</style>
