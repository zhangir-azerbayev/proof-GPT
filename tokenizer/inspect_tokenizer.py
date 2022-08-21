import sys
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained(sys.argv[1])
print(tokenizer)

tokens = sorted(tokenizer.vocab.items(), key=lambda x: x[1], reverse=False)

whitespace_tokens=0

print('first words after base vocabulary')
for token, index in tokens[257:280]: 
    text = tokenizer.convert_tokens_to_string(token)
    if len(text.strip())>1: 
        print(f'`{text}` at index {index}')
    else: 
        whitespace_tokens+=1
print(f'\nNumber of whitespace tokens: {whitespace_tokens}')

print("Last words in the vocabulary:")
for token, index in tokens[-20:-3]:
    print(f'`{tokenizer.convert_tokens_to_string(token)}` at index {index}')
