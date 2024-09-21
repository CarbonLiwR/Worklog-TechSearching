from embedding import load_embedding_models

# 全局变量，存储已加载的模型
_emb_model = None

async def initialize_model():
    """初始化并加载模型"""
    global _emb_model
    if _emb_model is None:
        _emb_model = await load_embedding_models()

def get_shared_state():
    """返回共享状态，包括BERT嵌入模型和分词器"""
    if _emb_model is None:
        raise ValueError("模型尚未加载。请确保在应用程序启动时调用initialize_model()。")
    model_state = {
        'embedding_model': _emb_model
    }
    return model_state
