<template>
    <div class="bottom-block">
        <div class="logo">
            <img draggable="false" src="@/assets/logo/logo.png" alt="" />
            <p>Dataflow</p>
        </div>
        <div class="info-container">
            <div v-show="false" class="info-block" :span="6">
                <p>Research Group</p>
                <a href="https://xinyizhang-pku.github.io/" title="zhang_xinyi@pku.edu.cn"
                    >Database: Xinyi Zhang</a
                >
                <a
                    href="https://scholar.google.com/citations?user=vFYm_QEAAAAJ&hl=zh-CN"
                    title="ccchengfu@pku.edu.cn"
                    >ML Systems: Fangcheng Fu</a
                >
                <a href="https://zwt233.github.io/" title="wentao.zhang@pku.edu.cn"
                    >Data-centric ML</a
                >
                <a href="https://salty-fish-97.github.io/" title="shenyu@pku.edu.cn"
                    >AutoML: Yu Shen</a
                >
            </div>
            <div class="info-block" :span="6">
                <p>Quick Links</p>
                <a href="https://www.pku.edu.cn/">Peking University</a>
                <a href="https://cs.pku.edu.cn/">School of Computer Science, PKU</a>
                <a href="https://github.com/PKU-DAIR">Github of PKU-DAIR</a>
            </div>
            <div v-show="false" class="info-block" :span="6">
                <p>Contact</p>
                <a>Phone: +86 10 62765821 (Office)</a>
                <a>+86 10 62765822 (Fax)</a>
                <a>Office: 1630, Science BLK 1</a>
                <a>E-mail: bin.cui@pku.edu.cn</a>
            </div>
            <div class="info-block" :span="6">
                <p>Developer</p>
                <a href="https://github.com/aleversn" title="lpc@pku.edu.cn">Peichao Lai</a>
            </div>
        </div>
        <div class="copyright">
            <p>© {{ new Date().getFullYear() }} PKU DAIR Lab</p>
            <p class="oth-item">School of Computer Science, Peking University</p>
        </div>
    </div>
</template>

<style lang="scss" scoped>
.bottom-block {
    @include HcenterC;
    position: relative;
    width: 100%;
    height: auto;
    padding: 35px calc(50% - 640px);
    background: rgba(19, 19, 19, 0);
    box-sizing: border-box;

    .logo {
        @include HcenterVcenter;
        position: relative;
        width: 100%;
        display: flex;
        justify-content: flex-start;
        img {
            width: 35px;
            height: auto;
            user-select: none;
        }

        p {
            margin-left: 10px;
            font-size: 15px;
            font-style: italic;
            color: rgba(245, 245, 245, 0.6);
        }
    }

    .info-container {
        position: relative;
        width: 100%;
        height: auto;
        margin-top: 35px;
        padding: 15px;
        box-sizing: border-box;
        display: flex;

        .info-block {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            line-height: 2.5;

            p {
                font-weight: bold;
                color: rgba(245, 245, 245, 0.9);
            }

            a {
                font-size: 12px;
                font-weight: lighter;
                color: rgba(245, 245, 245, 0.8);
                text-decoration: none;

                &:hover {
                    text-decoration: underline;
                }
            }
        }
    }

    .copyright {
        @include Vcenter;
        position: relative;
        width: 100%;
        height: 35px;
        margin-top: 35px;
        font-size: 13px;
        color: rgba(245, 245, 245, 0.8);

        .oth-item {
            margin-left: 10px;
        }
    }
}

@media screen and (max-width: 1280px) {
    .bottom-block {
        padding: 15px;
    }
}

@media screen and (max-width: 760px) {
    .bottom-block {
        padding: 25px;

        .info-container {
            flex-direction: column;
        }

        .bottom-info-container {
            display: flex;
            flex-direction: column;
        }

        .copyright {
            @include VcenterC;

            .oth-item {
                margin-left: 1px;
            }
        }
    }
}
</style>
