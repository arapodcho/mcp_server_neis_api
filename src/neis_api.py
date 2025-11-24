import os
import re
import requests
import dotenv
dotenv.load_dotenv()

URL_SCHOOL_TIMETABLE = "http://open.neis.go.kr/hub/hisTimetable"
URL_SCHOOL_INFO = "http://open.neis.go.kr/hub/schoolInfo"
URL_SCHOOL_SCHEDULE = "http://open.neis.go.kr/hub/SchoolSchedule"

SERVICE_KEY = os.getenv("NEIS_SERVICE_KEY") or os.getenv("SERVICE_KEY") or ""

def get_school_info(school_name: str):
    params = {
        'KEY' : SERVICE_KEY,
        'Type': 'json',
        'pIndex': '1',
        'pSize': '100',
        'SCHUL_NM': school_name    
    }
    response = requests.get(URL_SCHOOL_INFO, params=params)
    data = response.json()
    
    return data

# print("test_get_school_info")
# print(get_school_info("진관초등학교"))