import json
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

class PilotDataHandler:
    def __init__(self, data_dir="pilotData/decrypted"):
        """Initialize PilotDataHandler and load valid survey Data."""
        self.data_dir = data_dir
        self.records = []
        self._load_data()

    def _load_data(self):
        """Loads JSON files from the decrypted directory."""
        if not os.path.exists(self.data_dir):
            print(f"Directory {self.data_dir} not found.")
            return

        for filename in os.listdir(self.data_dir):
            if not filename.endswith(".txt"):
                continue
            
            filepath = os.path.join(self.data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Some files might have multiple JSON objects separated by newlines
                    # For pilotData/decrypted, it seems each txt file is one JSON object.
                    for line in content.strip().split('\n'):
                        if not line.strip(): continue
                        record = json.loads(line)
                        if 'survey_response' in record and 'fingerprint' in record:
                            # only keep valid records
                            visitor_id = record['fingerprint'].get('visitorId')
                            if visitor_id:
                                self.records.append(record)
            except Exception as e:
                print(f"Error reading {filename}: {e}")
        
        print(f"Loaded {len(self.records)} valid records.")

    def get_overall_uniqueness(self):
        """
        Calculates the proportion of unique fingerprints in the whole dataset.
        Returns:
            dict: { 'unique_count': int, 'total_count': int, 'ratio': float }
        """
        total_count = len(self.records)
        if total_count == 0:
            return {'unique_count': 0, 'total_count': 0, 'ratio': 0.0}

        unique_fingerprints = set(r['fingerprint']['visitorId'] for r in self.records)
        unique_count = len(unique_fingerprints)
        ratio = unique_count / total_count

        return {
            'unique_count': unique_count,
            'total_count': total_count,
            'ratio': ratio
        }

    def get_demographic_uniqueness(self, demographic_key):
        """
        Calculates the proportion of unique fingerprints within a specific demographic.
        Args:
            demographic_key (str): e.g., 'age', 'education', 'gender', 'income'
        Returns:
            dict: { 'group_name': {'unique_count': int, 'total_count': int, 'ratio': float} }
        """
        groups = {}
        for r in self.records:
            sv = r.get('survey_response', {})
            val = sv.get(demographic_key)
            if val is None:
                val = "Unknown"
            
            if val not in groups:
                groups[val] = []
            
            groups[val].append(r['fingerprint']['visitorId'])

        results = {}
        for group_name, v_ids in groups.items():
            total_count = len(v_ids)
            unique_count = len(set(v_ids))
            ratio = unique_count / total_count if total_count > 0 else 0.0
            results[group_name] = {
                'unique_count': unique_count,
                'total_count': total_count,
                'ratio': ratio
            }
        
        return results

    def plot_overall_uniqueness(self, save_path=None):
        """Plots a pie chart of overall unique vs duplicate fingerprints."""
        stats = self.get_overall_uniqueness()
        if stats['total_count'] == 0:
            print("No data to plot for overall uniqueness.")
            return

        unique_count = stats['unique_count']
        duplicates = stats['total_count'] - unique_count

        labels = ['Unique', 'Duplicates']
        sizes = [unique_count, duplicates]
        colors = ['#4CAF50', '#FFC107']
        explode = (0.1, 0)

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%',
               shadow=True, startangle=140)
        ax.axis('equal')
        
        plt.title(f"Overall Fingerprint Uniqueness (n={stats['total_count']})", fontsize=14, pad=20)
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            print(f"Saved overall uniqueness plot to {save_path}")
        else:
            plt.show()
        
        plt.close()

    def plot_demographic_uniqueness(self, demographic_key, save_path=None):
        """Plots a bar chart of uniqueness percentages by demographic group."""
        stats = self.get_demographic_uniqueness(demographic_key)
        if not stats:
            print(f"No data to plot for demographic: {demographic_key}")
            return

        # Sort by ratio descending
        sorted_stats = dict(sorted(stats.items(), key=lambda item: item[1]['ratio'], reverse=True))

        groups = list(sorted_stats.keys())
        ratios = [s['ratio'] * 100 for s in sorted_stats.values()]  # Convert to percentage
        ns = [s['total_count'] for s in sorted_stats.values()]

        fig, ax = plt.subplots(figsize=(10, 6))
        
        x_pos = np.arange(len(groups))
        bars = ax.bar(x_pos, ratios, color='#2196F3', edgecolor='black')

        # Add percentage labels and 'n' count on top of bars
        for bar, ratio, n in zip(bars, ratios, ns):
            height = bar.get_height()
            ax.annotate(f'{ratio:.1f}%\n(n={n})',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10)

        ax.set_ylabel('Unique Fingerprints (%)', fontsize=12)
        ax.set_title(f'Fingerprint Uniqueness by {demographic_key.capitalize()} Demographic', fontsize=14, pad=25)
        ax.set_xticks(x_pos)
        
        # Format labels - split long labels if needed
        formatted_groups = [g if len(g) < 20 else g[:17] + '...' for g in groups]
        ax.set_xticklabels(formatted_groups, rotation=45, ha='right')

        # Limit y-axis to a slightly higher top for annotations to fit
        ax.set_ylim(0, max(ratios) + 15 if ratios else 100)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            print(f"Saved {demographic_key} uniqueness plot to {save_path}")
        else:
            plt.show()
            
        plt.close()

    def plot_demographic_heatmap(self, save_path=None):
        """Plots a multi-index heatmap for age, gender, income, and education."""
        data = []
        for r in self.records:
            sv = r.get('survey_response', {})
            vid = r['fingerprint']['visitorId']
            
            data.append({
                'age': sv.get('age', 'Unknown'),
                'gender': sv.get('gender', 'Unknown'),
                'income': sv.get('income', 'Unknown'),
                'education': sv.get('education', 'Unknown'),
                'vid': vid
            })
            
        if not data:
            print("No data to plot heatmap.")
            return
            
        df = pd.DataFrame(data)
        
        # Calculate unique proportion and count for each combination
        grouped = df.groupby(['education', 'income', 'age', 'gender']).agg(
            total_count=('vid', 'count'),
            unique_count=('vid', 'nunique')
        ).reset_index()
        
        # Calculate ratio
        grouped['ratio'] = grouped['unique_count'] / grouped['total_count']
        
        # Pivot the data for the heatmap
        pivot_ratio = grouped.pivot_table(
            index=['education', 'income'], 
            columns=['age', 'gender'], 
            values='ratio', 
            fill_value=np.nan
        )
        
        pivot_count = grouped.pivot_table(
            index=['education', 'income'], 
            columns=['age', 'gender'], 
            values='total_count', 
            fill_value=0
        )
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        sns.heatmap(
            pivot_ratio, 
            annot=pivot_count, 
            fmt=".0f", 
            cmap="YlGnBu", 
            ax=ax,
            cbar_kws={'label': 'Proportion of Unique Fingerprints'},
            linewidths=.5,
            mask=pivot_count == 0
        )
        
        ax.set_title("Fingerprint Uniqueness by Demographics\n(Color: Uniqueness Proportion, Number: Data Points)", fontsize=16, pad=20)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            print(f"Saved demographic heatmap to {save_path}")
        else:
            plt.show()
            
        plt.close()

    def plot_all_demographics(self, output_dir="plots"):
        """Generates plots for overall uniqueness and all key demographics."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        self.plot_overall_uniqueness(save_path=os.path.join(output_dir, 'overall_uniqueness.png'))
        
        demographic_keys = ['age', 'education', 'gender', 'income']
        for key in demographic_keys:
            self.plot_demographic_uniqueness(key, save_path=os.path.join(output_dir, f'{key}_uniqueness.png'))
            
        self.plot_demographic_heatmap(save_path=os.path.join(output_dir, 'demographics_heatmap.png'))


