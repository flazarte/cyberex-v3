import os
from CTFd.plugins import override_template, register_plugin_assets_directory
from CTFd.plugins.challenges import CHALLENGE_CLASSES
#from flask_socketio import SocketIO
from CTFd.plugins.custom.routing import (
    c3,
    view_scoreboard_list, 
    get_available_challenges, 
    view_challenge_category, 
    view_challenge_list, 
    uploader, 
    write_ups_api, 
    custom_submissions_listing, 
    new_scoreboard, 
    c3_setting, 
    category_chals_api,
    c3_category_api, 
    c3_category_update_api,
    get_solves_api,
    c3_category_requirements_api,
    new_static_html,
    category_chals_id_api,
    chronicles_api,
    counter_measure_api,
    progress_api,
    uploaded_file,
    new_users_detail,
    new_teams_detail,
    get_scoreboard_api,
    get_leatherboard_api,
    user_public,
    team_public,
    article_add,
    article_update,
    counter_update_api,
    challenges_api_v2,
    docs_publish_api,
    ctk_register,
    ctk_login,
    ctk_private,
    ctk_join,
    ctk_new,
    ctk_listing,
    ctk_settings,
    users_listing,
    maj_units_api,
    sub_units_api,
    get_mysolves_api,
    article_update_attempt,
    challenge_hint,
    get_scoreboard_top,
    get_team_standings,
    multiplayers_chronicles_api,
    multiplayers_countermeasures_api,
    ctk_admin_register,
    ctk_directorate_chronicles,
    ctk_directorate_countermeasure,
    dashboard_drectorate,
    ctk_statistics,
    ctk_directorate_average_chronicles,
    ctk_directorate_OverallChroniclesaverage,
    knowledge_measure_api,
    ctk_directorate_knowledge,
    ctk_directorate_average_knowledge,
    ctk_directorate_OverallKnowledgeaverage,
    ctk_who_login,
    admin_knowledge_api,
    admin_knowledge_grade,
    admin_chronicles_grade,
    admin_countermeasure_grade,
    ctk_directorate_average_chroniclesv2,
    cyberex_reset,
    red_teaming_api
) 
from CTFd.plugins.custom.models import CategoryGameClass
from werkzeug.routing import Rule


def load(app):
    app.db.create_all()  
    #set-up csrf protection
    CHALLENGE_CLASSES["c3_category"] = CategoryGameClass
    #override scoreboard
    dir_path = os.path.dirname(os.path.realpath(__file__))
    #scoreboard Override
    new_scorebord = os.path.join(dir_path, 'templates/new-scoreboard.html')
    override_template('scoreboard.html', open(new_scorebord).read())
    #Challenges Override
    new_challenges = os.path.join(dir_path, 'templates/new-challenges.html')
    override_template('challenges.html', open(new_challenges).read())
    new_base = os.path.join(dir_path, 'templates/base.html')
    override_template('base.html', open(new_base).read())
    new_challenge = os.path.join(dir_path, 'templates/challenge.html')
    override_template('challenge.html', open(new_challenge).read())
    new_teams = os.path.join(dir_path, 'components/teams.html')
    override_template('teams/teams.html', open(new_teams).read())
    new_users = os.path.join(dir_path, 'components/users.html')
    override_template('users/users.html', open(new_users).read())
    new_pub_team = os.path.join(dir_path, 'components/team_public.html')
    override_template('teams/public.html', open(new_pub_team).read())
    new_pri_team = os.path.join(dir_path, 'components/team_private.html')
    override_template('teams/private.html', open(new_pri_team).read())
    new_pub_user = os.path.join(dir_path, 'components/user_public.html')
    override_template('users/public.html', open(new_pub_user).read())
    new_pri_user = os.path.join(dir_path, 'components/user_private.html')
    override_template('users/private.html', open(new_pri_user).read())
    reset_pass = os.path.join(dir_path, 'components/reset_passw.html')
    override_template('reset_password.html', open(reset_pass).read())
    new_teams_join = os.path.join(dir_path, 'components/join_team.html')
    override_template('teams/join_team.html', open(new_teams_join).read())
    new_teams_create = os.path.join(dir_path, 'components/new_team.html')
    override_template('teams/new_team.html', open(new_teams_create).read())
    #front-end navbar|login|register Override
    new_navbar = os.path.join(dir_path, 'components/navbar.html')
    override_template('components/navbar.html', open(new_navbar).read())
    new_login = os.path.join(dir_path, 'components/login.html')
    override_template('login.html', open(new_login).read())
    new_register = os.path.join(dir_path, 'templates/notifications.html')
    override_template('notifications.html', open(new_register).read())
    new_settings = os.path.join(dir_path, 'templates/settings.html')
    override_template('settings.html', open(new_settings).read())
    new_notif = os.path.join(dir_path, 'components/register.html')
    override_template('register.html', open(new_notif).read())
    #override admin templates
    admin_challenges_list = os.path.join(dir_path, 'admin/challenges/challenges.html')
    override_template('admin/challenges/challenges.html', open(admin_challenges_list).read())
    admin_scoreboard_standings = os.path.join(dir_path, 'admin/scoreboard/scoreboard.html')
    override_template('admin/scoreboard.html', open(admin_scoreboard_standings).read())
    admin_new_challenges = os.path.join(dir_path, 'admin/challenges/new.html')
    override_template('admin/challenges/new.html', open(admin_new_challenges).read())
    standings = os.path.join(dir_path, 'admin/scoreboard/standings.html')
    override_template('admin/scoreboard/standings.html', open(standings).read())
    user_standings = os.path.join(dir_path, 'admin/scoreboard/users.html')
    override_template('admin/scoreboard/users.html', open(user_standings).read())
    admin_new_challenge = os.path.join(dir_path, 'admin/challenges/challenge.html')
    override_template('admin/challenges/challenge.html', open(admin_new_challenge).read())
    admin_user = os.path.join(dir_path, 'admin/user/user.html')
    override_template('admin/users/user.html', open(admin_user).read())
    # admin_team = os.path.join(dir_path, 'admin/teams/team.html') //disabl for update bugs
    # override_template('admin/teams/team.html', open(admin_team).read())
    #reset 
    admin_reset = os.path.join(dir_path, 'admin/reset.html')
    override_template('admin/reset.html', open(admin_reset).read())
    #Submission 
    admin_submissions_list = os.path.join(dir_path, 'admin/submissions/submissions.html')
    override_template('admin/submissions.html', open(admin_submissions_list).read())
    #create users
    admin_user_create = os.path.join(dir_path, 'admin/user/create.html')
    override_template('admin/modals/users/create.html', open(admin_user_create).read())
    # #base_html
    # index_html = os.path.join(dir_path, 'templates/page.html')
    # override_template('page.html', open(index_html).read())
    #admin_base
    admin_base = os.path.join(dir_path, 'admin/base.html')
    override_template('admin/base.html', open(admin_base).read())

    app.register_blueprint(c3)
    #add routes methods
    app.url_map.add(Rule('/challenges', endpoint='challenges.listing', methods=['GET', 'POST']))
    app.url_map.add(Rule('/uploader', endpoint='c3.uploader', methods=['GET', 'POST', 'DELETE']))
    #add url url_for rule
    app.add_url_rule('/challenge-category', 'c3.view_challenge_category', view_challenge_category)
    app.add_url_rule('/uploader', 'c3.uploader', uploader)
    app.add_url_rule('/api/v2/challenge-category/<int:c3_id>', 'c3.c3_update_api',c3_category_update_api)
    app.add_url_rule('/api/v2/category-challenge/<int:cat_id>', 'c3.category_chals_id_api',category_chals_id_api)
    app.add_url_rule('/api/v2/chronicles/<int:id>', 'c3.chronicles_api', chronicles_api)
    app.add_url_rule('/admin/directorate', 'c3.dashboard_drectorate_url', dashboard_drectorate)
    #view functions front-end
    app.view_functions['challenges.listing'] = get_available_challenges
    app.view_functions['c3.view_challenge_category'] = view_challenge_category
    app.view_functions['c3.uploader'] = uploader
    app.view_functions['c3.uploaded_file'] = uploaded_file
    app.view_functions['users.public'] = user_public
    app.view_functions['teams.public'] = team_public
    app.view_functions['auth.register'] = ctk_register
    app.view_functions['auth.login'] = ctk_login
    app.view_functions['teams.private'] = ctk_private
    app.view_functions['teams.join'] = ctk_join
    app.view_functions['teams.new'] = ctk_new
    app.view_functions['teams.listing'] = ctk_listing
    app.view_functions['views.settings'] = ctk_settings
    app.view_functions['users.listing'] = users_listing
    app.view_functions['api.v1.ChallengeList.get'] = users_listing
    app.view_functions['c3.dashboard_drectorate'] = dashboard_drectorate
    #view functions | admin
    app.view_functions['admin.scoreboard_listing'] = view_scoreboard_list
    app.view_functions['admin.challenges_listing'] = view_challenge_list
    app.view_functions['admin.users_detail'] = new_users_detail
    app.view_functions['admin.reset'] = cyberex_reset

    # app.view_functions['admin.teams_detail'] =  new_teams_detail   //disable for now bug exist in saving an update
    app.view_functions['admin.users_new'] = ctk_admin_register
    #custom api routes
    app.view_functions['c3.writeups_api'] = write_ups_api
    app.view_functions['c3.category_chals_api'] = category_chals_api
    app.view_functions['c3.c3_category_api'] = c3_category_api
    app.view_functions['c3.c3_update_api'] = c3_category_update_api
    app.view_functions['c3.c3_category_requirements_api'] = c3_category_requirements_api
    app.view_functions['c3.c3_solves_api'] = get_solves_api
    app.view_functions['c3.category_chals_id_api'] = category_chals_id_api
    app.view_functions['c3.chronicles_api'] = chronicles_api
    app.view_functions['c3.counter_update_api'] = counter_update_api
    app.view_functions['c3.counter_measure_api'] = counter_measure_api
    app.view_functions['c3.progress_api'] = progress_api
    app.view_functions['c3.get_scoreboard_api'] = get_scoreboard_api
    app.view_functions['c3.get_leatherboard_api'] = get_leatherboard_api
    app.view_functions['c3.challenges_api_v2'] = challenges_api_v2
    app.view_functions['c3.docs_publish_api'] = docs_publish_api
    app.view_functions['c3.maj_units_api'] = maj_units_api
    app.view_functions['c3.sub_units_api'] = sub_units_api
    app.view_functions['c3.get_mysolves_api'] = get_mysolves_api
    app.view_functions['c3.article_update_attempt'] = article_update_attempt
    app.view_functions['c3.challenge_hint'] = challenge_hint
    app.view_functions['c3.get_scoreboard_top'] = get_scoreboard_top
    app.view_functions['c3.get_team_standings'] = get_team_standings
    app.view_functions['c3.multiplayers_chronicles_api'] =  multiplayers_chronicles_api
    app.view_functions['c3.multiplayers_countermeasures_api'] =  multiplayers_countermeasures_api
    app.view_functions['c3.ctk_directorate_chronicles'] = ctk_directorate_chronicles
    app.view_functions['c3.ctk_directorate_countermeasure'] = ctk_directorate_countermeasure
    app.view_functions['c3.ctk_statistics'] = ctk_statistics
    app.view_functions['c3.ctk_directorate_average_chronicles'] = ctk_directorate_average_chronicles
    app.view_functions['c3.ctk_directorate_OverallChroniclesaverage'] = ctk_directorate_OverallChroniclesaverage
    app.view_functions['c3.knowledge_measure_api'] = knowledge_measure_api
    app.view_functions['c3.ctk_directorate_knowledge'] = ctk_directorate_knowledge
    app.view_functions['c3.ctk_directorate_average_knowledge'] =  ctk_directorate_average_knowledge
    app.view_functions['c3.ctk_directorate_OverallKnowledgeaverage'] = ctk_directorate_OverallKnowledgeaverage
    app.view_functions['c3.ctk_who_login'] = ctk_who_login
    app.view_functions['c3.admin_knowledge_api'] = admin_knowledge_api
    app.view_functions['c3.admin_knowledge_grade'] = admin_knowledge_grade
    app.view_functions['c3.admin_chronicles_grade'] = admin_chronicles_grade
    app.view_functions['c3.admin_countermeasure_grade'] = admin_countermeasure_grade
    app.view_functions['c3.ctk_directorate_average_chroniclesv2'] = ctk_directorate_average_chroniclesv2
    app.view_functions['c3.red_teaming_api'] = red_teaming_api
    #custom submission
    app.view_functions['admin.submissions_listing'] = custom_submissions_listing
    #scoreboard
    app.view_functions['scoreboard.listing'] = new_scoreboard
    #pages
    app.view_functions['views.static_html'] = new_static_html
    #admin c3 setting
    app.view_functions['c3.settings'] = c3_setting
    #admin blog/aticle functions
    app.view_functions['c3.add_article'] = article_add
    app.view_functions['c3.edit_article'] = article_update
    #telegram integration
    # SocketIO(app,cors_allowed_origins="*")
    register_plugin_assets_directory(app, base_path="/plugins/custom/admin/assets/img/")
    #register new assets
    register_plugin_assets_directory(app, base_path="/plugins/custom/assets/")
    register_plugin_assets_directory(app, base_path="/plugins/custom/assets/dropzone/dist/")
    register_plugin_assets_directory(app, base_path="/plugins/custom/assets/js/")
    register_plugin_assets_directory(app, base_path="/plugins/custom/admin/challenges/")
    register_plugin_assets_directory(app, base_path="/plugins/custom/writeups/")
    register_plugin_assets_directory(app, base_path="/plugins/custom/ctk-editor/")
    register_plugin_assets_directory(app, base_path="/plugins/custom/countermeasure/")
    register_plugin_assets_directory(app, base_path="/plugins/custom/knowledge/")
    register_plugin_assets_directory(app, base_path="/plugins/custom/playbook/")