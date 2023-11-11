from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime, timedelta
import atexit
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
# Configure the SQLAlchemy part
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comments.db'
db = SQLAlchemy(app)

migrate = Migrate(app, db)

# Define the Comment model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(250), nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Comment {self.content}>'

# Define the PastComment model
class PastComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(255), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False)
    date_moved = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<PastComment {self.content}>'

    def to_dict(self):
        return {
            'id': self.id,
            'content': self.content,
            'date_posted': self.date_posted.isoformat(),
            'date_moved': self.date_moved.isoformat()
        }


# Initialize the database
with app.app_context():
    db.create_all()

# Route for the main page
@app.route('/')
def index():
    return render_template('index.html')  # The updated HTML file needs to be saved as 'index.html'

# Route for submitting a comment
@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    content = request.form['content']
    new_comment = Comment(content=content)
    db.session.add(new_comment)
    db.session.commit()
    return jsonify(success=True)

# Route for getting comments
@app.route('/get_comments')
def get_comments():
    comments = Comment.query.all()
    return render_template('comments.html', comments=comments)  # This needs a new template

# Function to reset comments daily
def reset_comments():
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    Comment.query.filter(Comment.date_posted < yesterday).delete()
    db.session.commit()

@app.route('/get_past_comments')
def get_past_comments():
    # 데이터베이스에서 과거 댓글 데이터를 불러옵니다.
    past_comments = PastComment.query.all()
    # 데이터를 JSON 형식으로 변환하여 반환합니다.
    return jsonify({'past_comments': [comment.to_dict() for comment in past_comments]})


# Scheduler to reset comments daily at midnight
scheduler = BackgroundScheduler()
scheduler.add_job(func=reset_comments, trigger="cron", hour=0, minute=0)
scheduler.start()

# Shutdown your cron thread if the web process is stopped
atexit.register(lambda: scheduler.shutdown())

if __name__ == '__main__':
    app.run(debug=True)
