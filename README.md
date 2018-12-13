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
 When I ran this, I believe I used parameters `15000 4 4000 4` and ran it in an m5.2xlarge EC2 instance with 8 cores.

NOTE: The code, as written, will only push to my own S3 bucket because when I ran this, I also ran `docker run` with `-v` to mount my local `~/.aws` folder to `~/.aws` in the container, which enabled write to the S3 bucket.

5. 
