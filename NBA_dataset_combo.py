import pandas as pd

def aggregate_player_totals(input_csv_path, output_csv_path, sum_columns, keep_columns, max_columns, concat_columns, year_column):
   
    try:
        df = pd.read_csv(input_csv_path)
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return

    # Filter to include only specified columns plus 'playerid'
    all_specified_columns = set(sum_columns + keep_columns + max_columns + concat_columns + [year_column])
    df_filtered = df.loc[:, df.columns.intersection(all_specified_columns)]

    # Define aggregation dictionary
    agg_dict = {col: 'sum' for col in sum_columns}
    agg_dict.update({col: 'first' for col in keep_columns})
    agg_dict.update({col: 'max' for col in max_columns})
    agg_dict.update({col: lambda x: ', '.join(x.astype(str)) for col in concat_columns})
    agg_dict.update({
        year_column: lambda x: f"{str(x.min())}-{str(x.max())}" if not x.empty else ""
        })

    # Group by playerid and aggregate
    aggregated_df = df_filtered.groupby('player_id', as_index=False).agg(agg_dict)

    # Write the aggregated DataFrame to a new CSV file
    try:
        aggregated_df.to_csv(output_csv_path, index=False)
        print(f"Aggregated totals successfully written to {output_csv_path}")
    except Exception as e:
        print(f"Error writing the aggregated CSV file: {e}")

def calculate_percentages_and_per_game_stats(totals_csv_path):
    try:
        df = pd.read_csv(totals_csv_path)
    except Exception as e:
        print(f"Error reading the CSV file: {e}")
        return
    df['mpg'] = df['mp'] / df['g']
    df['fg%'] = df['fg'] / df['fga']
    df['3p%'] = df['x3p'] / df['x3pa']
    df['2p%'] = df['x2p'] / df['x2pa']
    df['ft%'] = df['ft'] / df['fta']
    df['rpg'] = df['trb'] / df['g']
    df['apg'] = df['ast'] / df['g']
    df['spg'] = df['stl'] / df['g']
    df['bpg'] = df['blk'] / df['g']
    df['tpg'] = df['tov'] / df['g']
    df['pfpg'] = df['pf'] / df['g']
    df['ppg'] = df['pts'] / df['g']
    try:
        df.to_csv(totals_csv_path, index=False)
        print(f"Per Game totals successfully written to {totals_csv_path}")
    except Exception as e:
        print(f"Error writing the aggregated CSV file: {e}")

def count_all_star_appearances(data_csv_path, names_csv_path):
    df_names = pd.read_csv(names_csv_path)
    df_data = pd.read_csv(data_csv_path)

    names = df_names['player'].unique()
    name_counts = {name: 0 for name in names}
    for name in names:
        name_counts[name] = (df_data['player'] == name).sum()

    # If a name from df_names does not appear in df_data, it will get a count of 0
    df_names['all-star selections'] = df_names['player'].map(name_counts).fillna(0)
    df_names.to_csv(names_csv_path, index=False)
    print(f"All Star Selections successfully written to {names_csv_path}")

def award_counter(award_csv, total_csv):
    # Load awards data
    awards_df = pd.read_csv(award_csv)

    # Load combined NBA totals data
    combined_totals_df = pd.read_csv(total_csv)

    # Filter for award winners
    winners_df = awards_df[awards_df['winner'] == True]

    # Count the occurrences of each player winning each award
    award_counts = winners_df.groupby(['player', 'award']).size().reset_index(name='count')

    # Pivot the award counts DataFrame
    award_counts_pivot = award_counts.pivot(index='player', columns='award', values='count').fillna(0).reset_index()

    # Merge the award counts with the combined totals DataFrame
    combined_totals_with_awards = combined_totals_df.merge(award_counts_pivot, on='player', how='left').fillna(0)

    # Assuming 'player' column exists in combined_totals_df for the merge
    # If the 'player' column does not exist or has a different name, adjust 'on' parameter in merge

    # Example to save the merged DataFrame back to a new CSV file
    combined_totals_with_awards.to_csv(total_csv, index=False)
    print(f"Award totals successfully written to {total_csv}")


def rings_appearances_counter(losses_csv, wins_csv, total_csv):
    total_df = pd.read_csv(total_csv)
    losses_df = pd.read_csv(losses_csv)
    wins_df = pd.read_csv(wins_csv, encoding='ISO-8859-1')

    # Convert 'player' columns to lowercase for case-insensitive comparison
    total_df['player'] = total_df['player'].str.lower()
    wins_df['player'] = wins_df['player'].str.lower()
    losses_df['player'] = losses_df['player'].str.lower()


    # Count the championships per player
    player_rings = wins_df['player'].value_counts().reset_index()
    player_rings.columns = ['player', 'count']
    merged_df = pd.merge(total_df, player_rings, on='player', how='left')

    merged_df['championships'] = merged_df['count'].fillna(0).astype(int)
    merged_df.drop(columns=['count'], inplace=True)

   # Count the finals losses per player
    player_losses = losses_df['player'].value_counts().reset_index()
    player_losses.columns = ['player', 'losses_count']

    # Combine the championships count and the losses count to get finals appearances
    player_rings.columns = ['player', 'wins_count']
    player_appearances = pd.merge(player_rings, player_losses, on='player', how='outer')
    player_appearances['finals_appearances'] = player_appearances['wins_count'].fillna(0) + player_appearances['losses_count'].fillna(0)

    # Merge the finals appearances with the merged_df
    merged_df = pd.merge(merged_df, player_appearances[['player', 'finals_appearances']], on='player', how='left')

    # Fill NaN values with 0 for players without any finals appearances
    merged_df['finals_appearances'] = merged_df['finals_appearances'].fillna(0).astype(int)



    # Filter for fmvp == True
    fmvp_true = wins_df[wins_df['fmvp'] == True]
    fmvp_counts = fmvp_true['player'].value_counts().reset_index()
    fmvp_counts.columns = ['player', 'fmvp']

    # Merge the fmvp counts
    merged_df = pd.merge(merged_df, fmvp_counts, on='player', how='left')
    # Fill NaN values with 0 for players without an 'fmvp' count
    merged_df['fmvp'] = merged_df['fmvp'].fillna(0).astype(int)

    # Save the merged DataFrame to a CSV file
    merged_df.to_csv(total_csv, index=False)
    print(f"Championships/Appearance/fmvps successfully written to {total_csv}")

def hall_of_fame(total_csv, hof_csv):
    totals_df = pd.read_csv(total_csv)
    hof_df = pd.read_csv(hof_csv)

    hof_df['player'] = hof_df['player'].str.lower().str.strip()

    totals_df['hof'] = totals_df['player'].isin(hof_df['player']).map({True: 'yes', False: 'no'})
    totals_df.loc[totals_df['season'].str.contains('2024'), 'hof'] = 'active'


    totals_df.to_csv(total_csv, index=False)
    print(f"Hall of Fame successfully written to {total_csv}")

def reorder_columns(final_csv):
    final_df = pd.read_csv(final_csv)
    new_order = ['player', 'hof', 'pos', 'experience', 'tm', 'age', 'season', 'lg', 'player_id',
                 'nba mvp', 'aba mvp', 'championships', 'finals_appearances', 'fmvp', 'all-star selections', 
                 'nba roy', 'aba roy', 'dpoy', 'smoy', 'dpoy', 'g','gs','mp','fg','fga','x3p','x3pa','x2p','x2pa','ft','fta',
                 'orb','drb','trb','ast','stl','blk','tov','pf','pts','mpg','fg%','3p%','2p%','ft%','rpg',
                 'apg','spg','bpg','tpg','pfpg','ppg']
    final_df = final_df[new_order]

    final_df.to_csv(final_csv, index=False)
    print(f"Reordered Columns successfully written to {final_csv}")


