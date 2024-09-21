from quart import Quart, request, render_template, jsonify
from quart_cors import cors
import requests
import pymysql
import mysql.connector
from dataembedding import process_logs
import aiomysql
import json
import asyncio
from embedding import load_embedding_models, get_sentence_embedding
import time
from search import query_embedding
from formatter import process_and_store_log
from utils import initialize_model
import threading

app = Quart(__name__)
app = cors(app, allow_origin="*")

# 数据库连接参数
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'techsearch',
    'db': 'logdb',
    'charset': 'utf8mb4',
    'autocommit': True
}


@app.before_serving
async def startup():
    """在应用程序启动时加载模型"""
    # 如果有需要初始化的模型，可以在这里调用
    await initialize_model()


@app.route('/')
async def home():
    """渲染主页。"""
    return await render_template('index.html')


@app.route('/search')
async def search_query():
    """使用 query_embedding 函数处理搜索查询。"""
    query = request.args.get('q')
    if not query:
        results = []
    else:
        # 使用 query_embedding 函数执行搜索
        results = await query_embedding(query)

        # 处理结果，将空格替换为换行符，并为关键词添加样式
        formatted_results = []
        for result, similarity in results:
            # 将关键字变成带有淡蓝色样式的HTML标签，并加上换行符
            for keyword in ["时间：", "解决问题：", "解决方法：", "解决效果："]:
                result = result.replace(keyword, f'<br>{keyword}')
            # 替换空格为换行符
            formatted_result = result.replace(" ", "<br>")
            formatted_results.append((formatted_result, similarity))  # 保留相似度用于排序

        # 按相似度排序并提取前3个工作日志内容
        top_logs = [res[0] for res in sorted(formatted_results, key=lambda x: x[1], reverse=True)[:3]]

        print(f"Query: {query}, Results: {top_logs}")  # 调试信息

    return await render_template('results.html', query=query, results=[r[0] for r in formatted_results])


async def run_sync_task(func, *args):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, func, *args)

async def c1onnect_to_db():
    """异步连接到MySQL数据库"""
    try:
        connection = await aiomysql.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            db=DB_CONFIG['db'],
            charset=DB_CONFIG['charset'],
            autocommit=DB_CONFIG['autocommit']
        )
        cursor = await connection.cursor(aiomysql.DictCursor)
        print("成功连接到数据库")
        return connection, cursor
    except aiomysql.MySQLError as err:
        print(f"连接数据库失败: {err}")
        return None, None

@app.route('/showlogs')
async def showlogs():
    """获取数据库中的日志数据并返回。"""
    db, cursor = await c1onnect_to_db()  # 使用异步数据库连接函数
    if not db or not cursor:
        return jsonify({"error": "无法连接到数据库"}), 500

    try:
        query = "SELECT * FROM logs2"
        await cursor.execute(query)
        results = await cursor.fetchall()

        logs = [dict(result) for result in results]
        return await render_template('showlogs.html', logs=logs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()  # 关闭游标
        db.close()      # 关闭数据库连接

@app.route('/addlogs')
async def addlogs():
    """渲染添加日志页面。"""
    name = "张三"
    return await render_template('addlogs.html',username=name)


async def connect_to_db():
    """异步连接到MySQL数据库"""
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
        print("成功连接到数据库")
        return db, cursor
    except mysql.connector.Error as err:
        print(f"连接数据库失败: {err}")
        return None, None


def split_text_by_double_newlines(text):
    """按双换行符分割文本"""
    parts = []
    current_part = []

    for line in text.splitlines():
        if line.strip() == '' and current_part:
            # 检查 current_part 是否只包含空格
            if any(line.strip() for line in current_part):
                parts.append('\n'.join(current_part))
            current_part = []
        else:
            current_part.append(line)

    # 最后一部分的处理
    if current_part and any(line.strip() for line in current_part):
            parts.append('\n'.join(current_part))

    return parts


async def insert_log_parts(text):
    """将分割后的日志部分插入数据库"""
    db, cursor = await connect_to_db()
    if not db or not cursor:
        return False  # 连接失败

    parts = split_text_by_double_newlines(text)

    for i, part in enumerate(parts, start=1):
        retries = 0
        max_retries = 2

        while retries <= max_retries:
            try:
                # 插入数据到MySQL
                query = "INSERT INTO logs2 (工作日志) VALUES (%s)"
                cursor.execute(query, (part,))
                db.commit()
                print(f"部分{i}日志数据已成功插入到数据库")
                break  # 跳出重试循环
            except mysql.connector.Error as err:
                retries += 1
                if retries > max_retries:
                    print(f"插入部分{i}数据失败: {err}")
                    break  # 跳过该部分，继续下一部分
                print(f"重试插入部分{i}数据...")
                await asyncio.sleep(5)  # 等待5秒后重试

    cursor.close()
    db.close()
    return True  # 插入成功


async def divide(text):
    """分割并插入日志文本"""
    success = await insert_log_parts(text)
    return success


async def process_and_divide_log(log_text):
    # 调用 process_and_store_log 并转换为字符串类型
    processed_result = process_and_store_log(log_text)

    # 调用 divide 并等待其完成
    success = await divide(processed_result)
    return success


async def dbembeddingrun():
    await process_logs()


@app.route('/submit_log', methods=['POST'])
async def submit_log():
    """处理日志提交请求"""
    data = await request.get_json()
    log_text = data.get('logData')

    if not log_text:
        return jsonify({"error": "日志数据是必需的"}), 400

    try:
        # 使用 run_sync_task 运行封装后的同步函数
        success = await process_and_divide_log(log_text)

        await dbembeddingrun()

        if success:
            return jsonify({"success": "日志已提交并处理成功"}), 200
        else:
            return jsonify({"error": "日志处理失败"}), 500

    except Exception as e:
        return jsonify({"error": f"处理请求时发生错误: {str(e)}"}), 500


def check(text: str):
    url = 'https://api.coze.cn/open_api/v2/chat'
    headers = {
        'Authorization': 'Bearer pat_J0kTR3d58Z8bWcFpUisvOMvrOToUDg6aVIk76yoraRCKapOt8jlHa6ghBbXO5a0h',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': 'api.coze.cn',
        'Connection': 'keep-alive'
    }

    data = {
        "conversation_id": "1234",
        "bot_id": "7400423003794227254",
        "user": "29032201862555",
        "query": text,
        "stream": False
    }

    for _ in range(3):  # Retry up to 3 times
        try:
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response.raise_for_status()  # Raise an HTTPError for bad responses (4xx and 5xx)
            response_data = response.json()
            messages = response_data.get("messages", [])
            for message in messages:
                if message.get("role") == "assistant" and message.get("type") == "answer":
                    return message.get("content")
            return None
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            time.sleep(5)  # Wait for 5 seconds before retrying

    raise ConnectionError("API请求失败: 超过最大重试次数")


@app.route('/check_text', methods=['POST'])
async def check_text():
    try:
        # 从请求中获取 JSON 数据
        data = await request.get_json()
        text = data.get('text')

        # 调用同步的 check 函数并获取返回结果
        checked_text = await asyncio.to_thread(check, text)

        # 将检查后的文本返回给前端
        return jsonify({'checkedText': checked_text})

    except Exception as e:
        # 捕获异常并返回错误信息
        return jsonify({'error': str(e)}), 500


@app.route('/api/ask', methods=['POST'])
async def api_ask():
    """处理API请求并返回响应。"""
    data = await request.get_json()  # 使用 await 来获取请求数据
    text = data.get('question')  # 从请求中获取输入内容
    if not text:
        return jsonify({"error": "No query provided"}), 400

    # 在发送给API的文本之前附加前三个工作日志内容
    top_logs = data.get('top_logs', [])
    background_text = "请以" + "、".join(
        [f"文本{i + 1}：" + log for i, log in enumerate(top_logs)]) + "为背景，回答“" + text + "”"

    url = 'https://api.coze.cn/open_api/v2/chat'
    headers = {
        'Authorization': 'Bearer pat_J0kTR3d58Z8bWcFpUisvOMvrOToUDg6aVIk76yoraRCKapOt8jlHa6ghBbXO5a0h',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Host': 'api.coze.cn',
        'Connection': 'keep-alive'
    }

    payload = {
        "conversation_id": "123",
        "bot_id": "7398757473089716261",
        "user": "29032201862555",
        "query": background_text,  # 使用格式化后的文本
        "stream": False
    }

    for _ in range(3):  # 重试最多3次
        try:
            response = await asyncio.to_thread(requests.post, url, headers=headers, data=json.dumps(payload))
            response.raise_for_status()  # 为错误响应抛出HTTPError（4xx和5xx）
            response_data = response.json()
            messages = response_data.get("messages", [])
            for message in messages:
                if message.get("role") == "assistant" and message.get("type") == "answer":
                    return jsonify({"answer": message.get("content")})  # 返回统一的格式
            return jsonify({"error": "No valid response received"}), 500
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {e}")
            await asyncio.sleep(5)  # 在重试前等待5秒

    return jsonify({"error": "API请求失败: 超过最大重试次数"}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
