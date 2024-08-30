import joblib
import os
import random
import pandas as pd

#search path
search_path = os.path.join('PFI-Tesis-2024', 'models', 'decision_tree_model.pkl') #get the correct path for the DTC

#load the DTC to make the prediction
dtc = joblib.load('..\\'+search_path)

#dictionay with questions, a dictionary per group. Questions : List of answers
hor_questions = {
    "En una situación en la que tus ideas son cuestionadas, ¿cómo respondes habitualmente?" : ["Afirmo mi punto de vista y mantengo mi postura","Intento conciliar las diferencias y mantener la armonía","Tomo distancia para reflexionar y reconsiderar mi posición"],
    "Si te sientes abrumado, ¿cuál es tu respuesta típica?" : ["Sigo adelante y tomo acción","Me retiro para reflexionar y recargar mi energía","Me retiro para reflexionar y recargar mi energía"],
}
harc_questions = {
    "Imagina que te enfrentas con un obstáculo en tu camino hacia un objetivo, ¿cómo reaccionarías?" : ["Me concentro en encontrar una solución y seguir adelante","Mantengo una actitud positiva y busco el lado bueno", "Reacciono emocionalmente y expreso mi frustración"],
    "¿Cómo afrontas los problemas inesperados que interrumpen tus planes?" : ["Me concentro en resolver el problema con determinación", "Intento mantenerme optimista y espero encontrar una solución", "Manifiesto mis opiniones con convicción"]
}
hary_questions= {
    "Cuando trabajas en un proyecto grupal, ¿qué es lo que más motiva tu comportamiento?" : ["Asegurarme de que todos se sientan involucrados y que el proyecto refleje el consenso del grupo", "Asegurarme de que el proyecto cumpla con un alto estándar de excelencia, incluso si eso implica hacer críticas", "Asegurarme de que el proyecto se mantenga encaminado tomando la iniciativa, incluso si eso implica tomar decisiones difíciles"],
    "¿Qué te motiva a ayudar a otros?" : ["El deseo de ser una parte valiosa e integral del grupo.", "La frustración de ver a otros luchar y querer mejorar su situación", "La necesidad de asegurar mi importancia en la vida de otros y que los demás puedan contar conmigo"]
}
triad_questions ={
    "Cuando alguien te critica, ¿cuál es tu reacción inicial?" : ["Me siento herido o rechazado","Me defiendo instintivamente","Analizo la validez de la crítica"],
    "¿Cómo aborda la resolución de problemas en una situación de alta presión?" : ["Confío en mis emociones y en cómo me hace sentir la situación","Confío en mis instintos para guiarme","Pienso en la situación lógicamente"]
}

#questions and answers for the user to give
hor_index = random.choice(list(hor_questions.keys()))
harc_index = random.choice(list(harc_questions.keys()))
hary_index = random.choice(list(hary_questions.keys()))
triad_index = random.choice(list(triad_questions.keys()))
print("\n\nSeleccione una opción para cada pregunta:")
hornevian = input("\nP: {question}: \n    1) {assertive} (assertive) \n    2) {compliant} (compliant) \n    3) {withdrawn} (withdrawn)\n\nSeleccione una opción: ".format(question = hor_index, assertive = hor_questions[hor_index][0], compliant = hor_questions[hor_index][1], withdrawn = hor_questions[hor_index][2]))
harmonic = input("\nP: {question}: \n    1) {competency} (competency) \n    2) {positive} (positive) \n    3) {reactive} (reactive) \n\nSeleccione una opción: ".format(question = harc_index, competency = harc_questions[harc_index][0], positive = harc_questions[harc_index][1], reactive = harc_questions[harc_index][2]))
harmony = input("\nP: {question}: \n    1) {attachment} (attachment) \n    2) {frustration} (frustration) \n    3) {rejection} (rejection) \n\nSeleccione una opción: ".format(question = hary_index, attachment = hary_questions[hary_index][0], frustration = hary_questions[hary_index][1], rejection = hary_questions[hary_index][2]))
triad = input("\nP: {question}: \n    1) {feeling} (feeling) \n    2) {intuition} (intuition) \n    3) {thought} (thought) \n\nSeleccione una opción: ".format(question =triad_index, feeling = triad_questions[triad_index][0], intuition = triad_questions[triad_index][1], thought = triad_questions[triad_index][2]))

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

print(f'\nTu Eneatipo predicho es: {predicted_enneatype[0]}')