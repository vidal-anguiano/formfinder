import argparse

import pandas as pd

from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.ml.classification import LogisticRegression, LogisticRegressionModel
from pyspark.ml.feature import (RegexTokenizer, StopWordsRemover, Word2Vec, HashingTF, IDF)

import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
stop_words = list(stopwords.words('english'))

MODEL = './model.model'


def reindex_data(filepath):
    pdata = pd.read_parquet(filepath)
    pdata = pdata.reset_index(drop=True).set_index('pdf_id')
    pdata.to_parquet('./reindexed_data.parq')

    return None


def read_data(filepath, spark):
    ''' Reads data and creates temp view.'''
    data = spark.read.option('header', 'true')\
                     .option('inferSchema', 'true')\
                     .parquet(filepath)
    data.createOrReplaceTempView('data')


def clean_data(spark):
    data = spark.sql('''
                     SELECT *
                     FROM data
                     WHERE text is not NULL
                     ''')
    data.createOrReplaceTempView('data')
    data = spark.sql('''
                     SELECT *
                     FROM data
                     WHERE length(text) > 20
                     ''')
    data.createOrReplaceTempView('data')

    return data


def create_pipeline(model):
    regexTokenizer = RegexTokenizer(inputCol='text',
                                    outputCol='words',
                                    pattern="\\W")

    stopwordsRemover = StopWordsRemover(inputCol='words',
                                        outputCol='filtered').setStopWords(stop_words)

    hashingTF = HashingTF(inputCol='filtered',
                          outputCol='rawFeatures',
                          numFeatures=10000)

    idf = IDF(inputCol='rawFeatures',
              outputCol='features',
              minDocFreq=5)

    model = LogisticRegressionModel.load(model)

    pipeline = Pipeline(stages=[regexTokenizer,
                                stopwordsRemover,
                                hashingTF,
                                idf,
                                model])

    return pipeline


def predict(pipeline, data):
    pipelineFit = pipeline.fit(data)
    results = pipelineFit.transform(data)
    results.createOrReplaceTempView('results')


def output_results(spark):
    pred = spark.sql('''
                     SELECT from_page, 
                     pdf_url,
                     num_pages,
                     num_pages_scraped,
                     is_fillable,
                     probability,
                     prediction
                     FROM results''').toPandas()
    pred['prob'] = pred.probability.apply(lambda x: x[1])
    pred = pred.sort_values(by='prob', ascending=False)
    pred = pred[['from_page',
             'pdf_url',
             'num_pages',
             'num_pages_scraped',
             'is_fillable',
             'prediction',
             'prob',]]
    pred.to_csv('./output/results.csv')


def run_model(filepath, model):
    spark = SparkSession\
        .builder\
        .master('local[*]')\
        .appName('Python Text Classification')\
        .config("spark.executor.memory", "1g")\
        .getOrCreate()

    print('SPARK SESSION STARTED')

    reindex_data(filepath)

    read_data(filepath, spark)
    print("DATA HAS BEEN READ")

    print("DATA IS BEING CLEANED")
    data = clean_data(spark)
    print("DATA IS CLEAN")

    pipeline = create_pipeline(model)

    print("PIPELINE CREATED")
    print("PIPELINE RUNNING")
    predict(pipeline, data)
    print("PIPELINE COMPLETE")

    print("PRODUCING RESULTS")
    output_results(spark)

    print("PROCESS COMPLETE")
    return "Done."

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start prediction process.')
    parser.add_argument('filepath',
                        help='Local parquet file produced by running web and pdf scraper.')
    parser.add_argument('model',
                        help='Local saved model.')

    args = parser.parse_args()

    run_model(args.filepath, args.model)
