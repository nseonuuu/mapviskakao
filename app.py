import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, render_template, jsonify
import pandas as pd

app = Flask(__name__)

protest_data = pd.read_csv('RT_SU_Update.csv')

def get_safe_path(start_station, end_station, protest_coords, protest_population):
    return f"From {start_station} to {end_station}, avoiding protest at {protest_coords} with {protest_population} people."

def get_path_based_on_time(start_station, end_station, time, protest_data):
    matching_protests = protest_data[protest_data['Time'] == time]
    paths = []
    for _, row in matching_protests.iterrows():
        coords = row['Coordinates']
        population = row['신고 인원']
        path = get_safe_path(start_station, end_station, coords, population)
        paths.append(path)
    
    shortest_path = min(paths, key=len) if paths else "가능한 우회로가 없습니다. 다른 이동수단을 이용해주세요."
    return shortest_path

@app.route('/')
def index():
    start_station = request.args.get('start_station')
    end_station = request.args.get('end_station')
    time = '14:00'  # 사용자가 선택한 시간
    result = get_path_based_on_time(start_station, end_station, time, protest_data)
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
