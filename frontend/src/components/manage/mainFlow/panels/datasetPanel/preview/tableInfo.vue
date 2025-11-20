<template>
    <div class="collapse-item-content">
        <div class="control-block">
            <fv-button
                background="transparent"
                border-radius="8"
                style="width: 30px; height: 30px"
                @click="$emit('back')"
            >
                <i class="ms-Icon ms-Icon--Back"></i>
            </fv-button>
            <p>{{ local('Back') }}</p>
        </div>
        <div class="table-wrapper">
            <i v-show="!tableInfo.length" class="empty-icon ms-Icon ms-Icon--Important"></i>
            <p v-show="!tableInfo.length" class="empty-title">{{ local('No Data') }}</p>
            <fv-details-list
                v-show="tableInfo.length"
                :model-value="tableInfo"
                :head="heads"
                ref="table"
                style="width: 100%; height: 100%"
            >
                <template v-for="(col, i) in heads" :key="i + 1" v-slot:[`column_${i}`]="x">
                    <p :title="i == 0 ? x.row_index + 1 : x.item[col.key] ? x.item[col.key] : ''">
                        {{ i == 0 ? x.row_index + 1 : x.item[col.key] ? x.item[col.key] : '' }}
                    </p>
                </template>
            </fv-details-list>
        </div>
        <fv-pagination
            v-show="pages > 0 && tableInfo.length"
            v-model="currentPage"
            :total="pages"
            background="rgba(255, 255, 255, 1)"
            foreground="rgba(111, 92, 196, 1)"
            :small="true"
            style="width: 100%; height: 35px; margin-top: 5px"
        />
    </div>
</template>

<script>
import { mapState } from 'pinia'
import { useAppConfig } from '@/stores/appConfig'

export default {
    props: {
        item: {
            type: Object,
            default: () => ({})
        }
    },
    data() {
        return {
            num_per_page: 10,
            currentPage: 1,
            heads: [],
            tableInfo: []
        }
    },
    watch: {
        currentPage() {
            this.getTableData(false)
        }
    },
    computed: {
        ...mapState(useAppConfig, ['local']),
        pages() {
            return Math.ceil(this.item.num_samples / this.num_per_page)
        }
    },
    mounted() {
        this.getTableData()
    },
    methods: {
        getTableData(refreshHead = true) {
            if (!this.item.id) return
            this.$api.datasets
                .get_pandas_data(
                    this.item.id,
                    (this.currentPage - 1) * this.num_per_page,
                    this.currentPage * this.num_per_page
                )
                .then((res) => {
                    if (res.code === 200) {
                        this.tableInfo = JSON.parse(res.data)
                        if (refreshHead) this.getHeads()
                    }
                })
        },
        getHeads() {
            if (!this.tableInfo.length) return []
            let heads = []
            heads.push({
                key: 'index',
                content: '#',
                minWidth: 60,
                width: 60
            })
            for (let key in this.tableInfo[0]) {
                heads.push({
                    key,
                    content: key,
                    minWidth: 80,
                    width: 150,
                    sortName: key
                })
            }
            heads[heads.length - 1].width = 900
            this.heads = heads
            this.$nextTick(() => {
                this.$refs.table.headInit()
            })
        }
    }
}
</script>

<style lang="scss">
.control-block {
    position: relative;
    width: 100%;
    height: 35px;
    padding: 5px;
    gap: 5px;
    font-size: 13.8px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    margin-bottom: 10px;
}

.table-wrapper {
    position: relative;
    width: 100%;
    height: 500px;
    padding: 5px;
    background: white;
    border: 1px solid rgba(120, 120, 120, 0.1);
    border-radius: 8px;
    box-shadow: 0px 1px 3px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    overflow: hidden;

    .empty-icon {
        font-size: 40px;
        color: rgba(120, 120, 120, 0.5);
    }

    .empty-title {
        font-size: 16px;
        color: rgba(120, 120, 120, 0.5);
    }
}
</style>
