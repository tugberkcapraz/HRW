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


async def extract_accusation_category(session, primary_accusation):
    function_schema = {
        "name": "extract_accusation_category",
        "description": "Categorizes the primary accusation from a human rights article.",
        "parameters": {
            "type": "object",
            "properties": {
                "accusation_category": {
                    "type": "string",
                    "enum": [
                        "Political Repression and Authoritarianism",
                        "War Crimes and Crimes Against Humanity",
                        "Human Rights Violations",
                        "Discrimination and Persecution of Minorities",
                        "Freedom of Expression and Media Suppression",
                        "Violence Against Civilians",
                        "Judicial and Legal System Abuses",
                        "Women's and Children's Rights Violations",
                        "Refugee and Migrant Rights Violations",
                        "Environmental and Economic Injustices",
                        "Torture and Inhumane Treatment",
                        "Religious Freedom Violations",
                        "Labor Rights Violations",
                        "Electoral Misconduct and Democratic Backsliding",
                        "Arbitrary Detention and Enforced Disappearances"
                    ]
                }
            },
            "required": ["accusation_category"]
        }
    }

    try:
        async with session.post('https://api.openai.com/v1/chat/completions', json={
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "user",
                    "content": f"Categorize the following primary accusation: {primary_accusation}"
                }
            ],
            "functions": [function_schema],
            "function_call": {"name": "extract_accusation_category"}
        }, headers={"Authorization": f"Bearer {openai.api_key}"}) as response:
            response_data = await response.json()

        if 'choices' in response_data and len(response_data['choices']) > 0:
            category = json.loads(response_data['choices'][0]['message']['function_call']['arguments'])
            return category['accusation_category']
        else:
            print(f"Error: Unexpected response format: {response_data}")
            return None

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

async def process_chunk(session, chunk):
    async def process_row(row):
        try:
            accusation_category = await extract_accusation_category(session, row['Primary Accusation'])
            return accusation_category
        except Exception as e:
            print(f"Error processing row: {e}")
            return None

    tasks = [process_row(row) for _, row in chunk.iterrows()]
    results = await asyncio.gather(*tasks)
    return results

async def categorize_accusations(input_csv, output_csv, chunk_size=50):
    # Read the CSV file
    df = pd.read_csv(input_csv)
    
    # Ensure 'Primary Accusation' column exists
    if 'Primary Accusation' not in df.columns:
        raise ValueError("The 'Primary Accusation' column is missing from the input CSV.")

    categories = []
    async with aiohttp.ClientSession() as session:
        for i in tqdm(range(0, len(df), chunk_size), desc="Processing chunks"):
            chunk = df.iloc[i:i+chunk_size]
            chunk_categories = await process_chunk(session, chunk)
            categories.extend(chunk_categories)

    # Add the new column to the DataFrame
    df['accusation_category'] = categories

    # Save the updated DataFrame
    df.to_csv(output_csv, index=False)
    print(f"Categorized data saved to {output_csv}")

# Usage
if __name__ == "__main__":
    input_file = 'hrw_articles_with_dimensions.csv'
    output_file = 'hrw_articles_with_categories.csv'
    asyncio.run(categorize_accusations(input_file, output_file, chunk_size=50))
