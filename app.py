from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
import csv
from flask import make_response

# 🔥 New block to define DB path in project root
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'todo.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # content = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default="active")
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    deleted_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    subject = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    stakeholders = db.Column(db.String(200))
    impact = db.Column(db.Text)
    def __repr__(self):
        return f'<Task {self.id}>'

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            subject = request.form['subject']
            description = request.form.get('description')
            start_date = request.form.get('start_date') or None
            due_date = request.form.get('due_date') or None
            stakeholders = request.form.get('stakeholders')
            impact = request.form.get('impact')

            # Convert dates from string to datetime.date (if provided)
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
            due_date = datetime.strptime(due_date, '%Y-%m-%d').date() if due_date else None

            new_task = Task(
                subject=subject,
                description=description,
                start_date=start_date,
                due_date=due_date,
                stakeholders=stakeholders,
                impact=impact,
                status='active',
                created_at=datetime.utcnow()
            )

            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except Exception as e:
            print("Error:", e)
            return 'There was an issue adding your task'
    else:
        tasks = Task.query.filter_by(status="active").order_by(Task.id).all()
        return render_template('index.html', tasks=tasks)
@app.route('/archived')
def view_archived():
    archived_tasks = Task.query.filter_by(status="archived").order_by(Task.id).all()
    return render_template('archived.html', tasks=archived_tasks)

@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get_or_404(id)
    task.deleted_at = datetime.utcnow()
    db.session.delete(task)  # You can also just set a status like 'deleted' and skip the delete()
    db.session.commit()
    return redirect('/')
@app.route('/archive/<int:id>')
def archive(id):
    task = Task.query.get_or_404(id)
    task.status = 'archived'
    task.completed_at = datetime.utcnow()
    db.session.commit()
    return redirect('/')
@app.route('/archived')
def archived():
    archived_tasks = Task.query.filter_by(status='archived').all()
    return render_template('archived.html', tasks=archived_tasks)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    task = Task.query.get_or_404(id)
    if request.method == 'POST':
        task.content = request.form['content']
        task.updated_at = datetime.utcnow()
        db.session.commit()
        return redirect('/')
    return render_template('edit.html', task=task)

@app.route('/download-archived')
def download_archived():
    tasks = Task.query.filter_by(status='archived').all()

    # Create the CSV in-memory
    output = []
    header = ['S.No', 'Task Name', 'Created At', 'Completed At']
    output.append(header)

    for i, task in enumerate(tasks, 1):
        output.append([
            i,
            task.content,
            task.created_at.strftime('%Y-%m-%d %H:%M') if task.created_at else '',
            task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else ''
        ])

    # Build the CSV response
    response = make_response('\n'.join([','.join(map(str, row)) for row in output]))
    response.headers['Content-Disposition'] = 'attachment; filename=archived_tasks.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)
