import os
import argparse
from multiprocessing import Process, Pool, Queue, Value

import pandas as pd

from pdfscrape import pdf_pipeline
from cityscrape import scrape

if not os.path.isdir("./data"):
    os.makedirs('data/temp')
    os.makedirs('data/parquet')

SKIP_URL = ['department', 'spec', 'council', 'please', '311', 'phone', 'press', 'release', 'news']

tovisit_q = Queue()  # Stores the URLs that are to be visited on a FIFO basis
writeto_q = Queue()  # NOT IMPLEMENTED - eventually will be used to hold data that is to later be written by
                        # another process
faildrd_q = Queue()  # Stores the URLs that are dead or were not reached
pdflink_q = Queue()  # Stores links to PDF files to be scraped

pdflink_qs = Queue()  # Sores a Set that is shared by all Processes and used for keeping track of the pdf links
pdflink_qs.put(set()) # that have been added to the pdflink queue. 

visited_qs = Queue()  # Stores a Set that is shared by all Processes and used for keeping track of the pages 
visited_qs.put(set()) # that have been visited in order to prevent putting URLs into the queue when they've
                      # already been visited.
tovisit_qs = Queue()  # Similar to the visited_qs, this queue holds a Set of the URLs that are already in the
tovisit_qs.put(set()) # queue and prevents them from being added again.

kill_switch = Value('d', 0)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Start scrape process.')
    parser.add_argument('startpage',
                        help='Site from which to start the scrape.')
    parser.add_argument('web_to_scrape', type=int,
                        help='Number of web pages to scrape.')
    parser.add_argument('web_processes', type=int,
                        help='Number of web processors to use.')
    parser.add_argument('pdf_processes', type=int,
                        help='Number of pdf processors to use.')
    parser.add_argument('pdf_to_scrape', type=int,
                        help='Number of pdfs to scrape.')
    parser.add_argument('-s3', action='store_true',
                        help='Push data to S3')
    parser.add_argument('-fnp', default='pdfscrape_data',
                        help='default prefix for filename.')

    args = parser.parse_args()

    w = scrape.WebScrape(args.startpage,
                     tovisit_q,
                     writeto_q,
                     faildrd_q,
                     pdflink_q,
                     visited_qs,
                     tovisit_qs,
                     pdflink_qs,
                     lmt_doma='www.cityofchicago.org',
                     kill_switch=kill_switch)


    pdf_arguments = [(pdflink_q, 10, 5, 5, args.pdf_to_scrape, './data/scrape{}.csv'.format(i), 'temp{}.pdf'.format(i), kill_switch, False) for i in range(1, args.pdf_processes)]
    pdf_arguments.append((pdflink_q, 10, 5, 5, args.pdf_to_scrape + 20, './data/scrape{}.csv'.format(args.pdf_processes), 'temp_last.pdf', kill_switch, True))

    web_processes = [Process(name="Web Crawler {}", target=w.scrape, args=(args.web_to_scrape, SKIP_URL)) for i in range(1, args.web_processes + 1)]
    pdf_processes = [Process(name="PDF Scraper {}".format(i), target=pdf_pipeline.scrape_pdfs, args=(*pdf_arguments[i],)) for i, x in enumerate(pdf_arguments)]

    processes = web_processes + pdf_processes

    for process in processes:
        process.start()
    for process in processes:
        process.join()

    files = ['./data/scrape{}.csv'.format(i) for i in range(1, args.pdf_processes + 1)]

    for i, file in enumerate(files):
        print("READING CSV {}...".format(i))
        data = pd.read_csv(file, delimiter='`')
        print("CSV {} READ".format(i))
        filename = './data/parquet/scrape{}.parquet'.format(i + 1)
        print("CSV {} BEING DELETED...".format(i))
        os.remove(file)
        print("CSV {} DELETED.".format(i))
        print("WRITING FILE {} TO PARQUET...".format(i))
        if args.s3:
            data.to_parquet('s3://lsdm-vidal/formfinder/{}_{}.parquet'.format(args.fnp, i + 1))
        else:
            data.to_parquet(filename)
        print("FILE {} WRITTEN TO PARQUET.".format(i))

