import os
import torch
from transformers import BertModel, BertTokenizer, BertConfig
import asyncio

async def load_file_async(path):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, torch.load, path, torch.device('cpu'))

async def load_embedding_models():
    """加载BERT模型和分词器"""
    base_path = os.path.dirname(__file__)  # 获取当前文件的目录
    path = os.path.join(base_path, 'model')

    # 定义文件路径
    model_path = os.path.join(path, 'pytorch_model.bin')
    config_path = os.path.join(path, 'config.json')
    vocab_path = os.path.join(path, 'vocab.txt')

    # 加载配置文件
    config = BertConfig.from_pretrained(config_path)

    # 初始化模型
    model = BertModel(config)

    # 异步加载模型权重
    state_dict = await load_file_async(model_path)
    model.load_state_dict(state_dict)

    # 加载分词器
    tokenizer = BertTokenizer(vocab_file=vocab_path)

    return {"model": model, "tokenizer": tokenizer}

async def get_sentence_embedding(text, emb_model):
    """获取句子的BERT嵌入"""
    inputs = emb_model["tokenizer"](text, return_tensors='pt')
    with torch.no_grad():
        outputs = emb_model["model"](**inputs)
    # 获取 [CLS] token 的向量
    cls_embedding = outputs.last_hidden_state[:, 0, :].numpy()
    return cls_embedding
