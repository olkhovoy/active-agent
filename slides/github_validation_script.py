#!/usr/bin/env python3
"""
GitHub Validation Study - Coherence Score Analysis
Анализ успешных и неудачных проектов для валидации CS
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Tuple

class GitHubCoherenceAnalyzer:
    def __init__(self, github_token: str = None):
        self.github_token = github_token
        self.headers = {}
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
        
        # Проекты для анализа
        self.successful_projects = {
            'facebook/react': 'React',
            'vuejs/vue': 'Vue.js', 
            'tensorflow/tensorflow': 'TensorFlow',
            'kubernetes/kubernetes': 'Kubernetes',
            'rust-lang/rust': 'Rust',
            'moby/moby': 'Docker',
            'vercel/next.js': 'Next.js',
            'microsoft/TypeScript': 'TypeScript'
        }
        
        self.failed_projects = {
            'atom/atom': 'Atom',
            'bower/bower': 'Bower',
            'gulpjs/gulp': 'Gulp',
            'meteor/meteor': 'Meteor',
            'Polymer/polymer': 'Polymer',
            'angular/angular.js': 'AngularJS',
            'jashkenas/backbone': 'Backbone.js',
            'jquery/jquery': 'jQuery'
        }
    
    def get_repo_data(self, repo: str, months_back: int = 12) -> Dict:
        """Получить данные репозитория за последние N месяцев"""
        print(f"Собираем данные для {repo}...")
        
        # Базовые данные репозитория
        repo_url = f"https://api.github.com/repos/{repo}"
        response = requests.get(repo_url, headers=self.headers)
        if response.status_code != 200:
            print(f"Ошибка получения данных для {repo}: {response.status_code}")
            return None
        
        repo_data = response.json()
        
        # Коммиты
        commits_url = f"{repo_url}/commits"
        commits = self._get_paginated_data(commits_url, months_back)
        
        # Issues
        issues_url = f"{repo_url}/issues"
        issues = self._get_paginated_data(issues_url, months_back)
        
        # Pull Requests
        prs_url = f"{repo_url}/pulls"
        prs = self._get_paginated_data(prs_url, months_back)
        
        # Releases
        releases_url = f"{repo_url}/releases"
        releases = self._get_paginated_data(releases_url, months_back)
        
        return {
            'repo': repo,
            'name': repo_data.get('name', ''),
            'description': repo_data.get('description', ''),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'created_at': repo_data.get('created_at', ''),
            'commits': commits,
            'issues': issues,
            'prs': prs,
            'releases': releases
        }
    
    def _get_paginated_data(self, url: str, months_back: int) -> List[Dict]:
        """Получить пагинированные данные с ограничением по времени"""
        data = []
        page = 1
        cutoff_date = datetime.now() - timedelta(days=months_back * 30)
        
        while True:
            params = {'page': page, 'per_page': 100}
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                break
                
            page_data = response.json()
            if not page_data:
                break
            
            # Фильтруем по дате
            filtered_data = []
            for item in page_data:
                item_date = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                if item_date >= cutoff_date:
                    filtered_data.append(item)
                else:
                    break
            
            data.extend(filtered_data)
            
            # Если нашли старые данные, останавливаемся
            if len(filtered_data) < len(page_data):
                break
                
            page += 1
            time.sleep(0.1)  # Rate limiting
        
        return data
    
    def calculate_coherence_reduction(self, repo_data: Dict) -> float:
        """Рассчитать coherence_reduction (60% веса)"""
        commits = repo_data.get('commits', [])
        issues = repo_data.get('issues', [])
        
        if not commits:
            return 0.0
        
        # Анализ регулярности коммитов
        commit_dates = [datetime.fromisoformat(c['commit']['author']['date'].replace('Z', '+00:00')) 
                       for c in commits]
        commit_dates.sort()
        
        # Рассчитываем интервалы между коммитами
        intervals = []
        for i in range(1, len(commit_dates)):
            interval = (commit_dates[i] - commit_dates[i-1]).total_seconds() / 3600  # часы
            intervals.append(interval)
        
        if not intervals:
            return 0.0
        
        # Стабильность (меньше вариация = больше когерентность)
        interval_std = np.std(intervals)
        interval_mean = np.mean(intervals)
        stability = 1.0 / (1.0 + interval_std / max(interval_mean, 1.0))
        
        # Время ответа на issues
        issue_response_times = []
        for issue in issues:
            if issue.get('closed_at'):
                created = datetime.fromisoformat(issue['created_at'].replace('Z', '+00:00'))
                closed = datetime.fromisoformat(issue['closed_at'].replace('Z', '+00:00'))
                response_time = (closed - created).total_seconds() / 3600  # часы
                issue_response_times.append(response_time)
        
        if issue_response_times:
            avg_response_time = np.mean(issue_response_times)
            response_quality = 1.0 / (1.0 + avg_response_time / 168.0)  # 1 неделя = 168 часов
        else:
            response_quality = 0.5
        
        return (stability + response_quality) / 2
    
    def calculate_stimulation_contribution(self, repo_data: Dict) -> float:
        """Рассчитать stimulation_contribution (30% веса)"""
        commits = repo_data.get('commits', [])
        description = repo_data.get('description', '')
        
        if not commits:
            return 0.0
        
        # Анализ новизны коммитов
        commit_messages = [c['commit']['message'] for c in commits]
        
        # Подсчет инновационных паттернов в сообщениях коммитов
        innovation_keywords = ['feature', 'add', 'implement', 'new', 'improve', 'enhance', 'optimize']
        innovation_count = sum(1 for msg in commit_messages 
                             if any(keyword in msg.lower() for keyword in innovation_keywords))
        
        innovation_score = min(innovation_count / len(commit_messages), 1.0)
        
        # Релевантность описания
        relevance_keywords = ['framework', 'library', 'tool', 'platform', 'system', 'engine']
        description_relevance = sum(1 for keyword in relevance_keywords 
                                  if keyword in description.lower()) / len(relevance_keywords)
        
        return innovation_score * description_relevance
    
    def calculate_temporal_alignment(self, repo_data: Dict) -> float:
        """Рассчитать temporal_alignment (10% веса)"""
        commits = repo_data.get('commits', [])
        releases = repo_data.get('releases', [])
        
        if not commits:
            return 0.0
        
        # Консистентность разработки
        commit_dates = [datetime.fromisoformat(c['commit']['author']['date'].replace('Z', '+00:00')) 
                       for c in commits]
        commit_dates.sort()
        
        # Рассчитываем равномерность распределения коммитов
        total_days = (commit_dates[-1] - commit_dates[0]).days
        if total_days == 0:
            return 0.0
        
        commits_per_day = len(commits) / total_days
        consistency = min(commits_per_day / 10.0, 1.0)  # Нормализуем к 10 коммитам в день
        
        # Ориентация на будущее (наличие релизов)
        future_orientation = min(len(releases) / 5.0, 1.0)  # Нормализуем к 5 релизам
        
        return (consistency + future_orientation) / 2
    
    def calculate_coherence_score(self, repo_data: Dict) -> float:
        """Рассчитать итоговый Coherence Score"""
        coherence_reduction = self.calculate_coherence_reduction(repo_data)
        stimulation_contribution = self.calculate_stimulation_contribution(repo_data)
        temporal_alignment = self.calculate_temporal_alignment(repo_data)
        
        cs = (0.6 * coherence_reduction + 
              0.3 * stimulation_contribution + 
              0.1 * temporal_alignment)
        
        return cs * 100  # Масштабируем к 0-100
    
    def analyze_projects(self) -> pd.DataFrame:
        """Анализировать все проекты и вернуть результаты"""
        results = []
        
        # Анализируем успешные проекты
        for repo, name in self.successful_projects.items():
            repo_data = self.get_repo_data(repo)
            if repo_data:
                cs = self.calculate_coherence_score(repo_data)
                results.append({
                    'project': name,
                    'repo': repo,
                    'category': 'successful',
                    'coherence_score': cs,
                    'stars': repo_data['stars'],
                    'coherence_reduction': self.calculate_coherence_reduction(repo_data) * 100,
                    'stimulation_contribution': self.calculate_stimulation_contribution(repo_data) * 100,
                    'temporal_alignment': self.calculate_temporal_alignment(repo_data) * 100
                })
        
        # Анализируем неудачные проекты
        for repo, name in self.failed_projects.items():
            repo_data = self.get_repo_data(repo)
            if repo_data:
                cs = self.calculate_coherence_score(repo_data)
                results.append({
                    'project': name,
                    'repo': repo,
                    'category': 'failed',
                    'coherence_score': cs,
                    'stars': repo_data['stars'],
                    'coherence_reduction': self.calculate_coherence_reduction(repo_data) * 100,
                    'stimulation_contribution': self.calculate_stimulation_contribution(repo_data) * 100,
                    'temporal_alignment': self.calculate_temporal_alignment(repo_data) * 100
                })
        
        return pd.DataFrame(results)
    
    def generate_report(self, df: pd.DataFrame) -> str:
        """Сгенерировать отчет по результатам"""
        successful = df[df['category'] == 'successful']
        failed = df[df['category'] == 'failed']
        
        report = f"""
# GitHub Coherence Score Validation Report

## Общая статистика
- Успешных проектов: {len(successful)}
- Неудачных проектов: {len(failed)}
- Средний CS успешных: {successful['coherence_score'].mean():.1f}
- Средний CS неудачных: {failed['coherence_score'].mean():.1f}

## Топ успешных проектов по CS:
{successful.nlargest(5, 'coherence_score')[['project', 'coherence_score']].to_string(index=False)}

## Топ неудачных проектов по CS:
{failed.nsmallest(5, 'coherence_score')[['project', 'coherence_score']].to_string(index=False)}

## Корреляция CS с успехом:
- Разделяющая линия: CS = 60
- Точность предсказания: {(len(successful[successful['coherence_score'] > 60]) + len(failed[failed['coherence_score'] <= 60])) / len(df) * 100:.1f}%

## Детальный анализ компонентов:
{df.groupby('category')[['coherence_reduction', 'stimulation_contribution', 'temporal_alignment']].mean().round(1)}
"""
        return report

def main():
    """Основная функция для запуска анализа"""
    print("GitHub Coherence Score Validation Study")
    print("=" * 50)
    
    # Инициализируем анализатор
    analyzer = GitHubCoherenceAnalyzer()
    
    # Анализируем проекты
    results_df = analyzer.analyze_projects()
    
    # Сохраняем результаты
    results_df.to_csv('github_coherence_results.csv', index=False)
    
    # Генерируем отчет
    report = analyzer.generate_report(results_df)
    
    with open('github_coherence_report.md', 'w') as f:
        f.write(report)
    
    print("\nАнализ завершен!")
    print("Результаты сохранены в:")
    print("- github_coherence_results.csv")
    print("- github_coherence_report.md")
    
    # Показываем краткие результаты
    print("\nКраткие результаты:")
    print(results_df[['project', 'category', 'coherence_score']].round(1))

if __name__ == "__main__":
    main() 