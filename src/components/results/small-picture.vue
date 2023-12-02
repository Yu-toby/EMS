<template>
    <div class="small-picture">
        <img class="picture" :src="src" alt="資訊錯誤" />
    </div>
</template>
<script>
export default {
    props: {
        src: {
            type: String,
            default: ''
        }
    }
}
</script>
<style >
.small-picture {
    overflow: hidden;
    /* box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); */
}

.small-picture img {
    height: 12vh;
    margin-left: 10px;
    margin-right: 10px;
}

.small-picture:hover {
    transform: scale(1.1, 1);
}
</style>