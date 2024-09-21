import pymysql
import numpy as np
from embedding import load_embedding_models, get_sentence_embedding

# 数据库连接参数
config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'techsearch',
    'database': 'logdb',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

async def process_logs():
    # 加载嵌入模型
    emb_model = await load_embedding_models()

    # 创建数据库连接
    connection = pymysql.connect(**config)

    try:
        with connection.cursor() as cursor:
            # 查询所有日志数据，包括向量列
            select_sql = "SELECT id, 工作日志, 向量 FROM logs2"
            cursor.execute(select_sql)
            results = cursor.fetchall()

            # 遍历每条日志，根据条件处理
            for row in results:
                log_id = row['id']
                work_log = row['工作日志']
                vector_blob = row['向量']

                if work_log and not vector_blob:
                    # 如果工作日志不为空且向量为空，生成嵌入
                    embedding = await get_sentence_embedding(work_log, emb_model)
                    vector_blob = embedding.tobytes()  # 将向量转换为二进制格式

                    # 更新数据库中的向量列
                    update_sql = "UPDATE logs2 SET 向量 = %s WHERE id = %s"
                    cursor.execute(update_sql, (vector_blob, log_id))
                    print(f"Updated embedding for ID {log_id}")

                elif not work_log and vector_blob:
                    # 如果工作日志为空且向量不为空，输出警告后删除该行
                    print(f"警告: ID 为 {log_id} 的行工作日志数据缺失，请重新填写")
                    delete_sql = "DELETE FROM logs2 WHERE id = %s"
                    cursor.execute(delete_sql, (log_id,))
                    print(f"Deleted row with ID {log_id} due to missing 工作日志")

                elif not work_log and not vector_blob:
                    # 如果工作日志和向量都为空，删除该行
                    delete_sql = "DELETE FROM logs2 WHERE id = %s"
                    cursor.execute(delete_sql, (log_id,))
                    print(f"Deleted row with ID {log_id} due to missing both 工作日志 and 向量")

            # 提交事务
            connection.commit()

    finally:
        # 关闭数据库连接
        connection.close()

    print("所有日志的处理已完成。")
