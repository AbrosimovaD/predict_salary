import requests
import time
import datetime
import statistics as s
import os
from itertools import count
from terminaltables import AsciiTable
from dotenv import load_dotenv


def fetch_all_vacancy_sj(vacancy, tech_params_for_platform, params_to_add=''):
    params, url, headers = tech_params_for_platform['params'],tech_params_for_platform['url'],tech_params_for_platform['headers']
    for page in count(0):
        page_params = {'page': page}
        params.update(**params_to_add,**page_params)
        page_response = requests.get(url, params=params, headers=headers)
        page_response.raise_for_status()
        page_payload = page_response.json()
        yield from page_payload['objects']
        time.sleep(0.25)
        if page_payload['objects'] == []:
            break


def fetch_all_vacancy_hh(vacancy, tech_params_for_platform, params_to_add=''):
    params, url = tech_params_for_platform['params'],tech_params_for_platform['url']
    for page in count(0):
        page_params = {'page': page}
        params.update(**params_to_add,**page_params)
        page_response = requests.get(url, params=params)
        if page_response.status_code == 400:
            break
        page_response.raise_for_status()
        page_payload = page_response.json()
        yield from page_payload['items']
        time.sleep(0.25)
        if page_payload['items'] == []:
            break


def predict_salary(salary_from, salary_to): 
    if salary_from and salary_to:
        salary=(int(salary_from) + int(salary_to))/2
    elif salary_from:
        salary=int(salary_from)*1.2
    elif salary_to:
        salary=int(salary_to)*0.8
    else:
        salary = None
    return salary


def predict_rub_salary_hh(vacancy,tech_params_for_platform):
    vacancy_salaries=[]
    for vacancy in fetch_all_vacancy_hh(vacancy,tech_params_for_platform, {'text': vacancy}):
        if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
            salary=predict_salary(vacancy['salary']['from'], vacancy['salary']['to'])            
        else:
            salary=None
        vacancy_salaries.append(salary)
    return vacancy_salaries


def predict_rub_salary_sj(vacancy,tech_params_for_platform):
    vacancy_salaries=[]
    for vacancy in fetch_all_vacancy_sj(vacancy, tech_params_for_platform, {'keyword': vacancy}):
        salary=predict_salary(vacancy['payment_from'],vacancy['payment_to'])
        vacancy_salaries.append(salary)
    return vacancy_salaries


def get_salary_statictic(platform,tech_params_for_platform):
    top10_langs_list=['Shell', 'Go', 'C', 'C#', 'CSS', 'C++', 'PHP', 'Ruby', 'Python', 'Java', 'JavaScript']
    vacancies_salary_statictic={}
    function_to_calc= globals()[f'predict_rub_salary_{platform}']
    for lang in top10_langs_list:
        prediction_salary = function_to_calc(lang,tech_params_for_platform)
        not_none_prediction_salary = [x for x in prediction_salary if x is not None]
        vacancy_statistic={'vacancies_found': len(prediction_salary),
        'vacancies_processed': len(not_none_prediction_salary),
        'average_salary': int(s.mean(not_none_prediction_salary)) if len(not_none_prediction_salary)!=0 else None}
        vacancies_salary_statictic[lang]=vacancy_statistic
    return vacancies_salary_statictic


def print_statistic_in_table(data_for_print,title):
    headers_for_table = [['Язык программирования' , 'Вакансий найдено' , 'Вакансий обработано' ,'Средняя зарплата' ]]
    for lang, salary_statistic in data_for_print.items():
        row_to_add=[lang, salary_statistic['vacancies_found'] , salary_statistic['vacancies_processed'], salary_statistic['average_salary']]
        headers_for_table.append(row_to_add)
    table = AsciiTable(headers_for_table,title)
    print(table.table)


def main():
    load_dotenv()
    sj_key = os.environ['SUBERJOB_KEY']
    days= 30
    vacancies_per_page = 100
    catalog_for_search=48
    city_for_sj=4
    city_for_hh=1
    platforms={
    'sj':{'url':'https://api.superjob.ru/2.0/vacancies',
    'params':{'town':city_for_sj, 'catalogues':catalog_for_search, 'period':days, 'currency':'rub'},
    'headers':{'X-Api-App-Id': sj_key}},
    'hh':{'url':'https://api.hh.ru/vacancies',
    'params':{'area': city_for_hh, 'period': days, 'per_page':vacancies_per_page},
    'headers': None}
    }
    sj_statistic=get_salary_statictic('sj', platforms['sj'])
    hh_statistic=get_salary_statictic('hh', platforms['hh'])
    print_statistic_in_table(hh_statistic, 'HeadHunter Moscow')
    print_statistic_in_table(sj_statistic,'SuperJob Moscow')


if __name__ == '__main__':
    main()
