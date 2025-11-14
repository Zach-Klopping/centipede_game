import pandas as pd
from openpyxl.utils import get_column_letter

raw_csv = "/Users/zachklopping/Desktop/Centipede.csv"     # your oTree raw data
output_xlsx = "clean.xlsx"   # output Excel file

# Load CSV
df = pd.read_csv(raw_csv)

df = df[df["participant._current_page_name"] == "Conclusion"]

# participant columns to keep explicitly (Unchanged)
participant_cols = [
    "participant.id_in_session",
    "participant.code",
    "participant.label",
    "participant._current_page_name",
    "participant.payoff",
    "centipede_game_1.2.group.id_in_subsession"
]

# Start the clean dataframe with just the participant data
df_clean = df.loc[:, participant_cols].copy()

# --- START: New "Per-Row" Merging Logic ---
for r in range(1, 5):  # For games 1–4
    
    # 1. COALESCE PAYOFFS (Numeric)
    payoff_cols = df.filter(regex=f"^centipede_game_{r}\..*\.player\.payoff_final$").columns
    if not payoff_cols.empty:
        # Sum them horizontally (axis=1)
        payoff_data = df[payoff_cols].apply(pd.to_numeric, errors='coerce').sum(axis=1)
        df_clean[f'game_{r}.payoff_final'] = payoff_data

    # 2. COALESCE PLAYER.FIRST (Non-Numeric)
    first_cols = df.filter(regex=f"^centipede_game_{r}\..*\.player\.first$").columns
    if not first_cols.empty:
        # bfill() fills NaN with the next value in the row
        first_data = df[first_cols].fillna(method='bfill', axis=1).iloc[:, 0]
        df_clean[f'game_{r}.player_first'] = first_data

    # 3. COALESCE PLAYER.TAKE and FIND ROUND (Numeric)
    take_cols = df.filter(regex=f"^centipede_game_{r}\..*\.player\.take$").columns
    if not take_cols.empty:
        # Convert all to numeric (NaNs for errors)
        take_df = df[take_cols].apply(pd.to_numeric, errors='coerce')
        
        # A) Create the simple 'take' column (0 or 1)
        # We can sum() them just like payoffs. A row like [NaN, 0, 1, 0] becomes 1.
        df_clean[f'game_{r}.take'] = take_df.sum(axis=1)
        
        # B) Find the round number they took in
        # .idxmax(axis=1) finds the column *name* (label) with the max value (which is 1)
        # We replace 0 with NaN so idxmax() ignores 'pass' (0) rounds
        take_col_names = take_df.replace(0, pd.NA).idxmax(axis=1)
        
        # Extract the round number (1-6) from the column name
        df_clean[f'game_{r}.round_taken'] = take_col_names.str.extract(r"\.([1-6])\.")[0].astype(float)

# --- END: New "Per-Row" Merging Logic ---

# Rename the group ID as you had before (Unchanged)
df_clean = df_clean.rename(columns={
    "centipede_game_1.2.group.id_in_subsession": "group.id_in_subsession"
})

# Save to Excel with adjusted column widths
with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
    df_clean.to_excel(writer, index=False, sheet_name="CleanedData")
    worksheet = writer.sheets["CleanedData"]

    # Auto-adjust column widths based on content
    for i, column in enumerate(df_clean.columns, start=1):
        col_letter = get_column_letter(i)
        # Calculate width based on column name length plus some padding
        column_width = max(len(str(column)) + 2, 10)  # minimum width of 10
        worksheet.column_dimensions[col_letter].width = column_width
        
print(f"Successfully cleaned data and saved to {output_xlsx}")