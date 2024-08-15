from statistics import mode
from sqlalchemy.sql.expression import asc
from CTFd.models import Teams, db, Challenges, Awards, Solves, Users, Submissions
from sqlalchemy.sql import or_, union_all
from CTFd.plugins.custom.models import (
    C3_category, 
    C3_selected_cat, 
    C3CategoryChallenge, 
    C3ChallengeCategory,
    CTK_Config,
    ChallengeWriteUps,
    ChallengeCounterMeasure,
    c3_lockout,
    docs_publish,
    ChroniclesDirectorate,
    CountermeasureDirectorate,
    KnowledgeWellDocs,
    KnowledgeDirectorate,
    DocumentationDirectorate
    )
from CTFd.utils.user import is_admin, get_current_user
from CTFd.utils.scores import get_standings, get_user_standings, get_team_standings
from CTFd.utils.config.visibility import challenges_visible
from CTFd.utils.dates import (
    ctf_started, ctftime, view_after_ctf, unix_time_to_utc
)
from CTFd.cache import cache
from CTFd.utils import get_config
from CTFd.utils.dates import unix_time_to_utc
from CTFd.utils.modes import get_model
from CTFd.utils.config import is_teams_mode, is_users_mode
import decimal
import string
import random
#import multiple choice modul plugin | Required Module
from CTFd.plugins.multiple import MultiChallenge
from sqlalchemy.orm import aliased
import json
from pprint import pprint


#Get User mode
def ctk_mode():
    #set default config as users 
    mode = 'users'
    curent_user = get_current_user()
    if curent_user is None:
        mode = 'users'
    else:
        if is_admin():
            pass
        else:
            user = db.session.query(CTK_Config).filter_by(id=curent_user.id).first()
            mode = user.mode
    return mode

#Get User mode
def ctk_users_mode():
    return ctk_mode() == 'users'

#Get Teams mode
def ctk_teams_mode():
    return ctk_mode() == 'teams'

#Get Directorate mode
def ctk_directorate_mode():
    return ctk_mode() == 'directorate'

#get score challenges with date
def ctk_scores_date(mode,cat_id):
    #team mode
    if mode == 'team':
        solves = db.session.query(
                        C3CategoryChallenge.value.label("points"),
                        Solves.challenge_id.label("challenge_id"),
                        Solves.team_id.label("team_id"),
                        Submissions.date.label("date"),
                ).join(C3CategoryChallenge
                ).filter(C3CategoryChallenge.id == Solves.challenge_id
                ).filter(C3CategoryChallenge.c3_category == cat_id
                ).order_by(asc(Solves.date)).all()
    #user mode
    if mode == 'user':
        user_ids = []
        players = db.session.query(Users.id).filter(Users.type != 'admin').filter(Users.team_id == None).all()
        for player in players:
            user_ids.insert(0, player.id)
        solves = db.session.query(
                        C3CategoryChallenge.value.label("points"),
                        Solves.challenge_id.label("challenge_id"),
                        Solves.user_id.label("user_id"),
                        Submissions.date.label("date"),
                ).join(C3CategoryChallenge
                ).filter(C3CategoryChallenge.id == Solves.challenge_id
                ).filter(C3CategoryChallenge.c3_category == cat_id
                ).filter(Solves.user_id.in_(user_ids)
                ).order_by(asc(Solves.date)).all()
    return solves

#new ctk model
def ctk_get_model():
    if ctk_users_mode():
        return Users
    elif ctk_teams_mode():
        return Teams


#get score in documentations Writeups
def ctk_knowledge_scores(mode, account_id):
    published = db.session.query(docs_publish).first()
    if published is None:
        db.session.merge(docs_publish(countermeasure_published=False))
        db.session.commit()
    if mode == 'team':   
        #knowledge Well
        if published.countermeasure_published == False:
            know_exist  = None
        else:
            know_exist = db.session.query(db.func.sum(ChallengeWriteUps.know_score)).filter_by(team_id = account_id).scalar()
    if mode == 'user':
        #writeups
        if published.countermeasure_published == False:
            know_exist = None
        else:
            know_exist = db.session.query(db.func.sum(ChallengeWriteUps.know_score)).filter_by(user_id = account_id).scalar()
    if know_exist is None:
        know_exist = 0

    return know_exist

#get score in documentations Writeups
def ctk_writeups_scores(mode, account_id):
    published = db.session.query(docs_publish).first()
    if published is None:
        db.session.merge(docs_publish(countermeasure_published=False))
        db.session.commit()
    if mode == 'team':   
        #writeups
        if published.countermeasure_published == False:
            doc_exist  = None
        else:
            doc_exist = db.session.query(db.func.sum(ChallengeWriteUps.do_score)).filter_by(team_id = account_id).scalar()
    if mode == 'user':
        #writeups
        if published.countermeasure_published == False:
            doc_exist = None
        else:
            doc_exist = db.session.query(db.func.sum(ChallengeWriteUps.do_score)).filter_by(user_id = account_id).scalar()
    if doc_exist is None:
        doc_exist = 0

    return doc_exist


#get score in documentations Writeups | Countermeasures
def ctk_countermeasure_scores(mode, account_id):
    published = db.session.query(docs_publish).first()
    if published is None:
        db.session.merge(docs_publish(countermeasure_published=False))
        db.session.commit()
    if mode == 'team':   
        #countermeasure
        if published.countermeasure_published is None:
            counter_exist = None
        else:
            counter_exist = db.session.query(db.func.sum(ChallengeWriteUps.learn_score)).filter_by(team_id = account_id).scalar()  
    if mode == 'user':
        #countermeasure
        if published.countermeasure_published == False:
            counter_exist = None
        else:
            counter_exist = db.session.query(db.func.sum(ChallengeWriteUps.learn_score)).filter_by(user_id = account_id).scalar()
    if counter_exist is None:
        counter_exist = 0
            
    return counter_exist

#check if category exist
def ctk_cat_exist(mode):
    cat_exist = None
    user = get_current_user()
    if mode == 'user':
        cat_exist = db.session.query(C3_selected_cat).filter_by(user_id = user.id).first()
    if mode == 'team':
        cat_exist = db.session.query(C3_selected_cat).filter_by(team_id = user.team_id).first()
    return cat_exist
   
#get challenges by mode user | team
def ctk_challenge(mode):
    chals = ''
    user = get_current_user()
    #prepare team selected category
    selected = aliased(C3_selected_cat)
    #team mode
    if mode == 'team':
        chals = C3CategoryChallenge.query.join(selected,(selected.team_id == user.team_id)
                ).filter(or_(C3CategoryChallenge.state != 'hidden', C3CategoryChallenge.state is None)
                ).filter(C3CategoryChallenge.c3_category == selected.ctf_category_id).order_by(C3CategoryChallenge.value.asc()).all()
    #user mode
    if mode == 'user':
        chals = C3CategoryChallenge.query.join(selected,(selected.user_id == user.id)
                ).filter(or_(C3CategoryChallenge.state != 'hidden', C3CategoryChallenge.state is None)
                ).filter(C3CategoryChallenge.c3_category == selected.ctf_category_id).order_by(C3CategoryChallenge.value.asc()).all()
    return chals

#get the challenge total counts
def ctk_total_challenge(mode,c3):
    chals = ''
    user = get_current_user()
    #prepare team selected category
    selected = aliased(C3_selected_cat)
    #team mode
    if mode == 'team':
        chals = C3CategoryChallenge.query.join(selected,(selected.team_id == user.team_id)
                ).filter(or_(C3CategoryChallenge.state != 'hidden', C3CategoryChallenge.state is None)
                ).filter(C3CategoryChallenge.c3_category == c3).count()
    #user mode
    if mode == 'user':
        chals = C3CategoryChallenge.query.join(selected,(selected.user_id == user.id)
                ).filter(or_(C3CategoryChallenge.state != 'hidden', C3CategoryChallenge.state is None)
                ).filter(C3CategoryChallenge.c3_category == c3).count()
    return chals

#get total score | overall
def overall_score(users=None):
    total_standings = []
    #awards = Awards.query.filter_by(user_id).all()
    #user mode support
    if ctk_users_mode():
        user_standings = []
        if users:
            for standing in get_user_standings():
                for user_player in users:
                    if user_player.id == standing.user_id:
                        flag = Users.query.filter(Users.id == standing.user_id).first()
                        counter_exist = ctk_countermeasure_scores(mode='user',account_id=standing.user_id)
                        doc_exist = ctk_writeups_scores(mode='user',account_id=standing.user_id)
                        total_scores = decimal.Decimal(standing.score) + decimal.Decimal(doc_exist) + decimal.Decimal(counter_exist)
                        user_standings.append({
                            'account_id': standing.user_id,
                            'name': standing.name,
                            'score': total_scores,
                            'country': flag.country
                        })
        standings = {
            'overall': sorted(user_standings , key=lambda x: x['score'], reverse=True),
        }
    #team mode support
    if ctk_teams_mode():
        for standing in get_team_standings():
            counter_exist = ctk_countermeasure_scores(mode='team',account_id=standing.team_id)
            doc_exist = ctk_writeups_scores(mode='team',account_id=standing.team_id)
            total_scores = decimal.Decimal(standing.score) + decimal.Decimal(doc_exist) + decimal.Decimal(counter_exist)
            total_standings.append({
            'account_id': standing.team_id,
            'name': standing.name,
            'score': total_scores
            })
        standings = {
            'overall': sorted(total_standings , key=lambda x: x['score'], reverse=True),
        }
    
    #user mode support
    if ctk_directorate_mode():
        user_standings = []
        if users:
            for standing in get_user_standings():
                for user_player in users:
                    if user_player.id == standing.user_id:
                        counter_exist = ctk_countermeasure_scores(mode='user',account_id=standing.user_id)
                        doc_exist = ctk_writeups_scores(mode='user',account_id=standing.user_id)
                        total_scores = decimal.Decimal(standing.score) + decimal.Decimal(doc_exist) + decimal.Decimal(counter_exist)
                        user_standings.append({
                            'account_id': standing.user_id,
                            'name': standing.name,
                            'score': total_scores,
                            'country': standing.country
                        })
        standings = {
            'overall': sorted(user_standings , key=lambda x: x['score'], reverse=True),
        }
    return standings

#get total score | overall
def All_scores(users=None):
    total_standings = []
    #awards = Awards.query.all()
   
    #user mode support
    if users == 'users':
        players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'users')
        all_players = players.all()
        user_standings = []
        if all_players:
            for standing in get_user_standings():
                for user_player in all_players:
                    if user_player.id == standing.user_id:
                        total_chronicles = 0
                        total_counter = 0
                        total_knowledge = 0
                        # counter_exist = ctk_countermeasure_scores(mode='user',account_id=standing.user_id)
                        # doc_exist = ctk_writeups_scores(mode='user',account_id=standing.user_id)
                        published = db.session.query(docs_publish).first()
                        #if published.countermeasure_published == True or ctk_directorate_mode():
                        # if published.countermeasure_published == True:
                        #     #countermeasures
                        #     counter_exist = ctk_directorate_averageScore_countermeasures(mode='user',account_id=standing.user_id)
                        #     for cgrade in counter_exist['data']:
                        #                 total_counter = total_counter+int(cgrade['average'])
                        #     #chronicles
                        #     doc_exist = ctk_directorate_averageScore_chronicles(mode='user', account_id=standing.user_id)
                        #     for grade in doc_exist['data']:
                        #                 total_chronicles = total_chronicles+int(grade['average'])
                        #     #knowledge-well
                        #     knowledge_exist = ctk_directorate_averageScore_knowledge(mode='user', account_id=standing.user_id)
                        #     for knowledge in knowledge_exist['data']:
                        #                 total_knowledge = total_knowledge+int(knowledge['average'])
                        # total_scores = decimal.Decimal(standing.score) + total_counter +  total_chronicles + total_knowledge
                        #if published.countermeasure_published == True or ctk_directorate_mode() == True:    #countermeasure
                        if published.countermeasure_published == True:
                            # counter_exist = ctk_directorate_averageScore_countermeasures(mode='team',account_id=standing.team_id)
                            # for cgrade in counter_exist['data']:
                            #             total_counter = total_counter+int(cgrade['average'])
                            total_counter = ctk_countermeasure_scores(mode='user',account_id=standing.user_id)
                            #chronicles
                            # doc_exist = ctk_directorate_averageScore_chronicles(mode='team', account_id=standing.team_id)
                            # for grade in doc_exist['data']:
                            #             total_chronicles = total_chronicles+int(grade['average'])
                            total_chronicles = ctk_writeups_scores(mode='user', account_id=standing.user_id)
                            #knowledge-well
                            # knowledge_exist = ctk_directorate_averageScore_knowledge(mode='team', account_id=standing.team_id)
                            # for knowledge in knowledge_exist['data']:
                            #             total_knowledge = total_knowledge+int(knowledge['average'])
                            total_knowledge = ctk_knowledge_scores(mode='user', account_id=standing.user_id)
                        total_scores = decimal.Decimal(standing.score) +  total_counter +  total_chronicles + total_knowledge
                        #awards
                        # for award in awards:
                        #     ctk_user = Users.query.filter_by(id=award.user_id, user_id=standing.user_id).first()
                        #     if ctk_user != None:
                        #         if award.user_id == ctk_user.id:
                        #             total_scores = total_scores + (award.value)
                        flag = Users.query.filter(Users.id == standing.user_id).first()
                        user_standings.append({
                            'account_id': standing.user_id,
                            'name': standing.name,
                            'score': total_scores,
                            'country': flag.country
                        })
        standings = {
            'users': sorted(user_standings , key=lambda x: x['score'], reverse=True),
        }
            
    #team mode support
    if users == 'teams':
        for standing in get_team_standings():
            total_chronicles = 0
            total_counter = 0
            total_knowledge = 0
            published = db.session.query(docs_publish).first()
            #if published.countermeasure_published == True or ctk_directorate_mode() == True:    #countermeasure
            if published.countermeasure_published == True:
                # counter_exist = ctk_directorate_averageScore_countermeasures(mode='team',account_id=standing.team_id)
                # for cgrade in counter_exist['data']:
                #             total_counter = total_counter+int(cgrade['average'])
                total_counter = ctk_countermeasure_scores(mode='team',account_id=standing.team_id)
                #chronicles
                # doc_exist = ctk_directorate_averageScore_chronicles(mode='team', account_id=standing.team_id)
                # for grade in doc_exist['data']:
                #             total_chronicles = total_chronicles+int(grade['average'])
                total_chronicles = ctk_writeups_scores(mode='team', account_id=standing.team_id)
                #knowledge-well
                # knowledge_exist = ctk_directorate_averageScore_knowledge(mode='team', account_id=standing.team_id)
                # for knowledge in knowledge_exist['data']:
                #             total_knowledge = total_knowledge+int(knowledge['average'])
                total_knowledge = ctk_knowledge_scores(mode='team', account_id=standing.team_id)
            total_scores = decimal.Decimal(standing.score) +  total_counter +  total_chronicles + total_knowledge
            #awards
            # for award in awards:
            #     ctk_team = Users.query.filter_by(id=award.user_id, team_id=standing.team_id).first()
            #     if ctk_team != None:
            #         if award.user_id == ctk_team.id:
            #             total_scores = total_scores + (award.value)
            #final score
            flag = Teams.query.filter(Teams.id == standing.team_id).first()
            total_standings.append({
            'account_id': standing.team_id,
            'name': standing.name,
            'score': total_scores,
            'country': flag.country
            })
        standings = {
            'overall': sorted(total_standings , key=lambda x: x['score'], reverse=True),
        }

    return standings

#get user standings
def get_user_score(users=None, c3=None):
    #user mode support
    if ctk_users_mode():
        user_standings = []
        if users:
            for standing in custom_get_user_standings(c3=c3):
                for user_player in users:
                    if user_player.id == standing.user_id:
                        user_standings.append({
                            'user_id': standing.user_id,
                            'name': standing.name,
                            'score': standing.score
                        })
        standings = {
            'overall': sorted(user_standings , key=lambda x: x['score'], reverse=True),
        }
    
    #Directorate mode support
    if ctk_directorate_mode():
        user_standings = []
        if users:
            for standing in custom_get_user_standings(c3=c3):
                for user_player in users:
                    if user_player.id == standing.user_id:
                        user_standings.append({
                            'user_id': standing.user_id,
                            'name': standing.name,
                            'score': standing.score
                        })
        standings = {
            'overall': sorted(user_standings , key=lambda x: x['score'], reverse=True),
        }
    return standings['overall']

#category class
def get_category():
    ctf_cat = db.session.query(C3_category).first()
    if ctf_cat is None:
        #Add default data of the C3_category
        db.session.add_all([
        C3_category(category = "Apprentice"),
        C3_category(category = "Warrior"),
        C3_category(category = "Conqueror")
        ])
        db.session.commit()
        return db.session.query(C3_category).order_by(C3_category.id.asc()).all()
    else:
        return db.session.query(C3_category).order_by(C3_category.id.asc()).all()
    
#ovveride load chalenges under challenge listing
def get_challenges():
    if not is_admin():
        if not ctftime():
            if view_after_ctf():
                pass
            else:
                return []
   
    if challenges_visible() and (ctf_started() or is_admin()):
        #user mode support
        if ctk_users_mode():
           #get challenges
            chals = ctk_challenge(mode='user')
        #teams mode
        if ctk_teams_mode():
            #get challenges
            chals = ctk_challenge(mode='team')
        #Direcorate
        if ctk_directorate_mode():
            chals = ctk_challenge(mode='user')
        #sort out result
        jchals = []
        results = []
        for x in chals:
            prereq = []
            if x.requirements is None:
                req = x.requirements
            else:
                # req = json.loads( x.requirements )
                req = json.dumps( x.requirements )
                req = json.loads(req)
                for reqs in req['prerequisites']:
                    if reqs:
                        val = int(reqs)
                        prereq.append({
                            'id':val
                        })
            jchals.append({
                'id': x.id,
                'name': x.name,
                'value': x.value,
                'category': x.category,
                'description': x.description,
                'requirements': prereq,
                'category_image': '',
                "category_desc": ''
            })
        # Sort into groups
        xxcat = []
        categories = set(map(lambda x: x['category'], jchals))
        for xcat in categories:
            exist = db.session.query(C3ChallengeCategory).filter_by(category_name=xcat).first()
            if exist:
                xx = vars(exist)
                xxcat.append({
                'name': xcat,
                'desc': xx['description'],
                'image_name': xx['image_name'],
                'loc': xx['location']
                })
        jchals = [j for c in xxcat for j in jchals if j['category'] == c['name']]
        results.append({
            'categories': xxcat,
            'challenges': jchals
        })
        return results
    return []

#custom scoreboard standings c3 Category
@cache.memoize(timeout=60)
def custom_get_standings(count=None, admin=False, fields=None, c3=None, chronicles=False):
    """
    Get standings as a list of tuples containing account_id, name, and score e.g. [(account_id, team_name, score)].

    Ties are broken by who reached a given score first based on the solve ID. Two users can have the same score but one
    user will have a solve ID that is before the others. That user will be considered the tie-winner.

    Challenges & Awards with a value of zero are filtered out of the calculations to avoid incorrect tie breaks.
    """
    if fields is None:
        fields = []
    Model = ctk_get_model()
    
    #integrate CTK Players Mode
    #Teams Mode
    if ctk_teams_mode():
        scores = (
            db.session.query(
                Solves.team_id.label("account_id"),
                db.func.sum(C3CategoryChallenge.value).label("score"),
                db.func.max(Solves.id).label("id"),
                db.func.max(Solves.date).label("date")
            )
            .join(C3CategoryChallenge)
            .filter(C3CategoryChallenge.value != 0)
            .filter(C3CategoryChallenge.c3_category == c3)
            .group_by(Solves.team_id)
        )

        awards = (
            db.session.query(
                Awards.team_id.label("account_id"),
                db.func.sum(Awards.value).label("score"),
                db.func.max(Awards.id).label("id"),
                db.func.max(Awards.date).label("date"),
            )
            .filter(Awards.value != 0)
            .group_by(Awards.team_id)
        )

    #Users Mode
    if ctk_users_mode():
        scores = (
            db.session.query(
                Solves.user_id.label("account_id"),
                db.func.sum(C3CategoryChallenge.value).label("score"),
                db.func.max(Solves.id).label("id"),
                db.func.max(Solves.date).label("date")
            )
            .join(C3CategoryChallenge)
            .filter(C3CategoryChallenge.value != 0)
            .filter(C3CategoryChallenge.c3_category == c3)
            .group_by(Solves.user_id)
        )

        awards = (
            db.session.query(
                Awards.user_id.label("account_id"),
                db.func.sum(Awards.value).label("score"),
                db.func.max(Awards.id).label("id"),
                db.func.max(Awards.date).label("date"),
            )
            .filter(Awards.value != 0)
            .group_by(Awards.user_id)
        )

    """
    Filter out solves and awards that are before a specific time point.
    """
    freeze = get_config("freeze")
    if not admin and freeze:
        scores = scores.filter(Solves.date < unix_time_to_utc(freeze))
        awards = awards.filter(Awards.date < unix_time_to_utc(freeze))

    """
    Combine awards and solves with a union. They should have the same amount of columns
    """
    results = union_all(scores, awards).alias("results")

    """
    Sum each of the results by the team id to get their score.
    """
    sumscores = (
        db.session.query(
            results.columns.account_id,
            db.func.sum(results.columns.score).label("score"),
            db.func.max(results.columns.id).label("id"),
            db.func.max(results.columns.date).label("date"),
        )
        .group_by(results.columns.account_id)
        .subquery()
    )

    """
    Admins can see scores for all users but the public cannot see banned users.

    Filters out banned users.
    Properly resolves value ties by ID.

    Different databases treat time precision differently so resolve by the row ID instead.
    """
    if admin:
        standings_query = (
            db.session.query(
                Model.id.label("account_id"),
                Model.oauth_id.label("oauth_id"),
                Model.name.label("name"),
                Model.hidden,
                Model.banned,
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Model.id == sumscores.columns.account_id)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )
    else:
        standings_query = (
            db.session.query(
                Model.id.label("account_id"),
                Model.oauth_id.label("oauth_id"),
                Model.name.label("name"),
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Model.id == sumscores.columns.account_id)
            .filter(Model.banned == False, Model.hidden == False)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )

    """
    Only select a certain amount of users if asked.
    """
    if count is None:
        standings = standings_query.all()
    else:
        standings = standings_query.limit(count).all()
    #integrate cyber exercise chronicles
    if chronicles:
        total_standings = []
        for standing in standings:
            #team mode support
            if ctk_teams_mode():
                doc_exist = db.session.query(
                    db.func.sum(ChallengeWriteUps.points)
                    ).join(C3CategoryChallenge).filter(ChallengeWriteUps.team_id == standing.account_id).filter(C3CategoryChallenge.c3_category == c3).scalar()
            #user mode support
            if ctk_users_mode():
                doc_exist = db.session.query(
                    db.func.sum(ChallengeWriteUps.points)
                    ).join(C3CategoryChallenge).filter(ChallengeWriteUps.user_id == standing.account_id).filter(C3CategoryChallenge.c3_category == c3).scalar()
            #total scores and chronicles
            if doc_exist is None:
                doc_exist = 0
            total_scores = decimal.Decimal(standing.score) + decimal.Decimal(doc_exist)
            total_standings.append({
                'account_id': standing.account_id,
                'name': standing.name,
                'score': total_scores
            })
        return total_standings
    return standings

#custom scoreboard standings Multiple Choice
@cache.memoize(timeout=60)
def multiple_custom_get_standings(count=None, admin=False, fields=None, c3=None, chronicles=False):
    """
    Get standings as a list of tuples containing account_id, name, and score e.g. [(account_id, team_name, score)].

    Ties are broken by who reached a given score first based on the solve ID. Two users can have the same score but one
    user will have a solve ID that is before the others. That user will be considered the tie-winner.

    Challenges & Awards with a value of zero are filtered out of the calculations to avoid incorrect tie breaks.
    """
    if fields is None:
        fields = []
    Model = get_model()

    scores = (
        db.session.query(
            Solves.account_id.label("account_id"),
            db.func.sum(C3CategoryChallenge.value).label("score"),
            db.func.max(Solves.id).label("id"),
            db.func.max(Solves.date).label("date")
        )
        .join(C3CategoryChallenge, MultiChallenge)
        .filter(C3CategoryChallenge.value != 0)
        .filter(MultiChallenge.c3_category == c3)
        .group_by(Solves.account_id)
    )

    awards = (
        db.session.query(
            Awards.account_id.label("account_id"),
            db.func.sum(Awards.value).label("score"),
            db.func.max(Awards.id).label("id"),
            db.func.max(Awards.date).label("date"),
        )
        .filter(Awards.value != 0)
        .group_by(Awards.account_id)
    )

    """
    Filter out solves and awards that are before a specific time point.
    """
    freeze = get_config("freeze")
    if not admin and freeze:
        scores = scores.filter(Solves.date < unix_time_to_utc(freeze))
        awards = awards.filter(Awards.date < unix_time_to_utc(freeze))

    """
    Combine awards and solves with a union. They should have the same amount of columns
    """
    results = union_all(scores, awards).alias("results")

    """
    Sum each of the results by the team id to get their score.
    """
    sumscores = (
        db.session.query(
            results.columns.account_id,
            db.func.sum(results.columns.score).label("score"),
            db.func.max(results.columns.id).label("id"),
            db.func.max(results.columns.date).label("date"),
        )
        .group_by(results.columns.account_id)
        .subquery()
    )

    """
    Admins can see scores for all users but the public cannot see banned users.

    Filters out banned users.
    Properly resolves value ties by ID.

    Different databases treat time precision differently so resolve by the row ID instead.
    """
    if admin:
        standings_query = (
            db.session.query(
                Model.id.label("account_id"),
                Model.oauth_id.label("oauth_id"),
                Model.name.label("name"),
                Model.hidden,
                Model.banned,
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Model.id == sumscores.columns.account_id)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )
    else:
        standings_query = (
            db.session.query(
                Model.id.label("account_id"),
                Model.oauth_id.label("oauth_id"),
                Model.name.label("name"),
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Model.id == sumscores.columns.account_id)
            .filter(Model.banned == False, Model.hidden == False)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )

    """
    Only select a certain amount of users if asked.
    """
    if count is None:
        standings = standings_query.all()
    else:
        standings = standings_query.limit(count).all()
    #integrate cyber exercise chronicles
    if chronicles:
        total_standings = []
        for standing in standings:
            #team mode support
            if ctk_teams_mode():
                doc_exist = db.session.query(
                    db.func.sum(ChallengeWriteUps.points)
                    ).join(MultiChallenge).filter(ChallengeWriteUps.team_id == standing.account_id).filter(MultiChallenge.c3_category == c3).scalar()
            #user mode support
            if ctk_users_mode():
                doc_exist = db.session.query(
                    db.func.sum(ChallengeWriteUps.points)
                    ).join(MultiChallenge).filter(ChallengeWriteUps.user_id == standing.account_id).filter(MultiChallenge.c3_category == c3).scalar()
            #total scores and chronicles
            if doc_exist is None:
                doc_exist = 0
            total_scores = decimal.Decimal(standing.score) + decimal.Decimal(doc_exist)
            total_standings.append({
                'account_id': standing.account_id,
                'name': standing.name,
                'score': total_scores
            })
        return total_standings
    return standings

@cache.memoize(timeout=60)
def custom_get_user_standings(count=None, admin=False, fields=None, c3=None):
    if fields is None:
        fields = []
    scores = (
        db.session.query(
            Solves.user_id.label("user_id"),
            db.func.sum(C3CategoryChallenge.value).label("score"),
            db.func.max(Solves.id).label("id"),
            db.func.max(Solves.date).label("date"),
        )
        .join(C3CategoryChallenge)
        .filter(C3CategoryChallenge.value != 0)
        .filter(C3CategoryChallenge.c3_category == c3)
        .group_by(Solves.user_id)
    )
    awards = (
        db.session.query(
            Awards.user_id.label("user_id"),
            db.func.sum(Awards.value).label("score"),
            db.func.max(Awards.id).label("id"),
            db.func.max(Awards.date).label("date"),
        )
        .filter(Awards.value != 0)
        .group_by(Awards.user_id)
    )

    freeze = get_config("freeze")
    if not admin and freeze:
        scores = scores.filter(Solves.date < unix_time_to_utc(freeze))
        awards = awards.filter(Awards.date < unix_time_to_utc(freeze))

    results = union_all(scores, awards).alias("results")

    sumscores = (
        db.session.query(
            results.columns.user_id,
            db.func.sum(results.columns.score).label("score"),
            db.func.max(results.columns.id).label("id"),
            db.func.max(results.columns.date).label("date"),
        )
        .group_by(results.columns.user_id)
        .subquery()
    )

    if admin:
        standings_query = (
            db.session.query(
                Users.id.label("user_id"),
                Users.oauth_id.label("oauth_id"),
                Users.name.label("name"),
                Users.team_id.label("team_id"),
                Users.hidden,
                Users.banned,
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Users.id == sumscores.columns.user_id)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )
    else:
        standings_query = (
            db.session.query(
                Users.id.label("user_id"),
                Users.oauth_id.label("oauth_id"),
                Users.name.label("name"),
                Users.team_id.label("team_id"),
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Users.id == sumscores.columns.user_id)
            .filter(Users.banned == False, Users.hidden == False)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )

    if count is None:
        standings = standings_query.all()
    else:
        standings = standings_query.limit(count).all()
    
    return standings

#Get C3 Category data
def get_c3_category(id=None):
    results = []
    if(id):
        doc_exist = db.session.query(C3_category).filter_by(id = id).first()
        if(doc_exist):
            c3_data = vars(doc_exist)
            results.append({
                'id': c3_data['id'],
                'category': c3_data['category'],
                'description': c3_data['description'],
                'location': c3_data['location'] 
            })
            return results
    return results

#get category challenges
def get_cat_chals():
    results = []
    doc_exist = db.session.query(C3ChallengeCategory).order_by(C3ChallengeCategory.id.asc()).all()
    if doc_exist:
        for x in doc_exist:
            results.append({
                'id': x.id,
                'type': x.type,
                'category_name': x.category_name,
                'description': x.description,
                'image_name': x.image_name,
                'location': x.location
            })
        return results       
    return results

#apprentice progress status
def get_ctk_cat_status(c3=None, id=None, mode=None):
    results = []
    frank = None
    user = get_current_user()
    #user mode support
    if ctk_users_mode():
        chals = ctk_total_challenge(mode='user',c3=c3)
        solves = db.session.query(
                        Solves
                    ).join(C3CategoryChallenge
                    ).filter(Solves.user_id == user.id
                    ).filter(C3CategoryChallenge.id == Solves.challenge_id
                    ).filter(C3CategoryChallenge.c3_category == c3
                    ).count()
        
        #players = db.session.query(Teams).filter(Teams.hidden!=1).count()
        players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'users')
        all_players = players.all()
        players = players.count()
        rank = overall_score(users=all_players)
        for i, player_rank in enumerate(rank['overall']):
            if player_rank['account_id'] == user.id:
                frank = i+1
    #team mode support
    if ctk_teams_mode():
        chals = ctk_total_challenge(mode='team',c3=c3)
        solves = db.session.query(
                        Solves
                    ).join(C3CategoryChallenge
                    ).filter(Solves.team_id == user.team_id
                    ).filter(C3CategoryChallenge.id == Solves.challenge_id
                    ).filter(C3CategoryChallenge.c3_category == c3
                    ).count()
        # players = db.session.query(Teams).filter(Teams.hidden!=1, Teams.banned!=1).count() | Mysql
        players = db.session.query(Teams).filter(Teams.hidden==False, Teams.banned==False).count()
        rank = overall_score()
        for i, player_rank in enumerate(rank['overall']):
            if player_rank['account_id'] == user.team_id:
                frank = i+1

    #Directorate mode support
    if ctk_directorate_mode():
        chals = ctk_total_challenge(mode='user',c3=c3)
        solves = db.session.query(
                        Solves
                    ).join(C3CategoryChallenge
                    ).filter(Solves.user_id == user.id
                    ).filter(C3CategoryChallenge.id == Solves.challenge_id
                    ).filter(C3CategoryChallenge.c3_category == c3
                    ).count()
        #players = db.session.query(Teams).filter(Teams.hidden!=1).count()
        players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'directorate')
        all_players = players.all()
        players = players.count()
        rank = overall_score(users=all_players)
        for i, player_rank in enumerate(rank['overall']):
            if player_rank['account_id'] == user.id:
                frank = i+1

    #admin progress monitoring
    if is_admin():
        if id is None:
            user = get_current_user()
            account_id = user.id
        else:
            account_id = id
        
        if mode=='team':
            chals = ctk_total_challenge(mode='team',c3=c3)
            solves = db.session.query(
                            Solves
                        ).join(C3CategoryChallenge
                        ).filter(Solves.team_id == account_id
                        ).filter(C3CategoryChallenge.id == Solves.challenge_id
                        ).filter(C3CategoryChallenge.c3_category == c3
                        ).count()
            # players = db.session.query(Teams).filter(Teams.hidden!=1, Teams.banned!=1).count() | Mysql
            players = db.session.query(Teams).filter(Teams.hidden==False, Teams.banned==False).count()
            rank = overall_score()
            for i, player_rank in enumerate(rank['overall']):
                if player_rank['account_id'] == account_id:
                    frank = i+1

        if mode=='user':
            chals = ctk_total_challenge(mode='user',c3=c3)
            solves = db.session.query(
                            Solves
                        ).join(C3CategoryChallenge
                        ).filter(Solves.user_id == account_id
                        ).filter(C3CategoryChallenge.id == Solves.challenge_id
                        ).filter(C3CategoryChallenge.c3_category == c3
                        ).count()
            #players = db.session.query(Teams).filter(Teams.hidden!=1).count()
            players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'users')
            all_players = players.all()
            players = players.count()
            rank = overall_score(users=all_players)
            for i, player_rank in enumerate(rank['overall']):
                if player_rank['account_id'] == account_id:
                    frank = i+1
            
                
    #validation if challenge is not yet set    
    if chals == 0:
        quotient = 0
    else:
        quotient = solves / chals
    percent = quotient * 100
    #lock game category default false to Apprentice
    if c3 == 1:
        lock = False
    else:
        #apprentice
        if solves == chals:
            lock = False
        lock = True
        
    results.append({
        'total_chals':chals,
        'total_solves':solves,
        'progress': int(percent),
        'total_player': players,
        'rank': frank,
        'lock': lock
    })
    return results

#create rensom for unique directory
def id_generator(size=10, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

#get score c3_category
def get_team_score(team_id,c3,date):
        t = []
        score = db.func.sum(C3CategoryChallenge.value).label("score")
        solves_date = db.session.query(
                Solves.team_id,
                Submissions.date,
                score
        ).join(C3CategoryChallenge).filter(C3CategoryChallenge.id == Solves.challenge_id).filter(Solves.team_id == team_id).filter(C3CategoryChallenge.c3_category == c3).filter(Solves.date <= date)
        award_score = db.func.sum(Awards.value).label("award_score")
        award = db.session.query(award_score).filter_by(team_id=team_id)
        team = solves_date.group_by(Solves.team_id).first()
        award = award.first()
        if team and award:
            return int(team.score or 0) + int(award.award_score or 0)
        elif team:
            return int(team.score or 0)
        elif award:
            return int(award.award_score or 0)
        else:
            return 0

def get_user_score_date(user_id,c3,date):
        t = []
        score = db.func.sum(C3CategoryChallenge.value).label("score")
        solves_date = db.session.query(
                Solves.user_id,
                Solves.date,
                score
        ).join(C3CategoryChallenge).filter(C3CategoryChallenge.id == Solves.challenge_id).filter(Solves.user_id == user_id).filter(C3CategoryChallenge.c3_category == c3).filter(Solves.date <= date)
        award_score = db.func.sum(Awards.value).label("award_score")
        award = db.session.query(award_score).filter_by(user_id=user_id)
        user = solves_date.group_by(Solves.user_id).first()
        award = award.first()
        if user and award:
            return int(user.score or 0) + int(award.award_score or 0)
        elif user:
            return int(user.score or 0)
        elif award:
            return int(award.award_score or 0)
        else:
            return 0


def total_custom_standing(cat=None):
    result = []
    C3_category = custom_get_standings(c3=cat)
    multiple = multiple_custom_get_standings(c3=cat)
    for c3  in C3_category:
        for mul in multiple:
            if c3.account_id == mul.account_id:
                result.append({
                    'account_id': c3.account_id,
                    'score': c3.score + mul.score,
                    'name': c3.name
                })
            else:
                result.append({
                    'account_id': c3.account_id,
                    'score': c3.score,
                    'name': c3.name
                })
    # total_standing = C3_category + multiple
    return  result

#cyber ex category lockout
def cyberex_lock(c3=None):
    if is_admin():
        lockout = db.session.query(c3_lockout).filter_by(ctf_category_id = c3).first()
    else:
        user = get_current_user()
        ctk_user = CTK_Config.query.filter_by(id=user.id).first()
        lockout = db.session.query(c3_lockout).filter_by(ctf_category_id = c3).first()
        #Cyber eX Directorates Privileges to access all challenges
        if ctk_user.mode == 'directorate':
            lockout.lockout_percentage = 0
    return lockout

#lockout variables for Cyber eX
def CTK_lockout(id=None, mode=None):
    results = []
    apprentice_lockout = cyberex_lock(c3=1)
    warrior_lockout = cyberex_lock(c3=2)
    conqueror_lockout = cyberex_lock(c3=3)
    results.append({
        'apprentice':get_ctk_cat_status(c3=1,id=id, mode=mode),
        'warrior': get_ctk_cat_status(c3=2, id=id, mode=mode),
        'conqueror': get_ctk_cat_status(c3=3, id=id, mode=mode),
        'apprentice_lockout':apprentice_lockout.lockout_percentage if apprentice_lockout else None,
        'warrior_lockout': warrior_lockout.lockout_percentage if warrior_lockout else None,
        'conqueror_lockout': conqueror_lockout.lockout_percentage if conqueror_lockout else None,
    })
    return results

@cache.memoize(timeout=60)
def get_ctk_team_standings(count=None, admin=False, fields=None, c3=None):
    if fields is None:
        fields = []
    scores = (
            db.session.query(
                Solves.team_id.label("account_id"),
                db.func.sum(C3CategoryChallenge.value).label("score"),
                db.func.max(Solves.id).label("id"),
                db.func.max(Solves.date).label("date")
            )
            .join(C3CategoryChallenge)
            .filter(C3CategoryChallenge.value != 0)
            .filter(C3CategoryChallenge.c3_category == c3)
            .group_by(Solves.team_id)
        )

    awards = (
            db.session.query(
                Awards.team_id.label("account_id"),
                db.func.sum(Awards.value).label("score"),
                db.func.max(Awards.id).label("id"),
                db.func.max(Awards.date).label("date"),
            )
            .filter(Awards.value != 0)
            .group_by(Awards.team_id)
        )

    freeze = get_config("freeze")
    if not admin and freeze:
        scores = scores.filter(Solves.date < unix_time_to_utc(freeze))
        awards = awards.filter(Awards.date < unix_time_to_utc(freeze))

    results = union_all(scores, awards).alias("results")

    sumscores = (
        db.session.query(
            results.columns.account_id,
            db.func.sum(results.columns.score).label("score"),
            db.func.max(results.columns.id).label("id"),
            db.func.max(results.columns.date).label("date"),
        )
        .group_by(results.columns.account_id)
        .subquery()
    )

    if admin:
        standings_query = (
            db.session.query(
                Teams.id.label("team_id"),
                Teams.oauth_id.label("oauth_id"),
                Teams.name.label("name"),
                Teams.hidden,
                Teams.banned,
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Teams.id == sumscores.columns.account_id)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )
    else:
        standings_query = (
            db.session.query(
                Teams.id.label("account_id"),
                Teams.oauth_id.label("oauth_id"),
                Teams.name.label("name"),
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Teams.id == sumscores.columns.account_id)
            .filter(Teams.banned == False)
            .filter(Teams.hidden == False)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )

    if count is None:
        standings = standings_query.all()
    else:
        standings = standings_query.limit(count).all()

    return standings

#branch of service
def ctk_branch():
    units = [
        {
            'name':'Philippine Army',
            'key': 'PA'
        },
         {
            'name':'Philippine Navy',
            'key': 'PN'
        },
        {
            'name':'Philippine Air Force',
            'key': 'PAF'
        },
        {
            'name': 'Armed Forces of the Philippines',
            'key': 'AFP'
        },
        {
            'name': 'Reserve Officers Training Corps',
            'key': 'ROTC'
        },
        {
            'name': 'United States Army Pacific',
            'key': 'USARPAC'
        },
        {
            'name': 'United States Marine Corps Forces Pacific',
            'key': 'MARFORPAC'
        },
        {
            'name': 'United States Pacific Fleet',
            'key': 'USPACFLT'
        },
        {
            'name': 'Pacific Air Forces',
            'key': 'PACAF'
        },
        {
            'name': 'United States Armed Forces',
            'key': 'USAF'
        }
    ]
    return units

#Major Units
def ctk_major_units(maj_units=None):
    units = []
    if maj_units == 'PA':
        units = [
            {
                'name': 'Army Signal Regiment',
                'key': 'ASR'
            },
             {
                'name': 'Civil-Military Operations Regiment',
                'key': 'CMOR'
            },
            {
                'name': 'Army Artillery Regiment',
                'key': 'AAR'
            },
            {
                'name': 'Armor Division',
                'key': 'AD'
            },
            {
                'name': '1st Brigade Combat Team',
                'key': '1BCT'
            },
            {
                'name': 'Army Intelligence Regiment',
                'key': 'AIR'
            }
        ]

    if maj_units == 'AFP':
        units = [
            {
                'name': 'General Headquarters',
                'key': 'GHQ'
            }
        ]
    
    if maj_units == 'USARPAC':
        units = [
            {
                'name': 'Eighth Army',
                'key': '8th_Army'
            },
            {
                'name': 'I Corps',
                'key': 'I_Corps'
            },
            {
                'name': '94th Army Air and Missile Defense Command',
                'key': '94th_AAMDC'
            },
            {
                'name': '8th Theater Sustainment Command',
                'key': '8th_TSC'
            },
            {
                'name': '311th Signal Command',
                'key': '311th_SC'
            },
            {
                'name': '18th Medical Command',
                'key': '18th_MC'
            },
            {
                'name': '9th Mission Support Command',
                'key': '9th_MSC'
            },
            {
                'name': '196th Infantry Brigade',
                'key': '196th_IB'
            },
            {
                'name': '500th Military Intelligence Brigade',
                'key': '500th_MIB'
            },
            {
                'name': '5th Battlefield Coordination Detachment',
                'key': '5th_BCD'
            },
            {
                'name': 'Other Unit',
                'key': ''
            }
        ]
    
    if maj_units == 'MARFORPAC':
        units = [
            {
                'name': 'I Marine Expeditionary Force',
                'key': 'I_MEF'
            },
            {
                'name': 'III Marine Expeditionary Force',
                'key': 'III_MEF'
            },
            {
                'name': 'Marine Corps Base',
                'key': 'MCB'
            },
            {
                'name': 'Marine Rotational Force',
                'key': 'MRF'
            },
            {
                'name': 'Other Unit',
                'key': ''
            }
        ]
    
    if maj_units == 'USPACFLT':
        units = [
            {
                'name': 'United States Third Fleet',
                'key': 'USTHFLT'
            },
            {
                'name': 'United States Seventh Fleet',
                'key': 'USSFLT'
            },
            {
                'name': 'Naval Air Force Pacific',
                'key': 'CNAP'
            },
            {
                'name': 'Naval Surface Force Pacific',
                'key': 'NAVSURFPAC'
            },
            {
                'name': 'Navy Region Hawaii',
                'key': 'CNRH'
            },
            {
                'name': 'Other Unit',
                'key': ''
            }
        ]
    
    if maj_units == 'PACAF':
        units = [
            {
                'name': 'Fifth Air Force',
                'key': '5_AF'
            },
            {
                'name': 'Seventh Air Force',
                'key': '7_AF'
            },
            {
                'name': 'Eleventh Air Force',
                'key': '11_AF'
            },
            {
                'name': '613th Air Operations Center',
                'key': '613_AOC'
            },
            {
                'name': 'Other Unit',
                'key': ''
            }
        ]
        return units
    return units

#Sub Units
def ctk_sub_units(unit=None):
    sub_units = []
    if unit == 'ASR':
        sub_units  = [
            {
                'name':'Headquarters and Headquarters Company',
                'key':'HHC'
            },
            {
                'name':'Signal Installation & Maintenance Battalion',
                'key':'SIMBn'
            },
            {
                'name':'Command Signal Battalion',
                'key':'CSBn'
            },
            {
                'name':'The Signal School',
                'key':'TSS'
            },
            {
                'name':'Network Enterprise & Technology Battalion',
                'key':'NETBn'
            },
            {
                'name': 'Cyber Battalion',
                'key': 'CyberBn'
            },
            {
                'name': '1st Signal Battalion',
                'key': '1SBn'
            },
             {
                'name': '2nd Signal Battalion',
                'key': '2SBn'
            },
            {
                'name': '3rd Signal Battalion',
                'key': '3SBn'
            },
            {
                'name': '4th Signal Battalion',
                'key': '4SBn'
            },
            {
                'name':'5th Signal Battalion',
                'key':'5SBn',
            },
            {
                'name':'6th Signal Battalion',
                'key':'6SBn'
            },
            {
                'name':'7th Signal Battalion',
                'key':'7SBn'
            },
            {
                'name':'8th Signal Battalion',
                'key': '8SBn'
            },
            {
                'name':'9th Signal Battalion',
                'key':'9SBn'
            },
            {
                'name':'10th Signal Battalion',
                'key':'10SBn'
            },
            {
                'name':'11th Signal Battalion',
                'key': '11SBn'
            }
        ]

    if unit == 'AAR':
        sub_units  = [
            {
                'name': 'Office of the General 6',
                'key': 'OG6'
            },
            {
                'name': '1st Field Artillery Battalion',
                'key': '1FABn'
            },
             {
                'name': '2nd Field Artillery Battalion',
                'key': '2FABn'
            },
            {
                'name': '3rd Field Artillery Battalion',
                'key': '3FABn'
            },
            {
                'name': '4th Field Artillery Battalion',
                'key': '4FABn'
            },
            {
                'name':'5th Field Artillery Battalion',
                'key':'5FABn',
            },
            {
                'name':'6th Field Artillery Battalion',
                'key':'6FABn'
            },
            {
                'name':'7th Field Artillery Battalion',
                'key':'7FABn'
            },
            {
                'name':'8th Field Artillery Battalion',
                'key': '8FABn'
            },
            {
                'name':'9th Field Artillery Battalion',
                'key':'9FABn'
            },
            {
                'name':'1st Multiple Launch Rocket System Battery',
                'key':'1MLRS-Btry'
            },
            {
                'name':'2nd Multiple Launch Rocket System Battery',
                'key': '2MLRS-Btry'
            },
            {
                'name':'1st Land-based Missile System Battery',
                'key':'1LBMS-Btry'
            },
            {
                'name':'1st Field Artillery Battery',
                'key':'1FA-Btry'
            },
            {
                'name':'2nd Field Artillery Battery',
                'key':'2FA-Btry'
            },
            {
                'name':'1st Air Defense Artillery Battery',
                'key':'1ADA-Btry'
            },
            {
                'name':'2nd Air Defense Artillery Battery',
                'key':'2ADA-Btry'
            }
        ]

    if unit == 'AD':
        sub_units  = [
            {
                'name': 'Office of the General 6',
                'key': 'OG6'
            },
            {
                'name':'1st Mechanized Infantry (Lakan) Battalion',
                'key':'1MIBn'
            },
            {
                'name':'2nd Mechanized Infantry (Makasag) Battalion',
                'key':'2MIBn'
            },
            {
                'name':'3rd Mechanized Infantry (Makatarungan) Battalion',
                'key':'3MIBn'
            },
            {
                'name':'4th Mechanized Infantry (Kalasag) Battalion',
                'key':'4MIBn'
            },
            {
                'name':'5th Mechanized Infantry (Kaagapay) Battalion',
                'key':'5MIBn'
            },
            {
                'name':'6th Mechanised Infantry (Salaknib) Battalion',
                'key':'6MIBn'
            }
        ]

    if unit == '1BCT':
        sub_units  = [
            {
                'name': 'Office of the General 6',
                'key': 'OG6'
            },
            {
                'name':'Headquarters and Headquarters Company',
                'key':'HHC'
            },
            {
                'name':'45th Infantry "Gallant" Battalion',
                'key':'45InfBn'
            },
            {
                'name':'92nd Infantry "Tanglaw Diwa" Battalion',
                'key':'92InfBn'
            }
        ]

    if unit == 'AIR':
        sub_units  = [
            {
                'name':'15th Army Intelligence Battalion',
                'key':'15AIB'
            },
            {
                'name':'17th Army Intelligence Battalion',
                'key':'17AIB'
            },
            {
                'name':'24th Army Intelligence Battalion',
                'key':'24AIB'
            },
            {
                'name': '1st Intelligence Service Unit',
                'key': '1ISU'
            },
            {
                'name':'2nd Intelligence Service Unit',
                'key':'2ISU'
            },
            {
                'name':'3rd Intelligence Service Unit',
                'key':'3ISU'
            },
            {
                'name':'4th Intelligence Service Unit',
                'key':'4ISU'
            },
            {
                'name':'5th Intelligence Service Unit',
                'key':'5ISU'
            },
            {
                'name':'7th Intelligence Service Unit',
                'key':'7ISU'
            },
            {
                'name':'8th Intelligence Service Unit',
                'key':'8ISU'
            },
            {
                'name':'9th Intelligence Service Unit',
                'key':'9ISU'
            },
            {
                'name':'10th Intelligence Service Unit',
                'key':'10ISU'
            },
            {
                'name':'11th Intelligence Service Unit',
                'key':'11ISU'
            },
            {
                'name':'12th Intelligence Service Unit',
                'key':'12ISU'
            },
            {
                'name':'14th Intelligence Service Unit',
                'key':'14ISU'
            },
            {
                'name':'15th Intelligence Service Unit',
                'key':'15ISU'
            },
            {
                'name':'16th Intelligence Service Unit',
                'key':'16ISU'
            },
            {
                'name':'17th Intelligence Service Unit',
                'key':'17ISU'
            },
            {
                'name':'22nd Intelligence Service Unit',
                'key':'22ISU'
            },
            {
                'name':'24th Intelligence Service Unit',
                'key':'24ISU'
            }
            
        ]
    if unit == 'GHQ':
        sub_units  = [
            {
                'name': 'Cyber Group',
                'key': 'CYG'
            }
    ]
    
   # if unit == '8th_Army':
    #    sub_units  = [
    #        {
     #           'name': 'Headquarters & Headquarters Company',
     #           'key': 'HHCO'
      #      },
      #      {
      #          'name': '2nd Infantry Division',
       #         'key': '2ID'
      #      },
       #     {
       #         'name': '17th Aviation Brigade',
       #         'key': '17th_AB'
        #    }
   # ]
    return sub_units

#all time users scorebaord
@cache.memoize(timeout=60)
def get_alltimeuser_standings(count=None, admin=False, fields=None):
    if fields is None:
        fields = []

    players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'users')
    all_players = players.all()
    user_ids = [user.id for user in all_players]
    scores = (
        db.session.query(
            Solves.user_id.label("user_id"),
            db.func.sum(C3CategoryChallenge.value).label("score"),
            db.func.max(Solves.id).label("id"),
            db.func.max(Solves.date).label("date"),
        )
        .join(C3CategoryChallenge)
        .filter(C3CategoryChallenge.value != 0)
        .filter(Solves.user_id.in_(user_ids))
        .group_by(Solves.user_id)
    )

    awards = (
        db.session.query(
            Awards.user_id.label("user_id"),
            db.func.sum(Awards.value).label("score"),
            db.func.max(Awards.id).label("id"),
            db.func.max(Awards.date).label("date"),
        )
        .filter(Awards.value != 0)
        .group_by(Awards.user_id)
    )

    freeze = get_config("freeze")
    if not admin and freeze:
        scores = scores.filter(Solves.date < unix_time_to_utc(freeze))
        awards = awards.filter(Awards.date < unix_time_to_utc(freeze))

    results = union_all(scores, awards).alias("results")

    sumscores = (
        db.session.query(
            results.columns.user_id,
            db.func.sum(results.columns.score).label("score"),
            db.func.max(results.columns.id).label("id"),
            db.func.max(results.columns.date).label("date"),
        )
        .group_by(results.columns.user_id)
        .subquery()
    )

    if admin:
        standings_query = (
            db.session.query(
                Users.id.label("user_id"),
                Users.oauth_id.label("oauth_id"),
                Users.name.label("name"),
                Users.team_id.label("team_id"),
                Users.hidden,
                Users.banned,
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Users.id == sumscores.columns.user_id)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )
    else:
        standings_query = (
            db.session.query(
                Users.id.label("user_id"),
                Users.oauth_id.label("oauth_id"),
                Users.name.label("name"),
                Users.team_id.label("team_id"),
                sumscores.columns.score,
                *fields,
            )
            .join(sumscores, Users.id == sumscores.columns.user_id)
            .filter(Users.banned == False, Users.hidden == False)
            .order_by(sumscores.columns.score.desc(), sumscores.columns.id)
        )

    if count is None:
        standings = standings_query.all()
    else:
        standings = standings_query.limit(count).all()

    return standings


#get the average score
def ctk_directorate_averageScore_chronicles(mode, account_id):
    result = {}
    if mode == 'team':
        team = Teams.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = team.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.team_id==account_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        chronicles_ids = [chronicle.id for chronicle in chronicles]
        graded = ChroniclesDirectorate.query.filter(ChroniclesDirectorate.writeups_id.in_(chronicles_ids)).all()
        graded_ids = [directorate.writeups_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_chronicles = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_chronicles.append({
                    'writeups_id': grade.writeups_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_points,
            })
            total_rater.append({
                'writeups_id': grade.writeups_id,
                'rater': graded_chronicles
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['writeups_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'writeups_id': list_rated['writeups_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    #user
    if mode == 'user':
        user = Users.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = user.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.user_id==account_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        chronicles_ids = [chronicle.id for chronicle in chronicles]
        graded = ChroniclesDirectorate.query.filter(ChroniclesDirectorate.writeups_id.in_(chronicles_ids)).all()
        graded_ids = [directorate.writeups_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_chronicles = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_chronicles.append({
                    'writeups_id': grade.writeups_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_points,
            })
            total_rater.append({
                'writeups_id': grade.writeups_id,
                'rater': graded_chronicles
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['writeups_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'writeups_id': list_rated['writeups_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    return {"success": True, "data": result}

#average countermeasures
def ctk_directorate_averageScore_countermeasures(mode, account_id):
    result = {}
    if mode == 'team':
        team = Teams.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = team.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        countermeasure = ChallengeCounterMeasure.query.filter(ChallengeCounterMeasure.team_id==account_id, ChallengeCounterMeasure.challenge_id.in_(challenge_solved)).all()
        countermeasure_ids = [counter.id for counter in countermeasure]
        graded = CountermeasureDirectorate.query.filter(CountermeasureDirectorate.countermeasures_id.in_(countermeasure_ids)).all()
        graded_ids = [directorate.countermeasures_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_countermeasures = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_countermeasures.append({
                    'countermeasures_id': grade.countermeasures_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_points,
            })
            total_rater.append({
                'countermeasures_id': grade.countermeasures_id,
                'rater': graded_countermeasures
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['countermeasures_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'countermeasures_id': list_rated['countermeasures_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    #user
    if mode == 'user':
        user = Users.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = user.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        countermeasure = ChallengeCounterMeasure.query.filter(ChallengeCounterMeasure.user_id==account_id, ChallengeCounterMeasure.challenge_id.in_(challenge_solved)).all()
        countermeasure_ids = [counter.id for counter in countermeasure]
        graded = CountermeasureDirectorate.query.filter(CountermeasureDirectorate.countermeasures_id.in_(countermeasure_ids)).all()
        graded_ids = [directorate.countermeasures_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_countermeasures = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_countermeasures.append({
                    'countermeasures_id': grade.countermeasures_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_points,
            })
            total_rater.append({
                'countermeasures_id': grade.countermeasures_id,
                'rater': graded_countermeasures
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['countermeasures_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'countermeasures_id': list_rated['countermeasures_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count 
    return {"success": True, "data": result}

#average knowledge-well
def ctk_directorate_averageScore_knowledge(mode, account_id):
    result = {}
    if mode == 'team':
        team = Teams.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = team.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        knowledges = KnowledgeWellDocs.query.filter(KnowledgeWellDocs.team_id==account_id, KnowledgeWellDocs.challenge_id.in_(challenge_solved)).all()
        knowledge_ids = [knowledge.id for knowledge in knowledges]
        graded = KnowledgeDirectorate.query.filter(KnowledgeDirectorate.knowledge_id.in_(knowledge_ids)).all()
        graded_ids = [directorate.knowledge_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_knowledge = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_knowledge.append({
                    'knowledge_id': grade.knowledge_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_points,
            })
            total_rater.append({
                'knowledge_id': grade.knowledge_id,
                'rater': graded_knowledge
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['knowledge_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'knowledge_id': list_rated['knowledge_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    #user
    if mode == 'user':
        user = Users.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = user.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        knowledges = KnowledgeWellDocs.query.filter(KnowledgeWellDocs.user_id==account_id, KnowledgeWellDocs.challenge_id.in_(challenge_solved)).all()
        knowledge_ids = [knowledge.id for knowledge in knowledges]
        graded = KnowledgeDirectorate.query.filter(KnowledgeDirectorate.knowledge_id.in_(knowledge_ids)).all()
        graded_ids = [directorate.knowledge_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_chronicles = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_chronicles.append({
                    'knowledge_id': grade.knowledge_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_points,
            })
            total_rater.append({
                'knowledge_id': grade.knowledge_id,
                'rater': graded_chronicles
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['knowledge_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'knowledge_id': list_rated['knowledge_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    return {"success": True, "data": result}

#documentation submission
def docs_graded(mode, account_id):
    user = get_current_user()
    data = {}

    #multiplayer
    if mode=='team':
        #team Knowledge Well
        knowledge_well = KnowledgeWellDocs.query.filter(KnowledgeWellDocs.team_id==account_id)
        total_submission_knowledge = knowledge_well.count()
        total_knowledge = knowledge_well.all()
        knowledge_ids = [knowledge.id for knowledge in total_knowledge]
        graded_knowledge = KnowledgeDirectorate.query.filter(KnowledgeDirectorate.directorate_id==user.id, KnowledgeDirectorate.knowledge_id.in_(knowledge_ids)).count()
        #teams chronicles
        chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.team_id==account_id)
        total_submission = chronicles.count()
        total_chronicles = chronicles.all()
        chronicles_ids = [chronicle.id for chronicle in total_chronicles]
        graded_chronicles = ChroniclesDirectorate.query.filter(ChroniclesDirectorate.directorate_id==user.id, ChroniclesDirectorate.writeups_id.in_(chronicles_ids)).count()
        #team countermeasures
        countermeasure = ChallengeCounterMeasure.query.filter(ChallengeCounterMeasure.team_id==account_id)
        total_submission_counter =  countermeasure.count()
        total_counter = countermeasure.all()
        counter_ids = [counterm.id for counterm in total_counter]
        graded_counter = CountermeasureDirectorate.query.filter( CountermeasureDirectorate.directorate_id==user.id,  CountermeasureDirectorate.countermeasures_id.in_(counter_ids)).count()

    #individuals
    if mode=='user':
        #team Knowledge Well
        knowledge_well = KnowledgeWellDocs.query.filter(KnowledgeWellDocs.user_id==account_id)
        total_submission_knowledge = knowledge_well.count()
        total_knowledge = knowledge_well.all()
        knowledge_ids = [knowledge.id for knowledge in total_knowledge]
        graded_knowledge = KnowledgeDirectorate.query.filter(KnowledgeDirectorate.directorate_id==user.id, KnowledgeDirectorate.knowledge_id.in_(knowledge_ids)).count()
        #teams chronicles
        chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.user_id==account_id)
        total_submission = chronicles.count()
        total_chronicles = chronicles.all()
        chronicles_ids = [chronicle.id for chronicle in total_chronicles]
        graded_chronicles = ChroniclesDirectorate.query.filter(ChroniclesDirectorate.directorate_id==user.id, ChroniclesDirectorate.writeups_id.in_(chronicles_ids)).count()
        #team countermeasures
        countermeasure = ChallengeCounterMeasure.query.filter(ChallengeCounterMeasure.user_id==account_id)
        total_submission_counter =  countermeasure.count()
        total_counter = countermeasure.all()
        counter_ids = [counterm.id for counterm in total_counter]
        graded_counter = CountermeasureDirectorate.query.filter( CountermeasureDirectorate.directorate_id==user.id,  CountermeasureDirectorate.countermeasures_id.in_(counter_ids)).count()

    data = {
             'knowledgeWell' : {
                'count': total_submission_knowledge,
                'graded': graded_knowledge,
                'not_graded': (total_submission_knowledge - graded_knowledge)
            },
            'chronicles' : {
                'count':total_submission,
                'graded': graded_chronicles,
                'not_graded': (total_submission - graded_chronicles)
            },
            'countermeasures':{
                'count': total_submission_counter,
                'graded': graded_counter,
                'not_graded': (total_submission_counter - graded_counter)
            }
        }
    return data
#new documentation calculations version 3
def ctk_directorate_averageScore_documentations_do(mode, account_id):
    result = {}
    if mode == 'team':
        team = Teams.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = team.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.team_id==account_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        chronicles_ids = [chronicle.id for chronicle in chronicles]
        graded = DocumentationDirectorate.query.filter(DocumentationDirectorate.writeups_id.in_(chronicles_ids)).all()
        graded_ids = [directorate.writeups_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_chronicles = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_chronicles.append({
                    'writeups_id': grade.writeups_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_do,
            })
            total_rater.append({
                'writeups_id': grade.writeups_id,
                'rater': graded_chronicles
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['writeups_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'writeups_id': list_rated['writeups_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    #user
    if mode == 'user':
        user = Users.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = user.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.user_id==account_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        chronicles_ids = [chronicle.id for chronicle in chronicles]
        graded = DocumentationDirectorate.query.filter(DocumentationDirectorate.writeups_id.in_(chronicles_ids)).all()
        graded_ids = [directorate.writeups_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_chronicles = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_chronicles.append({
                    'writeups_id': grade.writeups_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_do,
            })
            total_rater.append({
                'writeups_id': grade.writeups_id,
                'rater': graded_chronicles
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['writeups_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'writeups_id': list_rated['writeups_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    return {"success": True, "data": result}


def ctk_directorate_averageScore_know(mode, account_id):
    result = {}
    if mode == 'team':
        team = Teams.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = team.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        knowledges = ChallengeWriteUps.query.filter(ChallengeWriteUps.team_id==account_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        knowledge_ids = [knowledge.id for knowledge in knowledges]
        graded =  DocumentationDirectorate.query.filter(DocumentationDirectorate.writeups_id.in_(knowledge_ids)).all()
        graded_ids = [directorate.writeups_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_knowledge = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_knowledge.append({
                    'knowledge_id': grade.writeups_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_know,
            })
            total_rater.append({
                'knowledge_id': grade.writeups_id,
                'rater': graded_knowledge
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['knowledge_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'knowledge_id': list_rated['knowledge_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    #user
    if mode == 'user':
        user = Users.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = user.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        knowledges = ChallengeWriteUps.query.filter(ChallengeWriteUps.user_id==account_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        knowledge_ids = [knowledge.id for knowledge in knowledges]
        graded =  DocumentationDirectorate.query.filter(DocumentationDirectorate.writeups_id.in_(knowledge_ids)).all()
        graded_ids = [directorate.writeups_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_chronicles = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_chronicles.append({
                    'knowledge_id': grade.writeups_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_know,
            })
            total_rater.append({
                'knowledge_id': grade.writeups_id,
                'rater': graded_chronicles
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['knowledge_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'knowledge_id': list_rated['knowledge_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    return {"success": True, "data": result}


#average countermeasures verssion3
def ctk_directorate_averageScore_learn(mode, account_id):
    result = {}
    if mode == 'team':
        team = Teams.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = team.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        countermeasure = ChallengeWriteUps.query.filter(ChallengeWriteUps.team_id==account_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        countermeasure_ids = [counter.id for counter in countermeasure]
        graded =  DocumentationDirectorate.query.filter(DocumentationDirectorate.writeups_id.in_(countermeasure_ids)).all()
        graded_ids = [directorate.writeups_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_countermeasures = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_countermeasures.append({
                    'countermeasures_id': grade.writeups_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_learn,
            })
            total_rater.append({
                'countermeasures_id': grade.writeups_id,
                'rater': graded_countermeasures
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['countermeasures_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'countermeasures_id': list_rated['countermeasures_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count
    #user
    if mode == 'user':
        user = Users.query.filter_by(id=account_id, banned=False, hidden=False).first_or_404()
        solves = user.get_solves()
        challenge_solved = [solve.challenge_id for solve in solves]
        countermeasure = ChallengeWriteUps.query.filter(ChallengeWriteUps.user_id==account_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        countermeasure_ids = [counter.id for counter in countermeasure]
        graded =  DocumentationDirectorate.query.filter(DocumentationDirectorate.writeups_id.in_(countermeasure_ids)).all()
        graded_ids = [directorate.writeups_id for directorate in graded]
        total_rater = []
        for grade in graded:
            graded_countermeasures = []
            rater = Users.query.filter_by(id=grade.directorate_id).first()
            graded_countermeasures.append({
                    'countermeasures_id': grade.writeups_id,
                    'rater_name': rater.name,
                    'grade': grade.rater_learn,
            })
            total_rater.append({
                'countermeasures_id': grade.writeups_id,
                'rater': graded_countermeasures
            })
        total_graded = set(graded_ids)
        final_count = []
        for list in total_graded:
            groups = []
            sum = 0
            for list_rated in total_rater:
                if list == list_rated['countermeasures_id']:
                    sum = sum + int(list_rated['rater'][0]['grade'])
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'countermeasures_id': list_rated['countermeasures_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(sum / count),
            })
        result = final_count 
    return {"success": True, "data": result}
