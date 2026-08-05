import jieba


def tokenize(text):
    tokens = jieba.cut(
        text,
        cut_all=False
    )
    
    return " ".join(tokens)