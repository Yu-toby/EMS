<template>
    <header class="navbar">
        <div class="header-logo">
            <img id="tsmc-logo" src="@/assets/picture/台積logo.png" />
            <a id="title-words">台積電熱影像辨識網頁</a>
        </div>
        <div class="options">
            <router-link to="/logout" >登出</router-link>
            <router-link to="/settings" >設定</router-link>
            <router-link to="/resultsShow" >辨識結果顯示</router-link>
            <router-link to="/" >首頁</router-link>
        </div>
    </header>
</template>

<script>
export default {}
</script>

<style scoped>
.navbar {
    overflow: hidden;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: rgb(255, 242, 204);
    height: 55px;
    padding: 0px;
}
/*----------------------------------------------------------------------------------*/
.header-logo {    
    display: flex;
    color: black;
    align-items: center;
    padding: 0px;    
}
#tsmc-logo {
    padding: 10px;
    height: 55px;
}
#title-words {
    font-weight: bold;
    font-size: 23px;
}
/*----------------------------------------------------------------------------------*/
.options a {    
    font-size: 18px;
    font-weight: bold;
    float: right;
    color: rgb(36, 30, 9);
    padding: 5px 10px;
    border-radius: 500px;
    text-decoration: none;
}

.options a:hover {
    background-color: rgba(3, 3, 3, 0.6);
    color: rgb(255, 242, 204);
}
</style>
