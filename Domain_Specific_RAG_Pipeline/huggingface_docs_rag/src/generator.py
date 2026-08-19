from typing import List, Dict
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline


class LLMGenerator:
    def __init__(self, model_name: str, prompt_template: str):
        self.prompt_template = prompt_template
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto",
        )
        self.pipeline = pipeline("text-generation", model=self.model, tokenizer=self.tokenizer)

    def generate_answer(
        self, 
        query: str, 
        retrieved_docs: List[Dict], 
        max_new_tokens: int = 256
    ) -> Dict:
        context = "\n\n".join(doc["text"] for doc in retrieved_docs)
        prompt = self.prompt_template.format(context=context, question=query)

        outputs = self.pipeline(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            return_full_text=False,
        )
        answer = outputs[0]["generated_text"].strip()
        return {
            "query": query,
            "answer": answer,
            "context": context,
            "retrieved_docs": retrieved_docs,
        }