"""
S&OP Capacity Business Case — Mercado Envios
Creado por Gustavo Garcia Carrillo
"""

import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt


# CARGA DE DATOS

ruta = "C:\\Users\\gus30\\Desktop\\MeLi Business Case"

data_1 = pd.read_excel(ruta + '\\' + 'Caso de Negocio - Analista Sr S&OP - MELITLÁN.xlsx', sheet_name="BD_1")
data_1

data_2 = pd.read_excel(ruta + '\\' + 'Caso de Negocio - Analista Sr S&OP - MELITLÁN.xlsx', sheet_name="BD_2", skiprows=1)
data_2


# ============================================================
# PASO 1 — VALIDACION DE DATOS
# ============================================================

print("=== Resumen de los datos ===")
print(f"BD_1: {len(data_1):,} registros")
print(f"BD_2: {len(data_2):,} registros")
print(f"Período: {data_1['CALENDAR_DATE'].min().date()} → {data_1['CALENDAR_DATE'].max().date()}")
print(f"Items únicos: {data_1['ITEM'].nunique()}")
print(f"Almacenes: {', '.join(map(str, data_1['WAREHOUSE_ID'].unique()))}")

# Registros
print(len(data_1))

# Nulos
data_1.isnull().sum()[data_1.isnull().sum() > 0]

# Porcentaje de Nulos respecto al total
nulls = data_1.isnull().sum()[data_1.isnull().sum() > 0]/len(data_1)
nulls

# Duplicados
if data_1.duplicated().any():
    print("El DataFrame contiene registros duplicados.")
else:
    print("El DataFrame contiene registros únicos.")

# ============================================================
# PASO 2 — ESTADISTICAS DESCRIPTIVAS DE CAPACIDAD HISTORICA
# ============================================================

# Calculo de volumen unitario y volumen ocupado por stock
data_1["VOLUMEN_UNITARIO_M3"] = (data_1["ITE_LENGTH (cm)"] * data_1["ITE_WIDTH (cm)"] * data_1["ITE_HEIGHT (cm)"]) / (10**6)
data_1["M3_OCUPADOS"] = data_1["VOLUMEN_UNITARIO_M3"] * data_1["STOCK (Units)"]

# Total de m3 ocupados por dia y almacen
m3_diario = data_1.groupby(["CALENDAR_DATE", "WAREHOUSE_ID"])["M3_OCUPADOS"].sum().reset_index()
m3_diario

# Capacidad promedio
capacidad_promedio_historica = m3_diario.groupby("WAREHOUSE_ID")["M3_OCUPADOS"].mean().reset_index()
capacidad_promedio_historica

# Capacidad maxima
max_ocupacion = m3_diario.groupby("WAREHOUSE_ID")["M3_OCUPADOS"].max().reset_index()
max_ocupacion

print("Capacidad promedio historica (m3):\n", capacidad_promedio_historica)
print("\nMaxima ocupacion historica (m3):\n", max_ocupacion)

# ==========================================================================
# PREGUNTA 1 — ¿Cual es tu capacidad de almacenaje promedio historica en M3?
# ==========================================================================

ocupacion_diaria = data_1.groupby("CALENDAR_DATE")["Ocupacion Almacenamiento (Units)"].first().reset_index()
capacidad_diaria = m3_diario.merge(ocupacion_diaria, on="CALENDAR_DATE")
capacidad_diaria["CAPACIDAD_INSTALADA_M3"] = capacidad_diaria["M3_OCUPADOS"] / capacidad_diaria["Ocupacion Almacenamiento (Units)"]

print(capacidad_diaria["CAPACIDAD_INSTALADA_M3"].describe())
cv_capacidad = capacidad_diaria["CAPACIDAD_INSTALADA_M3"].std() / capacidad_diaria["CAPACIDAD_INSTALADA_M3"].mean() * 100

print(f"Coeficiente de variacion: {cv_capacidad:.1f}% ")


def graficar_capacidad_instalada(capacidad_diaria_df, fecha_col="CALENDAR_DATE", valor_col="CAPACIDAD_INSTALADA_M3"):
    df = capacidad_diaria_df.sort_values(fecha_col)
    print(df)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df[fecha_col], df[valor_col], marker="o", linewidth=1.5, label="Capacidad instalada implicita")
    ax.axhline(df[valor_col].mean(), color="red", linestyle="--", linewidth=1,
               label=f"Promedio: {df[valor_col].mean():,.0f} m3")
    ax.set_title("Capacidad instalada implicita (M3) — MXXX1")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("M3")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


graficar_capacidad_instalada(capacidad_diaria)


# ============================================================
# PASO 4 — PROYECCION DE FALTANTE DE CAPACIDAD (3 ESCENARIOS)
# ============================================================

print("\n" + "=" * 60)
print("PASO 4 — PROYECCION DE FALTANTE DE CAPACIDAD")
print("=" * 60)

# BD_1 (historico) y BD_2 (forecast) son tramos CONSECUTIVOS de la misma serie,
# no se unen por fecha coincidente — se concatenan en una linea de tiempo continua.
stock_hist = data_1.groupby("CALENDAR_DATE")["STOCK (Units)"].sum().reset_index()
stock_hist["PERIODO"] = "Historico"
stock_hist = stock_hist.rename(columns={"CALENDAR_DATE": "FECHA"})
stock_hist

data_2 = data_2.rename(columns={"Dia": "FECHA"})
data_2["PERIODO"] = "Forecast"
data_2

# Factor de densidad (m3 por unidad de stock), derivado del historico
factor_m3_por_unidad = m3_diario["M3_OCUPADOS"].sum() / stock_hist["STOCK (Units)"].sum()
print(f"Factor de densidad: {factor_m3_por_unidad:.5f} m3/unidad")

# Proyeccion de m3 futuros aplicando el factor al forecast de unidades de BD_2
data_2["M3_PROYECTADOS"] = data_2["Stock (Units)"] * factor_m3_por_unidad
data_2

# Borrar
data_2.to_clipboard(index=False)

# Serie continua historico + forecast (para graficar la linea de tiempo completa)
timeline = pd.concat([
    stock_hist.rename(columns={"STOCK (Units)": "STOCK_UNITS"})[["FECHA", "STOCK_UNITS", "PERIODO"]],
    data_2.rename(columns={"Stock (Units)": "STOCK_UNITS"})[["FECHA", "STOCK_UNITS", "PERIODO"]]
], ignore_index=True)

timeline.to_clipboard(index=False)

fig, ax = plt.subplots(figsize=(11, 5))
for periodo, grupo in timeline.groupby("PERIODO"):
    estilo = "-" if periodo == "Historico" else "--"
    ax.plot(grupo["FECHA"], grupo["STOCK_UNITS"], estilo, label=periodo)

ax.set_title("Stock (Units) - historico + forecast, linea de tiempo continua")
ax.set_xlabel("Fecha")
ax.set_ylabel("Stock (Units)")
ax.legend()
ax.grid(alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Borrar
print(timeline.shape)

print(timeline.head())

print(timeline["PERIODO"].unique())

print(timeline.dtypes)

# Faltante bajo 3 escenarios de capacidad instalada (sensibilidad, no un solo numero fijo)
escenarios_capacidad = {
    "Conservador": 3780,
    "Base historico": 3406,
    "Optimista": 4251,
}

for nombre, capacidad in escenarios_capacidad.items():
    data_2[f"FALTANTE_M3_{nombre.replace(' ', '_')}"] = data_2["M3_PROYECTADOS"] - capacidad
    col = f"FALTANTE_M3_{nombre.replace(' ', '_')}"
    en_deficit = data_2["FALTANTE_M3_" + nombre.replace(' ', '_')] > 0
    # inicio de deficit SOSTENIDO (no un cruce momentaneo de un solo dia)
    inicio = None
    for i in range(len(data_2)):
        if en_deficit.iloc[i:].all():
            inicio = data_2["FECHA"].iloc[i].date()
            break
    faltante_final = data_2[col].iloc[-1]
    print(f"Escenario {nombre} ({capacidad} m3) -> "
          f"inicio deficit sostenido: {inicio if inicio else 'sin deficit en el horizonte'} | "
          f"faltante al {data_2['FECHA'].iloc[-1].date()}: {faltante_final:+.0f} m3")

print("\nDetalle diario (escenario base, capacidad = 3780 m3):")
print(data_2[["FECHA", "M3_PROYECTADOS", "FALTANTE_M3_Conservador"]].to_string(index=False))


# ============================================================
# PASO 5 — INSIGHT: VENTA PLANA VS. STOCK CRECIENTE + ROTACION POR CATEGORIA
# ============================================================
print("\n" + "=" * 60)
print("PASO 5 — VENTA VS. STOCK Y ROTACION DE INVENTARIO POR CATEGORIA")
print("=" * 60)

venta_hist_diaria = data_1.groupby("CALENDAR_DATE")["Venta (Units)"].sum().reset_index()
venta_hist_diaria

data_2["Stock (Units)"].iloc[0]

crecimiento_stock_pct = (data_2["Stock (Units)"].iloc[-1] / stock_hist["STOCK (Units)"].iloc[-1] - 1) * 100
crecimiento_stock_pct

print(f"Crecimiento de stock proyectado (extremo a extremo): {crecimiento_stock_pct:+.1f}%")
print("(el forecast de venta se calcula en el Paso 6 — ahi se completa esta comparacion)")

# Rotacion de inventario por categoria: Venta total / Stock promedio del periodo
rotacion = data_1.groupby("ITEM").agg(
    venta_total=("Venta (Units)", "sum"),
    stock_promedio=("STOCK (Units)", "mean")
).reset_index()
rotacion["ROTACION"] = rotacion["venta_total"] / rotacion["stock_promedio"]
rotacion = rotacion.sort_values("ROTACION")
rotacion

print("\nCategorias con MENOR rotacion (mayor riesgo de acumulacion de stock):")
print(rotacion.head(10).to_string(index=False))
rotacion.head(10).to_clipboard(index=False)

print("\nCategorias con MAYOR rotacion:")
print(rotacion.tail(10).to_string(index=False))
rotacion.tail(10).to_clipboard(index=False)

fig, ax = plt.subplots(figsize=(9, 5))
bajo_giro = rotacion.head(10).sort_values("ROTACION")
ax.barh(bajo_giro["ITEM"], bajo_giro["ROTACION"], color="#C24A0E")
ax.set_title("10 categorias con menor rotacion de inventario (mayor riesgo de acumulacion)")
ax.set_xlabel("Rotacion (Venta total / Stock promedio)")
plt.tight_layout()
plt.show()

# Insight: el crecimiento de stock proyectado no se explica por una necesidad general de mas
# espacio -- hay categorias especificas de bajo giro (ej. SOMMIER BASES, DEEP FRYERS) que
# concentran la acumulacion. Vale la pena validar con Compras/Comercial antes de asumir que
# todo el crecimiento de inventario es saludable.


# ============================================================
# PASO 6 — FORECAST DE VENTA: COMPARACION DE 4 MODELOS (BACKTESTING)
# ============================================================
print("\n" + "=" * 60)
print("PASO 6 — FORECAST DE VENTA (BACKTESTING DE 4 MODELOS)")
print("=" * 60)

venta = pd.Series(
    data_1.groupby("CALENDAR_DATE")["Venta (Units)"].sum().values,
    index=pd.date_range("2026-05-27", "2026-06-25", freq="D")
)

TEST_DAYS = 7
train, test = venta[:-TEST_DAYS], venta[-TEST_DAYS:]


def mae(real, pred):
    return np.mean(np.abs(np.array(real) - np.array(pred)))


resultados = {}

# a) Promedio simple
pred_a = [train.mean()] * TEST_DAYS
resultados["Promedio Simple"] = mae(test, pred_a)

# b) Media movil (ventana de 7 dias)
pred_b = [train[-7:].mean()] * TEST_DAYS
resultados["Media Movil (7d)"] = mae(test, pred_b)

# c) Suavizacion exponencial simple
modelo_ses = SimpleExpSmoothing(train).fit(optimized=True)
pred_c = modelo_ses.forecast(TEST_DAYS)
resultados["Suavizacion Exponencial Simple"] = mae(test, pred_c)

# d) Suavizacion exponencial doble (Holt)
modelo_holt = Holt(train).fit(optimized=True)
pred_d = modelo_holt.forecast(TEST_DAYS)
resultados["Suavizacion Exponencial Doble (Holt)"] = mae(test, pred_d)

tabla_error = pd.DataFrame(resultados.items(), columns=["Modelo", "MAE"]).sort_values("MAE")
print(tabla_error.to_string(index=False))
print(f"\nModelo ganador: {tabla_error.iloc[0]['Modelo']} (menor MAE)")



# Forecast final: reentrenar el modelo ganador (SES) con los 30 dias completos
modelo_final = SimpleExpSmoothing(venta).fit(optimized=True)
horizonte = pd.date_range("2026-06-26", "2026-07-25", freq="D")
forecast_final = modelo_final.forecast(len(horizonte))

tabla_forecast = pd.DataFrame({
    "CALENDAR_DATE": horizonte,
    "Venta_Forecast": forecast_final.round(0).astype(int)
})
print(f"\nForecast de venta: {tabla_forecast['Venta_Forecast'].iloc[0]} u/dia constante "
      f"(SES no detecto tendencia en el historico)")

# Cierre del insight del Paso 5: venta plana vs. stock creciente
print(f"\n--- Cierre Paso 5: Venta forecast plana (~{tabla_forecast['Venta_Forecast'].iloc[0]} u/dia) "
      f"vs. Stock forecast {crecimiento_stock_pct:+.1f}% -> divergencia confirmada")


# ============================================================
# PASO 7 — PRODUCTIVIDAD HISTORICA DE PACKING
# ============================================================
print("\n" + "=" * 60)
print("PASO 7 — PRODUCTIVIDAD HISTORICA DE PACKING")
print("=" * 60)

# Metodo A: promedio de razones diarias
diario = data_1.groupby("CALENDAR_DATE").agg(
    venta=("Venta (Units)", "sum"),
    horas=("Horas Hombre Packing", "sum")
).reset_index()

diario.to_clipboard(index=False)

diario["productividad"] = diario["venta"] / diario["horas"]
productividad_metodo_A = diario["productividad"].mean()

productividad_metodo_A

# Metodo B: razon de totales del periodo (metodo reportado, mas robusto)
productividad_metodo_B = data_1["Venta (Units)"].sum() / data_1["Horas Hombre Packing"].sum()
productividad_metodo_B

print(f"Productividad Metodo A (promedio de razones diarias): {productividad_metodo_A:.2f} u/h")
print(f"Productividad Metodo B (razon de totales — reportado): {productividad_metodo_B:.2f} u/h")
print(f"Diferencia entre metodos: {abs(productividad_metodo_A - productividad_metodo_B) / productividad_metodo_B * 100:.1f}% "
      f"-> productividad estable dia a dia")

fig, ax = plt.subplots(figsize=(11, 4))
ax.plot(diario["CALENDAR_DATE"], diario["productividad"], marker="o", color="#2E5090")
ax.axhline(productividad_metodo_B, color="red", linestyle="--", label=f"Metodo B: {productividad_metodo_B:.1f} u/h")
ax.set_title("Productividad diaria de Packing (u/hora-hombre)")
ax.set_xlabel("Fecha")
ax.set_ylabel("u/hora")
ax.legend()
ax.grid(alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# ============================================================
# PASO 8 — STAFFING: HEADCOUNT Y MESAS DE PACKING
# ============================================================
print("\n" + "=" * 60)
print("PASO 8 — STAFFING: HEADCOUNT Y MESAS DE PACKING")
print("=" * 60)

# Clasificacion de tamano (sin dato categorico en el archivo original -> supuesto declarado)
data_1["VOL_M3"] = (data_1["ITE_LENGTH (cm)"] * data_1["ITE_WIDTH (cm)"] * data_1["ITE_HEIGHT (cm)"]) / 1_000_000
UMBRAL_M3 = data_1["VOL_M3"].median()
UMBRAL_M3

data_1["TAMANO"] = data_1["VOL_M3"].apply(lambda v: "Pequeño" if v <= UMBRAL_M3 else "Grande")

mix = data_1.groupby("TAMANO")["Venta (Units)"].sum()
mix.to_clipboard()

mix_pct = mix / mix.sum()

mix_pct

# Pico diario de WK29 (13-19 jul), tomado del forecast SES (plano)
wk29 = pd.date_range("2026-07-13", "2026-07-19", freq="D")
forecast_wk29 = modelo_final.forecast(len(pd.date_range("2026-06-26", "2026-07-19", freq="D")))[-7:]
pico_diario_total = forecast_wk29.max()

pico_pequeno = pico_diario_total * mix_pct["Pequeño"]
pico_grande = pico_diario_total * mix_pct["Grande"]

HORAS_TURNO = 8
throughput_mesa_dia = productividad_metodo_B * HORAS_TURNO

mesas_pequeno = math.ceil(pico_pequeno / throughput_mesa_dia)
mesas_grande = math.ceil(pico_grande / throughput_mesa_dia)

print(f"Umbral de clasificacion (mediana volumen): {UMBRAL_M3:.4f} m3")
print("Mix historico Pequeño/Grande:\n", mix_pct)
print(f"Mesas necesarias -> Pequeño: {mesas_pequeno} | Grande: {mesas_grande}")

# Headcount necesario para WK29
volumen_semanal_wk29 = pico_diario_total * 7
horas_hombre_necesarias = volumen_semanal_wk29 / productividad_metodo_B
HORAS_POR_PERSONA_SEMANA = 48
headcount = math.ceil(horas_hombre_necesarias / HORAS_POR_PERSONA_SEMANA)

print(f"Horas-hombre necesarias en WK29: {horas_hombre_necesarias:.1f}")
print(f"Headcount necesario (WK29): {headcount} personas")


print("\n" + "=" * 60)
print("FIN DEL ANALISIS")
print("=" * 60)
