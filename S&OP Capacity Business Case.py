import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

# Leer archivo Excel
ruta = "C:\\Users\\gus30\\Desktop\\MeLi Business Case"

# Tablas de datos
data_1 = pd.read_excel(ruta + '\\' + 'Caso de Negocio - Analista Sr S&OP - MELITLÁN.xlsx',sheet_name="BD_1")
data_2 = pd.read_excel(ruta + '\\' + 'Caso de Negocio - Analista Sr S&OP - MELITLÁN.xlsx',sheet_name="BD_2", skiprows=1)

# Validacion de Datos
data_1.head()
data_2.head()

# 1. Volumen unitario
data_1["VOLUMEN_UNITARIO_M3"] = (data_1["ITE_LENGTH (cm)"] * data_1["ITE_WIDTH (cm)"] * data_1["ITE_HEIGHT (cm)"]) / 1_000_000

# 2. Volumen ocupado por stock
data_1["M3_OCUPADOS"] = (data_1["VOLUMEN_UNITARIO_M3"] * data_1["STOCK (Units)"])

data_1

# 3. Total por día y almacén
m3_diario = (data_1.groupby(["CALENDAR_DATE", "WAREHOUSE_ID"])["M3_OCUPADOS"].sum().reset_index())
print(m3_diario)

m3_diario.to_clipboard(index=False)

# Ocupacion promedio histórica
capacidad_promedio_historica = (m3_diario.groupby("WAREHOUSE_ID")["M3_OCUPADOS"].mean().reset_index())
capacidad_promedio_historica

# 4. Cruce con la ocupación % para obtener la capacidad instalada implícita (esto también ya lo hiciste)
occ = data_1.groupby("CALENDAR_DATE")["Ocupacion Almacenamiento (Units)"].first().reset_index()
occ
occ.to_clipboard(index=False)

check = m3_diario.merge(occ, on="CALENDAR_DATE")
check.to_clipboard(index=False)

check["CAPACIDAD_INSTALADA_M3"] = check["M3_OCUPADOS"] / check["Ocupacion Almacenamiento (Units)"]
check

print(check["CAPACIDAD_INSTALADA_M3"].describe())



# 5. Definir la función (una sola vez, esto va antes de usarla)
def graficar_capacidad_instalada(check_df, fecha_col="CALENDAR_DATE", valor_col="CAPACIDAD_INSTALADA_M3"):
    df = check_df.sort_values(fecha_col)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.plot(df[fecha_col], df[valor_col], marker="o", linewidth=1.5, label="Capacidad instalada implícita")
    ax.axhline(df[valor_col].mean(), color="red", linestyle="--", linewidth=1, label=f"Promedio: {df[valor_col].mean():,.0f} m³")
    ax.set_title("Capacidad instalada implícita (M3) — MXXX1")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("M3")
    ax.legend()
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# 6. Llamarla, pasándole TU dataframe "check"
graficar_capacidad_instalada(check)





# 1. idKey de periodo en cada base
stock_hist = data_1.groupby("CALENDAR_DATE")["STOCK (Units)"].sum().reset_index()
stock_hist["PERIODO"] = "Historico"
stock_hist = stock_hist.rename(columns={"CALENDAR_DATE": "FECHA"})


stock_hist

data_2 = data_2.rename(columns={"Dia": "FECHA"})
data_2["PERIODO"] = "Forecast"

# 2. Factor de densidad: m3 promedio ocupado por unidad de stock (histórico)
factor_m3_por_unidad = m3_diario["M3_OCUPADOS"].sum() / stock_hist["STOCK (Units)"].sum()
print("Factor m3/unidad:", factor_m3_por_unidad)

# 3. Proyectar m3 futuros aplicando el factor al forecast de unidades
data_2["M3_PROYECTADOS"] = data_2["Stock (Units)"] * factor_m3_por_unidad

# 4. Serie continua histórico + forecast (concatenar, no merge)
timeline = pd.concat([
    stock_hist.rename(columns={"STOCK (Units)": "STOCK_UNITS"})[["FECHA","STOCK_UNITS","PERIODO"]],
    data_2.rename(columns={"Stock (Units)": "STOCK_UNITS"})[["FECHA","STOCK_UNITS","PERIODO"]]
], ignore_index=True)

# 5. Faltante: m3 proyectados vs capacidad instalada (usa el valor/tramo que decidiste en la Pregunta 1)
CAPACIDAD_INSTALADA_M3 = 3780  # <-- ajusta con el valor final que definiste
data_2["FALTANTE_M3"] = data_2["M3_PROYECTADOS"] - CAPACIDAD_INSTALADA_M3



# FALTANTE_M3 ya lo tienes definido como:
# data_2["FALTANTE_M3"] = data_2["M3_PROYECTADOS"] - CAPACIDAD_INSTALADA_M3

# Encontrar la primera fecha donde el faltante se vuelve positivo (déficit de capacidad)
dias_con_deficit = data_2[data_2["FALTANTE_M3"] > 0]

if len(dias_con_deficit) > 0:
    primera_fecha_deficit = dias_con_deficit.iloc[0]["FECHA"]
    print(f"Primer día con déficit de capacidad: {primera_fecha_deficit}")
else:
    print("No se proyecta déficit de capacidad en el horizonte de forecast (todo julio)")

# Para ver la evolución completa día a día
print(data_2[["FECHA", "M3_PROYECTADOS", "FALTANTE_M3"]].to_string(index=False))



promedio_global = (m3_diario["M3_OCUPADOS"].mean())
promedio_global


# Máxima ocupación histórica:
max_ocupacion = (
    m3_diario
    .groupby("WAREHOUSE_ID")["M3_OCUPADOS"]
    .max().reset_index()
)

max_ocupacion


# Variabilidad
desviacion = (
    m3_diario
    .groupby("WAREHOUSE_ID")["M3_OCUPADOS"]
    .std()
)

desviacion



import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt

# 1. Tu serie de ventas
venta = pd.Series(
    [1430,1325,1234,1330,1308,1229,1414,1322,1317,1401,1273,1350,
     1313,1304,1371,1313,1386,1309,1333,1322,1326,1272,1390,1400,
     1449,1385,1336,1316,1306,1348],
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

# b) Media móvil (ventana de 7 días)
ventana = 7
pred_b = [train[-ventana:].mean()] * TEST_DAYS
resultados["Media Movil (7d)"] = mae(test, pred_b)

# c) Suavizacion exponencial simple
modelo_ses = SimpleExpSmoothing(train).fit(optimized=True)
pred_c = modelo_ses.forecast(TEST_DAYS)
resultados["Suavizacion Exponencial Simple"] = mae(test, pred_c)

# d) Suavizacion exponencial doble (Holt)
modelo_holt = Holt(train).fit(optimized=True)
pred_d = modelo_holt.forecast(TEST_DAYS)
resultados["Suavizacion Exponencial Doble (Holt)"] = mae(test, pred_d)

# Tabla comparativa
tabla_error = pd.DataFrame(resultados.items(), columns=["Modelo", "MAE"]).sort_values("MAE")
print(tabla_error)


# Datos Finales
modelo_final = SimpleExpSmoothing(venta).fit(optimized=True)

horizonte = pd.date_range("2026-06-26", "2026-07-25", freq="D")
forecast_final = modelo_final.forecast(len(horizonte))

tabla_forecast = pd.DataFrame({
    "CALENDAR_DATE": horizonte,
    "Venta_Forecast": forecast_final.round(0).astype(int)
})

print(tabla_forecast.to_string(index=False))




# Productividad horaria = Unidades procesadas (Venta) / Horas Hombre Packing

# METODO A
diario = data_1.groupby("CALENDAR_DATE").agg(
    venta=("Venta (Units)", "sum"),
    horas=("Horas Hombre Packing", "sum")
).reset_index()
diario["productividad"] = diario["venta"] / diario["horas"]
productividad_metodo_A = diario["productividad"].mean()



# METODO B
productividad_metodo_B = data_1["Venta (Units)"].sum() / data_1["Horas Hombre Packing"].sum()


productividad_metodo_A
productividad_metodo_B


# Clasificar pequeño y grande: 
data_1["VOL_M3"] = (data_1["ITE_LENGTH (cm)"]*data_1["ITE_WIDTH (cm)"]*data_1["ITE_HEIGHT (cm)"])/1_000_000

UMBRAL_M3 = data_1["VOL_M3"].median()  # supuesto: split por mediana ≈ 0.026 m3
data_1["TAMANO"] = data_1["VOL_M3"].apply(lambda v: "Pequeño" if v <= UMBRAL_M3 else "Grande")


# 1. Clasificar tamaño (ya definido arriba)
# 2. Mix histórico de venta por tamaño (para prorratear el forecast total)
mix = data_1.groupby("TAMANO")["Venta (Units)"].sum()
mix_pct = mix / mix.sum()
print(mix_pct)

# 3. Forecast de venta total para WK29 (usa tu modelo ganador, SES)
wk29 = pd.date_range("2026-07-13", "2026-07-19", freq="D")
forecast_wk29 = modelo_final.forecast(len(pd.date_range("2026-06-26","2026-07-19",freq="D")))[-7:]
pico_diario_total = forecast_wk29.max()  # el día más alto dentro de WK29

# 4. Split del pico por tamaño, usando el mix histórico
pico_pequeno = pico_diario_total * mix_pct["Pequeño"]
pico_grande = pico_diario_total * mix_pct["Grande"]



# 5. Productividad por hora (de tu Pregunta 4) y horas por turno (supuesto, ej. 8h)
HORAS_TURNO = 8
productividad_hora = 50.1  # tu resultado de la Pregunta 4 (ajusta si te salió distinto)
throughput_mesa_dia = productividad_hora * HORAS_TURNO

# 6. Mesas necesarias
import math
mesas_pequeno = math.ceil(pico_pequeno / throughput_mesa_dia)
mesas_grande = math.ceil(pico_grande / throughput_mesa_dia)

print(mix_pct)
print("Mesas Pequeño:", mesas_pequeno, "| Mesas Grande:", mesas_grande)


# Horas-hombre necesarias en WK29 = Volumen total de la semana (unidades) / Productividad (u/hora)
# Headcount = Horas-hombre necesarias / Horas disponibles por persona en la semana

volumen_semanal_wk29 = 1339 * 7  # los 7 días de WK29, todos iguales por ser SES plano
horas_hombre_necesarias = volumen_semanal_wk29 / productividad_hora  # 50.10

HORAS_POR_PERSONA_SEMANA = 48  # supuesto: jornada de 8h x 6 días — declara el tuyo si usas otro esquema
headcount = math.ceil(horas_hombre_necesarias / HORAS_POR_PERSONA_SEMANA)
print("Horas-hombre semana:", horas_hombre_necesarias, "| Headcount:", headcount)