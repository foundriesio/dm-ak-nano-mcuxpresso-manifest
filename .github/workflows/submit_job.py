#!/usr/bin/env python3

import argparse
import os
import requests
import sys
import logging
import time
import yaml

from urllib.parse import urlparse


# create logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def resolve_job_id(qa_server, qa_backend, qa_job_id):
    server_parts = urlparse(qa_server)
    QA_SERVER = f"{server_parts.scheme}://{server_parts.netloc}/"

    # get job details
    url = f"{QA_SERVER}/api/testjobs/{qa_job_id}/"
    response = requests.get(url)
    lava_job_id = None
    if response.status_code == 200:
        job_details = response.json()
        lava_job_id = job_details["job_id"]
    if lava_job_id is None:
        logger.info("No LAVA job ID available")
        return

    # get backend details
    url = f"{QA_SERVER}/api/backends/?name={qa_backend}"
    response = requests.get(url)
    backend = None
    if response.status_code == 200:
        results = response.json()["results"]
        if len(results) > 0:
            # there should be only one
            backend = results[0]
    backend_job_url = None
    if backend is not None:
        backend_parts = urlparse(backend["url"])
        backend_job_url = f"{backend_parts.scheme}://{backend_parts.netloc}/scheduler/job/{lava_job_id}"
        logger.info(f"LAVA job URL: {backend_job_url}")



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--qa-server",
            required=True)
    parser.add_argument("--qa-token",
            default=os.environ.get("QA_TOKEN"),
            required=False)
    parser.add_argument("--qa-team",
            required=True)
    parser.add_argument("--qa-project",
            required=True)
    parser.add_argument("--qa-version",
            required=True)
    parser.add_argument("--qa-backend",
            required=True)
    parser.add_argument("--job-filename",
            required=True)
    parser.add_argument("--commit-id",
            default=os.environ.get("COMMIT_ID"),
            required=False)
    parser.add_argument("--commit-repository",
            default=os.environ.get("COMMIT_REPOSITORY"),
            required=False)
    parser.add_argument("--commit-repository-user",
            default=os.environ.get("COMMIT_REPOSITORY_USER"),
            required=False)
    parser.add_argument("--qa-patch-source",
            default=os.environ.get("QA_PATCH_SOURCE"),
            required=False)
    parser.add_argument("--gh-calling-action",
            default=os.environ.get("BUILD_RUN_ID"),
            required=False)
    parser.add_argument("--gh-artifacts-url",
            default=os.environ.get("GITHUB_ARTIFACTS_URL"),
            required=False)


    args = parser.parse_args()
    if not args.qa_token:
        logger.error("QA Token missing")
        sys.exit(1)

    server_parts = urlparse(args.qa_server)
    QA_SERVER = f"{server_parts.scheme}://{server_parts.netloc}/"
    QA_TOKEN = args.qa_token

    TEAM = args.qa_team
    PROJECT = args.qa_project
    VERSION = args.qa_version

    patch_id = None
    if args.commit_id and args.commit_repository and args.commit_repository_user and args.qa_patch_source:
        patch_id = f"{args.commit_repository_user}/{args.commit_repository}/{args.commit_id}"

    headers = {
        "Auth-Token": QA_TOKEN
    }
    data = {}
    if patch_id is not None:
        data.update({
            "patch_id": patch_id,
            "patch_source": args.qa_patch_source
        })

    url = "{QA_SERVER}/api/createbuild/{QA_SERVER_TEAM}/{QA_SERVER_PROJECT}/{QA_SERVER_VERSION}".format(
        QA_SERVER=QA_SERVER,
        QA_SERVER_TEAM=TEAM,
        QA_SERVER_PROJECT=PROJECT,
        QA_SERVER_VERSION=VERSION
    )

    build_response = requests.post(url, data=data, headers=headers)
    if build_response.status_code == 201:
        logger.info(f"QA Reports build created: {QA_SERVER}/{TEAM}/{PROJECT}/build/{VERSION}")

    # build artifacts
    artifact_url = None
    artifact_response = requests.get(args.gh_artifacts_url)
    if artifact_response.status_code == 200:
        artifact_list = artifact_response.json()
        logger.debug(artifact_list)
        artifact_url = artifact_list["artifacts"][0]["archive_download_url"]

    definition = None
    ENVIRONMENT = None
    with open(args.job_filename, "r") as jobfile:
        definition = jobfile.read()
        ENVIRONMENT = yaml.safe_load(definition)['device_type']
    data = {
        "backend": args.qa_backend,
        "definition": definition.format_map(SafeDict(BUILD_URL=artifact_url, OTA_REVISION_BASE=args.gh_calling_action[:6]))
    }

    URL = "%s/api/submitjob/%s/%s/%s/%s" % (QA_SERVER, TEAM, PROJECT, VERSION, ENVIRONMENT)
    response = requests.post(URL, data=data, headers=headers)
    if response.status_code == 201:
        qa_job_id = response.text
        logger.info(f"Test job submitted via QA Reports: {QA_SERVER}/api/testjobs/{qa_job_id}/")
        time.sleep(30)  # wait 30 seconds for test job submission
        resolve_job_id(QA_SERVER, args.qa_backend, qa_job_id)

if __name__ == "__main__":
    main()
