import pandas as pd
import os
import argparse

parser = argparse.ArgumentParser(description="Name of the csv file that needs to be converted.")
parser.add_argument("file", type=str, help="The csv file name")
args = parser.parse_args()

# Set the paths
input_csv = args.file.lower() # Change to your actual CSV filename
output_dir = os.getcwd()  # Folder where .txt files will be stored

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Load the CSV file
df = pd.read_csv(input_csv)


print(type(df))
# Inspect the first few rows to find the correct column names
print(df.head())

# Define columns to include (adjust these based on your dataset)
ticket_id_col = "ticket_id"  # Update if your CSV has a different column name
subject_col = "subject"  # Update if available
body_col = "body"
answer_col = "answer"
type_col = "type"

# Loop through each row and save as a .txt file
for index, row in df.iterrows():
    ticket_id = row.get(ticket_id_col, f"ticket_{index}")
    subject = row.get(subject_col, "No Subject")
    body = row.get(body_col, "No Description")
    answer = row.get(answer_col, "Unknown Priority")
    type = row.get(type_col, "Unknown Status")

    # Format the ticket content
    content = f"""Ticket ID: {ticket_id}
Subject: {subject}
Incident Type: {type}
Customer Issue: {body}
Customer Service answer: {answer}
"""

    # Save as a .txt file
    filename = os.path.join(output_dir, f"ticket_{ticket_id}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)

print(f"✅ {len(df)} tickets have been saved in '{output_dir}/' as .txt files.")
