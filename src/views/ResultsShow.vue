<script setup>
import SmallPicture from '@/components/results/small-picture.vue'
import Detail from '@/components/results/detail.vue'
import * as XLSX from 'xlsx'
</script>

<template>
    <div class="container1">
        <div class="optionsbar">
            <div class="item" id="display-name">
                <input type="file" id="fileInput" ref="fileInput" multiple />
                <button
                    @click="uploadFiles"
                    id="uploadButton"
                    type="button"
                    class="btn"
                    :class="{ 'btn-secondary': !loading, 'btn-dark': loading }"
                    :disabled="loading"
                >
                    <span v-if="loading" class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                    {{ loading ? '辨識中...' : '上傳' }}
                </button>
                <div id="status"></div>
            </div>
            <div class="dropdown item" id="drop-down-menu">
                <select v-model="selectedOption" @change="updatePieChart(); getCategories()">
                    <option value="" disabled selected>請選擇類別</option>
                    <option
                        v-for="(category, index) in categories"
                        :key="index"
                        :value="category"
                    >{{ category }}</option>
                </select>
                <!-- <button
                    class="btn btn-secondary dropdown-toggle"
                    type="button"
                    id="dropdownMenuButton2"
                    data-bs-toggle="dropdown"
                    aria-expanded="false"
                >下拉選單</button>
                <ul class="dropdown-menu dropdown-menu-dark" aria-labelledby="dropdownMenuButton1" >
                    <li v-for="(option, index) in options" :key="index">
                        <a class="dropdown-item" href="#">{{ option }}</a>
                    </li>
                </ul>-->
            </div>
            <div class="item" id="export">
                <button type="button" class="btn btn-secondary" @click="exportExcel">匯出報告</button>
            </div>
        </div>

        <div class="content">
            <div class="item" id="last-page">
                <!-- <button
                    type="button"
                    class="btn btn-outline-secondary btn-sm"
                    id="last-page-button"
                >
                    上一頁
                </button>-->
            </div>

            <div class="item" id="pie-chart">
                <!-- <div id="pie-chart-title"><p>123</p></div> -->
                <div ref="chartRef" style="width: 100%; height: 90%"></div>
            </div>

            <div class="item" id="thumbnail">
                <div id="normal">
                    <p class="status-text">正常</p>
                    <div class="picture" id="nor-pic">
                        <div
                            v-for="(details, index) in details"
                            :src="details.image"
                            :key="index"
                            @click="show(index)"
                        >
                            <SmallPicture
                                v-if="details.result === '正常' && details.category === selectedOption && details.time === uploadTime"
                                :src="details.image"
                            ></SmallPicture>
                        </div>
                    </div>
                </div>

                <div id="notice">
                    <P class="status-text">注意</P>
                    <div class="picture" id="not-pic">
                        <div
                            v-for="(details, index) in details"
                            :src="details.image"
                            :key="index"
                            @click="show(index)"
                        >
                            <SmallPicture
                                v-if="details.result === '注意' && details.category === selectedOption && details.time === uploadTime"
                                :src="details.image"
                            ></SmallPicture>
                        </div>
                    </div>
                </div>

                <div id="abnormal">
                    <p class="status-text">異常</p>
                    <div class="picture" id="abn-pic">
                        <div
                            v-for="(details, index) in details"
                            :src="details.image"
                            :key="index"
                            @click="show(index)"
                        >
                            <SmallPicture
                                v-if="details.result === '異常' && details.category === selectedOption && details.time === uploadTime"
                                :src="details.image"
                            ></SmallPicture>
                        </div>
                    </div>
                </div>

                <div id="danger">
                    <p class="status-text">危險</p>
                    <div class="picture" id="dan-pic">
                        <div
                            v-for="(details, index) in details"
                            :src="details.image"
                            :key="index"
                            @click="show(index)"
                        >
                            <SmallPicture
                                v-if="details.result === '危險' && details.category === selectedOption && details.time === uploadTime"
                                :src="details.image"
                            ></SmallPicture>
                        </div>
                    </div>
                </div>
                <Detail
                    :src="details[showIndex].image"
                    :bcolor="details[showIndex].result === '正常' ? 'rgb(226, 245, 215)' : details[showIndex].result === '注意' ? 'rgb(255, 243, 205)' : details[showIndex].result === '異常' ? 'rgb(248, 215, 178)' : 'rgb(245, 215, 215)'"
                    :tbcolor="details[showIndex].result === '正常' ? 'rgb(124, 208, 72)' : details[showIndex].result === '注意' ? 'rgb(255, 200, 25)' : details[showIndex].result === '異常' ? 'rgb(191, 108, 17)' : 'rgb(181, 59, 59)'"
                    :describe="details[showIndex]"
                    v-show="showModal"
                    @close="showModal = false"
                ></Detail>
            </div>
            <div class="item" id="next-page">
                <!-- <button
                    type="button"
                    class="btn btn-outline-secondary btn-sm"
                    id="next-page-button"
                >
                    下一頁
                </button>-->
            </div>
        </div>
    </div>
</template>

<script>
import * as echarts from 'echarts'
import { markRaw } from 'vue'

export default {
    data() {
        return {
            chart: null,
            
            showIndex: 0,
            showModal: false,
            options: ['風扇', '電線', '保險絲', '繼電器', '...'],
            details: [{}],
            selectedOption: '', // 綁訂下拉選單與圓餅圖標題
            chartData: [
                // 初始化數據
                { value: 0, name: '正常' },
                { value: 0, name: '注意' },
                { value: 0, name: '異常' },
                { value: 0, name: '危險' }
            ],
            categories: [], // 新增用來存放 MongoDB 中的類別選項
            loading: 0,
            uploadTime: ''
        }
    },
    mounted() {
        this.chart = markRaw(echarts.init(this.$refs.chartRef))

        var option = {
            title: {
                text: '',
                left: 'center',
                textStyle: {
                    fontSize: 40
                },
                top: '3%'
            },
            tooltip: {
                trigger: 'item'
            },
            legend: {
                bottom: '0%',
                left: 'center',
                textStyle: {
                    fontSize: 25 // 使用圖例字體大小
                },
                itemGap: 20, // 使用圖例標籤間距
                formatter: function (name) {
                    // 在圖例中顯示資料數量
                    var dataItem = option.series[0].data.find(function (item) {
                        return item.name === name
                    })
                    return name + ':' + dataItem.value
                }
            },
            series: [
                {
                    // name: '設備名稱',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: '#fff',
                        borderWidth: 2,
                        normal: {
                            color: function (colors) {
                                var colorList = [
                                    'rgb(124, 208, 72)',
                                    'rgb(255, 200, 25)',
                                    'rgb(191, 108, 17)',
                                    'rgb(181, 59, 59)'
                                ]
                                return colorList[colors.dataIndex]
                            }
                        }
                    },
                    label: {
                        show: false,
                        position: 'center'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 40,
                            fontWeight: 'bold'
                        }
                    },
                    labelLine: {
                        show: false
                    },
                    data: this.chartData // 使用響應式數據
                }
            ]
        }

        this.chart.setOption(option)

        window.addEventListener('resize', this.resizeHandler)

        //獲取時間紀錄
        this.GetTimeRecord()

        //API
        this.GetToDo()
        this.intervalId = setInterval(this.GetToDo, 1000)

        // 在 mounted 中加入獲取 MongoDB 類別選項的程式碼
        this.getCategories()
        this.intervalId = setInterval(this.getCategories, 1000)

        // 開始定時檢查 if_detect 狀態
        this.startCheckingIfDetect();

        // 在 mounted 方法中初始化資料分類
        // this.filterDetailsByCategory()
    },
    beforeUnmount() {
        window.removeEventListener('resize', this.resizeHandler)
        //API
        clearInterval(this.intervalId)
    },
    methods: {
        show(index) {
            ;(this.showIndex = index), (this.showModal = true)
        },
        resizeHandler() {
            if (this.chart) {
                this.chart.resize()
            }
        },
        
        // 上傳圖片
        uploadFiles() {
            // 獲取上傳的文件
            const fileInput = this.$refs.fileInput;
            const files = fileInput.files;

            // 檢查是否選擇了文件
            if (files.length === 0) {
                alert('請選擇要上傳的文件');
                return;
            }

            // 使用FormData來構建HTTP POST請求
            const formData = new FormData();

            // 將每個選中的文件添加到FormData中
            for (let i = 0; i < files.length; i++) {
                formData.append('image', files[i]);
            }

            // 當上傳過程開始時，將 loading 設置為 true
            this.loading = true;
            this.ifDetectStatus = 1;

            // 執行上傳操作
            this.axios
                .post('/tsmcserver', formData, {
                    headers: {
                        'Content-Type': 'multipart/form-data', // 設定標頭
                    },
                })
                .then((response) => {
                    if (response.data.status === 'success') {
                        // 上傳成功，執行相應操作
                        alert('上傳成功');
                        // 清空選中的文件
                        fileInput.value = '';
                        // 或取時間紀錄
                        this.GetTimeRecord();
                        // 重新獲取數據或執行其他操作
                        this.GetToDo();
                        //更改if_detect狀態
                        this.toggleIfDetect();
                        // 開始定時檢查 if_detect 狀態
                        this.startCheckingIfDetect();
                    } else {
                        // 上傳失敗，執行相應操作
                        alert('上傳失敗');
                        this.loading = false; // 上傳失敗時，重置 loading 為 false
                        this.ifDetectStatus = 0; // 辨識失敗時，重置為未辨識
                    }
                })
                .catch((error) => {
                    // 上傳過程中出現錯誤
                    console.error('上傳過程中出現錯誤：', error);
                    this.loading = false; // 出現錯誤時，重置 loading 為 false
                    this.ifDetectStatus = 0; // 辨識失敗時，重置為未辨識
                });
        },

        // 切換 if_detect 狀態
        toggleIfDetect() {
            // 向後端發送POST請求來切換if_detect狀態
            this.axios.post('/tsmcserver/if_detect').then((res) => {
            if (res.data.status === 'success') {
            // 更新ifDetectStatus以反映新的狀態
                this.ifDetectStatus = res.data.new_number;

                // // 如果 if_detect 變成 0，則重置 loading 為 false
                // if (res.data.new_number === 0) {
                //     this.loading = false;
                // }
            } else {
                console.error('if_detect切換失敗');
            }
            });
        },

        // 開始定時檢查 if_detect 狀態
        startCheckingIfDetect() {
            // 設定每秒執行一次 checkIfDetect 方法
            this.ifDetectInterval = setInterval(this.checkIfDetect, 1000);
        },
        // 停止定時檢查 if_detect 狀態
        stopCheckingIfDetect() {
            clearInterval(this.ifDetectInterval);
        },
        // 向後端發送請求來獲取 if_detect 狀態
        checkIfDetect() {
            this.axios.get('/tsmcserver/if_detect').then((res) => {
                console.log(res.data);
                this.loading = res.data;
                if (res.data === 0) {
                    this.stopCheckingIfDetect();
                }
                // if (res.data.status === 'success') {
                //     this.ifDetectStatus = res.data.new_number;
                //     // 如果 if_detect 變成 0，則停止定時檢查
                //     if (res.data.new_number === 0) {
                //         this.stopCheckingIfDetect();
                //         this.loading = false;
                //     }
                // } else {
                //     console.error('if_detect 檢查失敗');
                // }
            });
        },
        //匯出excel檔案
        exportExcel() {

            try {
                const now = new Date();
                const year = now.getFullYear(); // 取得年份
                const month = (now.getMonth() + 1).toString().padStart(2, '0'); // 取得月份，並補零
                const day = now.getDate().toString().padStart(2, '0'); // 取得日期，並補零

                const formattedDate = `${year}${month}${day}`; // 格式化日期為 "年-月-日"
                // console.log(this.details)
                //整理資料以符合Excel格式
                const data = [[`${formattedDate} — 台科大JDP Project —紅外線熱影像辨識報告`],
                            ['檔名', '類別', '結果', '最大溫度', '平均溫度', '最小溫度']];
                for (const item of this.details) {
                    const parts = item.original_image.split("\\"); // 使用斜杠字符分割 URL
                    const filename = parts[parts.length - 1]; // 提取最後一個部分，即文件名
                data.push([filename, item.category, item.result, item.max, item.avg, item.min]);
                }                

                // 創建工作簿和工作表
                const ws = XLSX.utils.aoa_to_sheet(data);
                const wb = XLSX.utils.book_new();
                XLSX.utils.book_append_sheet(wb, ws, '資料表');

                // 步驟3: 生成Excel文件\
                const filename = `${formattedDate}_紅外線熱影像辨識報告.xlsx`; // 生成檔案名稱
                XLSX.writeFile(wb, filename);
            } catch (error) {
                console.error('匯出至Excel失敗：', error);
            }
        },
    
        GetToDo() {
            this.axios.get('/tsmcserver').then((res) => {
                this.details = res.data
                // console.log(this.details)
            })
        },

        //讀取時間紀錄
        GetTimeRecord() {
            this.axios.get('/tsmcserver/time_record').then((res) => {
                this.uploadTime = res.data
            })
        },

        //更新圓餅圖
        updatePieChart() {
            // 更新 chartData 變數的值，這裡只是一個示例，你可以根據你的數據結構進行更改
            this.chartData = [
                { value: this.details.filter((item) => item.result === '正常' && item.category === this.selectedOption).length, name: '正常' },
                { value: this.details.filter((item) => item.result === '注意' && item.category === this.selectedOption).length, name: '注意' },
                { value: this.details.filter((item) => item.result === '異常' && item.category === this.selectedOption).length, name: '異常' },
                { value: this.details.filter((item) => item.result === '危險' && item.category === this.selectedOption).length, name: '危險' }
            ];  
            let that = this
            this.chart.setOption({
                //更新圓餅圖的標題
                title: {
                    text: this.selectedOption
                },
                //更新圓餅圖的數據
                series: [
                    {data: this.chartData}
                ],
                legend: {
                    bottom: '0%',
                    left: 'center',
                    textStyle: {
                        fontSize: 25 // 使用圖例字體大小
                    },
                    itemGap: 20, // 使用圖例標籤間距
                    formatter: function (name) {
                        // 在圖例中顯示資料數量
                        //這裡不能用this.chartData，因為this會是指向當前的函數，而不是上面的data，所以在上面要用that告訴他是指向上面的data
                        var dataItem = that.chartData.find(function (item) {    
                            return item.name === name
                        })
                        return name + ':' + dataItem.value
                    }
                },
            });            
        },

        // 獲取 MongoDB 中的類別選項
        getCategories() {
            this.axios.get('/tsmcserver/categories').then((res) => {
                this.categories = res.data
            })
        },

        // addNewOption() {
        //     const newOptionValue = prompt('請輸入新選項的值：')
        //     if (newOptionValue) {
        //         this.options.push(newOptionValue)
        //     }
        // }
    }
}
</script>

<style scoped>
.container1 {
    display: grid;
    grid-template-rows: 60px 1fr 10px;
}

/* 選項條============================================================= */

.optionsbar {
    display: grid;
    grid-template-columns: 1fr 2.8fr 1.8fr 1fr 0.8fr 1.2fr;
    /* border: 2px solid black; */
}

/* .item {
    border: 1px solid black;
} */

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

/* 內容============================================================= */
.content {
    display: grid;
    grid-template-columns: 0.7fr 5fr 5fr 0.7fr;
    /* border: 2px solid black; */
}

#last-page {
    grid-column: 0;
    display: flex;
    justify-content: flex-start;
    display: grid;
    grid-template-rows: 10% 1fr 10%;
}

#last-page-button {
    grid-row: 2;
}

#next-page {
    grid-column: 4;
    display: flex;
    justify-content: flex-end;
    display: grid;
    grid-template-rows: 10% 1fr 10%;
}

#next-page-button {
    grid-row: 2;
}

#pie-chart {
    display: flex;
    justify-content: center;
    align-items: center;
    flex-direction: column;
}

#thumbnail {
    display: flex;
    justify-content: space-around;
    align-items: center;
    flex-direction: column;
    width: 43.6vw;
}

.status-text {
    writing-mode: vertical-rl;
    text-orientation: upright;
    white-space: nowrap;
    font-size: 2.5vw;
    font-weight: bold;
    margin-right: 2px;
    margin-left: 10px;
}

/* #thumbnail img {
    height: 70%;
    margin-left: 10px;
    margin-right: 10px;
} */

.picture {
    display: flex;
    align-items: center;
    width: 40vw;
    overflow-x: auto;
}

#normal {
    display: flex;
    align-items: center;
    margin: 0px;
    height: 23%;
    width: 100%;
}

#nor-pic {
    /* width: 100%; */
    height: 100%;
    background-color: rgb(226, 245, 215);
    border-left-style: solid;
    border-left-color: rgb(124, 208, 72);
    border-left-width: 8px;
}

#notice {
    display: flex;
    align-items: center;
    margin: 0px;
    height: 23%;
    width: 100%;
}

#not-pic {
    width: 100%;
    height: 100%;
    background-color: rgb(255, 243, 205);
    border-left-style: solid;
    border-left-color: rgb(255, 200, 25);
    border-left-width: 8px;
}

#abnormal {
    display: flex;
    align-items: center;
    margin: 0px;
    height: 23%;
    width: 100%;
}

#abn-pic {
    width: 100%;
    height: 100%;
    background-color: rgb(248, 215, 178);
    border-left-style: solid;
    border-left-color: rgb(191, 108, 17);
    border-left-width: 8px;
}

#danger {
    display: flex;
    align-items: center;
    margin: 0px;
    height: 23%;
    width: 100%;
}

#dan-pic {
    width: 100%;
    height: 100%;
    background-color: rgb(245, 215, 215);
    border-left-style: solid;
    border-left-color: rgb(181, 59, 59);
    border-left-width: 8px;
}
</style>
