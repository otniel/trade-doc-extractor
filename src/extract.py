import fitz
import json
from dotenv import load_dotenv
load_dotenv()
from anthropic import Anthropic
from schema import TradeConfirmation

def extract_text(pdf_path: str) -> str:
    doc = fitz.open(pdf_path)
    text = "\n".join(page.get_text() for page in doc)
    doc.close()
    return text

def extract_fields(text: str) -> dict:
    client = Anthropic()
    schema = TradeConfirmation.model_json_schema()
    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": f"Extract the fields from this trade confirmation. "
                       f"Return ONLY valid JSON matching this schema, no prose, no markdown fences:\n\n"
                       f"SCHEMA:\n{json.dumps(schema, indent=2)}\n\n"
                       f"DOCUMENT:\n{text}"
        }]
    )
    raw = resp.content[0].text.strip()
    print(raw)
    return
    #return json.loads(raw)

if __name__ == "__main__":
    text = extract_text("documents/trade_confirmation_001.pdf")
    fields = extract_fields(text)
    # print(json.dumps(fields, indent=2))
