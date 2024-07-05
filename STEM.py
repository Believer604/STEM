# -*- coding: utf-8 -*-
"""STEM.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1-C7U_HVI5gj37bmvnunaWXLjOkzbPBoC
"""
"Install the required libraries and packages"

!pip install catboost
!pip install rdkit
!pip install lightgbm
!pip install shap

import sys
import shap
import urllib.request
from collections import defaultdict
import torch
import os
import numpy as np
import pandas as pd
import matplotlib as plt
import networkx as nx
from tqdm.notebook import tqdm
from sklearn.metrics import roc_auc_score,roc_curve, precision_recall_curve, accuracy_score, average_precision_score, precision_score, recall_score, f1_score, average_precision_score
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
from rdkit.Chem.Draw import IPythonConsole
from catboost import CatBoostClassifier
from joblib import dump, load
import pickle
from sklearn.preprocessing import MinMaxScaler
import matplotlib as plt
from matplotlib import pyplot
from collections import Counter
from sklearn.ensemble import AdaBoostClassifier,StackingClassifier,RandomForestClassifier
from sklearn.linear_model import Lasso, LogisticRegression
from sklearn.svm import SVC
from sklearn.ensemble import ExtraTreesRegressor, ExtraTreesClassifier
import sklearn
import statistics
import lightgbm as lgb
from sklearn.neural_network import MLPClassifier
import numpy as np
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import f1_score
from sklearn.metrics import auc
from sklearn.model_selection import cross_val_score,StratifiedKFold, KFold,train_test_split,RepeatedStratifiedKFold

!pip install patool
import patoolib
patoolib.extract_archive('H.zip', outdir="/content")
patoolib.extract_archive('T.zip', outdir="/content")

def load_data2(): # Iterate over all files in the folder
    folder_path = 'T'
    truncate = 'T/'
    file_pattern = "*.csv"
    meta_data = pd.read_csv('H/Metadata.csv')
    #meta_data = meta_data.drop(['ID'],axis = 1)
    data_frames = {}  # A dictionary to store DataFrames
    #selected_files = ['rdkit.csv', 'KlekotaRoth.csv', 'CDKextended.csv', 'maccs.csv']
    #selected_files = ['2d3d.csv', 'rdkit.csv', 'KlekotaRoth.csv', 'CDKextended.csv', 'maccs.csv']
    selected_files = ['rd-kit.csv', 'klekota-Roth.csv', 'CDK-Extended.csv', '1D and 2D Desc.csv','3D desc.csv']
    for file_name in os.listdir(folder_path):
        if file_name in selected_files:
            file_path = os.path.join(folder_path, file_name)
            data_frames[file_name] = pd.read_csv(file_path).fillna(0)
    print(data_frames)
    common_col = 'SMILES'

    # Initialize the merged DataFrame with the first DataFrame
    merged_df = data_frames[list(data_frames.keys())[0]]

    # Loop through the rest of the DataFrames and merge them
    for key, df in data_frames.items():
        if key != list(data_frames.keys())[0]:
            #print(key, df.shape) # Skip the first DataFrame
            merged_df = pd.merge(merged_df, df, on=common_col)

    print(f'Shape after merging all fingeprints {merged_df.shape}')
    merged_df = pd.merge(meta_data, merged_df, on = common_col)
    print(f'Shape after merging all fingeprints with metadata {merged_df.shape}')
    return merged_df


def train_test(merge):

    X_data = merge.iloc[:,1:]
    Y_data = merge['Mutagenicity']
    X_data_train, X_data_test, y_data_train, y_data_test = train_test_split(X_data, Y_data, test_size=0.16, random_state=42)

    # Calculate the number of samples and class distribution for training and testing data
    train_samples = len(X_data_train)
    train_class_distribution = Counter(y_data_train)
    test_samples = len(X_data_test)
    test_class_distribution = Counter(y_data_test)

    print(f"Training Data Summary:")
    print(f"Number of Samples: {train_samples}")
    print(f"Class Distribution: {train_class_distribution}\n")

    print(f"Testing Data Summary:")
    print(f"Number of Samples: {test_samples}")
    print(f"Class Distribution: {test_class_distribution}")

    print('w/o scaling')
    print(X_data_train.shape, X_data_test.shape)
    return X_data_train, X_data_test, y_data_train, y_data_test

frame = load_data1()

x_data_train, x_data_test, y_data_train, y_data_test = train_test(frame)
print(type(x_data_test), type(y_data_test))

X_data_train = x_data_train.iloc[:,1:]
X_data_test = x_data_test.iloc[:,1:]
X_data_train.head(2), X_data_test.head(2)

import lightgbm as lgb
# Define the LightGBM parameters
params = {
    'objective': 'binary',
    'metric': 'binary_logloss',
    'boosting_type':  'gbdt',#'rf''num_leaves': 31,
    'learning_rate': 0.1,
    'feature_fraction': 0.9,
    'n_estimators': 200
}

# Train the LightGBM model

import lightgbm as lgb

num_round = 200
lgb_train = lgb.Dataset(X_data_train, y_data_train)
lgb_model = lgb.train(params, lgb_train, num_round)

lgb_model.feature_importance()

# importance of each attribute
fea_imp_ = pd.DataFrame({'cols':X_data_train.columns, 'fea_imp':lgb_model.feature_importance()})
selected_feat = fea_imp_.loc[fea_imp_.fea_imp > 0].sort_values(by=['fea_imp'], ascending = False)['cols']
print(len(selected_feat))
feat = list(selected_feat)
selected_feat.tolist()

import seaborn as sns  

# Sort features by importance
feature_names = X_data_train.columns  # Replace with your actual feature names
feature_importance = lgb_model.feature_importance(importance_type='split')
sorted_idx = feature_importance.argsort()[::-1]

# Set the number of top features to display
max_features = 20

# Create a figure and axes
plt.pyplot.figure(figsize=(10, 6))

# Create a bar plot for feature importances
sns.barplot(y=[feature_names[i] for i in sorted_idx[:max_features]], x=feature_importance[sorted_idx][:max_features], orient="h")

# Set the title and labels
plt.pyplot.title("LightGBM - Top Feature Importances")
plt.pyplot.xlabel("Importance")
plt.pyplot.ylabel("Feature")

# Add horizontal grid lines
plt.pyplot.grid(axis="x", linestyle="--", alpha=0.7)

for i, v in enumerate(feature_importance[sorted_idx][:max_features]):
    plt.pyplot.text(v, i, f" {v}", va='center', fontsize=10, color='black', fontweight='bold')
plt.pyplot.savefig('Feature importances by lightgbm on finger+desc.png', dpi = 600)
# Display the plot
plt.pyplot.show()

X_data_train.shape, X_data_test.shape,y_data_train.shape,y_data_test.shape

def eval_metrics(y_test, y_pred):

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)

    # Calculate precision, recall, and F1-score
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)

    # Generate a confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    return accuracy, precision, recall, f1

def average(my_dict):
    average_dict = {}

    #Calculate the average performance score
    for key, values in my_dict.items():
        avg = sum(values) / len(values)
        std_dev = statistics.stdev(values)
        average_dict[key] = {'average': avg, 'std_deviation': std_dev}

    # Print the average values
    for key, average in average_dict.items():
        print(f"Average for {key}: {average['average']} +/- {average['std_deviation']}")

    return average_dict

def stacking1(X_train, y_train, X_test, y_test, seed, name = 'stacking'):
  my_dict={'ACC':[], 'PRE':[], 'REC':[], 'F1':[], 'AUC':[], 'AUPR':[]}
  my_dict_train={'ACC':[], 'PRE':[], 'REC':[], 'F1':[], 'AUC':[], 'AUPR':[]}
  i=1
  mean_fpr = np.linspace(0, 1, 100)
  tprs=[]
  aucs=[]

  shap_values_lists = []
  precision_list, recall_list = [],[]
  result_table = pd.DataFrame(columns=['model','seed','fingerprint','mean_fpr','mean_tpr','auc'])
  result_table1 = pd.DataFrame(columns=['model','seed','fingerprint','mean_fpr','mean_tpr','auc'])

  cv = StratifiedKFold(n_splits = 5, random_state=seed, shuffle = True)
  arr1 = np.array([])
  arr2 = np.array([])
  arr3 = np.array([])
  y_val_all = pd.Series([])
  for train_index, val_index in cv.split(X_train, y_train):
    shap_values_fold = []
    p_fold,r_fold=[],[]
    X_, X_val = X_train.iloc[train_index], X_train.iloc[val_index]
    y_, y_val = y_train.iloc[train_index], y_train.iloc[val_index]

    params = {
        'objective': 'binary',
        'metric': 'binary_logloss',
        'boosting_type':  'gbdt',#'rf'
        'num_leaves': 31,
        'learning_rate': 0.1,
        'feature_fraction': 0.9,
        'n_estimators': 200
    }

    # Train the LightGBM model
    num_round = 200



    lgb_train = lgb.Dataset(X_, y_)
    lgb_model = lgb.train(params, lgb_train, num_round)

    # Train Random Forest
    rf_model = RandomForestClassifier(n_estimators = 120, max_depth = 17, min samples split = 2, min samples leaf = 1)
    rf_model.fit(X_, y_)

    reg_model = ExtraTreesClassifier(n_estimators=350,  criterion = 'gini' , min samples split =  2, min samples leaf =  1)
    reg_model.fit(X_,y_)



    svm_model = SVC(kernel = 'linear', C=1.0, probability = True)
    svm_model.fit(X_, y_)



    catboost_model = CatBoostClassifier(iterations=40, learning_rate=0.2, verbose=1)
    catboost_model.fit(X_, y_)

    # Generate predictions from base models
    lgb_predictions = lgb_model.predict(X_val)
    reg_predictions = reg_model.predict_proba(X_val)[:,1]
    rf_predictions = rf_model.predict_proba(X_val)[:,1]
    svm_predictions = svm_model.predict_proba(X_val)[:,1]
    cat_predictions = catboost_model.predict_proba(X_val)[:,1]


    # Stacking Layer
    stacked_features = np.column_stack((lgb_predictions, reg_predictions, rf_predictions, svm_predictions, cat_predictions))

    if np.size(arr1) == 0:
      arr1 = stacked_features
    else:
      arr1 = np.vstack((arr1, stacked_features))

    if y_val_all.empty:
      y_val_all = y_val
    else:
      y_val_all = y_val_all.append(y_val)


    # Make predictions with the stacked ensemble
    stacked_test_features = np.column_stack((lgb_model.predict(X_test), reg_model.predict_proba(X_test)[:,1], rf_model.predict_proba(X_test)[:,1],svm_model.predict_proba(X_test)[:,1], catboost_model.predict_proba(X_test)[:,1]))
    #print(stacked_test_features)
    #print(stacked_test_features.shape)

    if np.size(arr2) == 0:
      arr2 = stacked_test_features
    else:

      arr2 = np.sum((arr2, stacked_test_features), axis = 0)
      #print(arr2.shape)


  arr2 = arr2/5.0


  print('=======Outside Cross-Validation=======')
  print(arr1.shape, arr2.shape, y_val_all.shape)
  final_model = MLPClassifier(hidden_layer_sizes=(100), max_iter = 200,learning_rate_init= 0.001, solver = 'adam', batch_size= 'auto', random_state=42)
  final_model.fit(arr1, y_val_all)

  final_predictions = final_model.predict(arr1)
  final_prediction = final_model.predict_proba(arr1)[:,1]


  # Evaluate the final stacked ensemble model
  accuracy = accuracy_score(y_val_all, final_predictions)
  auc = roc_auc_score(y_val_all, final_predictions)
  rec = recall_score(y_val_all, final_predictions)
  prec = precision_score(y_val_all, final_predictions)
  f1 = f1_score(y_val_all, final_predictions)
  aupr = average_precision_score(y_val_all, final_predictions)
  my_dict['ACC'].append(accuracy)
  my_dict['PRE'].append(prec)
  my_dict['REC'].append(rec)
  my_dict['F1'].append(f1)
  my_dict['AUPR'].append(aupr)
  fpr,tpr,t=roc_curve(y_val_all, final_prediction)
  increased_thresholds = np.linspace(0, 1, 1000)

  # Interpolate to get corresponding thresholds
  interp_thresholds = np.interp(increased_thresholds, fpr, t)
  precision,recall,threshold=precision_recall_curve(y_val_all, final_prediction)
  tprs.append(np.interp(mean_fpr,fpr,tpr))
  roc_auc = sklearn.metrics.auc(fpr,tpr)

  my_dict['AUC'].append(roc_auc)
  #print(my_dict)
  aucs.append(roc_auc)

  i=i+1

  p_fold.append(precision)
  r_fold.append(recall)
  precision_list.append(p_fold)
  recall_list.append(r_fold)

  dic1 = {'model': name,'seed': seed,'fingerprint': fingerprint,'mean_fpr': (fpr), 'mean_tpr': (tpr), 'auc': my_dict['AUC']}
  print(len(dic1['mean_tpr']), len(dic1['mean_fpr']))
  k = pd.DataFrame.from_dict(dic1, orient='index')
  k= k.transpose()
  result_table = pd.concat([result_table, k], ignore_index = True)



  final_predictions = final_model.predict(arr2)
  final_prediction = final_model.predict_proba(arr2)[:,1]

  # Evaluate the final stacked ensemble model
  accuracy = accuracy_score(y_test, final_predictions)
  auc = roc_auc_score(y_test, final_predictions)
  rec = recall_score(y_test, final_predictions)
  prec = precision_score(y_test, final_predictions)
  f1 = f1_score(y_test, final_predictions)
  aupr = average_precision_score(y_test, final_predictions)
  my_dict_train['ACC'].append(accuracy)
  my_dict_train['PRE'].append(prec)
  my_dict_train['REC'].append(rec)
  my_dict_train['F1'].append(f1)
  my_dict_train['AUPR'].append(aupr)
  fpr,tpr,t=roc_curve(y_test, final_prediction)
  roc_auc = sklearn.metrics.auc(fpr,tpr)
  my_dict_train['AUC'].append(roc_auc)

  dic1 = {'model': name,'seed': seed,'fingerprint': fingerprint,'mean_fpr': (fpr), 'mean_tpr': (tpr), 'auc': my_dict_train['AUC']}

  print(len(dic1['mean_tpr']), len(dic1['mean_fpr']))
  k = pd.DataFrame.from_dict(dic1, orient='index')

  k= k.transpose()
  result_table1 = pd.concat([result_table1, k], ignore_index = True)


  col_names = ['LGBM', 'ET', 'RF','SVM','CB']

  return my_dict_train, my_dict, result_table, result_table1, final_predictions

fingerprint = 'all'
k = 50

X_data_train = X_data_train[selected_feat.tolist()]
X_data_test = X_data_test[selected_feat.tolist()]

results_dict_val,results_dict_test = {},{}
all_my_dict = {'ACC':[], 'PRE':[], 'REC':[], 'F1':[], 'AUC':[], 'AUPR':[]}
sum_dict = {'ACC':[0], 'PRE':[0], 'REC':[0], 'F1':[0], 'AUC':[0], 'AUPR':[0]}
result_table_1 = pd.DataFrame(columns=['model','seed','fingerprint','mean_fpr','mean_tpr','auc'])
result_table_2 = pd.DataFrame(columns=['model','seed','fingerprint','mean_fpr','mean_tpr','auc'])


name = 'stacking'
seed_values = [42, 123, 567, 789, 999, 111, 222, 333, 444, 555]
for seed in range(1,2):
    metric_test, metric_val, names, prediction = dict(),dict(),list(), list()
    metric_test, metric_val, result_table_val, result_table_test, prediction = stacking1(X_data_train, y_data_train, X_data_test, y_data_test, seed, name)
    result_table_1 = pd.concat([result_table_val, result_table_1], ignore_index = True)
    result_table_2 = pd.concat([result_table_test, result_table_2], ignore_index = True)



# Iterate over the keys in dict1 (or dict2, as they have the same keys)
    for key in metric_test:
    # Sum the values for the common key and store in result_dict
      sum_dict[key] = metric_test[key] + sum_dict[key]

    metric_string_val = ', '.join([f'{k}{v}' for k, v in metric_val.items()])
    metric_string_test = ', '.join([f'{k}{v}' for k, v in metric_test.items()])
    print(f'Seed {seed} > {name} {metric_string_test}')

# store the results for this seed in the dictionary
    results_dict_val[f'Seed {seed} model {name}'] = {'results': metric_string_val}
    results_dict_test[f'Seed {seed} model {name}'] = {'results': metric_string_test}

# Group by 'column_name' and create a dictionary of DataFrames
grouped_dataframes = dict(tuple(df.groupby('seed')))

# Save each DataFrame as a separate CSV file
for key, value in grouped_dataframes.items():
    filename = f"{key}_data.csv"
    value.to_csv(filename, index=False)
    print(f"{filename} saved successfully.")

import pandas as pd
# Function to convert string representation to list of floats
def convert_to_list(string_representation):
    # Remove brackets and split values by space, then convert to float
    return [float(value) for value in string_representation.strip('[]').split()]
AUC = [0.941, 0.9427, 0.9415, 0.9422, 0.9431, 0.9421, 0.9416, 0.9406, 0.9426, 0.941]
#AUC = [0.9518, 0.9521, 0.9506, 0.9528, 0.9518, 0.9524, 0.9533, 0.9514, 0.9530, 0.9526]
# Assuming 'column_name' is the column you want to use for splitting
df = pd.read_csv('Toxcsm_result_table_test_ok(all including 3d).csv')
df['mean_fpr'] = df['mean_fpr'].apply(convert_to_list)
df['mean_tpr'] = df['mean_tpr'].apply(convert_to_list)
df['auc'] = AUC
df

# Group by 'column_name' and create a dictionary of DataFrames
grouped_dataframes = dict(tuple(df.groupby('seed')))

# Save each DataFrame as a separate CSV file
for key, value in grouped_dataframes.items():
    filename = f"{key}_data.csv"
    value.to_csv(filename, index=False)
    print(f"{filename} saved successfully.")

import matplotlib as plt
import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

from ast import literal_eval
from matplotlib.colors import to_rgba

# List of original colors for each line
original_colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown', 'pink', 'gray', 'cyan', 'magenta']

# Iterate over all files in the folder
folder_path = '/content'
truncate = '/content/'
file_pattern = "*_data.csv"
paths = glob.glob(os.path.join(folder_path, file_pattern))
threshold = 0.81
# Create a figure and axis for the plot
fig, ax = plt.subplots(figsize=(8, 6))
# Iterate through the CSV files and plot each ROC curve
for i, file_path in enumerate(paths):
    # Load data from the CSV file
    filename_without_folder = os.path.basename(file_path).replace('_data.csv', '')
    df = pd.read_csv(file_path)
    print(filename_without_folder)
    # df['mean_fpr'] = df['mean_fpr'].apply(convert_to_list)
    # df['mean_tpr'] = df['mean_tpr'].apply(convert_to_list)
    # Extract data for the ROC curve
    mean_fpr = df['mean_fpr']
    print(type(mean_fpr))
    mean_fpr = mean_fpr.apply(literal_eval)[0]
    print(type(mean_fpr))
    mean_tpr = df['mean_tpr']
    print(type(mean_tpr))
    mean_tpr = mean_tpr.apply(literal_eval)[0]
    print(type(mean_tpr))
    #auc_value = literal_eval(df['auc'][0])[0]
    auc_value = df['auc'][0]
    #value = v for v in auc_value
    print((auc_value))

    # Select the color for the current line
    line_color = original_colors[i % len(original_colors)]

    # Plot the ROC curve with its AUC value as a label
    ax.plot(mean_fpr, mean_tpr, label=f'S_{filename_without_folder} (AUC = {auc_value:.4f})', alpha=1.0, linewidth=0.25, color=line_color)

ax.plot([0,1],[0,1], linestyle='--', lw=1, color='k',label='No Skill', alpha=0.9)
# Set labels and title
ax.set_xlabel('False Positive Rate', fontsize=14)
ax.set_ylabel('True Positive Rate', fontsize=14)
ax.tick_params(axis='x', labelsize=14)
ax.tick_params(axis='y', labelsize=14)
ax.set_title('')

# Add a legend
ax.legend(fontsize = 11.5)

# Save and display the plot
plt.savefig('toxcsm_mean_auc_plot_ok.png', dpi=600)
plt.show()

import sys
import urllib.request
from collections import defaultdict
import torch

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from tqdm.notebook import tqdm

from rdkit import Chem
from rdkit.Chem import AllChem, Draw
from rdkit.Chem.Draw import IPythonConsole
import torch.optim as optim

import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, Subset

from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.utils import to_networkx

from catboost import CatBoostClassifier
from xgboost import XGBClassifier
from joblib import dump, load

config = {
    
    'save_path': 'model_save',
    'log_path' : 'log',
    'dataset_type': ['classification']
    'task_num':1,
    'val_path': 'outputs',
    'test_path':'outputs',
    'seed':0,
    'num_folds':1,
    'metric': None,
    'epochs':100,
    'batch_size':32,
    'hidden_size': 300,
    'fp_2_dim':512,
    'nhid':60,
    'nheads':8,
    'gat_scale':0.5,
    'dropout':0.2,
    'dropout_gat':0.0,
    'predict_path':'outputs',
    'result_path':'result.txt',
    'model_path':'outputs',
    'search_num':10,
    'figure_path':'figure',
    'cuda' : False,
    'init_lr' : 1e-4,
    'max_lr' : 1e-3,
    'final_lr' : 1e-4,
    'warmup_epochs' : 2.0,
    'num_lrs' :1,
    'search_now' :0,
    'inter_graph': 1

}
if config['dataset_type'] == 'classification':
    config['metric'] = ['auc', 'prc-auc']
else:
    config['metric'] = ['rmse']

from argparse import Namespace
from rdkit import Chem
import torch

atom_type_max = 100
atom_f_dim = 133
atom_features_define = {
    'atom_symbol': list(range(atom_type_max)),
    'degree': [0, 1, 2, 3, 4, 5],
    'formal_charge': [-1, -2, 1, 2, 0],
    'charity_type': [0, 1, 2, 3],
    'hydrogen': [0, 1, 2, 3, 4],
    'hybridization': [
        Chem.rdchem.HybridizationType.SP,
        Chem.rdchem.HybridizationType.SP2,
        Chem.rdchem.HybridizationType.SP3,
        Chem.rdchem.HybridizationType.SP3D,
        Chem.rdchem.HybridizationType.SP3D2
    ],}

smile_changed = {}

def get_atom_features_dim():
    return atom_f_dim

def onek_encoding_unk(key,length):
    encoding = [0] * (len(length) + 1)
    index = length.index(key) if key in length else -1
    encoding[index] = 1

    return encoding

def get_atom_feature(atom):
    feature = onek_encoding_unk(atom.GetAtomicNum() - 1, atom_features_define['atom_symbol']) + \
           onek_encoding_unk(atom.GetTotalDegree(), atom_features_define['degree']) + \
           onek_encoding_unk(atom.GetFormalCharge(), atom_features_define['formal_charge']) + \
           onek_encoding_unk(int(atom.GetChiralTag()), atom_features_define['charity_type']) + \
           onek_encoding_unk(int(atom.GetTotalNumHs()), atom_features_define['hydrogen']) + \
           onek_encoding_unk(int(atom.GetHybridization()), atom_features_define['hybridization']) + \
           [1 if atom.GetIsAromatic() else 0] + \
           [atom.GetMass() * 0.01]
    return feature

class GraphOne:
    def __init__(self,smile,config):
        self.smile = smile
        self.atom_feature = []

        mol = Chem.MolFromSmiles(self.smile)

        self.atom_num = mol.GetNumAtoms()

        for i, atom in enumerate(mol.GetAtoms()):
            self.atom_feature.append(get_atom_feature(atom))
        self.atom_feature = [self.atom_feature[i] for i in range(self.atom_num)]

class GraphBatch:
    def __init__(self,graphs,config):
        smile_list = []
        for graph in graphs:
            smile_list.append(graph.smile)
        self.smile_list = smile_list
        self.smile_num = len(self.smile_list)
        self.atom_feature_dim = get_atom_features_dim()
        self.atom_no = 1
        self.atom_index = []

        atom_feature = [[0]*self.atom_feature_dim]
        for graph in graphs:
            atom_feature.extend(graph.atom_feature)
            self.atom_index.append((self.atom_no,graph.atom_num))
            self.atom_no += graph.atom_num

        self.atom_feature = torch.FloatTensor(atom_feature)

    def get_feature(self):
        return self.atom_feature,self.atom_index

def create_graph(smile,config):
    graphs = []
    for one in smile:
        if one in smile_changed:
            graph = smile_changed[one]
        else:
            graph = GraphOne(one, config)
            smile_changed[one] = graph
        graphs.append(graph)
    return GraphBatch(graphs,config)

atts_out = []

class GATLayer(nn.Module):

    def __init__(self, in_features, out_features, dropout_gnn, alpha, inter_graph, concat=True):
        super(GATLayer, self).__init__()
        self.dropout_gnn= dropout_gnn
        self.in_features = in_features
        self.out_features = out_features
        self.alpha = alpha
        self.concat = concat
        self.dropout = nn.Dropout(p=self.dropout_gnn)
        self.inter_graph = inter_graph

        self.W = nn.Parameter(torch.zeros(size=(in_features, out_features)))
        nn.init.xavier_uniform_(self.W.data, gain=1.414)
        self.a = nn.Parameter(torch.zeros(size=(2*out_features, 1)))
        nn.init.xavier_uniform_(self.a.data, gain=1.414)

        self.leakyrelu = nn.LeakyReLU(self.alpha)
        if self.inter_graph is not None:
            self.atts_out = []

    def forward(self,mole_out,adj):
        atom_feature = torch.mm(mole_out, self.W)
        N = atom_feature.size()[0]

        atom_trans = torch.cat([atom_feature.repeat(1, N).view(N * N, -1), atom_feature.repeat(N, 1)], dim=1).view(N, -1, 2 * self.out_features)
        e = self.leakyrelu(torch.matmul(atom_trans, self.a).squeeze(2))

        zero_vec = -9e15*torch.ones_like(e)
        attention = torch.where(adj > 0, e, zero_vec)

        if self.inter_graph is not None:
            att_out = attention
            if att_out.is_cuda:
                att_out = att_out.cpu()
            att_out = np.array(att_out)
            att_out[att_out<-10000] = 0
            att_out = att_out.tolist()
            atts_out.append(att_out)

        attention = nn.functional.softmax(attention, dim=1)
        attention = self.dropout(attention)
        output = torch.matmul(attention, atom_feature)

        if self.concat:
            return nn.functional.elu(output)
        else:
            return output


class GATOne(nn.Module):
    def __init__(self,config):
        super(GATOne, self).__init__()
        self.nfeat = get_atom_features_dim()
        self.nhid = config['nhid']
        self.dropout_gnn = config['dropout_gat']
        self.atom_dim = config['hidden_size']
        self.alpha = 0.2
        self.nheads = config['nheads']
        self.config = config
        self.dropout = nn.Dropout(p=self.dropout_gnn)

        if hasattr(config,'inter_graph'):
            self.inter_graph = config['inter_graph']
        else:
            self.inter_graph = None

        self.attentions = [GATLayer(self.nfeat, self.nhid, dropout_gnn=self.dropout_gnn, alpha=self.alpha, inter_graph=self.inter_graph, concat=True) for _ in range(self.nheads)]
        for i, attention in enumerate(self.attentions):
            self.add_module('attention_{}'.format(i), attention)

        self.out_att = GATLayer(self.nhid * self.nheads, self.atom_dim, dropout_gnn=self.dropout_gnn, alpha=self.alpha, inter_graph=self.inter_graph, concat=False)

    def forward(self,mole_out,adj):
        mole_out = self.dropout(mole_out)
        mole_out = torch.cat([att(mole_out, adj) for att in self.attentions], dim=1)
        mole_out = self.dropout(mole_out)
        mole_out = nn.functional.elu(self.out_att(mole_out, adj))
        return nn.functional.log_softmax(mole_out, dim=1)

class GATEncoder(nn.Module):
    def __init__(self,config):
        super(GATEncoder,self).__init__()
        self.cuda = config['cuda']
        self.config = config
        self.encoder = GATOne(self.config)

    def forward(self,mols,smiles):
        atom_feature, atom_index = mols.get_feature()
        # if self.cuda:
        #     atom_feature = atom_feature.cuda()

        gat_outs=[]
        for i,one in enumerate(smiles):
            adj = []
            mol = Chem.MolFromSmiles(one)
            adj = Chem.rdmolops.GetAdjacencyMatrix(mol)
            adj = adj/1
            adj = torch.from_numpy(adj)
            # if self.cuda:
            #     adj = adj.cuda()

            atom_start, atom_size = atom_index[i]
            one_feature = atom_feature[atom_start:atom_start+atom_size]

            gat_atoms_out = self.encoder(one_feature,adj)
            gat_out = gat_atoms_out.sum(dim=0)/atom_size
            gat_outs.append(gat_out)
        gat_outs = torch.stack(gat_outs, dim=0)
        return gat_outs

class GAT(nn.Module):
    def __init__(self,config,out=2):
        super(GAT,self).__init__()
        self.config = config
        self.encoder = GATEncoder(self.config)
        self.fc1 = nn.Linear(300,64,bias=True)
        self.fc2 = nn.Linear(64,out_features=out)
        self.softmax = nn.Softmax(1)
        self.leakyRelu = nn.LeakyReLU()

    def forward(self,smile):
        mol = create_graph(smile, self.config)
        gat_out = self.encoder.forward(mol,smile)

        x = self.leakyRelu(self.fc1(gat_out))
        x = self.leakyRelu(self.fc2(x))



        return x, gat_out

model = GAT(config)

#Training on ToxCSM mutagenicity dataset
selected_df = pd.read_csv('/kaggle/input/ames-mutagenicity/Hansen_metadata.csv')
selected_df = selected_df.drop('ID', axis=1)
selected_df.head(2)

#For predicting embeddings of Hansen mutagenicity dataset
num_classes = len(selected_df['Mutagenicity'].unique())

from sklearn.model_selection import train_test_split

y = selected_df['Mutagenicity']
X = selected_df.drop(['Mutagenicity'],axis=1)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.16, random_state=42, stratify=y)

class CustomSmileDataset(Dataset):
        def __init__(self,X,y):

            self.X = X
            self.smiles = self.X['SMILES'].tolist()
        #     self.features = self.X.drop(['SMILES'],axis=1)
            self.y = y.tolist()



        def __len__(self):
                return len(self.y)

        def __getitem__(self, idx):
                try:
                        # ex = self.X.loc[self.X['SMILES'] == self.smiles[idx]]
                        # ex = dict(ex.drop(['SMILES'],axis=1))
                        # feat = []
                        # for k , v in ex.items():
                        #         feat.append(v.item())
                        # feat = np.array(feat).reshape(1,-1)
                        # feat = torch.from_numpy(feat)

                        return self.smiles[idx],self.y[idx]
                except:
                        print(self.smiles[idx])


trainset = CustomSmileDataset(X_train,y_train)
testset = CustomSmileDataset(X_test,y_test)

full_dataset = CustomSmileDataset(X,y)
full_dataloader = DataLoader(full_dataset,batch_size=1,shuffle=False)


train_dataloader = DataLoader(trainset,batch_size=32,shuffle=True)
valid_dataloader = DataLoader(testset,batch_size=32,shuffle=True)

from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import label_binarize

N_epochs = 100
optimizer = torch.optim.Adam(model.parameters(), lr = 2e-3)

criterion = nn.CrossEntropyLoss(reduction='sum')

# model.train_ml_models(features=features, labels=labels)  # classical models are trained now
best_acc = np.float64(0.0)
for epoch in range(N_epochs):

    train_loss_per_epoch = 0.0
    train_predictions = []
    train_actuals = []
    train_steps = 0

    valid_loss_per_epoch = 0.0
    valid_predictions = []
    valid_actuals = []
    valid_steps = 0

    train_class_probs = []
    valid_class_probs = []

    loop1 = tqdm(train_dataloader, total=len(train_dataloader),desc='Train')
    for b , (smiles,y) in enumerate(loop1):

        # smiles -> smiles
        # batch wise input to ml models
        # y -> labels
        # features are in the form of batches , such that ml model will produce
        # thier o/p which will be used for ensemble learning



        output, _   = model(smiles)  # (batch, num_clasess)

        loss = criterion(output, y)

        preds = output.argmax(1)
        train_loss_per_epoch += loss.item()
        train_steps += int(y.shape[0])

        train_predictions.extend(preds)
        train_actuals.extend(y)


        loss.backward()
        optimizer.step()
        optimizer.zero_grad()

    train_predictions_labels = np.array(train_predictions)
    train_accuracy = (train_predictions_labels == train_actuals).mean()

    train_auc = roc_auc_score(train_actuals, train_predictions)

    print(f"(Train) | (Epoch : {epoch + 1}) | Loss : {train_loss_per_epoch/train_steps}")
    print(f"(Train) | (Epoch : {epoch + 1}) | Accuracy : {train_accuracy}, ROC-AUC : {train_auc}")


    loop2 = tqdm(valid_dataloader, total=len(valid_dataloader),desc='Valid')
    for b , (smiles,y) in enumerate(loop2):

        # X -> smiles
        # y -> labels
        # features are in the form of batches , such that ml model will produce
        # thier o/p which will be used for ensemble learning
        with torch.inference_mode():
            output, _   = model(smiles)  # (batch, num_clasess)

            preds = output.argmax(1)
            loss = criterion(output, y)

            valid_loss_per_epoch += loss.item()
            valid_steps += int(y.shape[0])

            valid_predictions.extend(preds)
            valid_actuals.extend(y)

    valid_predictions_labels = np.array(valid_predictions)
    valid_accuracy = (valid_predictions_labels == valid_actuals).mean()
    valid_auc = roc_auc_score(valid_actuals, valid_predictions)
    print(type(valid_auc), type(best_acc))
    if valid_auc >= best_acc:
        print('Inside comparison loop')
        best_acc = valid_auc
        torch.save(model.state_dict(),'gat_best_hansen.pth')
    print(f"(Valid) | (Epoch : {epoch + 1}) | Loss : {valid_loss_per_epoch/valid_steps}")
    print(f"(Valid) | (Epoch : {epoch + 1}) | Accuracy : {valid_accuracy}, ROC-AUC : {valid_auc}")

model.load_state_dict(torch.load('/kaggle/working/gat_best_hansen.pth'))
model.eval()

embd_dict = {}
loop3 = tqdm(full_dataloader, total=len(full_dataloader),desc='Embed')
for b , (smiles,y) in enumerate(loop3):

    # X -> smiles
    # y -> labels
    # features are in the form of batches , such that ml model will produce
    # thier o/p which will be used for ensemble learning
    with torch.inference_mode():

        _, emb   = model(smiles)  # (batch, num_clasess)

        embd_dict[smiles[0]] = emb
