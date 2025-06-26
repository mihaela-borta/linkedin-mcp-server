import json
import csv


def process_batch_results(input_file, output_file):
    """Process batch results JSONL file and convert to CSV"""
    results = []

    with open(input_file, "r", encoding="utf-8") as file:
        for line in file:
            result = json.loads(line.strip())

            # Extract the JSON content from the message
            if result["result"]["type"] == "succeeded":
                content = result["result"]["message"]["content"][0]["text"]

                # Find the JSON block in the response
                json_start = content.find("```json\n") + 8
                json_end = content.find("\n```")

                if json_start > 7 and json_end > json_start:
                    json_content = content[json_start:json_end]
                    try:
                        extracted_data = json.loads(json_content)
                        results.append(extracted_data)
                    except json.JSONDecodeError as e:
                        print(f"JSON decode error for {result['custom_id']}: {e}")
                        print(f"Content: {json_content[:200]}...")

    # Define the CSV fieldnames in the requested order
    fieldnames = [
        "Company",
        "Title",
        "Name",
        "Email",
        "Phone",
        "LinkedIn",
        "Location",
        "Industry",
        "Brief_Profile",
        "Detailed_Profile",
        "Media_Links",
        "Professional_Links",
    ]

    # Write to CSV with semicolon separator
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()

        for result in results:
            # Ensure all fields exist, use empty string if missing
            row = {}
            for field in fieldnames:
                row[field] = result.get(field, "")
            writer.writerow(row)

    print(f"Successfully processed {len(results)} records to {output_file}")
    return len(results)


# Process the batch results
if __name__ == "__main__":
    input_file = "data/parsed_ddg_results_frej.jsonl"
    output_file = "data/parsed_ddg_results_frej.csv"

    count = process_batch_results(input_file, output_file)
    print(f"CSV file created with {count} profiles")
