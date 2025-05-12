from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import logic
import os
from logic import socketio
from functools import wraps # Import wraps for decorators

# --- Flask App Setup ---
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24)) 

socketio.init_app(app)

# --- Decorators for Route Protection ---

def login_required(f):
    """Decorator to ensure a user or organization is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'entity_type' not in session:
            flash("Por favor inicia sesión para acceder a esta página.", "warning")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def user_login_required(f):
    """Decorator to ensure a standard user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('entity_type') != 'user':
            flash("Debes iniciar sesión como usuario para realizar esta acción.", "error")
            return redirect(url_for('login')) 
        return f(*args, **kwargs)
    return decorated_function

def org_login_required(f):
    """Decorator to ensure an organization is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('entity_type') != 'organization':
            flash("Debes iniciar sesión como organización para realizar esta acción.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# --- Template Context Processor ---
# This makes the 'session' object available in all templates automatically.
@app.context_processor
def inject_session():
    return dict(session=session)


# --- Basic Routes ---

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


# --- Authentication Routes ---

@app.route('/register/user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        # Extract data from form
        name = request.form.get('name')
        nickname = request.form.get('nickname')
        email = request.form.get('email')
        student_code = request.form.get('student_code')
        password = request.form.get('password')
        interests = request.form.get('interests')
        career = request.form.get('career')
        photo = request.form.get('photo')

        # Call logic function (unchanged)
        result = logic.register_user(name, nickname, email, student_code, password, interests, career, photo)

        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('login'))
        else:
            return redirect(url_for('register_user'))

    # For GET request, just show the registration form
    return render_template('register_user.html')

@app.route('/register/org', methods=['GET', 'POST'])
@user_login_required # Use decorator to ensure a user is logged in
def register_org():
    creator_student_code = session.get('student_code')
    creator_email = session.get('email')
    if not creator_student_code:
        flash("No se pudo identificar al usuario conectado.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        description = request.form.get('description')
        password = request.form.get('password')
        interests = request.form.get('interests')
        photo = request.form.get('photo', "photo-org.png") # Default photo

        result = logic.register_organization(creator_email, creator_student_code, name, email, description, password, interests, photo)

        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('index'))
        else:
            return redirect(url_for('register_org'))
    return render_template('register_org.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'entity_type' in session:
        if session['entity_type'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        code = request.form.get('identifier') 
        password = request.form.get('password')

        result = logic.login(code, password)

        if result['status'] == 'success':
            session.clear()
            session['entity_id'] = result['entity_id']
            session['entity_type'] = result['entity_type']
            session['name'] = result['name']
            session['nickname'] = result.get('nickname', '')
            session['student_code'] = result.get('student_code', '')
            session['email'] = result['email']
            session['career'] = result.get('career', '')
            session['interests'] = result.get('interests', '')
            session['description'] = result.get('description', '')
            session['points'] = result.get('points', 0)
            session['photo'] = result.get('photo', '')

            if result['entity_type'] == 'admin':
                flash(f"¡Inicio de sesión de administrador exitoso para {session['name']}!", 'success')
                return redirect(url_for('admin_dashboard'))
            
            if result['entity_type'] == 'user':
                flash(f"¡Inicio de sesión exitoso!", 'success')
                return redirect(url_for('index'))
        else:
            flash(result['message'], result['status'])
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/login/org', methods=['GET', 'POST'])
def login_org():
    if 'entity_type' in session:
        if session['entity_type'] == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        creator_code = request.form.get('creator_code')
        password = request.form.get('password')
        
        result = logic.login_orgs(creator_code, password)
        
        if result['status'] == 'success':
            session.clear()
            session['entity_id'] = result['entity_id']
            session['entity_type'] = 'organization'
            session['name'] = result['name']
            session['email'] = result['email']
            session['description'] = result.get('description', '')
            session['interests'] = result.get('interests', '')
            session['points'] = result.get('points', 0)
            session['creator_student_code'] = result.get('creator_student_code', '')
            session['photo'] = result.get('photo', '')

            flash(f"¡Inicio de sesión de organización exitoso para {session['name']}!", 'success')
            return redirect(url_for('index'))
        else:
            flash(result['message'], result['status'])
            return redirect(url_for('login_org'))
    
    return render_template('login_org.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Has cerrado sesión exitosamente.", 'success')
    return redirect(url_for('index'))

# --- Profile Routes ---
@app.route('/profile')
@login_required
def profile():
    entity_id = None
    entity_type = session.get('entity_type')
    
    if entity_type == 'user':
        entity_id = session.get('entity_id')
        
        user_data = {
            'name': session.get('name'),
            'email': session.get('email'),
            'student_code': session.get('student_code'),
            'career': session.get('career'),
            'interests': session.get('interests'),
            'points': session.get('points', 0),
            'photo': session.get('photo', '')
        }
        
        fresh_user_data = logic.get_entity_by_id(entity_id, entity_type)
        if fresh_user_data:
            if not user_data['career'] or user_data['career'] == 'None':
                user_data['career'] = fresh_user_data.get('career', '')
            if not user_data['interests'] or user_data['interests'] == 'None':
                user_data['interests'] = fresh_user_data.get('interests', '')
            session['career'] = fresh_user_data.get('career', '')
            session['interests'] = fresh_user_data.get('interests', '')
            session.modified = True
        
        points = session.get('points', 0)
        user_orgs = []
        
        badges = []
        result = logic.get_entity_achievements(entity_id, entity_type)
        if result['status'] == 'success' and 'data' in result:
            badges = result.get('data', [])

        orgs_result = logic.get_user_orgs_logic(entity_id)
        if orgs_result['status'] == 'success':
            user_orgs = orgs_result['data']
        
        return render_template('profile.html',
                            entity_type=entity_type, 
                            user_data=user_data,
                            points=points, 
                            badges=badges,
                            user_orgs=user_orgs)
        

    elif entity_type == 'organization':
        entity_id = session.get('entity_id')
        
        org_data = {
            'name': session.get('name'),
            'email': session.get('email'),
            'description': session.get('description'),
            'interests': session.get('interests'),
            'points': session.get('points', 0),
            'photo': session.get('photo', '')
        }
        
        members = []
        members_result = logic.get_org_members_logic(entity_id)
        if members_result['status'] == 'success':
            members = members_result['data']
        
        return render_template('profile.html',
                            entity_type=entity_type, 
                            org_data=org_data,
                            members=members)
    
    else:
        flash("Tipo de entidad desconocido.", "error")
        return redirect(url_for('index'))

@app.route('/profile/update', methods=['GET', 'POST'])
@login_required
def update_profile():
    entity_id = session.get('entity_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("No se pudo identificar tu sesión.", "error")
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        new_data = {}
        
        if entity_type == 'user':
            if request.form.get('name'):
                new_data['name'] = request.form.get('name')
            if request.form.get('nickname'):
                new_data['nickname'] = request.form.get('nickname')
            if request.form.get('email'):
                new_data['email'] = request.form.get('email')
            if request.form.get('student_code'):
                new_data['student_code'] = request.form.get('student_code')
            if request.form.get('career'):
                new_data['career'] = request.form.get('career')
            if request.form.get('interests'):
                new_data['interests'] = request.form.get('interests')
        
        elif entity_type == 'organization':
            if request.form.get('name'):
                new_data['name'] = request.form.get('name')
            if request.form.get('email'):
                new_data['email'] = request.form.get('email')
            if request.form.get('description'):
                new_data['description'] = request.form.get('description')
            if request.form.get('interests'):
                new_data['interests'] = request.form.get('interests')
        
        result = logic.update_my_profile_logic(entity_id, entity_type, new_data)
        flash(result['message'], result['status'])
        
        if result['status'] == 'success':
            if 'name' in new_data:
                session['name'] = new_data['name']
            if entity_type == 'user':
                if 'nickname' in new_data:
                    session['nickname'] = new_data['nickname']
                if 'career' in new_data:
                    session['career'] = new_data['career']
                if 'interests' in new_data:
                    session['interests'] = new_data['interests']
            elif entity_type == 'organization':
                if 'description' in new_data:
                    session['description'] = new_data['description']
                if 'interests' in new_data:
                    session['interests'] = new_data['interests']
            session.modified = True
        
        return redirect(url_for('profile'))
    
    if entity_type == 'user':
        data = {
            'name': session.get('name'),
            'nickname': session.get('nickname'),
            'email': session.get('email'),
            'student_code': session.get('student_code'),
            'career': session.get('career'),
            'interests': session.get('interests'),
            'points': session.get('points', 0)
        }
        
        result = logic.get_entity_by_id(entity_id, entity_type)
        if result['status'] == 'success' and 'data' in result:
            db_data = result['data']
            if 'email' in db_data and not data['email']:
                data['email'] = db_data['email']
            if 'career' in db_data and not data['career']:
                data['career'] = db_data['career']
            if 'interests' in db_data and not data['interests']:
                data['interests'] = db_data['interests']
        
        return render_template('update_profile.html', entity_type=entity_type, data=data)
    else:
        data = {
            'name': session.get('name'),
            'email': session.get('email'),
            'description': session.get('description'),
            'interests': session.get('interests'),
            'points': session.get('points', 0)
        }
        
        return render_template('update_profile.html', entity_type=entity_type, data=data)

@app.route('/profile/delete', methods=['GET', 'POST'])
@login_required
def delete_account():
    entity_id = session.get('entity_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("No se pudo identificar tu sesión.", "error")
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        if not password:
            flash("Se requiere contraseña para eliminar tu cuenta.", "error")
            return redirect(url_for('delete_account'))
        
        result = logic.delete_my_account_logic(entity_id, entity_type, password)
        
        if result['status'] == 'success':
            session.clear()
            flash("Tu cuenta ha sido eliminada exitosamente.", "success")
            return redirect(url_for('index'))
        else:
            flash(result['message'], result['status'])
            return redirect(url_for('delete_account'))
    
    return render_template('delete_account.html')

@app.route('/exchange/requests')
@user_login_required
def view_my_requests():
    user_id = session.get('entity_id')
    if not user_id:
        flash("No se pudo identificar la sesión de usuario.", "error")
        return redirect(url_for('login'))
    
    request_type = request.args.get('type', 'received')
    if request_type not in ['received', 'sent']:
        request_type = 'received'
    
    result = logic.view_my_exchange_requests_logic(user_id, request_type)
    
    if result['status'] == 'success':
        requests = result.get('data', [])
        return render_template('exchange_requests.html', 
                              requests=requests, 
                              request_type=request_type)
    else:
        flash(result['message'], result['status'])
        return render_template('exchange_requests.html', 
                              requests=[], 
                              request_type=request_type)

@app.route('/search/users')
@login_required
def search_users():
    q = request.args.get('q', '')
    career = request.args.get('career', '')
    interests = request.args.get('interests', '')
    result = logic.search_users_logic(query=q, career=career, interests=interests)
    users = result.get('data', []) if result.get('status')=='success' else []
    return render_template(
        'search_users.html',
        users=users,
        query=q,
        career=career,
        interests=interests
    )


# --- Organization Routes ---
@app.route('/search_orgs')
def search_orgs():
    query = request.args.get('q', '')
    interests = request.args.get('interests', '')
    sort_by = request.args.get('sort_by', 'name')
    
    result = logic.search_orgs_logic(query=query, interests=interests, sort_by=sort_by)
    
    if result['status'] == 'success':
        orgs = result.get('data', [])
        return render_template('search_orgs.html', 
                              orgs=orgs, 
                              query=query, 
                              interests=interests, 
                              sort_by=sort_by)
    else:
        flash(result['message'], result['status'])
        return render_template('search_orgs.html', 
                              orgs=[], 
                              query=query, 
                              interests=interests, 
                              sort_by=sort_by)


@app.route('/organization/<int:org_id>/members')
def view_org_members(org_id):
    result = logic.get_org_members_logic(org_id)
    
    org_details = None
    orgs_result = logic.search_orgs_logic(query="", sort_by="name")
    if orgs_result['status'] == 'success':
        for org in orgs_result['data']:
            if org['org_id'] == org_id:
                org_details = org
                break
    
    if not org_details:
        flash("Organización no encontrada.", "error")
        return redirect(url_for('search_orgs'))
    
    if result['status'] == 'success':
        members = result.get('data', [])
        is_member = False
        if session.get('entity_type') == 'user' and session.get('entity_id'):
            user_id = session.get('entity_id')
            for member in members:
                if member.get('entity_id') == user_id:
                    is_member = True
                    break
        
        return render_template('org_members.html', 
                               org=org_details,
                               members=members,
                               is_member=is_member)
    else:
        flash(result['message'], result['status'])
        return redirect(url_for('search_orgs'))

@app.route('/organization/join/<int:org_id>', methods=['POST'])
@user_login_required
def join_org(org_id):
    user_id = session.get('entity_id')
    if not user_id:
        flash("No se pudo identificar la sesión de usuario.", "error")
        return redirect(url_for('login'))
    
    result = logic.join_org_logic(user_id, org_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('search_orgs'))

@app.route('/organization/leave/<int:org_id>', methods=['POST'])
@user_login_required
def leave_org(org_id):
    user_id = session.get('entity_id')
    if not user_id:
        flash("No se pudo identificar la sesión de usuario.", "error")
        return redirect(url_for('login'))
    
    result = logic.leave_org_logic(user_id, org_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('search_orgs'))

@app.route('/organization/<int:org_id>')
def view_org_profile(org_id):
    result = logic.get_entity_by_id(org_id, 'org')
    
    if result['status'] != 'success':
        flash(result['message'], 'error')
        return redirect(url_for('search_orgs'))
    
    org_data = result['data']
    
    is_member = False
    if session.get('entity_type') == 'user' and session.get('entity_id'):
        user_id = session.get('entity_id')
        orgs_result = logic.get_user_orgs_logic(user_id)
        if orgs_result['status'] == 'success':
            for org in orgs_result['data']:
                if org['org_id'] == org_id:
                    is_member = True
                    break
    
    return render_template('org_profile.html', 
                           org_data=org_data,
                           is_member=is_member)


# --- Event Routes ---
@app.route('/event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    organizer_id = session.get('entity_id')
    organizer_type = session.get('entity_type')

    if not organizer_id or not organizer_type:
         flash("No se pudieron identificar los detalles del organizador desde la sesión.", "error")
         return redirect(url_for('index'))

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_datetime = request.form.get('event_datetime')
        location = request.form.get('location')
        event_type = request.form.get('event_type')

        result = logic.create_event_logic(
            organizer_id, organizer_type, title, description, 
            event_datetime, location, event_type
        )

        flash(result['message'], result['status'])
        return redirect(url_for('index'))

    return render_template('create_event.html')

@app.route('/event/delete/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    entity_id = session.get('entity_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("No se pudo identificar tu sesión.", "error")
        return redirect(url_for('view_events'))
    
    result = logic.delete_event_logic(entity_id, entity_type, event_id)
    flash(result['message'], result['status'])

    return redirect(url_for('view_events'))

@app.route('/events')
def view_events():
    query = request.args.get('q', '')
    result = logic.search_events_logic(query)
    
    if result['status'] == 'success':
        events = result.get('data', [])
        return render_template('view_events.html', events=events)
    else:
        flash(result['message'], result['status'])
        return render_template('view_events.html', events=[])

@app.route('/event/participants/<int:event_id>')
@login_required
def view_event_participants(event_id):
    entity_id = session.get('entity_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("No se pudo identificar tu sesión.", "error")
        return redirect(url_for('view_events'))
    
    result = logic.get_event_participants_logic(event_id)
    
    if result['status'] != 'success':
        flash(result['message'], result['status'])
        return redirect(url_for('view_events'))
    
    participants = result['data']
    
    is_organizer = False
    event_details = None
    
    events_result = logic.search_events_logic(query="")
    if events_result['status'] == 'success':
        for event in events_result['data']:
            if event['event_id'] == event_id:
                event_details = event
                
                if ((event['organizer_type'] == entity_type or 
                    (event['organizer_type'] == 'org' and entity_type == 'organization')) and
                    event['organizer_id'] == entity_id):
                    is_organizer = True
                break
    
    if not event_details:
        flash("Evento no encontrado.", "error")
        return redirect(url_for('view_events'))
    
    return render_template('event_participants.html', 
                           event_id=event_id,
                           event=event_details,
                           participants=participants,
                           is_organizer=is_organizer)

@app.route('/event/register/<int:event_id>', methods=['POST'])
@user_login_required
def register_for_event(event_id):
    entity_id = session.get('entity_id')
    entity_type = session.get("entity_type")
    if not entity_id:
        flash("No se pudo identificar la sesión de usuario.", "error")
        return redirect(url_for('login'))

    result = logic.register_for_event_logic(entity_id, event_id)
    flash(result['message'], result['status'])

    if result['status'] == 'success':
         user_data = logic.get_entity_by_id(entity_id, entity_type)
         if user_data['status'] == 'success':
             session['points'] = user_data['data'].get('points', session.get('points'))
             session.modified = True

    return redirect(url_for('view_events'))

@app.route('/event/leave/<int:event_id>', methods=['POST'])
@user_login_required
def leave_event(event_id):
    user_id = session.get('entity_id')
    if not user_id:
        flash("No se pudo identificar la sesión de usuario.", "error")
        return redirect(url_for('view_events'))
    
    result = logic.leave_event_logic(user_id, event_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('view_events'))

@app.route('/event/mark_attendance', methods=['POST'])
@login_required
def mark_attendance():
    marker_id = session.get('entity_id')
    marker_type = session.get('entity_type')
    
    if not marker_id or not marker_type:
        flash("No se pudo identificar tu sesión.", "error")
        return redirect(url_for('view_events'))
    
    event_id = request.form.get('event_id')
    participant_id = request.form.get('participant_id')
    participant_type = request.form.get('participant_type')
    
    if not event_id or not participant_id or not participant_type:
        flash("Falta información necesaria para marcar asistencia.", "error")
        return redirect(url_for('view_event_participants', event_id=event_id))
    
    try:
        event_id = int(event_id)
        participant_id = int(participant_id)
    except ValueError:
        flash("ID de evento o participante inválido.", "error")
        return redirect(url_for('view_events'))
    
    result = logic.mark_event_attendance_logic(
        event_id, marker_id, participant_id, participant_type
    )
    
    flash(result['message'], result['status'])
    return redirect(url_for('view_event_participants', event_id=event_id))


# --- Item Routes ---
@user_login_required
@app.route('/item/add', methods=['GET', 'POST'])
def add_item():
    owner_id = session.get('entity_id')
    owner_type = session.get('entity_type') 

    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        item_type = request.form.get('item_type')
        item_terms = request.form.get('item_terms')

        if not all([name, description, item_type, item_terms]):
            flash("Todos los campos son obligatorios.", "error")
            return redirect(url_for('add_item'))
            
        result = logic.add_item_logic(
            owner_id, name, description, item_type, item_terms
        )

        flash(result['message'], result['status'])
        
        if result['status'] == 'success':
             user_data = logic.get_entity_by_id(owner_id, owner_type)
             if user_data['status'] == 'success':
                 session['points'] = user_data['data'].get('points', session.get('points')) 
                 session.modified = True 

        return redirect(url_for('view_items'))

    return render_template('add_item.html')

@app.route('/item/delete/<int:item_id>', methods=['POST'])
@user_login_required
def delete_my_item(item_id):
    user_id = session.get('entity_id')
    if not user_id:
        flash("No se pudo identificar la sesión de usuario.", "error")
        return redirect(url_for('login'))

    result = logic.delete_my_item_logic(user_id, item_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('view_items'))

@app.route('/items')
def view_items():
    item_terms = request.args.get('terms')
    
    result = logic.view_items_logic(item_terms=item_terms)
    
    if result['status'] == 'success':
        items = result.get('data', [])
        return render_template('view_items.html', items=items, current_filter=item_terms)
    else:
        flash(result['message'], result['status'])
        return render_template('view_items.html', items=[], current_filter=item_terms)

@app.route('/item/request/<int:item_id>', methods=['POST'])
@user_login_required
def request_item(item_id):
    requester_id = session.get('entity_id')
    if not requester_id:
        flash("Debe iniciar sesión para solicitar un ítem.", "error")
        return redirect(url_for('login'))

    result = logic.request_item_logic(requester_id, item_id, "")
    flash(result['message'], result['status'])

    if result['status'] == 'success':
        item = logic.get_item_details_logic(item_id)
        owner_id = item.get('owner_id')
        return redirect(url_for('private_chat', user_id=owner_id))

    return redirect(url_for('view_items'))

@app.route('/exchange/accept/<int:exchange_id>', methods=['POST'])
@user_login_required
def accept_exchange(exchange_id):
    user_id = session.get('entity_id')
    if not user_id:
        flash("No se pudo identificar la sesión de usuario.", "error")
        return redirect(url_for('login'))

    result = logic.accept_exchange_logic(user_id, exchange_id)
    flash(result['message'], result['status'])

    return redirect(url_for('view_my_requests'))

@app.route('/exchange/reject/<int:exchange_id>', methods=['POST'])
@user_login_required
def reject_exchange(exchange_id):
    user_id = session.get('entity_id')
    if not user_id:
        flash("No se pudo identificar la sesión de usuario.", "error")
        return redirect(url_for('login'))
    
    result = logic.reject_exchange_logic(user_id, exchange_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('view_my_requests'))


# --- Map Routes ---

@app.route('/map')
def view_map():
    map_points = logic.get_map_points()
    return render_template('view_map.html', map_points=map_points)

@app.route('/map/add', methods=['GET', 'POST'])
@login_required
def add_map_point():
    entity_id = session.get('entity_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("No se pudo identificar tu sesión.", "error")
        return redirect(url_for('view_map'))
    
    if request.method == 'POST':
        permission_code = request.form.get('permission_code')
        name = request.form.get('name')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        point_type = request.form.get('point_type')
        description = request.form.get('description')
        
        if not all([permission_code, name, latitude, longitude, point_type]):
            flash("Todos los campos requeridos deben completarse.", "error")
            return redirect(url_for('add_map_point'))
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except ValueError:
            flash("La latitud y longitud deben ser números válidos.", "error")
            return redirect(url_for('add_map_point'))
        
        result = logic.add_map_point_logic(
            entity_id, entity_type, permission_code, name, 
            latitude, longitude, point_type, description
        )
        
        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('view_map'))
    else:
            return redirect(url_for('add_map_point'))
    
    return render_template('add_map_point.html')

@app.route('/save_map_point', methods=['POST'])
def save_map_point():
    if request.method == 'POST':
        data = request.json
        point = {
            'name': data.get('name'),
            'description': data.get('description'),
            'point_type': data.get('point_type'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'added_by': session.get('name', 'Anonymous'),
            'creator_id': session.get('entity_id', 1)
        }
        
        result = logic.save_map_point(point)
        return jsonify(result)


# --- Challenge Routes ---

@app.route('/challenges')
@login_required
def view_challenges():
    entity_type = session.get('entity_type')
    
    result = logic.search_challenges_logic(entity_type)
    
    if result['status'] == 'success':
        challenges = result.get('data', [])
        
        active_challenges = []
        if 'entity_type' in session:
            entity_id = session.get('entity_id')
            active_result = logic.get_my_active_challenges_logic(entity_id, entity_type)
            if active_result['status'] == 'success':
                active_challenges = active_result.get('data', [])
        
        return render_template('view_challenges.html', 
                              challenges=challenges, 
                              active_challenges=active_challenges)
    else:
        flash(result['message'], result['status'])
        return render_template('view_challenges.html', challenges=[], active_challenges=[])

@app.route('/challenge/join/<int:challenge_id>', methods=['POST'])
@login_required
def join_challenge(challenge_id):
    entity_id = session.get('entity_id')
    entity_type = session.get('entity_type')
    
    if not entity_id or not entity_type:
        flash("No se pudo identificar tu sesión.", "error")
        return redirect(url_for('view_challenges'))
    
    result = logic.join_challenge_logic(entity_id, entity_type, challenge_id)
    flash(result['message'], result['status'])
    
    return redirect(url_for('view_challenges'))

@app.route('/achievements')
@login_required
def view_achievements():
    entity_type = session.get('entity_type')
    entity_id   = session.get('entity_id')

    result = logic.search_achievements_logic(entity_type)

    unlocked = []
    if entity_type == 'user':
        user_data = logic.get_entity_by_id(entity_id, entity_type)
        if user_data['status'] == 'success':
            unlocked = user_data['data'].get('achievements', [])

    if result['status'] == 'success':
        achievements = result['data']
    else:
        flash(result['message'], result['status'])
        achievements = []

    return render_template(
        'view_achievements.html',
        achievements=achievements,
        unlocked_achievements=unlocked
    )

# --- Admin Routes ---

def admin_required(f):
    """Decorator to ensure admin is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('entity_type') != 'admin':
            flash("Se requiere acceso de administrador para esta página.", "error")
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if session.get('entity_type') == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        result = logic.admin_login(username, password)
        
        if result['status'] == 'success':
            session.clear()
            session['entity_type'] = 'admin'
            session['admin_id'] = result['admin_id']
            session['name'] = result['name']
            
            flash("¡Inicio de sesión de administrador exitoso!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash(result['message'], result['status'])
            return redirect(url_for('admin_login'))
    
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    flash("Administrador desconectado exitosamente.", "success")
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    users_count = logic.get_users_count()
    orgs_count = logic.get_orgs_count()
    events_count = logic.get_events_count()
    items_count = logic.get_items_count()
    
    all_users = logic.users_view()
    all_orgs = logic.orgs_view()
    
    top_orgs = logic.get_top_orgs_by_points(limit=5)

    return render_template('admin/dashboard.html',
                          users_count=users_count,
                          orgs_count=orgs_count,
                          events_count=events_count,
                          items_count=items_count,
                          all_users=all_users,
                          all_orgs=all_orgs,
                          top_orgs=top_orgs)

@app.route('/admin/users')
@admin_required
def admin_users():
    query = request.args.get('q', '')
    
    users = logic.search_users(query=query)
    
    return render_template('admin/users.html', users=users, query=query)

@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    admin_id = session.get('admin_id')
    result = logic.admin_delete_user_logic(admin_id, user_id)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_users'))
  
@app.route('/admin/organizations')
@admin_required
def admin_organizations():
    query = request.args.get('q', '')
    
    result = logic.search_orgs_logic(query=query)
    
    if result['status'] == 'success':
        organizations = result.get('data', [])
        return render_template('admin/organizations.html', organizations=organizations, query=query)
    else:
        flash(result['message'], result['status'])
        return render_template('admin/organizations.html', organizations=[], query=query)
    
@app.route('/admin/organizations/<int:org_id>/delete', methods=['POST'])
@admin_required
def admin_delete_organization(org_id):
    admin_id = session.get('admin_id')
    result = logic.admin_delete_org_logic(admin_id, org_id)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_organizations'))

@app.route('/admin/events')
@admin_required
def admin_events():
    query = request.args.get('q', '')
    
    result = logic.admin_get_events(query)
    
    if result['status'] == 'success':
        events = result.get('data', [])
        return render_template('admin/events.html', events=events, query=query)
    else:
        flash(result['message'], result['status'])
        return render_template('admin/events.html', events=[], query=query)

@app.route('/admin/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def admin_delete_event(event_id):
    result = logic.admin_delete_event(event_id)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_events'))

@app.route('/admin/challenges')
@admin_required
def admin_challenges():
    user_result = logic.search_challenges_logic('user')
    org_result = logic.search_challenges_logic('organization')
    
    challenges = []
    
    if user_result['status'] == 'success':
        challenges.extend(user_result.get('data', []))
        
    if org_result['status'] == 'success':
        challenges.extend(org_result.get('data', []))
        
    return render_template('admin/challenges.html', challenges=challenges)

@app.route('/admin/challenges/create', methods=['GET', 'POST'])
@admin_required
def admin_create_challenge():
    if request.method == 'POST':
        admin_id = session.get('admin_id')
        name = request.form.get('title')
        description = request.form.get('description')
        points = int(request.form.get('points', 0))
        target_entity = request.form.get('target_entity')
        
        goal_type = 'participation'
        goal_target = 1
        time_allowed = 0
        
        result = logic.admin_create_challenge_logic(
            admin_id, name, description, goal_type, goal_target, 
            points, time_allowed, target_entity
        )
        
        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('admin_challenges'))
        
    return render_template('admin/create_challenge.html')

@app.route('/admin/challenges/<int:challenge_id>/delete', methods=['POST'])
@admin_required
def admin_delete_challenge(challenge_id):
    admin_id = session.get('admin_id')
    target_entity = request.form.get('target_entity', 'user')
    result = logic.admin_delete_challenge_logic(admin_id, challenge_id, target_entity)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_challenges'))

@app.route('/admin/achievements')
@admin_required
def admin_achievements():
    user_result = logic.search_achievements_logic('user')
    org_result = logic.search_achievements_logic('organization')
    
    achievements = []
    
    if user_result['status'] == 'success':
        achievements.extend(user_result.get('data', []))
        
    if org_result['status'] == 'success':
        achievements.extend(org_result.get('data', []))
        
    return render_template('admin/achievements.html', achievements=achievements)

@app.route('/admin/achievements/create', methods=['GET', 'POST'])
@admin_required
def admin_create_achievement():
    if request.method == 'POST':
        admin_id = session.get('admin_id')
        name = request.form.get('name')
        description = request.form.get('description')
        target_entity = request.form.get('target_entity')
        points_threshold = int(request.form.get('points_threshold', 0))
        badge_icon = request.form.get('badge_icon', 'default_badge')
        
        result = logic.admin_create_achievement_logic(
            admin_id, name, description, points_threshold, badge_icon, target_entity
        )
        
        flash(result['message'], result['status'])
        if result['status'] == 'success':
            return redirect(url_for('admin_achievements'))
        
    return render_template('admin/create_achievement.html')

@app.route('/admin/achievements/<int:achievement_id>/delete', methods=['POST'])
@admin_required
def admin_delete_achievement(achievement_id):
    admin_id = session.get('admin_id')
    target_entity = request.form.get('target_entity', 'user')
    result = logic.admin_delete_achievement_logic(admin_id, achievement_id, target_entity)
    flash(result['message'], result['status'])
    return redirect(url_for('admin_achievements'))

@app.route('/admin/stats')
@admin_required
def admin_stats():
    stats = {
        'total_users': logic.get_users_count(),
        'total_orgs': logic.get_orgs_count(),
        'total_events': logic.get_events_count(),
        'total_items': logic.get_items_count(),
        'users': logic.users_view(),
        'orgs': logic.orgs_view(),
        'top_orgs': logic.get_top_orgs_by_points(limit=10)
    }
    
    return render_template('admin/stats.html', stats=stats)

@app.route('/admin/update_org_points', methods=['GET', 'POST'])
@admin_required
def admin_update_org_points():
    if request.method == 'POST':
        result = logic.update_org_points_from_members_logic()
        flash(result['message'], result['status'])
        
        if result['status'] == 'success' and 'updated_orgs' in result:
            updated_orgs = result['updated_orgs']
            return render_template('admin/org_points_updated.html', updated_orgs=updated_orgs)
        
    return render_template('admin/update_org_points.html')

@app.route('/index_prueba_messages')
def chat_test():
    session.clear()
    session['entity_id'] = 1
    session['entity_type'] = 'user'
    session['name'] = f'Usuario Temporal {1}'
    session.modified = True
    print(f"[Workaround] Sesión establecida manualmente para user_id: {1}")
    current_user_id = session.get('entity_id')
    return render_template('index_prueba_messages.html', current_user_id=current_user_id)

@app.route('/user/<int:user_id>')
@login_required
def view_user_profile(user_id):
    res = logic.get_entity_by_id(user_id, 'user')
    if res['status']!='success': 
        flash(res['message'], 'error')
        return redirect(url_for('search_users'))
    user_data = res['data']
    badges = logic.get_entity_achievements(user_id, 'user').get('data', [])
    user_orgs = logic.get_user_orgs_logic(user_id).get('data', [])
    points = user_data.get('points', 0)
    return render_template('user_profile.html',
                           user_data=user_data,
                           badges=badges,
                           user_orgs=user_orgs,
                           points=points)

@app.route('/chat/<int:user_id>')
@login_required
def private_chat(user_id):
    my_id = session['entity_id']
    msgs = logic.get_conversation_logic(
        my_id, session['entity_type'],
        user_id, 'user',
        limit=50
    ).get('data', [])

    recipient = logic.get_entity_by_id(user_id, 'user').get('data', {})
    recipient_name = recipient.get('name', 'Usuario')

    return render_template(
        'chat.html',
        recipient_id=user_id,
        recipient_name=recipient_name,
        messages=msgs
    )

if __name__ == '__main__':
    import db_conn
    print("Setting up database...")
    db_conn.setup_database()
    print("Database setup complete")

    socketio.run(app, host = '0.0.0.0', port = 5000)