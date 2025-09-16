import re
import unicodedata


def normalize_text(text):
    text = re.sub(r"[‘'´`]", "'", text)
    text = re.sub(r'[""]', '"', text)
    text = unicodedata.normalize("NFC", text)
    text = re.sub(r"[\x00-\x09\x0B-\x1F\x7F]", "", text)
    return text


def clean_inline_media(text):
    text = re.sub(r"\[https?:\/\/[^\]]+\]", "", text)
    text = re.sub(r"Image:\s*https?:\/\/\S+", "", text)
    text = re.sub(r"\[\w+\]\s*=>\s*[^ ]+", "", text)
    text = re.sub(r"\[[^\]]+\]", "", text)
    return text.strip()


def clean_text(text):
    text = normalize_text(text)
    text = clean_inline_media(text)

    text = text.replace("=>", "→")
    text = text.replace("->", "→")
    text = text.replace("→", " ")
    text = re.sub(r"[-]{1,2}>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
