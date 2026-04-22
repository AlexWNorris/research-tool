"""
Advanced Exploratory Data Analysis module for parsing, evaluating, and visualizing 
demographic entropy shifts and fingerprint duplications within the browser dataset.
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import entropy
from itertools import combinations

try:
    from pywaffle import Waffle
except ImportError:
    print("Warning: Please install pywaffle to generate the Waffle Chart (pip install pywaffle).")
    Waffle = None

# ==========================================
# Configuration & Setup
# ==========================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "fullData", "decrypted")
OUTPUT_DIR = os.path.join(BASE_DIR, "plots", "advanced_eda")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

sns.set_theme(style="whitegrid", context="paper")
plt.rcParams.update({'font.size': 12, 'figure.figsize': (10, 6), 'axes.titleweight': 'bold'})

# ==========================================
# Data Loading & Preprocessing
# ==========================================
def load_data(data_dir=DATA_DIR):
    """
    Load data from decrypted directory.
    
    Args:
        data_dir (str): Path to the decrypted JSON text files.
        
    Returns:
        pd.DataFrame: A DataFrame containing flattened record statistics.
    """
    records = []
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Data directory {data_dir} does not exist.")
    for filename in os.listdir(data_dir):
        if not filename.endswith(".txt"): continue
        filepath = os.path.join(data_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f.read().strip().split('\n'):
                if not line.strip(): continue
                try:
                    item = json.loads(line)
                    if 'survey_response' not in item or 'fingerprint' not in item: continue
                    flat_record = {
                        'session_id': item.get('session_id', ''),
                        'timestamp': item.get('timestamp', ''),
                        'visitorId': item['fingerprint'].get('visitorId', ''),
                    }
                    for k, v in item['survey_response'].items():
                        flat_record[f"demo_{k}"] = v
                    components = item['fingerprint'].get('components', {})
                    for comp_name, comp_data in components.items():
                        val = comp_data.get('value', None)
                        if isinstance(val, (dict, list)):
                            val = str(val)
                        flat_record[f"feat_{comp_name}"] = val
                        
                    records.append(flat_record)
                except Exception as e:
                    print(f"Error parsing record in {filename}: {e}")
    df = pd.DataFrame(records)
    print(f"Loaded {len(df)} records with {len(df.columns)} flattened columns.")
    return df

# ==========================================
# Task 1: Feature-Level Entropy Analysis
# ==========================================
def task_1_entropy(df):
    """
    Perform feature-level entropy analysis to evaluate identifying properties of footprint fields.
    
    Args:
        df (pd.DataFrame): Input dataframe containing features to evaluate.
    """
    print("\n--- Running Task 1: Feature Entropy ---")
    feature_cols = [c for c in df.columns if c.startswith('feat_')]
    entropies = {}
    for col in feature_cols:
        counts = df[col].value_counts(normalize=True).values
        entropies[col.replace('feat_', '')] = entropy(counts, base=2)
    ent_df = pd.DataFrame(list(entropies.items()), columns=['Feature', 'Entropy'])
    ent_df = ent_df.sort_values(by='Entropy', ascending=False)
    
    plt.figure(figsize=(12, 10))
    sns.barplot(x='Entropy', y='Feature', data=ent_df, hue='Feature', palette="viridis", legend=False)
    plt.title("Feature Information Value (Shannon Entropy)", fontsize=18, pad=20)
    plt.xlabel("Entropy (bits)",fontsize=16)
    plt.yticks(fontsize=16)
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "task1_feature_entropy.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved Feature Entropy Chart to: {output_path}")

# ==========================================
# Task 2: Duplicates Network Graph
# ==========================================
def task_2_network(df):
    """
    Construct a network graph to visualize exactly duplicated footprints across sessions.
    
    Args:
        df (pd.DataFrame): Data containing footprint and demographic columns.
    """
    print("\n--- Running Task 2: Duplicates Network Graph ---")
    G = nx.Graph()
    feature_cols = [c for c in df.columns if c.startswith('feat_')]
    for idx, row in df.iterrows():
        node_id = row['session_id']
        gender = row['demo_gender'] if pd.notna(row.get('demo_gender')) else 'Unknown'
        G.add_node(node_id, gender=gender)
        
    df_features = df[feature_cols]
    for u, v in combinations(df.iterrows(), 2):
        if tuple(df_features.loc[u[0]]) == tuple(df_features.loc[v[0]]):
            G.add_edge(u[1]['session_id'], v[1]['session_id'])
    
    isolated = list(nx.isolates(G))
    G.remove_nodes_from(isolated)
    if len(G.nodes) == 0:
        print("No exact duplicates found. Skipping Network Graph generation.")
        return
        
    genders = nx.get_node_attributes(G, 'gender')
    unique_genders = list(set(genders.values()))
    palette = sns.color_palette("Set2", len(unique_genders))
    color_map = {g: c for g, c in zip(unique_genders, palette)}
    node_colors = [color_map[genders[node]] for node in G.nodes()]

    plt.figure(figsize=(12, 10))
    pos = nx.spring_layout(G, k=0.7, seed=42)
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=600, edgecolors='black', linewidths=1.5, alpha=0.9)
    nx.draw_networkx_edges(G, pos, width=2.5, alpha=0.6, edge_color='gray')
    
    import matplotlib.patches as mpatches
    legend_handles = [mpatches.Patch(color=color_map[g], label=g) for g in unique_genders]
    plt.legend(handles=legend_handles, title="Demographic: Gender", loc='upper left')
    plt.title("Fingerprint Collisions (Shared Exact Footprints)")
    plt.axis("off")
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "task2_duplicates_network.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved Network Graph to: {output_path}")

# ==========================================
# Task 3: Similarity & Sankey Diagram
# ==========================================
def calculate_jaccard(row1, row2, feature_cols):
    """
    Calculate simple Jaccard similarity index.
    
    Args:
        row1 (pd.Series): First user fingerprint footprint vector.
        row2 (pd.Series): Second user fingerprint footprint vector.
        feature_cols (list): Fields to include in index matching.
        
    Returns:
        float: Jaccard similarity scalar.
    """
    matches = sum(1 for col in feature_cols if row1[col] == row2[col])
    return matches / len(feature_cols) if feature_cols else 0.0

def task_3_sankey(df):
    """
    Generate an interactive sankey plot linking Income -> Education -> Uniqueness.
    
    Args:
        df (pd.DataFrame): Base dataframe including demographics.
    """
    print("\n--- Running Task 3: Similarity & Sankey Diagram ---")
    feature_cols = [c for c in df.columns if c.startswith('feat_')]
    similarities = [calculate_jaccard(df.iloc[u], df.iloc[v], feature_cols) for u, v in combinations(df.index, 2)]
    avg_sim = np.mean(similarities) if similarities else 0
    print(f"Average pairwise Jaccard similarity across dataset: {avg_sim:.4f}")
    
    feature_cols = [c for c in df.columns if c.startswith('feat_')]
    is_duplicate = df.duplicated(subset=feature_cols, keep=False)
    df['Uniqueness'] = is_duplicate.map({True: "Duplicate", False: "Unique"})
    
    df['Income'] = df.get('demo_income', pd.Series(['Unknown']*len(df))).fillna('Unknown')
    df['Education'] = df.get('demo_education', pd.Series(['Unknown']*len(df))).fillna('Unknown')
    
    all_nodes = list(df['Income'].unique()) + list(df['Education'].unique()) + list(df['Uniqueness'].unique())
    node_indices = {key: i for i, key in enumerate(all_nodes)}
    
    source = []
    target = []
    value = []
    
    inc_edu = df.groupby(['Income', 'Education']).size().reset_index(name='count')
    for _, row in inc_edu.iterrows():
        source.append(node_indices[row['Income']])
        target.append(node_indices[row['Education']])
        value.append(row['count'])
        
    edu_uni = df.groupby(['Education', 'Uniqueness']).size().reset_index(name='count')
    for _, row in edu_uni.iterrows():
        source.append(node_indices[row['Education']])
        target.append(node_indices[row['Uniqueness']])
        value.append(row['count'])
        
    fig = go.Figure(data=[go.Sankey(
        node = dict(pad=20, thickness=30, line=dict(color="black", width=0.5), label=all_nodes, color="#3498DB"),
        link = dict(source=source, target=target, value=value, color="rgba(169, 169, 169, 0.4)")
    )])
    fig.update_layout(title_text="Flow Analysis: Demographics vs Fingerprint Uniqueness", height=700, width=1000)
    output_path = os.path.join(OUTPUT_DIR, "task3_sankey.html")
    fig.write_html(output_path)
    print(f"Saved Interactive Sankey Diagram to: {output_path}")

# ==========================================
# Task 4: Uniqueness Waffle Chart
# ==========================================
def task_4_waffle(df):
    """
    Output a waffle plot charting overall count of unique to duplicate footprints.
    
    Args:
        df (pd.DataFrame): Output demographics target dataframe.
    """
    print("\n--- Running Task 4: Uniqueness Waffle Chart ---")
    if Waffle is None:
        print("Skipped because pywaffle is not installed.")
        return
        
    feature_cols = [c for c in df.columns if c.startswith('feat_')]
    is_duplicate = df.duplicated(subset=feature_cols, keep=False)
    df['Uniqueness'] = is_duplicate.map({True: "Duplicate", False: "Unique"})
    
    counts = df['Uniqueness'].value_counts()
    unique_count = counts.get('Unique', 0)
    duplicate_count = counts.get('Duplicate', 0)
    total = unique_count + duplicate_count
    
    plt.figure(
        FigureClass=Waffle,
        rows=5,
        columns=max(1, total // 5 + (1 if total % 5 != 0 else 0)),
        values={'Unique': unique_count, 'Duplicate': duplicate_count},
        colors=("#16A085", "#E74C3C"), 
        legend={'loc': 'upper center', 'bbox_to_anchor': (0.5, -0.1), 'ncol': 2, 'fontsize': 14},
        figsize=(12, 6),
        title={'label': 'Overall Fingerprint Uniqueness Representation', 'loc': 'center', 'fontsize': 18, 'pad': 20}
    )
    output_path = os.path.join(OUTPUT_DIR, "task4_uniqueness_waffle.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved Unique/Duplicate Waffle Chart to: {output_path}")

# ==========================================
# Task 5: Demographic Distribution Charts
# ==========================================
def task_5_demographics(df):
    """
    Assemble multi-axis distribution sunburst and parallel charts.
    
    Args:
        df (pd.DataFrame): Records containing relevant demographics targets.
    """
    print("\n--- Running Task 5: Demographic Distribution Charts ---")
    demo_df = df[['demo_age', 'demo_gender', 'demo_income', 'demo_education']].fillna('Unknown').copy()
    demo_df.columns = ['Age', 'Gender', 'Income', 'Education']
    
    fig_parallel = px.parallel_categories(
        demo_df, 
        dimensions=['Age', 'Gender', 'Income', 'Education'],
        title="Demographic Overview: Parallel Categories (Alluvial Diagram)",
        labels={'Age': 'Age Group', 'Gender': 'Gender', 'Income': 'Income Bracket', 'Education': 'Education Level'}
    )
    fig_parallel.update_layout(
        margin=dict(l=60, r=60, t=60, b=40),
        font=dict(size=26),
        title_font=dict(size=24)
    )
    parallel_path = os.path.join(OUTPUT_DIR, "task5_demographics_parallel.html")
    fig_parallel.write_html(parallel_path)
    print(f"Saved Parallel Categories Diagram to: {parallel_path}")
    
    count_df = demo_df.groupby(['Age', 'Gender', 'Income', 'Education']).size().reset_index(name='Count')
    fig_sunburst = px.sunburst(
        count_df, 
        path=['Age', 'Gender', 'Income', 'Education'], 
        values='Count',
        title="Demographic Hierarchy: Sunburst Chart",
        color='Count',
        color_continuous_scale='Blues'
    )
    fig_sunburst.update_layout(
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(size=36), 
        title_font=dict(size=36)
    )
    fig_sunburst.update_traces(
        insidetextorientation='auto' 
    )
    
    sunburst_path = os.path.join(OUTPUT_DIR, "task5_demographics_sunburst.html")
    fig_sunburst.write_html(sunburst_path)
    print(f"Saved Sunburst Chart to: {sunburst_path}")


# ==========================================
# Task 6: Cumulative Uniqueness by Entropy
# ==========================================
def task_6_uniqueness_accumulation(df):
    """
    Measure accumulating percentage of uniqueness with incremental inclusion 
    of top N identifying trace components.
    
    Args:
        df (pd.DataFrame): Base dataframe of complete trace inputs.
    """
    print("\n--- Running Task 6: Cumulative Uniqueness by Entropy ---")
    feature_cols = [c for c in df.columns if c.startswith('feat_')]
    entropies = {}
    for col in feature_cols:
        counts = df[col].value_counts(normalize=True).values
        entropies[col] = entropy(counts, base=2)
    
    # Sort features by entropy descending
    sorted_features = sorted(entropies.keys(), key=lambda k: entropies[k], reverse=True)
    
    percentages = []
    user_unique_at_k = {i: None for i in range(len(df))}
    total_users = len(df)
    
    for k in range(1, len(sorted_features) + 1):
        selected_features = sorted_features[:k]
        subset_df = df[selected_features].astype(str)
        is_unique_subset = ~subset_df.duplicated(keep=False)
        percentages.append((is_unique_subset.sum() / total_users) * 100)
        
        for i, is_uniq in is_unique_subset.items():
            if is_uniq and user_unique_at_k[i] is None:
                user_unique_at_k[i] = k

    # Calculate same logic but for features excluding the top 10
    excluded_features = sorted_features[10:]
    percentages_excluded = []
    
    for k in range(1, len(excluded_features) + 1):
        selected_features = excluded_features[:k]
        subset_df = df[selected_features].astype(str)
        is_unique_subset = ~subset_df.duplicated(keep=False)
        percentages_excluded.append((is_unique_subset.sum() / total_users) * 100)
                
    # Calculate average features required for users who become uniquely identified
    required_features = [k for k in user_unique_at_k.values() if k is not None]
    if required_features:
        avg_features = np.mean(required_features)
        print(f"Average features to uniquely identify a user: {avg_features:.2f}")
    else:
        print("No users could be uniquely identified.")
        
    plt.figure(figsize=(10, 6))
    
    # Plot line 1 (All features)
    plt.plot(range(1, len(sorted_features) + 1), percentages, marker='o', linestyle='-', color='#8E44AD', linewidth=2, markersize=6, label='All Features')
    
    # Plot line 2 (Excluding top 10)
    plt.plot(range(1, len(excluded_features) + 1), percentages_excluded, marker='s', linestyle='--', color='#E74C3C', linewidth=2, markersize=6, label='Excluding Top 10 Entropy Features')
    
    plt.title("Uniquely Identified Users vs. Features Added", fontsize=16, pad=20)
    plt.xlabel("Number of Features Included (Descending by Entropy)", fontsize=14)
    plt.ylabel("Uniquely Identified Users (%)", fontsize=14)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend(fontsize=12)
    
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "task6_cumulative_uniqueness.png")
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Saved Cumulative Uniqueness Graph to: {output_path}")

# ==========================================
# Task 7: Demographic Boundary Entropy Shift Analysis
# ==========================================
def task_7_boundary_entropy(df):
    """
    Execute task 7 script detecting the demographic boundaries with the largest
    entropy shifts for the browser parameters across properties.
    
    Args:
        df (pd.DataFrame): Pre-processed data.
    """
    print("\n--- Running Task 7: Demographic Boundary Entropy Shift Analysis ---")
    
    boundaries = {
        'Age': ['<=34', '>=35'],
        'Income': ['<= 54,999', '>= 55,000'],
        'Education': ['Pre-University', 'University Level and Above'],
        'Gender': ['Female', 'Male']
    }
    
    feature_cols = [c for c in df.columns if c.startswith('feat_')]
    summary_results = []
    all_results = []
    
    for demo_name, groups in boundaries.items():
        col_name = f"demo_{demo_name.lower()}"
        if col_name not in df.columns:
            continue
            
        for i in range(len(groups) - 1):
            g1, g2 = groups[i], groups[i+1]
            
            df_g1 = df[df[col_name] == g1]
            df_g2 = df[df[col_name] == g2]
            
            if len(df_g1) == 0 or len(df_g2) == 0:
                continue
                
            boundary_max_diff = -1
            boundary_max_feat = None
            boundary_g1_ent = 0
            boundary_g2_ent = 0
            
            for feat in feature_cols:
                # Calculate entropy for group 1
                counts1 = df_g1[feat].value_counts(normalize=True).values
                ent1 = entropy(counts1, base=2)
                
                # Calculate entropy for group 2
                counts2 = df_g2[feat].value_counts(normalize=True).values
                ent2 = entropy(counts2, base=2)
                
                diff = abs(ent1 - ent2)
                clean_feat = feat.replace('feat_', '')
                
                all_results.append({
                    "Demographic": demo_name,
                    "Boundary": f"{g1} -> {g2}",
                    "Attribute": clean_feat,
                    "Group 1 Entropy": round(ent1, 4),
                    "Group 2 Entropy": round(ent2, 4),
                    "Absolute Diff": round(diff, 4)
                })
                
                if diff > boundary_max_diff:
                    boundary_max_diff = diff
                    boundary_max_feat = clean_feat
                    boundary_g1_ent = ent1
                    boundary_g2_ent = ent2
            
            if boundary_max_feat is not None:
                summary_results.append({
                    "Demographic": demo_name,
                    "Boundary": f"{g1} -> {g2}",
                    "Top Attribute": boundary_max_feat,
                    "Group 1 Entropy": round(boundary_g1_ent, 4),
                    "Group 2 Entropy": round(boundary_g2_ent, 4),
                    "Absolute Diff": round(boundary_max_diff, 4)
                })

    if summary_results:
        sum_df = pd.DataFrame(summary_results)
        print("\nTop Browser Attribute Shifts Across Demographic Boundaries:")
        print("=" * 110)
        print(sum_df.to_string(index=False, justify="center"))
        print("=" * 110)
        
        all_df = pd.DataFrame(all_results)
        csv_path = os.path.join(OUTPUT_DIR, "task7_boundary_shifts.csv")
        all_df.to_csv(csv_path, index=False)
        print(f"Saved comprehensive boundary shifts analysis to: {csv_path}")
    else:
        print("No valid boundaries found or not enough data to compare adjacent boundaries.")

# ==========================================
# Main Execution Trigger
# ==========================================
if __name__ == "__main__":
    print("Initializing Exploratory Data Analysis Pipeline...")
    try:
        df_records = load_data()
        
        if len(df_records) > 0:
            task_1_entropy(df_records)
            task_2_network(df_records)
            task_3_sankey(df_records)
            task_4_waffle(df_records)
            task_5_demographics(df_records)
            task_6_uniqueness_accumulation(df_records)
            task_7_boundary_entropy(df_records)
            print("\n*** ALL EDA TASKS COMPLETED SUCCESSFULLY ***")
        else:
            print("No records loaded. Terminating script.")
    except Exception as e:
        print(f"Fatal error during execution: {e}")
