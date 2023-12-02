<template>
    <div class="options">
        <div class="item" id="display-name">
            <input type="file" id="fileInput" />
            <button id="uploadButton">上傳</button>
            <div id="status"></div>
        </div>
        <div class="item" id="drop-down-menu">下拉選單</div>
        <div class="item" id="export"><button>匯出報告</button></div>
    </div>
</template>

<script>
export default {}
</script>

<style scoped>
.options {
    display: grid;
    grid-template-columns: 1fr 2.8fr 1fr 1.7fr 1fr 1fr;
    border: 2px solid black;
}

.item {
    border: 1px solid black;
}

#display-name {
    grid-column: 2;
    display: flex;
    align-items: center;
    justify-content: center;
}

#drop-down-menu {
    grid-column: 4;
    display: flex;
    align-items: center;
    justify-content: center;
}

#export {
    grid-column: 6;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>
