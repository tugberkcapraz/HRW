import pandas as pd
import openai
import asyncio
import aiohttp
import json
from tqdm import tqdm
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

async def extract_victim_category(session, victim_demographics):
    function_schema = {
        "name": "extract_victim_category",
        "description": "Categorizes the victim demographics from a human rights article.",
        "parameters": {
            "type": "object",
            "properties": {
                "victim_category": {
                    "type": "string",
                    "enum": [
                        "Ethnic and religious minorities",
                        "Political dissidents and activists",
                        "Journalists and media professionals",
                        "Women and girls",
                        "Children and youth",
                        "LGBTQ+ individuals",
                        "Refugees and migrants",
                        "Indigenous peoples",
                        "Civilians in conflict zones",
                        "Human rights defenders",
                        "Specific named individuals",
                        "General populations of various countries",
                        "People with disabilities",
                        "Workers and labor rights advocates",
                        "Environmental activists",
                        "Prisoners and detainees"
                    ]
                }
            },
            "required": ["victim_category"]
        }
    }

    try:
        async with session.post('https://api.openai.com/v1/chat/completions', json={
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": f"Categorize the following victim demographics: {victim_demographics}"
                }
            ],
            "functions": [function_schema],
            "function_call": {"name": "extract_victim_category"}
        }, headers={"Authorization": f"Bearer {openai.api_key}"}) as response:
            response_data = await response.json()

        if 'choices' in response_data and len(response_data['choices']) > 0:
            category = json.loads(response_data['choices'][0]['message']['function_call']['arguments'])
            return category['victim_category']
        else:
            print(f"Error: Unexpected response format: {response_data}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def process_chunk(session, chunk):
    async def process_row(row):
        try:
            victim_category = await extract_victim_category(session, row['Victim Demographics'])
            return victim_category
        except Exception as e:
            print(f"Error processing row: {e}")
            return None

    tasks = [process_row(row) for _, row in chunk.iterrows()]
    results = await asyncio.gather(*tasks)
    return results

async def categorize_victim_demographics(input_csv, output_csv, chunk_size=50):
    # Read the CSV file
    df = pd.read_csv(input_csv)
    
    # Ensure 'Victim Demographics' column exists
    if 'Victim Demographics' not in df.columns:
        raise ValueError("The 'Victim Demographics' column is missing from the input CSV.")

    categories = []
    async with aiohttp.ClientSession() as session:
        for i in tqdm(range(0, len(df), chunk_size), desc="Processing chunks"):
            chunk = df.iloc[i:i+chunk_size]
            chunk_categories = await process_chunk(session, chunk)
            categories.extend(chunk_categories)

    # Add the new column to the DataFrame
    df['victim_category'] = categories

    # Save the updated DataFrame
    df.to_csv(output_csv, index=False)
    print(f"Categorized data saved to {output_csv}")

# Usage
if __name__ == "__main__":
    input_file = 'hrw_articles_with_categories.csv'
    output_file = 'hrw_articles_with_categories.csv'
    asyncio.run(categorize_victim_demographics(input_file, output_file, chunk_size=50))
