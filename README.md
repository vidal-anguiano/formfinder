# formfinder
This project scrapes municipal websites for pdf files, scrapes them, and uses Machine Learning to identify webpages with pdf forms as a way of finding paper-based processes.


# Instructions for Running

These instructions are divided into two parts: 
 - One for scraping the web for PDF files and scraping the text from those PDF files
 - The second for running the output of the web + PDF scraper through a model which splits out a probability score of whether it is a form.
 
 
## Running the Web and PDF Scraper

1. Clone this repository  

2. EITHER:  
 - Build the Docker image using the Dockerfile in the the `scraper` directory  
 - Pull the image from DockerHub using `docker pull vidalanguiano/formfinder`  
 
3. Run the Docker container using `docker run -it --rm -v [LOCAL REPO FOLDER]:/mnt vidalanguiano/formfinder bash`

4. To run the scraper, run `python scraper/run_scraper.py "https://cityofchicago.org" 15000 2 4000 2`  
`-s3` flag can be used to push data straight to S3 and `-fnp` flag can be used to specify the filename'  
The numbers in the above command are:  
 - 15000: the number of web pages to be scraped (PER PROCESS) for PDF links before the web scraper process stops  
 - 2: the number of processes to dedicate to web scraping in parallel  
 - 4000: the number of PDF documents to scrape for text (PER PROCESS) before the process stops  
 - 2: the umber of processes to dedicate to the PDF scraping in parallel  
 When I ran this, I believe I used parameters `15000 4 4000 4` and ran it in an m5.2xlarge EC2 instance with 8 cores. When I ran it in an EC2 instance, I had to install Docker among other things, and I unfortunately can't find the file where I kept all the commands I used to setup the EC2 instance.

NOTE: The code, as written, will only push to my own S3 bucket. I also ran `docker run` with `-v` to mount my local `~/.aws` folder to `~/.aws` in the container, which enabled write to the S3 bucket.

5. Once the process is complete, you should see a new folder `data` created in your working directory containing all of the parquet files. 

NOTE: The output for when the files are saved locally are not the files that can be used as inputs into the PDF Classifier. In order to produce the single parquet file that is used as an input for the PDF Classifier, use Pandas to read in each of the parquet files, join the DataFrames, and use `df.to_parquet()`, which will unify the separate parquet files into one. The output that was supposed to be produced for the PDF Classifier can only be produced using the `-s3` flag. Before moving onto the next step, make sure to create the single parquet file as described here and put it in `./modeldeploy`. 


## Running the PDF Classifier

1. Pull the stock jupyter/pyspark-notebook image using `docker pull jupyter/pyspark-notebook`  

2. Start the Docker container using `docker run -it -v [LOCAL REPO FOLDER]:/home/jovyan/ jupyter/pyspark-notebook bash`  

3. Install nltk by running `pip install nltk`.  

4. Run the data produced from the web + PDF scraper through the model in the repo by running `python modeldeploy/run_model.py data.parq model.model`  
NOTE: There are two command line arguments here, one is the filepath of the parquet file you created above (I highly recommend using mine which can be found [here](https://drive.google.com/drive/folders/1sQzYmUM_U8PvAWvXQs3Z1eksDZoczilZ?usp=sharing)) and the second argument is the model, which is in the repo.

5. See the results which should now be located in `./modeldeploy/output/results.csv`. See [here](https://drive.google.com/drive/folders/1sQzYmUM_U8PvAWvXQs3Z1eksDZoczilZ?usp=sharing) for an example of the output.


