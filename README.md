# Prometheus Cloud Foundry Proxy #

NOTE: This was developed as part of a spike investigating Prometheus scraping
applications deployed on Cloud Foundry.

This app exists to set an extra header `X-CF-APP-INSTANCE`, on requests from
Prometheus to apps with multiple instances on CF. Cloud Foundry's router uses
this header to route requests to the specific instances. This allows you to get
metric coverage over all running instances.

As well as doing this it applies some additional Prometheus labels for more
useful querying (app name, guid, space, instance_index).

This app is then added as a target to Prometheus to scrape all configured apps
on Cloud Foundry.

## Configuration ##

```ini
[some-app-serving-metrics.cloudapps.digital]
app=rails-prometheus
space=sandbox
org=somewhere
guid=8c6d6391-6d5d-4b42-8741-f1c96312bcfa
path=/metrics
port=443
instances=2
```

If we progress any further with this apps would be discovered using the Cloud
Foundry API. Removing the need for individual app configuration.
