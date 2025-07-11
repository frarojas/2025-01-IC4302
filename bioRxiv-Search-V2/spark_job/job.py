from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, to_date
import os
import glob
import shutil
import sys

atlas_uri = "mongodb+srv://sebcalvo:9StJIotFXpl0CbNw@cluster0.xosgnib.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

spark = SparkSession.builder \
    .appName("BioRxivSparkProcessor") \
    .config("spark.mongodb.output.uri", atlas_uri) \
    .getOrCreate()

#verificar si hay archivos en /augmented
json_files = glob.glob("/augmented/*.json")
if not json_files:
    print("No hay archivos en /augmented para procesar. Saliendo.")
    spark.stop()
    sys.exit(0)

#leer todos los JSON enriquecidos que esten en /augmented
df_raw = spark.read.json(json_files)

#explode del array "collection" para que cada articulo sea fila independiente
df_articles = df_raw.selectExpr("explode(collection) as article").select("article.*")

#extraer author_name de rel_authors
df_with_authors = df_articles.withColumn("authors", col("rel_authors.author_name"))

#normalizar campos
df_norm = df_with_authors \
    .withColumnRenamed("rel_doi", "doi") \
    .withColumnRenamed("rel_title", "title") \
    .withColumnRenamed("rel_abs", "abstract") \
    .withColumn("date", to_date(col("rel_date"), "yyyy-MM-dd")) \
    .withColumnRenamed("rel_category", "category")

#seleccionar columnas a guardar en Mongo
df_out = df_norm.select(
    col("doi"),
    col("title"),
    col("abstract"),
    col("authors"),
    col("date"),
    col("entities"),
    col("category")
)

#escribir en MongoDB
df_out.write \
    .format("com.mongodb.spark.sql.DefaultSource") \
    .mode("append") \
    .option("database", "projectDB") \
    .option("collection", "documents") \
    .save()

spark.stop()
print("Spark Job completado con éxito.")

#mover los archivos procesados a la carpeta de procesados
processed_folder = "./procesados"
os.makedirs(processed_folder, exist_ok=True)

for file in json_files:
    destination = os.path.join(processed_folder, os.path.basename(file))
    shutil.move(file, destination)
    print(f"Archivo {file} movido a {destination}")