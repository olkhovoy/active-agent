# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import List, Dict
import yaml
import os

@dataclass
class UserProfile:
    """
    Профиль активного агента для персонализации оценки токенов.
    """
    # Основные интересы пользователя в крипто-сфере
    interests: List[str] = field(default_factory=lambda: ["DeFi", "Infrastructure", "Layer 2"])
    
    # Уровень толерантности к риску
    # low: предпочитает устоявшиеся токены с высокой капитализацией
    # medium: готов к риску ради более высокой доходности, но в разумных пределах
    # high: ищет высокорисковые токены с потенциалом экспоненциального роста
    risk_tolerance: str = "medium"
    
    # Предпочитаемые блокчейны (пока только ethereum)
    preferred_chains: List[str] = field(default_factory=lambda: ["ethereum"])
    
    # Минимальная сумма для рассмотрения ликвидности в USD
    min_liquidity_usd: int = 100000
    
    # "Черный список" токенов или категорий, которые следует избегать
    excluded_categories: List[str] = field(default_factory=lambda: ["Meme Coin"])
    excluded_tokens: List[str] = field(default_factory=list) # по символу или адресу

    def to_dict(self) -> Dict:
        """Преобразование профиля в словарь."""
        return {
            "interests": self.interests,
            "risk_tolerance": self.risk_tolerance,
            "preferred_chains": self.preferred_chains,
            "min_liquidity_usd": self.min_liquidity_usd,
            "excluded_categories": self.excluded_categories,
            "excluded_tokens": self.excluded_tokens,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'UserProfile':
        """Создание профиля из словаря."""
        return cls(**data)


class UserProfileManager:
    """
    Управляет сохранением и загрузкой профиля пользователя.
    """
    def __init__(self, file_path: str = "user_profile.yaml"):
        self.file_path = file_path

    def save_profile(self, profile: UserProfile):
        """Сохраняет профиль пользователя в YAML файл."""
        with open(self.file_path, 'w', encoding='utf-8') as f:
            yaml.dump(profile.to_dict(), f, allow_unicode=True, default_flow_style=False)
        print(f"Профиль пользователя сохранен в {self.file_path}")

    def load_profile(self) -> UserProfile:
        """
        Загружает профиль пользователя из YAML файла.
        Если файл не найден, создает и сохраняет профиль по умолчанию.
        """
        if not os.path.exists(self.file_path):
            print(f"Файл профиля не найден. Создаю профиль по умолчанию в {self.file_path}")
            default_profile = UserProfile()
            self.save_profile(default_profile)
            return default_profile
        
        with open(self.file_path, 'r', encoding='utf-8') as f:
            profile_data = yaml.safe_load(f)
            if profile_data:
                return UserProfile.from_dict(profile_data)
            else:
                # Если файл пуст, создаем профиль по умолчанию
                default_profile = UserProfile()
                self.save_profile(default_profile)
                return default_profile

# Пример использования
if __name__ == "__main__":
    manager = UserProfileManager()
    
    # Загрузка профиля (или создание нового)
    user_profile = manager.load_profile()
    
    print("--- Текущий профиль пользователя ---")
    print(yaml.dump(user_profile.to_dict(), allow_unicode=True))
    
    # Изменение профиля
    user_profile.risk_tolerance = "high"
    user_profile.interests.append("GameFi")
    user_profile.excluded_categories.append("Gambling")
    
    # Сохранение изменений
    manager.save_profile(user_profile)
    
    print("\n--- Обновленный профиль пользователя ---")
    updated_profile = manager.load_profile()
    print(yaml.dump(updated_profile.to_dict(), allow_unicode=True))

    # Демонстрация создания профиля с нуля
    if os.path.exists("temp_profile.yaml"):
        os.remove("temp_profile.yaml")
        
    temp_manager = UserProfileManager("temp_profile.yaml")
    new_profile = temp_manager.load_profile()
    print("\n--- Профиль, созданный с нуля ---")
    print(yaml.dump(new_profile.to_dict(), allow_unicode=True))
    os.remove("temp_profile.yaml")
