<template lang="">
    <div id="modal0">
        <div class="modal-content0">
            <div id="category-title">
                <p id="category-text">辨識類別：{{ describe?.category}}</p>
                <div id="closeButton"><button type="button" class="btn-close" aria-label="Close" @click="closeModal"></button></div>
            </div>
            <div id="details" :style="{ backgroundColor: bcolor }">
                <table class="temperature-table0">
                    <tr>
                        <th id="top-table" :style="{ backgroundColor: tbcolor }">MAX</th>
                        <th id="top-table" :style="{ backgroundColor: tbcolor }">AVG</th>
                        <th id="top-table" :style="{ backgroundColor: tbcolor }">MIN</th>
                    </tr>
                    <tr>
                        <th id="max-temperature">{{describe?.max}}℃</th>
                        <th id="avg-temperature">{{describe?.avg}}℃</th>
                        <th id="min-temperature">{{describe?.min}}℃</th>
                    </tr>
                </table>
                <img :src="src" id="detail-picture"  :style="{ borderColor: tbcolor }">
            </div>
            <div id="result-field">
                <p id="result-text">檢測結果：{{describe?.result}}</p>
            </div>
        </div> 
    </div>
</template>
<script>
export default {
    props:{    
        src: {
            type: String,
            required: ''
        },    
        describe: {
            type: Object,
            default: () => ({})
        },
        bcolor: {
            type: String,
            default: ''
        },
        tbcolor: {
            type: String,
            default: ''
        }
    },
    emit: [
        "close"
    ],
    methods: {
        closeModal() {
            this.$emit("close");
        }
    },
}
</script>
<style>
/* .hidden {
    display: none !important;
} */

#modal0 {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.35);
    display: flex;
    justify-content: center;
    align-items: center;
}

.modal-content0 {
    padding: 0;
    height: 70dvb;
    width: 85dvb;
    background-color: white;
    border: 5px solid rgb(46, 46, 41);
    border-radius: 10px;
    display: grid;
    grid-template-rows: 0.12fr 1fr 0.12fr;
}

#category-title {
    margin: 0;
    display: grid;
    grid-template-columns: 50px 1fr 35px;
    /* border: 1px solid black; */

}

#category-text {
    margin: 0;
    grid-column: 2;
    font-size: 2vw;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
}

#closeButton {
    grid-column: 3;
    display: flex;
    align-items: center;
    justify-content: start;
}

#details {
    margin: 0;
    /* background-color: rgb(226, 245, 215); */
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
}

.temperature-table0 {
    margin-bottom: 3%;
    font-size: 1.5vw;
    border-collapse: collapse;
}

.temperature-table0 th {
    padding: 0.1vw 1.5vw;
    border: 3px solid rgb(66, 66, 58);
    height: 100%;
    background-color: white;
    text-align: center;
}

/* #top-table {
    background-color: rgb(124, 208, 72);
} */

#detail-picture {
    height: 33vh;
    width: auto;
    margin-top: 5%;
    border: 3px solid;
    /* border-color: rgb(124, 208, 72); */
}

#result-field {
    margin: 0;
    display: flex;
    justify-content: center;
    /* border: 1px solid black; */
}

#result-text {
    margin: 0;
    font-size: 2vw;
    font-weight: bold;
    display: flex;
    align-items: center;
    justify-content: center;
}
</style>