import os
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import graphviz
import datetime
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.tree import DecisionTreeClassifier, plot_tree, export_graphviz
from sklearn.metrics import accuracy_score, confusion_matrix

#Save path for the decision tree.
save_path = os.path.join('PFI-Tesis-2024', 'models', 'decision_tree_model.pkl') #save path

sns.set_theme(style='whitegrid')

#normalize the path to the dataset
csv_path = os.path.join('PFI-Tesis-2024','data', 'dataset.csv') #normalization
df = pd.read_csv(csv_path) #transform into dataframe

df_encoded = pd.get_dummies(df, columns=['Hornevian','Harmonic','Harmony','Triad']) #encode the data frame to turn the categorical data into quantitative data
column_names = df_encoded.columns
print(column_names)

#features and target
X = df_encoded.drop('Result', axis=1) #Features. All columns except 'Result'
y = df_encoded['Result'] #Target. Column 'Result' => Enneatype

#split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

#initialize the Decision Tree Classifier
dtc = DecisionTreeClassifier(max_depth=7, min_samples_split=10, class_weight='balanced' ,criterion='entropy', random_state=42)
#trains the classifier with the testing data from our data set
dtc.fit(X_train, y_train)

#Saves the DTC so it can be used by other files
joblib.dump(dtc, save_path)

#predictions based on the test we want to run
y_pred = dtc.predict(X_test)
#accuracy evaluation
accuracy = accuracy_score(y_test,y_pred) #Compares the testing data with the prediction made by the tree.
print(f'Accuracy: {accuracy:.2f}')
#cross validation evaluation
skf = StratifiedKFold(n_splits=5)
scores = cross_val_score(dtc, X, y, cv=skf)
print(f'Cross-Validation Accuracy: {scores.mean():.2f}')
#confusion matrix evaluation
cm = confusion_matrix(y_test, y_pred)
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels= range(1,10), yticklabels=range(1,10)) #Better visualize confusion matrix
plt.xlabel('Predicted')
plt.ylabel('Actual')
plt.title('Confusion Matrix')
plt.show()

#featureImportance
feature_importances = pd.Series(dtc.feature_importances_, index=X.columns)
feature_importances.nlargest(10).plot(kind='barh')
plt.title('Top 10 Feature Importances')
plt.show()

#export the Decision Tree to Matplotlib format and displays it
plt.figure(figsize=(12, 8))
plot_tree(dtc, feature_names=X.columns, 
          class_names=[str(i) for i in sorted(y.unique())], 
          filled=True, rounded=True, fontsize=10, proportion=True)

plt.title("Decision Tree for Enneatype Prediction")
plt.show()

#formats the Matplotlib generated graph into a pdf file, which is more legible.

pdf_save_path= os.path.join('PFI-Tesis-2024', 'output','decision_tree_classifier')

dot_data = export_graphviz(dtc, out_file=None, 
                           feature_names=X.columns,  
                           class_names=[str(i) for i in sorted(y.unique())],  
                           filled=True, rounded=True,  
                           special_characters=True,
                           proportion=True) 

dot_data = dot_data.replace('value =', '')

graph = graphviz.Source(dot_data) 
graph.render(pdf_save_path) 
graph.view() 