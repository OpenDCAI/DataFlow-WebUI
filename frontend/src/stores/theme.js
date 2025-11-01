import onecolor from "onecolor";
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'

export const useTheme = defineStore('useTheme', () => {
    const themeColor = ref('rgba(45, 80, 125, 1)');
    const Theme = ref('light')

    function reviseTheme(themeValue) {
        Theme.value = themeValue;
    }

    const theme = computed(() => Theme.value)
    const color = computed(() => themeColor.value)
    const color01 = computed(() => {
        let color = onecolor(themeColor.value);
        color = color.alpha(0.1);
        return color.cssa();
    })
    const gradient = computed(() => {
        let color = onecolor(themeColor.value);
        color = color.alpha(1);
        let from = color.cssa();
        let hsl = color.hsl();
        let h = Math.round(hsl.h() * 360);
        let s = hsl.s();
        let l = hsl.l();
        h = h + 25;
        s = (s - 0.1).toFixed(2);
        l = (l - 0.06).toFixed(2);
        let to = `hsla(${h}, ${s * 100}%, ${l * 100}%, 1)`;
        return `linear-gradient(to right, ${from}, ${to})`;
    })
    const gradient01 = computed(() => {
        let color = onecolor(themeColor.value);
        color = color.alpha(0.1);
        let from = color.cssa();
        let hsl = color.hsl();
        let h = Math.round(hsl.h() * 360);
        let s = hsl.s();
        let l = hsl.l();
        h = h + 25;
        s = (s - 0.1).toFixed(2);
        l = (l - 0.06).toFixed(2);
        let to = `hsla(${h}, ${s * 100}%, ${l * 100}%, 0.1)`;
        return `linear-gradient(to right, ${from}, ${to})`;
    });
    const gray01 = computed(() => {
        let color = onecolor(themeColor.value);
        color = color.alpha(1);
        let hsl = color.hsl();
        let h = hsl.h();
        let s = 0.1;
        let l = hsl.l();
        return `hsla(${h}, ${s * 100}%, ${l * 100}%, 1)`;
    })

    return {
        reviseTheme, theme, color, color01, gradient, gradient01, gray01
    }
})