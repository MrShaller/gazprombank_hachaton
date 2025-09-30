import os, json, re
import torch
import numpy as np
import pandas as pd
from transformers import AutoTokenizer, AutoModel

# ====== 1. Архитектура головы ======
class XLMRTopicsSent(torch.nn.Module):
    def __init__(self, base_model_name: str, num_topics=13, num_states=4, dropout=0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model_name)
        hidden = self.encoder.config.hidden_size
        self.dropout = torch.nn.Dropout(dropout)
        self.classifier = torch.nn.Linear(hidden, num_topics * num_states)
        self.num_topics = num_topics
        self.num_states = num_states

    def forward(self, input_ids, attention_mask):
        enc_out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls = enc_out.last_hidden_state[:, 0]
        logits = self.classifier(self.dropout(cls))                # [B, 13*4]
        logits = logits.view(-1, self.num_topics, self.num_states) # [B, 13, 4]
        return logits

# ====== 2. Загрузка модели ======
def load_pretrained(path, device="cpu"):
    tok = AutoTokenizer.from_pretrained(path, use_fast=True)
    with open(os.path.join(path, "config.json"), "r", encoding="utf-8") as f:
        cfg = json.load(f)
    mdl = XLMRTopicsSent(
        cfg.get("model_name", "FacebookAI/xlm-roberta-large"),
        num_topics=cfg.get("num_topics", 13),
        num_states=cfg.get("num_states", 4),
        dropout=cfg.get("dropout", 0.1),
    )
    sd = torch.load(os.path.join(path, "pytorch_model.bin"), map_location=device)
    mdl.load_state_dict(sd, strict=True)
    mdl.to(device).eval()
    return tok, mdl, cfg

# ====== 3. Инференс ======
@torch.inference_mode()
def predict(texts, tok, mdl, max_len=128, batch_size=32, device="cpu"):
    mdl.eval()
    preds_all, probs_all = [], []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        enc = tok(batch, truncation=True, padding=True, max_length=max_len, return_tensors="pt")
        input_ids = enc["input_ids"].to(device)
        attention_mask = enc["attention_mask"].to(device)
        logits = mdl(input_ids=input_ids, attention_mask=attention_mask)
        if isinstance(logits, tuple):
            logits = logits[0]
        probs = torch.softmax(logits, dim=-1).cpu().numpy()    # [B,13,4]
        preds = probs.argmax(-1)                               # [B,13]
        preds_all.append(preds)
        probs_all.append(probs)
    return np.vstack(preds_all), np.vstack(probs_all)
