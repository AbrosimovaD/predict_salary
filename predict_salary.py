import requests
import time
import datetime
import statistics as s
import os
from itertools import count
from terminaltables import AsciiTable
from dotenv import load_dotenv


def get_tech_params_for_platform(platform):
    load_dotenv()
    sj_key = os.environ['SUBERJOB_KEY']
    platforms={
    'sj':{'url':'https://api.superjob.ru/2.0/vacancies',
    'params':{'town':4, 'catalogues':48, 'period':30, 'currency':'rub'},
    'headers':{'X-Api-App-Id': sj_key}},
    'hh':{'url':'https://api.hh.ru/vacancies',
    'params':{'area': 1, 'period': 30, 'per_page':100},
    'headers': None}
    }
    return platforms[platform]


def fetch_all_vacancy(vacancy, platform, params_to_add=''):
    tech_params_for_platform = get_tech_params_for_platform(platform)
    params, url, headers = tech_params_for_platform['params'],tech_params_for_platform['url'],tech_params_for_platform['headers']
    if params_to_add != '':
        params.update(params_to_add)
    for page in count(0):
        page_params = {'page': page}
        params.update(page_params)
        page_response = requests.get(url, params=params, headers=headers)
        if platform == 'hh' and page_response.status_code == 400:
            break
        page_response.raise_for_status()
        page_payload = page_response.json()
        first_key=list(page_payload.keys())[0]
        yield from page_payload[first_key]
        time.sleep(0.25)
        if page_payload[first_key] == []:
            break


def predict_salary(salary_from, salary_to):
    if (salary_from == None and salary_to == None) or (salary_from == 0 and salary_to == 0):
        salary = None
    elif salary_from == None or int(salary_from) == 0:
        salary=int(salary_to)*0.8
    elif salary_to == None or int(salary_to) == 0:
        salary=int(salary_from)*1.2
    else:
        salary=(int(salary_from) + int(salary_to))/2
    return salary


def predict_rub_salary_hh(vacancy):
    vacancy_salary=[]
    for vacancy in fetch_all_vacancy(vacancy, 'hh', {'text': vacancy}):
        if vacancy['salary'] != None and vacancy['salary']['currency'] == 'RUR':
            salary=predict_salary(vacancy['salary']['from'], vacancy['salary']['to'])
        else:
            salary=None
        vacancy_salary.append(salary)
    return vacancy_salary


def predict_rub_salary_sj(vacancy):
    vacancy_salary=[]
    for vacancy in fetch_all_vacancy(vacancy, 'sj', {'keyword': vacancy}):
        salary=predict_salary(vacancy['payment_from'],vacancy['payment_to'])
        vacancy_salary.append(salary)
    return vacancy_salary


def get_salary_statictic(platform):
    top10_langs_list=['Shell', 'Go', 'C', 'C#', 'CSS', 'C++', 'PHP', 'Ruby', 'Python', 'Java', 'JavaScript']
    vacancies_salary_statictic={}
    function_to_calc= globals()[f'predict_rub_salary_{platform}']
    for lang in top10_langs_list:
        prediction_salary = function_to_calc(lang)
        not_none_prediction_salary = [x for x in prediction_salary if x is not None]
        vacancy_statistic={'vacancies_found': len(prediction_salary),
        'vacancies_processed': len(not_none_prediction_salary),
        'average_salary': int(s.mean(not_none_prediction_salary)) if len(not_none_prediction_salary)!=0 else None}
        vacancies_salary_statictic[lang]=vacancy_statistic
    return vacancies_salary_statictic


def get_salary_statictic_hh():
    return get_salary_statictic('hh')


def get_salary_statictic_sj():
    return get_salary_statictic('sj')


def print_statistic_in_table(data_for_print,title):
    table_data = [['Язык программирования' , 'Вакансий найдено' , 'Вакансий обработано' ,'Средняя зарплата' ]]
    for lang, salary_statistic in data_for_print.items():
        row_to_add=[lang, salary_statistic['vacancies_found'] , salary_statistic['vacancies_processed'], salary_statistic['average_salary']]
        table_data.append(row_to_add)
    table = AsciiTable(table_data,title)
    print(table.table)


def main():
    sj_data=get_salary_statictic_sj()
    hh_data=get_salary_statictic_hh()
    print_statistic_in_table(hh_data, 'HeadHunter Moscow')
    print_statistic_in_table(sj_data,'SuperJob Moscow')


if __name__ == '__main__':
    main()
