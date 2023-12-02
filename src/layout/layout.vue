<script setup>
import navbar from './navbar.vue'
import footerLayout from './footer.vue'
</script>

<template lang="">
    <div class="container0">
        <navbar></navbar>
        <router-view></router-view>
        <footerLayout></footerLayout>
    </div>
</template>
<script>
export default {}
</script>
<style scoped> 
    .container0 {
        display: grid;
        height: 100vh;
        grid-template-rows: 55px 1fr 35px;
    }
</style>
