import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from embedding import get_sentence_embedding
from utils import get_shared_state  # 确保模型已加载


async def query_embedding(query):
    """执行数据库日志的相似性搜索。"""
    model_state = get_shared_state()  # 确保在调用时获取模型状态

    try:
        import mysql.connector
        db = mysql.connector.connect(
            host="localhost",
            user="root",
            password="liweiran",
            database="logdb"
        )
        cursor = db.cursor()

        # 从数据库获取嵌入和工作日志
        cursor.execute("SELECT 工作日志, 向量 FROM logs2")
        rows = cursor.fetchall()

        # 获取查询的嵌入
        query_emb = await get_sentence_embedding(query, model_state['embedding_model'])

        # 用于存储相似性结果的列表
        results = []

        for row in rows:
            work_log = row[0]
            vector_data = row[1]

            if vector_data is not None:  # 检查向量是否为 None
                stored_emb = np.frombuffer(vector_data, dtype=np.float32).reshape(1, -1)

                # 计算余弦相似度
                similarity = cosine_similarity(query_emb, stored_emb)[0][0]
                results.append((work_log, similarity))

        # 按相似度降序排序结果，并取前10个
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)[:10]

        return sorted_results

    except mysql.connector.Error as err:
        print(f"数据库连接失败: {err}")
        return []

    finally:
        cursor.close()
        db.close()
