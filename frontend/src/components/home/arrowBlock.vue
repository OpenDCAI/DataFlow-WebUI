<template>
    <div class="arrow-container">
        <div class="arrow-row-block" v-for="(item, i) in rows" :key="i">
            <p class="arrow-unit" v-for="(item, j) in cols" :key="`${i},${j}`" :style="getArrowStyle(i, j)">→</p>
        </div>
    </div>
</template>

<script>
import gsap from "gsap";

export default {
    data() {
        return {
            rows: 30,
            cols: 50,
            angle: 180,
            colorR: 255,
            colorG: 90,
            colorB: 255
        }
    },
    watch: {
        angle() {
        }
    },
    mounted() {
        this.loop();
    },
    methods: {
        loop() {
            gsap.to(this.$data, {
                angle: 0,
                duration: 10,
                colorR: 0,
                colorG: 90,
                colorB: 90,
                repeat: 20,
                yoyo: true
            })
        },
        // 计算每个箭头的旋转角度和颜色
        getArrowStyle(i, j) {
            // 计算一个模拟的磁场方向（你可以换成真实磁场数据）
            const angle = Math.sin(i * 0.1) * Math.cos(j * 0.1) * this.angle; // 角度
            const intensity = Math.abs(Math.sin(i * 0.05) * Math.cos(j * 0.05)); // 强度

            // 颜色渐变从淡红到深红
            const color = `rgb(${Math.floor(this.colorR * intensity)}, ${this.colorG}, ${Math.floor(this.colorB * (1 - intensity))})`;

            return {
                transform: `rotate(${angle}deg)`, // 旋转
                color: color, // 颜色
            };
        },
    }
}
</script>

<style lang="scss">
.arrow-container {
    position: relative;
    width: 100%;
    height: auto;
    color: whitesmoke;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-weight: bold;
    user-select: none;

    .arrow-row-block {
        @include HaroundVcenter;

        position: relative;
        width: 100%;

        .arrow-unit {
            font-size: 13.5px;
        }
    }
}
</style>