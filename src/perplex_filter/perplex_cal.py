import torch
import yaml


def load_config():
    with open("config/perplex_filter_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_device():
    config = load_config()
    device_config = config["perplex_cal"]["device"]

    if device_config == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        else:
            return torch.device("cpu")

    if device_config == "cuda":
        return torch.device("cuda")

    return torch.device("cpu")


def get_max_length():
    config = load_config()

    return config["perplex_cal"]["max_length"]


def calculate_pseudo_ppl(text,model,tokenizer):
    device = get_device()
    max_length = get_max_length()

    model.to(device)
    model.eval()

    encoded = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )

    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)

    seq_length = input_ids.size(1)

    total_loss = 0.0
    token_count = 0

    with torch.no_grad():
        for index in range(seq_length):
            masked_input_ids = input_ids.clone()
            original_token = input_ids[0, index]
            masked_input_ids[0, index] = tokenizer.mask_token_id
            outputs = model(
                input_ids=masked_input_ids,
                attention_mask=attention_mask,
            )
            logits = outputs.logits
            token_logits = logits[0, index]
            loss = torch.nn.functional.cross_entropy(
                token_logits.unsqueeze(0),
                original_token.unsqueeze(0),
            )
            total_loss += loss.item()
            token_count += 1

    average_loss = total_loss / token_count

    return float(torch.exp(torch.tensor(average_loss)))


def calculate_ppl(text,model,tokenizer):
    device = get_device()
    max_length = get_max_length()

    model.to(device)
    model.eval()

    encoded = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=max_length,
    )

    input_ids = encoded["input_ids"].to(device)
    attention_mask = encoded["attention_mask"].to(device)
    labels = input_ids.clone()

    with torch.no_grad():
        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels,
        )

    loss = outputs.loss

    return float(torch.exp(loss))


def calculate_perplexity(text,model,tokenizer,score_type):
    if score_type == "pseudo_ppl":
        return calculate_pseudo_ppl(
            text,
            model,
            tokenizer,
        )

    if score_type == "ppl":
        return calculate_ppl(
            text,
            model,
            tokenizer,
        )

    raise ValueError(
        f"Unsupported score_type: {score_type}"
    )