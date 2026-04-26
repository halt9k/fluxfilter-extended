import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter1d

# ============================================================
# 1. ВАШИ РЕАЛЬНЫЕ ДАННЫЕ
# ============================================================

df = pd.read_csv('output/REddyProc_tv_fy4_3m_2025.txt', delimiter=' ')

# Удаляем первую строку, которая содержит единицы измерения и нечисловые значения
df = df.iloc[1:].copy()


df['Ustar'] = pd.to_numeric(df['Ustar'], errors='coerce')
df['NEE'] = pd.to_numeric(df['NEE'], errors='coerce')

# Обработка пропущенных значений (-9999)
# Заменяем -9999 на NaN в столбцах 'Ustar' и 'NEE' (этот шаг также покроет, если -9999 был числом)
df['Ustar'] = df['Ustar'].replace(-9999, np.nan)
df['NEE'] = df['NEE'].replace(-9999, np.nan)

# Удаляем строки, содержащие NaN в этих столбцах
df.dropna(subset=['Ustar', 'NEE'], inplace=True)

# Проверка загрузки данных
print("Первые 5 строк загруженных данных (после обработки пропусков):")
print(df.head())
print("\n")

# Берём значения Ustar и NEE (только ночные часы или весь период — как у вас принято)
u_star_all = df['Ustar'].values
nee_all = df['NEE'].values


# ============================================================
# 2. ФУНКЦИЯ ПОИСКА ПОРОГА MOVING POINT
# ============================================================

def find_u_star_threshold(u_star, nee, n_bins=30, smooth_window=5):
    """
    Moving point метод для нахождения порога u*.
    """
    # Сортируем по u*
    idx = np.argsort(u_star)
    u_sorted = u_star[idx]
    nee_sorted = nee[idx]
    
    # Биннинг
    bins = np.percentile(u_sorted, np.linspace(0, 100, n_bins + 1))
    bin_centers = (bins[:-1] + bins[1:]) / 2
    nee_means = []
    
    for i in range(n_bins):
        mask = (u_sorted >= bins[i]) & (u_sorted < bins[i + 1])
        if np.any(mask):
            nee_means.append(np.mean(nee_sorted[mask]))
        else:
            nee_means.append(np.nan)
    
    nee_means = np.array(nee_means)
    bin_centers = bin_centers[~np.isnan(nee_means)]
    nee_means = nee_means[~np.isnan(nee_means)]
    
    if len(nee_means) < 5:
        return np.median(u_star)
    
    # Сглаживание
    if len(nee_means) > smooth_window:
        from scipy.ndimage import uniform_filter1d
        nee_smooth = uniform_filter1d(nee_means, size=smooth_window, mode='nearest')
        derivative = np.gradient(nee_smooth, bin_centers)
        deriv_smooth = uniform_filter1d(np.abs(derivative), size=smooth_window, mode='nearest')
    else:
        derivative = np.gradient(nee_means, bin_centers)
        deriv_smooth = np.abs(derivative)
    
    # Порог = точка минимальной производной (начало плато)
    min_idx = np.argmin(deriv_smooth)
    threshold = bin_centers[min_idx]
    
    return threshold


# ============================================================
# 3. БУТСТРАППИНГ: 200 ИТЕРАЦИЙ
# ============================================================

def bootstrap_thresholds(u_star, nee, n_bootstrap=200, n_bins=30):
    """
    Бутстраппинг для получения распределения порога.
    Возвращает массив из n_bootstrap значений.
    """
    n = len(u_star)
    thresholds = []
    
    print(f"Запуск бутстраппинга ({n_bootstrap} итераций)...")
    
    for i in range(n_bootstrap):
        # Выборка с возвращением
        idx = np.random.choice(n, size=n, replace=True)
        u_boot = u_star[idx]
        nee_boot = nee[idx]
        
        try:
            th = find_u_star_threshold(u_boot, nee_boot, n_bins=n_bins)
            thresholds.append(th)
        except:
            thresholds.append(np.median(u_boot))
        
        if (i + 1) % 50 == 0:
            print(f"  Выполнено {i + 1} из {n_bootstrap}")
    
    return np.array(thresholds)


# Запускаем
bootstrap_thresholds_values = bootstrap_thresholds(u_star_all, nee_all, n_bootstrap=200, n_bins=30)

# ============================================================
# 4. КВАНТИЛИ И ВЕСА
# ============================================================

# 5 квантилей
quantiles = [0.05, 0.25, 0.50, 0.75, 0.95]
threshold_quantiles = np.percentile(bootstrap_thresholds_values, [q * 100 for q in quantiles])

# Вычисляем веса: доля бутстреп-оценок между квантилями
sorted_th = np.sort(bootstrap_thresholds_values)
n_boot = len(bootstrap_thresholds_values)

# Границы зон (середины между квантилями)
boundaries = [np.min(sorted_th)]
for i in range(len(threshold_quantiles) - 1):
    boundaries.append((threshold_quantiles[i] + threshold_quantiles[i + 1]) / 2)
boundaries.append(np.max(sorted_th))

# Веса = доля точек в каждой зоне
weights = []
for i in range(len(threshold_quantiles)):
    # Учитываем, что последняя граница должна быть включена для последнего интервала
    if i == len(threshold_quantiles) - 1:
        count = np.sum((sorted_th >= boundaries[i]) & (sorted_th <= boundaries[i + 1]))
    else:
        count = np.sum((sorted_th >= boundaries[i]) & (sorted_th < boundaries[i + 1]))
    weights.append(count / n_boot)

# ============================================================
# 5. РЕЗУЛЬТАТЫ
# ============================================================

print("\n=== РЕЗУЛЬТАТЫ БУТСТРАППИНГА ===")
print(f"Всего бутстреп-итераций: {n_boot}")
print(f"\n5 порогов (квантили распределения):")
for q, th in zip(quantiles, threshold_quantiles):
    print(f"  {q * 100:.0f}%: {th:.4f} м/с")

print(f"\nВеса порогов (из бутстреп-распределения):")
for q, th, w in zip(quantiles, threshold_quantiles, weights):
    print(f"  {q * 100:.0f}% ({th:.4f} м/с): вес = {w:.4f} ({w * 100:.1f}%)")

print(f"\nСумма весов: {sum(weights):.4f}")


results = pd.DataFrame({
    'quantile': quantiles,
    'threshold_ms': threshold_quantiles,
    'weight': weights
})
results.to_csv('bootstrap_thresholds_with_weights.csv', index=False)
print("\nРезультаты сохранены в 'bootstrap_thresholds_with_weights.csv'")


print("\nПервые 5 строк сохраненных результатов:")
saved_results = pd.read_csv('bootstrap_thresholds_with_weights.csv')
print(saved_results.head())
