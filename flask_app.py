from flask import Flask, send_from_directory, send_from_directory
from flask import render_template, jsonify, request
#from flask_cors import CORS
from flasgger import Swagger
from flask_restful import Api, Resource
import pandas as pd
import joblib
import spacy
import en_core_web_sm
import preprocessing as ppc


app = Flask(__name__, static_url_path='/', static_folder='./build')
#api = Api(app)

template = {
  "swagger": "2.0",
  "info": {
    "title": "Stackoverflow tags predictor for question",
    "description": "API to predict tags of a stackoverflow non-cleaned question.",
    "contact": {
      "email": "bdiomande@dataream.fr"
    },
    "version": "0.0.1"
  }
}

swagger = Swagger(app, template=template)
# Load pre-trained models
model_path = "static/models/"
vectorizer = joblib.load(model_path + "tfidf_vectorizer.pkl", 'r')
multilabel_binarizer = joblib.load(model_path + "multilabel_binarizer.pkl", 'r')
model = joblib.load(model_path + "logit_nlp_model.pkl", 'r')

#class Autotag(Resource):
def getTags(question):

    """
    This examples uses FlaskRESTful Resource for Stackoverflow auto-tagging questions
    To test, copy and paste a non-cleaned question (even with HTML tags or code) and execute the model.
    ---
    parameters:
      - in: path
        name: question
        type: string
        required: true
    responses:
      '200':
        description: Predicted list of tags and probabilities
        content:
            application/json:
                schema:
                    type: object
                    properties:
                        Predicted_Tags:
                            type: string
                            description: List of predicted tags with over 50% of probabilities.
                        Predicted_Tags_Probabilities:
                            type: string
                            description: List of tags with over 30% of probabilities
    """
    # Clean the question sent
    nlp = spacy.load('en_core_web_sm')
    #nlp = en_core_web_sm.load(exclude=['tok2vec', 'ner', 'parser', 'attribute_ruler', 'lemmatizer'])
    #nlp = spacy.load('en_core_web_md', exclude=['tok2vec', 'ner', 'parser', 'attribute_ruler', 'lemmatizer'])
    #nlp = spacy.load('en_core_web_lg') 
    pos_list = ["NOUN","PROPN"]
    rawtext = question
    cleaned_question = ppc.text_cleaner(rawtext, nlp, pos_list, "english")
    
    # Apply saved trained TfidfVectorizer
    X_tfidf = vectorizer.transform([cleaned_question])
    
    # Perform prediction
    predict = model.predict(X_tfidf)
    predict_probas = model.predict_proba(X_tfidf)
    # Inverse multilabel binarizer
    tags_predict = multilabel_binarizer.inverse_transform(predict)
    
    # DataFrame of probas
    df_predict_probas = pd.DataFrame(columns=['Tags', 'Probas'])
    df_predict_probas['Tags'] = multilabel_binarizer.classes_
    df_predict_probas['Probas'] = predict_probas.reshape(-1)
    # Select probas > 33%
    df_predict_probas = df_predict_probas[df_predict_probas['Probas']>=0.33]\
        .sort_values('Probas', ascending=False)
        
    # Results
    results = {}
    results['Predicted_Tags'] = tags_predict
    results['Predicted_Tags_Probabilities'] = df_predict_probas\
        .set_index('Tags')['Probas'].to_dict()
    
    #return results, 200
    return tags_predict


@app.route("/", defaults={'path':''})
def serve(path):
    return send_from_directory(app.static_folder,'index.html')


@app.route('/api/getRecommendedTags', methods=['POST'])
def api_all():
    #question = []
    #question.append(request.json['question'])
    question = request.json['question']
    print(question)
    tags = getTags(question)[0]
    return jsonify(tags)

#api.add_resource(Autotag, '/autotag/<question>')

if __name__ == "__main__":
	app.run()
