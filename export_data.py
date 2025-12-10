import os
import pathlib
from sqlalchemy import create_engine
from dotenv import load_dotenv
import pandas as pd

# 1. 明确 .env 的路径：和这个脚本同一目录
BASE_DIR = pathlib.Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

print(f"🔎 Looking for .env at: {ENV_PATH}")

if not ENV_PATH.exists():
    raise RuntimeError(f"❌ .env file not found at {ENV_PATH}. Please create it first.")

# 2. 从指定路径加载 .env
load_dotenv(dotenv_path=ENV_PATH)

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL not found in .env! Please add a line: DATABASE_URL=postgresql://...")

print("✅ DATABASE_URL loaded (hidden for safety).")

# 3. 连接数据库
engine = create_engine(DATABASE_URL)

# 4. 读取 users 表
users_query = """
SELECT *
FROM users
ORDER BY id;
"""
df_users = pd.read_sql(users_query, engine)

# 5. 读取 chat_history 表
history_query = """
SELECT id, passcode, user_message, bot_response, timestamp
FROM chat_history
ORDER BY timestamp;
"""
df_history = pd.read_sql(history_query, engine)

# 🔧 6. 处理带时区的 datetime 列（Excel 不支持 tz-aware datetime）
for df_name, df in [("users", df_users), ("chat_history", df_history)]:
    for col in df.columns:
        if pd.api.types.is_datetime64tz_dtype(df[col]):
            print(f"⏱ Converting timezone-aware column '{col}' in '{df_name}' to naive datetime...")
            df[col] = df[col].dt.tz_localize(None)   # 去掉时区信息，保留时间值（通常是 UTC）

# 7. 写入同一个 Excel 文件，不同 sheet
output_file = BASE_DIR / "../bot_data.xlsx"

with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
    df_users.to_excel(writer, sheet_name="users", index=False)
    df_history.to_excel(writer, sheet_name="chat_history", index=False)

print(f"✅ Export complete! File saved as: {output_file}")