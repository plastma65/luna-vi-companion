"""Fine-tune Luna bằng QLoRA trên dataset persona (Giai đoạn 1b).

Chạy:
    python scripts/train_luna_sft.py

Lần đầu sẽ tải model nền Qwen về (~vài GB, cần mạng). Adapter được lưu vào
checkpoints/luna_lora/ (chỉ vài chục MB), KHÔNG phải cả model.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

from luna.config import SFT, PROCESSED_DIR, ADAPTER_DIR

DATA_FILE = PROCESSED_DIR / "luna_persona.jsonl"

# 1) Nạp model nền ở 4-bit (QLoRA)
bnb = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
print("Đang tải model nền:", SFT.base_model, "(lần đầu hơi lâu)...")
tokenizer = AutoTokenizer.from_pretrained(SFT.base_model)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    SFT.base_model,
    quantization_config=bnb,
    device_map="auto",
    torch_dtype=torch.bfloat16,
)
model = prepare_model_for_kbit_training(model)

# 2) Gắn adapter LoRA (chỉ train vài triệu tham số này)
lora = LoraConfig(
    r=SFT.r,
    lora_alpha=SFT.lora_alpha,
    lora_dropout=SFT.lora_dropout,
    bias="none",
    task_type="CAUSAL_LM",
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
)
model = get_peft_model(model, lora)
model.print_trainable_parameters()

# 3) Nạp + định dạng dataset theo chat template của Qwen
ds = load_dataset("json", data_files=str(DATA_FILE), split="train")


def format_and_tok(ex):
    text = tokenizer.apply_chat_template(ex["messages"], tokenize=False)
    return tokenizer(text, truncation=True, max_length=SFT.max_len)


ds = ds.map(format_and_tok, remove_columns=ds.column_names)
collator = DataCollatorForLanguageModeling(tokenizer, mlm=False)

# 4) Cấu hình train
args = TrainingArguments(
    output_dir=str(ADAPTER_DIR),
    per_device_train_batch_size=SFT.batch_size,
    gradient_accumulation_steps=SFT.grad_accum,
    learning_rate=SFT.lr,
    num_train_epochs=SFT.epochs,
    logging_steps=5,
    save_strategy="epoch",
    bf16=True,
    optim="paged_adamw_8bit",
    report_to="none",
)

model.config.use_cache = False
trainer = Trainer(model=model, args=args, train_dataset=ds, data_collator=collator)
trainer.train()

# 5) Lưu adapter
model.save_pretrained(str(ADAPTER_DIR))
tokenizer.save_pretrained(str(ADAPTER_DIR))
print("Đã lưu adapter vào:", ADAPTER_DIR)
