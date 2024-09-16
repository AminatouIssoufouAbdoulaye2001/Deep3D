import os
import itertools
import argparse
import numpy as np
import glob
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns  # Add this import

parser = argparse.ArgumentParser(description = 'Train or test neural net')
parser.add_argument('--test', dest = 'test', action = 'store_true', default = False)
parser.add_argument('--episodes', type=int, default=200, help=' Nb itérations ')

args = parser.parse_args()

results = {}

# Define the different values for each hyperparameter
learning_rates = [0.01, 0.001]
batch_size = [2, 4]
epsilon_decays = [0.8, 0.995]

# Create all combinations of hyperparameters
combinations = list(itertools.product(learning_rates, batch_size, epsilon_decays))

for lr, b, ed in combinations:
    if args.test:
        command = f"python3 main_vf.py --test --learning_rate {lr} --batch_size {b} --epsilon_decay {ed} --episodes {args.episodes}"
    else:
        command = f"python3 main_vf.py --train --learning_rate {lr} --batch_size {b} --epsilon_decay {ed} --episodes {args.episodes}"
    os.system(command)


# Load the .npy files
for lr in learning_rates:
    for b in batch_size:
        for ed in epsilon_decays:
            if args.test:
                prefix = f"save/test_lr{lr}_b{b}_ed{ed}"
            else:
                prefix = f"save/lr{lr}_b{b}_ed{ed}"

            scores = np.load(f"{prefix}_scores.npy")
            times = np.load(f"{prefix}_times.npy")
            avg_score = np.max(scores)
            total_time = np.sum(times) / 100
            results[prefix] = {'scores': scores, 'times': times, 'avg_score': avg_score, 'total_time': total_time}

if args.test:
    pathTimes = f'save/test_time_algos.png'
    pathRewards = f'save/test_reward_algos.png'
    pathCSV = 'save/test_model_comparison_summary.csv'
else :
    pathTimes = f'save/train_time_algos.png'
    pathRewards = f'save/train_reward_algos.png'
    pathCSV = 'save/train_model_comparison_summary.csv'
    
# Plot comparison of scores
plt.figure(figsize=(10, 6))
for key, value in results.items():
    key = os.path.basename(key)
    plt.plot(value['scores'], label=f"Model {key}")
plt.xlabel('Episodes')
plt.ylabel('Score')
plt.title('Comparison of Scores Across Models')
plt.legend()
plt.savefig(pathRewards)

# Plot comparison of times
plt.figure(figsize=(10, 6))
for key, value in results.items():
    key = os.path.basename(key)
    plt.plot(value['times'], label=f"Model {key}")
plt.xlabel('Episodes')
plt.ylabel('Time (seconds)')
plt.title('Comparison of Training Times Across Models')
plt.legend()
plt.savefig(pathTimes)

# Create a DataFrame to summarize the average scores and total times
summary_table = [] #pd.DataFrame(columns=['Model', 'Average Score', 'Total Time'])
for key, value in results.items():
    summary_table.append({
        'Model': key,
        'Average Score': value['avg_score'],
        'Total Time': value['total_time']})#, ignore_index=True)

# Print the summary table
summary_table = pd.DataFrame(summary_table)
print(summary_table)

# Save the summary table as a CSV file (optional)
summary_table.to_csv(pathCSV, index=False)
# Prepare data for bar plot
# Convert summary_table DataFrame to a format suitable for seaborn barplot
summary_table['Model'] = summary_table['Model'].apply(lambda x: x.replace('_', ' ').replace('save/', ''))
summary_table_sorted = summary_table.sort_values(by='Average Score', ascending=False)  # Sort by Average Score

# Plot comparison of average scores using a bar plot
plt.figure(figsize=(12, 8))
sns.barplot(x='Model', y='Average Score', data=summary_table_sorted, palette='viridis')
plt.title('Comparison of Average Scores Across Models')
plt.xlabel('Model')
plt.ylabel('Average Score')
plt.xticks(rotation=45, ha='right')  # Rotate labels for better readability
plt.ylim(0, max(summary_table_sorted['Average Score']) * 1.1)  # Extend y-axis a bit for clarity
plt.tight_layout()
plt.savefig(pathRewards)

# Similarly, you can plot total times
summary_table_sorted = summary_table.sort_values(by='Total Time', ascending=True)  # Sort by Total Time

plt.figure(figsize=(12, 8))
sns.barplot(x='Model', y='Total Time', data=summary_table_sorted, palette='viridis')
plt.title('Comparison of Total Training Times Across Models')
plt.xlabel('Model')
plt.ylabel('Total Time (seconds)')
plt.xticks(rotation=45, ha='right')  # Rotate labels for better readability
plt.ylim(0, max(summary_table_sorted['Total Time']) * 1.1)  # Extend y-axis a bit for clarity
plt.tight_layout()
plt.savefig(pathTimes)