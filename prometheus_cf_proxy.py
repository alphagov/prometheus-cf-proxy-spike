import configparser
import requests
import time

from wsgiref.simple_server import make_server
from prometheus_client import make_wsgi_app, REGISTRY
from prometheus_client.parser import text_string_to_metric_families

def parse_config(fd):
    config = configparser.ConfigParser()
    config.read(fd)
    return config

class CloudFoundryAppCollector:
    def __init__(self, url, guid, instance_count=1, additional_labels=None):
        self.url = url
        self.guid = guid
        self.additional_labels = additional_labels
        self.instance_count = instance_count

    def relabel_metrics(self, metrics, instance_number):
        for m in metrics:
            for _, samples, _ in m.samples:
                samples.update(self.additional_labels)
                samples.update({'instance_index': "{}".format(instance_number)})

    def read_metrics(self, instance_number):
        response = requests.get(self.url, headers={'X-CF-APP-INSTANCE': "{}:{}".format(self.guid, instance_number)})
        if response.status_code == 200:
            metrics = text_string_to_metric_families(response.content.decode('utf-8'))
            return list(metrics)
        return []

    def squash_metrics(self, instance_metrics, complete_metrics):
        complete_by_name = dict([(m.name, m) for m in complete_metrics])
        for metric in instance_metrics:
            if metric.name in complete_by_name:
                complete_by_name[metric.name].samples.extend(metric.samples)


    def collect(self):
        print("Collect!")
        complete_metrics = []
        for i in range(self.instance_count):
            instance_metrics = self.read_metrics(i)
            self.relabel_metrics(instance_metrics, i)
            self.squash_metrics(instance_metrics, complete_metrics)
            complete_metrics.extend(instance_metrics)
        for m in complete_metrics:
            print("{} - {} - {}".format(m.name, m.samples, m.type))
        return complete_metrics

def load_collectors(config):
    DEFAULTS = {
        "protocol": "https://",
        "port": "443",
        "path": "/metrics",
        "instances": 1,
    }

    for hostname in config.sections():
        app_config = DEFAULTS.copy()
        app_config.update(config[hostname])
        url = "https://{hostname}{path}".format(hostname=hostname, **app_config)
        additional_labels = {
            "app": app_config['app'],
            "space": app_config['space'],
            "org": app_config['org'],
            "guid": app_config['guid'],
        }
        collector = CloudFoundryAppCollector(url, app_config['guid'],
                                             instance_count=int(app_config['instances']),
                                             additional_labels=additional_labels)
        REGISTRY.register(collector)


if __name__ == '__main__':
    conf = parse_config('config.ini')
    load_collectors(conf)

    httpd = make_server('0.0.0.0', 8000, make_wsgi_app(REGISTRY))
    httpd.serve_forever()
