import pandas as pd

def clean_dk_file(input_file="DKSalaries.csv", output_file="cleaned_players.csv"):
    df = pd.read_csv(input_file)

    # Convert DraftKings file into optimizer-ready format
    df_clean = df[["Name", "TeamAbbrev", "Position", "Salary", "AvgPointsPerGame", "Game Info"]].copy()
    df_clean.columns = ["name", "team", "position", "salary", "ev", "game"]
    df_clean["sigma"] = df_clean["ev"] * 0.2

    df_clean = df_clean.drop_duplicates(subset=["name", "team", "position"])
    df_clean.to_csv(output_file, index=False)

    print(f"✅ Cleaned data saved to {output_file}")
    return df_clean

if __name__ == "__main__":
    clean_dk_file()
