from transformers import MBart50TokenizerFast
from transformers import MBartForConditionalGeneration

tokenizer = MBart50TokenizerFast.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")
model = MBartForConditionalGeneration.from_pretrained("facebook/mbart-large-50-many-to-many-mmt")

def translate_prompt(prompt, src_lang):
    """helper function to translate prompt to English"""

    tokenizer.set_src_lang_special_tokens(src_lang)
    tokenizer.src_lang = src_lang

    encoded_prompt = tokenizer(prompt, return_tensors="pt").to("cpu")
    generated_tokens = model.generate(**encoded_prompt, max_new_tokens=1000, forced_bos_token_id=tokenizer.lang_code_to_id["en_XX"])

    en_trans = tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    return en_trans[0]
