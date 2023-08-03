import requests
import time
import datetime
import statistics as s
import os
from itertools import count
from terminaltables import AsciiTable
from dotenv import load_dotenv


def fetch_all_vacancy_sj(vacancy, params, url, headers):
    params['keyword'] = vacancy
    for page in count(0):
        params['page'] = page
        page_response = requests.get(url, params=params, headers=headers)
        page_response.raise_for_status()
        page_payload = page_response.json()
        yield from page_payload['objects']
        time.sleep(0.25)
        if not page_payload['objects']:
            break


def fetch_all_vacancy_hh(vacancy, params, url):
    params['text'] = vacancy
    for page in count(0):
        params['page'] = page
        page_response = requests.get(url, params=params)
        if page_response.status_code == 400:
            break
        page_response.raise_for_status()
        page_payload = page_response.json()
        yield from page_payload['items']
        time.sleep(0.25)
        if not page_payload['items']:
            break


def predict_salary(salary_from, salary_to):
    if salary_from and salary_to:
        salary = (int(salary_from) + int(salary_to))/2
    elif salary_from:
        salary = int(salary_from)*1.2
    elif salary_to:
        salary = int(salary_to)*0.8
    else:
        salary = None
    return salary


def predict_rub_salaries_hh(vacancy, params, url):
    vacancy_salaries = []
    for vacancy in fetch_all_vacancy_hh(vacancy, params, url):
        if vacancy['salary'] and vacancy['salary']['currency'] == 'RUR':
            salary = predict_salary(vacancy['salary']['from'], vacancy['salary']['to'])            
        else:
            salary = None
        vacancy_salaries.append(salary)
    return vacancy_salaries


def predict_rub_salaries_sj(vacancy, params, url, headers):
    vacancy_salaries = []
    for vacancy in fetch_all_vacancy_sj(vacancy, params, url, headers):
        salary = predict_salary(vacancy['payment_from'], vacancy['payment_to'])
        vacancy_salaries.append(salary)
    return vacancy_salaries


def get_salary_statictic_hh(params, url):
    top_langs = ['Shell', 'Go', 'C', 'C#', 'CSS', 'C++', 'PHP', 'Ruby', 'Python', 'Java', 'JavaScript']
    vacancies_salary_statictic = {}
    for lang in top_langs:
        prediction_salaries = predict_rub_salaries_hh(lang, params, url)
        not_none_prediction_salaries = [x for x in prediction_salaries if x]
        vacancy_statistic = {'vacancies_found': len(prediction_salaries),
                             'vacancies_processed': len(not_none_prediction_salaries),
                             'average_salary': int(s.mean(not_none_prediction_salaries)) if len(not_none_prediction_salaries) else None}
        vacancies_salary_statictic[lang] = vacancy_statistic
    return vacancies_salary_statictic


def get_salary_statictic_sj(params, url, headers):
    top_langs = ['Shell', 'Go', 'C', 'C#', 'CSS', 'C++', 'PHP', 'Ruby', 'Python', 'Java', 'JavaScript']
    vacancies_salary_statictic = {}
    for lang in top_langs:
        prediction_salaries = predict_rub_salaries_sj(lang, params, url, headers)
        not_none_prediction_salaries = [x for x in prediction_salaries if x]
        vacancy_statistic = {'vacancies_found': len(prediction_salaries),
                             'vacancies_processed': len(not_none_prediction_salaries),
                             'average_salary': int(s.mean(not_none_prediction_salaries)) if len(not_none_prediction_salaries) else None}
        vacancies_salary_statictic[lang] = vacancy_statistic
    return vacancies_salary_statictic


def print_statistic_in_table(vacancies_statistic, title):
    headers_for_table = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for lang, salary_statistic in vacancies_statistic.items():
        row_to_add = [lang, salary_statistic['vacancies_found'], salary_statistic['vacancies_processed'], salary_statistic['average_salary']]
        headers_for_table.append(row_to_add)
    table = AsciiTable(headers_for_table, title)
    print(table.table)


def main():
    load_dotenv()
    sj_key = os.environ['SUBERJOB_KEY']
    days = 30
    vacancies_per_page = 100
    catalog_for_search = 48
    city_for_sj = 4
    city_for_hh = 1
    sj_url = 'https://api.superjob.ru/2.0/vacancies'
    sj_params = {'town': city_for_sj, 'catalogues': catalog_for_search, 'period': days, 'currency': 'rub'}
    sj_headers = {'X-Api-App-Id': sj_key}
    hh_url = 'https://api.hh.ru/vacancies'
    hh_params = {'area': city_for_hh, 'period': days, 'per_page': vacancies_per_page}
    sj_statistic = get_salary_statictic_sj(sj_params, sj_url, sj_headers)
    hh_statistic = get_salary_statictic_hh(hh_params, hh_url)
    print_statistic_in_table(hh_statistic, 'HeadHunter Moscow')
    print_statistic_in_table(sj_statistic, 'SuperJob Moscow')


if __name__ == '__main__':
    main()
