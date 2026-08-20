import pytest

chromadb = pytest.importorskip("chromadb")
from chromadb.utils import embedding_functions
import json
import os

# ==============================
# 配置区（根据你的实际情况修改）
# ==============================
DB_PATH = "./fin_sight_db"          # 向量库存储位置（会自动创建文件夹）
COLLECTION_NAME = "fish_disease_kb" # 集合名称
MODEL_NAME = "all-MiniLM-L6-v2"     # 轻量嵌入模型，首次运行会自动下载约80MB
SAMPLE_DATA_FILE = "knowledge_chunks_sample.jsonl"  # Member 2 提供的样本数据文件名

# ==============================
# 初始化 ChromaDB（本地持久化）
# ==============================
print("🔄 正在初始化 ChromaDB...")
client = chromadb.PersistentClient(path=DB_PATH)

# 使用 SentenceTransformer 作为嵌入函数
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
collection = client.get_or_create_collection(
    name=COLLECTION_NAME,
    embedding_function=ef
)
print(f"✅ 集合 '{COLLECTION_NAME}' 已就绪")

# ==============================
# 加载并入库样本数据
# ==============================
if not os.path.exists(SAMPLE_DATA_FILE):
    print(f"⚠️ 警告：找不到数据文件 '{SAMPLE_DATA_FILE}'")
    print("👉 请确认 Member 2 是否已提供该文件，或手动创建一个测试用 JSONL 文件")
    print("📌 示例格式（每行一个JSON对象）：")
    print('{"text": "White spot disease causes small white cysts on fins and body.", "condition_id": "ICH_001", "evidence_type": "symptom", "source_url": "https://example.com/ich"}')
    exit()

docs, metadatas, ids = [], [], []
with open(SAMPLE_DATA_FILE, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        try:
            chunk = json.loads(line.strip())
            docs.append(chunk["text"])
            metadatas.append({
                "condition_id": chunk.get("condition_id", ""),
                "evidence_type": chunk.get("evidence_type", ""),
                "source_url": chunk.get("source_url", "")
            })
            ids.append(f"chunk_{i}")
        except Exception as e:
            print(f"❌ 第 {i+1} 行解析失败: {e}")

if docs:
    print(f"📥 正在将 {len(docs)} 条知识片段入库...")
    collection.add(documents=docs, metadatas=metadatas, ids=ids)
    print("✅ 数据入库完成")
else:
    print("⚠️ 未加载到任何有效数据")

# ==============================
# 测试检索
# ==============================
test_query = "goldfish with white spots and clamped fins"
print(f"\n🔍 测试查询: '{test_query}'")
results = collection.query(
    query_texts=[test_query],
    n_results=3,
    include=["documents", "metadatas"]
)

print("\n📊 检索结果：")
for idx, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
    print(f"\n--- 结果 {idx+1} ---")
    print(f"📄 内容: {doc[:150]}{'...' if len(doc) > 150 else ''}")
    print(f"🏷️ 类型: {meta.get('evidence_type', 'N/A')} | 疾病ID: {meta.get('condition_id', 'N/A')}")
    print(f"🔗 来源: {meta.get('source_url', 'N/A')}")
