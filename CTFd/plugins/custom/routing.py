from email import message
from itertools import groupby
from operator import mod
import os, json
import statistics
from unittest import result
from CTFd.models import db, Challenges, Submissions, Solves, Teams, TeamFieldEntries, Tracking, Users, UserFieldEntries,  UserFields, TeamFields, UserTokens, Awards, Pages, Notifications, Unlocks
from flask import (
    render_template,
    jsonify,
    Blueprint,
    url_for,
    redirect,
    request,
    session,
    Flask,
    abort,
)
from CTFd.utils.config import is_teams_mode, is_users_mode, user_mode
from CTFd.utils.decorators import admins_only
from CTFd.utils.scores import get_standings, get_user_standings, get_team_standings
from CTFd.plugins.custom.utils import (
    get_category, 
    get_challenges, 
    custom_get_standings, 
    custom_get_user_standings, 
    get_c3_category,
    get_cat_chals,
    id_generator,
    get_team_score,
    ctk_cat_exist,
    ctk_writeups_scores,
    ctk_countermeasure_scores,
    ctk_knowledge_scores,
    ctk_scores_date,
    overall_score,
    get_user_score,
    get_user_score_date,
    CTK_lockout,
    ctk_users_mode,
    ctk_teams_mode,
    All_scores,
    get_ctk_team_standings,
    ctk_branch,
    ctk_major_units,
    ctk_sub_units,
    get_alltimeuser_standings,
    ctk_directorate_mode,
    docs_graded,
    ctk_directorate_averageScore_chronicles,
    ctk_directorate_averageScore_countermeasures,
    ctk_directorate_averageScore_knowledge,
    ctk_directorate_averageScore_documentations_do,
    ctk_directorate_averageScore_know,
    ctk_directorate_averageScore_learn
)
from CTFd.plugins.custom.modes import require_team_mode, require_user_mode
from CTFd.utils.dates import isoformat, unix_time_to_utc
from CTFd.utils.user import is_admin, authed, get_current_user, get_current_team, get_current_user_attrs
from CTFd.utils import user as current_user
from CTFd.utils import validators
from CTFd.utils import get_config, set_config
from CTFd.utils.security.auth import logout_user
from CTFd.utils.decorators import authed_only, during_ctf_time_only, require_verified_emails, require_complete_profile, ratelimit
from CTFd.utils.decorators.visibility import check_challenge_visibility, check_score_visibility, check_account_visibility, check_registration_visibility
#from CTFd.utils.decorators.modes import require_team_mode
from CTFd.plugins.custom.models import (
    C3_selected_cat, 
    C3CategoryChallenge,
    C3CounterMeasure, 
    ChallengeWriteUps, 
    C3ChallengeCategory, 
    C3_category,
    ChallengeCounterMeasure,
    CTK_Blog,
    KnowledgeDirectorate,
    c3_lockout,
    docs_publish,
    CTK_Config,
    ChroniclesDirectorate,
    CountermeasureDirectorate,
    KnowledgeWellDocs,
    docs_publish,
    red_teaming,
    logo,
    DocumentationDirectorate
)
from CTFd.utils.crypto import verify_password
from CTFd.cache import clear_team_session, clear_user_session, make_cache_key, cache, clear_config, clear_pages, clear_standings
from CTFd.utils.security.auth import login_user
from CTFd.utils.logging import log
from CTFd.utils.validators import ValidationError
from werkzeug.utils import secure_filename
from CTFd.plugins import bypass_csrf_protection
from CTFd.utils.helpers.models import build_model_filters
from CTFd.utils.modes import get_model, TEAMS_MODE
from CTFd.utils.helpers import get_infos, get_errors, markup
from CTFd.utils.config.visibility import scores_visible
from CTFd.utils import config, get_config,  email
from CTFd.utils.config.pages import get_page
from sqlalchemy.sql import not_, column
from CTFd.plugins.custom.CTK_Challenge import CTKpost
import decimal
#import multiple choice modul plugin | Required Module
#from CTFd.api.v1.challenges import ChallengeList
from CTFd.plugins.custom.api.v2.challenges import ChallengeList
from CTFd.models import Hints, HintUnlocks
from CTFd.schemas.hints import HintSchema
from collections import defaultdict
from CTFd.utils.uploads import delete_file
from slugify import slugify
from CTFd.plugins.custom.vpn.api import VPNConnector
from pprint import pp, pprint #for Debugging purpose only remove in Production

#custom blue print in view and routing
app = Flask(__name__, template_folder='templates')
app.config['UPLOAD_PATH'] = 'CTFd/plugins/custom/'
FILE_LOCATON = '/plugins/custom/writeups/'
FILE_LOCATON_COUNTER = '/plugins/custom/countermeasure/'
FILE_LOCATON_KNOWLEDGE = '/plugins/custom/knowledge/'
CATEGORY_FILE_LOCATON = '/plugins/custom/admin/assets/img/'
c3 = Blueprint('c3', __name__, static_folder='assets',static_url_path='/plugins/custom/')
ALLOWED_EXTENSIONS = set(['pdf'])

#new view scoreboard | Admin
@admins_only
def view_scoreboard_list():
    q = request.args.get("game_category")
    if request.method == 'GET' and q:
        if q is None:
            standings = get_standings(admin=True)
            user_standings = get_user_standings(admin=True)
            return jsonify(standings=standings, users_standings=user_standings)
        else:
            standings = custom_get_standings(admin=True, c3=q)
            user_standings = custom_get_user_standings(admin=True, c3=q)
            return jsonify(standings=standings, users_standings=user_standings)

    standings = get_standings(admin=True)
    # user_standings = get_user_standings(admin=True) if ctk_teams_mode() else None
    user_standings = get_user_standings(admin=True)
    return render_template('plugins/custom/admin/scoreboard/scoreboard.html', standings=standings, user_standings=user_standings, cat=get_category())

@during_ctf_time_only
@require_verified_emails
@check_challenge_visibility
@require_complete_profile
def get_available_challenges():
    progress = []
    team_prereq = []
    user = get_current_user()
    published = db.session.query(docs_publish).first()
    #user mode support
    if ctk_users_mode():
        cat_exist = db.session.query(C3_selected_cat).filter_by(user_id = user.id).first()
        if cat_exist is None:
            return redirect("challenge-category", code=303)
        c3_data = cat_exist
        c3_cat = get_c3_category(id=cat_exist.ctf_category_id)
        #pre-requisite
        prereq = ChallengeList.get(query_args={})

    #teams mode
    if ctk_teams_mode():
        cat_exist = db.session.query(C3_selected_cat).filter_by(team_id = user.team_id).first()
        if cat_exist is None:
            return redirect("challenge-category", code=303)
        if cat_exist.team_id is None: 
            return redirect("challenge-category", code=303)
        c3_data = vars(cat_exist)
        c3_cat = get_c3_category(id=c3_data['ctf_category_id'])
        prereqs = ChallengeList.get(query_args={})
        for requisite in prereqs['data']:
            solved_of_me = True
            solved = Solves.query.filter_by(team_id=user.team_id, challenge_id=requisite['id']).first()
            if solved is None:
                 solved_of_me = False
            team_prereq.append({
                'id': requisite['id'],
                'name': requisite['name'],
                'script': requisite['script'],
                'solved_by_me': solved_of_me,
                'solves': requisite['solves'],
                'tags': requisite['tags'],
                'template': requisite['template'],
                'type': requisite['type'],
                'value': requisite['value'],
            })
        final_team_prereq={
            'data':team_prereq
        }
        prereq=final_team_prereq

    #Directorates Mode
    if ctk_directorate_mode():
        cat_exist = db.session.query(C3_selected_cat).filter_by(user_id = user.id).first()
        if cat_exist is None:
            return redirect("challenge-category", code=303)
        c3_data = cat_exist
        c3_cat = get_c3_category(id=cat_exist.ctf_category_id)
        #pre-requisite
        prereq = ChallengeList.get(query_args={})

    progress = CTK_lockout()
    if published is None:
        return render_template('challenges.html', results = get_challenges(), prereq=prereq, c3_cat = c3_cat, progress = progress, team = ctk_teams_mode(), published=False)
    return render_template('challenges.html', results = get_challenges(), prereq=prereq, c3_cat = c3_cat, progress = progress, team = ctk_teams_mode(), published=published.countermeasure_published)

#upload function
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@c3.route('/uploader', methods=["GET", "POST", "DELETE"])
@bypass_csrf_protection
@authed_only
def uploader():
    if request.method == 'POST':
        if 'files' in request.files:
            write_ups = request.files['files']
            challenge_id = int(request.form['challenge'])
            if not write_ups:
                resp = {'message':'No file part in the request'}
                return jsonify(resp),400
        
            errors = {}
            success = False
            
            if write_ups and allowed_file(write_ups.filename):
                filename = secure_filename(write_ups.filename)
                folder = id_generator()
                directory = os.path.isdir(app.config['UPLOAD_PATH']+"writeups/"+folder)
                #create the upload directory if not exist
                if directory is False:
                    os.makedirs(app.config['UPLOAD_PATH']+"writeups/"+folder)
                write_ups.save(os.path.join(app.config['UPLOAD_PATH']+"writeups/"+folder, filename))
                loc = FILE_LOCATON+folder+"/"+filename
                user = get_current_user()
                #team mode
                if ctk_teams_mode():
                    solves = Teams.query.filter_by(id=user.team_id).first_or_404()
                    solve_ids = [solve.challenge_id for solve in solves.get_solves()]
                    if challenge_id in  solve_ids:
                        doc_exist = db.session.query(ChallengeWriteUps).filter_by(team_id = user.team_id, challenge_id = challenge_id).first()
                        if doc_exist is None:
                            db.session.add(ChallengeWriteUps(location = loc, name = filename, challenge_id = challenge_id, user_id = user.id, team_id = user.team_id))
                        db.session.commit()
                        success = True
                    else:
                        errors = {'message':'A system error is encountered! Please refresh Cyber eX Page to retry!'}
                        resp = jsonify(errors)
                        resp.status_code = 400
                        return resp
                #user mode
                if ctk_users_mode():
                    solves = Users.query.filter_by(id=user.id).first_or_404()
                    solve_ids = [solve.challenge_id for solve in solves.get_solves()]
                    if challenge_id in  solve_ids:
                        doc_exist = db.session.query(ChallengeWriteUps).filter_by(user_id = user.id, challenge_id = challenge_id).first()
                        if doc_exist is None:
                            db.session.add(ChallengeWriteUps(location = loc, name = filename, challenge_id = challenge_id, user_id = user.id))
                        db.session.commit()
                        success = True
                    else:
                        errors = {'message':'A system error is encountered! Please refresh Cyber eX Page to retry!'}
                        resp = jsonify(errors)
                        resp.status_code = 400
                        return resp
            
                if success:
                    resp = jsonify({'message' : 'Files successfully uploaded','filename': filename,'location': loc, 'points':0})
                    resp.status_code = 201
                    return resp
            else:
                errors = {'message':'File type is not allowed. Please reload page and re-upload a (.pdf) file.'}
                resp = jsonify(errors)
                resp.status_code = 400
                return resp
            
    #delete uploaded file     
    if request.method == 'DELETE':
        errors = {}
        success = False
        challenge_id = request.json
        user = get_current_user()
        doc_exist = db.session.query(ChallengeWriteUps).filter_by(user_id = user.id, challenge_id = challenge_id['challenge']).first()
        if doc_exist is None:
            errors['message'] = 'File Not Found!'
        else:
            db.session.query(ChallengeWriteUps).filter_by(user_id = user.id, challenge_id = challenge_id['challenge']).delete()
            db.session.commit()
            success = True
            errors['message'] = 'File successfully deleted!'
            resp = jsonify(errors,{'success': success})
            resp.status_code = 206
            return resp
       
#set-up challenge category picker
@c3.route('/challenge-category', methods=['GET', 'POST'])
@authed_only
def view_challenge_category():
    results = []
    #validate exisiting user category selected
    user = get_current_user()
    #user mode support
    if ctk_users_mode():
        cat_exist = db.session.query(C3_selected_cat).filter_by(user_id = user.id).first()
        if not authed():
            return redirect(url_for('auth.login', next=request.path))
        #insert or update selected game categor for Beginner, Intermediate and advanced
        if request.method == 'GET' and request.args.get('c3_category'):
            cat = request.args.get('c3_category')
            if cat_exist is None:
                db.session.merge(C3_selected_cat(ctf_category_id = cat, user_id = user.id))
            else:
                db.session.query(C3_selected_cat).filter_by(user_id = user.id).update(dict(ctf_category_id = cat))
            db.session.commit()
            return redirect(url_for('challenges.listing'))
    #team mode
    if ctk_teams_mode():
        cat_exist = db.session.query(C3_selected_cat).filter_by(team_id = user.team_id).first()
        if not authed():
            return redirect(url_for('auth.login', next=request.path))
        if get_current_team() is None:
            return redirect(url_for("teams.private", next=request.full_path))
        #insert or update selected game category for Beginner, Intermediate and advanced
        if request.method == 'GET' and request.args.get('c3_category'):
            cat = request.args.get('c3_category')
            if cat_exist is None:
                db.session.merge(C3_selected_cat(ctf_category_id = cat, team_id = user.team_id))
            else:
                db.session.query(C3_selected_cat).filter_by(team_id = user.team_id).update(dict(ctf_category_id = cat))
            db.session.commit()
            return redirect(url_for('challenges.listing'))
    #Directorate Mode
    if ctk_directorate_mode():
        cat_exist = db.session.query(C3_selected_cat).filter_by(user_id = user.id).first()
        if not authed():
            return redirect(url_for('auth.login', next=request.path))
        #insert or update selected game categor for Beginner, Intermediate and advanced
        if request.method == 'GET' and request.args.get('c3_category'):
            cat = request.args.get('c3_category')
            if cat_exist is None:
                db.session.merge(C3_selected_cat(ctf_category_id = cat, user_id = user.id))
            else:
                db.session.query(C3_selected_cat).filter_by(user_id = user.id).update(dict(ctf_category_id = cat))
            db.session.commit()

            return redirect(url_for('challenges.listing'))
    results = CTK_lockout()
   
    return render_template('plugins/custom/templates/challenge-category.html', cat=get_category(), progress = results)

#New Challenges List View Backend Admin
@admins_only
def view_challenge_list():
    q = request.args.get("q")
    field = request.args.get("field")
    filters = []
    game_category = request.args.get('game_category_challenges')

    if q:
    # The field exists as an exposed column
        if Challenges.__mapper__.has_property(field):
            filters.append(getattr(Challenges, field).like("%{}%".format(q)))
    
    #game category filter for Beginner, Intermediate and advanced
    if request.method == 'GET' and game_category is None:
        query = Challenges.query.filter(*filters).order_by(Challenges.id.asc())
        challenges = query.all()
        total = query.count()
    else:
        query = C3CategoryChallenge.query.filter(*filters).filter(C3CategoryChallenge.c3_category==game_category).order_by(C3CategoryChallenge.id.asc())
        challenges = query.all()
        results = []
        for x in challenges:
            results.append({
                'id': x.id,
                'name': x.name,
                'value': x.value,
                'category': x.category,
                'type': x.type,
                'state': x.state
            })
        return jsonify({'challenges': results })
        

    query = Challenges.query.filter(*filters).order_by(Challenges.id.asc())
    challenges = query.all()
    total = query.count()
    return render_template('plugins/custom/admin/challenges/challenges.html', cat=get_category(), challenges=challenges, total=total, q=q, field=field)

#set custom API for challenges
@c3.route('/api/v2/writeups/<int:challenge_id>', methods=['GET'])
@authed_only
def write_ups_api(challenge_id):
    user = get_current_user()
    published = db.session.query(docs_publish).first()
    #team mode
    if ctk_teams_mode():
        doc_exist = db.session.query(ChallengeWriteUps).filter_by(team_id = user.team_id, challenge_id = challenge_id).first()
        if doc_exist:    
            data = vars(doc_exist)
            file_data = {
                'id': data['id'],
                'challenges': data['challenge_id'],
                'location': data['location'],
                'type': data['type'],
                'user_id': data['user_id'],
                'team_id': data['team_id'],
                'name': data['name'],
                'points': data['points'],
                'published':  published.countermeasure_published,
                'view_ratings':  published.chronicles_published
            }
            return jsonify(file_data)
    #user mode
    if ctk_users_mode():
        doc_exist = db.session.query(ChallengeWriteUps).filter_by(user_id = user.id, challenge_id = challenge_id).first()
        if doc_exist:    
            data = vars(doc_exist)
            file_data = {
                'id': data['id'],
                'challenges': data['challenge_id'],
                'location': data['location'],
                'type': data['type'],
                'user_id': data['user_id'],
                'name': data['name'],
                'points': data['points'],
                'published':  published.countermeasure_published,
                'view_ratings':  published.chronicles_published
            }
            return jsonify(file_data)
    return jsonify({})
    
#New Submission List View Backend Admin
#Submission
@admins_only
def custom_submissions_listing(submission_type):
    filters_by = {}
    if submission_type:
        filters_by["type"] = submission_type
    filters = []

    q = request.args.get("q")
    field = request.args.get("field")
    page = abs(request.args.get("page", 1, type=int))
    game_category_submissions = request.args.get('game_category_submissions')

    filters = build_model_filters(
        model=Submissions,
        query=q,
        field=field,
        extra_columns={
            "challenge_name": Challenges.name,
            "account_id": Submissions.account_id,
        },
    )

    Model = get_model()

    submissions = (
        Submissions.query.filter_by(**filters_by)
        .filter(*filters)
        .join(Challenges)
        .join(Model)
        .order_by(Submissions.date.desc())
        .paginate(page=page, per_page=50)
    )

    args = dict(request.args)
    args.pop("page", 1)

    if request.method == 'GET' and game_category_submissions is None:
        test = "test"
    else:    
        submissions = (
            Submissions.query.filter_by(**filters_by)
            .filter(*filters)
            .join(Challenges,C3CategoryChallenge)
            .join(Model)
            .filter(C3CategoryChallenge.c3_category==game_category_submissions)
            .order_by(Submissions.date.desc())
            .paginate(page=page, per_page=50)
        )
        data = vars(submissions)        
        results = []
        
        for x in data["items"]:
            results.append({
                'challenge_id': x.challenge_id,
                'challengename': x.challenge.name,
                'date':x.date,
                'id': x.id,
                'ip': x.ip,
                'provided': x.provided,
                'team_id': x.team_id,
                'teamname': x.team.name,
                'type': x.type,
                'user_id': x.user_id,
                'username': x.user.name
            })
        return jsonify({"submissions":results})    
   
    return render_template(
        "admin/submissions.html",
        cat=get_category(),
        submissions=submissions,
        prev_page=url_for(
            request.endpoint,
            submission_type=submission_type,
            page=submissions.prev_num,
            **args
        ),
        next_page=url_for(
            request.endpoint,
            submission_type=submission_type,
            page=submissions.next_num,
            **args
        ),
        type=submission_type,
        q=q,
        field=field,
    )

#new scoreboard Listing | Front-end
@check_score_visibility
def new_scoreboard():
    fields_entries = []
    #user mode support
    if ctk_users_mode():
        # TEAM AFP/PA Major or Sub units @ /admin/config
        fields = UserFieldEntries.query.join(Users).all()
        players = db.session.query(Users).filter(Users.type != 'admin').filter(Users.team_id == None).all()
        if(fields):
            for field in fields:
                fields_entries.append({
                    'id': field.id,
                    'user_id': field.user_id,
                    'field_name': field.name,
                    'type': field.type,
                    'value': field.value
                })
        cat_exist = ctk_cat_exist(mode='user')
        if cat_exist is None:
            return redirect("challenge-category", code=303)
        standings = get_user_score(users=players, c3=cat_exist.ctf_category_id)
    #teams mode
    if ctk_teams_mode():
        # TEAM AFP/PA Major or Sub units @ /admin/config
        fields = TeamFieldEntries.query.join(Teams).all()
        if(fields):
            for field in fields:
                fields_entries.append({
                    'id': field.id,
                    'team_id': field.team_id,
                    'type': field.type,
                    'value': field.value
                })
        cat_exist = ctk_cat_exist(mode='team')
        if cat_exist is None:
            return redirect("challenge-category", code=303)
        #scores of teams 
        standings = custom_get_standings(c3=cat_exist.ctf_category_id)

    #Directorate Mode support
    if ctk_directorate_mode():
        # TEAM AFP/PA Major or Sub units @ /admin/config
        fields = UserFieldEntries.query.join(Users).all()
        players = db.session.query(Users).filter(Users.type != 'admin').filter(Users.team_id == None).all()
        if(fields):
            for field in fields:
                fields_entries.append({
                    'id': field.id,
                    'user_id': field.user_id,
                    'field_name': field.name,
                    'type': field.type,
                    'value': field.value
                })
        cat_exist = ctk_cat_exist(mode='user')
        if cat_exist is None:
            return redirect("challenge-category", code=303)
        standings = get_user_score(users=players, c3=cat_exist.ctf_category_id)
    infos = get_infos()
    #validate users if category is already selected
    if cat_exist is None:
        return redirect("challenge-category", code=303)
    
    if config.is_scoreboard_frozen():
        infos.append("Scoreboard has been frozen")

    if is_admin() is True and scores_visible() is False:
        infos.append("Scores are not currently visible to users")
    return render_template("plugins/custom/templates/new-scoreboard.html", 
        standings=standings, 
        infos=infos,
        c3=cat_exist, 
        fields=fields_entries,
        team_mode=ctk_teams_mode(),
        user_mode=ctk_users_mode(),
        )

#set-up C3 Setting | Config
@c3.route('/admin/custom_setting', methods=['GET'])
@admins_only
def c3_setting():
    results = [] 
    individuals = []
    counterdata = []
    counter_individuals = []
    knowledge_multi = []
    knowledge_individual = []
    q = request.args.get("q")
    field = request.args.get("field")
    filters = []
    logo_teams = []
    #added for Player Logo
    player_teams = Teams.query.filter_by(banned=False, hidden=False).all()
    team_logo = logo.query.all()
    if q:
        # The field exists as an exposed column
        if C3CategoryChallenge.__mapper__.has_property(field):
            filters.append(getattr(C3CategoryChallenge, field).like("%{}%".format(q)))
    #knowledge well for teams
    # knowledge_query = C3CategoryChallenge.query.join(KnowledgeWellDocs, Teams).filter(*filters).order_by(KnowledgeWellDocs.id.asc())
    # knowledge_list = knowledge_query.with_entities(C3CategoryChallenge ,KnowledgeWellDocs, Teams).all()
    # for knowledge_well in knowledge_list:
    #     knowledge_chals = vars(knowledge_well[0])
    #     knowledge = vars(knowledge_well[1])
    #     Knowteams = vars(knowledge_well[2])
    #     knowledge_multi.append({
    #         'challenge_id': knowledge_chals['id'],
    #         'challenge_name': knowledge_chals['name'],
    #         'challenge_cat': knowledge_chals['category'],
    #         'c3_category': knowledge_chals['c3_category'],
    #         'knowledge_id': knowledge['id'],
    #         'location': knowledge['location'],
    #         'filename': knowledge['name'],
    #         'points': knowledge['points'],
    #         'team_id': Knowteams['id'],
    #         'team_name': Knowteams['name'],
    #         'writeup_link': knowledge_chals['writeups'],
    #     })

    #chronicles for Teams
    query = C3CategoryChallenge.query.join(ChallengeWriteUps, Teams).filter(*filters).order_by(ChallengeWriteUps.id.asc())
    challenges = query.with_entities(C3CategoryChallenge, ChallengeWriteUps, Teams).all()
    for chals in challenges:
        write_chals = vars(chals[0])
        cronicles = vars(chals[1])
        teams = vars(chals[2])
        results.append({
            'challenge_id': write_chals['id'],
            'challenge_name': write_chals['name'],
            'challenge_cat': write_chals['category'],
            'c3_category': write_chals['c3_category'],
            'writeups_id': cronicles['id'],
            'location': cronicles['location'],
            'filename': cronicles['name'],
            'points': cronicles['points'],
            'team_id': teams['id'],
            'team_name': teams['name'],
            'writeup_link': write_chals['writeups'],
        })
    #knowledge Well for Individuals
    # knowIndividuals_query = C3CategoryChallenge.query.join(KnowledgeWellDocs, CTK_Config).filter(*filters).filter(CTK_Config.mode == 'users').order_by(KnowledgeWellDocs.id.asc())
    # knowIndividuals_challenges =  knowIndividuals_query.with_entities(C3CategoryChallenge, KnowledgeWellDocs, CTK_Config).all()
    # for knowledge_well_indi in knowIndividuals_challenges:
    #     knowledge_chals_indi = vars(knowledge_well_indi[0])
    #     knowledge_indi = vars(knowledge_well_indi[1])
    #     Knowteams_indi = vars(knowledge_well_indi[2])
    #     knowledge_individual.append({
    #         'challenge_id': knowledge_chals_indi['id'],
    #         'challenge_name': knowledge_chals_indi['name'],
    #         'challenge_cat': knowledge_chals_indi['category'],
    #         'c3_category': knowledge_chals_indi['c3_category'],
    #         'knowledge_id': knowledge_indi['id'],
    #         'location': knowledge_indi['location'],
    #         'filename': knowledge_indi['name'],
    #         'points': knowledge_indi['points'],
    #         'team_id': Knowteams_indi['id'],
    #         'team_name': Knowteams_indi['name'],
    #         'knowledge_link': knowledge_chals_indi['writeups'],
    #     })

    #chronicles for individuals
    individuals_query = C3CategoryChallenge.query.join(ChallengeWriteUps, CTK_Config).filter(*filters).filter(CTK_Config.mode == 'users').order_by(ChallengeWriteUps.id.asc())
    individuals_challenges =  individuals_query.with_entities(C3CategoryChallenge, ChallengeWriteUps, CTK_Config).all()
    for individ_chals in individuals_challenges:
        users_write_chals = vars(individ_chals[0])
        users_cronicles = vars(individ_chals[1])
        users_names = vars(individ_chals[2])
        individuals.append({
            'challenge_id': users_write_chals['id'],
            'challenge_name': users_write_chals['name'],
            'challenge_cat': users_write_chals['category'],
            'c3_category': users_write_chals['c3_category'],
            'writeups_id': users_cronicles['id'],
            'location': users_cronicles['location'],
            'filename': users_cronicles['name'],
            'points': users_cronicles['points'],
            'team_id': users_names['id'],
            'team_name': users_names['name'],
            'writeups_link': users_write_chals['writeups'],
        })
    total = query.count()
    #countermeasure for Teams
    # countermeasure = C3CategoryChallenge.query.join(ChallengeCounterMeasure, Teams).filter(*filters).order_by(ChallengeCounterMeasure.id.asc())
    # counters = countermeasure.with_entities(C3CategoryChallenge, ChallengeCounterMeasure, Teams).all()
    # for counter in counters:
    #     count = vars(counter[0])
    #     measure = vars(counter[1])
    #     teams = vars(counter[2])
    #     counterdata.append({
    #         'challenge_id': count['id'],
    #         'challenge_name': count['name'],
    #         'challenge_cat': count['category'],
    #         'c3_category': count['c3_category'],
    #         'counter_id': measure['id'],
    #         'location': measure['location'],
    #         'filename': measure['name'],
    #         'team_id': teams['id'],
    #         'team_name': teams['name'],
    #         'points': measure['points'],
    #     })
    #countermeasure for individuals
    # individuals_counterquery = C3CategoryChallenge.query.join(ChallengeCounterMeasure, CTK_Config).filter(*filters).filter(CTK_Config.mode == 'users').order_by(ChallengeCounterMeasure.id.asc())
    # individuals_counterchallenges =  individuals_counterquery.with_entities(C3CategoryChallenge, ChallengeCounterMeasure, CTK_Config).all()
    # for individ_counterchals in individuals_counterchallenges:
    #     users_write_counterchals = vars(individ_counterchals[0])
    #     users_countercronicles = vars(individ_counterchals[1])
    #     users_counternames = vars(individ_counterchals[2])
    #     counter_individuals.append({
    #         'challenge_id': users_write_counterchals['id'],
    #         'challenge_name': users_write_counterchals['name'],
    #         'challenge_cat': users_write_counterchals['category'],
    #         'c3_category': users_write_counterchals['c3_category'],
    #         'counter_id': users_countercronicles['id'],
    #         'location': users_countercronicles['location'],
    #         'filename': users_countercronicles['name'],
    #         'points': users_countercronicles['points'],
    #         'team_id': users_counternames['id'],
    #         'team_name': users_counternames['name'],
    #         'writeup_link': users_write_counterchals['writeups'],
    #     })
    #Article | Blog 
    blog_filters = []
    if q:
        # The field exists as an exposed column
        if CTK_Blog.__mapper__.has_property(field):
            blog_filters.append(getattr(CTK_Blog, field).like("%{}%".format(q)))
    blog = CTK_Blog.query.filter(*blog_filters).order_by(CTK_Blog.id.asc())
    blog_article = blog.with_entities(CTK_Blog).all()   
    lockout = db.session.query(c3_lockout).first()
    if lockout is None:
        c3_cat =  get_category()
        for category_chal in c3_cat:
            db.session.merge(c3_lockout(ctf_category_id = category_chal.id))
            db.session.commit()
    lockout_score = db.session.query(c3_lockout).order_by(c3_lockout.ctf_category_id.asc()).all()

    #documentation publish status
    publish = docs_publish.query.first()
    return render_template("plugins/custom/admin/settings/settings.html", 
        cat=get_category(),
        chals=get_cat_chals(),
        challenges=sorted(results , key=lambda x: x['team_name'], reverse=False),
        counter=sorted(counterdata, key=lambda x: x['team_name'], reverse=False),
        blog=blog_article,
        lockout=lockout_score,
        total=total,
        q=q,
        field=field,
        knowledgewell=sorted(knowledge_multi, key=lambda x: x['team_name'], reverse=False),
        knowledge_individual=sorted(knowledge_individual, key=lambda x: x['team_name'], reverse=False),
        individuals=sorted(individuals , key=lambda x: x['team_name'], reverse=False),
        counter_individuals=sorted(counter_individuals, key=lambda x: x['team_name'], reverse=False),
        publish=publish,
        team_logos=player_teams,
        logo=team_logo
        )

#set custom API for challenges Category
@c3.route('/api/v2/category-challenge', methods=['GET'])
@authed_only
def category_chals_api():
    results = []
    doc_exist = db.session.query(C3ChallengeCategory).all()
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
        return jsonify(results)        
    return jsonify(results)

#set custom API for challenges Category with cat ID
@c3.route('/api/v2/category-challenge/<int:cat_id>', methods=['GET','POST','DELETE'])
@bypass_csrf_protection
@authed_only
def category_chals_id_api(cat_id):
    results = []
    #update data
    if request.method == 'POST':
        cat_name = request.form['c3_category_name']
        cat_desc = request.form['category_description']
        if request.files['category_image']:
            cat_image = request.files['category_image']
            filename = secure_filename(cat_image.filename)
            directory = os.path.isdir(app.config['UPLOAD_PATH']+"admin/assets/img")
            #create the upload directory if not exist
            if directory is False:
                os.makedirs(app.config['UPLOAD_PATH']+"admin/assets/img")
            cat_image.save(os.path.join(app.config['UPLOAD_PATH']+"admin/assets/img", filename))
            loc = CATEGORY_FILE_LOCATON+filename
            doc_exist = db.session.query(C3ChallengeCategory).filter_by(category_name = cat_name).first()
            if doc_exist is None:
                db.session.merge(C3ChallengeCategory(location = loc, image_name = filename, category_name = cat_name, description = cat_desc))
            else:
                db.session.query(C3ChallengeCategory).filter_by(category_name = cat_name).update(dict(location = loc, image_name = filename, category_name = cat_name, description = cat_desc))
            success = True
        else:
            doc_exist = db.session.query(C3ChallengeCategory).filter_by(category_name = cat_name).first()
            if doc_exist is None:
                db.session.merge(C3ChallengeCategory(category_name = cat_name, description = cat_desc))
            else:
                db.session.query(C3ChallengeCategory).filter_by(category_name = cat_name).update(dict(category_name = cat_name, description = cat_desc))
            success = True
        db.session.commit()
        return redirect(request.referrer)

    #delete Data
    if request.method == 'DELETE':
        db.session.query(C3ChallengeCategory).filter_by(id=cat_id).delete()
        db.session.commit()
        results.append({
                    'success': True
                })
        return jsonify(results)

    #fetch data
    if request.method == 'GET':
        doc_exist = db.session.query(C3ChallengeCategory).filter_by(id=cat_id).first()
        if doc_exist:
            cat = vars(doc_exist)
            results.append({
                'id': cat['id'],
                'type': cat['type'],
                'category_name': cat['category_name'],
                'description': cat['description'],
                'image_name': cat['image_name'],
                'location': cat['location']
            })
            return jsonify(results)        
        return jsonify(results)

#set upload logo
@c3.route('/api/v2/logo/<int:id>', methods=['GET','POST','DELETE'])
@bypass_csrf_protection
@authed_only
def player_logo(id):
    if request.method == 'POST':
        if request.files['team_logo']:
            cat_image = request.files['team_logo']
            filename = secure_filename(cat_image.filename)
            directory = os.path.isdir(app.config['UPLOAD_PATH']+"admin/assets/img")
            #create the upload directory if not exist
            if directory is False:
                os.makedirs(app.config['UPLOAD_PATH']+"admin/assets/img")
            cat_image.save(os.path.join(app.config['UPLOAD_PATH']+"admin/assets/img", filename))
            loc = CATEGORY_FILE_LOCATON+filename
            doc_exist = db.session.query(logo).filter_by(id = id).first()
            if doc_exist is None:
                db.session.merge(logo(id = id, location = loc, name = filename))
            else:
                db.session.query(logo).filter_by(id = id).update(dict(location = loc,  name = filename))
            success = True
        # else:
        #     doc_exist = db.session.query(team_logo).filter_by(team_id = id).first()
        #     if doc_exist is None:
        #         db.session.merge(team_logo(team_id = id, location = loc))
        #     else:
        #         db.session.query(team_logo).filter_by(team_id = id).update(dict(location = loc))
        #     success = True
        db.session.commit()
        return redirect(request.referrer)


#set custom API for C3 Category
@c3.route('/api/v2/challenge-category', methods=['GET'])
@authed_only
def c3_category_api():
    results = []
    cat = get_category()
    if cat:
        for x in cat:
            results.append({
                'id': x.id,
                'category': x.category    
            })
        return jsonify(results)
    return jsonify(results)

#c3 category edit/update
@c3.route('/api/v2/challenge-category/<int:c3_id>', methods=['GET','POST','DELETE'])
@admins_only
@bypass_csrf_protection
def c3_category_update_api(c3_id):
    results = []
    #update data
    if request.method == 'POST':
        #lockout itegration
        lockout = request.form.get('lockout', None)
        if lockout != None:
            if request.form['lockout'] == 'true':
                db.session.query(c3_lockout).filter_by(ctf_category_id = c3_id).update(dict(lockout_percentage = request.form['lockout-percent']))
        #c3 category update
        c3_update = request.form.get('c3-category', None)
        if c3_update != None:
            if request.form['c3-category'] == 'true':
                cat_name = request.form['challenge-c3-category-name']
                cat_desc = request.form['challenge-c3-category-description']
                if request.files['c3_image']:
                    cat_image = request.files['c3_image']
                    filename = secure_filename(cat_image.filename)
                    cat_image.save(os.path.join(app.config['UPLOAD_PATH']+"admin/assets/img", filename))
                    loc = CATEGORY_FILE_LOCATON+filename
                    doc_exist = db.session.query(C3_category).filter_by(id = c3_id).first()
                    if doc_exist is None:
                        db.session.merge(C3_category(category = cat_name, description = cat_desc,location=loc, image_name = filename))
                    else:
                        db.session.query(C3_category).filter_by(id = c3_id).update(dict(category = cat_name, description = cat_desc, location=loc, image_name = filename))
                else:
                    doc_exist = db.session.query(C3_category).filter_by(id = c3_id).first()
                    if doc_exist is None:
                        db.session.merge(C3_category(category = cat_name, description = cat_desc))
                    else:
                        db.session.query(C3_category).filter_by(id = c3_id).update(dict(category = cat_name, description = cat_desc))
        db.session.commit()
        return redirect(request.referrer)
        
    #delete Data
    if request.method == 'DELETE':
        db.session.query(C3_category).filter_by(id = c3_id).delete()
        db.session.commit()
        results.append({
                    'success': True
                })
        return jsonify(results)

    #fetch data
    if request.method == 'GET':
        cat_exist = db.session.query(C3_category).filter_by(id = c3_id).all()
        if cat_exist:
            for cat in cat_exist:
                results.append({
                    'id': cat.id,
                    'category': cat.category,
                    'description': cat.description,
                    'image_name': cat.image_name,
                    'location': cat.location    
                })
            return jsonify(results)
    return jsonify(results)

#c3 gt challenge solves
@c3.route('/api/v2/solves/<int:challenge_id>', methods=['GET'])
@authed_only
def get_solves_api(challenge_id):
    results = []
    #team mode support
    if ctk_teams_mode():
        solves_exist = db.session.query(Solves).filter_by(challenge_id = challenge_id).all()
        if solves_exist:
            for solved in solves_exist:
                team_exist = db.session.query(Teams).filter_by(id = solved.team_id).first()
                if team_exist:  
                    results.append({
                            'challenge_id': solved.challenge_id,
                            'date': solved.date,
                            'id': solved.id,
                            'ip': solved.ip,
                           # 'provided': solved.provided,
                            'account_id': solved.team_id,
                            'mode': 'teams',
                            'type': solved.type,
                            'user_id': solved.user_id,
                            'account_name': team_exist.name,
                        })
            count = len(results)
            results.append({
                'count': count
            })
            return jsonify(results)    
    #user mode support
    if ctk_users_mode():
        solves_exist = db.session.query(Solves).join(CTK_Config).filter(Solves.challenge_id == challenge_id).filter(CTK_Config.mode == 'users').all()
        if solves_exist:
            for solved in solves_exist:
                user_exist = db.session.query(Users).filter_by(id = solved.user_id).first()
                if user_exist:  
                    results.append({
                            'challenge_id': solved.challenge_id,
                            'date': solved.date,
                            'id': solved.id,
                            'ip': solved.ip,
                           # 'provided': solved.provided,
                            'account_id': solved.team_id,
                            'mode': 'users',
                            'type': solved.type,
                            'user_id': solved.user_id,
                            'account_name': user_exist.name,
                        })
            count = len(results)
            results.append({
                'count': count
            })
            return jsonify(results)      
    return jsonify(results)

    
#Challenges_Requirements
@c3.route('/api/v2/c3_category/<int:category_id>', methods=['GET', 'POST'])
@bypass_csrf_protection
@authed_only
def c3_category_requirements_api(category_id):
    results = []
    t_chals = []
    if request.method == 'POST':
        req = request.json
        json_req = json.dumps(req['req'])
        chal_exist = db.session.query(Challenges).filter_by(id = req['challenge_id']).first()
        if(chal_exist):
            db.session.query(Challenges).filter_by(id = int(req['challenge_id'])).update(dict(requirements = json.loads(json_req)))
            db.session.commit()
        return jsonify(True)
    else:
        query = Challenges.query.join(C3CategoryChallenge).filter(C3CategoryChallenge.c3_category==category_id).order_by(Challenges.id.asc())
        requirements = query.all()
        if requirements:
            for x in requirements:
                results.append({
                    'id': x.id,
                    'name': x.name,
                    'value': x.value,
                    'category': x.category,
                    'type': x.type,
                    'state': x.state,
                    'requirements': x.requirements
                })
    return jsonify(results)  

@c3.route("/", defaults={"route": "index"})
@c3.route("/<path:route>")
def new_static_html(route):
    """
    Route in charge of routing users to Pages.
    :param route:
    :return:
    """
    # TEAM AFP/PA Major or Sub units @ /admin/config
    fields_entries = []
    multiplayer = False
    individual = False
    fields = TeamFieldEntries.query.join(Teams).all()
    if(fields):
        for field in fields:
            fields_entries.append({
                'id': field.id,
                'team_id': field.team_id,
                'type': field.type,
                'value': field.value
            })

    #chronicles and countermesures views permission
    published = db.session.query(docs_publish).first()
    document_chart = False
    #if published.countermeasure_published == True or ctk_directorate_mode():
    if published:
        if published.countermeasure_published == True:
            document_chart = True

    #users mode fields
    user_fields = UserFieldEntries.query.join(Users).all()
    user_fields_entries = []
    if(user_fields):
        for user_field in user_fields:
            user_fields_entries.append({
                'id': user_field.id,
                'user_id': user_field.user_id,
                'field_name':user_field.name,
                'type': user_field.type,
                'value': user_field.value
            })
    
    page = get_page(route)
    if page is None:
        abort(404)
    else:
        if page.auth_required and authed() is False:
            return redirect(url_for("auth.login", next=request.full_path))
        #get over all score
        teams = All_scores(users='teams')
        users = All_scores(users='users')
        if len(teams['overall']) > 0:
            multiplayer = True
        
        if len(users['users']) > 0:
            individual = True
       
        #blog featured
        blog = CTK_Blog.query.first()
        #players Logo
        team_logo = logo.query.all()
        if blog != None:
            # blog = CTK_Blog.query.filter_by(featured=1).limit(5).all() | MYSQL
            blog = CTK_Blog.query.filter_by(featured=True).limit(5).all()
        return render_template("plugins/custom/templates/page.html", 
            content=page.html, 
            title=page.title, 
            teams=teams, 
            users=users,
            fields=fields_entries, 
            user_fields=user_fields_entries,
            cat=get_category(),
            multiplayer=multiplayer,
            individual=individual,
            blogs=blog,
            document_chart=document_chart,
            logo=team_logo)   

#set custom API for chronicles
@c3.route('/api/v2/chronicles/<int:id>', methods=['GET','POST', 'DELETE'])
@bypass_csrf_protection
@authed_only
def chronicles_api(id):
    results = []
    resp = {}
    if request.method == 'POST':
        points = request.form['writeups-points']
        doc_exist = db.session.query(ChallengeWriteUps).filter_by(id = id).first()
        if doc_exist:
            db.session.query(ChallengeWriteUps).filter_by(id = id).update(dict(points = points))
            db.session.commit()
        return redirect(request.referrer)
    
    if request.method == 'GET':
        doc_exist = db.session.query(ChallengeWriteUps).filter_by(id = id).first()
        if doc_exist:
            chronicle = vars(doc_exist)
            results.append({
                'challenge_id': chronicle['challenge_id'],
                'id': chronicle['id'],
                'location': chronicle['location'],
                'name': chronicle['name'],
                'points': chronicle['points'],
                'team_id': chronicle['team_id'],
                'type': chronicle['type'],
                'user_id': chronicle['user_id']
            })
            return jsonify(results) 

    #Delete chronicles
    if request.method == 'DELETE':
        db.session.query(ChallengeWriteUps).filter_by(id=id).delete()
        db.session.commit()
        resp = jsonify({'message' : 'Chronicles successfully deleted!'})
        resp.status_code = 200
        return resp    
    return jsonify(results) 

#set custom API for chronicles
@c3.route('/api/v2/countermeasure/update/<int:id>', methods=['GET','POST', 'DELETE'])
@bypass_csrf_protection
@authed_only
def counter_update_api(id):
    results = []
    if request.method == 'POST':
        #update counter measure points
        points = request.form['counter-points']
        if points:
            doc_exist = db.session.query(ChallengeCounterMeasure).filter_by(id = id).first()
            if doc_exist:
                db.session.query(ChallengeCounterMeasure).filter_by(id = id).update(dict(points = points))
                db.session.commit()
                return redirect(request.referrer)
    
    if request.method == 'GET':
        doc_exist = db.session.query(ChallengeCounterMeasure).filter_by(id = id).first()
        if doc_exist:    
                data = vars(doc_exist)
                results.append({
                    'challenges': data['challenge_id'],
                    'location': data['location'],
                    'id': data['id'],
                    'type': data['type'],
                    'user_id': data['user_id'],
                    'team_id': data['team_id'],
                    'name': data['name'],
                    'points': data['points']
                })
                return jsonify(results)    
    #Delete countermeasure
    if request.method == 'DELETE':
        db.session.query(ChallengeCounterMeasure).filter_by(id=id).delete()
        db.session.commit()
        resp = jsonify({'message' : 'Chronicles successfully deleted!'})
        resp.status_code = 200
        return resp      
    return jsonify(results)           

#set custom API for counter measure in challenges
@c3.route('/api/v2/countermeasure/<int:challenge_id>', methods=['GET', 'POST', 'DELETE'])
@bypass_csrf_protection
@authed_only
def counter_measure_api(challenge_id):
    user = get_current_user()
    #upload counter measure data
    if request.method == 'POST':
        if 'files' in request.files:
                write_ups = request.files['files']
                challenge_id = int(request.form['challenge'])
                if not write_ups:
                    resp = {'message':'No file part in the request'}
                    return jsonify(resp),400
            
                errors = {}
                success = False
                
                if write_ups and allowed_file(write_ups.filename):
                    filename = secure_filename(write_ups.filename)
                    folder = id_generator()
                    directory = os.path.isdir(app.config['UPLOAD_PATH']+"countermeasure/"+folder)
                    #create the upload directory if not exist
                    if directory is False:
                        os.makedirs(app.config['UPLOAD_PATH']+"countermeasure/"+folder)
                    write_ups.save(os.path.join(app.config['UPLOAD_PATH']+"countermeasure/"+folder, filename))
                    loc = FILE_LOCATON_COUNTER+folder+"/"+filename
                    user = get_current_user()
                    #team mode
                    if ctk_teams_mode():
                        solves = Teams.query.filter_by(id=user.team_id).first_or_404()
                        solve_ids = [solve.challenge_id for solve in solves.get_solves()]
                        if challenge_id in  solve_ids:
                            doc_exist = db.session.query(ChallengeCounterMeasure).filter_by(team_id = user.team_id, challenge_id = challenge_id).first()
                            if doc_exist is None:
                                db.session.add(ChallengeCounterMeasure(location = loc, name = filename, challenge_id = challenge_id, user_id = user.id, team_id = user.team_id))
                            db.session.commit()
                            success = True
                        else:
                            errors = {'message':'A system error is encountered! Please refresh Cyber eX Page to retry!'}
                            resp = jsonify(errors)
                            resp.status_code = 400
                            return resp

                    #user mode
                    if ctk_users_mode():
                        solves = Users.query.filter_by(id=user.id).first_or_404()
                        solve_ids = [solve.challenge_id for solve in solves.get_solves()]
                        if challenge_id in  solve_ids:
                            doc_exist = db.session.query(ChallengeCounterMeasure).filter_by(user_id = user.id, challenge_id = challenge_id).first()
                            if doc_exist is None:
                                db.session.add(ChallengeCounterMeasure(location = loc, name = filename, challenge_id = challenge_id, user_id = user.id))
                            db.session.commit()
                            success = True
                        else:
                            errors = {'message':'A system error is encountered! Please refresh Cyber eX Page to retry!'}
                            resp = jsonify(errors)
                            resp.status_code = 400
                            return resp
                    if success:
                        resp = jsonify({'message' : 'Files successfully uploaded','filename': filename,'location': loc, 'points':0})
                        resp.status_code = 201
                        return resp
                else:
                    errors = {'message':'File type is not allowed. Please reload page and re-upload a (.pdf) file.'}
                    resp = jsonify(errors)
                    resp.status_code = 400
                    return resp
                    
    #get counter measure data
    if request.method == 'GET':
        published = db.session.query(docs_publish).first()
        #team mode
        if ctk_teams_mode():
            doc_exist = db.session.query(ChallengeCounterMeasure).filter_by(team_id = user.team_id, challenge_id = challenge_id).first()
            if doc_exist:    
                data = vars(doc_exist)
                file_data = {
                    'id': data['id'],
                    'challenges': data['challenge_id'],
                    'location': data['location'],
                    'type': data['type'],
                    'user_id': data['user_id'],
                    'team_id': data['team_id'],
                    'name': data['name'],
                    'points': data['points'],
                    'published': published.countermeasure_published,
                    'view_ratings':  published.chronicles_published
                }
                return jsonify(file_data)
        #user mode
        if ctk_users_mode():
            doc_exist = db.session.query(ChallengeCounterMeasure).filter_by(user_id = user.id, challenge_id = challenge_id).first()
            if doc_exist:    
                data = vars(doc_exist)
                file_data = {
                    'id': data['id'],
                    'challenges': data['challenge_id'],
                    'location': data['location'],
                    'type': data['type'],
                    'user_id': data['user_id'],
                    'name': data['name'],
                    'points': data['points'],
                    'published': published.countermeasure_published,
                    'view_ratings':  published.chronicles_published
                }
                return jsonify(file_data)

    #delete counter mesure uploaded file     
    if request.method == 'DELETE':
        if ctk_teams_mode():
            errors = {}
            success = False
            challenge_id = request.json
            user = get_current_user()
            doc_exist = db.session.query(ChallengeCounterMeasure).filter_by(team_id = user.team_id, challenge_id = challenge_id['challenge']).first()
            if doc_exist is None:
                errors['message'] = 'File Not Found!'
            else:
                db.session.query(ChallengeCounterMeasure).filter_by(team_id = user.team_id, challenge_id = challenge_id['challenge']).delete()
                db.session.commit()
                success = True
                errors['message'] = 'File successfully deleted!'
                resp = jsonify(errors,{'success': success})
                resp.status_code = 206
                return resp

        if ctk_users_mode():
            errors = {}
            success = False
            challenge_id = request.json
            user = get_current_user()
            doc_exist = db.session.query(ChallengeCounterMeasure).filter_by(user_id = user.id, challenge_id = challenge_id['challenge']).first()
            if doc_exist is None:
                errors['message'] = 'File Not Found!'
            else:
                db.session.query(ChallengeCounterMeasure).filter_by(user_id = user.id, challenge_id = challenge_id['challenge']).delete()
                db.session.commit()
                success = True
                errors['message'] = 'File successfully deleted!'
                resp = jsonify(errors,{'success': success})
                resp.status_code = 206
                return resp
    return jsonify({})

#set custom API for counter measure in challenges
@c3.route('/api/v2/knowledge-well/<int:challenge_id>', methods=['GET', 'POST', 'DELETE'])
@bypass_csrf_protection
@authed_only
def knowledge_measure_api(challenge_id):
    user = get_current_user()
    #upload counter measure data
    if request.method == 'POST':
        if 'files' in request.files:
                knowledge_docs = request.files['files']
                challenge_id = int(request.form['challenge'])
                if not knowledge_docs:
                    resp = {'message':'No file part in the request'}
                    return jsonify(resp),400
            
                errors = {}
                success = False
                
                if knowledge_docs and allowed_file(knowledge_docs.filename):
                    filename = secure_filename(knowledge_docs.filename)
                    folder = id_generator()
                    directory = os.path.isdir(app.config['UPLOAD_PATH']+"knowledge/"+folder)
                    #create the upload directory if not exist
                    if directory is False:
                        os.makedirs(app.config['UPLOAD_PATH']+"knowledge/"+folder)
                    knowledge_docs.save(os.path.join(app.config['UPLOAD_PATH']+"knowledge/"+folder, filename))
                    loc = FILE_LOCATON_KNOWLEDGE+folder+"/"+filename
                    user = get_current_user()
                    #team mode
                    if ctk_teams_mode():
                        solves = Teams.query.filter_by(id=user.team_id).first_or_404()
                        solve_ids = [solve.challenge_id for solve in solves.get_solves()]
                        if challenge_id in  solve_ids:
                            doc_exist = db.session.query(KnowledgeWellDocs).filter_by(team_id = user.team_id, challenge_id = challenge_id).first()
                            if doc_exist is None:
                                db.session.add(KnowledgeWellDocs(location = loc, name = filename, challenge_id = challenge_id, user_id = user.id, team_id = user.team_id))
                            db.session.commit()
                            success = True
                        else:
                            errors = {'message':'A system error is encountered! Please refresh Cyber eX Page to retry!'}
                            resp = jsonify(errors)
                            resp.status_code = 400
                            return resp
                    
                    #user mode
                    if ctk_users_mode():
                        solves = Users.query.filter_by(id=user.id).first_or_404()
                        solve_ids = [solve.challenge_id for solve in solves.get_solves()]
                        if challenge_id in  solve_ids:
                            doc_exist = db.session.query(KnowledgeWellDocs).filter_by(user_id = user.id, challenge_id = challenge_id).first()
                            if doc_exist is None:
                                db.session.add(KnowledgeWellDocs(location = loc, name = filename, challenge_id = challenge_id, user_id = user.id))
                            db.session.commit()
                            success = True
                        else:
                            errors = {'message':'A system error is encountered! Please refresh Cyber eX Page to retry!'}
                            resp = jsonify(errors)
                            resp.status_code = 400
                            return resp
                    
                    if success:
                        resp = jsonify({'message' : 'Files successfully uploaded','filename': filename,'location': loc, 'points':0})
                        resp.status_code = 201
                        return resp
                        
                else:
                    errors = {'message':'File type is not allowed. Please reload page and re-upload a (.pdf) file.'}
                    resp = jsonify(errors)
                    resp.status_code = 400
                    return resp
    
    #get counter measure data
    if request.method == 'GET':
        published = db.session.query(docs_publish).first()
        #team mode
        if ctk_teams_mode():
            doc_exist = db.session.query(KnowledgeWellDocs).filter_by(team_id = user.team_id, challenge_id = challenge_id).first()
            if doc_exist:    
                data = vars(doc_exist)
                file_data = {
                    'id': data['id'],
                    'challenges': data['challenge_id'],
                    'location': data['location'],
                    'type': data['type'],
                    'user_id': data['user_id'],
                    'team_id': data['team_id'],
                    'name': data['name'],
                    'points': data['points'],
                    'published': published.countermeasure_published,
                    'view_ratings':  published.chronicles_published
                }
                return jsonify(file_data)
        #user mode
        if ctk_users_mode():
            doc_exist = db.session.query(KnowledgeWellDocs).filter_by(user_id = user.id, challenge_id = challenge_id).first()
            if doc_exist:    
                data = vars(doc_exist)
                file_data = {
                    'id': data['id'],
                    'challenges': data['challenge_id'],
                    'location': data['location'],
                    'type': data['type'],
                    'user_id': data['user_id'],
                    'name': data['name'],
                    'points': data['points'],
                    'published': published.countermeasure_published,
                    'view_ratings':  published.chronicles_published
                }
                return jsonify(file_data)

    #delete counter mesure uploaded file     
    if request.method == 'DELETE':
        if ctk_teams_mode():
            errors = {}
            success = False
            challenge_id = request.json
            user = get_current_user()
            doc_exist = db.session.query(KnowledgeWellDocs).filter_by(team_id = user.team_id, challenge_id = challenge_id['challenge']).first()
            if doc_exist is None:
                errors['message'] = 'File Not Found!'
            else:
                db.session.query(KnowledgeWellDocs).filter_by(team_id = user.team_id, challenge_id = challenge_id['challenge']).delete()
                db.session.commit()
                success = True
                errors['message'] = 'File successfully deleted!'
                resp = jsonify(errors,{'success': success})
                resp.status_code = 206
                return resp

        if ctk_users_mode():
            errors = {}
            success = False
            challenge_id = request.json
            user = get_current_user()
            doc_exist = db.session.query(KnowledgeWellDocs).filter_by(user_id = user.id, challenge_id = challenge_id['challenge']).first()
            if doc_exist is None:
                errors['message'] = 'File Not Found!'
            else:
                db.session.query(KnowledgeWellDocs).filter_by(user_id = user.id, challenge_id = challenge_id['challenge']).delete()
                db.session.commit()
                success = True
                errors['message'] = 'File successfully deleted!'
                resp = jsonify(errors,{'success': success})
                resp.status_code = 206
                return resp
    return jsonify({})

#set custom API for progress bar
@c3.route('/api/v2/status', methods=['GET'])
@authed_only
def progress_api():
    results = CTK_lockout()
    return jsonify(results)
 
# CK-EDITOR IMAGE Upload
@c3.route('/uploads/<filename>', methods=['POST'])
@bypass_csrf_protection
@admins_only
def uploaded_file(filename):
    # datetime object containing current date and time
    write_ups = request.files['upload']
    if not write_ups:
        resp = {'message':'No file part in the request'}
        return jsonify(resp),400
    folder = id_generator()
    os.makedirs(app.config['UPLOAD_PATH']+"ctk-editor/"+folder)
    write_ups.save(os.path.join(app.config['UPLOAD_PATH']+"ctk-editor/"+folder, filename))
    resp = jsonify({'message' : 'Files successfully uploaded','filename': filename, 'url':'/plugins/custom/ctk-editor/'+folder+'/'+filename})
    resp.status_code = 201
    return resp

#override users
@admins_only
def new_users_detail(user_id):
    c3 = ''
    # Get user object
    user = Users.query.filter_by(id=user_id).first_or_404()

    
        
    # Get the user's solves
    solves = user.get_solves(admin=True)

    # Get challenges that the user is missing
    if get_config("user_mode") == TEAMS_MODE:
        if user.team:
            all_solves = user.team.get_solves(admin=True)
        else:
            all_solves = user.get_solves(admin=True)
    else:
        all_solves = user.get_solves(admin=True)

    solve_ids = [s.challenge_id for s in all_solves]
    missing = Challenges.query.filter(not_(Challenges.id.in_(solve_ids))).all()

    # Get IP addresses that the User has used
    addrs = (
        Tracking.query.filter_by(user_id=user_id).order_by(Tracking.date.desc()).all()
    )

    # Get Fails
    fails = user.get_fails(admin=True)

    # Get Awards
    awards = user.get_awards(admin=True)

    # Check if the user has an account (team or user)
    # so that we don't throw an error if they dont
    if user.account:
        score = user.account.get_score(admin=True)
        place = user.account.get_place(admin=True)
    else:
        score = None
        place = None

    #Game category filter
    if request.args.get('game_category_challenges_user'):
        c3 = request.args.get('game_category_challenges_user')
        solves = db.session.query(
                Solves
        ).join(Challenges, C3CategoryChallenge).filter(Solves.user_id == user_id).filter(Challenges.id == Solves.challenge_id).filter(C3CategoryChallenge.c3_category == c3).all()
        solve_ids = [s.challenge_id for s in solves]
        missing =  db.session.query(
                Challenges
        ).join(C3CategoryChallenge).filter(C3CategoryChallenge.c3_category == c3).filter(not_(Challenges.id.in_(solve_ids))).all()
        fails = db.session.query(
                Submissions
        ).join(C3CategoryChallenge).filter( Submissions.type == 'incorrect').filter(C3CategoryChallenge.c3_category == c3).all()
        return render_template(
        "plugins/custom/admin/user/user.html",
        solves=solves,
        user=user,
        addrs=addrs,
        score=score,
        missing=missing,
        place=place,
        fails=fails,
        awards=awards,
        cat=get_category(),
        selected=c3
        )

    return render_template(
        "plugins/custom/admin/user/user.html",
        solves=solves,
        user=user,
        addrs=addrs,
        score=score,
        missing=missing,
        place=place,
        fails=fails,
        awards=awards,
        cat=get_category(),
        selected=c3
    )

#override teams
@admins_only
def new_teams_detail(team_id):
    results = []
    c3 = ''
    team = Teams.query.filter_by(id=team_id).first_or_404()

    # Get members
    members = team.members
    member_ids = [member.id for member in members]

    # Get Solves for all members
    solves = team.get_solves(admin=True)
    fails = team.get_fails(admin=True)
    awards = team.get_awards(admin=True)
    score = team.get_score(admin=True)
    place = team.get_place(admin=True)
    
    # Get missing Challenges for all members
    # TODO: How do you mark a missing challenge for a team?
    solve_ids = [s.challenge_id for s in solves]
    missing = Challenges.query.filter(not_(Challenges.id.in_(solve_ids))).all()

    # Get addresses for all members
    addrs = (
        Tracking.query.filter(Tracking.user_id.in_(member_ids))
        .order_by(Tracking.date.desc())
        .all()
    )

    #Game category filter
    if request.args.get('game_category_challenges_team'):
        c3 = request.args.get('game_category_challenges_team')
        solves = db.session.query(
                Solves
        ).join(Challenges, C3CategoryChallenge).filter(Solves.team_id == team_id).filter(Challenges.id == Solves.challenge_id).filter(C3CategoryChallenge.c3_category == c3).all()
        solve_ids = [s.challenge_id for s in solves]
        missing =  db.session.query(
                Challenges
        ).join(C3CategoryChallenge).filter(C3CategoryChallenge.c3_category == c3).filter(not_(Challenges.id.in_(solve_ids))).all()
        fails = db.session.query(
                Submissions
        ).join(C3CategoryChallenge).filter( Submissions.type == 'incorrect').filter(C3CategoryChallenge.c3_category == c3).all()
        for team_member in members:
            scores = db.session.query(
                Solves.id,
                db.func.sum(Challenges.value).label("score")
            ).join(Challenges, C3CategoryChallenge).filter(Solves.user_id == team_member.id ).filter(Challenges.id == Solves.challenge_id).filter(C3CategoryChallenge.c3_category == c3).first()
            if scores.score is None:
                new_score = 0
            else:
                new_score = scores.score
            results.append({
                'id': team_member.id,
                'score': new_score,
                'name':team_member.name,
                'email': team_member.email
            })
        return render_template(
        "plugins/custom/admin/teams/team.html",
        team=team,
        members=results,
        score=score,
        place=place,
        solves=solves,
        fails=fails,
        missing=missing,
        awards=awards,
        addrs=addrs,
        cat=get_category(),
        selected=c3,
        )

    return render_template(
        "plugins/custom/admin/teams/team.html",
        team=team,
        members=members,
        score=score,
        place=place,
        solves=solves,
        fails=fails,
        missing=missing,
        awards=awards,
        addrs=addrs,
        cat=get_category(),
        selected=c3
    )

#ctk scoreboard api
@c3.route('/api/v2/scoreboard/<int:cat_id>', methods=['GET'])
@bypass_csrf_protection
@authed_only
def get_scoreboard_api(cat_id):
    date = []
    sol = []
    top10 = []
    #user mode support
    if ctk_users_mode():
        players = db.session.query(Users).filter(Users.type != 'admin').filter(Users.team_id == None).all()
        standings = get_user_score(users=players, c3=cat_id)
        solves = ctk_scores_date(mode='user',cat_id=cat_id)
        cat_name =  db.session.query(C3_category.category).filter_by(id=cat_id).first()
        for solve in solves:
            t_score = 0
            user_name = db.session.query(Users.name).filter_by(id=solve.user_id).first()
            c3_score =  get_user_score_date(user_id=solve.user_id,c3=cat_id,date=solve.date)    
            sol.append([
                solve.challenge_id,
                #  solve.date.strftime("%d%m%Y"),
                solve.date.strftime("%m/%d/%Y %H:%M:%S"),
                user_name.name,
                c3_score,
                t_score
            ])
            date.append({
                # 'date': solve.date.strftime("%d%m%Y")
                'date': solve.date.strftime("%m/%d/%Y %H:%M:%S")
            })
    
        for top in standings:
            top10.append({
                'name':top['name']
            })
    else:
        standings = None
    #team mode support
    if ctk_teams_mode():
        standings = custom_get_standings(c3=cat_id)
        solves = ctk_scores_date(mode='team',cat_id=cat_id)
        cat_name =  db.session.query(C3_category.category).filter_by(id=cat_id).first()
        for solve in solves:
            if solve.team_id != None:
                t_score = 0
                team_name = db.session.query(Teams.name).filter_by(id=solve.team_id).first()
                c3_score =  get_team_score(team_id=solve.team_id,c3=cat_id,date=solve.date)
                sol.append([
                    solve.challenge_id,
                    #  solve.date.strftime("%d%m%Y"),
                    solve.date.strftime("%m/%d/%Y %H:%M:%S"),
                    team_name.name,
                    c3_score,
                    t_score
                ])
                date.append({
                    # 'date': solve.date.strftime("%d%m%Y")
                    'date': solve.date.strftime("%m/%d/%Y %H:%M:%S")
                })
    
        for top in standings:
            top10.append({
                'name':top.name
            })

    return jsonify(
        standings=standings,
        users_standings=standings,
        board=sol,
        cat_name=cat_name,
        top10=top10,
        dates=date
    )

#c3 new scoreboard per category
@c3.route('/api/v2/leatherboard/<category>', methods=['GET'])
def get_leatherboard_api(category):
    #overall
    if category == 'overall':
        total_standings = []
        teams = []
        beginner = []
        intermmediate = []
        advanced = []
        chronicles = []
        countermeasure = []
        for i, standing in  enumerate(get_team_standings()):
            #team mode support
            #writeups
            doc_exist = ctk_writeups_scores(mode='team', account_id=standing.team_id)
            teams.insert(i, standing.name)
            chronicles.insert(i,decimal.Decimal(doc_exist))
            #countermeasure
            counter_exist = ctk_countermeasure_scores(mode='team',  account_id=standing.team_id)
            countermeasure.insert(i,decimal.Decimal(counter_exist))
       
        #apprentice data
        for i, team in enumerate(teams):
            for apprentice1 in get_ctk_team_standings(c3=1):
                if(team==apprentice1.name):
                    if apprentice1.score < 0:
                        beginner.insert(i, 0)
                    else:
                        beginner.insert(i, apprentice1.score)

        #warrior data
        for i, team in enumerate(teams):
            for warrior1 in get_ctk_team_standings(c3=2):
                if(team==warrior1.name):
                    if warrior1.score < 0:
                        intermmediate.insert(i, 0)
                    else:
                        intermmediate.insert(i, warrior1.score)

        #conqueror data
        for i, team in enumerate(teams):
            for conq1 in get_ctk_team_standings(c3=3):
                if(team==conq1.name):
                    if conq1.score < 0:
                        advanced.insert(i, 0)
                    else:
                        advanced.insert(i, conq1.score)
        #overall
        total_standings.insert(0, teams)
        total_standings.insert(1, beginner)
        total_standings.insert(2, intermmediate)
        total_standings.insert(3, advanced)
        total_standings.insert(4, chronicles)
        total_standings.insert(5, countermeasure)
        return jsonify(overall=total_standings)



#Users Public
@check_account_visibility
@check_score_visibility
def user_public(user_id):
    infos = get_infos()
    errors = get_errors()
    c3=0
    chronicles_docs = []
    countermeasure_docs = []
    knowledge_docs = []
    currentuser = get_current_user()
    user = Users.query.filter_by(id=user_id, banned=False, hidden=False).first_or_404()
    #Game category filter
    if request.args.get('game_category_challenges_user'):
        c3 = request.args.get('game_category_challenges_user')
        solves = db.session.query(
                Solves
        ).join(Challenges, C3CategoryChallenge).filter(Solves.user_id == user_id).filter(Challenges.id == Solves.challenge_id).filter(C3CategoryChallenge.c3_category == c3).all()
        if c3 == str(0):
            #Deafault solves value
            solves = db.session.query(
                    Solves
            ).join(Challenges).filter(Solves.user_id == user_id).filter(Challenges.id == Solves.challenge_id).all() 
    else:
        #Deafault solves value
        solves = db.session.query(
                Solves
        ).join(Challenges).filter(Solves.user_id == user_id).filter(Challenges.id == Solves.challenge_id).all()

    if config.is_scoreboard_frozen():
        infos.append("Scoreboard has been frozen")
    
    if ctk_directorate_mode():
        challenge_solved = [solve.challenge_id for solve in solves]
        #get chronicles submissions
        chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.user_id==user_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        #get countermeasures submissions
        countermeasures = ChallengeCounterMeasure.query.filter(ChallengeCounterMeasure.user_id==user_id, ChallengeCounterMeasure.challenge_id.in_(challenge_solved)).all()
        #get knowledge-well
        knowledge_well = KnowledgeWellDocs.query.filter(KnowledgeWellDocs.user_id==user_id, KnowledgeWellDocs.challenge_id.in_(challenge_solved)).all()
        #knowledge-well
        # if knowledge_well:
        #     for knowledge in knowledge_well:
        #         for solve in solves:
        #             if knowledge.challenge_id == solve.challenge_id:
        #                 my_rate = 0
        #                 rated = KnowledgeDirectorate.query.filter_by(directorate_id = currentuser.id, knowledge_id=knowledge.id).first()
        #                 if rated != None:
        #                     my_rate = rated.rater_points
        #                 knowledge_docs.append({
        #                     'docs_id': knowledge.id,
        #                     'challenge_id': knowledge.challenge_id,
        #                     'user_id':knowledge.user_id,
        #                     'challenge_name': solve.challenge.name,
        #                     'category': solve.challenge.category,
        #                     'docs_location': knowledge.location,
        #                     'docs_name':knowledge.name,
        #                     'points': my_rate
        #                 })
        #chronicles
        if chronicles:
            for chronicle in chronicles:
                for solve in solves:
                    if chronicle.challenge_id == solve.challenge_id:
                        my_rate = 0
                        rated = DocumentationDirectorate.query.filter_by(directorate_id = currentuser.id, writeups_id=chronicle.id).first()
                        if rated != None:
                            my_rate = rated.rater_know+rated.rater_do+rated.rater_learn
                        chronicles_docs.append({
                            'docs_id': chronicle.id,
                            'challenge_id': chronicle.challenge_id,
                            'user_id':chronicle.user_id,
                            'challenge_name': solve.challenge.name,
                            'category': solve.challenge.category,
                            'docs_location': chronicle.location,
                            'docs_name':chronicle.name,
                            'points': my_rate
                        })
        #countermeasure
        # if countermeasures:
        #     for countermeasure in countermeasures:
        #         for solve in solves:
        #             if countermeasure.challenge_id == solve.challenge_id:
        #                 my_rates = 0
        #                 rated_chronicles = CountermeasureDirectorate.query.filter_by(directorate_id = currentuser.id, countermeasures_id=countermeasure.id).first()
        #                 if  rated_chronicles != None:
        #                     my_rates = rated_chronicles.rater_points
        #                 countermeasure_docs.append({
        #                     'docs_id': countermeasure.id,
        #                     'challenge_id': countermeasure.challenge_id,
        #                     'user_id':countermeasure.user_id,
        #                     'challenge_name': solve.challenge.name,
        #                     'category': solve.challenge.category,
        #                     'docs_location': countermeasure.location,
        #                     'docs_name':countermeasure.name,
        #                     'points': my_rates
        #                 })
    #chronicles and countermesures views permission
    published = db.session.query(docs_publish).first()
    document_chart = False
    if published:
        if published.countermeasure_published == True or ctk_directorate_mode():
            document_chart = True

    return render_template(
        "users/public.html", 
        user=user, 
        account=user.account, 
        infos=infos, 
        errors=errors, 
        cat=get_category(),
        user_solves=solves, 
        selected=c3,
        chronicles=chronicles_docs,
        countermeasures=countermeasure_docs,
        knowledge=knowledge_docs,
        directorate=ctk_directorate_mode(),
        current_url=request.base_url,
        document_chart=document_chart
    )

#Teams Public
@check_account_visibility
@check_score_visibility
#@require_team_mode
def team_public(team_id):
    results = []
    chronicles_docs = []
    countermeasure_docs = []
    knowledge_docs = []
    c3 = 0
    members = []
    user = get_current_user()
    infos = get_infos()
    errors = get_errors()
    team = Teams.query.filter_by(id=team_id, banned=False, hidden=False).first_or_404()
    solves = team.get_solves()
    awards = team.get_awards()
    place = team.place
    score = team.score
    
    if errors:
        return render_template("teams/public.html", team=team, errors=errors)

    if config.is_scoreboard_frozen():
        infos.append("Scoreboard has been frozen")

    #Game category filter
    if request.args.get('game_category_challenges_team'):
        c3 = request.args.get('game_category_challenges_team')
        solves = db.session.query(
                Solves
        ).join(Challenges, C3CategoryChallenge).filter(Solves.team_id == team_id).filter(Challenges.id == Solves.challenge_id).filter(C3CategoryChallenge.c3_category == c3).all()
        for team_member in team.members:
            scores = db.session.query(
                Solves.id,
                db.func.sum(Challenges.value).label("score")
            ).join(Challenges, C3CategoryChallenge).filter(Solves.user_id == team_member.id ).filter(Challenges.id == Solves.challenge_id).filter(C3CategoryChallenge.c3_category == c3).first()
            if scores.score is None:
                new_score = 0
            else:
                new_score = scores.score
            results.append({
                'id': team_member.id,
                'score': new_score,
                'name':team_member.name,
                'email': team_member.email
            })
        members=results
        if c3 == str(0):
            members=team.members
            solves=team.get_solves()
    else:
        members=team.members
    #Cyber eX Directorate Scoring
    if ctk_directorate_mode():
        challenge_solved = [solve.challenge_id for solve in solves]
        #get chronicles submissions
        chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.team_id==team_id, ChallengeWriteUps.challenge_id.in_(challenge_solved)).all()
        #get countermeasures submissions
        countermeasures = ChallengeCounterMeasure.query.filter(ChallengeCounterMeasure.team_id==team_id, ChallengeCounterMeasure.challenge_id.in_(challenge_solved)).all()
        #get knowledge-well
        knowledge_well = KnowledgeWellDocs.query.filter(KnowledgeWellDocs.team_id==team_id, KnowledgeWellDocs.challenge_id.in_(challenge_solved)).all()
        #knowledge-well
        # if knowledge_well:
        #     for knowledge in knowledge_well:
        #         for solve in solves:
        #             if knowledge.challenge_id == solve.challenge_id:
        #                 my_rate = 0
        #                 rated = KnowledgeDirectorate.query.filter_by(directorate_id = user.id, knowledge_id=knowledge.id).first()
        #                 if rated != None:
        #                     my_rate = rated.rater_points
        #                 knowledge_docs.append({
        #                     'docs_id': knowledge.id,
        #                     'challenge_id': knowledge.challenge_id,
        #                     'user_id':knowledge.user_id,
        #                     'challenge_name': solve.challenge.name,
        #                     'category': solve.challenge.category,
        #                     'docs_location': knowledge.location,
        #                     'docs_name':knowledge.name,
        #                     'points': my_rate
        #                 })
        #chronicles
        if chronicles:
            for chronicle in chronicles:
                #chronicles
                for solve in solves:
                    if chronicle.challenge_id == solve.challenge_id:
                        my_rate = 0
                        rated = DocumentationDirectorate.query.filter_by(directorate_id = user.id, writeups_id=chronicle.id).first()
                        if rated != None:
                            my_rate = rated.rater_know+rated.rater_do+rated.rater_learn
                        chronicles_docs.append({
                            'docs_id': chronicle.id,
                            'challenge_id': chronicle.challenge_id,
                            'team_id':chronicle.team_id,
                            'challenge_name': solve.challenge.name,
                            'category': solve.challenge.category,
                            'docs_location': chronicle.location,
                            'docs_name':chronicle.name,
                            'points': my_rate
                        })
        #countermeasure
        # if countermeasures:
        #     for countermeasure in countermeasures:
        #         for solve in solves:
        #             if countermeasure.challenge_id == solve.challenge_id:
        #                     my_rates = 0
        #                     rated_chronicles = CountermeasureDirectorate.query.filter_by(directorate_id = user.id, countermeasures_id=countermeasure.id).first()
        #                     if  rated_chronicles != None:
        #                         my_rates = rated_chronicles.rater_points
        #                     countermeasure_docs.append({
        #                         'docs_id': countermeasure.id,
        #                         'challenge_id': countermeasure.challenge_id,
        #                         'team_id':countermeasure.team_id,
        #                         'challenge_name': solve.challenge.name,
        #                         'category': solve.challenge.category,
        #                         'docs_location': countermeasure.location,
        #                         'docs_name':countermeasure.name,
        #                         'points': my_rates
        #                     })

    fields = UserFieldEntries.query.join(Users).all()
    fields_entries = []
    if(fields):
        for user_field in fields:
            fields_entries.append({
                'id': user_field.id,
                'user_id': user_field.user_id,
                'field_name':user_field.name,
                'type': user_field.type,
                'value': user_field.value
            })

    #chronicles and countermesures views permission
    published = db.session.query(docs_publish).first()
    document_chart = False
    if published:
        if published.countermeasure_published == True or ctk_directorate_mode():
            document_chart = True

    return render_template(
        "teams/public.html",
        solves=solves,
        awards=awards,
        team=team,
        score=score,
        place=place,
        score_frozen=config.is_scoreboard_frozen(),
        infos=infos,
        errors=errors,
        cat=get_category(),
        members=members,
        selected=c3,
        fields=fields_entries,
        chronicles=chronicles_docs,
        knowledge=knowledge_docs,
        countermeasures=countermeasure_docs,
        directorate=ctk_directorate_mode(),
        current_url=request.base_url,
        document_chart=document_chart
    )


#c3 article pages
@c3.route('/article/<slug_id>', methods=['GET'])
def article_page(slug_id):
    blog = CTK_Blog.query.filter_by(slug=slug_id).first_or_404()
    author = Users.query.filter_by(id=blog.author).first()
    articles = CTK_Blog.query.filter(not_(CTK_Blog.id ==  blog.id)).all()
    dates = blog.date
    dates = dates.strftime('%A %d %B %Y')
    if blog is None:
        return redirect("/", code=303)
    return render_template("plugins/custom/templates/article.html", blog=blog, author=author, date=dates, articles=articles) 

#add blog/content Page
@c3.route('/article/add', methods=['GET', 'POST'])
@admins_only
@authed_only
@bypass_csrf_protection
def article_add():
    user = get_current_user()
    #add BLOG | Article
    blog_featured_val = False
    if request.method == 'POST':
        blog_title = request.form['blog-name']
        blog_description = request.form['blog-description']
        blog_content = request.form['blog-content']
        blog_featured = request.form['blog_featured']
        if blog_featured:
            if blog_featured == 'False':
                 blog_featured_val = False
            else:
                blog_featured_val = True
        url = slugify(blog_title)
        db.session.merge(CTK_Blog(name = blog_title, description = blog_description, slug=url, content = blog_content, author = user.id, featured=blog_featured_val))
        db.session.commit()
        return redirect("/admin/custom_setting", code=303)
    return render_template("plugins/custom/admin/settings/configs/add-blog.html")

#edit/update blog/content Page
@c3.route('/article/edit/<int:blog_id>', methods=['GET', 'POST'])
@admins_only
@authed_only
@bypass_csrf_protection
def article_update(blog_id):
    blog_featured_val = False
    blog = CTK_Blog.query.filter_by(id=blog_id).first_or_404()
    if blog is None:
        return redirect("/admin/custom_setting", code=303)
    #Update BLOG | Article
    if request.method == 'POST':
        blog_title = request.form['blog-name']
        blog_description = request.form['blog-description']
        blog_content = request.form['blog-content']
        blog_featured = request.form['blog_featured']
        if blog_featured:
            if blog_featured == 'False':
                 blog_featured_val = False
            else:
                blog_featured_val = True
        url = slugify(blog_title)
        db.session.query(CTK_Blog).filter_by(id = blog_id).update(dict(name = blog_title, description = blog_description, slug=url,content = blog_content, featured=blog_featured_val))
        db.session.commit()
        return redirect("/admin/custom_setting", code=303)
    return render_template("plugins/custom/admin/settings/configs/edit-blog.html", blog=blog)

#delete/update blog/content Page
@c3.route('/api/v2/article/delete/<int:blog_id>', methods=['DELETE'])
@admins_only
@authed_only
@bypass_csrf_protection
def article_delete(blog_id):
    results = []
    #delete Article|Blog
    if request.method == 'DELETE':
        db.session.query(CTK_Blog).filter_by(id = blog_id).delete()
        db.session.commit()
        results.append({
                    'success': True
                })
        return jsonify(results)
    return jsonify(results)

#custom challenges v2
@c3.route('/api/v2/challenges', defaults={"challenge_id": None}, methods=['GET'])
@c3.route('/api/v2/challenges/<int:challenge_id>', methods=['GET'])
@authed_only
def challenges_api_v2(challenge_id):
    results = []
    user = get_current_user()
    if(challenge_id != None):
        challenge = db.session.query(Challenges).filter_by(id=challenge_id).first()
        if authed():
            if ctk_teams_mode():
                 # Get current attempts for the multiplayers
                attempts = Submissions.query.filter_by(
                    team_id=user.team_id, challenge_id=challenge.id
                ).count()
            if ctk_users_mode():
                # Get current attempts for the individuals
                attempts = Submissions.query.filter_by(
                    user_id=user.id, challenge_id=challenge.id
                ).count()
        else:
            attempts = 0
        results.append({
            'id': challenge.id,
            'name': challenge.name,
            'description': challenge.description,
            'max_attempts': challenge.max_attempts,
            'attempts': attempts,
            'value': challenge.value,
            'category': challenge.category,
            'type': challenge.type,
            'state': challenge.state,
            'requirements': challenge.requirements,
            'connection_info': challenge.connection_info,
        })
        return jsonify(results)
    else:
        challenges = db.session.query(Challenges).all()
        for challenge in challenges:
            if authed():
                if ctk_teams_mode():
                    # Get current attempts for the multiplayers
                    attempts = Submissions.query.filter_by(
                        team_id=user.team_id, challenge_id=challenge.id
                    ).count()
                if ctk_users_mode():
                    # Get current attempts for the individuals
                    attempts = Submissions.query.filter_by(
                        user_id=user.user_id, challenge_id=challenge.id
                    ).count()
            else:
                attempts = 0
            results.append({
                'id': challenge.id,
                'name': challenge.name,
                'description': challenge.description,
                'max_attempts': challenge.max_attempts,
                'attempts': attempts,
                'value': challenge.value,
                'category': challenge.category,
                'type': challenge.type,
                'state': challenge.state,
                'requirements': challenge.requirements,
                'connection_info': challenge.connection_info,
            })
        return jsonify(results)

#docs published | unpublished points
@c3.route('/api/v2/docs', defaults={"publish_id": None}, methods=['GET'])
@c3.route('/api/v2/docs/<publish_id>', methods=['POST'])
@bypass_csrf_protection
@authed_only
@admins_only
def docs_publish_api(publish_id):
    results = []
    success = False
    if request.method == 'POST':
        publish = request.form['counter-publish']
        #published|unpublish counter measure points
        if publish_id == 'document_publish':
            db.session.query(docs_publish).update(dict(countermeasure_published = int(publish)))
            db.session.commit()
        if publish_id == 'view_rating':
            db.session.query(docs_publish).update(dict(chronicles_published = int(publish)))
            db.session.commit()
        success = True
        results.append({
            'success':success
        })
        return redirect("/admin/custom_setting", code=303)

    if request.method == 'GET':
        counter = db.session.query(docs_publish).first()
        success = True
        results.append({
            'countermeasure': counter.countermeasure_published,
            'chronicles': counter.chronicles_published,
            'success': success
        })
    return jsonify(results)

#CTK Registration for Users Mode | Teams Mode
@check_registration_visibility
@ratelimit(method="POST", limit=10, interval=5)
def ctk_register():
    errors = get_errors()
    message = []
    if current_user.authed():
        return redirect(url_for("challenges.listing"))
    user_field = UserFields.query.all()

    #unit Branch
    branch = ctk_branch()
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email_address = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        user_mode = request.form.get("user-mode", "").strip()
        #validation for directorate registration for admin users only
        if user_mode == 'directorate':
            return abort(404)
     
        website = request.form.get("website")
        affiliation = request.form.get("affiliation")
        country = request.form.get("country")
        registration_code = request.form.get("registration_code", "")

        name_len = len(name) == 0
        name_column = column('name')
        id_column = column('id')
        email_column = column('email')
        names = Users.query.add_columns(name_column, id_column).filter_by(name=name).first()
        emails = (
            Users.query.add_columns(email_column,  id_column)
            .filter_by(email=email_address)
            .first()
        )
        pass_short = len(password) == 0
        pass_long = len(password) > 128
        valid_email = validators.validate_email(email_address)
        team_name_email_check = validators.validate_email(name)

        if get_config("registration_code"):
            if (
                registration_code.lower()
                != get_config("registration_code", default="").lower()
            ):
                errors.append("The registration code you entered was incorrect")

        # Process additional user fields
        fields = {}
        for field in UserFields.query.all():
            fields[field.id] = field
        
        entries = {}
        for field_id, field in fields.items():
            value = request.form.get(f"fields[{field_id}]", "").strip()
            if field.required is True and (value is None or value == ""):
                errors.append("Please provide all required fields")
                break

            # Handle special casing of existing profile fields
            if field.name.lower() == "affiliation":
                affiliation = value
                break
            elif field.name.lower() == "website":
                website = value
                break

            if field.field_type == "boolean":
                entries[field_id] = bool(value)
            else:
                entries[field_id] = value

        if country:
            try:
                validators.validate_country_code(country)
                valid_country = True
            except ValidationError:
                valid_country = False
        else:
            valid_country = True

        if website:
            valid_website = validators.validate_url(website)
        else:
            valid_website = True

        if affiliation:
            valid_affiliation = len(affiliation) < 128
        else:
            valid_affiliation = True

        if not valid_email:
            errors.append("Please enter a valid email address")
        if email.check_email_is_whitelisted(email_address) is False:
            errors.append(
                "Only email addresses under {domains} may register".format(
                    domains=get_config("domain_whitelist")
                )
            )
        if names:
            errors.append("That user name is already taken")
        if team_name_email_check is True:
            errors.append("Your user name cannot be an email address")
        if emails:
            errors.append("That email has already been used")
        if pass_short:
            errors.append("Pick a longer password")
        if pass_long:
            errors.append("Pick a shorter password")
        if name_len:
            errors.append("Pick a longer user name")
        if valid_website is False:
            errors.append("Websites must be a proper URL starting with http or https")
        if valid_country is False:
            errors.append("Invalid country")
        if valid_affiliation is False:
            errors.append("Please provide a shorter affiliation")

        if len(errors) > 0:
            return render_template(
                "register.html",
                errors=errors,
                name=request.form["name"],
                email=request.form["email"],
                password=request.form["password"],
            )
        else:
            with app.app_context():
                user = CTK_Config(name=name, email=email_address, password=password, mode=user_mode)

                if website:
                    user.website = website
                if affiliation:
                    user.affiliation = affiliation
                if country:
                    user.country = country
                #get the  full name from custom fields
                fullname = ""
                for field_id, value in entries.items():
                    entry = UserFieldEntries(
                        field_id=field_id, value=value, user_id=user.id
                    )
                    #get the user full name
                    if entry.field_id == 1:
                        fullname = entry.value

                #vpn connection
                connector = VPNConnector()
                connector.CreateUser(username=name, user_full_name=fullname, user_password=password)
                #Save the registartion if vpn connection successful
                db.session.add(user)
                db.session.commit()
                db.session.flush()

                for field_id, value in entries.items():
                    entry = UserFieldEntries(
                        field_id=field_id, value=value, user_id=user.id
                    )
                    db.session.add(entry)
                db.session.commit()
                #successfull messsage notifications
                message.append({
                "message":"Welcome to Cyber Exercise for Excellence!. Your username: {name} is successfully registered!. Please login to continue.".format(
                    name=name)
                })
        log(
            "registrations",
            format="[{date}] {ip} - {name} registered with {email}",
            name=user.name,
            email=user.email,
        )
        db.session.close()

        return render_template("login.html", message=message)
    else:
        return render_template("register.html", errors=errors, branchs=branch, extra=user_field)

#MAjor units in registration
@c3.route('/api/v2/maj_unit/<unit>', methods=['GET'])
def maj_units_api(unit):
    results = ctk_major_units(maj_units=unit)
    return jsonify(results)

#sub units in registartion
@c3.route('/api/v2/sub_unit/<unit>', methods=['GET'])
def sub_units_api(unit):
    results = ctk_sub_units(unit=unit)
    return jsonify(results)

@authed_only
@require_team_mode
def ctk_private():
    infos = get_infos()
    errors = get_errors()

    user = get_current_user()
    if not user.team_id:
        return render_template("teams/team_enrollment.html")

    team_id = user.team_id

    team = Teams.query.filter_by(id=team_id).first_or_404()
    solves = team.get_solves()
    awards = team.get_awards()

    place = team.place
    score = team.score

    if config.is_scoreboard_frozen():
        infos.append("Scoreboard has been frozen")
    
    fields = UserFieldEntries.query.join(Users).all()
    fields_entries = []
    if(fields):
        for user_field in fields:
            fields_entries.append({
                'id': user_field.id,
                'user_id': user_field.user_id,
                'field_name':user_field.name,
                'type': user_field.type,
                'value': user_field.value
            })

    return render_template(
        "teams/private.html",
        solves=solves,
        awards=awards,
        user=user,
        team=team,
        score=score,
        place=place,
        score_frozen=config.is_scoreboard_frozen(),
        infos=infos,
        errors=errors,
        fields=fields_entries
    )

@authed_only
@require_team_mode
@ratelimit(method="POST", limit=10, interval=5)
def ctk_join():
    infos = get_infos()
    errors = get_errors()
    team_list = Teams.query.filter_by(hidden=False, banned=False).all()
    user = get_current_user_attrs()
    if user.team_id:
        errors.append("You are already in a team. You cannot join another.")

    if request.method == "GET":
        team_size_limit = get_config("team_size", default=0)
        if team_size_limit:
            plural = "" if team_size_limit == 1 else "s"
            infos.append(
                "Teams are limited to {limit} member{plural}".format(
                    limit=team_size_limit, plural=plural
                )
            )
        return render_template("teams/join_team.html", infos=infos, errors=errors,  team_list=team_list)

    if request.method == "POST":
        teamname = request.form.get("name")
        passphrase = request.form.get("password", "").strip()

        team = Teams.query.filter_by(name=teamname).first()

        if errors:
            return (
                render_template("teams/join_team.html", infos=infos, errors=errors,  team_list=team_list),
                403,
            )

        if team and verify_password(passphrase, team.password):
            team_size_limit = get_config("team_size", default=0)
            if team_size_limit and len(team.members) >= team_size_limit:
                errors.append(
                    "{name} has already reached the team size limit of {limit}".format(
                        name=team.name, limit=team_size_limit
                    )
                )
                return render_template(
                    "teams/join_team.html", infos=infos, errors=errors, team_list=team_list
                )

            user = get_current_user()
            user.team_id = team.id
            db.session.commit()

            if len(team.members) == 1:
                team.captain_id = user.id
                db.session.commit()

            clear_user_session(user_id=user.id)
            clear_team_session(team_id=team.id)

            return redirect(url_for("challenges.listing"))
        else:
            errors.append("That information is incorrect")
            return render_template("teams/join_team.html", infos=infos, errors=errors, team_list=team_list)

@authed_only
@require_team_mode
def ctk_new():
    infos = get_infos()
    errors = get_errors()
    current_login = get_current_user()
    user_field = TeamFields.query.all()

    num_teams_limit = int(get_config("num_teams", default=0))
    num_teams = Teams.query.filter_by(banned=False, hidden=False).count()
    if num_teams_limit and num_teams >= num_teams_limit:
        abort(
            403,
            description=f"Reached the maximum number of teams ({num_teams_limit}). Please join an existing team.",
        )

    user = get_current_user_attrs()
    if user.team_id:
        errors.append("You are already in a team. You cannot join another.")

    if request.method == "GET":
        team_size_limit = get_config("team_size", default=0)
        if team_size_limit:
            plural = "" if team_size_limit == 1 else "s"
            infos.append(
                "Teams are limited to {limit} member{plural}".format(
                    limit=team_size_limit, plural=plural
                )
            )
        return render_template("teams/new_team.html", infos=infos, errors=errors, user_login=current_login, extra=user_field)

    elif request.method == "POST":
        teamname = request.form.get("name", "").strip()
        passphrase = request.form.get("password", "").strip()

        website = request.form.get("website")
        affiliation = request.form.get("affiliation")

        user = get_current_user()

        existing_team = Teams.query.filter_by(name=teamname).first()
        if existing_team:
            errors.append("That team name is already taken")
        if not teamname:
            errors.append("That team name is invalid")

        # Process additional user fields
        fields = {}
        for field in TeamFields.query.all():
            fields[field.id] = field

        entries = {}
        for field_id, field in fields.items():
            value = request.form.get(f"fields[{field_id}]", "").strip()
            if field.required is True and (value is None or value == ""):
                errors.append("Please provide all required fields")
                break

            # Handle special casing of existing profile fields
            if field.name.lower() == "affiliation":
                affiliation = value
                break
            elif field.name.lower() == "website":
                website = value
                break

            if field.field_type == "boolean":
                entries[field_id] = bool(value)
            else:
                entries[field_id] = value

        if website:
            valid_website = validators.validate_url(website)
        else:
            valid_website = True

        if affiliation:
            valid_affiliation = len(affiliation) < 128
        else:
            valid_affiliation = True

        if valid_website is False:
            errors.append("Websites must be a proper URL starting with http or https")
        if valid_affiliation is False:
            errors.append("Please provide a shorter affiliation")

        if errors:
            return render_template("teams/new_team.html", errors=errors, user_login=current_login, extra=user_field), 403

        team = Teams(name=teamname, password=passphrase, captain_id=user.id)

        if website:
            team.website = website
        if affiliation:
            team.affiliation = affiliation

        db.session.add(team)
        db.session.commit()

        for field_id, value in entries.items():
            entry = TeamFieldEntries(field_id=field_id, value=value, team_id=team.id)
            db.session.add(entry)
        db.session.commit()

        user.team_id = team.id
        db.session.commit()

        clear_user_session(user_id=user.id)
        clear_team_session(team_id=team.id)

        return redirect(url_for("challenges.listing"))

@check_account_visibility
#@require_team_mode
def ctk_listing():
    q = request.args.get("q")
    field = request.args.get("field", "name")
    filters = []

    if field not in ("name", "affiliation", "website"):
        field = "name"

    if q:
        filters.append(getattr(Teams, field).like("%{}%".format(q)))

    teams = (
        Teams.query.filter_by(hidden=False, banned=False)
        .filter(*filters)
        .order_by(Teams.id.asc())
        .paginate(per_page=50)
    )

    #directorate docs monitoring
    docs = []
    if ctk_directorate_mode():
        ctk_teams =  Teams.query.filter_by(hidden=False, banned=False).all()
        for ctk_team in ctk_teams:
            docs.append({
                'team_id': ctk_team.id,
                'docs':docs_graded(mode='team', account_id=ctk_team.id)
            })
    #progess monitoring
    progress = []
    if is_admin():
        ctk_teams =  Teams.query.filter_by(hidden=False, banned=False).all()
        for ctk_team in ctk_teams:
            status = CTK_lockout(id=ctk_team.id, mode='team')
            for stats in status:
                progress.append({
                    'team_id': ctk_team.id,
                    'apprentice': stats['apprentice'][0]['progress'],
                    'warrior': stats['warrior'][0]['progress'],
                    'conqueror': stats['conqueror'][0]['progress']
                })                              

    # TEAM AFP/PA Major or Sub units @ /admin/config
    fields = TeamFieldEntries.query.join(Teams).all()
    fields_entries = []
    if(fields):
        for team_field in fields:
            fields_entries.append({
                'id': team_field.id,
                'team_id': team_field.team_id,
                'type': team_field.type,
                'value': team_field.value
             })

    args = dict(request.args)
    args.pop("page", 1)
    return render_template(
        "teams/teams.html",
        teams=teams,
        prev_page=url_for(request.endpoint, page=teams.prev_num, **args),
        next_page=url_for(request.endpoint, page=teams.next_num, **args),
        q=q,
        field=field,
        fields=fields_entries,
        docs=docs,
        directorate=ctk_directorate_mode(),
        admin=is_admin(),
        progress=progress
    )

@authed_only
def ctk_settings():
    infos = get_infos()
    errors = get_errors()

    user = get_current_user()
    name = user.name
    email = user.email
    website = user.website
    affiliation = user.affiliation
    country = user.country

    tokens = UserTokens.query.filter_by(user_id=user.id).all()
    user_config = CTK_Config.query.filter_by(id=user.id).first()

    prevent_name_change = get_config("prevent_name_change")
    user_field = UserFields.query.all()
    #unit Branch
    branch = ctk_branch()

    if get_config("verify_emails") and not user.verified:
        confirm_url = markup(url_for("auth.confirm"))
        infos.append(
            markup(
                "Your email address isn't confirmed!<br>"
                "Please check your email to confirm your email address.<br><br>"
                f'To have the confirmation email resent please <a href="{confirm_url}">click here</a>.'
            )
        )

    return render_template(
        "settings.html",
        name=name,
        email=email,
        website=website,
        affiliation=affiliation,
        country=country,
        tokens=tokens,
        prevent_name_change=prevent_name_change,
        infos=infos,
        errors=errors,
        user_config=user_config,
        branchs=branch,
        extra=user_field,
        user=user
    )

@check_account_visibility
def users_listing():
    q = request.args.get("q")
    field = request.args.get("field", "name")
    if field not in ("name", "affiliation", "website"):
        field = "name"

    filters = []
    if q:
        filters.append(getattr(CTK_Config, field).like("%{}%".format(q)))

    users = (
        CTK_Config.query.filter_by(banned=False, hidden=False)
        .filter(*filters)
        .filter_by(mode='users')
        .order_by(CTK_Config.id.asc())
        .paginate(per_page=50)
    )

    #directorate docs monitoring
    docs = []
    if ctk_directorate_mode():
        ctk_users = (
        CTK_Config.query.filter_by(banned=False, hidden=False)
        .filter_by(mode='users')
        .all()
        )
        for user in ctk_users:
            docs.append({
                'user': user.id,
                'docs':docs_graded(mode='user', account_id=user.id)
            })
    #progess monitoring
    progress = []
    if is_admin():
        ctk_users = (
        CTK_Config.query.filter_by(banned=False, hidden=False)
        .filter_by(mode='users')
        .all()
        )
        for user in ctk_users:
            status = CTK_lockout(id=user.id, mode='user')
            for stats in status:
                progress.append({
                    'user_id': user.id,
                    'apprentice': stats['apprentice'][0]['progress'],
                    'warrior': stats['warrior'][0]['progress'],
                    'conqueror': stats['conqueror'][0]['progress']
                })     

    fields = UserFieldEntries.query.join(Users).all()
    fields_entries = []
    if(fields):
        for user_field in fields:
            fields_entries.append({
                'id': user_field.id,
                'user_id': user_field.user_id,
                'field_name':user_field.name,
                'type': user_field.type,
                'value': user_field.value
            })

    args = dict(request.args)
    args.pop("page", 1)
    return render_template(
        "users/users.html",
        users=users,
        prev_page=url_for(request.endpoint, page=users.prev_num, **args),
        next_page=url_for(request.endpoint, page=users.next_num, **args),
        q=q,
        field=field,
        fields_entries=fields_entries,
        docs=docs,
        directorate=ctk_directorate_mode(),
        admin=is_admin(),
        progress=progress
    )

#c3 gt challenge solves
@c3.route('/api/v2/mysolves' ,defaults={"challenge_id": None}, methods=['GET'])
@c3.route('/api/v2/mysolves/<int:challenge_id>', methods=['GET'])
@authed_only
def get_mysolves_api(challenge_id):
    results = []
    user = get_current_user()
    published = db.session.query(docs_publish).first()
    #team mode support
    if ctk_teams_mode():
        if(challenge_id):
            solves_exist = db.session.query(Solves).filter_by(team_id = user.team_id, challenge_id = challenge_id).first()
            if solves_exist != None:
                results.append({
                        'challenge_id': solves_exist.challenge_id,
                        'date': solves_exist.date,
                        'id': solves_exist.id,
                        'ip': solves_exist.ip,
                        'account_id': solves_exist.team_id,
                        'mode': 'teams',
                        'type': solves_exist.type,
                        'user_id': solves_exist.user_id,
                        'solved_by_me': True,
                        'published': published.countermeasure_published
                        })
        else:
            solves_exist = db.session.query(Solves).filter_by(team_id = user.team_id).all()
            if solves_exist:
                for solved in solves_exist:
                    team_exist = db.session.query(Teams).filter_by(id = solved.team_id).first()
                    if team_exist:  
                        results.append({
                                'challenge_id': solved.challenge_id,
                                'date': solved.date,
                                'id': solved.id,
                                'ip': solved.ip,
                            # 'provided': solved.provided,
                                'account_id': solved.team_id,
                                'mode': 'teams',
                                'type': solved.type,
                                'user_id': solved.user_id,
                                'account_name': team_exist.name,
                                'published': published.countermeasure_published
                            })
        return jsonify(results)    
    #user mode support
    if ctk_users_mode():
        if(challenge_id):
            solves_exist = db.session.query(Solves).join(CTK_Config).filter(Solves.user_id == user.id, Solves.challenge_id == challenge_id).filter(CTK_Config.mode == 'users').first()
            if solves_exist != None:
                results.append({
                        'challenge_id': solves_exist.challenge_id,
                        'date': solves_exist.date,
                        'id': solves_exist.id,
                        'ip': solves_exist.ip,
                        'account_id': solves_exist.user_id,
                        'mode': 'users',
                        'type': solves_exist.type,
                        'user_id': solves_exist.user_id,
                        'solved_by_me': True,
                        'published': published.countermeasure_published
                        })
        else:
            solves_exist = db.session.query(Solves).join(CTK_Config).filter(Solves.user_id == user.id).filter(CTK_Config.mode == 'users').all()
            if solves_exist:
                for solved in solves_exist:
                    user_exist = db.session.query(Users).filter_by(id = solved.user_id).first()
                    if user_exist:  
                        results.append({
                                'challenge_id': solved.challenge_id,
                                'date': solved.date,
                                'id': solved.id,
                                'ip': solved.ip,
                                'account_id': solved.user_id,
                                'mode': 'users',
                                'type': solved.type,
                                'user_id': solved.user_id,
                                'account_name': user_exist.name,
                                'published': published.countermeasure_published
                            })
        return jsonify(results)      
    return jsonify(results)

#challenge attempt v2
@c3.route('/api/v2/attempt', methods=['GET', 'POST'])
@authed_only
@bypass_csrf_protection
def article_update_attempt():
    #override challenge attemp submissions
    return CTKpost()

#hints validation for team or Multiplayers
@c3.route('/api/v2/hints/<int:hint_id>', methods=['GET'])
@authed_only
def challenge_hint(hint_id):
    user = get_current_user()
    hint = Hints.query.filter_by(id=hint_id).first_or_404()

    # if is_admin():
    #     if request.args.get("preview", False):
    #         view = "admin"

    view = "unlocked"
    if hint.cost:
        view = "locked"
        if ctk_teams_mode():
            unlocked = HintUnlocks.query.filter_by(
                team_id=user.team_id, target=hint.id
            ).first()
            if unlocked:
                view = "unlocked"
                response = HintSchema(view=view).dump(hint)
                return {"success": True, "data": response.data}
        #set individual Players no changes
        if ctk_users_mode():
            return {"success": True, "data": None}
    return {"success": False, "data": None}

#Cyber eX Scoreboards Multiplayers | Individuals
@check_account_visibility
@check_score_visibility
@cache.cached(timeout=60, key_prefix=make_cache_key)
@c3.route('/api/v2/scoreboard/top/<count>', methods=['GET'])
def get_scoreboard_top(count):
    response = {}
    category = {}
    mode = {}
    user = get_current_user()
    # standings = get_standings(count=count)
    if ctk_users_mode():
        selected = db.session.query(C3_selected_cat).filter_by(user_id=user.id).first()
        if selected is None:
            return redirect("challenge-category", code=303)
        c3_cat = db.session.query(C3_category).filter_by(id=selected.ctf_category_id).first()
        category = c3_cat.category
        mode = "Individuals"
        standings = custom_get_standings(c3=selected.ctf_category_id)
        players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'users')
        all_players = players.all()
        standings = get_user_score(users=all_players, c3=selected.ctf_category_id)
        team_ids = [team['user_id'] for team in standings]
        c3_category_chals = db.session.query(C3CategoryChallenge).filter(C3CategoryChallenge.c3_category==selected.ctf_category_id).all()
        c3_category_chals_ids = [chals.id for chals in c3_category_chals]
        solves = Solves.query.filter(Solves.user_id.in_(team_ids), Solves.challenge_id.in_(c3_category_chals_ids))
        # solves = Solves.query.filter(Solves.user_id.in_(team_ids))
        awards = Awards.query.filter(Awards.user_id.in_(team_ids))

        freeze = get_config("freeze")

        if freeze:
            solves = solves.filter(Solves.date < unix_time_to_utc(freeze))
            awards = awards.filter(Awards.date < unix_time_to_utc(freeze))

        solves = solves.all()
        awards = awards.all()

        # Build a mapping of accounts to their solves and awards
        solves_mapper = defaultdict(list)
        for solve in solves:
            solves_mapper[solve.user_id].append(
                {
                    "challenge_id": solve.challenge_id,
                    "account_id": solve.user_id,
                    "team_id": solve.team_id,
                    "user_id": solve.user_id,
                    "value": solve.challenge.value,
                    "date": isoformat(solve.date),
                }
            )

        for award in awards:
            solves_mapper[award.user_id].append(
                {
                    "challenge_id": None,
                    "account_id": award.user_id,
                    "team_id": award.team_id,
                    "user_id": award.user_id,
                    "value": award.value,
                    "date": isoformat(award.date),
                }
            )

        # Sort all solves by date
        for team_id in solves_mapper:
            solves_mapper[team_id] = sorted(
                solves_mapper[team_id], key=lambda k: k["date"]
            )

        for i, _team in enumerate(team_ids):
            response[i + 1] = {
                "id": standings[i]['user_id'],
                "name": standings[i]['name'],
                "solves": solves_mapper.get(standings[i]['user_id'], []),
            }

    if ctk_teams_mode():
        selected = db.session.query(C3_selected_cat).filter_by(team_id=user.team_id).first()
        if selected is None:
            return redirect("challenge-category", code=303)
        standings = custom_get_standings(c3=selected.ctf_category_id)
        c3_cat = db.session.query(C3_category).filter_by(id=selected.ctf_category_id).first()
        category = c3_cat.category
        mode = "Multiplayers"
        team_ids = [team.account_id for team in standings]
        c3_category_chals = db.session.query(C3CategoryChallenge).filter(C3CategoryChallenge.c3_category==selected.ctf_category_id).all()
        c3_category_chals_ids = [chals.id for chals in c3_category_chals]
        solves = Solves.query.filter(Solves.team_id.in_(team_ids), Solves.challenge_id.in_(c3_category_chals_ids))
        # solves = Solves.query.filter(Solves.team_id.in_(team_ids))
        awards = Awards.query.filter(Awards.team_id.in_(team_ids))

        freeze = get_config("freeze")

        if freeze:
            solves = solves.filter(Solves.date < unix_time_to_utc(freeze))
            awards = awards.filter(Awards.date < unix_time_to_utc(freeze))

        solves = solves.all()
        awards = awards.all()

        # Build a mapping of accounts to their solves and awards
        solves_mapper = defaultdict(list)
        for solve in solves:
            solves_mapper[solve.team_id].append(
                {
                    "challenge_id": solve.challenge_id,
                    "account_id": solve.team_id,
                    "team_id": solve.team_id,
                    "user_id": solve.user_id,
                    "value": solve.challenge.value,
                    "date": isoformat(solve.date),
                }
            )

        for award in awards:
            solves_mapper[award.team_id].append(
                {
                    "challenge_id": None,
                    "account_id": award.team_id,
                    "team_id": award.team_id,
                    "user_id": award.user_id,
                    "value": award.value,
                    "date": isoformat(award.date),
                }
            )

        # Sort all solves by date
        for team_id in solves_mapper:
            solves_mapper[team_id] = sorted(
                solves_mapper[team_id], key=lambda k: k["date"]
            )

        for i, _team in enumerate(team_ids):
            response[i + 1] = {
                "id": standings[i].account_id,
                "name": standings[i].name,
                "solves": solves_mapper.get(standings[i].account_id, []),
            }


    return {"success": True, "data": response, "category": category, "mode": mode}

#ovel all multi Players scoreboard
@cache.cached(timeout=60)
@c3.route('/api/v2/scoreboard/<mode>', methods=['GET'])
def get_alltime_team_scoreboard_top(mode):
    response = {}
    if mode == 'multiplayers':
        #standings = get_team_standings()
        standings = All_scores(users='teams')
        team_ids = [team['account_id'] for team in standings['overall']]
        solves = Solves.query.filter(Solves.team_id.in_(team_ids))
        awards = Awards.query.filter(Awards.team_id.in_(team_ids))

        freeze = get_config("freeze")

        if freeze:
            solves = solves.filter(Solves.date < unix_time_to_utc(freeze))
            awards = awards.filter(Awards.date < unix_time_to_utc(freeze))

        solves = solves.all()
        awards = awards.all()

        # Build a mapping of accounts to their solves and awards
        solves_mapper = defaultdict(list)
        for solve in solves:
            solves_mapper[solve.team_id].append(
                {
                    "challenge_id": solve.challenge_id,
                    "account_id": solve.team_id,
                    "team_id": solve.team_id,
                    "user_id": solve.user_id,
                    "value": solve.challenge.value,
                    "date": isoformat(solve.date),
                }
            )

        for award in awards:
            solves_mapper[award.team_id].append(
                {
                    "challenge_id": None,
                    "account_id": award.team_id,
                    "team_id": award.team_id,
                    "user_id": award.user_id,
                    "value": award.value,
                    "date": isoformat(award.date),
                }
            )
        
        #custom awards
        users = Users.query.filter(Users.team_id.in_(team_ids))
        for user in users.all():
            ctk_awards = Awards.query.filter_by(user_id=user.id, team_id=None).all()
            for ctk_award in ctk_awards:
                solves_mapper[user.team_id].append(

                    {
                        "challenge_id": None,
                        "account_id": user.team_id,
                        "team_id": user.team_id,
                        "user_id": ctk_award.user_id,
                        "value": ctk_award.value,
                        "date": isoformat(ctk_award.date),
                    }
                )
                   

        # Sort all solves by date
        for team_id in solves_mapper:
            solves_mapper[team_id] = sorted(
                solves_mapper[team_id], key=lambda k: k["date"]
            )

        for i, _team in enumerate(team_ids):
            response[i + 1] = {
                "id": standings['overall'][i]['account_id'],
                "name": standings['overall'][i]['name'],
                "solves": solves_mapper.get(standings['overall'][i]['account_id'], []),
            }

    if mode == 'individuals':
        standings = get_user_standings()
        players = CTK_Config.query.filter(CTK_Config.mode=='users', CTK_Config.type != 'admin').all()
        user_ids = [user.id for user in players]
        new_standings = [j for i, j in enumerate(standings) if j.user_id in user_ids]
        solves = Solves.query.filter(Solves.user_id.in_(user_ids))
        awards = Awards.query.filter(Awards.user_id.in_(user_ids))

        freeze = get_config("freeze")

        if freeze:
            solves = solves.filter(Solves.date < unix_time_to_utc(freeze),Solves.user_id.in_(user_ids))
            awards = awards.filter(Awards.date < unix_time_to_utc(freeze), Awards.user_id.in_(user_ids))

        solves = solves.all()
        awards = awards.all()

        # Build a mapping of accounts to their solves and awards
        solves_mapper = defaultdict(list)
        for solve in solves:
            solves_mapper[solve.user_id].append(
                {
                    "challenge_id": solve.challenge_id,
                    "account_id": solve.user_id,
                    "team_id": solve.team_id,
                    "user_id": solve.user_id,
                    "value": solve.challenge.value,
                    "date": isoformat(solve.date),
                }
            )

        for award in awards:
            solves_mapper[award.user_id].append(
                {
                    "challenge_id": None,
                    "account_id": award.user_id,
                    "team_id": award.team_id,
                    "user_id": award.user_id,
                    "value": award.value,
                    "date": isoformat(award.date),
                }
            )
    
        # Sort all solves by date
        for user_id in solves_mapper:
            solves_mapper[user_id] = sorted(
                solves_mapper[user_id], key=lambda k: k["date"]
            )

        for i, standing in enumerate(new_standings):
            response[i + 1] = {
                "id": standing.user_id,
                "name": standing.name,
                "solves": solves_mapper.get(standing.user_id, []),
            }
    return {"success": True, "data": response}


#get chrnicles in public
@c3.route('/api/v2/chronicles/<mode>', methods=['GET'])
def multiplayers_chronicles_api(mode):
    results = []
    if request.method == 'GET':
        if mode == 'multiplayers':
            teams = Teams.query.filter_by(hidden=False, banned=False).all()
            if teams:
                for team in teams:
                    chronicle = ctk_writeups_scores(mode='team', account_id=team.id)
                    results.append({
                        'account_id':team.id,
                        'name':team.name,
                        'value':chronicle
                    })      
    return {"success": True, "data": results} 

#get countermeasures in public
@c3.route('/api/v2/countermeasures/<mode>', methods=['GET'])
def multiplayers_countermeasures_api(mode):
    results = []
    if request.method == 'GET':
        if mode == 'multiplayers':
            teams = Teams.query.filter_by(hidden=False, banned=False).all()
            if teams:
                for team in teams:
                    chronicle = ctk_countermeasure_scores(mode='team', account_id=team.id)
                    results.append({
                        'account_id':team.id,
                        'name':team.name,
                        'value':chronicle
                    })      
    return {"success": True, "data": results}

#CTK Registration for Users Mode | Teams Mode
@admins_only
@bypass_csrf_protection
@c3.route('/admin/users/new', methods=['GET', 'POST'])
def ctk_admin_register():
    errors = get_errors()
    message = []
    user_field = UserFields.query.all()
    #unit Branch
    branch = ctk_branch()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email_address = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        user_mode = request.form.get("user-mode", "").strip()
     
        website = request.form.get("website")
        affiliation = request.form.get("affiliation")
        country = request.form.get("country")

        name_len = len(name) == 0
        name_column = column('name')
        id_column = column('id')
        email_column = column('email')
        names = Users.query.add_columns(name_column, id_column).filter_by(name=name).first()
        emails = (
            Users.query.add_columns(email_column, id_column)
            .filter_by(email=email_address)
            .first()
        )
        pass_short = len(password) == 0
        pass_long = len(password) > 128
        valid_email = validators.validate_email(email_address)
        team_name_email_check = validators.validate_email(name)

        # Process additional user fields
        fields = {}
        for field in UserFields.query.all():
            fields[field.id] = field
        
        entries = {}
        for field_id, field in fields.items():
            value = request.form.get(f"fields[{field_id}]", "").strip()
            if field.required is True and (value is None or value == ""):
                errors.append("Please provide all required fields")
                break

            # Handle special casing of existing profile fields
            if field.name.lower() == "affiliation":
                affiliation = value
                break
            elif field.name.lower() == "website":
                website = value
                break

            if field.field_type == "boolean":
                entries[field_id] = bool(value)
            else:
                entries[field_id] = value

        if country:
            try:
                validators.validate_country_code(country)
                valid_country = True
            except ValidationError:
                valid_country = False
        else:
            valid_country = True

        if website:
            valid_website = validators.validate_url(website)
        else:
            valid_website = True

        if affiliation:
            valid_affiliation = len(affiliation) < 128
        else:
            valid_affiliation = True

        if not valid_email:
            errors.append("Please enter a valid email address")
        if email.check_email_is_whitelisted(email_address) is False:
            errors.append(
                "Only email addresses under {domains} may register".format(
                    domains=get_config("domain_whitelist")
                )
            )
        if names:
            errors.append("That user name is already taken")
        if team_name_email_check is True:
            errors.append("Your user name cannot be an email address")
        if emails:
            errors.append("That email has already been used")
        if pass_short:
            errors.append("Pick a longer password")
        if pass_long:
            errors.append("Pick a shorter password")
        if name_len:
            errors.append("Pick a longer user name")
        if valid_website is False:
            errors.append("Websites must be a proper URL starting with http or https")
        if valid_country is False:
            errors.append("Invalid country")
        if valid_affiliation is False:
            errors.append("Please provide a shorter affiliation")

        if len(errors) > 0:
            return render_template(
                "admin/users/new.html",
                errors=errors,
                name=request.form["name"],
                email=request.form["email"],
                password=request.form["password"],
            )
        else:
            with app.app_context():
                user = CTK_Config(name=name, email=email_address, password=password, mode=user_mode)

                if website:
                    user.website = website
                if affiliation:
                    user.affiliation = affiliation
                if country:
                    user.country = country

                db.session.add(user)
                db.session.commit()
                db.session.flush()

                for field_id, value in entries.items():
                    entry = UserFieldEntries(
                        field_id=field_id, value=value, user_id=user.id
                    )
                    db.session.add(entry)
                db.session.commit()
                #successfull messsage notifications
                message.append({
                "message":"Welcome to Cyber Exercise for Excellence!. Your username: {name} is successfully registered!. Please login to continue.".format(
                    name=name)
                })
        log(
            "registrations",
            format="[{date}] {ip} - {name} registered with {email}",
            name=user.name,
            email=user.email,
        )
        db.session.close()

        # return render_template("admin/users/{user_id}".format(user_id=user.id))
        return redirect(url_for('admin.users_detail',user_id=user.id))
    else:
        return render_template("admin/users/new.html", errors=errors, branchs=branch, extra=user_field)

#directorate scoring API
@authed_only
@bypass_csrf_protection
@c3.route('/api/v2/chronicles/directorate/<int:id>', methods=['GET', 'POST'])
def ctk_directorate_chronicles(id):
    results = []
    rater = []
    rated = False
    user = get_current_user()
    ctk_user = CTK_Config.query.filter_by(mode='directorate').all()
    #set super admin privilege
    if is_admin():
            rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = ChroniclesDirectorate.query.filter_by(writeups_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'writeups_id':rate.writeups_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_points':rate.rater_points,
                                'date':rate.date
                            })
    if ctk_directorate_mode():
        if request.method == 'GET':
            rater_grade_exist = ChroniclesDirectorate.query.filter_by(writeups_id=id, directorate_id=user.id).first()
            if rater_grade_exist != None:
                if rater_grade_exist.directorate_id == user.id:
                    rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = ChroniclesDirectorate.query.filter_by(writeups_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'writeups_id':rate.writeups_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_points':rate.rater_points,
                                'date':rate.date
                            })
    
        #Saved Directorate Grade
        if request.method == 'POST':
            rater_points = request.form['counter-points']
            if int(rater_points) > 100:
                abort(404)
            site_url = request.form['site_url']
            rater_grade = ChroniclesDirectorate.query.filter_by(writeups_id=id, directorate_id=user.id).first()
            if rater_grade != None:
                # abort(404)
                db.session.query(ChroniclesDirectorate).filter_by(writeups_id=id, directorate_id=user.id).update(dict(rater_points = int(rater_points)))
                db.session.commit()
                return redirect(site_url+"#chronicles-row")
            else:
                db.session.add(ChroniclesDirectorate(writeups_id = id, directorate_id = user.id, rater_points = int(rater_points)))
                db.session.commit()
                return redirect(site_url+"#chronicles-row")
                
    #teams ratings breakdown
    if ctk_teams_mode():
        if request.method == 'GET':
            rater_grade_exist = ChroniclesDirectorate.query.filter_by(writeups_id=id, directorate_id=user.id).first()
            if rater_grade_exist != None:
                if rater_grade_exist.directorate_id == user.id:
                    rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = ChroniclesDirectorate.query.filter_by(writeups_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'writeups_id':rate.writeups_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_points':rate.rater_points,
                                'date':rate.date
                            })
    return jsonify(results=results, rater=rater, rated=rated)

#directorate scoring API for countermeasures
@authed_only
@bypass_csrf_protection
@c3.route('/api/v2/countermeasures/directorate/<int:id>', methods=['GET', 'POST'])
def ctk_directorate_countermeasure(id):
    results = []
    rater = []
    rated = False
    user = get_current_user()
    ctk_user = CTK_Config.query.filter_by(mode='directorate').all()
    #set admin privilege 
    if is_admin():
        if request.method == 'GET':
            rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = CountermeasureDirectorate.query.filter_by(countermeasures_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'countermeasures_id':rate.countermeasures_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_points':rate.rater_points,
                                'date':rate.date
                            })
    if ctk_directorate_mode():
        if request.method == 'GET':
            rater_grade_exist = CountermeasureDirectorate.query.filter_by(countermeasures_id=id, directorate_id=user.id).first()
            if rater_grade_exist != None:
                if rater_grade_exist.directorate_id == user.id:
                    rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = CountermeasureDirectorate.query.filter_by(countermeasures_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'countermeasures_id':rate.countermeasures_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_points':rate.rater_points,
                                'date':rate.date
                            })
        #Saved Directorate Grade
        if request.method == 'POST':
            rater_points = request.form['counter-points']
            if int(rater_points) > 100:
                abort(404)
            site_url = request.form['site_url']
            rater_grade = CountermeasureDirectorate.query.filter_by(countermeasures_id=id, directorate_id=user.id).first()
            if rater_grade != None:
                # abort(404)
                db.session.query(CountermeasureDirectorate).filter_by(countermeasures_id=id, directorate_id=user.id).update(dict(rater_points = int(rater_points)))
                db.session.commit()
                return redirect(site_url+"#countermeasure-row")
            else:
                db.session.add(CountermeasureDirectorate(countermeasures_id = id, directorate_id = user.id, rater_points = int(rater_points)))
                db.session.commit()
                return redirect(site_url+"#countermeasure-row")

    #teams rating view
    if ctk_teams_mode():
        if request.method == 'GET':
            rater_grade_exist = CountermeasureDirectorate.query.filter_by(countermeasures_id=id, directorate_id=user.id).first()
            if rater_grade_exist != None:
                if rater_grade_exist.directorate_id == user.id:
                    rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = CountermeasureDirectorate.query.filter_by(countermeasures_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'countermeasures_id':rate.countermeasures_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_points':rate.rater_points,
                                'date':rate.date
                            })
    return jsonify(results=results, rater=rater, rated=rated)

#directorate scoring API for Knowledge-Well
@authed_only
@bypass_csrf_protection
@c3.route('/api/v2/knowledge-well/directorate/<int:id>', methods=['GET', 'POST'])
def ctk_directorate_knowledge(id):
    results = []
    rater = []
    rated = False
    user = get_current_user()
    ctk_user = CTK_Config.query.filter_by(mode='directorate').all()
    #Set Admin privilege
    if is_admin():
        if request.method == 'GET':
            rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = KnowledgeDirectorate.query.filter_by(knowledge_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'knowledge_id':rate.knowledge_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_points':rate.rater_points,
                                'date':rate.date
                            })
    if ctk_directorate_mode():
        if request.method == 'GET':
            rater_grade_exist = KnowledgeDirectorate.query.filter_by(knowledge_id=id, directorate_id=user.id).first()
            if rater_grade_exist != None:
                if rater_grade_exist.directorate_id == user.id:
                    rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = KnowledgeDirectorate.query.filter_by(knowledge_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'knowledge_id':rate.knowledge_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_points':rate.rater_points,
                                'date':rate.date
                            })
        #Saved Directorate Grade
        if request.method == 'POST':
            rater_points = request.form['counter-points']
            if int(rater_points) > 100:
                abort(404)
            site_url = request.form['site_url']
            rater_grade = KnowledgeDirectorate.query.filter_by(knowledge_id=id, directorate_id=user.id).first()
            if rater_grade != None:
                # abort(404)
                db.session.query(KnowledgeDirectorate).filter_by(knowledge_id=id, directorate_id=user.id).update(dict(rater_points = int(rater_points)))
                db.session.commit()
                return redirect(site_url+"#knowledge-row")
            else:
                db.session.add(KnowledgeDirectorate(knowledge_id = id, directorate_id = user.id, rater_points = int(rater_points)))
                db.session.commit()
                return redirect(site_url+"#knowledge-row")
    
    #user in team query ratings
    if ctk_teams_mode():
        if request.method == 'GET':
            rater_grade_exist = KnowledgeDirectorate.query.filter_by(knowledge_id=id, directorate_id=user.id).first()
            if rater_grade_exist != None:
                if rater_grade_exist.directorate_id == user.id:
                    rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = KnowledgeDirectorate.query.filter_by(knowledge_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'knowledge_id':rate.knowledge_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_points':rate.rater_points,
                                'date':rate.date
                            })
    return jsonify(results=results, rater=rater, rated=rated)

#dashboard of Cyber eX Directorates
@authed_only
@c3.route('/admin/directorate', methods=['GET', 'POST'])
def dashboard_drectorate():
    if ctk_directorate_mode():
        statistics = ctk_statistics()
        user = get_current_user()
        fields = UserFieldEntries.query.join(Users).filter(Users.id==user.id).all()
        user_entries = {}
        if len(fields) > 0:
            for user_field in fields:
                if user_field.name == 'Full Name':
                    user_entries = {
                        'id': user_field.id,
                        'user_id': user_field.user_id,
                        'field_name':user_field.name,
                        'type': user_field.type,
                        'name': user_field.value
                    }
        #top 
        team_top = []
        top_list_users = []
        # top 10 teams
        top_5 = All_scores(users="teams")
        for i, top in  enumerate(top_5['overall']):
            if i > 9 :break
            team_top.append(top)
        #top 10 users
        top_5_users = All_scores(users="users")
        for i, top_users in  enumerate(top_5_users['users']):
            if i > 9 :break
            top_list_users.append(top_users)
    else:
        return abort(404)
    #chronicles and countermesures views permission
    published = db.session.query(docs_publish).first()
    document_chart = False
    #if published.countermeasure_published == True or ctk_directorate_mode():
    if published.countermeasure_published == True:
        document_chart = True
    return render_template("plugins/custom/templates/dashboard/dashboard.html", fields=user_entries, statistics=statistics.json, team_top=team_top, top_users=top_list_users, published=document_chart)

#overide login for Directorate Dashboard
@ratelimit(method="POST", limit=10, interval=5)
def ctk_login():
    errors = get_errors()
    if request.method == "POST":
        name = request.form["name"]
        # Check if the user submitted an email address or a team name
        if validators.validate_email(name) is True:
            user = Users.query.filter_by(email=name).first()
        else:
            user = Users.query.filter_by(name=name).first()

        if user:
            if user.password is None:
                errors.append(
                    "Your account was registered with a 3rd party authentication provider. "
                    "Please try logging in with a configured authentication provider."
                )
                return render_template("login.html", errors=errors)

            if user and verify_password(request.form["password"], user.password):
                session.regenerate()

                login_user(user)
                log("logins", "[{date}] {ip} - {name} logged in", name=user.name)

                db.session.close()
                if request.args.get("next") and validators.is_safe_url(
                    request.args.get("next")
                ):
                    return redirect(request.args.get("next"))
                if ctk_directorate_mode():
                    return redirect(url_for("c3.dashboard_drectorate_url"))
                return redirect(url_for("challenges.listing"))

            else:
                # This user exists but the password is wrong
                log(
                    "logins",
                    "[{date}] {ip} - submitted invalid password for {name}",
                    name=user.name,
                )
                errors.append("Your username or password is incorrect")
                db.session.close()
                return render_template("login.html", errors=errors)
        else:
            # This user just doesn't exist
            log("logins", "[{date}] {ip} - submitted invalid account information")
            errors.append("Your username or password is incorrect")
            db.session.close()
            return render_template("login.html", errors=errors)
    else:
        db.session.close()
        return render_template("login.html", errors=errors)

#api statistics
@authed_only
@c3.route('/api/v2/statistics', methods=['GET'])
def ctk_statistics():
    user = get_current_user()
    if ctk_directorate_mode():
        teams = Teams.query.filter_by(banned=False, hidden=False).all()
        team_ids = [team.id for team in teams]
        #team Knowledge Well
        knowledge_well = KnowledgeWellDocs.query.filter(KnowledgeWellDocs.team_id.in_(team_ids))
        total_submission_knowledge = knowledge_well.count()
        total_knowledge = knowledge_well.all()
        knowledge_ids = [knowledge.id for knowledge in total_knowledge]
        graded_knowledge = KnowledgeDirectorate.query.filter(KnowledgeDirectorate.directorate_id==user.id, KnowledgeDirectorate.knowledge_id.in_(knowledge_ids)).count()
        #teams chronicles
        chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.team_id.in_(team_ids))
        total_submission = chronicles.count()
        total_chronicles = chronicles.all()
        chronicles_ids = [chronicle.id for chronicle in total_chronicles]
        graded_chronicles = ChroniclesDirectorate.query.filter(ChroniclesDirectorate.directorate_id==user.id, ChroniclesDirectorate.writeups_id.in_(chronicles_ids)).count()
        #team countermeasures
        countermeasure = ChallengeCounterMeasure.query.filter(ChallengeCounterMeasure.team_id.in_(team_ids))
        total_submission_counter =  countermeasure.count()
        total_counter = countermeasure.all()
        counter_ids = [counterm.id for counterm in total_counter]
        graded_counter = CountermeasureDirectorate.query.filter( CountermeasureDirectorate.directorate_id==user.id,  CountermeasureDirectorate.countermeasures_id.in_(counter_ids)).count()
        team = {
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
        players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'users')
        all_players = players.all()
        user_ids = [individual.id for individual in  all_players]
        #Individuals Knowledge Well
        knowledge_well_users = KnowledgeWellDocs.query.filter(KnowledgeWellDocs.user_id.in_(user_ids))
        total_submission_knowledge_users = knowledge_well_users.count()
        total_knowledge_users = knowledge_well_users.all()
        knowledge_ids_users = [knowledge.id for knowledge in total_knowledge_users]
        graded_knowledge_users = KnowledgeDirectorate.query.filter(KnowledgeDirectorate.directorate_id==user.id, KnowledgeDirectorate.knowledge_id.in_(knowledge_ids_users)).count()
        #individuals chronicles
        user_chronicles = ChallengeWriteUps.query.filter(ChallengeWriteUps.user_id.in_(user_ids))
        total_user_submission = user_chronicles.count()
        total_user_chronicles = user_chronicles.all()
        user_chronicles_ids = [chronicleuser.id for chronicleuser in total_user_chronicles]
        graded_userchronicles = ChroniclesDirectorate.query.filter(ChroniclesDirectorate.directorate_id==user.id, ChroniclesDirectorate.writeups_id.in_(user_chronicles_ids)).count()
        #individuals countermeasures
        user_countermeasure = ChallengeCounterMeasure.query.filter(ChallengeCounterMeasure.user_id.in_(user_ids))
        total_user_submission_counter =user_countermeasure.count()
        total_user_counter = user_countermeasure.all()
        user_counter_ids = [counteruser.id for counteruser in total_user_counter]
        user_graded_counter = CountermeasureDirectorate.query.filter(CountermeasureDirectorate.directorate_id==user.id,  CountermeasureDirectorate.countermeasures_id.in_(user_counter_ids)).count()
        user = {
             'knowledgeWell' : {
                'count': total_submission_knowledge_users,
                'graded': graded_knowledge_users,
                'not_graded': (total_submission_knowledge_users - graded_knowledge_users)
            },
             'chronicles' : {
                'count': total_user_submission,
                'graded': graded_userchronicles,
                'not_graded': (total_user_submission - graded_userchronicles)
            },
            'countermeasures':{
                'count': total_user_submission_counter,
                'graded': user_graded_counter,
                'not_graded': (total_user_submission_counter - user_graded_counter)
            }
        }
       
    else:
        return abort(404)
    return jsonify(team=team, user=user)

#overall average score of Knowledge-Well
@c3.route('/api/v2/directorate/knowledge/<mode>/<int:account_id>', methods=['GET', 'POST'])
def ctk_directorate_average_knowledge(mode, account_id):
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
                    sum = sum + (int(list_rated['rater'][0]['grade']))
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'knowledge_id': list_rated['knowledge_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(int(sum) / int(count)),
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
    return jsonify(data=result)

#overall average score of chronicles
# @authed_only
@c3.route('/api/v2/directorate/chronicles/<mode>/<int:account_id>', methods=['GET', 'POST'])
def ctk_directorate_average_chronicles(mode, account_id):
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
                    sum = sum + (int(list_rated['rater'][0]['grade']))
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'writeups_id': list_rated['writeups_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(int(sum) / int(count)),
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
    return jsonify(data=result)

#overall average score of countermeasures
# @authed_only
@c3.route('/api/v2/directorate/countermeasures/<mode>/<int:account_id>', methods=['GET', 'POST'])
def ctk_directorate_average_countermeasures(mode, account_id):
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
                    sum = sum + (int(list_rated['rater'][0]['grade']))
                    groups.append({
                        'rater_name': list_rated['rater'][0]['rater_name'],
                        'countermeasures_id': list_rated['countermeasures_id'],
                        'grade': list_rated['rater'][0]['grade']
                    })
                count = len(groups)
            final_count.append({
                list:groups,
                'average': int(int(sum) / int(count)),
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
    return jsonify(data=result)

# @authed_only
@c3.route('/api/v2/directorate/documentation/chronicles/<mode>', methods=['GET', 'POST'])
def ctk_directorate_OverallChroniclesaverage(mode):
    results = []
    if request.method == 'GET':
        if mode == 'multiplayers':
            teams = Teams.query.filter_by(hidden=False, banned=False).all()
            if teams:
                for team in teams:
                    # total = 0
                    # directorateChronicles = ctk_directorate_average_chronicles(mode='team', account_id=team.id)
                    # graded = directorateChronicles.json
                    # for grade in graded['data']:
                    #     total = total + (int(grade['average']))
                    total_chronicles = ctk_writeups_scores(mode='team', account_id=team.id)
                    results.append({
                        'account_id':team.id,
                        'name':team.name,
                        'value':total_chronicles
                    }) 
        #users
        if mode == 'individuals':
            players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'users')
            all_players = players.all()
            if all_players:
                for standing in get_user_standings():
                    for user_player in all_players:
                        # total = 0
                        # if user_player.id == standing.user_id:
                        #     directorateChronicles = ctk_directorate_average_chronicles(mode='user', account_id=standing.user_id)
                        #     graded = directorateChronicles.json
                        #     for grade in graded['data']:
                        #         total = total+int(grade['average'])
                        #     results.append({
                        #         'account_id':standing.user_id,
                        #         'name':standing.name,
                        #         'value':total
                        #      }) 
                        total_chronicles = ctk_writeups_scores(mode='user', account_id=user_player.id)
                        results.append({
                            'account_id':user_player.id,
                            'name':user_player.name,
                            'value':total_chronicles
                        }) 
    return {"success": True, "data": results}

# @authed_only
@c3.route('/api/v2/directorate/documentation/countermeasures/<mode>', methods=['GET', 'POST'])
def ctk_directorate_OverallCountermeasuresaverage(mode):
    results = []
    if request.method == 'GET':
        if mode == 'multiplayers':
            teams = Teams.query.filter_by(hidden=False, banned=False).all()
            if teams:
                for team in teams:
                    # total = 0
                    # directorateChronicles = ctk_directorate_average_countermeasures(mode='team', account_id=team.id)
                    # graded = directorateChronicles.json
                    # for grade in graded['data']:
                    #     total = total + (int(grade['average']))
                    total_counter = ctk_countermeasure_scores(mode='team',account_id=team.id)
                    results.append({
                        'account_id':team.id,
                        'name':team.name,
                        'value':total_counter
                    }) 
        #users / Individuals
        if mode == 'individuals':  
            players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'users')
            all_players = players.all()
            if all_players:
                for standing in get_user_standings():
                    for user_player in all_players:
                        # total = 0
                        # if user_player.id == standing.user_id:
                        #     directorate_countermeasures = ctk_directorate_average_countermeasures(mode='user', account_id=standing.user_id) 
                        #     graded = directorate_countermeasures.json
                        #     for grade in graded['data']:
                        #         total = total+int(grade['average'])
                        #     results.append({
                        #         'account_id': standing.user_id,
                        #         'name': standing.name,
                        #         'value':total
                        #     }) 
                        total_counter = ctk_countermeasure_scores(mode='user',account_id=user_player.id)
                        results.append({
                            'account_id':user_player.id,
                            'name':user_player.name,
                            'value':total_counter
                        })   
    return {"success": True, "data": results}

#get the knowledge Well Average
@c3.route('/api/v2/directorate/documentation/knowledge/<mode>', methods=['GET', 'POST'])
def ctk_directorate_OverallKnowledgeaverage(mode):
    results = []
    if request.method == 'GET':
        if mode == 'multiplayers':
            teams = Teams.query.filter_by(hidden=False, banned=False).all()
            if teams:
                for team in teams:
                    # total = 0
                    # directorateKnowledge = ctk_directorate_average_knowledge(mode='team', account_id=team.id)
                    # graded = directorateKnowledge.json
                    # for grade in graded['data']:
                    #     total = total + (int(grade['average']))
                    total_knowledge = ctk_knowledge_scores(mode='team', account_id=team.id)
                    results.append({
                        'account_id':team.id,
                        'name':team.name,
                        'value':total_knowledge
                    }) 
        #users / Individuals
        if mode == 'individuals':  
            players = db.session.query(CTK_Config).filter(CTK_Config.type != 'admin').filter(CTK_Config.mode == 'users')
            all_players = players.all()
            if all_players:
                for standing in get_user_standings():
                    for user_player in all_players:
                        # total = 0
                        # if user_player.id == standing.user_id:
                        #     ctk_directorate_knowledge = ctk_directorate_average_knowledge(mode='user', account_id=standing.user_id) 
                        #     graded = ctk_directorate_knowledge.json
                        #     for grade in graded['data']:
                        #         total = total+int(grade['average'])
                        #     results.append({
                        #         'account_id': standing.user_id,
                        #         'name': standing.name,
                        #         'value':total
                        #     })  
                        total_knowledge = ctk_knowledge_scores(mode='user', account_id=user_player.id)
                        results.append({
                            'account_id':user_player.id,
                            'name':user_player.name,
                            'value':total_knowledge
                        })  
    return {"success": True, "data": results}

#override navbar
@authed_only
@c3.route('/api/v2/who_login', methods=['GET'])
def ctk_who_login():
    response = {
        'multiplayer': ctk_teams_mode(),
        'individual' : ctk_users_mode(),
        'directorate': ctk_directorate_mode(),
    }
    return jsonify(data=response)

#set custom API for knowledge Well
@c3.route('/api/v2/knowledgeWell/<int:id>', methods=['DELETE'])
@bypass_csrf_protection
@authed_only
def admin_knowledge_api(id):
    results = []
    resp = {}
    #Delete knowledge well
    if request.method == 'DELETE':
        db.session.query(KnowledgeWellDocs).filter_by(id=id).delete()
        db.session.commit()
        resp = jsonify({'message' : 'Knowledge Well successfully deleted!'})
        resp.status_code = 200
        return resp    
    return jsonify(results)

#Calculate average Knowledge Well Score
@authed_only
@admins_only
@bypass_csrf_protection
@c3.route('/api/v2/knowledgeWell-Grade/<mode>', methods=['GET','POST'])
def admin_knowledge_grade(mode):
    message = ''
    if request.method == 'POST':
        if mode == 'multiplayers':
            teams = Teams.query.filter_by(hidden=False, banned=False).all()
            if teams:
                for team in teams:
                    directorateKnowledge = ctk_directorate_averageScore_knowledge(mode='team', account_id=team.id)
                    # graded = directorateKnowledge.json
                    for grade in directorateKnowledge['data']:
                        id = list(grade.keys())
                        db.session.query(KnowledgeWellDocs).filter_by( id = int(id[0]), team_id = team.id).update(dict(points = int(grade['average'])))
                        db.session.commit()
                message = 'Knowledge Well Already Recorded!'
    return jsonify(success=True, message=message)

#Calculate average Chronicles Score
@authed_only
@admins_only
@bypass_csrf_protection
@c3.route('/api/v2/chronicles-Grade/<mode>', methods=['GET','POST'])
def admin_chronicles_grade(mode):
    message = ''
    if request.method == 'POST':
        if mode == 'multiplayers':
            teams = Teams.query.filter_by(hidden=False, banned=False).all()
            if teams:
                for team in teams:
                    directorateChronicles = ctk_directorate_averageScore_chronicles(mode='team', account_id=team.id)
                    # graded = directorateChronicles.json
                    for grade in directorateChronicles['data']:
                        id = list(grade.keys())
                        db.session.query(ChallengeWriteUps).filter_by( id = int(id[0]), team_id = team.id).update(dict(points = int(grade['average'])))
                        db.session.commit()
                message = 'Chronicles Already Recorded!'
    return jsonify(success=True, message=message)

#Calculate average Countermeasures Score
@authed_only
@admins_only
@bypass_csrf_protection
@c3.route('/api/v2/countermeasure-Grade/<mode>', methods=['GET','POST'])
def admin_countermeasure_grade(mode):
    message = ''
    if request.method == 'POST':
        if mode == 'multiplayers':
            teams = Teams.query.filter_by(hidden=False, banned=False).all()
            if teams:
                for team in teams:
                    directorateCounter = ctk_directorate_averageScore_countermeasures(mode='team', account_id=team.id)
                    # graded = directorateCounter.json
                    for grade in directorateCounter['data']:
                        id = list(grade.keys())
                        db.session.query(ChallengeCounterMeasure).filter_by( id = int(id[0]), team_id = team.id).update(dict(points = int(grade['average'])))
                        db.session.commit()
                message = 'Countermeasures Already Recorded!'
    return jsonify(success=True, message=message)

@c3.route('/api/v2/directorate/documents/average/<mode>/<int:account_id>', methods=['GET', 'POST'])
def ctk_directorate_average_chroniclesv2(mode, account_id):
    if request.method == 'GET':
        published = db.session.query(docs_publish).first()
        result = []
        if mode == 'team':
            if published.countermeasure_published == True:
                #countermeasures
                total_counter = ctk_countermeasure_scores(mode='team',account_id=account_id)
                #chronicles
                total_chronicles = ctk_writeups_scores(mode='team', account_id=account_id)
                #knowledge well
                total_knowledge = ctk_knowledge_scores(mode='team', account_id=account_id)
                result.append({
                    'know': total_knowledge,
                    'do': total_chronicles,
                    'learn': total_counter
                })
    return jsonify(data=result)

#reset cyberex (CTK) instance
def cyberex_reset():
    if request.method == "POST":
        require_setup = False
        logout = False
        next_url = url_for("admin.statistics")

        data = request.form

        if data.get("pages"):
            _pages = Pages.query.all()
            for p in _pages:
                for f in p.files:
                    delete_file(file_id=f.id)

            Pages.query.delete()

        if data.get("notifications"):
            Notifications.query.delete()

        if data.get("challenges"):
            _challenges = Challenges.query.all()
            for c in _challenges:
                for f in c.files:
                    delete_file(file_id=f.id)
            Challenges.query.delete()

        if data.get("accounts"):
            CTK_Config.query.filter_by(type='user').filter(CTK_Config.mode!='directorate').delete()
            Teams.query.delete()
            # require_setup = True
            logout = True

        if data.get("submissions"):
            Solves.query.delete()
            Submissions.query.delete()
            Awards.query.delete()
            Unlocks.query.delete()
            Tracking.query.delete()
            ChallengeWriteUps.query.delete()
            ChallengeCounterMeasure.query.delete()
            KnowledgeWellDocs.query.delete()
            ChroniclesDirectorate.query.delete()
            CountermeasureDirectorate.query.delete()
            KnowledgeDirectorate.query.delete()

        if require_setup:
            set_config("setup", False)
            cache.clear()
            logout_user()
            next_url = url_for("views.setup")

        db.session.commit()

        clear_pages()
        clear_standings()
        clear_config()

        if logout is True:
            cache.clear()
            logout_user()

        db.session.close()
        return redirect(next_url)

    return render_template("admin/reset.html")


#enable red teaming
@c3.route('/api/v2/redteaming', defaults={"id": None}, methods=['GET'])
@c3.route('/api/v2/redteaming/<id>', methods=['POST'])
@bypass_csrf_protection
@authed_only
@admins_only
def red_teaming_api(id):
    results = []
    success = False
    if request.method == 'POST':
        activate = request.form['conqueror-activate']
        pp(activate)
        #published|unpublish counter measure points
        if id == 'activate':
            db.session.query(red_teaming).update(dict(redteaming_activate = int(activate)))
            db.session.commit()
        success = True
        results.append({
            'success':success
        })
        return redirect("/admin/custom_setting", code=303)

    if request.method == 'GET':
        counter =  db.session.query(red_teaming).first()
        pprint(counter)
        success = True
        results.append({
            'activate': '',
            'success': success
        })
    return jsonify(results)



#directorate scoring API version 3
@authed_only
@bypass_csrf_protection
@c3.route('/api/v2/directorate/<int:id>', methods=['GET', 'POST'])
def ctk_directorate(id):
    results = []
    rater = []
    rated = False
    user = get_current_user()
    ctk_user = CTK_Config.query.filter_by(mode='directorate').all()
    #set super admin privilege
    if is_admin():
            rated = True
            rates = 0
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = DocumentationDirectorate.query.filter_by(writeups_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rates = rate.rater_know+rate.rater_do+rate.rater_learn
                            rater.append({
                                'id':rate.id,
                                'writeups_id':rate.writeups_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_know':rate.rater_know,
                                'rater_do':rate.rater_do,
                                'rater_learn':rate.rater_learn,
                                'grade':rates,
                                'date':rate.date,
                                'admin': True
                            })
    if ctk_directorate_mode():
        if request.method == 'GET':
            rates = 0
            rater_grade_exist = DocumentationDirectorate.query.filter_by(writeups_id=id, directorate_id=user.id).first()
            if rater_grade_exist != None:
                if rater_grade_exist.directorate_id == user.id:
                    rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = DocumentationDirectorate.query.filter_by(writeups_id=id, directorate_id=user.id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rates = rate.rater_know+rate.rater_do+rate.rater_learn
                            rater.append({
                                'id':rate.id,
                                'writeups_id':rate.writeups_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_know':rate.rater_know,
                                'rater_do':rate.rater_do,
                                'rater_learn':rate.rater_learn,
                                'grade':rates,
                                'date':rate.date,
                                'admin': False
                            })
    
        #Saved Directorate Grade
        if request.method == 'POST':
            rater_know = request.form['know-points']
            rater_do = request.form['do-points']
            rater_learn = request.form['counter-points']
            if int(rater_know) > 20:
                abort(404)
            if int(rater_do) > 60:
                abort(404)
            if int(rater_learn) > 20:
                abort(404)
            site_url = request.form['site_url']
            rater_grade = DocumentationDirectorate.query.filter_by(writeups_id=id, directorate_id=user.id).first()
            if rater_grade != None:
                # abort(404)
                db.session.query(DocumentationDirectorate).filter_by(writeups_id=id, directorate_id=user.id).update(dict(rater_know = int(rater_know), rater_do = int(rater_do), rater_learn = int(rater_learn)))
                db.session.commit()
                return redirect(site_url+"#chronicles-row")
            else:
                db.session.add(DocumentationDirectorate(writeups_id = id, directorate_id = user.id, rater_know = int(rater_know), rater_do = int(rater_do), rater_learn = int(rater_learn)))
                db.session.commit()
                return redirect(site_url+"#chronicles-row")
                
    #teams ratings breakdown
    if ctk_teams_mode():
        if request.method == 'GET':
            rater_grade_exist = DocumentationDirectorate.query.filter_by(writeups_id=id, directorate_id=user.id).first()
            if rater_grade_exist != None:
                if rater_grade_exist.directorate_id == user.id:
                    rated = True
            #Get all rater score breakdown
            for directorate in ctk_user:
               rater_grade = DocumentationDirectorate.query.filter_by(writeups_id=id).all()
               if len(rater_grade) > 0:
                    for rate in rater_grade:
                        if directorate.id == rate.directorate_id:
                            rater.append({
                                'id':rate.id,
                                'writeups_id':rate.writeups_id,
                                'directorate_id':rate.directorate_id,
                                'directorate_name': directorate.name,
                                'rater_know':rate.rater_know,
                                'rater_do':rate.rater_do,
                                'rater_learn':rate.rater_learn,
                                'date':rate.date
                            })
    return jsonify(results=results, rater=rater, rated=rated)


#Calculate  documentation points
@authed_only
@admins_only
@bypass_csrf_protection
@c3.route('/api/v2/documentation/<mode>', methods=['GET','POST'])
def admin_documentations_grade(mode):
    message = ''
    if request.method == 'POST':
        if mode == 'multiplayers':
            teams = Teams.query.filter_by(hidden=False, banned=False).all()
            if teams:
                for team in teams:
                    #know
                    directorateKnowledge = ctk_directorate_averageScore_know(mode='team', account_id=team.id)
                    # graded = directorateKnowledge.json
                    for grade in directorateKnowledge['data']:
                        id = list(grade.keys())
                        db.session.query(ChallengeWriteUps).filter_by( id = int(id[0]), team_id = team.id).update(dict(know_score = int(grade['average'])))
                        db.session.commit()
                    #DO
                    directorateChronicles = ctk_directorate_averageScore_documentations_do(mode='team', account_id=team.id)
                    # graded = directorateChronicles.json
                    for grade in directorateChronicles['data']:
                        id = list(grade.keys())
                        db.session.query(ChallengeWriteUps).filter_by( id = int(id[0]), team_id = team.id).update(dict(do_score = int(grade['average'])))
                        db.session.commit()
                    #learn ctk_directorate_averageScore_learn
                    directoratelearn = ctk_directorate_averageScore_learn(mode='team', account_id=team.id)
                    # graded = directorateKnowledge.json
                    for grade in directoratelearn['data']:
                        id = list(grade.keys())
                        db.session.query(ChallengeWriteUps).filter_by( id = int(id[0]), team_id = team.id).update(dict(learn_score = int(grade['average'])))
                        db.session.commit()
                message = 'Documentations for Multiplayers Already Recorded!'
        #individuals documents
        if mode == 'individual':
            users = Users.query.filter_by(hidden=False, banned=False).all()
            if users:
                for user in users:
                    #know
                    directorateKnowledge = ctk_directorate_averageScore_know(mode='user', account_id=user.id)
                    for grade in directorateKnowledge['data']:
                        id = list(grade.keys())
                        db.session.query(ChallengeWriteUps).filter_by( id = int(id[0]), user_id = user.id).update(dict(know_score = int(grade['average'])))
                        db.session.commit()
                    #do
                    directorateChronicles = ctk_directorate_averageScore_documentations_do(mode='user', account_id=user.id)
                    # graded = directorateChronicles.json
                    for grade in directorateChronicles['data']:
                        id = list(grade.keys())
                        db.session.query(ChallengeWriteUps).filter_by( id = int(id[0]), user_id = user.id).update(dict(do_score = int(grade['average'])))
                        db.session.commit()
                    #learn
                    directoratelearn = ctk_directorate_averageScore_learn(mode='user', account_id=user.id)
                    for grade in directoratelearn['data']:
                        id = list(grade.keys())
                        db.session.query(ChallengeWriteUps).filter_by( id = int(id[0]), user_id = user.id).update(dict(learn_score = int(grade['average'])))
                        db.session.commit()
                message = 'Documentations for Individuals Already Recorded!'
        
    return jsonify(success=True, message=message)