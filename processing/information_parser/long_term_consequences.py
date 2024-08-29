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

async def extract_long_term_consequence_category(session, long_term_consequence):
    function_schema = {
        "name": "extract_long_term_consequence_category",
        "description": "Categorizes the long-term consequences from a human rights article.",
        "parameters": {
            "type": "object",
            "properties": {
                "long_term_consequence_category": {
                    "type": "string",
                    "enum": [
                        "Erosion of Civil Liberties and Democratic Processes",
                        "Humanitarian Crises and Displacement",
                        "Impunity and Lack of Accountability",
                        "Discrimination and Marginalization",
                        "Violence and Conflict Escalation",
                        "Suppression of Dissent and Free Expression",
                        "Economic and Social Instability",
                        "Environmental Degradation and Health Risks",
                        "Cultural and Identity Erasure",
                        "Judicial and Legal System Failures",
                        "International Law and Diplomacy Challenges",
                        "Educational and Developmental Setbacks",
                        "Psychological and Social Trauma",
                        "Women's and LGBTQ+ Rights Violations",
                        "Child Rights Violations",
                        "Refugee and Migrant Rights Abuses",
                        "Media Freedom Restrictions",
                        "Labor Rights Violations"
                    ]
                }
            },
            "required": ["long_term_consequence_category"]
        }
    }

    try:
        async with session.post('https://api.openai.com/v1/chat/completions', json={
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": f"Categorize the following long-term consequence: {long_term_consequence}"
                }
            ],
            "functions": [function_schema],
            "function_call": {"name": "extract_long_term_consequence_category"}
        }, headers={"Authorization": f"Bearer {openai.api_key}"}) as response:
            response_data = await response.json()

        if 'choices' in response_data and len(response_data['choices']) > 0:
            category = json.loads(response_data['choices'][0]['message']['function_call']['arguments'])
            return category['long_term_consequence_category']
        else:
            print(f"Error: Unexpected response format: {response_data}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def process_chunk(session, chunk):
    async def process_row(row):
        try:
            long_term_consequence_category = await extract_long_term_consequence_category(session, row['Long-term Consequences'])
            return long_term_consequence_category
        except Exception as e:
            print(f"Error processing row: {e}")
            return None

    tasks = [process_row(row) for _, row in chunk.iterrows()]
    results = await asyncio.gather(*tasks)
    return results

async def categorize_long_term_consequences(input_csv, output_csv, chunk_size=50):
    # Read the CSV file
    df = pd.read_csv(input_csv)
    
    # Ensure 'Long-term Consequences' column exists
    if 'Long-term Consequences' not in df.columns:
        raise ValueError("The 'Long-term Consequences' column is missing from the input CSV.")

    categories = []
    async with aiohttp.ClientSession() as session:
        for i in tqdm(range(0, len(df), chunk_size), desc="Processing chunks"):
            chunk = df.iloc[i:i+chunk_size]
            chunk_categories = await process_chunk(session, chunk)
            categories.extend(chunk_categories)

    # Add the new column to the DataFrame
    df['long_term_consequence_category'] = categories

    # Save the updated DataFrame
    df.to_csv(output_csv, index=False)
    print(f"Categorized data saved to {output_csv}")

# Usage
if __name__ == "__main__":
    input_file = 'hrw_articles_with_categories.csv'
    output_file = 'hrw_articles_with_categories.csv'
    asyncio.run(categorize_long_term_consequences(input_file, output_file, chunk_size=50))
