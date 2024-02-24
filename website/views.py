from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from . import db
import json

from .models import Question, Answer, Reply, User
views = Blueprint('views', __name__)


@views.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html", user=current_user)

@views.route('/terms_of_service')
def  terms_of_service():
    return render_template('terms_of_service.html', user=current_user)

@views.route('/privacy_policy')
def  privacy_policy():
    return render_template('privacy_policy.html', user=current_user)  
@views.route('/help')
@login_required
def help():
    return render_template("help.html",user=current_user)

@views.route('/profile', methods=['GET','POST'])
@login_required
def profile():
    if  request.method == "POST":
        flash('Password succesfully!',category='success')
        return render_template('home.html',user=current_user)
    game=Game.query.filter_by(user_id=current_user.id).first()
    return render_template('profile.html',user=current_user,game=game)

@views.route('/leaderboard')
@login_required
def leaderboard():
    users = db.session.query(Game.user_id, (Game.won / (Game.played - Game.won)).label('win_loss_ratio')).all()
    users2 = db.session.query(Game.user_id, (Game.won / Game.played * 100).label('percentage')).all()
    sorted_users_played = sorted(users, key=lambda x: x.win_loss_ratio if x.win_loss_ratio is not None else float('-inf'))
    sorted_users = sorted(users2, key=lambda x: x.percentage if x.percentage is not None else float('-inf'), reverse=True)
    
    # Enumerate the sorted_users
    enumerated_users = list(enumerate(sorted_users))

    top_user = sorted_users[0] if sorted_users else None
    return render_template('leaderboard.html', user=current_user, top_user=top_user, sorted_users=enumerated_users, sorted_users_played=sorted_users_played)


@views.route('/messages')
@login_required
def messages():
    
    messages = db.session.query(Message.content, User.first_name).join(User).all()
    return render_template('messages.html', messages=messages, user=current_user)

from .models import db, Message
from .forms import ContactForm

@views.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    if request.method == 'POST':
        message_content = request.form.get('message')
        if message_content:
            try:
                # Create a new Message instance
                new_message = Message(content=message_content, user_id=current_user.id)
                db.session.add(new_message)
                db.session.commit()
                flash('Your message has been sent!', category='success')
                return redirect(url_for('views.support'))
            except Exception as e:
                flash('An error occurred while sending your message. Please try again.', category='error')
                print(f"Error sending message: {e}")  # Print the error to debug
        else:
            flash('Message cannot be empty!', category='error')
    return render_template("support.html", user=current_user)

@views.route('/forum')
@login_required
def forum():
    questions = Question.query.all()
    return render_template("forum.html", questions=questions, user=current_user)

@views.route('/forum/question/<int:question_id>', methods=['GET', 'POST'])
@login_required
def view_question(question_id):
    question = Question.query.get_or_404(question_id)
    answers = Answer.query.filter_by(question_id=question_id).all()      
    if request.method == 'POST':
        answer_content = request.form.get('content')
        if answer_content:
            try:
                new_answer = Answer(content=answer_content, question_id=question.id, user_id=current_user.id)
                db.session.add(new_answer)
                db.session.commit()
                flash('Your answer has been posted!', category='success')
                return redirect(url_for('views.view_question', question_id=question.id))
            except Exception as e:
                flash('An error occurred while posting your answer. Please try again.', category='error')
                views.logger.error(f"Error posting answer: {e}")
        else:
            flash('Answer cannot be empty!', category='error')    
    return render_template("view_question.html", question=question, answers=answers, user=current_user)


@views.route('/forum/reply/<int:answer_id>', methods=['POST'])
@login_required
def post_reply(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    reply_content = request.form.get('content')
    if reply_content:
        new_reply = Reply(content=reply_content, answer_id=answer.id, user_id=current_user.id)
        db.session.add(new_reply)
        db.session.commit()
        flash('Your reply has been posted!', category='success')
    else:
        flash('Reply cannot be empty!', category='error')
    return redirect(url_for('views.view_question', question_id=answer.question.id))


@views.route('/forum/answers/<int:question_id>')
@login_required
def view_answers(question_id):
    question = Question.query.get_or_404(question_id)
    answers = Answer.query.filter_by(question_id=question_id).all()
    return render_template("view_answers.html", question=question, answers=answers, user=current_user)




@views.route('/submit-question', methods=['GET', 'POST'])
@login_required
def submit_question():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            new_question = Question(title=title, content=content, user_id=current_user.id)
            db.session.add(new_question)
            db.session.commit()
            flash('Your question has been submitted!', category='success')
            return redirect(url_for('views.forum'))
        else:
            flash('Title and content cannot be empty!', category='error')
    return render_template("submit_question.html", user=current_user)



from .models import Game
@views.route('/startgame', methods=['GET', 'POST'])
@login_required
def startgame():
    if request.method == 'POST':
        data = request.json
        if data:
            received_data = data.get('data')
            x_won=0
            x_lose=0
            x_draw=0
            if received_data:
                print('Received data from JS:', received_data)
                
                game = Game.query.filter_by(user_id=current_user.id).first()
                if received_data=='You Win':
                    x_won=1
                elif received_data=='Draw':
                    x_draw=1
                else:
                    x_lose=1
                if game:
                    # If user exists, update the played and won counts
                    game.played += 1
                    if x_won:
                        game.won += x_won
                    elif x_draw:
                        game.draw += x_draw                    
                else:
                    game = Game(user_id=current_user.id, played=1, won=x_won, draw=x_draw)
                    db.session.add(game)

                db.session.commit()
                            
                return jsonify({'message': 'Data received successfully'}), 200
            else:
                return jsonify({'error': 'Data key not found in JSON'}), 400
        else:
            return jsonify({'error': 'Invalid JSON format or no data provided'}), 400
    # If it's a GET request, render the startgame.html template
    return render_template('startgame.html', user=current_user)











