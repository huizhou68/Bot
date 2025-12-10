import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import pandas as pd

# 1. 读取环境变量中的 DATABASE_URL（本地或 Render 用的都行）
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL not found in environment!")

# 2. 连接数据库
engine = create_engine(DATABASE_URL)

# 3. 读取 users 表
users_query = """
SELECT *
FROM users
ORDER BY id;
"""
df_users = pd.read_sql(users_query, engine)

# 4. 读取 chat_history 表
history_query = """
SELECT id, passcode, user_message, bot_response, timestamp
FROM chat_history
ORDER BY timestamp;
"""
df_history = pd.read_sql(history_query, engine)

# 5. 写入同一个 Excel 文件，不同 sheet
output_file = "bot_data.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df_users.to_excel(writer, sheet_name="users", index=False)
    df_history.to_excel(writer, sheet_name="chat_history", index=False)

print(f"✅ Export complete! File saved as: {output_file}")