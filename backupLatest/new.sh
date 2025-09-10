#!/bin/bash

rm -r /home/rocky/missing

python /home/rocky/elastic/data/collectMissingArticles.py --startDate "2024-11-06"

python /home/rocky/elastic/data/collectMissingSocialFeeds.py --startDate "2024-11-06"

#python articleMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_in_mongo_2024-11-01.csv"
#python articleMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_in_mongo_2024-11-02.csv"
#python articleMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_in_mongo_2024-11-03.csv"
python /home/rocky/elastic/data/articleMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_in_mongo_2024-11-06.csv"
python /home/rocky/elastic/data/articleMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_in_mongo_2024-11-07.csv"

#python socialFeedMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_sf_in_mongo_2024-11-01.csv"
#python socialFeedMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_sf_in_mongo_2024-11-02.csv"
#python socialFeedMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_sf_in_mongo_2024-11-03.csv"
python /home/rocky/elastic/data/socialFeedMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_sf_in_mongo_2024-11-06.csv"
python /home/rocky/elastic/data/socialFeedMigrationBSONByIds.py --csvPath "/home/rocky/missing/missing_sf_in_mongo_2024-11-07.csv"

#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=article --db=pnq /home/rocky/missing/article_20241101.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=article --db=pnq /home/rocky/missing/article_20241102.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=article --db=pnq /home/rocky/missing/article_20241103.bson
mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=article --db=pnq /home/rocky/missing/article_20241106.bson
mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=article --db=pnq /home/rocky/missing/article_20241107.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=articleTag --db=pnq /home/rocky/missing/articleTag_20241101.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=articleTag --db=pnq /home/rocky/missing/articleTag_20241102.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=articleTag --db=pnq /home/rocky/missing/articleTag_20241103.bson
mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=articleTag --db=pnq /home/rocky/missing/articleTag_20241106.bson
mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=articleTag --db=pnq /home/rocky/missing/articleTag_20241107.bson

#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeed --db=pnq /home/rocky/missing/socialFeed_20241101.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeed --db=pnq /home/rocky/missing/socialFeed_20241102.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeed --db=pnq /home/rocky/missing/socialFeed_20241103.bson
mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeed --db=pnq /home/rocky/missing/socialFeed_20241106.bson
mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeed --db=pnq /home/rocky/missing/socialFeed_20241107.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeedTag --db=pnq /home/rocky/missing/socialFeedTag_20241101.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeedTag --db=pnq /home/rocky/missing/socialFeedTag_20241102.bson
#mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeedTag --db=pnq /home/rocky/missing/socialFeedTag_20241103.bson
mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeedTag --db=pnq /home/rocky/missing/socialFeedTag_20241106.bson
mongorestore --uri="mongodb://admin:V5%26uX%233L%5E8rQ@mongo.pnq.co.in:27017/pnq?authSource=admin" --collection=socialFeedTag --db=pnq /home/rocky/missing/socialFeedTag_20241107.bson

python /home/rocky/elastic/data/missingPrintMongo2Elastic.py --csvPath "/home/rocky/missing/missing_in_elastic_2024-11-07.csv"
python /home/rocky/elastic/data/missingPrintMongo2Elastic.py --csvPath "/home/rocky/missing/missing_in_elastic_2024-11-06.csv"
#python missingPrintMongo2Elastic.py --csvPath "/home/rocky/missing/missing_in_elastic_2024-11-03.csv"
#python missingPrintMongo2Elastic.py --csvPath "/home/rocky/missing/missing_in_elastic_2024-11-02.csv"
#python missingPrintMongo2Elastic.py --csvPath "/home/rocky/missing/missing_in_elastic_2024-11-01.csv"

python /home/rocky/elastic/data/missingOnlineMongo2Elastic.py --csvPath "/home/rocky/missing/missing_sf_in_elastic_2024-11-07.csv"
python /home/rocky/elastic/data/missingOnlineMongo2Elastic.py --csvPath "/home/rocky/missing/missing_sf_in_elastic_2024-11-06.csv"
#python missingOnlineMongo2Elastic.py --csvPath "/home/rocky/missing/missing_sf_in_elastic_2024-11-03.csv"
#python missingOnlineMongo2Elastic.py --csvPath "/home/rocky/missing/missing_sf_in_elastic_2024-11-02.csv"
#python missingOnlineMongo2Elastic.py --csvPath "/home/rocky/missing/missing_sf_in_elastic_2024-11-01.csv" 