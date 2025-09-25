import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

app = Flask(__name__)
CORS(app, supports_credentials=True) 

app.config['SECRET_KEY'] = 'a-secret-key-you-should-change'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    def set_password(self, password): self.password_hash = generate_password_hash(password)
    def check_password(self, password): return check_password_hash(self.password_hash, password)

class TradePlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_name = db.Column(db.String(50), nullable=False)
    entry_price = db.Column(db.Float, nullable=False)
    desired_gain = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id): return User.query.get(int(user_id))

def get_volatility_rating(percentage):
    if percentage < 2: return "Stable"
    elif percentage < 4: return "Minor Fluctuation"
    elif percentage < 7: return "Moderate Volatility"
    elif percentage < 10: return "High Volatility"
    else: return "Extreme Volatility"

def calculate_historical_analysis(historical_data):
    if not historical_data: return {}
    dates = [day['date'] for day in historical_data if day.get('date')]
    if not dates: return {}
    start_date = min(dates); end_date = max(dates)
    daily_volatilities = []
    max_high = 0; min_low = float('inf')
    for day in historical_data:
        high = day.get('high'); low = day.get('low')
        if high is None or low is None: continue
        if low > 0:
            volatility = ((high - low) / low) * 100
            daily_volatilities.append(volatility)
        if high > max_high: max_high = high
        if low < min_low: min_low = low
    if not daily_volatilities: return {}
    average_daily_volatility = sum(daily_volatilities) / len(daily_volatilities)
    return { "start_date": start_date, "end_date": end_date, "days": len(daily_volatilities), "avg_vol": average_daily_volatility, "avg_vol_rating": get_volatility_rating(average_daily_volatility), "max_vol": max(daily_volatilities), "period_fluc": ((max_high - min_low) / min_low) * 100 if min_low > 0 else 0 }

def calculate_day_of_week_analysis(historical_data):
    if not historical_data: return {}
    weekly_stats = { day: {"highs": [], "lows": [], "vols": []} for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] }
    for day in historical_data:
        try:
            date_obj = datetime.datetime.strptime(day['date'], '%Y-%m-%d')
            day_name = date_obj.strftime('%A')
            weekly_stats[day_name]["highs"].append(day['high'])
            weekly_stats[day_name]["lows"].append(day['low'])
            if day.get('low', 0) > 0:
                vol = ((day['high'] - day['low']) / day['low']) * 100
                weekly_stats[day_name]["vols"].append(vol)
        except (ValueError, KeyError):
            continue
    report = {}
    for day_name, data in weekly_stats.items():
        if len(data["vols"]) > 0:
            report[day_name] = { "avg_high": sum(data["highs"]) / len(data["highs"]), "avg_low": sum(data["lows"]) / len(data["lows"]), "avg_vol": sum(data["vols"]) / len(data["vols"]) }
    return report

def calculate_target_gain_plan(historical_data, trade_plan):
    if not historical_data: return {}
    desired_gain_percent = trade_plan.get('desired_gain', 0)
    entry_price = trade_plan.get('entry_price', 0)
    successful_days = 0
    total_days = len(historical_data)
    if total_days == 0: return {}
    gain_multiplier = 1 + (desired_gain_percent / 100)
    for day in historical_data:
        low_price = day.get('low')
        high_price = day.get('high')
        if low_price is None or high_price is None or low_price == 0:
            continue
        if high_price >= low_price * gain_multiplier:
            successful_days += 1
    success_probability = (successful_days / total_days) * 100
    return { "required_exit_price": entry_price * gain_multiplier, "success_probability": success_probability, "successful_days": successful_days, "total_days": total_days }

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'Username already exists'}), 409
    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return jsonify({'message': 'Logged in successfully!'})
    return jsonify({'message': 'Invalid username or password'}), 401

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully!'})

@app.route('/analyze', methods=['POST'])
@login_required
def analyze_data_endpoint():
    price_data = request.get_json().get('price_data', [])
    historical_results = calculate_historical_analysis(price_data)
    day_of_week_results = calculate_day_of_week_analysis(price_data)
    return jsonify({ "historical_analysis": historical_results, "day_of_week_analysis": day_of_week_results })

@app.route('/plan', methods=['POST'])
@login_required
def plan_trade_endpoint():
    data = request.get_json()
    price_data = data.get('price_data', [])
    trade_plan = data.get('trade_plan', {})
    plan_results = calculate_target_gain_plan(price_data, trade_plan)
    return jsonify(plan_results)
