import mysql.connector
import time

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'techsearch',
    'database': 'logdb',
    'charset': 'utf8mb4',
    'autocommit': True
}

def connect_to_db():
    """连接到MySQL数据库"""
    try:
        db = mysql.connector.connect(**DB_CONFIG)
        cursor = db.cursor()
        print("成功连接到数据库")
        return db, cursor
    except mysql.connector.Error as err:
        print(f"连接数据库失败: {err}")
        exit(1)

def split_text_by_double_newlines(text):
    """按双换行符分割文本"""
    parts = []
    current_part = []

    for line in text.splitlines():
        if line.strip() == '' and current_part:
            parts.append('\n'.join(current_part))
            current_part = []
        else:
            current_part.append(line)

    if current_part:
        parts.append('\n'.join(current_part))

    return parts

def insert_log_parts(text):
    """将分割后的日志部分插入数据库"""
    db, cursor = connect_to_db()
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
                time.sleep(5)  # 等待5秒后重试

    cursor.close()
    db.close()

# 主框架调用示例
def divide(text):
    try:
        insert_log_parts(text)
        return True
    except Exception as e:
        print(f"处理时发生错误: {str(e)}")
        return False

if __name__ == '__main__':
    text = """姓名：苏武
时间：2024-08-19
解决问题：对公司内外网环境进行网络安全审计，发现并修复潜在安全漏洞。
解决方法：使用自动化扫描工具对内外网服务器、网络设备和应用系统进行漏洞扫描，共发现中高危漏洞 15 个。逐一复核并确认漏洞有效性，编写详细漏洞报告，包括漏洞描述、影响范围、修复建议和优先级排序。紧急协调相关部门对高危漏洞进行修复，并跟踪修复进度，确保所有漏洞在限定时间内得到妥善处理。
解决效果：有效发现并修复了潜在安全漏洞，提升了公司内外网环境的安全性，为公司网络稳定运行提供了有力保障。

姓名：苏武
时间：2024-08-19
解决问题：根据公司最新安全要求和行业标准更新网络安全策略。
解决方法：审查现有的网络安全策略文档，识别出与最新安全要求不符的条款。制定新的安全策略，包括访问控制、密码策略、数据加密、安全审计等方面的规定。组织一场内部培训会，向全体员工介绍新安全策略的重要性和具体内容，确保大家能够遵守执行。
解决效果：更新后的网络安全策略更符合公司最新要求和行业标准，员工对新策略有了清晰认识，增强了网络安全防范意识。

姓名：苏武
时间：2024-08-19
解决问题：为即将到来的网络安全应急演练做准备，包括制定演练计划、搭建模拟环境和培训应急响应团队。
解决方法：与团队成员讨论并确定演练的主题和目标，制定详细的演练计划。搭建模拟网络环境，模拟常见的网络攻击场景，如 DDoS 攻击、SQL 注入、勒索软件等。组织应急响应团队进行一次预演，对演练流程进行优化和调整，确保演练能够顺利进行。
解决效果：完善了应急演练的前期准备工作，提高了应急响应团队的应对能力和协作水平，为正式演练的顺利开展奠定了基础。

姓名：苏武
时间：2024-08-19
解决问题：研究最新网络安全威胁趋势和防御技术并组织内部技术分享。
解决方法：研究最新的网络安全威胁趋势和防御技术，特别是关于零日漏洞的防范和应急响应策略。下午组织一场内部技术分享会，向同事们介绍自己的研究成果，并鼓励大家积极参与网络安全技术的交流和探讨。
解决效果：促进了团队成员对最新网络安全技术的了解和掌握，增强了团队整体的技术实力和应对能力。

姓名：苏武
时间：2024-08-19
解决问题：漏洞扫描中发现某台服务器防火墙配置不当，部分安全规则未生效。
解决方法：立即联系该服务器的管理员，指导其调整防火墙配置，并重新进行扫描验证，确认所有安全规则均已正确生效。
解决效果：及时解决了服务器防火墙配置问题，保障了服务器的安全运行，避免了潜在的安全风险。
    """
    divide(text)
    print("处理完成")