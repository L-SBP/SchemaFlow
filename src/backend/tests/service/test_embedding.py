"""
Embedding 服务测试脚本。

运行方式：
    cd src/backend
    python -m tests.service.test_embedding
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from openai import OpenAI
from app.config import settings

# 从配置文件获取 API key
client = OpenAI(
    api_key=settings.embedding.api_key,
    base_url=settings.embedding.base_url
)

completion = client.embeddings.create(
    model=settings.embedding.model,
    input='衣服的质量杠杠的，很漂亮，不枉我等了这么久啊，喜欢，以后还来这里买',
    dimensions=settings.embedding.dimensions,
    encoding_format="float"
)

print(completion.model_dump_json())