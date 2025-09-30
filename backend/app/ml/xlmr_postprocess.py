import re
import pandas as pd

def safe_name(s: str) -> str:
    return re.sub(r"[^\w]+", "_", s).strip("_")

def postprocess(preds, probs, df, classes, id2sent, tau=0.5):
    present_prob = 1.0 - probs[:, :, 0]
    present_bin = (present_prob >= tau).astype(int)

    out_cols = {}
    for i, name in enumerate(classes):
        base = safe_name(name)
        out_cols[f"{base}__present_prob"] = present_prob[:, i]
        out_cols[f"{base}__present_bin"]  = present_bin[:, i]
        out_cols[f"{base}__state_id"]     = preds[:, i]
        out_cols[f"{base}__state_str"]    = [id2sent[str(int(v))] if isinstance(id2sent, dict) else id2sent[int(v)] for v in preds[:, i]]

    pred_df = pd.DataFrame(out_cols)
    res_df = pd.concat([df.reset_index(drop=True), pred_df], axis=1)

    # компактный вид
    if isinstance(id2sent, dict):
        id2sent_map = {int(k): v for k, v in id2sent.items()}
        id2sent_list = [id2sent_map[i] for i in range(4)]
    else:
        id2sent_list = list(id2sent)

    pred_pairs_list = []
    for r in range(len(df)):
        pairs = []
        for t_idx, name in enumerate(classes):
            if present_bin[r, t_idx] == 1:
                s_id = int(preds[r, t_idx])
                s_str = id2sent_list[s_id]
                pairs.append(f"{name}: {s_str}")
        pred_pairs_list.append(" | ".join(pairs) if pairs else "—")

    res_df["pred_pairs"] = pred_pairs_list
    
    # финальный компактный DataFrame
    new_result = res_df[["review_id", "clause_id", "clause", "pred_pairs"]]

    return new_result
