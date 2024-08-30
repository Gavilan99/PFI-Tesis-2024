import joblib
import os
import pandas as pd


#search path
search_path = os.path.join('PFI-Tesis-2024', 'models', 'decision_tree_model.pkl') #get the correct path for the DTC

#load the DTC to make the prediction
dtc = joblib.load(search_path)

#questions and answers for the user to give
print("Seleccione una opción para cada pregunta:")
hornevian = input("1. Hornevian: \n1) Assertive \n2) Compliant \n3) Withdrawn\n")
harmonic = input("2.  Harmonic: \n1) Positive \n2) Reactive \n3) Competency\n")
harmony = input("3. Harmony: \n1) Attachment \n2) Frustration \n3) Rejection\n")
triad = input("4. Triad: \n1) Feeling \n2) Intuition \n3) Thought\n")

#map the answers
encoded_responses = {
    'Hornevian_Assertive': True if hornevian == '1' else False,
    'Hornevian_Compliant': True if hornevian == '2' else False,
    'Hornevian_Withdrawn': True if hornevian == '3' else False,
    'Harmonic_Competency': True if harmonic == '1' else False,
    'Harmonic_Positive': True if harmonic == '2' else False,
    'Harmonic_Reactive': True if harmonic == '3' else False,
    'Harmony_Attachment': True if harmony == '1' else False,
    'Harmony_Frustration': True if harmony == '2' else False,
    'Harmony_Rejection': True if harmony == '3' else False,
    'Triad_Feeling': True if triad == '1' else False,
    'Triad_Intuition': True if triad == '2' else False,
    'Triad_Thought': True if triad == '3' else False
}

#convert the answers into a dataframe
user_df = pd.DataFrame([encoded_responses])

#make the prediction with the answers given by the user
predicted_enneatype = dtc.predict(user_df)

print(f'Tu Eneatipo predicho es: {predicted_enneatype[0]}')