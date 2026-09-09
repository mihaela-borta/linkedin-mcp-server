import json
import csv
import requests
from anthropic import Anthropic


def extract_json_from_text(text):
    # Find the first '{' and last '}' to extract the JSON block
    json_start = text.find("{")
    json_end = text.rfind("}") + 1
    if json_start != -1 and json_end > json_start:
        try:
            return json.loads(text[json_start:json_end])
        except Exception as e:
            print(
                f"JSON decode error: {e}\nContent: {text[json_start:json_end][:200]}..."
            )
    return None


def jsonl_to_csv(input_file, output_file, delete_input=True):
    records = []
    all_keys = set()

    with open(input_file, "r", encoding="utf-8") as infile:
        for line in infile:
            obj = json.loads(line)
            # Navigate to the text field
            try:
                text = obj["result"]["message"]["content"][0]["text"]
            except Exception as e:
                print(f"Error extracting text: {e}")
                continue
            data = extract_json_from_text(text)
            records.append(data)
            all_keys.update(data.keys())

    fieldnames = sorted(all_keys)

    with open(output_file, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        for rec in records:
            writer.writerow({k: rec.get(k, "") for k in fieldnames})

    print(f"Wrote {len(records)} records to {output_file}")
    
    if delete_input:
        try:
            import os
            os.remove(input_file)
            print(f"Deleted input file: {input_file}")
        except Exception as e:
            print(f"Warning: Could not delete input file {input_file}: {e}")


def json_to_csv(input_file, output_file, delete_input=True):
    """Convert JSON file to CSV, handling both single JSON objects and JSONL format"""
    records = []
    all_keys = set()

    try:
        with open(input_file, "r", encoding="utf-8") as infile:
            content = infile.read().strip()
            
            # Try to parse as single JSON first
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    # It's a JSON array
                    for item in data:
                        if isinstance(item, dict):
                            records.append(item)
                            all_keys.update(item.keys())
                elif isinstance(data, dict):
                    # It's a single JSON object
                    records.append(data)
                    all_keys.update(data.keys())
                else:
                    print(f"Unexpected JSON format: {type(data)}")
                    return False
            except json.JSONDecodeError:
                # Try JSONL format (line-by-line JSON)
                infile.seek(0)
                for line in infile:
                    line = line.strip()
                    if line:
                        try:
                            obj = json.loads(line)
                            if isinstance(obj, dict):
                                records.append(obj)
                                all_keys.update(obj.keys())
                        except json.JSONDecodeError as e:
                            print(f"Error parsing JSONL line: {e}")
                            continue

        if not records:
            print("No valid records found in input file")
            return False

        fieldnames = sorted(all_keys)

        with open(output_file, "w", newline="", encoding="utf-8") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=";")
            writer.writeheader()
            for rec in records:
                writer.writerow({k: rec.get(k, "") for k in fieldnames})

        print(f"Wrote {len(records)} records to {output_file}")
        
        if delete_input:
            try:
                import os
                os.remove(input_file)
                print(f"Deleted input file: {input_file}")
            except Exception as e:
                print(f"Warning: Could not delete input file {input_file}: {e}")
        
        return True
        
    except Exception as e:
        print(f"Error processing file: {e}")
        return False


def clean_string(s: str) -> str:
    s = s.replace("Ø", "Oe").replace("ø", "oe")
    s = s.replace("Æ", "Ae").replace("æ", "ae")
    s = s.replace("Å", "Aa").replace("å", "aa")
    s = s.encode("ascii", "replace").decode("ascii")
    s = "".join(c for c in s if c.isalnum())
    return s or "unknown"


def create_batch_job(client: Anthropic, requests):
    print(type(client))
    batch = client.messages.batches.create(requests=requests)
    print(f"Batch job created with ID: {batch.id}")
    return batch.id


def poll_for_batch_completion(
    client: Anthropic, batch_id: str, poll_interval: int = 60
) -> str:
    print(f"Polling for batch {batch_id} to complete...")
    import time

    while True:
        print(type(client))
        batch = client.messages.batches.retrieve(batch_id)
        print(f"Batch status: {batch.processing_status}")
        if batch.processing_status == "ended":
            print("Batch processing ended.")
            if hasattr(batch, "results_url") and batch.results_url:
                print(f"Results URL: {batch.results_url}")
                return batch.results_url
            else:
                print("Batch ended but no results_url found!")
                raise RuntimeError("Batch ended but no results_url found!")
        else:
            print(f"Batch {batch_id} is still processing...")
            time.sleep(poll_interval)


def download_results_file(results_url: str, output_jsonl: str, api_key: str):
    print(f"Downloading results from {results_url} to {output_jsonl}")
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    response = requests.get(results_url, headers=headers, stream=True)
    response.raise_for_status()
    with open(output_jsonl, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print(f"Results downloaded to {output_jsonl}")
