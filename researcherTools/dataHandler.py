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
        self._calculate_risks()

    def _calculate_risks(self):
        """Calculates the risk value (bits of info) for each user based on fingerprint features."""
        if not self.records:
            return
            
        # Step 1: Collect features across all records
        feature_counts = {}
        total_records = len(self.records)
        
        for r in self.records:
            components = r['fingerprint'].get('components', {})
            for comp_name, comp_data in components.items():
                val = str(comp_data.get('value', 'missing'))
                if comp_name not in feature_counts:
                    feature_counts[comp_name] = {}
                feature_counts[comp_name][val] = feature_counts[comp_name].get(val, 0) + 1
        
        # Step 2: Calculate bits of information (risk) for each user
        for r in self.records:
            risk_value = 0.0
            components = r['fingerprint'].get('components', {})
            for comp_name, comp_data in components.items():
                val = str(comp_data.get('value', 'missing'))
                count = feature_counts[comp_name].get(val, 1)
                prob = count / total_records
                if prob > 0:
                    risk_value -= np.log2(prob)
            r['risk_value'] = risk_value

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
        colors = ['#DE591C', '#00c896']

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
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

    def get_demographic_risk(self, demographic_key):
        """
        Calculates the average risk value (bits of info) for a specific demographic.
        Args:
            demographic_key (str): e.g., 'age', 'education', 'gender', 'income'
        Returns:
            dict: { 'group_name': {'average_risk': float, 'total_count': int} }
        """
        if not self.records or 'risk_value' not in self.records[0]:
            self._calculate_risks()
            
        groups = {}
        for r in self.records:
            sv = r.get('survey_response', {})
            val = sv.get(demographic_key, "Unknown")
            if val is None:
                val = "Unknown"
            
            if val not in groups:
                groups[val] = []
            
            groups[val].append(r.get('risk_value', 0.0))

        results = {}
        for group_name, risks in groups.items():
            results[group_name] = {
                'average_risk': np.mean(risks) if risks else 0.0,
                'total_count': len(risks)
            }
        
        return results

    def plot_demographic_risk(self, demographic_key, save_path=None):
        """Plots a bar chart of average risk (bits) by demographic group."""
        stats = self.get_demographic_risk(demographic_key)
        if not stats:
            print(f"No data to plot for demographic risk: {demographic_key}")
            return

        # Sort by average risk descending
        sorted_stats = dict(sorted(stats.items(), key=lambda item: item[1]['average_risk'], reverse=True))

        groups = list(sorted_stats.keys())
        risks = [s['average_risk'] for s in sorted_stats.values()]
        ns = [s['total_count'] for s in sorted_stats.values()]

        fig, ax = plt.subplots(figsize=(10, 6))
        
        x_pos = np.arange(len(groups))
        bars = ax.bar(x_pos, risks, color='#00c896', edgecolor='black')

        for bar, risk, n in zip(bars, risks, ns):
            height = bar.get_height()
            ax.annotate(f'{risk:.1f} bits\n(n={n})',
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),  # 3 points vertical offset
                        textcoords="offset points",
                        ha='center', va='bottom', fontsize=10)

        ax.set_ylabel('Average Identifying Information (Bits)', fontsize=12)
        ax.set_title(f'Average Fingerprint Risk by {demographic_key.capitalize()} Demographic', fontsize=14, pad=25)
        ax.set_xticks(x_pos)
        
        # Format labels - split long labels if needed
        formatted_groups = [g if len(g) < 20 else g[:17] + '...' for g in groups]
        ax.set_xticklabels(formatted_groups, rotation=45, ha='right')

        # Limit y-axis to a slightly higher top for annotations to fit
        ax.set_ylim(0, max(risks) + max(risks)*0.15 if risks else 100)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            print(f"Saved {demographic_key} risk plot to {save_path}")
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

    def plot_risk_subplots(self, save_path=None):
        """Plots a 2x2 multi-axis subplot matrix containing demographic risk charts."""
        demographics = ['gender', 'income', 'age', 'education']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        axes = axes.flatten()
        
        for i, demo_key in enumerate(demographics):
            ax = axes[i]
            stats = self.get_demographic_risk(demo_key)
            if not stats:
                ax.set_title(f"No risk data for {demo_key}")
                continue
                
            sorted_stats = dict(sorted(stats.items(), key=lambda item: item[1]['average_risk'], reverse=True))
            groups = list(sorted_stats.keys())
            risks = [s['average_risk'] for s in sorted_stats.values()]
            ns = [s['total_count'] for s in sorted_stats.values()]
            
            x_pos = np.arange(len(groups))
            bars = ax.bar(x_pos, risks, color='#00c896', edgecolor='black')
            
            for bar, risk, n in zip(bars, risks, ns):
                height = bar.get_height()
                ax.annotate(f'{risk:.1f}\n(n={n})',
                            xy=(bar.get_x() + bar.get_width() / 2, height),
                            xytext=(0, 3), 
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=10)
                            
            ax.set_ylabel('Avg Information (Bits)', fontsize=11)
            ax.set_title(f'Risk by {demo_key.capitalize()}', fontsize=14, pad=15)
            ax.set_xticks(x_pos)
            
            formatted_groups = [g if len(g) < 20 else g[:17] + '...' for g in groups]
            ax.set_xticklabels(formatted_groups, rotation=45 if len(groups) > 2 else 0, ha='right' if len(groups) > 2 else 'center')
            ax.set_ylim(0, max(risks) + max(risks)*0.15 if risks else 100)

        plt.suptitle("Average Fingerprint Risk Across Demographics", fontsize=18, y=0.96)
        plt.tight_layout(rect=[0, 0, 1, 0.94])

        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            print(f"Saved combined risk subplots to {save_path}")
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
            self.plot_demographic_risk(key, save_path=os.path.join(output_dir, f'{key}_risk.png'))
            
        self.plot_demographic_heatmap(save_path=os.path.join(output_dir, 'demographics_heatmap.png'))
        self.plot_risk_subplots(save_path=os.path.join(output_dir, 'combined_risk_subplots.png'))


