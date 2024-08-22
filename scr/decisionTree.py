import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.metrics import accuracy_score


#provisional data set
data = {
    'introversion' : [8, 4, 2, 3, 6, 5, 7, 9, 1, 5],
    'anxiety' : [6, 4, 8, 2, 1, 6, 8, 9, 4, 3],
    'creativity' : [4, 4, 7, 4, 7, 2, 1, 3, 6, 4],
    'enneatype' : [5, 4, 6, 7, 3, 4, 9, 2, 1, 7]
}

df = pd.DataFrame(data)

#features and target

X = df[['introversion','anxiety','creativity']]
y = df['enneatype']

#split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

#initialize the Decision Tree Classifier
dtc = DecisionTreeClassifier(random_state=42)
#trains the classifier with the testing data from our data set
dtc.fit(X_train, y_train)

#predictions based on the test we want to run
y_pred = dtc.predict(X_test)
#accuracy evaluation
accuracy = accuracy_score(y_test,y_pred) #Compares the testing data with the prediction made by the tree.
print(f'Accuracy: {accuracy:.2f}')

#export the Decision Tree to Matplotlib format and displays it
plt.figure(figsize=(12, 8))
plot_tree(dtc, feature_names=['introversion', 'anxiety', 'creativity'], 
          class_names=[str(i) for i in sorted(df['enneatype'].unique())], 
          filled=True, rounded=True, fontsize=10)
plt.title("Decision Tree for Enneatype Prediction")
plt.show()
