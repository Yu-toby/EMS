<script setup></script>

<template>
    <div>
        <!-- 上傳圖片的表單 -->
        <form @submit.prevent="uploadData">
            <div>
                <label for="category">Category:</label>
                <input type="text" id="category" v-model="formData.category"/>
            </div>
            <div>
                <label for="max">Max:</label>
                <input type="text" id="max" v-model="formData.max"/>
            </div>
            <div>
                <label for="avg">Avg:</label>
                <input type="text" id="avg" v-model="formData.avg"/>
            </div>
            <div>
                <label for="min">Min:</label>
                <input type="text" id="min" v-model="formData.min"/>
            </div>
            <div>
                <label for="result">Result:</label>
                <input type="text" id="result" v-model="formData.result"/>
            </div>
            <div>
                <label for="image">Image:</label>
                <input type="file" name="image" accept="image/*" @change="handleImageUpload" ref="fileInput" />
            </div>
            <button type="submit">上傳</button>
        </form>

        <!-- 顯示數據 -->
        <div v-for="item in data" :key="item._id">
            <!-- <p>{{ item. _id}}</p> -->
            <p>category: {{ item.category }}</p>
            <p>uploadTime: {{ item.time }}</p>
            <p>Max: {{ item.max }}</p>
            <p>Avg: {{ item.avg }}</p>
            <p>Min: {{ item.min }}</p>
            <p>Result: {{ item.result }}</p>
            <img :src="item.image" alt="Uploaded Image" style="height: 150px;" />
            <button @click="deleteData(item._id)">刪除</button>
        </div>
    </div>
</template>

<script>
export default {
    data() {
        return {
            formData: {
                category: '',
                max: '',
                avg: '',
                min: '',
                result: '',
                image: null
            },
            data: [],
            intervalId: null,
            ifDetectStatus: 0, // 初始狀態為0
            uploadTime: ''
        }
    },
    methods: {
        uploadData() {
            const now = new Date();
            const year = now.getFullYear(); // 取得年份
            const month = (now.getMonth() + 1).toString().padStart(2, '0'); // 取得月份，並補零
            const day = now.getDate().toString().padStart(2, '0'); // 取得日期，並補零
            const hour = now.getHours().toString().padStart(2, '0'); // 確保是兩位數
            const minute = now.getMinutes().toString().padStart(2, '0'); // 確保是兩位數
            this.uploadTime = `${year}${month}${day}-${hour}${minute}`; // 格式化日期為 "年月日"
            console.log(this.uploadTime);

            const formData = new FormData()
            formData.append('category', this.formData.category)
            formData.append('uploadTime', this.uploadTime)
            formData.append('result', this.formData.result)
            formData.append('max', this.formData.max)
            formData.append('avg', this.formData.avg)
            formData.append('min', this.formData.min)            
            formData.append('image', this.formData.image)

            this.axios.post('/tsmcserver', formData).then((res) => {
                if (res.data.status == 'success') {
                    this.GetToDo()
                    this.formData.category = ''
                    this.formData.result = ''
                    this.formData.max = ''
                    this.formData.avg = ''
                    this.formData.min = ''                    
                    this.formData.image = ''
                    this.$refs.imageInput.value = ''
                } else {
                    console.error('新增失敗')
                }
            })
        },
        handleImageUpload(event) {
            // 處理圖片上傳事件
            this.formData.image = event.target.files[0]
        },
        GetToDo() {
            this.axios.get('/tsmcserver').then((res) => {
                this.data = res.data
            })
        },
        deleteData(id) {
            this.axios.delete('/tsmcserver', { data: { index: id } }).then((res) => {
                if (res.data.status == 'success') {
                    this.GetToDo()
                } else {
                    console.error('刪除失敗')
                }
            })
        },
        toggleIfDetect() {
      // 向後端發送POST請求來切換if_detect狀態
        this.axios.post('/tsmcserver/if_detect').then((res) => {
        if (res.data.status === 'success') {
          // 更新ifDetectStatus以反映新的狀態
            this.ifDetectStatus = res.data.new_number;
        } else {
            console.error('if_detect切換失敗');
        }
        });
    }

    },
    mounted() {
        this.GetToDo()
        this.intervalId = setInterval(this.GetToDo, 1000)
    },
    beforeUnmount() {
        clearInterval(this.intervalId)
    }
}
</script>

<style>
</style>