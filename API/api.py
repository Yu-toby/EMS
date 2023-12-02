from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os  # 引入 os 模塊
import datetime # 引入 datetime 模塊
from PIL import Image, ImageDraw
import io
import base64  # 引入 base64 模塊

app = Flask(__name__)
CORS(app)
app.config["SECRET_KEY"] = "<secret_key>"

# 連接到 MongoDB 數據庫
client = MongoClient('mongodb://localhost:27017/')
# db = client['TSMC_test']
# collection = db['detect_result']
# collection_unidentified = db['Unidentified']
db = client['tsmcdatabase']
collection = db['tsmccollection']

collection1 = db['if_detect']
collection_TimeRecord = db['time_record']

# 設定圖片上傳的路徑
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 確保上傳目錄存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 設定當前日期+順序的資料夾
file_count = 0

@app.route('/tsmcserver', methods=['GET', 'POST', 'DELETE'])
def todo():
    global current_folder
    global file_count

    if request.method == 'GET':

        # 從 MongoDB 讀取所有數據
        tsmcservers  = list(collection.find())

        for tsmcserver  in tsmcservers:
            # 獲取 X、Y 座標
            x1 = int(tsmcserver.get("coordinate", {}).get("xmin", 0))
            y1 = int(tsmcserver.get("coordinate", {}).get("ymin", 0))
            x2 = int(tsmcserver.get("coordinate", {}).get("xmax", 0))
            y2 = int(tsmcserver.get("coordinate", {}).get("ymax", 0))

            # 獲取圖片路徑
            image_path = tsmcserver.get("image", "")

            # 開啟圖片
            original_image = Image.open(image_path)

            # 創建一個可以繪製形狀的對象
            draw = ImageDraw.Draw(original_image)

            # 繪製方框
            draw.rectangle([x1, y1, x2, y2], outline='red', width=5)

            # 將圖像轉換為RGB模式
            if original_image.mode == 'RGBA':
                original_image = original_image.convert('RGB')

            # 將圖像轉換為Base64字串
            image_buffer = io.BytesIO()
            original_image.save(image_buffer, format='JPEG')
            image_base64 = base64.b64encode(image_buffer.getvalue()).decode()

            tsmcserver["_id"] = str(tsmcserver["_id"])
            tsmcserver["time"] = tsmcserver.get("time", "")
            tsmcserver["category"] = tsmcserver.get("category", "")
            tsmcserver["max"] = round(float(tsmcserver.get("temp", {}).get("max", 0)), 1)
            tsmcserver["avg"] = round(float(tsmcserver.get("temp", {}).get("avg", 0)), 1)
            tsmcserver["min"] = round(float(tsmcserver.get("temp", {}).get("min", 0)), 1)
            tsmcserver["result"] = tsmcserver.get("result", "")
            tsmcserver["image"] = f"data:image/jpeg;base64,{image_base64}"
            tsmcserver["original_image"] = image_path

        return jsonify(tsmcservers)

    elif request.method == 'POST':
        data = request.form.to_dict()
        # 處理圖片上傳
        image = request.files.getlist('image')

        # 處理並保存每個圖片
        if image:
            # 創建以當前日期和順序命名的資料夾名稱
            current_date = datetime.date.today().strftime('%Y%m%d')
            new_filename = f'{current_date}-{str(file_count).zfill(3)}'
            if os.makedirs(new_filename, exist_ok=True):
                file_count += 1
            else:
                current_folder = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
                image_filenames = []
                for image in image:
                    os.makedirs(current_folder, exist_ok=True)
                    file_path = os.path.join(current_folder, image.filename)
                    image.save(file_path)
                    image_filenames.append(file_path)
                

                data['images'] = image_filenames
                file_count += 1

        #更新時間紀錄
        time_record = collection_TimeRecord.find_one()
        if time_record:
            # time_record = time_record.get("time_record", "")
            time_record = datetime.datetime.today().strftime('%Y%m%d-%H%M')
            collection_TimeRecord.update_one({}, {"$set": {"time_record": time_record}})

        # 插入數據到 MongoDB 
        result = collection.insert_one({
            "time": datetime.datetime.today().strftime('%Y%m%d-%H%M'),
            "image": image_filenames,
            "processed": False})
        
        if result.inserted_id:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error"})

    elif request.method == 'DELETE':
        data = request.get_json()
        index = data['index']
        # 刪除數據
        result = collection.delete_one({"_id": ObjectId(index)})
        if result.deleted_count == 1:
            return jsonify({"status": "success"})
        else:
            return jsonify({"status": "error", "message": "數據不存在"})

    return jsonify({"status": "error"})

# 新增一個路由來獲取 MongoDB 中的 "category" 選項
@app.route('/tsmcserver/categories', methods=['GET'])
def get_categories():
    categories = collection.distinct("category")
    return jsonify(categories)

@app.route('/tsmcserver/if_detect', methods=['GET', 'POST'])
def if_detect():
    if request.method == 'GET':
        if_detect_number = collection1.find_one().get("number", 0)
        return jsonify(if_detect_number)
        # if collection1.find_one():
        #     if_detect_number = collection1.find_one().get("number", 0)
        #     print(if_detect_number)
        #     return jsonify(if_detect_number)            
        # else:
        #     print("找不到集合 'if_detect' 或 'number' 字段")
        #     return jsonify("找不到集合 'if_detect' 或 'number' 字段")
        
    elif request.method == 'POST':
        # 檢查 "if_detect" 集合是否存在
        if "if_detect" not in db.list_collection_names():
            # 如果不存在，創建 "if_detect" 集合，並插入一個初始文檔，"number" 設置為 0
            db.create_collection("if_detect")
            db.if_detect.insert_one({"number": 0})

        # 檢索當前 "number" 值
        current_document = db.if_detect.find_one()
        if current_document:
            current_number = current_document.get("number", 0)
            # 切換 "number" 字段的值
            new_number = 1 if current_number == 0 else 1
            # 更新 "number" 字段的值
            db.if_detect.update_one({}, {"$set": {"number": new_number}})

            return jsonify({"status": "success", "new_number": new_number})
        else:
            return jsonify({"status": "error"})
    
#讀取跟寫入時間紀錄
@app.route('/tsmcserver/time_record', methods=['GET', 'POST'])
def time_record():
    if request.method == 'GET':
        time_record = collection_TimeRecord.find_one().get("time_record", "")
        return jsonify(time_record)



if __name__ == '__main__':
    app.run(debug=True, port=8000)