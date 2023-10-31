import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, request, render_template
import pandas as pd
from collections import defaultdict
from geopy.distance import geodesic

app = Flask(__name__)

# 1. 데이터 로드 및 처리
stations_df = pd.read_csv('C:\\Users\\USER\\RToday\\서울시 역사마스터 정보 수정.csv', encoding='cp949')
connections_df = pd.read_csv('C:\\Users\\USER\\RToday\\서울시 역사마스터 정보 순번 수정.csv', encoding='cp949')
protest_data = pd.read_csv('static/RT_SU_Update.csv')  # 시위 데이터 파일 경로를 수정해주세요.

# 2. 매핑 딕셔너리 생성
def find_direction_pattern_stations(station_order):
    return station_order[station_order.apply(lambda row: row.str.contains('|.*방향').any(), axis=1)]

def extract_direction_stations(direction_pattern_stations):
    return direction_pattern_stations.apply(lambda row: row[row.str.contains('|.*방향', na=False)], axis=1).dropna(how='all')

def create_mapping_dict(direction_stations):
    mapping = {}
    for _, series in direction_stations.iterrows():
        for val in series.dropna().values:
            station_name = val.split('|')[0]
            line_name = val.split('_')[-1]
            mapping[val] = f"{station_name}_{line_name}"
    return mapping

direction_pattern_stations = find_direction_pattern_stations(connections_df)
direction_stations = extract_direction_stations(direction_pattern_stations)
name_mapping = create_mapping_dict(direction_stations)

# 3. 지하철역 간의 연결 정보 생성
connections = defaultdict(list)
for _, row in connections_df.iterrows():
    line_stations = [station for station in row[1:] if pd.notna(station)]
    for i in range(len(line_stations) - 1):
        station1 = name_mapping.get(line_stations[i], line_stations[i])
        station2 = name_mapping.get(line_stations[i + 1], line_stations[i + 1])
        connections[station1].append(station2)
        connections[station2].append(station1)

# 환승 가중치 설정
for station in stations_df['unique_name']:
    for adj_station in stations_df['unique_name']:
        if station.split('_')[0] == adj_station.split('_')[0] and station != adj_station:
            connections[station].append((adj_station, 0.0833))

# 4. Dijkstra 알고리즘 구현
def dijkstra_with_path(graph, start, end):
    distances = {station: float('infinity') for station in graph}
    distances[start] = 0
    previous_stations = {station: None for station in graph}
    stations = list(graph.keys())
    while stations:
        current_station = min(stations, key=lambda station: distances[station])
        if distances[current_station] == float('infinity'):
            break
        if current_station == end:
            path = []
            while previous_stations[current_station]:
                path.append(current_station)
                current_station = previous_stations[current_station]
            path.append(start)
            return distances[end], path[::-1]
        for adjacent, weight in graph[current_station].items():
            distance = distances[current_station] + weight
            if distance < distances[adjacent]:
                distances[adjacent] = distance
                previous_stations[adjacent] = current_station
        stations.remove(current_station)
    return None, []

# 5. 시위가 발생하는 지하철역 반경 계산
def find_stations_within_radius_updated(coordinates, radius, station_data):
    stations_within_radius = []
    for _, row in station_data.iterrows():
        station_coords = (row['위도'], row['경도'])
        if geodesic(coordinates, station_coords).km <= radius:
            stations_within_radius.append(row['unique_name'])
    return stations_within_radius

@app.route('/get_path', methods=['GET', 'POST'])
def get_path():
    if request.method == 'POST':
        start_station = request.form.get('start_station', '서울역_1호선')
        end_station = request.form.get('end_station', '신촌_2호선')
        time = request.form.get('time', '14:00')
    else:
        start_station = request.args.get('start_station', '서울역_1호선')
        end_station = request.args.get('end_station', '신촌_2호선')
        time = request.args.get('time', '14:00')
    
    try:
        result = get_path_based_on_time(start_station, end_station, time, protest_data)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}, 500




def get_path_based_on_time(start_station, end_station, time, protest_data):
    # 해당 시간에 발생하는 시위 정보 추출
    matching_protests = protest_data[protest_data['집회 일시'] == time]
    
    # 모든 가능한 시위 정보를 반영하여 경로 계산
    paths = []
    for _, row in matching_protests.iterrows():
        coords = row['Coordinates']
        population = row['신고 인원']
        radius = (population ** 0.5) * 10
        path = get_safe_path(start_station, end_station, coords, population)
        paths.append(path)
    
    # 모든 경로 중에서 가장 짧은 경로 선택 (여기서는 각 경로의 길이만 고려하였습니다)
    shortest_path = min(paths, key=len) if paths else "가능한 우회로가 없습니다. 다른 이동수단을 이용해주세요."
    
    return shortest_path


@app.route('/')
def index():
    start_station = request.args.get('start_station', '서울역_1호선')
    end_station = request.args.get('end_station', '신촌_2호선')
    time = request.args.get('time', '14:00')
    
    result = get_path_based_on_time(start_station, end_station, time, protest_data)
    
    return render_template('index.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
