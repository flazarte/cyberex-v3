#import datetime
from datetime import datetime
from CTFd.models import Users, db, Challenges, Flags, Teams
from CTFd.plugins.challenges import BaseChallenge
from CTFd.models import db, Solves
from sqlalchemy.types import TIMESTAMP
from datetime import datetime
from sqlalchemy import Column, text, create_engine
from CTFd.utils.modes import get_model
import math
from CTFd.utils.user import is_admin, get_current_user
from CTFd.plugins.flags import FlagException, get_flag_class
from CTFd.utils.user import get_ip
from pprint import pprint

#custom c3 Databases
#Add category db
class C3_category(db.Model):
    __tablename__ = 'c3_category'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80))  
    description = db.Column(db.Text) 
    image_name = db.Column(db.Text)
    location = db.Column(db.Text)
    
    def __init__(self, *args, **kwargs):
        super(C3_category, self).__init__(**kwargs)

#Cyber eX Category Lockout
class c3_lockout(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    ctf_category_id = db.Column(
        db.Integer, db.ForeignKey("c3_category.id", ondelete="CASCADE")
    )
    lockout_percentage = db.Column(db.Integer)
    def __init__(self, *args, **kwargs):
        super(c3_lockout, self).__init__(**kwargs)
    
   
#Add c3 Selected category
class C3_selected_cat(db.Model):
    __tablename__ = 'c3_selected_cat'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    ctf_category_id = db.Column(db.Integer)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    team_id = db.Column(
        db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE")
    ) 
    def __init__(self, *args, **kwargs):
        super(C3_selected_cat, self).__init__(**kwargs)

class C3CategoryChallenge(Challenges):
    __mapper_args__ = {'polymorphic_identity': 'c3_category'}
    __table_args__ = {'extend_existing': True}
    id = db.Column(None, db.ForeignKey('challenges.id', ondelete="CASCADE"), primary_key=True)
    c3_category = db.Column(db.Integer)
    initial = db.Column(db.Integer)
    writeups = db.Column(db.Text)

    def __init__(self, c3_category, name, description, value, category,  writeups, type='c3_category'):
        self.c3_category = c3_category
        self.name = name
        self.description = description
        self.value = value
        self.initial = value
        self.category = category
        self.type = type
        self.writeups = writeups
        
class CategoryGameClass(BaseChallenge):
    id = "c3_category"  # Unique identifier used to register cyber eX challenges
    name = "c3_category"  # Name of a Cyber eX challenge type

    templates = {  # Templates used for each aspect of c3 challenge editing & viewing
        "create": "/plugins/custom/admin/challenges/create.html",
        "update": "/plugins/custom/admin/challenges/update.html",
        "view": "/plugins/custom/admin/challenges/view.html",
    }
    scripts = {  # Scripts that are loaded when a template is loaded
        "create": "/plugins/custom/admin/challenges/create.js",
        "update": "/plugins/custom/admin/challenges/update.js",
        "view": "/plugins/custom/admin/challenges/view.js",
    }
    challenge_model = C3CategoryChallenge

    @staticmethod
    def create(request):
        """
        This method is used to process the challenge creation request.
        :param request:
        :return:
        """
        # Create challenge
        data = request.form or request.get_json()
        chal = C3CategoryChallenge(
            c3_category=data['c3_category'],
            name=data['name'],
            description=data['description'],
            value=data['value'],
            category=data['category'],
            type=data['type'],
            writeups=data['writeups']
        )

        db.session.add(chal)
        db.session.commit()

        return chal

    @classmethod
    def attempt(cls, challenge, request):
        """
        This method is used to check whether a given input is right or wrong. It does not make any changes and should
        return a boolean for correctness and a string to be shown to the user. It is also in charge of parsing the
        user's input from the request itself.

        :param challenge: The Challenge object from the database
        :param request: The request the user submitted
        :return: (boolean, string)
        """
        data = request.form or request.get_json()
        submission = data["submission"].strip()
        flags = Flags.query.filter_by(challenge_id=challenge.id).all()
        for flag in flags:
            try:
                if get_flag_class(flag.type).compare(flag, submission):
                    return True, "Correct"
            except FlagException as e:
                return False, str(e)
        return False, "Incorrect"
    
#write-ups upload db
class C3WriteUps(db.Model):
    __tablename__ = "c3writeups"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), default="writeups")
    location = db.Column(db.Text)
    name = db.Column(db.Text)

    __mapper_args__ = {"polymorphic_identity": "c3writeups", "polymorphic_on": type}

    def __init__(self, *args, **kwargs):
        super(C3WriteUps, self).__init__(**kwargs)

    def __repr__(self):
        return "<File type={type} location={location}>".format(
            type=self.type, location=self.location
        )
        
class ChallengeWriteUps(C3WriteUps):
    __mapper_args__ = {"polymorphic_identity": "c3writeups_challenges"}
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE")
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    team_id = db.Column(
        db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE")
    )
    points = db.Column(db.Integer,default=0)

    def __init__(self, *args, **kwargs):
        super(ChallengeWriteUps, self).__init__(**kwargs)
    
        
#Challenge Category with description and image
class C3ChallengeCategory(db.Model):
    __tablename__ = "c3_challenge_category"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), default="c3_category")
    location = db.Column(db.Text)
    image_name = db.Column(db.Text)
    category_name = db.Column(db.Text)
    description = db.Column(db.Text)

    __mapper_args__ = {"polymorphic_identity": "c3_category", "polymorphic_on": type}

    def __init__(self, *args, **kwargs):
        super(C3ChallengeCategory, self).__init__(**kwargs)

    def __repr__(self):
        return "<File type={type} location={location}>".format(
            type=self.type, location=self.location
        )

#counter measure upload db
class C3CounterMeasure(db.Model):
    __tablename__ = "c3CounterMeasure"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), default="countermeasure")
    location = db.Column(db.Text)
    name = db.Column(db.Text)

    __mapper_args__ = {"polymorphic_identity": "countermeasure", "polymorphic_on": type}

    def __init__(self, *args, **kwargs):
        super(C3CounterMeasure, self).__init__(**kwargs)

    def __repr__(self):
        return "<File type={type} location={location}>".format(
            type=self.type, location=self.location
        )
        
class ChallengeCounterMeasure(C3CounterMeasure):
    __mapper_args__ = {"polymorphic_identity": "countermeasure_challenges"}
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE")
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    team_id = db.Column(
        db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE")
    )
    points = db.Column(db.Integer,default=0)

    def __init__(self, *args, **kwargs):
        super(ChallengeCounterMeasure, self).__init__(**kwargs)

#Blog Article Database
class CTK_Blog(db.Model):
    __tablename__ = "ctk_blog"
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80))
    slug = db.Column(db.Text)
    featured =  db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    content = db.Column(db.Text)
    # date = db.Column(TIMESTAMP, default=datetime.utcnow, nullable=False, server_default=text('0')) | MYSQL
    date = db.Column(db.DateTime, default=datetime.utcnow)
    author = db.Column(db.Integer)

    def __init__(self, *args, **kwargs):
        super(CTK_Blog, self).__init__(**kwargs)

#Published counter measure| Chronicles for a Score Surprise
#Based on KNOW-DO-LEARN Concept
class docs_publish(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    countermeasure_published = db.Column(db.Boolean, default=False)
    chronicles_published = db.Column(db.Boolean, default=False)

    def __init__(self, *args, **kwargs):
        super(docs_publish, self).__init__(**kwargs)

#Users | Teams Registration Modes
class CTK_Config(Users):
    __mapper_args__ = {"polymorphic_identity": "user"}
    mode = db.Column(db.Text)
    
    def __init__(self, *args, **kwargs):
        super(Users, self).__init__(**kwargs)

#Directorate Chronicles Scoring
class ChroniclesDirectorate(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    writeups_id = db.Column(
        db.Integer, db.ForeignKey("c3writeups.id", ondelete="CASCADE")
    )
    directorate_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    rater_points = db.Column(db.Integer,default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super(ChroniclesDirectorate, self).__init__(**kwargs)

#Directorate Countermeasures Scoring
class CountermeasureDirectorate(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    countermeasures_id = db.Column(
        db.Integer, db.ForeignKey("c3CounterMeasure.id", ondelete="CASCADE")
    )
    directorate_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    rater_points = db.Column(db.Integer,default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super(CountermeasureDirectorate, self).__init__(**kwargs)

#knowledge well v2
class KnowledgeWell(db.Model):
    __tablename__ = "knowledge_well"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(80), default="knowledge")
    location = db.Column(db.Text)
    name = db.Column(db.Text)

    __mapper_args__ = {"polymorphic_identity": "knowledge", "polymorphic_on": type}

    def __init__(self, *args, **kwargs):
        super(KnowledgeWell, self).__init__(**kwargs)

    def __repr__(self):
        return "<File type={type} location={location}>".format(
            type=self.type, location=self.location
        )
        
class KnowledgeWellDocs(KnowledgeWell):
    __mapper_args__ = {"polymorphic_identity": "knowledge_docs"}
    challenge_id = db.Column(
        db.Integer, db.ForeignKey("challenges.id", ondelete="CASCADE")
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    team_id = db.Column(
        db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE")
    )
    points = db.Column(db.Integer,default=0)

    def __init__(self, *args, **kwargs):
        super(KnowledgeWellDocs, self).__init__(**kwargs)

#Directorate Knowledge Well Scoring
class KnowledgeDirectorate(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    knowledge_id = db.Column(
        db.Integer, db.ForeignKey("knowledge_well.id", ondelete="CASCADE")
    )
    directorate_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE")
    )
    rater_points = db.Column(db.Integer,default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, *args, **kwargs):
        super(KnowledgeDirectorate, self).__init__(**kwargs)

#Red Teaming Activate
class red_teaming(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    redteaming_activate = db.Column(db.Boolean, default=False)

    def __init__(self, *args, **kwargs):
        super(red_teaming, self).__init__(**kwargs)