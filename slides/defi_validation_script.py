#!/usr/bin/env python3
"""
DeFi Validation Study - Coherence Score Analysis
Анализ успешных и неудачных DeFi проектов для валидации CS
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Tuple

class DeFiCoherenceAnalyzer:
    def __init__(self, github_token: str = None, etherscan_api_key: str = None):
        self.github_token = github_token
        self.etherscan_api_key = etherscan_api_key
        self.headers = {}
        if github_token:
            self.headers['Authorization'] = f'token {github_token}'
        
        # Успешные DeFi проекты
        self.successful_projects = {
            'Uniswap/uniswap-v3-core': 'Uniswap',
            'aave/aave-v3-core': 'Aave',
            'compound-finance/compound-protocol': 'Compound',
            'makerdao/dss': 'MakerDAO',
            'curvefi/curve-contract': 'Curve Finance',
            'Synthetixio/synthetix': 'Synthetix',
            'yearn/yearn-vaults': 'Yearn Finance',
            'balancer-labs/balancer-v2-monorepo': 'Balancer'
        }
        
        # Неудачные DeFi проекты
        self.failed_projects = {
            'terra-money/core': 'Terra/LUNA',
            'anchor-protocol/anchor': 'Anchor Protocol',
            'celsius-network/celsius-contracts': 'Celsius',
            'blockfi/blockfi-api': 'BlockFi',
            'voyager-digital/voyager-app': 'Voyager Digital',
            'three-arrows-capital/defi-protocols': 'Three Arrows Capital',
            'ftx/ftx-api': 'FTX',
            'alameda-research/alameda-trading': 'Alameda Research'
        }
    
    def get_github_data(self, repo: str, months_back: int = 12) -> Dict:
        """Получить данные GitHub репозитория"""
        print(f"Собираем GitHub данные для {repo}...")
        
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
        
        # Security advisories
        security_url = f"{repo_url}/security-advisories"
        security = self._get_paginated_data(security_url, months_back)
        
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
            'releases': releases,
            'security': security
        }
    
    def get_defi_pulse_data(self, project_name: str) -> Dict:
        """Получить данные DeFi Pulse (симуляция)"""
        # В реальности здесь был бы API вызов к DeFi Pulse
        # Пока используем симулированные данные
        
        defi_data = {
            'Uniswap': {'tvl': 3200000000, 'volume_24h': 500000000, 'users': 500000},
            'Aave': {'tvl': 6800000000, 'volume_24h': 200000000, 'users': 300000},
            'Compound': {'tvl': 2100000000, 'volume_24h': 100000000, 'users': 200000},
            'MakerDAO': {'tvl': 5400000000, 'volume_24h': 150000000, 'users': 250000},
            'Curve Finance': {'tvl': 2800000000, 'volume_24h': 300000000, 'users': 150000},
            'Synthetix': {'tvl': 400000000, 'volume_24h': 50000000, 'users': 80000},
            'Yearn Finance': {'tvl': 800000000, 'volume_24h': 30000000, 'users': 60000},
            'Balancer': {'tvl': 200000000, 'volume_24h': 20000000, 'users': 40000},
            'Terra/LUNA': {'tvl': 0, 'volume_24h': 0, 'users': 0},
            'Anchor Protocol': {'tvl': 0, 'volume_24h': 0, 'users': 0},
            'Celsius': {'tvl': 0, 'volume_24h': 0, 'users': 0},
            'BlockFi': {'tvl': 0, 'volume_24h': 0, 'users': 0},
            'Voyager Digital': {'tvl': 0, 'volume_24h': 0, 'users': 0},
            'Three Arrows Capital': {'tvl': 0, 'volume_24h': 0, 'users': 0},
            'FTX': {'tvl': 0, 'volume_24h': 0, 'users': 0},
            'Alameda Research': {'tvl': 0, 'volume_24h': 0, 'users': 0}
        }
        
        return defi_data.get(project_name, {'tvl': 0, 'volume_24h': 0, 'users': 0})
    
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
    
    def calculate_coherence_reduction(self, github_data: Dict, defi_data: Dict) -> float:
        """Рассчитать coherence_reduction (60% веса) для DeFi проекта"""
        commits = github_data.get('commits', [])
        issues = github_data.get('issues', [])
        security = github_data.get('security', [])
        
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
        
        # Стабильность разработки
        interval_std = np.std(intervals)
        interval_mean = np.mean(intervals)
        dev_stability = 1.0 / (1.0 + interval_std / max(interval_mean, 1.0))
        
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
        
        # Безопасность (отсутствие security advisories = лучше)
        security_score = 1.0 / (1.0 + len(security))
        
        # TVL стабильность (для успешных проектов)
        tvl_score = min(defi_data.get('tvl', 0) / 1000000000, 1.0)  # Нормализуем к 1B
        
        return (dev_stability + response_quality + security_score + tvl_score) / 4
    
    def calculate_stimulation_contribution(self, github_data: Dict, defi_data: Dict) -> float:
        """Рассчитать stimulation_contribution (30% веса) для DeFi проекта"""
        commits = github_data.get('commits', [])
        description = github_data.get('description', '')
        
        if not commits:
            return 0.0
        
        # Анализ новизны коммитов
        commit_messages = [c['commit']['message'] for c in commits]
        
        # Подсчет DeFi-специфичных инновационных паттернов
        defi_innovation_keywords = [
            'amm', 'liquidity', 'yield', 'lending', 'borrowing', 'swap', 'pool',
            'governance', 'dao', 'staking', 'rewards', 'flash', 'arbitrage',
            'oracle', 'price', 'feed', 'collateral', 'debt', 'mint', 'burn'
        ]
        
        innovation_count = sum(1 for msg in commit_messages 
                             if any(keyword in msg.lower() for keyword in defi_innovation_keywords))
        
        innovation_score = min(innovation_count / len(commit_messages), 1.0)
        
        # Релевантность описания для DeFi
        defi_relevance_keywords = ['defi', 'decentralized', 'finance', 'protocol', 'amm', 'lending', 'yield']
        description_relevance = sum(1 for keyword in defi_relevance_keywords 
                                  if keyword in description.lower()) / len(defi_relevance_keywords)
        
        # Объем транзакций как показатель активности
        volume_score = min(defi_data.get('volume_24h', 0) / 100000000, 1.0)  # Нормализуем к 100M
        
        return (innovation_score + description_relevance + volume_score) / 3
    
    def calculate_temporal_alignment(self, github_data: Dict, defi_data: Dict) -> float:
        """Рассчитать temporal_alignment (10% веса) для DeFi проекта"""
        commits = github_data.get('commits', [])
        releases = github_data.get('releases', [])
        
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
        
        # Количество пользователей как показатель adoption
        users_score = min(defi_data.get('users', 0) / 100000, 1.0)  # Нормализуем к 100k пользователей
        
        return (consistency + future_orientation + users_score) / 3
    
    def calculate_coherence_score(self, github_data: Dict, defi_data: Dict) -> float:
        """Рассчитать итоговый Coherence Score для DeFi проекта"""
        coherence_reduction = self.calculate_coherence_reduction(github_data, defi_data)
        stimulation_contribution = self.calculate_stimulation_contribution(github_data, defi_data)
        temporal_alignment = self.calculate_temporal_alignment(github_data, defi_data)
        
        cs = (0.6 * coherence_reduction + 
              0.3 * stimulation_contribution + 
              0.1 * temporal_alignment)
        
        return cs * 100  # Масштабируем к 0-100
    
    def analyze_projects(self) -> pd.DataFrame:
        """Анализировать все DeFi проекты и вернуть результаты"""
        results = []
        
        # Анализируем успешные проекты
        for repo, name in self.successful_projects.items():
            github_data = self.get_github_data(repo)
            if github_data:
                defi_data = self.get_defi_pulse_data(name)
                cs = self.calculate_coherence_score(github_data, defi_data)
                results.append({
                    'project': name,
                    'repo': repo,
                    'category': 'successful',
                    'coherence_score': cs,
                    'tvl': defi_data.get('tvl', 0),
                    'volume_24h': defi_data.get('volume_24h', 0),
                    'users': defi_data.get('users', 0),
                    'coherence_reduction': self.calculate_coherence_reduction(github_data, defi_data) * 100,
                    'stimulation_contribution': self.calculate_stimulation_contribution(github_data, defi_data) * 100,
                    'temporal_alignment': self.calculate_temporal_alignment(github_data, defi_data) * 100
                })
        
        # Анализируем неудачные проекты
        for repo, name in self.failed_projects.items():
            github_data = self.get_github_data(repo)
            if github_data:
                defi_data = self.get_defi_pulse_data(name)
                cs = self.calculate_coherence_score(github_data, defi_data)
                results.append({
                    'project': name,
                    'repo': repo,
                    'category': 'failed',
                    'coherence_score': cs,
                    'tvl': defi_data.get('tvl', 0),
                    'volume_24h': defi_data.get('volume_24h', 0),
                    'users': defi_data.get('users', 0),
                    'coherence_reduction': self.calculate_coherence_reduction(github_data, defi_data) * 100,
                    'stimulation_contribution': self.calculate_stimulation_contribution(github_data, defi_data) * 100,
                    'temporal_alignment': self.calculate_temporal_alignment(github_data, defi_data) * 100
                })
        
        return pd.DataFrame(results)
    
    def generate_report(self, df: pd.DataFrame) -> str:
        """Сгенерировать отчет по результатам DeFi анализа"""
        successful = df[df['category'] == 'successful']
        failed = df[df['category'] == 'failed']
        
        report = f"""
# DeFi Coherence Score Validation Report

## Общая статистика
- Успешных DeFi проектов: {len(successful)}
- Неудачных DeFi проектов: {len(failed)}
- Средний CS успешных: {successful['coherence_score'].mean():.1f}
- Средний CS неудачных: {failed['coherence_score'].mean():.1f}

## Топ успешных DeFi проектов по CS:
{successful.nlargest(5, 'coherence_score')[['project', 'coherence_score', 'tvl']].to_string(index=False)}

## Топ неудачных DeFi проектов по CS:
{failed.nsmallest(5, 'coherence_score')[['project', 'coherence_score', 'tvl']].to_string(index=False)}

## Корреляция CS с успехом:
- Разделяющая линия: CS = 60
- Точность предсказания: {(len(successful[successful['coherence_score'] > 60]) + len(failed[failed['coherence_score'] <= 60])) / len(df) * 100:.1f}%

## Детальный анализ компонентов:
{df.groupby('category')[['coherence_reduction', 'stimulation_contribution', 'temporal_alignment']].mean().round(1)}

## TVL vs Coherence Score:
- Корреляция TVL с CS: {df['tvl'].corr(df['coherence_score']):.3f}
- Средний TVL успешных: ${successful['tvl'].mean()/1000000:.1f}M
- Средний TVL неудачных: ${failed['tvl'].mean()/1000000:.1f}M
"""
        return report

def main():
    """Основная функция для запуска DeFi анализа"""
    print("DeFi Coherence Score Validation Study")
    print("=" * 50)
    
    # Инициализируем анализатор
    analyzer = DeFiCoherenceAnalyzer()
    
    # Анализируем проекты
    results_df = analyzer.analyze_projects()
    
    # Сохраняем результаты
    results_df.to_csv('defi_coherence_results.csv', index=False)
    
    # Генерируем отчет
    report = analyzer.generate_report(results_df)
    
    with open('defi_coherence_report.md', 'w') as f:
        f.write(report)
    
    print("\nDeFi анализ завершен!")
    print("Результаты сохранены в:")
    print("- defi_coherence_results.csv")
    print("- defi_coherence_report.md")
    
    # Показываем краткие результаты
    print("\nКраткие результаты:")
    print(results_df[['project', 'category', 'coherence_score', 'tvl']].round(1))

if __name__ == "__main__":
    main() 