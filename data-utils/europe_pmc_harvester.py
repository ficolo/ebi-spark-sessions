import logging
from typing import Dict, List
import requests
import json
from config import *
import urllib
import os
from datetime import datetime, date
from tqdm import tqdm

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def get_papers_by_keywords(keywords):
    europe_pmc_url = EUROPE_PMC_SERVICE_URL
    europe_pmc_query = EUROPE_PMC_KEYWORDS_QUERY.format(
        keywords='"' + '" OR "'.join(keywords) + '"'
    )
    europe_pmc_rq_url = europe_pmc_url + urllib.parse.quote_plus(europe_pmc_query)
    europe_pmc_results = execute_query_all(europe_pmc_rq_url)
    return europe_pmc_results


def get_paper_by_pmid(pmid):
    europe_pmc_url = EUROPE_PMC_SERVICE_URL
    europe_pmc_query = EUROPE_PMC_PMID_QUERY.format(pmid=pmid)
    europe_pmc_rq_url = europe_pmc_url + urllib.parse.quote_plus(europe_pmc_query)
    results = execute_query(europe_pmc_rq_url)["resultList"]["result"]
    paper = results[0] if len(results) > 0 else {}
    return paper


def execute_query(query, cursor_mark="%2A"):
    europe_pmc_results = None
    europe_pmc_opts = EUROPE_PMC_QUERY_OPTS.format(cursor=cursor_mark)
    rq_url = query + europe_pmc_opts
    try:
        logger.info("europe_pmc query started: " + rq_url)
        europe_pmc_results_json = requests.get(rq_url).text
        europe_pmc_results = json.loads(europe_pmc_results_json)
        logger.info("europe_pmc query finished")
    except Exception:
        logger.error("europe_pmc query failed: " + rq_url)
    return europe_pmc_results


def execute_query_all(rq_url):
    cursor_mark = "%2A"
    done = False
    results = []
    while not done:
        page_result = execute_query(rq_url, cursor_mark)
        results.extend(page_result["resultList"]["result"])
        done = cursor_mark == page_result["nextCursorMark"]
        cursor_mark = page_result["nextCursorMark"]
    return results


def export_to_json(references: List[Dict], offset: int, output_path: str):
    i = 0
    for chunk in chunks(references, 1000):
        with open(
            f"{output_path}/references_{offset + i}_{offset + i + 1000}.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(chunk, f, default=default_serializer)
        i += 1000


def chunks(dict_list, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(dict_list), n):
        yield dict_list[i : i + n]


def parse_result(reference):
    author_list = reference.pop("authorList") if "authorList" in reference else []
    reference["authorList"] = (
        author_list["author"] if not type(author_list) == list else author_list
    )
    grant_list = reference.pop("grantsList") if "grantsList" in reference else []
    reference["grantsList"] = (
        grant_list["grant"] if "grant" in grant_list else grant_list
    )
    full_text_url_list = (
        reference.pop("fullTextUrlList") if "fullTextUrlList" in reference else []
    )
    reference["fullTextUrlList"] = (
        full_text_url_list["fullTextUrl"]
        if "fullTextUrl" in full_text_url_list
        else full_text_url_list
    )
    mesh_heading_list = (
        reference.pop("meshHeadingList") if "meshHeadingList" in reference else []
    )
    mesh_heading_list = (
        mesh_heading_list["meshHeading"]
        if "meshHeading" in mesh_heading_list
        else mesh_heading_list
    )
    mesh_heading_list = [mesh_term["descriptorName"] for mesh_term in mesh_heading_list]
    reference["meshHeadingList"] = mesh_heading_list
    reference["firstPublicationDate"] = datetime.strptime(
        reference["firstPublicationDate"], "%Y-%m-%d"
    )
    reference["pubYear"] = int(reference["pubYear"])
    return reference


def generate_dataset(dataset_desc):
    output_path = os.path.join("data/", dataset_desc["name"])
    os.mkdir(output_path)
    if "pmids" in dataset_desc and len(dataset_desc["pmids"]) > 0:
        references = [get_paper_by_pmid(pmid) for pmid in tqdm(dataset_desc["pmids"])]
    else:
        references = get_papers_by_keywords(dataset_desc["keywords"])
    export_to_json(references, 0, output_path)


def default_serializer(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat()


# for resource in resources[1:]:
#     print("Processing " + resource["name"])
#     generate_dataset(resource)
#     print("Finalizing " + resource["name"])
generate_dataset(resources[0])
