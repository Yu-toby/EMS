<template>
    <div>
        <button
                    @click="startCheckingIfDetect"
                    id="uploadButton"
                    type="button"
                    class="btn"
                    :class="{ 'btn-primary': !loading, 'btn-secondary': loading }"
                    :disabled="loading"
                >
                    <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    {{ loading ? '辨識中...' : '上傳' }}
                </button>
    </div>
</template>

<script>
export default {
    data() {
        return {
            loading: 0, // 初始值為 0，表示不在加載狀態
        };
    },
    mounted() {
        this.startCheckingIfDetect();
        // this.interval = setInterval(this.check_if_detect, 1000);
    },
    methods: {
        startCheckingIfDetect() {
            // 設定每秒執行一次 checkIfDetect 方法
            this.ifDetectInterval = setInterval(this.check_if_detect, 1000);
        },
        stopCheckingIfDetect() {
            clearInterval(this.ifDetectInterval);
        },
        check_if_detect() {
            console.log('check_if_detect');
            this.axios.get('/tsmcserver/if_detect').then((res) => {
                console.log(res.data);
                this.loading = res.data;
                if (res.data === 0 ) {
                    this.stopCheckingIfDetect();
                }
            });
        },
    },
};
</script>
