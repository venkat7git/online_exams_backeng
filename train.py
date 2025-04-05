import pandas as pd
import os
from model import get_similarity

def load_data():
    df = pd.read_csv('data/claude_train_data.csv')
    file_path = "/data/claude_train_data.csv"
    if os.path.exists(file_path):
        print(f"✅ File found at {file_path}")
    else:
        print(f"❌ File not found at {file_path}. Check the directory.")
    print(df.head())
    return df

def evaluate():
    df = load_data()

    # Extract only the predicted score
    df['predicted_score'] = df.apply(lambda row: get_similarity(row['actual_answer'], row['student_answer'])[0], axis=1)

    # Display results
    print(df[['actual_answer', 'student_answer', 'score', 'predicted_score']].head())

if __name__ == "__main__":
    evaluate()
