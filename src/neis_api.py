import os
import re
import requests
import dotenv
dotenv.load_dotenv()

URL_SCHOOL_TIMETABLE = "http://open.neis.go.kr/hub/hisTimetable"
URL_SCHOOL_INFO = "http://open.neis.go.kr/hub/schoolInfo"
URL_SCHOOL_SCHEDULE = "http://open.neis.go.kr/hub/SchoolSchedule"

SERVICE_KEY = os.getenv("NEIS_SERVICE_KEY") or os.getenv("SERVICE_KEY") or ""

def _missing_key_mode() -> bool:
    return SERVICE_KEY.strip() == ""

def neis_get_school_info(school_name: str):
    result_value = {
                    'valid': False,
                    'message': 'Initialized',
                    'school_num': 0,                    
                    'school_name': [],
                    'school_code': [],
                    'org_name': [],
                    'org_code': []
                    }
    # Fallback: if key missing, limit output to at most 5 results (degraded mode).
    degraded = _missing_key_mode()
    
    params = {
        'Type': 'json',
        'pIndex': '1',
        'pSize': '100' if not degraded else '5',
        'SCHUL_NM': school_name    
    }
    if not degraded:
        params['KEY'] = SERVICE_KEY
    response = requests.get(URL_SCHOOL_INFO, params=params)
    data = response.json()
    return_code = data.get('RESULT', {}).get('CODE')
    if return_code is None:
        try:
            school_info_list = data.get('schoolInfo', [])[-1].get('row', [])
            for idx, school_info in enumerate(school_info_list):
                if degraded and idx >= 5:
                    break
                result_value['school_name'].append(school_info.get('SCHUL_NM'))
                result_value['school_code'].append(school_info.get('SD_SCHUL_CODE'))
                result_value['org_name'].append(school_info.get('ATPT_OFCDC_SC_NM'))
                result_value['org_code'].append(school_info.get('ATPT_OFCDC_SC_CODE'))                
            result_value['valid'] = True
            result_value['message'] = "Success (degraded mode: key missing, limited to 5)" if degraded else "Success to find"
            result_value['school_num'] = len(result_value['school_name'])
        except Exception as e:
            result_value['valid'] = False
            result_value['message'] = f"Error parsing school info: {str(e)}"
            result_value['school_num'] = 0
            result_value['school_name'] = []
            result_value['school_code'] = []
            result_value['org_name'] =  []
            result_value['org_code'] = []
            return result_value                
    else:
        return_message = data.get('RESULT', {}).get('MESSAGE')
        result_value['valid'] = False
        result_value['message'] = return_message
    
    return result_value


def neis_get_school_schedule(school_code, org_code, from_date, to_date):
    degraded = _missing_key_mode()
    result_value = {
                    'valid': False,
                    'message': 'Initialized',
                    'schedule_num': 0, 
                    'event_date': [],
                    'event_name': [],
                    'event_type': [],
                    'event_content': [],
                    'valid_grade': [[] for _ in range(6)],                    
                    }    
    params = {
        'Type': 'json',
        'pIndex': '1',
        'pSize': '100' if not degraded else '5',
        'SD_SCHUL_CODE': school_code,
        'ATPT_OFCDC_SC_CODE': org_code,
        'AA_FROM_YMD': from_date,
        'AA_TO_YMD': to_date    
    }
    if not degraded:
        params['KEY'] = SERVICE_KEY
    response = requests.get(URL_SCHOOL_SCHEDULE, params=params)
    data = response.json()
    return_code = data.get('RESULT', {}).get('CODE')
    if return_code is None:
        try:
            schedule_list = data.get('SchoolSchedule', [])[-1].get('row', [])
            for idx, schedule in enumerate(schedule_list):
                if degraded and idx >= 5:
                    break
                result_value['event_date'].append(schedule.get('AA_YMD'))
                result_value['event_name'].append(schedule.get('EVENT_NM'))
                result_value['event_type'].append(schedule.get('SBTR_DD_SC_NM'))
                result_value['event_content'].append(schedule.get('EVENT_CNTNT'))
                result_value['valid_grade'][0].append(str(schedule.get('ONE_GRADE_EVENT_YN', '')).upper() == 'Y')
                result_value['valid_grade'][1].append(str(schedule.get('TW_GRADE_EVENT_YN', '')).upper() == 'Y')
                result_value['valid_grade'][2].append(str(schedule.get('THREE_GRADE_EVENT_YN', '')).upper() == 'Y')
                result_value['valid_grade'][3].append(str(schedule.get('FR_GRADE_EVENT_YN', '')).upper() == 'Y')
                result_value['valid_grade'][4].append(str(schedule.get('FIV_GRADE_EVENT_YN', '')).upper() == 'Y')
                result_value['valid_grade'][5].append(str(schedule.get('SIX_GRADE_EVENT_YN', '')).upper() == 'Y')            
            result_value['valid'] = True
            result_value['message'] = "Success (degraded mode: key missing, limited to 5)" if degraded else "Success to find"
            result_value['schedule_num'] = len(result_value['event_date'])
        except Exception as e:
            result_value['valid'] = False
            result_value['message'] = f"Error parsing school schedule: {str(e)}"
            result_value['schedule_num'] = 0            
            return result_value                
    else:
        return_message = data.get('RESULT', {}).get('MESSAGE')
        result_value['valid'] = False
        result_value['message'] = return_message
        result_value['schedule_num'] = 0
                
    return result_value

def neis_get_school_schedule_by_name(school_name, from_date, to_date, grade=[1, 2, 3], target_org=None):
    result_value = []
    target_grade = [max(0, min(5, g-1)) for g in grade]
    school_info = neis_get_school_info(school_name)
    if school_info['valid'] and school_info['school_num'] > 0:
        for idx in range(school_info['school_num']):
            # If target_org is None, skip the org_name filter and accept all orgs.
            if target_org is None or school_info['org_name'][idx] == target_org:
                school_code = school_info['school_code'][idx]
                org_code = school_info['org_code'][idx]
                
                schedule_info = neis_get_school_schedule(school_code, org_code, from_date, to_date)
                if schedule_info['valid'] and schedule_info['schedule_num'] > 0:
                    for g in target_grade:
                        for sch_idx in range(schedule_info['schedule_num']):                        
                            if schedule_info['valid_grade'][g][sch_idx]:
                                result_value.append({
                                    'school_name': school_info['school_name'][idx],
                                    'event_date': schedule_info['event_date'][sch_idx],
                                    'event_name': schedule_info['event_name'][sch_idx],
                                    'event_type': schedule_info['event_type'][sch_idx],
                                    'event_content': schedule_info['event_content'][sch_idx],
                                    'grade': g + 1
                                })
                break                

    return result_value

print("test_get_school_info")
print(neis_get_school_info("진관초등학교"))