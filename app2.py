# Entire Flask Web Application Code

# Module Imports
import os
from flask import Flask, request, render_template
import pandas as pd
from collections import defaultdict
from geopy.distance import geodesic
import requests
import math

# Initialize Flask app
app = Flask(__name__)

# Constants for Kakao Maps API
KAKAO_API_KEY = "85d182fa8471245c9ea35ce700b3b82a"
KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"

# Load subway station data and connections
stations_df = pd.read_csv("static/서울시 역사마스터 정보 수정.csv", encoding='cp949')
connections_df = pd.read_csv("static/서울시 역사마스터 정보 순번 수정.csv", encoding='cp949')

# Load protest data
protest_data = pd.read_csv("static/RT_SU_Update.csv")

# Create subway station graph
graph = {}
for _, row in connections_df.iterrows():
    stations = row.dropna().tolist()[1:]
    for i in range(len(stations) - 1):
        if stations[i] not in graph:
            graph[stations[i]] = []
        if stations[i + 1] not in graph:
            graph[stations[i + 1]] = []
        graph[stations[i]].append(stations[i + 1])
        graph[stations[i + 1]].append(stations[i])

# Extract station coordinates
station_coords = {}
for _, row in stations_df.iterrows():
    station_name = f"{row['역사명']}_{row['호선']}"
    station_coords[station_name] = (row['위도'], row['경도'])

# Function to get coordinates from address
def get_coordinates_from_address(address):
    headers = {
        "Authorization": f"KakaoAK {KAKAO_API_KEY}"
    }
    params = {
        "query": address
    }
    response = requests.get(KAKAO_GEOCODE_URL, headers=headers, params=params)
    if response.status_code == 200 and 'documents' in response.json():
        documents = response.json()['documents']
        if documents:
            return documents[0]['y'], documents[0]['x']
    return None, None


# Step 3 & 4: Define the path extraction functions

# Function to find stations within a given radius using geodesic distance
def find_stations_within_radius(protest_coords, radius, stations_df):
    stations_within_radius = []
    for _, row in stations_df.iterrows():
        station_coords = (row['위도'], row['경도'])
        distance = geodesic(station_coords, protest_coords).meters
        if distance <= radius:
            stations_within_radius.append(f"{row['역사명']}_{row['호선']}")
    return stations_within_radius

from collections import deque

def dijkstra(graph, start, end):
    distances = {vertex: float('infinity') for vertex in graph}
    previous_vertices = {vertex: None for vertex in graph}
    distances[start] = 0
    vertices = list(graph.keys())

    while vertices:
        current_vertex = min(vertices, key=lambda vertex: distances[vertex])
        vertices.remove(current_vertex)
        for neighbour in graph[current_vertex]:
            alternative_route = distances[current_vertex] + 1  # 1 represents the weight of each edge
            if alternative_route < distances[neighbour]:
                distances[neighbour] = alternative_route
                previous_vertices[neighbour] = current_vertex

    path, current_vertex = deque(), end
    while previous_vertices[current_vertex] is not None:
        path.appendleft(current_vertex)
        current_vertex = previous_vertices[current_vertex]
    if path:
        path.appendleft(start)
        
    return list(path)

# Function to find a safe path
def find_safe_path(graph, start, end, protest_data, station_coords):
    stations_to_avoid = []
    for _, row in protest_data.iterrows():
        coords = get_coordinates_from_address(row['관련 지역'])
        if coords[0] and coords[1]:
            radius = math.sqrt(row['신고 인원']) * 10  # 10 meters per sqrt of reported participants
            stations_within_radius = find_stations_within_radius(station_coords, coords, radius)
            stations_to_avoid.extend(stations_within_radius)
    safe_graph = {k: [station for station in v if station not in stations_to_avoid] for k, v in graph.items()}
    return dijkstra(safe_graph, start, end)

# Function to get path based on time
def get_path_based_on_time(graph, start, end, protest_data, station_coords, time_str):
    date_str = str(protest_data['날짜'].iloc[0])
    formatted_date_str = f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:6]}"
    departure_time = f"{formatted_date_str} {time_str}"
    
    active_protests = protest_data[protest_data['집회 일시'] == departure_time]
    if active_protests.empty:
        return dijkstra(graph, start, end)
    else:
        return find_safe_path(graph, start, end, active_protests, station_coords)

# Step 5: Set up Flask routes

@app.route('/')
def index():
    start_station = request.args.get('start_station', '서울역_1호선')
    end_station = request.args.get('end_station', '신촌_2호선')
    time = request.args.get('time', '14:00')
    
    result = get_path_based_on_time(graph, start_station, end_station, protest_data, station_coords, time)
    
    return render_template('index.html', result=result)

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
        result = get_path_based_on_time(graph, start_station, end_station, protest_data, station_coords, time)
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}, 500

# Placeholder for the final step...
if __name__ == '__main__':
    app.run(debug=True)
