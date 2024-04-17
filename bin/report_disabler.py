import requests
import logging
import sys
import os
from logging.handlers import RotatingFileHandler
import urllib3

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from splunklib.modularinput import Argument
import splunklib.modularinput as smi

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ReportDisabler(smi.Script):
    def get_scheme(self):
        scheme = smi.Scheme("Report Disabling Input")
        scheme.description = "Set an application and a report_name to have it disabled when this input runs"
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False

        report_name = Argument("report_name")
        report_name.data_type = Argument.data_type_string
        report_name.required_on_edit = True
        report_name.required_on_create = True
        report_name.description = "Name of the report to be disabled"

        app_name = Argument("app")
        app_name.data_type = Argument.data_type_string
        app_name.required_on_edit = True
        app_name.required_on_create = True
        app_name.description = "Name of the app where the report exists"

        return scheme

    def stream_events(self, inputs, ew):
        # Create a logger
        logger = logging.getLogger(__name__)

        # Set the log level
        logger.setLevel(logging.INFO)
        #logger.setLevel(logging.DEBUG)
        
        log_file = os.environ['SPLUNK_HOME'] + "/var/log/splunk/report_disabler.log"

        # Create a handler
        handler = RotatingFileHandler(log_file, maxBytes=1048572, backupCount=3)

        # Create a formatter and add it to the handler
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(handler)
        
        logger.info("Report Disabler attempting to retrieve session key")
        # Define the headers
        headers = {"Authorization": "Splunk " + self.service.token }

        #Verify=false is hardcoded to workaround local SSL issues
        shc_check_url = 'https://localhost:8089/services/shcluster/captain/info?output_mode=json'
        res = requests.get(shc_check_url, headers=headers, verify=True)
        if (res.status_code == 503):
            logger.debug("Non-shcluster / standalone instance, safe to run on this node")
        elif (res.status_code != requests.codes.ok):
            logger.fatal(f"Unable to determine if this is a search head cluster or not, this is a bug, shc_check_url={shc_check_url} status_code={res.status_code} reason={res.reason} response={res.text}")
            return
        elif (res.status_code == 200):
            #We're in a search head cluster, but are we the captain?
            json_dict = res.json()
            if json_dict['origin'] != "https://localhost:8089/services/shcluster/captain/info":
                logger.info("Not on the captain, exiting now")
                return
            else:
                logger.info("On the captain node of an SHC, running")
        
        for input_name, input_item in list(inputs.inputs.items()):
            # Get fields from the InputDefinition object
            report_name = input_item["report_name"]
            app = input_item["app"]

            # Define the URLs
            report_url = f"https://localhost:8089/servicesNS/nobody/{app}/saved/searches/{report_name}?f=disabled&output_mode=json"
            report_post = f"https://localhost:8089/servicesNS/nobody/{app}/saved/searches/{report_name}"

            logger.debug(f"report_name={report_name} app={app} report_url={report_url} report_post={report_post}")

            logger.info(f"Check scheduled search with report_name={report_name} app={app}")

            # Make the GET request
            response = requests.get(report_url, headers=headers, verify=True)

            if response.status_code != 200:
                logger.error(f"GET request failed with status_code={response.status_code} text={response.text}")
                return

            # Parse the JSON data
            data = response.json()
            logger.debug(f"Response={data}")

            disabled = data['entry'][0]['content']['disabled']
            logger.debug(f"Disabled value is disabled={disabled}")

            if disabled == True:
                logger.info(f"Scheduled search with report_name={report_name} app={app} is already disabled")
                return
            else:
                # Make the POST request
                response = requests.post(report_post, headers=headers, data={"disabled": "1"}, verify=True)
                if response.status_code != 200:
                    logger.error(f"POST request failed with status_code={response.status_code} text={response.text}")
                    return
                logger.debug(f"POST request response status_code={response.status_code} text={response.text}")
                logger.info(f"POST request response status_code={response.status_code}")
                logger.info(f"scheduled search with name={report_name} app={app} is now disabled")

if __name__ == "__main__":
    exitcode = ReportDisabler().run(sys.argv)
    sys.exit(exitcode)

