## Introduction

The purpose of this application is to disable a scheduled search in a particular application 

## Installation
Install this into any forwarder, indexer, search head or search head cluster where you would like a scheduled search disabled
In general this is useful for reports in default applications that you would like to disable in an automated fashion

## Why was this application built?

The report heuristics_report in the splunk_secure_gateway in Splunk 9.1.3 was poorly written and running over a time period -1y. Since this is a built-in Splunk application it takes a little bit more work to ensure it's disabled on all cluster managers, monitoring consoles, search heads and indexers. Therefore this application was created.

## How do I use this application?
Configure your inputs.conf to disable the required app/report_name, for example:
```
[report_disabler://heuristics_report]
app = splunk_secure_gateway
interval = -1
report_name = heuristics_report
```

On a search head cluster the input will only run on the captain to avoid duplicated REST calls, otherwise the input will run on the requested interval

## Are there alternatives?
In a search head cluster this is easily disabled via the UI, on a forwarder or indexer this is slightly more effort.

For the report shown in the example, that runs on every indexer which makes it easier to distribute an application to disable the required report as the app is built into splunk.

If this were a non-default Splunk app you could simply override the disabled flag via savedsearches.conf

## Troubleshooting
### SSL validation errors
If you see an error such as:
`Caused by SSLError(SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain (_ssl.c:1106)')))`

This simply means that the port 8089 is running an SSL certificate that is not trusted by the default certificate store in use by Splunk's python
You can change `verify=True` to `verify=False` in the config files this will bypass SSL validation of your local Splunk instance on port 8089 (note that this comes with a minor security risk)

## Feedback?
Feel free to open an issue on github or use the contact author on the SplunkBase link and I will try to get back to you when possible, thanks!

## Other
Icons by Bing CoPilot

## Release Notes
### 0.0.1
Initial version
