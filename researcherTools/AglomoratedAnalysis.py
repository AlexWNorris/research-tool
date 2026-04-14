import os
import pandas as pd

# Fix plotting issues with imports by moving import to top and forcing backend if needed
import matplotlib
matplotlib.use('Agg') # Run headless to prevent GUI errors over CLI execution

from dataHandler import PilotDataHandler
import advanced_eda 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "fullData", "decrypted"))
OUTPUT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "plots", "aglomorated_analysis"))

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# --- Mapping Functions ---
def map_age(age):
    if pd.isna(age) or age == 'Unknown': return 'Unknown'
    if age == '18-24': return '<=24'
    return '>24'

def map_income(income):
    if pd.isna(income) or income == 'Unknown': return 'Unknown'
    low = ['Less than £15,000', '15,000 - £24,999', '£15,000 - £24,999', '£25,000 - £34,999', '£35,000 - £44,999', '£45,000 - £54,999']
    if income in low: return '<=£55,000'
    return '>£55,000'

def map_education(education):
    if pd.isna(education) or education == 'Unknown': return 'Unknown'
    uni = ["Bachelor's Degree", "Postgraduate Degree", "Higher Education"]
    if education in uni: return 'University level and above'
    return 'Pre-university qualifications'

def map_gender(gender):
    if pd.isna(gender) or gender == 'Unknown': return 'Unknown'
    if gender in ['Male', 'Female']: return gender
    return 'Ignore'

def run_aglomorated_analysis():
    print("====================================")
    print("Full ANALYSIS SCRIPT initialized")
    print("====================================")
    
    # --- 1. Run DataHandler Analysis ---
    print("\n[1/2] Running DataHandler Risk & Uniqueness Analysis with conglomerated groups...")
    handler = PilotDataHandler(data_dir=DATA_DIR)
    
    # Filter out 'Ignore' genders and apply mappings to records
    filtered_records = []
    for r in handler.records:
        sv = r.get('survey_response', {})
        gender = map_gender(sv.get('gender', 'Unknown'))
        if gender == 'Ignore':
            continue
        
        sv['gender'] = gender
        sv['age'] = map_age(sv.get('age', 'Unknown'))
        sv['income'] = map_income(sv.get('income', 'Unknown'))
        sv['education'] = map_education(sv.get('education', 'Unknown'))
        
        r['survey_response'] = sv
        filtered_records.append(r)
    
    handler.records = filtered_records
    print(f"Filtered invalid genders down to {len(handler.records)} records. Re-calculating informational risks.")
    
    # Recalculate risks with the aggregated dataset probabilities
    handler._calculate_risks()
    
    # Generate charts and output to new directory
    handler.plot_all_demographics(output_dir=OUTPUT_DIR)
    print(f"DataHandler graphical outputs saved to {OUTPUT_DIR}")
    
    # --- 2. Run Advanced EDA Analysis ---
    print("\n[2/2] Running Advanced EDA tasks with conglomerated groups...")
    
    # Override the default advanced_eda output directory
    advanced_eda.OUTPUT_DIR = OUTPUT_DIR 
    
    df = advanced_eda.load_data(DATA_DIR)
    
    # Safely map demographics back to the dataframe (advanced_eda expects demo_ columns)
    df['demo_age'] = df.get('demo_age', pd.Series(['Unknown']*len(df))).apply(map_age)
    df['demo_income'] = df.get('demo_income', pd.Series(['Unknown']*len(df))).apply(map_income)
    df['demo_education'] = df.get('demo_education', pd.Series(['Unknown']*len(df))).apply(map_education)
    df['demo_gender'] = df.get('demo_gender', pd.Series(['Unknown']*len(df))).apply(map_gender)
    
    # Drop rows where 'Ignore' was set for gender
    df = df[df['demo_gender'] != 'Ignore'].reset_index(drop=True)
    
    if len(df) > 0:
        advanced_eda.task_1_entropy(df)
        advanced_eda.task_2_network(df)
        advanced_eda.task_3_sankey(df)
        advanced_eda.task_4_waffle(df)
        advanced_eda.task_5_demographics(df)
        advanced_eda.task_6_uniqueness_accumulation(df)
        print("\n*** ALL AGLOMORATED EDA TASKS COMPLETED SUCCESSFULLY ***")
    else:
        print("No records left after filtering. Terminating Advance EDA.")

    print("\n--- 3. Statistical Significance Testing (Mann-Whitney U) ---")
    
    from scipy.stats import mannwhitneyu
    import numpy as np
    
    demographics_to_test = {
        'Gender': ('Female', 'Male'),
        'Age': ('<=24', '>24'),
        'Income': ('<=£55,000', '>£55,000'),
        'Education': ('University level and above', 'Pre-university qualifications')
    }
    
    results_data = []
    
    for demo_name, (group1_name, group2_name) in demographics_to_test.items():
        g1_risks = []
        g2_risks = []
        
        for r in handler.records:
            sv = r.get('survey_response', {})
            val = sv.get(demo_name.lower())
            risk = r.get('risk_value', 0.0)
            
            if val == group1_name:
                g1_risks.append(risk)
            elif val == group2_name:
                g2_risks.append(risk)
                
        if len(g1_risks) > 0 and len(g2_risks) > 0:
            stat, p = mannwhitneyu(g1_risks, g2_risks, alternative='two-sided')
            sig = "Statistically Significant" if p < 0.05 else "Not significant"
            
            results_data.append({
                "Demographic variable": demo_name,
                "n(group 1 / group 2)": f"{len(g1_risks)}/{len(g2_risks)}",
                "Mdn(Group 1)": f"{np.median(g1_risks):.2f}",
                "Mdn(Group 2)": f"{np.median(g2_risks):.2f}",
                "U": f"{stat:.1f}",
                "p": f"{p:.4f}",
                "Result": sig
            })
        else:
            print(f"[{demo_name}] Not enough data to compare {group1_name} vs {group2_name} (n1={len(g1_risks)}, n2={len(g2_risks)}).")

    if results_data:
        stats_df = pd.DataFrame(results_data)
        print("\nMann-Whitney U Test Results Console Table:")
        print("="*100)
        print(stats_df.to_string(index=False, justify="center"))
        print("="*100)
        
        csv_path = os.path.join(OUTPUT_DIR, "mann_whitney_results.csv")
        stats_df.to_csv(csv_path, index=False)
        print(f"\nSaved statistical test results table to: {csv_path}")

if __name__ == "__main__":
    run_aglomorated_analysis()
