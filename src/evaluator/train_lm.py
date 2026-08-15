from pathlib import Path
import random
import yaml
import shutil
import subprocess
import sys
import torch
import importlib
import time


def load_config():
    with open("config/evaluator_config.yaml","r",encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_tokenizer(language):
    module_name = (
        f"src.evaluator.{language}_tokenizer"
    )

    tokenizer_module = importlib.import_module(
        module_name
    )

    return tokenizer_module.tokenize


def set_seed(seed):
    random.seed(seed)

    torch.manual_seed(seed)

    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def select_device(device):
    if device == "cpu":
        return -1

    if device == "gpu":
        if not torch.cuda.is_available():
            raise RuntimeError(
                "GPU requested but CUDA unavailable."
            )
        return 0

    if torch.cuda.is_available():
        return 0

    return -1


def split_dataset(src_path,tgt_path,output_dir,seed):
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(src_path,"r",encoding="utf-8") as f:
        src_lines = f.readlines()

    with open(tgt_path,"r",encoding="utf-8") as f:
        tgt_lines = f.readlines()

    if len(src_lines) != len(tgt_lines):
        raise ValueError(
            "src/tgt line number mismatch."
        )

    data = list(
        zip(
            src_lines,
            tgt_lines
        )
    )

    random.Random(seed).shuffle(data)

    split_point = int(len(data) * 0.9)
    train = data[:split_point]
    valid = data[split_point:]

    paths = {
        "train_src":
            output_dir / "train.src",
        "train_tgt":
            output_dir / "train.tgt",
        "valid_src":
            output_dir / "valid.src",
        "valid_tgt":
            output_dir / "valid.tgt"
    }

    with(
        open(paths["train_src"],"w",encoding="utf-8") as src,
        open(paths["train_tgt"],"w",encoding="utf-8") as tgt
    ):         
        for s,t in train:
            src.write(s)
            tgt.write(t)

    with(
        open(paths["valid_src"],"w",encoding="utf-8") as src,
        open(paths["valid_tgt"],"w",encoding="utf-8") as tgt
    ):
        for s,t in valid:
            src.write(s)
            tgt.write(t)

    return paths


def tokenize_file(input_path,output_path,tokenizer):
    with(
        open(input_path,"r",encoding="utf-8") as infile,
        open(output_path,"w",encoding="utf-8") as outfile
    ):  
        for line in infile:
            text = line.strip()
            tokenized_text = tokenizer(text)
            tokenized_text = " ".join(tokenized_text.split())
            outfile.write(
                tokenized_text
                +
                "\n"
            )


def normalize_vocab_file(path):
    path = Path(path)

    text = path.read_text(
        encoding="utf-8"
    )

    text = text.replace(
        "\r\n",
        "\n"
    )

    path.write_text(
        text,
        encoding="utf-8",
        newline="\n"
    )


def create_onmt_config(config_path,data_paths,checkpoint_dir,train_config):
    vocab_path = Path(
        checkpoint_dir /
        "vocab"
    )

    model_path = Path(
        checkpoint_dir /
        "model"
    )

    config = {
        "save_data":str(vocab_path),
        "data":{
            "corpus_1":{
                "path_src":str(data_paths["train_src"]),
                "path_tgt":str(data_paths["train_tgt"])
            },
            "valid":{
                "path_src":str(data_paths["valid_src"]),
                "path_tgt":str(data_paths["valid_tgt"])
            }
        },
        "src_vocab":str(vocab_path) + ".src",
        "tgt_vocab":str(vocab_path) + ".tgt",
        "save_model":str(model_path),
        "encoder_type":"transformer",
        "decoder_type":"transformer",
        "layers":2,
        "hidden_size":256,
        "word_vec_size":256,
        "heads":4,
        "transformer_ff":1024,
        "position_encoding":True,
        "batch_type":"tokens",
        "batch_size":train_config.get("batch_size",2048),
        "normalization":"tokens",
        "optim":"adam",
        "adam_beta2":0.998,
        "max_grad_norm":0,
        "param_init":0,
        "param_init_glorot":True,
        "label_smoothing":0.1,
        "num_workers":0,
        "train_steps":train_config.get("train_steps",20000),
        "valid_steps":train_config.get("valid_steps",1000),
        "save_checkpoint_steps":train_config.get("save_checkpoint_steps",5000),
        "learning_rate":train_config.get("learning_rate",2.0),
        "decay_method":"noam",
        "warmup_steps":1000,
    }

    with open(config_path,"w",encoding="utf-8") as f:
        yaml.safe_dump(config,f,allow_unicode=True)


def run_command(args):
    subprocess.run(
        [
            sys.executable
        ]
        +
        args,
        check=True
    )


def find_checkpoint(checkpoint_dir):
    models = list(
        checkpoint_dir.glob(
            "model_step_*.pt"
        )
    )

    if not models:
        raise FileNotFoundError(
            "No checkpoint found."
        )

    return max(
        models,
        key=lambda x:x.stat().st_mtime
    )


def train_model(train_src_path,train_tgt_path,test_src_path,output_prediction_path):
    config = load_config()

    seed = config["train_lm"]["seed"]
    set_seed(seed)

    src_lang = config["train_lm"]["src_lang"]
    tgt_lang = config["train_lm"]["tgt_lang"]

    checkpoint_dir = (
        Path(config["train_lm"]["checkpoints_dir"])
        /
        f"{src_lang}-{tgt_lang}"
    )

    if checkpoint_dir.exists():
        time.sleep(3)
        shutil.rmtree(checkpoint_dir)

    checkpoint_dir.mkdir(
            parents=True
    )

    temp_dir = (
        checkpoint_dir /
        "temp"
    )

    if temp_dir.exists():
        shutil.rmtree(
            temp_dir
        )

    temp_dir.mkdir(
        parents=True
    )

    data_paths = split_dataset(
        Path(train_src_path),
        Path(train_tgt_path),
        temp_dir,
        seed
    )

    src_tokenizer = load_tokenizer(src_lang)
    tgt_tokenizer = load_tokenizer(tgt_lang)

    tokenize_file(
        data_paths["train_src"],
        temp_dir / "train.tokenized.src",
        src_tokenizer
    )

    tokenize_file(
        data_paths["train_tgt"],
        temp_dir / "train.tokenized.tgt",
        tgt_tokenizer
    )

    tokenize_file(
        data_paths["valid_src"],
        temp_dir / "valid.tokenized.src",
        src_tokenizer
    )

    tokenize_file(
        data_paths["valid_tgt"],
        temp_dir / "valid.tokenized.tgt",
        tgt_tokenizer
    )

    tokenized_paths = {
        "train_src": temp_dir / "train.tokenized.src",
        "train_tgt": temp_dir / "train.tokenized.tgt",
        "valid_src": temp_dir / "valid.tokenized.src",
        "valid_tgt": temp_dir / "valid.tokenized.tgt"
    }

    onmt_config = (
        temp_dir /
        "config.yaml"
    )

    create_onmt_config(
        onmt_config,
        tokenized_paths,
        checkpoint_dir,
        config["train_lm"]
    )

    run_command(
        [
            "-m",
            "onmt.bin.build_vocab",
            "-config",
            str(onmt_config)
        ]
    )

    vocab_path = checkpoint_dir / "vocab"

    normalize_vocab_file(
        str(vocab_path) + ".src"
    )

    normalize_vocab_file(
        str(vocab_path) + ".tgt"
    )

    train_cmd = [
        "-m",
        "onmt.bin.train",
        "-config",
        str(onmt_config)
    ]

    if select_device(
        config["train_lm"]["device"]
    ) >= 0:
        train_cmd += [
            "-gpu_ranks",
            "0"
        ]

    run_command(
        train_cmd
    )

    model_path = find_checkpoint(
        checkpoint_dir
    )

    output_prediction_path = Path(
        output_prediction_path
    )

    output_prediction_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    tokenized_test_path = (
        temp_dir /
        "test.tokenized.src"
    )

    tokenize_file(
        test_src_path,
        tokenized_test_path,
        src_tokenizer
    )

    translate_cmd = [
        "-m",
        "onmt.bin.translate",
        "-model",
        str(model_path),
        "-src",
        str(tokenized_test_path),
        "-output",
        str(output_prediction_path),
        "-beam_size",
        str(
            config["train_lm"]["beam_size"]
        )
    ]

    if select_device(
        config["train_lm"]["device"]
    ) >=0:
        translate_cmd += [
            "-gpu",
            "0"
        ]

    run_command(
        translate_cmd
    )

    #shutil.rmtree(
    #    temp_dir,
    #    ignore_errors=True
    #)