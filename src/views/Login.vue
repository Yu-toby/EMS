<script setup></script>

<template>
    <div id="container">
        <div id="greet">
            <h1 class="hello1">你好，使用者</h1>
            <h1 class="hello2">歡迎來到測試網頁</h1>
        </div>
        <div action="" class="login">
            <h1>登入</h1>
            <i class="fa fa-user-circle-o"></i>
            <h2>帳號</h2>
            <input type="text" id="name" placeholder="請輸入帳號" v-model="username" />
            <h2>密碼</h2>
            <input type="password" id="pwd" placeholder="請輸入密碼" v-model="password" />
            <button type="submit" id="btn" @click="login">登入</button>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            username: '',
            password: ''
        }
    },
    methods: {
        login() {
            if (this.username == '') {
                alert('帳號不得為空白')
            } else if (this.password != '123') {
                alert('密碼錯誤')
            } else {
                this.$router.push('/')
            }
        }
    }
}
</script>

<style scoped>
#container {
    height: 100vh;
    width: 100%;
    color: white;
    background: linear-gradient(90deg, rgb(128, 128, 0), rgb(0, 128, 128));
}

#greet {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
}
#greet h1 {
    font-size: 55px;
    font-family: fantasy;
}

.hello1 {
    opacity: 0;
    animation-name: show;
    animation-duration: 2.5s;
    animation-delay: 0.5s;
    animation-fill-mode: forwards;
}
.hello2 {
    opacity: 0;
    animation-name: show;
    animation-duration: 2.5s;
    animation-delay: 1.5s;
    animation-fill-mode: forwards;
}

@keyframes show {
    0% {
        opacity: 0;
    }
    100% {
        opacity: 1;
    }
}

.login {
    position: fixed;
    left: 50%;
    top: 60%;
    transform: translate(-50%, -50%);
    background: rgba(0, 0, 0, 0.5);
    text-align: center;
    color: #fff;
    border-radius: 10px;
    padding: 30px;
    width: 300px;
}
.login i {
    font-size: 75px;
    margin: 20px auto;
}

input[type='text'],
input[type='password'] {
    font-size: 16px;
    padding: 5px;
    border-radius: 4px;
    margin: 0 auto;
    display: block;
    width: 270px;
}

button {
    border: 0;
    padding: 6px 12px;
    margin-top: 20px;
    font-size: 16px;
    background: #fff;
    color: #000;
}
</style>
