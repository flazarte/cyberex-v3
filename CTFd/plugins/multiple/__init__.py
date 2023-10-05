from flask import (
    render_template,
    jsonify,
    Blueprint,
    url_for,
    redirect,
    request,
    Flask,
    abort,
    send_from_directory
)
from CTFd.plugins.challenges import CHALLENGE_CLASSES, BaseChallenge
from CTFd.plugins.custom.models import C3CategoryChallenge
from CTFd.plugins import register_plugin_assets_directory
from flask import session 
from CTFd.models import db, Challenges, Awards, Solves, Files, Tags
from CTFd import utils
import logging
from pprint import pprint #for Debugging purpose only remove in Production


class MultiChallenge(C3CategoryChallenge):
    __mapper_args__ = {'polymorphic_identity': 'multiplechoice'}
    id = db.Column(None, db.ForeignKey('c3_category_challenge.id', ondelete="CASCADE"), primary_key=True)
    question = db.Column(db.Text)
    choice_a = db.Column(db.Text)
    choice_b = db.Column(db.Text)
    choice_c = db.Column(db.Text)
    choice_d = db.Column(db.Text)

    def __init__(self, c3_category, name, description, value, category, choice_a, choice_b, choice_c, choice_d, writeups,  question, type='multiplechoice'):
        self.c3_category = c3_category
        self.name = name
        self.description = description
        self.value = value
        self.initial = value
        self.category = category
        self.type = type
        self.question = question
        self.choice_a = choice_a
        self.choice_b = choice_b
        self.choice_c = choice_c
        self.choice_d = choice_d
        self.writeups = writeups

class MultipleChoice(BaseChallenge):
    """multi-answer allows right and wrong answers and leaves the question open"""
    id = "multiplechoice"
    name = "multiplechoice"

    templates = {  # Handlebars templates used for each aspect of challenge editing & viewing
        'create': '/plugins/multiple/assets/multi-challenge-create.html',
        'update': '/plugins/multiple/assets/multi-challenge-update.html',
        'view': '/plugins/multiple/assets/multi-challenge-view.html',
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        'create': '/plugins/multiple/assets/multi-challenge-create.js',
        'update': '/plugins/multiple/assets/multianswer-challenge-update.js',
        'view': '/plugins/multiple/assets/multi-challenge-view.js',
    }
    challenge_model = MultiChallenge

    @staticmethod
    def create(request):
        """
        This method is used to process the challenge creation request.
        :param request:
        :return:
        """
        # Create challenge
        data = request.form or request.get_json()
        chal = MultiChallenge(
            c3_category=data['multiplechoice'],
            name=data['name'],
            description=data['description'],
            value=data['value'],
            category=data['category'],
            type=data['type'],
            question=data['question'],
            choice_a=data['choice_a'],
            choice_b=data['choice_b'],
            choice_c=data['choice_c'],
            choice_d=data['choice_d'],
            writeups=data['writeups']
        )

        db.session.add(chal)
        db.session.commit()

        return chal

def load(app):
    """load overrides for multianswer plugin to work properly"""
    app.db.create_all()
    register_plugin_assets_directory(app, base_path='/plugins/multiple/assets/')
    CHALLENGE_CLASSES["multiplechoice"] = MultipleChoice

  
    #Multiplechoice module routing
    #c3 new scoreboard per category
    @app.route('/api/v2/multiplechoice/<int:chal_id>', methods=['GET'])
    def get_multiplechoice_api(chal_id):
        result = []
        chals = db.session.query(MultiChallenge).filter_by(id=chal_id).first()
        if chals is None:
            return jsonify(result)
        else:    
            result.append({
                "id": chals.id,
                "q": chals.question,
                 "choices":{
                    "a": chals.choice_a,
                    "b": chals.choice_b,
                    "c": chals.choice_c,
                    "d": chals.choice_d,
                    }
                })
        return jsonify(result)


    #Routing Functions
    app.view_functions['app.multiplechoice'] = get_multiplechoice_api