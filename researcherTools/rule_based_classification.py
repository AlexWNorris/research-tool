"""
Module to formulate decision-tree classifiers mapping footprint traces to 
demographic outcomes, effectively generating rule-based prediction vectors.
"""
import os
import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import matplotlib.pyplot as plt
import advanced_eda
from agglomerated_analysis import map_age, map_income, map_education, map_gender

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLOTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "plots"))
AGGLOMERATED_DIR = os.path.join(PLOTS_DIR, "agglomerated_analysis")
SHIFTS_CSV_PATH = os.path.join(AGGLOMERATED_DIR, "boundary_shifts.csv")

def main():
    """
    Execute the evaluation pipeline loading past entropy maps and fitting 
    decision trees out of the most distinct attributes. Output final accuracy graphs.
    """
    print("===============================================")
    print("Rule-Based Classification using Entropy Shifts")
    print("===============================================")

    # 1. Load the task 7 boundary shifts CSV to find the top 5 attributes for each demographic boundary.
    if not os.path.exists(SHIFTS_CSV_PATH):
        print(f"Error: {SHIFTS_CSV_PATH} not found. Please run agglomerated_analysis.py first.")
        return
        
    shifts_df = pd.read_csv(SHIFTS_CSV_PATH)
    
    # 2. Extract top 5 features per demographic
    # The dataframe has columns: Demographic, Boundary, Attribute, Group 1 Entropy, Group 2 Entropy, Absolute Diff
    top_features_per_demo = {}
    for demo in shifts_df['Demographic'].unique():
        demo_df = shifts_df[shifts_df['Demographic'] == demo]
        # Sort by Absolute Diff descending, grab top 5 unique attributes
        top_attrs = demo_df.sort_values(by='Absolute Diff', ascending=False)['Attribute'].unique()[:5]
        top_features_per_demo[demo] = list(top_attrs)
        
    print("\n[ Top 5 Attributes Selected from Entropy Differences ]")
    for demo, attrs in top_features_per_demo.items():
        print(f"{demo}: {', '.join(attrs)}")

    # 3. Load the raw dataset
    print("\nLoading dataset via advanced_eda...")
    data_dir = os.path.abspath(os.path.join(BASE_DIR, "..", "fullData", "decrypted"))
    df = advanced_eda.load_data(data_dir=data_dir)
    
    if len(df) == 0:
        print("No records loaded. Terminating script.")
        return

    # Apply the same demographic mapping as agglomerated_analysis.py to ensure the classes match
    df['demo_age'] = df.get('demo_age', pd.Series(['Unknown']*len(df))).apply(map_age)
    df['demo_income'] = df.get('demo_income', pd.Series(['Unknown']*len(df))).apply(map_income)
    df['demo_education'] = df.get('demo_education', pd.Series(['Unknown']*len(df))).apply(map_education)
    df['demo_gender'] = df.get('demo_gender', pd.Series(['Unknown']*len(df))).apply(map_gender)

    mapping_targets = {
        'Age': 'demo_age',
        'Income': 'demo_income',
        'Education': 'demo_education',
        'Gender': 'demo_gender'
    }

    # 4. Filter and Train Decision Trees
    print("\n[ Training Rules-Based Decision Trees ]")
    accuracies = {}
    for demo, target_col in mapping_targets.items():
        if demo not in top_features_per_demo:
            continue
            
        print(f"\n--- Model for Demographic: {demo} ---")
        features_to_use = top_features_per_demo[demo]
        feature_cols = [f"feat_{attr}" for attr in features_to_use]
        # Filter out rows where the target value is 'Unknown', 'Prefer not to say', 'Other', or missing
        excluded_values = ['Prefer not to say', 'Other']
        valid_df = df[df[target_col].notna() & (~df[target_col].isin(excluded_values))].copy()
        
        if len(valid_df) < 5:
            print(f"Not enough valid records to train model for {demo}.")
            continue

        # Isolate X and y
        X = valid_df[feature_cols].copy()
        y = valid_df[target_col].copy()
        
        # Convert all features to string, then encode using LabelEncoder because Decision Trees require numeric input
        # Note: We keep track of encoders so we could (theoretically) decode rules back to strings if we built a custom rule parser,
        # but sklearn's export_text will output inequalities representing integer categories.
        encoders = {}
        for col in feature_cols:
            X[col] = X[col].astype(str)
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col])
            encoders[col] = le
            
        # Splitting data (using stratification to ensure the 70/30 split keeps the right ratio of classes in the 22 test records)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

        # Train a Decision Tree Classifier
        # Using min_samples_leaf=3 prevents the tree from creating arbitrary rules for just 1 or 2 people in the 52-record training set.
        clf = DecisionTreeClassifier(max_depth=3, min_samples_leaf=3, random_state=42)
        clf.fit(X_train, y_train)
        
        # Predict Training and Test to see how badly it overfits
        train_acc = accuracy_score(y_train, clf.predict(X_train))
        test_acc = accuracy_score(y_test, clf.predict(X_test))
        accuracies[demo] = test_acc
        
        # Calculate theoretical baseline accuracies
        test_proportions = y_test.value_counts(normalize=True)
        majority_baseline = test_proportions.max()
        weighted_random = (test_proportions ** 2).sum()
        
        print(f"Accuracy on Training Set (n={len(X_train)}): {train_acc:.2%}")
        print(f"Accuracy on 30% Test Set (n={len(X_test)}): {test_acc:.2%}")
        print(f"  -> Theoretical Baseline (Majority Class Guess): {majority_baseline:.2%}")
        print(f"  -> Theoretical Baseline (Weighted Random Guess): {weighted_random:.2%}")
        
        # Export the textual rules tree (Inequalities output)
        rules = export_text(clf, feature_names=feature_cols)
        print("\nDecision Rules (Inequalities based on Encoded Categorical values):")
        print(rules)
        print("Note: Feature values shown in rules are numeric categories from LabelEncoder.")
        
        # Optionally print the class mappings to make the inequalities understandable
        print("Feature Encodings Reference (class index corresponds to value in inequality):")
        for col in feature_cols:
            classes = encoders[col].classes_
            formatted_classes = []
            for i, c in enumerate(list(classes)[:5]):
                c_str = str(c)
                if len(c_str) > 40:
                    c_str = c_str[:37] + "..."
                formatted_classes.append(f"{i}: '{c_str}'")
            
            suffix = ", ..." if len(classes) > 5 else ""
            print(f"  {col}: {{{', '.join(formatted_classes)}}}{suffix}")

    # 5. Plot the classification accuracies
    if accuracies:
        plt.figure(figsize=(10, 6))
        # Use the same green hex (#16A085) featured in advanced_eda's waffle chart/theming
        plt.bar(accuracies.keys(), [acc * 100 for acc in accuracies.values()], color="#16A085", edgecolor="black", alpha=0.9)
        
        # Add labels above the bars
        for i, (demo, acc) in enumerate(accuracies.items()):
            plt.text(i, (acc * 100) + 1, f'{acc * 100:.1f}%', ha='center', va='bottom', fontweight='bold', fontsize=12)

        plt.title("Rule-Based Classifier Accuracy by Demographic", fontsize=16, pad=20, fontweight='bold')
        plt.ylabel("Test Set Accuracy (%)", fontsize=14, fontweight='bold')
        plt.xlabel("Demographic", fontsize=14, fontweight='bold')
        plt.ylim(0, 105) # Allow room for labels
        plt.xticks(fontsize=12)
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        chart_path = os.path.join(AGGLOMERATED_DIR, "rule_based_accuracy.png")
        plt.savefig(chart_path, dpi=300)
        plt.close()
        print(f"\n[+] Saved Accuracy Bar Chart to: {chart_path}")

if __name__ == "__main__":
    main()
